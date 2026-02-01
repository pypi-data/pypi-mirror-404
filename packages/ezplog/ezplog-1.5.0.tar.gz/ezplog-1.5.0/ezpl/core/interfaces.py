# ///////////////////////////////////////////////////////////////
# EZPL - Core Interfaces
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Core interfaces for Ezpl logging framework.

This module defines the core abstract base classes and protocols used
throughout the application. ABCs provide strict interfaces with runtime
enforcement for handler implementations, while Protocols provide structural
typing for flexible, duck-typed configuration management.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any, Protocol

# ///////////////////////////////////////////////////////////////
# ABSTRACT BASE CLASSES
# ///////////////////////////////////////////////////////////////


class LoggingHandler(ABC):
    """
    Abstract base class for logging handlers.

    All logging handlers (EzPrinter, EzLogger) must inherit from this class
    and implement the required methods.
    """

    @abstractmethod
    def log(self, level: str, message: str) -> None:
        """Log a message with the specified level."""
        ...

    @abstractmethod
    def set_level(self, level: str) -> None:
        """Set the logging level."""
        ...


class IndentationManager(ABC):
    """
    Abstract base class for indentation management.

    Handlers that support indentation (e.g., EzPrinter) must inherit from
    this class and implement the required methods.
    """

    @abstractmethod
    def get_indent(self) -> str:
        """Get the current indentation string."""
        ...

    @abstractmethod
    def add_indent(self) -> None:
        """Increase the indentation level."""
        ...

    @abstractmethod
    def del_indent(self) -> None:
        """Decrease the indentation level."""
        ...

    @abstractmethod
    def reset_indent(self) -> None:
        """Reset the indentation level to zero."""
        ...

    @abstractmethod
    def manage_indent(self) -> AbstractContextManager[None]:
        """Context manager for temporary indentation."""
        ...


# ///////////////////////////////////////////////////////////////
# PROTOCOLS
# ///////////////////////////////////////////////////////////////


class ConfigurationManager(Protocol):
    """
    Protocol for configuration management.

    This structural typing protocol defines the interface for configuration
    managers. Implementations can support different configuration sources
    (files, environment, in-memory) without coupling to a specific backend.
    """

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        ...

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        ...

    def get_log_level(self) -> str:
        """Get the current log level."""
        ...

    def get_log_file(self) -> Path:
        """Get the current log file path."""
        ...

    def get_printer_level(self) -> str:
        """Get the current printer level."""
        ...

    def get_file_logger_level(self) -> str:
        """Get the current file logger level."""
        ...

    def save(self) -> None:
        """Save configuration to file."""
        ...
