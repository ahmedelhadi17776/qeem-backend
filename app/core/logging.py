"""Logging configuration utilities.

Provides a helper to configure JSON or text logging format based on environment.
"""

import json
import logging
import logging.config
from typing import Literal


def configure_logging(
    level: str, fmt: Literal["json", "text"] = "text", color: bool = False
) -> None:
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    handler = logging.StreamHandler()
    if fmt == "json":

        class JsonFormatter(logging.Formatter):
            # type: ignore[override]
            def format(self, record: logging.LogRecord) -> str:
                payload = {
                    "level": record.levelname,
                    "name": record.name,
                    "message": record.getMessage(),
                }
                return json.dumps(payload)

        handler.setFormatter(JsonFormatter())
    else:
        if color:

            class ColorFormatter(logging.Formatter):
                COLORS = {
                    "DEBUG": "\033[36m",
                    "INFO": "\033[32m",
                    "WARNING": "\033[33m",
                    "ERROR": "\033[31m",
                    "CRITICAL": "\033[35m",
                }
                RESET = "\033[0m"

                # type: ignore[override]
                def format(self, record: logging.LogRecord) -> str:
                    color_code = self.COLORS.get(record.levelname, "")
                    msg = f"{record.levelname} {record.name}: {record.getMessage()}"
                    return f"{color_code}{msg}{self.RESET}"

            handler.setFormatter(ColorFormatter())
        else:
            handler.setFormatter(
                logging.Formatter("%(levelname)s %(name)s: %(message)s")
            )

    # reset handlers to avoid duplicates on reload
    logger.handlers = [handler]


def configure_uvicorn_json_logging(level: str) -> None:
    """Route uvicorn loggers through the JSON formatter."""
    json_formatter = {
        "()": "logging.Formatter",
        "format": "%(levelname)s %(name)s: %(message)s",
    }

    class JsonFormatter(logging.Formatter):
        # type: ignore[override]
        def format(self, record: logging.LogRecord) -> str:
            payload = {
                "level": record.levelname,
                "name": record.name,
                "message": record.getMessage(),
            }
            return json.dumps(payload)

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": JsonFormatter,
                },
            },
            "handlers": {
                "json": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "stream": "ext://sys.stdout",
                }
            },
            "loggers": {
                "uvicorn": {
                    "handlers": ["json"],
                    "level": level.upper(),
                    "propagate": False,
                },
                "uvicorn.error": {
                    "handlers": ["json"],
                    "level": level.upper(),
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["json"],
                    "level": level.upper(),
                    "propagate": False,
                },
            },
        }
    )


def configure_uvicorn_text_logging(level: str, color: bool = True) -> None:
    class PlainFormatter(logging.Formatter):
        # type: ignore[override]
        def format(self, record: logging.LogRecord) -> str:
            return f"{record.levelname} {record.name}: {record.getMessage()}"

    class ColorFormatter(logging.Formatter):
        COLORS = {
            "DEBUG": "\033[36m",
            "INFO": "\033[32m",
            "WARNING": "\033[33m",
            "ERROR": "\033[31m",
            "CRITICAL": "\033[35m",
        }
        RESET = "\033[0m"

        # type: ignore[override]
        def format(self, record: logging.LogRecord) -> str:
            color_code = self.COLORS.get(record.levelname, "")
            msg = f"{record.levelname} {record.name}: {record.getMessage()}"
            return f"{color_code}{msg}{self.RESET}"

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "text": {"()": ColorFormatter if color else PlainFormatter},
            },
            "handlers": {
                "text": {
                    "class": "logging.StreamHandler",
                    "formatter": "text",
                    "stream": "ext://sys.stdout",
                }
            },
            "loggers": {
                "uvicorn": {
                    "handlers": ["text"],
                    "level": level.upper(),
                    "propagate": False,
                },
                "uvicorn.error": {
                    "handlers": ["text"],
                    "level": level.upper(),
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["text"],
                    "level": level.upper(),
                    "propagate": False,
                },
            },
        }
    )
