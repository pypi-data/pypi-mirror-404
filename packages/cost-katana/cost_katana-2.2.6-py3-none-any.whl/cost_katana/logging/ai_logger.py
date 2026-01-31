"""
AI Logger for Cost Katana Python SDK
Non-blocking async logging with batching for AI operations
"""

import asyncio
import hashlib
import re
import time
import uuid
from datetime import datetime
from threading import Lock, Thread
from typing import Any, Dict, List, Optional

import httpx

from .logger import logger


class AILogger:
    """AI Logger with batching and async processing"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        base_url: str = "https://api.costkatana.com",
        batch_size: int = 50,
        flush_interval: float = 5.0,
        enable_logging: bool = True,
        max_prompt_length: int = 1000,
        max_result_length: int = 1000,
        redact_sensitive_data: bool = True,
    ):
        self.config = {
            "api_key": api_key or "",
            "project_id": project_id or "",
            "base_url": base_url,
            "batch_size": batch_size,
            "flush_interval": flush_interval,
            "enable_logging": enable_logging,
            "max_prompt_length": max_prompt_length,
            "max_result_length": max_result_length,
            "redact_sensitive_data": redact_sensitive_data,
        }

        self.log_buffer: List[Dict[str, Any]] = []
        self.buffer_lock = Lock()
        self.is_shutting_down = False
        self.flush_thread: Optional[Thread] = None
        self.client: Optional[httpx.Client] = None

        # Sensitive data patterns
        self.sensitive_patterns = [
            re.compile(r"api[_-]?key[_-]?:\s*['\"]?([a-zA-Z0-9_-]+)['\"]?", re.IGNORECASE),
            re.compile(r"token[_-]?:\s*['\"]?([a-zA-Z0-9_.-]+)['\"]?", re.IGNORECASE),
            re.compile(r"password[_-]?:\s*['\"]?([^'\"]+)['\"]?", re.IGNORECASE),
            re.compile(r"secret[_-]?:\s*['\"]?([a-zA-Z0-9_-]+)['\"]?", re.IGNORECASE),
            re.compile(r"bearer\s+([a-zA-Z0-9_.-]+)", re.IGNORECASE),
            re.compile(r"\b[A-Z0-9]{20,}\b"),  # Long uppercase alphanumeric
        ]

        if self.config["enable_logging"] and self.config["api_key"]:
            self._initialize_client()
            self._start_periodic_flush()

    def _initialize_client(self):
        """Initialize HTTP client"""
        self.client = httpx.Client(
            base_url=self.config["base_url"],
            headers={
                "Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json",
                "x-project-id": self.config["project_id"],
            },
            timeout=10.0,
        )

    def _start_periodic_flush(self):
        """Start periodic flush in background thread"""

        def flush_periodically():
            while not self.is_shutting_down:
                time.sleep(self.config["flush_interval"])
                try:
                    self.flush()
                except Exception as e:
                    logger.debug(f"Periodic flush failed: {e}")

        self.flush_thread = Thread(target=flush_periodically, daemon=True)
        self.flush_thread.start()

    def log_ai_call(self, entry: Dict[str, Any]) -> None:
        """Log an AI operation (async, non-blocking)"""
        if not self.config["enable_logging"]:
            return

        try:
            enriched_entry = self._enrich_log_entry(entry)

            with self.buffer_lock:
                self.log_buffer.append(enriched_entry)
                logger.debug(
                    f"AI call logged to buffer (size: {len(self.log_buffer)})"
                )

                # Flush if buffer is full
                if len(self.log_buffer) >= self.config["batch_size"]:
                    # Spawn thread to flush without blocking
                    Thread(target=self.flush, daemon=True).start()

        except Exception as e:
            logger.error(f"Failed to log AI call: {e}")

    def log_template_usage(
        self,
        template_id: str,
        template_name: str,
        variables: Dict[str, Any],
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log template usage"""
        entry = {
            "service": "template",
            "operation": "use_template",
            "aiModel": "template-engine",
            "statusCode": 200,
            "responseTime": 0,
            "templateId": template_id,
            "templateName": template_name,
            "templateVariables": variables,
            **(additional_data or {}),
        }
        self.log_ai_call(entry)

    def _enrich_log_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich log entry with metadata and context"""
        request_id = entry.get("requestId") or str(uuid.uuid4())

        # Redact sensitive data
        sanitized_prompt = (
            self._redact_sensitive_data(entry.get("prompt", ""))[
                : self.config["max_prompt_length"]
            ]
            if entry.get("prompt")
            else None
        )

        sanitized_result = (
            self._redact_sensitive_data(entry.get("result", ""))[
                : self.config["max_result_length"]
            ]
            if entry.get("result")
            else None
        )

        # Calculate tokens if not provided
        input_tokens = entry.get("inputTokens") or (
            len(entry.get("prompt", "")) // 4 if entry.get("prompt") else 0
        )
        output_tokens = entry.get("outputTokens") or (
            len(entry.get("result", "")) // 4 if entry.get("result") else 0
        )
        total_tokens = entry.get("totalTokens") or (input_tokens + output_tokens)

        # Determine success
        success = entry.get("success", entry.get("statusCode", 200) < 400)

        # Determine log level
        log_level = entry.get("logLevel") or self._determine_log_level(
            success, entry.get("statusCode", 200)
        )

        return {
            **entry,
            "userId": entry.get("userId"),
            "projectId": entry.get("projectId") or self.config["project_id"],
            "requestId": request_id,
            "prompt": sanitized_prompt,
            "result": sanitized_result,
            "inputTokens": input_tokens,
            "outputTokens": output_tokens,
            "totalTokens": total_tokens,
            "success": success,
            "logLevel": log_level,
            "environment": entry.get("environment", "development"),
            "logSource": entry.get("logSource", "cost-katana-python-sdk"),
        }

    def _redact_sensitive_data(self, text: str) -> str:
        """Redact sensitive data from text"""
        if not self.config["redact_sensitive_data"]:
            return text

        redacted = text
        for pattern in self.sensitive_patterns:
            redacted = pattern.sub(
                lambda m: m.group(0)[:3] + "*" * max(0, len(m.group(0)) - 6) + m.group(0)[-3:],
                redacted,
            )
        return redacted

    def _determine_log_level(self, success: bool, status_code: int) -> str:
        """Determine log level based on success and status code"""
        if not success:
            if status_code >= 500:
                return "CRITICAL"
            if status_code >= 400:
                return "ERROR"
            return "WARN"
        return "INFO"

    def flush(self) -> None:
        """Flush buffered logs to backend"""
        with self.buffer_lock:
            if not self.log_buffer or not self.client:
                return

            logs_to_send = self.log_buffer.copy()
            self.log_buffer.clear()

        try:
            response = self.client.post("/api/ai-logs", json={"logs": logs_to_send})
            response.raise_for_status()
            logger.debug(f"AI logs flushed to backend (count: {len(logs_to_send)})")
        except Exception as e:
            # Put logs back in buffer on failure
            with self.buffer_lock:
                self.log_buffer.extend(logs_to_send)
            logger.debug(f"Failed to flush AI logs: {e}")

    def get_buffer_size(self) -> int:
        """Get buffer size (for testing/debugging)"""
        with self.buffer_lock:
            return len(self.log_buffer)

    def clear_buffer(self) -> None:
        """Clear buffer (for testing)"""
        with self.buffer_lock:
            self.log_buffer.clear()

    def shutdown(self) -> None:
        """Shutdown the logger"""
        self.is_shutting_down = True
        self.flush()
        if self.client:
            self.client.close()

    def __del__(self):
        """Cleanup on deletion"""
        try:
            self.shutdown()
        except:
            pass


# Export singleton instance
ai_logger = AILogger()

