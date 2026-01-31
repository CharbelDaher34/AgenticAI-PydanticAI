"""Common utilities for PydanticAI Masterclass.

This package provides shared utilities used across all lessons:
- Mock database for examples
- Settings and configuration
- Structured logging
- Helper functions
"""

from common.database import MockDatabase, Order, Product, User, mock_db
from common.logging import get_logger, log
from common.settings import Settings, settings

__all__ = [
    "MockDatabase",
    "User",
    "Product",
    "Order",
    "mock_db",
    "Settings",
    "settings",
    "get_logger",
    "log",
]
