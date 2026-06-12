from __future__ import annotations

import logging
import logging.config
from pathlib import Path

from app.core.config import settings


def setup_logging() -> None:
    """Configure application logging for console and optional daily file output."""
    level = settings.log_level.upper()
    handlers = ["console"]

    if settings.log_file_enabled:
        Path(settings.log_dir).mkdir(parents=True, exist_ok=True)
        handlers.append("file")

    handler_config: dict[str, dict] = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": level,
        },
    }
    if settings.log_file_enabled:
        handler_config["file"] = {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "formatter": "standard",
            "level": level,
            "filename": str(Path(settings.log_dir) / "app.log"),
            "when": "midnight",
            "backupCount": settings.log_retention_days,
            "encoding": "utf-8",
            "utc": True,
        }

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                    "datefmt": "%Y-%m-%dT%H:%M:%S%z",
                },
            },
            "handlers": handler_config,
            "root": {
                "level": level,
                "handlers": handlers,
            },
            "loggers": {
                "uvicorn": {
                    "level": level,
                    "handlers": handlers,
                    "propagate": False,
                },
                "uvicorn.error": {
                    "level": level,
                    "handlers": handlers,
                    "propagate": False,
                },
                "uvicorn.access": {
                    "level": level,
                    "handlers": handlers,
                    "propagate": False,
                },
            },
        }
    )
