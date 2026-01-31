"""
Standard Console Logger for Cost Katana Python SDK
Simple, colorized console logging for debugging
"""

import sys
from datetime import datetime
from typing import Any, Optional

try:
    from colorama import Fore, Style, init

    init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False


class Logger:
    """Simple console logger with colorized output"""

    LOG_LEVELS = {"debug": 0, "info": 1, "warn": 2, "error": 3}

    def __init__(
        self,
        level: str = "info",
        prefix: str = "[Cost Katana]",
        timestamps: bool = True,
        colors: bool = True,
    ):
        self.config = {
            "level": level.lower(),
            "prefix": prefix,
            "timestamps": timestamps,
            "colors": colors and HAS_COLORAMA,
        }

    def debug(self, message: str, data: Any = None) -> None:
        """Log debug message"""
        self._log("debug", message, data)

    def info(self, message: str, data: Any = None) -> None:
        """Log info message"""
        self._log("info", message, data)

    def warn(self, message: str, data: Any = None) -> None:
        """Log warning message"""
        self._log("warn", message, data)

    def error(self, message: str, error: Optional[Exception] = None) -> None:
        """Log error message"""
        self._log("error", message, error)

    def set_level(self, level: str) -> None:
        """Set log level"""
        self.config["level"] = level.lower()

    def get_level(self) -> str:
        """Get current log level"""
        return self.config["level"]

    def _should_log(self, level: str) -> bool:
        """Check if a level should be logged"""
        return self.LOG_LEVELS[level] >= self.LOG_LEVELS[self.config["level"]]

    def _log(self, level: str, message: str, data: Any = None) -> None:
        """Internal log method"""
        if not self._should_log(level):
            return

        timestamp = self._get_timestamp() if self.config["timestamps"] else ""
        level_str = self._get_level_string(level)
        color = self._get_color(level) if self.config["colors"] else ""
        reset = Style.RESET_ALL if self.config["colors"] and HAS_COLORAMA else ""
        prefix = self.config["prefix"]

        log_message = f"{color}{timestamp}{prefix} {level_str} {message}{reset}"

        # Output based on level
        if level == "error":
            print(log_message, file=sys.stderr)
            if data:
                if isinstance(data, Exception):
                    print(f"{color}{str(data)}{reset}", file=sys.stderr)
                else:
                    print(data, file=sys.stderr)
        elif level == "warn":
            print(log_message, file=sys.stderr)
            if data:
                print(data, file=sys.stderr)
        else:
            print(log_message)
            if data:
                print(data)

    def _get_timestamp(self) -> str:
        """Get formatted timestamp"""
        now = datetime.now()
        return f"[{now.strftime('%H:%M:%S.%f')[:-3]}] "

    def _get_level_string(self, level: str) -> str:
        """Get level string"""
        level_map = {
            "debug": "DEBUG",
            "info": "INFO ",
            "warn": "WARN ",
            "error": "ERROR",
        }
        return level_map[level]

    def _get_color(self, level: str) -> str:
        """Get color for level"""
        if not HAS_COLORAMA:
            return ""

        color_map = {
            "debug": Fore.CYAN,
            "info": Fore.GREEN,
            "warn": Fore.YELLOW,
            "error": Fore.RED,
        }
        return color_map[level]

    def start_timer(self, label: str):
        """Create a timer for performance tracking"""
        start = datetime.now()
        self.debug(f"Timer started: {label}")

        def stop_timer():
            duration = (datetime.now() - start).total_seconds() * 1000
            self.debug(f"Timer ended: {label} ({duration:.0f}ms)")
            return duration

        return stop_timer


# Export singleton instance
logger = Logger()

