# ///////////////////////////////////////////////////////////////
# EZPL - Logger Protocol
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Logger Protocol for Ezpl logging framework.

This module defines the Protocol (abstract interface) that all logger
implementations must follow. It provides type checking and ensures
consistent API across different logger implementations.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

# ///////////////////////////////////////////////////////////////
# PROTOCOLS
# ///////////////////////////////////////////////////////////////


@runtime_checkable
class LoggerProtocol(Protocol):
    """
    Protocol defining the interface for logger implementations.

    All logger implementations must conform to this protocol to ensure
    consistent API and type safety.

    **Required Methods:**
        - Logging methods: info(), debug(), success(), warning(), warn(), error(), critical(), trace(), bind()
        - Utility methods: set_level(), log(), add_separator()
        - Getter methods: get_logger(), get_log_file()

    **Note:**
        This protocol is designed to be compatible with loguru.Logger
        while allowing custom implementations.
    """

    # ///////////////////////////////////////////////////////////////
    # CORE LOGGING METHODS (loguru-compatible)
    # ///////////////////////////////////////////////////////////////

    def trace(self, message: Any, *args, **kwargs) -> None:
        """Log a trace message."""
        ...

    def debug(self, message: Any, *args, **kwargs) -> None:
        """Log a debug message."""
        ...

    def info(self, message: Any, *args, **kwargs) -> None:
        """Log an info message."""
        ...

    def success(self, message: Any, *args, **kwargs) -> None:
        """Log a success message."""
        ...

    def warning(self, message: Any, *args, **kwargs) -> None:
        """Log a warning message."""
        ...

    def warn(self, message: Any, *args, **kwargs) -> None:
        """Alias for warning(). Log a warning message."""
        ...

    def error(self, message: Any, *args, **kwargs) -> None:
        """Log an error message."""
        ...

    def critical(self, message: Any, *args, **kwargs) -> None:
        """Log a critical message."""
        ...

    def exception(self, message: Any, *args, **kwargs) -> None:
        """Log an exception with traceback."""
        ...

    # ///////////////////////////////////////////////////////////////
    # LOGURU-SPECIFIC METHODS
    # ///////////////////////////////////////////////////////////////

    def bind(self, **kwargs) -> Any:
        """Bind context variables to the logger."""
        ...

    def opt(self, **kwargs) -> Any:
        """Configure logger options."""
        ...

    def patch(self, patcher) -> Any:
        """Patch log records."""
        ...

    # ///////////////////////////////////////////////////////////////
    # EZPL-SPECIFIC METHODS
    # ///////////////////////////////////////////////////////////////

    def set_level(self, level: str) -> None:
        """Set the logging level."""
        ...

    def log(self, level: str, message: Any) -> None:
        """Log a message with specified level."""
        ...

    def add_separator(self) -> None:
        """Add a session separator to the log file."""
        ...

    def get_log_file(self) -> Path:
        """Get the current log file path."""
        ...

    def close(self) -> None:
        """Close the logger and release resources."""
        ...
