"""
OR-AF Logger

Configurable logging system for the framework.
"""

import logging
import sys
from typing import Optional
from enum import Enum


class LogLevel(str, Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ORLogger:
    """
    Custom logger for OR-AF framework.
    
    Provides consistent logging across the framework with
    configurable output and formatting.
    """
    
    def __init__(
        self,
        name: str = "or-af",
        level: LogLevel = LogLevel.INFO,
        format_string: Optional[str] = None
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.value))
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, level.value))
        
        # Create formatter
        format_str = format_string or "%(asctime)s | %(levelname)s | %(message)s"
        formatter = logging.Formatter(format_str, datefmt="%H:%M:%S")
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
    
    def set_level(self, level: LogLevel) -> None:
        """Set log level"""
        self.logger.setLevel(getattr(logging, level.value))
        for handler in self.logger.handlers:
            handler.setLevel(getattr(logging, level.value))
    
    def debug(self, message: str, *args, **kwargs) -> None:
        """Log debug message"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs) -> None:
        """Log info message"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs) -> None:
        """Log warning message"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs) -> None:
        """Log error message"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs) -> None:
        """Log critical message"""
        self.logger.critical(message, *args, **kwargs)


# Default logger instance
default_logger = ORLogger()


def get_logger(name: str = "or-af", level: LogLevel = LogLevel.INFO) -> ORLogger:
    """Get a logger instance"""
    return ORLogger(name=name, level=level)


def set_log_level(level: LogLevel) -> None:
    """Set the default logger level"""
    default_logger.set_level(level)
