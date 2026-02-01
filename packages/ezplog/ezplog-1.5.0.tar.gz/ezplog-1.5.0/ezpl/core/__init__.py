# ///////////////////////////////////////////////////////////////
# EZPL - Core Module
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Core module for Ezpl logging framework.

This module exports core interfaces (protocols and abstract base classes)
and custom exception types used throughout the Ezpl framework.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Local imports
from .exceptions import (
    ConfigurationError,
    EzplError,
    FileOperationError,
    HandlerError,
    InitializationError,
    LoggingError,
    ValidationError,
)
from .interfaces import (
    ConfigurationManager,
    IndentationManager,
    LoggingHandler,
)

# ///////////////////////////////////////////////////////////////
# PUBLIC API
# ///////////////////////////////////////////////////////////////

__all__ = [
    # Protocols (structural typing interfaces)
    "LoggingHandler",
    "IndentationManager",
    "ConfigurationManager",
    # Custom exceptions
    "EzplError",
    "ConfigurationError",
    "LoggingError",
    "ValidationError",
    "InitializationError",
    "FileOperationError",
    "HandlerError",
]
