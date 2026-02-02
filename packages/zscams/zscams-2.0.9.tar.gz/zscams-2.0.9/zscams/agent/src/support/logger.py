"""
Logger module for TLS Tunnel Client
"""

"""Singleton logger handlers for local logging only"""
import sys
import logging
import os
import platform
from typing import Dict
from logging import Logger

from zscams.agent.src.support.configuration import get_config

loggers: Dict[str, Logger] = {}

# -------------------- COLOR FORMATTER --------------------


class ColorFormatter(logging.Formatter):
    """Formatter adding ANSI colors to console logs only."""

    COLORS = {
        "DEBUG": "\033[93m",  # Yellow
        "INFO": "\033[92m",  # Green
        "WARNING": "\033[95m",  # Magenta
        "ERROR": "\033[91m",  # Red
        "CRITICAL": "\033[41m",  # Red background
    }

    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        msg = super().format(record)
        return f"{color}{msg}{self.RESET}"


# -------------------- SYSTEM LOG PATH --------------------


def get_default_system_log_path():
    """Returns the system default logging path"""
    system = platform.system()

    if system == "Windows":
        return os.path.join(
            os.environ.get("WINDIR", "C:\\Windows"), "System32", "winevt", "Logs"
        )

    elif system == "Linux":
        return "/var/log"

    else:
        return None  # unsupported


# -------------------- LOGGER FACTORY --------------------


def get_logger(name: str) -> Logger:
    """Create a singleton instance for that logger name"""
    if name in loggers:
        return loggers[name]

    logger = logging.getLogger(
        f"ZSCAMs - {name}" if name.lower().find("zscams") == -1 else name
    )
    logger.setLevel(get_config().get("logging", {}).get("level", 10))
    logger.propagate = False  # Prevent duplicate logs

    # Cleanup handlers if any
    if logger.hasHandlers():
        logger.handlers.clear()

    # -------- Console Handler -------- #
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(get_config().get("logging", {}).get("level", 10))

    console_formatter = ColorFormatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    # Cache singleton
    loggers[name] = logger
    return logger
