"""Structured logging configuration for PydanticAI Masterclass.

This module provides a pre-configured structlog logger that works seamlessly
with Logfire for enhanced observability.
"""

import logging
from typing import Any
import structlog
from structlog.contextvars import merge_contextvars

# Configure structlog with sensible defaults
structlog.configure(
    processors=[
        merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)


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
        self._logger = structlog.get_logger(name)
    
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
