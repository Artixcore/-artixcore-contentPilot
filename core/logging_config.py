"""Centralized logging with secret sanitization and rotating file handler."""

from __future__ import annotations

import logging
import os
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

from core.utils import SENSITIVE_KEYS, sanitize_text

_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
_LOG_FILE = _LOG_DIR / "contentpilot.log"
_CONFIGURED = False

_SECRET_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9_-]{10,}", re.IGNORECASE),
    re.compile(r"sk-ant-[a-zA-Z0-9_-]{10,}", re.IGNORECASE),
    re.compile(r"Bearer\s+[a-zA-Z0-9._-]+", re.IGNORECASE),
    re.compile(r"Authorization:\s*\S+", re.IGNORECASE),
]


def sanitize_log_message(message: str) -> str:
    """Sanitize a log message before writing."""
    if not message:
        return ""
    text = sanitize_text(str(message))
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("****", text)
    return text


class SanitizingFormatter(logging.Formatter):
    """Formatter that redacts secrets from log records."""

    def format(self, record: logging.LogRecord) -> str:
        if record.msg:
            record.msg = sanitize_log_message(str(record.msg))
        if record.args:
            record.args = tuple(
                sanitize_log_message(str(a)) if isinstance(a, str) else a for a in record.args
            )
        formatted = super().format(record)
        return sanitize_log_message(formatted)


class ContextAdapter(logging.LoggerAdapter):
    """Logger adapter that injects action/request context."""

    def process(self, msg, kwargs):
        ctx = self.extra.get("context", "")
        if ctx:
            return f"[{ctx}] {msg}", kwargs
        return msg, kwargs


def setup_logging(level: str | None = None) -> None:
    """Configure console and rotating file logging."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_level_name = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = SanitizingFormatter(fmt, datefmt=datefmt)

    root = logging.getLogger()
    root.setLevel(log_level)

    console = logging.StreamHandler()
    console.setLevel(log_level)
    console.setFormatter(formatter)
    root.addHandler(console)

    file_handler = RotatingFileHandler(
        _LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    _CONFIGURED = True
    logging.getLogger(__name__).info("Logging initialized (level=%s, file=%s)", log_level_name, _LOG_FILE)


def get_logger(name: str, context: str | None = None) -> logging.Logger | ContextAdapter:
    """Return a logger, optionally wrapped with context."""
    logger = logging.getLogger(name)
    if context:
        return ContextAdapter(logger, {"context": context})
    return logger


def get_log_file_path() -> Path:
    return _LOG_FILE
