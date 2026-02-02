"""
Path utilities for TLS Tunnel Client
"""

import os
from pathlib import Path
from typing import Optional
from zscams.agent.src.support.logger import get_logger

logger = get_logger("FileSystem")


def resolve_path(path: Optional[str], base_dir: Optional[str] = None) -> Optional[str]:
    """
    Resolve a file path relative to a base directory.

    Args:
        path (str): Path to resolve (absolute or relative)
        base_dir (str, optional): Directory to resolve relative paths from.
            Defaults to None (current working directory)

    Returns:
        str: Absolute path
    """
    if path is None:
        return None
    if not os.path.isabs(path) and base_dir:
        return os.path.join(base_dir, path)
    return path


def ensure_dir(path: str):
    """Ensure a directory exists."""

    os.makedirs(path, exist_ok=True)


def is_file_exists(path, logger, base_dir=None):
    """Check if file exists."""
    absolute_path = resolve_path(path, base_dir)
    if os.path.exists(path) or os.path.exists(
        Path(absolute_path if absolute_path else __file__)
    ):
        logger.debug(f"File exists: {path}")
        return True

    logger.error(f"File not found: {path}")
    return False


def append_to_file(path, content: str):
    try:
        if isinstance(path, str):
            path = Path(path)

        if not path.parent.exists():
            os.mkdir(path.parent, 0o700)

        with open(path, "a", encoding="utf-8") as file:
            file.write(content)
    except Exception as exception:
        logger.error(exception)
        raise exception


def write_to_file(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
