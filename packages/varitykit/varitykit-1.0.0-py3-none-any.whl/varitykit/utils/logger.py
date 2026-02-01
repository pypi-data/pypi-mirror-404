"""
Logging utilities for VarityKit CLI
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class VarityLogger:
    """Enterprise-grade logger with structured logging support"""

    def __init__(self, name: str = "varitykit", level: str = "INFO", json_format: bool = False):
        self.name = name
        self.level = getattr(logging, level.upper())
        self.json_format = json_format
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Setup logger with appropriate handlers"""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.level)
        logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)

        if self.json_format:
            console_handler.setFormatter(JSONFormatter())
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
            console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

        return logger

    def add_file_handler(self, log_file: Path):
        """Add file handler to logger"""
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(self.level)

        if self.json_format:
            file_handler.setFormatter(JSONFormatter())
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        if kwargs:
            self.logger.debug(message, extra={"data": kwargs})
        else:
            self.logger.debug(message)

    def info(self, message: str, **kwargs):
        """Log info message"""
        if kwargs:
            self.logger.info(message, extra={"data": kwargs})
        else:
            self.logger.info(message)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        if kwargs:
            self.logger.warning(message, extra={"data": kwargs})
        else:
            self.logger.warning(message)

    def error(self, message: str, **kwargs):
        """Log error message"""
        if kwargs:
            self.logger.error(message, extra={"data": kwargs})
        else:
            self.logger.error(message)

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        if kwargs:
            self.logger.critical(message, extra={"data": kwargs})
        else:
            self.logger.critical(message)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra data if present
        if hasattr(record, "data"):
            log_data["data"] = record.data

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


# Global logger instance
_logger: Optional[VarityLogger] = None


def get_logger(level: str = "INFO", json_format: bool = False) -> VarityLogger:
    """Get or create global logger instance"""
    global _logger
    if _logger is None:
        _logger = VarityLogger(level=level, json_format=json_format)
    return _logger


def set_log_level(level: str):
    """Set log level for global logger"""
    logger = get_logger()
    logger.level = getattr(logging, level.upper())
    logger.logger.setLevel(logger.level)
