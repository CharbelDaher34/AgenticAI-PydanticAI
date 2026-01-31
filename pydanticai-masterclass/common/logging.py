"""Structured logging configuration for PydanticAI Masterclass.

This module provides a pre-configured structlog logger that works seamlessly
with Logfire for enhanced observability.
"""

import logging
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


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    """Get a configured structlog logger.
    
    Args:
        name: Logger name, typically __name__ of the calling module
        
    Returns:
        Configured structlog logger instance
        
    Example:
        ```python
        from common.logging import get_logger
        
        log = get_logger(__name__)
        log.info("agent_started", user_id=123, task="summarize")
        ```
    """
    return structlog.get_logger(name)


# Default logger instance
log = get_logger(__name__)
