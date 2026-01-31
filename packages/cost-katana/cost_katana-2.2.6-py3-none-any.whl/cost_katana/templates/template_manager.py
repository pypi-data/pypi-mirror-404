"""
Template Manager for Cost Katana Python SDK
Handles local and backend template management
"""

import re
import time
from typing import Any, Dict, List, Optional

import httpx

from ..logging.logger import logger


class TemplateManager:
    """Template Manager with local and backend support"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.costkatana.com",
        enable_caching: bool = True,
        cache_ttl: int = 300,  # 5 minutes in seconds
    ):
        self.config = {
            "api_key": api_key or "",
            "base_url": base_url,
            "enable_caching": enable_caching,
            "cache_ttl": cache_ttl,
        }

        self.local_templates: Dict[str, Dict[str, Any]] = {}
        self.template_cache: Dict[str, Dict[str, Any]] = {}
        self.client: Optional[httpx.Client] = None

        if self.config["api_key"]:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize HTTP client"""
        self.client = httpx.Client(
            base_url=self.config["base_url"],
            headers={
                "Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json",
            },
            timeout=10.0,
        )

    def define_template(self, template: Dict[str, Any]) -> None:
        """Define a local template"""
        template_id = template.get("id")
        if not template_id:
            raise ValueError("Template must have an 'id' field")

        self.local_templates[template_id] = template
        logger.debug(f"Template defined locally: {template_id}")

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a template by ID (checks local first, then backend)"""
        # Check local templates first
        if template_id in self.local_templates:
            logger.debug(f"Template found locally: {template_id}")
            return self.local_templates[template_id]

        # Check cache
        if self.config["enable_caching"] and template_id in self.template_cache:
            cached = self.template_cache[template_id]
            if cached["expiry"] > time.time():
                logger.debug(f"Template found in cache: {template_id}")
                return cached["template"]

        # Fetch from backend
        return self.fetch_template(template_id)

    def fetch_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Fetch template from backend"""
        if not self.client:
            logger.warn(
                "No API client configured. Cannot fetch templates from backend."
            )
            return None

        try:
            response = self.client.get(f"/api/prompt-templates/{template_id}")
            response.raise_for_status()
            template = response.json().get("data")

            # Cache the template
            if self.config["enable_caching"]:
                self.template_cache[template_id] = {
                    "template": template,
                    "expiry": time.time() + self.config["cache_ttl"],
                }

            logger.debug(f"Template fetched from backend: {template_id}")
            return template

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warn(f"Template not found: {template_id}")
            else:
                logger.error(f"Failed to fetch template: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch template: {e}")
            return None

    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates (local + backend)"""
        templates = list(self.local_templates.values())

        if self.client:
            try:
                response = self.client.get("/api/prompt-templates")
                response.raise_for_status()
                backend_templates = response.json().get("data", [])

                # Filter out duplicates (local takes precedence)
                unique_backend = [
                    t for t in backend_templates if t.get("id") not in self.local_templates
                ]

                templates.extend(unique_backend)
                logger.debug(
                    f"Templates listed - local: {len(self.local_templates)}, "
                    f"backend: {len(unique_backend)}"
                )
            except Exception as e:
                logger.error(f"Failed to list backend templates: {e}")

        return templates

    def resolve_template(
        self, template_id: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Resolve template with variables"""
        template = self.get_template(template_id)

        if not template:
            raise ValueError(f"Template not found: {template_id}")

        variables = variables or {}

        # Find all variables in template content
        content = template.get("content", "")
        variable_pattern = re.compile(r"\{\{(\w+)\}\}")
        found_variables = set(variable_pattern.findall(content))

        # Check for missing required variables
        template_variables = template.get("variables", [])
        required_variables = [
            v.get("name") for v in template_variables if v.get("required")
        ]
        missing_variables = [v for v in required_variables if v not in variables]

        if missing_variables:
            raise ValueError(f"Missing required variables: {', '.join(missing_variables)}")

        # Resolve variables with defaults
        resolved_variables = {}
        for var_name in found_variables:
            if var_name in variables:
                resolved_variables[var_name] = variables[var_name]
            else:
                # Check for default value
                var_def = next(
                    (v for v in template_variables if v.get("name") == var_name), None
                )
                if var_def and "defaultValue" in var_def:
                    resolved_variables[var_name] = var_def["defaultValue"]
                else:
                    resolved_variables[var_name] = f"{{{{{var_name}}}}}"  # Keep placeholder

        # Substitute variables in content
        prompt = content
        for key, value in resolved_variables.items():
            placeholder = f"{{{{{key}}}}}"
            prompt = prompt.replace(placeholder, str(value))

        logger.debug(
            f"Template resolved: {template_id} "
            f"(variables: {len(resolved_variables)})"
        )

        # Track usage if backend available
        if self.client:
            try:
                self._track_template_usage(template_id, resolved_variables)
            except:
                pass  # Silent fail - tracking is not critical

        return {
            "prompt": prompt,
            "template": template,
            "resolvedVariables": resolved_variables,
            "missingVariables": missing_variables if missing_variables else None,
        }

    def _track_template_usage(
        self, template_id: str, variables: Dict[str, Any]
    ) -> None:
        """Track template usage on backend"""
        if not self.client:
            return

        try:
            self.client.post(
                f"/api/prompt-templates/{template_id}/use",
                json={"variables": variables, "timestamp": time.time()},
            )
        except:
            pass  # Silent fail

    def clear_cache(self) -> None:
        """Clear template cache"""
        self.template_cache.clear()
        logger.debug("Template cache cleared")

    def remove_local_template(self, template_id: str) -> bool:
        """Remove a local template"""
        if template_id in self.local_templates:
            del self.local_templates[template_id]
            logger.debug(f"Local template removed: {template_id}")
            return True
        return False

    def get_local_template_count(self) -> int:
        """Get number of local templates"""
        return len(self.local_templates)

    def __del__(self):
        """Cleanup on deletion"""
        if self.client:
            try:
                self.client.close()
            except:
                pass


# Export singleton instance
template_manager = TemplateManager()

