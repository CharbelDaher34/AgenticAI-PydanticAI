"""Structured logging configuration for PydanticAI Masterclass.

This module provides a pre-configured structlog logger that works seamlessly
with Logfire for enhanced observability.
"""

import logging
from typing import Any
import structlog
from structlog.dev import ConsoleRenderer
from structlog.contextvars import merge_contextvars

import sys

class CustomConsoleRenderer:
    """Custom renderer for terminal output that formats logs in a YAML-like style with indentation."""
    
    def __call__(self, logger: logging.Logger, name: str, event_dict: dict[str, Any]) -> str:
        # Extract standard fields
        # Use Title case for the header (e.g. "Info", "Error")
        level = event_dict.pop("level", "info").title()
        event = event_dict.pop("event", "")
        timestamp = event_dict.pop("timestamp", None)
        
        # Build the output string - Header is the level
        lines = [f"{level}:"]
        
        # Common indentation
        indent = "  "
        
        # Prioritize event and timestamp
        if event:
            lines.append(f"{indent}event: {event}")
            
        if timestamp:
            lines.append(f"{indent}timestamp: {timestamp}")
            
        def _format_value(value: Any, current_indent: int) -> list[str]:
            """Recursively format values with indentation."""
            result = []
            if isinstance(value, dict):
                for k, v in value.items():
                    if isinstance(v, (dict, list)):
                        result.append(f"{' ' * current_indent}{k}:")
                        result.extend(_format_value(v, current_indent + 2))
                    else:
                        result.append(f"{' ' * current_indent}{k}: {v}")
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, (dict, list)):
                        result.append(f"{' ' * current_indent}-")
                        result.extend(_format_value(item, current_indent + 2))
                    else:
                        result.append(f"{' ' * current_indent}- {item}")
            else:
                result.append(f"{' ' * current_indent}{value}")
            return result

        # Format remaining context variables
        for key, value in event_dict.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{indent}{key}:")
                lines.extend(_format_value(value, len(indent) + 2))
            else:
                lines.append(f"{indent}{key}: {value}")
                
        # Join lines with a visual separator prefix
        return "\n".join(f"│ {line}" for line in lines)


def configure_logging() -> None:
    """Configure structured logging with dual output: JSON to file, YAML-like to console."""
    # Configure standard logging
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid implementation duplication
    root_logger.handlers = []
    
    # 1. File Handler - output as JSON (normally)
    file_handler = logging.FileHandler("pydanticai.log")
    json_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
    )
    file_handler.setFormatter(json_formatter)
    root_logger.addHandler(file_handler)
    
    # 2. Console Handler - output in custom flat/indented format
    console_handler = logging.StreamHandler(sys.stdout)
    custom_formatter = structlog.stdlib.ProcessorFormatter(
        processor=CustomConsoleRenderer(),
    )
    console_handler.setFormatter(custom_formatter)
    root_logger.addHandler(console_handler)
    
    # Configure structlog to wrap standard logging
    structlog.configure(
        processors=[
            merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

# Apply configuration
configure_logging()


class Logger:
    """Wrapper class for structured logging with context variable support.
    
    Example:
        ```python
        from common.logging import Logger
        
        log = Logger(__name__)
        log.info("agent_started", user_id=123, task="summarize")
        
        # With context variables
        log.bind_contextvars(request_id="req_123")
        log.info("processing")  # Will include request_id
        log.clear_contextvars()
        ```
    """
    
    def __init__(self, name: str = __name__):
        """Initialize logger with given name.
        
        Args:
            name: Logger name, typically __name__ of the calling module
        """
        # structlog.stdlib.get_logger() returns a BoundLogger that wraps a standard logger
        self._logger = structlog.stdlib.get_logger(name)
    
    def info(self, event: str, **kwargs: Any) -> None:
        """Log an info message.
        
        Args:
            event: Event name/message
            **kwargs: Additional context key-value pairs
        """
        self._logger.info(event, **kwargs)
    
    def debug(self, event: str, **kwargs: Any) -> None:
        """Log a debug message.
        
        Args:
            event: Event name/message
            **kwargs: Additional context key-value pairs
        """
        self._logger.debug(event, **kwargs)
    
    def warning(self, event: str, **kwargs: Any) -> None:
        """Log a warning message.
        
        Args:
            event: Event name/message
            **kwargs: Additional context key-value pairs
        """
        self._logger.warning(event, **kwargs)
    
    def error(self, event: str, **kwargs: Any) -> None:
        """Log an error message.
        
        Args:
            event: Event name/message
            **kwargs: Additional context key-value pairs
        """
        self._logger.error(event, **kwargs)
    
    def exception(self, event: str, **kwargs: Any) -> None:
        """Log an exception with traceback.
        
        Args:
            event: Event name/message
            **kwargs: Additional context key-value pairs
        """
        self._logger.exception(event, **kwargs)
    
    @staticmethod
    def bind_contextvars(**kwargs: Any) -> None:
        """Bind context variables to all subsequent log messages.
        
        Args:
            **kwargs: Key-value pairs to bind to the context
        """
        structlog.contextvars.bind_contextvars(**kwargs)
    
    @staticmethod
    def clear_contextvars() -> None:
        """Clear all bound context variables."""
        structlog.contextvars.clear_contextvars()


def get_logger(name: str = __name__) -> Logger:
    """Get a configured Logger instance.
    
    Args:
        name: Logger name, typically __name__ of the calling module
        
    Returns:
        Configured Logger instance
        
    Example:
        ```python
        from common.logging import get_logger
        
        log = get_logger(__name__)
        log.info("agent_started", user_id=123, task="summarize")
        ```
    """
    return Logger(name)


# Default logger instance
log = get_logger(__name__)

# Export public API
__all__ = ["Logger", "get_logger", "log"]
