"""
LOGGING CONFIGURATION — Centralized logging for the Cognitive Market Engine.

Usage:
    from config.logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("Processing news event")
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler

_CONFIGURED = False


def setup_logging(
    level: str = "INFO",
    log_file: str = None,
    max_bytes: int = 5 * 1024 * 1024,     # 5 MB
    backup_count: int = 3,
    console: bool = True,
):
    """
    Configure project-wide logging.

    Call once at startup (main.py bootstrap or tests).
    Subsequent calls are ignored.

    Args:
        level: Root log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file (None = console only)
        max_bytes: Max size per log file before rotation
        backup_count: Number of rotated backups to keep
        console: Whether to also log to stderr
    """
    global _CONFIGURED
    if _CONFIGURED:
        return
    _CONFIGURED = True

    root = logging.getLogger("cme")          # project root logger
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.propagate = False

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-7s %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    if console:
        ch = logging.StreamHandler(sys.stderr)
        ch.setFormatter(fmt)
        root.addHandler(ch)

    # File handler (with rotation)
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        fh = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        fh.setFormatter(fmt)
        root.addHandler(fh)

    # Silence noisy third-party loggers
    for noisy in ("urllib3", "requests", "chardet", "feedparser"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger under the 'cme' namespace.

    Example:
        logger = get_logger("engine.cognitive")
        # produces logger named "cme.engine.cognitive"
    """
    return logging.getLogger(f"cme.{name}")
