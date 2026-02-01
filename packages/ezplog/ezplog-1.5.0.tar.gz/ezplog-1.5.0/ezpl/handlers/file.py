# ///////////////////////////////////////////////////////////////
# EZPL - File Logger Handler
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
File logger handler for Ezpl logging framework.

This module provides a file-based logging handler with advanced formatting,
session separation, and structured output.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
from datetime import datetime
from pathlib import Path
from typing import Any

# Third-party imports
from loguru import logger
from loguru._logger import Logger as LoguruLogger

# Local imports
from ..core.exceptions import FileOperationError, LoggingError, ValidationError
from ..core.interfaces import LoggingHandler
from ..types.enums import LogLevel
from .utils import safe_str_convert, sanitize_for_file

# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class EzLogger(LoggingHandler):
    """
    File logger handler with advanced formatting and session management.

    This handler provides file-based logging with:
    - Structured log format
    - Session separators
    - HTML tag sanitization
    - Automatic file creation
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self,
        log_file: Path | str,
        level: str = "INFO",
        rotation: str | None = None,
        retention: str | None = None,
        compression: str | None = None,
    ) -> None:
        """
        Initialize the file logger handler.

        Args:
            log_file: Path to the log file
            level: The desired logging level
            rotation: Rotation size (e.g., "10 MB") or time (e.g., "1 day")
            retention: Retention period (e.g., "7 days")
            compression: Compression format (e.g., "zip", "gz")

        Raises:
            ValidationError: If the provided level is invalid
            FileOperationError: If file operations fail
        """
        if not LogLevel.is_valid_level(level):
            raise ValidationError(f"Invalid log level: {level}", "level", level)

        self._level = level.upper()
        self._log_file = Path(log_file)
        self._logger = logger.bind(task="logger")
        self._logger_id: int | None = None
        self._rotation = rotation
        self._retention = retention
        self._compression = compression

        # Valider et créer le répertoire parent
        try:
            self._log_file.parent.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            raise FileOperationError(
                f"Cannot create log directory: {e}",
                str(self._log_file.parent),
                "create_directory",
            ) from e

        # Valider que le fichier peut être créé/écrit
        try:
            if not self._log_file.exists():
                self._log_file.touch()
            # Test d'écriture
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write("")
        except (PermissionError, OSError) as e:
            raise FileOperationError(
                f"Cannot write to log file: {e}", str(self._log_file), "write"
            ) from e

        self._initialize_logger()

    # ------------------------------------------------
    # PRIVATE HELPER METHODS
    # ------------------------------------------------

    def _initialize_logger(self) -> None:
        """
        Initialize the file logger handler.

        Raises:
            LoggingError: If logger initialization fails
        """
        try:
            # Remove existing handler if any
            logger_id: int | None = self._logger_id
            if logger_id is not None:
                self._logger.remove(logger_id)

            # Call loguru.add() with keyword arguments directly
            # Note: loguru.add() accepts keyword arguments, not a dict
            self._logger_id = self._logger.add(
                sink=self._log_file,
                level=self._level,
                format=self._custom_formatter,  # type: ignore[arg-type]
                filter=lambda record: record["extra"]["task"] == "logger",
                encoding="utf-8",
                rotation=self._rotation if self._rotation else None,
                retention=self._retention if self._retention else None,
                compression=self._compression if self._compression else None,
            )
        except Exception as e:
            raise LoggingError(f"Failed to initialize file logger: {e}", "file") from e

    # ///////////////////////////////////////////////////////////////
    # UTILS METHODS
    # ///////////////////////////////////////////////////////////////

    def set_level(self, level: str) -> None:
        """
        Set the logging level.

        Args:
            level: The desired logging level

        Raises:
            ValidationError: If the provided level is invalid
            LoggingError: If level update fails
        """
        if not LogLevel.is_valid_level(level):
            raise ValidationError(f"Invalid log level: {level}", "level", level)

        try:
            self._level = level.upper()
            self._initialize_logger()
        except Exception as e:
            raise LoggingError(f"Failed to update log level: {e}", "file") from e

    def log(self, level: str, message: Any) -> None:
        """
        Log a message with the specified level.

        Args:
            level: The log level
            message: The message to log (any type, will be converted to string)

        Raises:
            ValidationError: If the level is invalid
            LoggingError: If logging fails
        """
        if not LogLevel.is_valid_level(level):
            raise ValidationError(f"Invalid log level: {level}", "level", level)

        # Convertir message en string de manière robuste
        message = safe_str_convert(message)

        try:
            log_method = getattr(self._logger, level.lower())
            log_method(message)
        except Exception as e:
            raise LoggingError(f"Failed to log message: {e}", "file") from e

    # ///////////////////////////////////////////////////////////////
    # LOGGING METHODS (API primaire - delegates to loguru)
    # ///////////////////////////////////////////////////////////////

    def trace(self, message: Any, *args, **kwargs) -> None:
        """Log a trace message."""
        message = safe_str_convert(message)
        self._logger.trace(message, *args, **kwargs)

    def debug(self, message: Any, *args, **kwargs) -> None:
        """Log a debug message."""
        message = safe_str_convert(message)
        self._logger.debug(message, *args, **kwargs)

    def info(self, message: Any, *args, **kwargs) -> None:
        """Log an info message."""
        message = safe_str_convert(message)
        self._logger.info(message, *args, **kwargs)

    def success(self, message: Any, *args, **kwargs) -> None:
        """Log a success message."""
        message = safe_str_convert(message)
        self._logger.success(message, *args, **kwargs)

    def warning(self, message: Any, *args, **kwargs) -> None:
        """Log a warning message."""
        message = safe_str_convert(message)
        self._logger.warning(message, *args, **kwargs)

    def warn(self, message: Any, *args, **kwargs) -> None:
        """Alias for warning(). Log a warning message."""
        self.warning(message, *args, **kwargs)

    def error(self, message: Any, *args, **kwargs) -> None:
        """Log an error message."""
        message = safe_str_convert(message)
        self._logger.error(message, *args, **kwargs)

    def critical(self, message: Any, *args, **kwargs) -> None:
        """Log a critical message."""
        message = safe_str_convert(message)
        self._logger.critical(message, *args, **kwargs)

    def exception(self, message: Any, *args, **kwargs) -> None:
        """Log an exception with traceback."""
        message = safe_str_convert(message)
        self._logger.exception(message, *args, **kwargs)

    # ///////////////////////////////////////////////////////////////
    # LOGURU-SPECIFIC METHODS (delegation)
    # ///////////////////////////////////////////////////////////////

    def bind(self, **kwargs: Any) -> LoguruLogger:
        """Bind context variables to the logger."""
        return self._logger.bind(**kwargs)  # type: ignore[return-value]

    def opt(self, **kwargs: Any) -> LoguruLogger:
        """Configure logger options."""
        return self._logger.opt(**kwargs)  # type: ignore[return-value]

    def patch(self, patcher: Any) -> LoguruLogger:
        """Patch log records."""
        return self._logger.patch(patcher)  # type: ignore[return-value]

    # ///////////////////////////////////////////////////////////////
    # GETTER - Returns the underlying loguru logger for advanced usage
    # ///////////////////////////////////////////////////////////////

    def get_loguru(self) -> LoguruLogger:
        """
        Get the underlying Loguru logger instance for advanced usage.

        **Returns:**

            * loguru.Logger: The loguru logger instance

        **Raises:**

            * LoggingError: If the logger is not initialized
        """
        if not self._logger:
            raise LoggingError("File logger not initialized", "file")
        return self._logger  # type: ignore[return-value]

    def get_log_file(self) -> Path:
        """
        Get the current log file path.

        Returns:
            Path to the log file
        """
        return self._log_file

    def get_file_size(self) -> int:
        """
        Get the current log file size in bytes.

        Returns:
            File size in bytes, or 0 if file doesn't exist or error occurs
        """
        try:
            if self._log_file.exists():
                return self._log_file.stat().st_size
            return 0
        except Exception:
            return 0

    def close(self) -> None:
        """
        Close the logger handler and release file handles.

        This method removes the loguru handler to release file handles,
        which is especially important on Windows where files can remain locked.
        """
        try:
            # Remove existing handler if any
            logger_id: int | None = self._logger_id
            if logger_id is not None:
                # Remove the specific handler
                self._logger.remove(logger_id)
                self._logger_id = None

                # Force flush and close on Windows
                import sys
                import time

                if sys.platform == "win32":
                    # Force garbage collection to release file handles
                    import gc

                    gc.collect()
                    # Give Windows time to release file locks
                    time.sleep(0.1)
        except Exception as e:
            raise LoggingError("Failed to close logger", "file") from e

    # ///////////////////////////////////////////////////////////////
    # FILE OPERATIONS
    # ///////////////////////////////////////////////////////////////

    def add_separator(self) -> None:
        """
        Add a separator line to the log file for session distinction.

        Raises:
            FileOperationError: If writing to the log file fails
        """
        try:
            current_time = datetime.now().strftime("%Y-%m-%d - %H:%M")
            separator = f"\n\n## ==> {current_time}\n## /////////////////////////////////////////////////////////////////\n"
            with open(self._log_file, "a", encoding="utf-8") as log_file:
                log_file.write(separator)
        except Exception as e:
            raise FileOperationError(
                f"Failed to add separator to log file: {e}",
                str(self._log_file),
                "write",
            ) from e

    # ///////////////////////////////////////////////////////////////
    # FORMATTING METHODS
    # ///////////////////////////////////////////////////////////////

    def _custom_formatter(self, record: dict[str, Any]) -> str:
        """
        Custom formatter for file output.

        Args:
            record: Loguru record to format

        Returns:
            Formatted log message (toujours retourne une string, ne lève jamais d'exception)
        """
        try:
            level = (
                record.get("level", {}).name
                if hasattr(record.get("level", {}), "name")
                else "INFO"
            )
            log_level = LogLevel[level]
            return self._format_message(record, log_level)
        except Exception as e:
            # Ne jamais lever d'exception dans un formatter - retourner un message d'erreur sécurisé
            try:
                return f"????-??-?? ??:??:?? | FORMAT_ERR | unknown:unknown:? - [FORMAT ERROR: {type(e).__name__}]\n"
            except Exception:
                return "????-??-?? ??:??:?? | FORMAT_ERR | unknown:unknown:? - [FORMAT ERROR]\n"

    def _format_message(self, record: dict[str, Any], log_level: LogLevel) -> str:
        """
        Format a log message for file output.

        Args:
            record: Loguru record
            log_level: LogLevel enum instance

        Returns:
            Formatted log message (toujours retourne une string valide)
        """
        try:
            # Sécuriser le formatage du timestamp
            try:
                time_obj: Any = record.get("time")
                # Check if time_obj is a datetime-like object with strftime
                if time_obj is not None:
                    strftime_method = getattr(time_obj, "strftime", None)
                    if strftime_method is not None and callable(strftime_method):
                        # Safe to call strftime - time_obj is datetime-like
                        timestamp = strftime_method("%Y-%m-%d %H:%M:%S")
                    else:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                timestamp = "????-??-?? ??:??:??"

            # Nettoyer le message de manière robuste
            message = safe_str_convert(record.get("message", ""))
            # Sanitizer pour fichier (supprime caractères problématiques)
            message = sanitize_for_file(message)

            # Nettoyer le nom de fonction
            fn = str(record.get("function", "unknown"))
            fn = fn.replace("<", "").replace(">", "")

            # Sécuriser module et line
            module = str(record.get("module", "unknown"))
            line = str(record.get("line", "?"))

            return (
                f"{timestamp} | "
                f"{log_level.label:<10} | "
                f"{module}:{fn}:{line} - "
                f"{message}\n"
            )
        except Exception as e:
            # Fallback sécurisé
            try:
                return f"????-??-?? ??:??:?? | FORMAT_ERR | unknown:unknown:? - [FORMAT ERROR: {type(e).__name__}]\n"
            except Exception:
                return "????-??-?? ??:??:?? | FORMAT_ERR | unknown:unknown:? - [FORMAT ERROR]\n"

    # ///////////////////////////////////////////////////////////////
    # REPRESENTATION METHODS
    # ///////////////////////////////////////////////////////////////

    def __str__(self) -> str:
        """String representation of the file logger."""
        return f"EzLogger(file={self._log_file}, level={self._level})"

    def __repr__(self) -> str:
        """Detailed string representation of the file logger."""
        return f"EzLogger(file={self._log_file}, level={self._level}, logger_id={self._logger_id})"
