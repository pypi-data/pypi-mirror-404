# ///////////////////////////////////////////////////////////////
# EZPL - Core Exceptions
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Core exceptions for Ezpl logging framework.

This module defines all custom exceptions used throughout the application
with detailed error codes for better error tracking and diagnosis.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
# (No standard library imports needed for this module)

# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class EzplError(Exception):
    """
    Base exception class for all Ezpl-related errors.

    All custom exceptions in the Ezpl framework inherit from this base class,
    enabling centralized exception handling and consistent error reporting.
    Each exception includes a message and optional error code for categorization.
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(self, message: str, error_code: str | None = None) -> None:
        """
        Initialize the Ezpl error.

        Args:
            message: Human-readable error message
            error_code: Optional error code for categorization and debugging

        Note:
            Error codes follow the pattern: COMPONENT_ERROR or OPERATION_ERROR
            (e.g., "CONFIG_ERROR", "FILE_ERROR") for consistent error tracking.
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code

    # ///////////////////////////////////////////////////////////////
    # REPRESENTATION METHODS
    # ///////////////////////////////////////////////////////////////

    def __str__(self) -> str:
        """String representation of the error."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ConfigurationError(EzplError):
    """
    Exception raised for configuration-related errors.

    This exception is raised when configuration loading, validation, or processing
    encounters issues. The optional config_key attribute helps identify which
    configuration parameter caused the problem.
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(self, message: str, config_key: str | None = None) -> None:
        """
        Initialize the configuration error.

        Args:
            message: Human-readable error message
            config_key: Optional configuration key that caused the error
        """
        super().__init__(message, "CONFIG_ERROR")
        self.config_key = config_key


class LoggingError(EzplError):
    """
    Exception raised for logging-related errors.

    This exception covers issues with logging operations such as file writing,
    format processing, or handler initialization. The optional handler_type
    attribute identifies which handler (console, file) caused the error.
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(self, message: str, handler_type: str | None = None) -> None:
        """
        Initialize the logging error.

        Args:
            message: Human-readable error message
            handler_type: Optional handler type that caused the error (e.g., "file", "console")
        """
        super().__init__(message, "LOGGING_ERROR")
        self.handler_type = handler_type


class ValidationError(EzplError):
    """
    Exception raised for validation errors.

    This exception is raised when input validation fails (e.g., invalid log levels,
    malformed configuration values). The optional field_name and value attributes
    help identify what was being validated when the error occurred.
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self, message: str, field_name: str | None = None, value: str | None = None
    ) -> None:
        """
        Initialize the validation error.

        Args:
            message: Human-readable error message
            field_name: Optional field name that failed validation
            value: Optional value that failed validation
        """
        super().__init__(message, "VALIDATION_ERROR")
        self.field_name = field_name
        self.value = value


class InitializationError(EzplError):
    """
    Exception raised for initialization errors.

    This exception is raised when Ezpl components fail to initialize properly.
    The optional component attribute identifies which component (printer, logger, config)
    encountered the initialization issue.
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(self, message: str, component: str | None = None) -> None:
        """
        Initialize the initialization error.

        Args:
            message: Human-readable error message
            component: Optional component that failed to initialize
        """
        super().__init__(message, "INIT_ERROR")
        self.component = component


class FileOperationError(EzplError):
    """
    Exception raised for file operation errors.

    This exception covers issues with file operations (reading, writing, creating files).
    The optional file_path and operation attributes help identify which file and
    operation (read, write, create) failed.
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self, message: str, file_path: str | None = None, operation: str | None = None
    ) -> None:
        """
        Initialize the file operation error.

        Args:
            message: Human-readable error message
            file_path: Optional file path that caused the error
            operation: Optional operation that failed (e.g., "read", "write", "create")
        """
        super().__init__(message, "FILE_ERROR")
        self.file_path = file_path
        self.operation = operation


class HandlerError(EzplError):
    """
    Exception raised for handler-related errors.

    This exception covers issues with logging handlers (initialization, configuration,
    operation failures). The optional handler_name attribute identifies which handler
    (EzPrinter, EzLogger) caused the problem.
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(self, message: str, handler_name: str | None = None) -> None:
        """
        Initialize the handler error.

        Args:
            message: Human-readable error message
            handler_name: Optional handler name that caused the error
        """
        super().__init__(message, "HANDLER_ERROR")
        self.handler_name = handler_name
