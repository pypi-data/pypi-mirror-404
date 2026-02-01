# ///////////////////////////////////////////////////////////////
# EZPL - Main logging singleton
# Project: ezpl
# ///////////////////////////////////////////////////////////////

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import sys
import threading
import warnings
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

# Third-party imports
from loguru import logger

# Local imports
from .config import ConfigurationManager
from .handlers import EzLogger, EzPrinter

# ///////////////////////////////////////////////////////////////
# GLOBALS
# ///////////////////////////////////////////////////////////////

APP_PATH = Path(sys.argv[0]).parent

# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class Ezpl:
    _instance: Ezpl | None = None
    _lock: threading.Lock = threading.Lock()
    _config_locked: bool = False
    _log_file: Path
    _printer: EzPrinter
    _logger: EzLogger
    _config_manager: ConfigurationManager

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    @classmethod
    def is_initialized(cls) -> bool:
        """
        Return True if the Ezpl singleton has already been created.

        Useful for libraries that want to know whether they are the first
        to initialize Ezpl or if they should avoid re-configuring it.
        """
        return cls._instance is not None

    def __new__(
        cls,
        log_file: Path | str | None = None,
        log_level: str | None = None,
        printer_level: str | None = None,
        file_logger_level: str | None = None,
        log_rotation: str | None = None,
        log_retention: str | None = None,
        log_compression: str | None = None,
        indent_step: int | None = None,
        indent_symbol: str | None = None,
        base_indent_symbol: str | None = None,
    ) -> Ezpl:
        """
        Creates and returns a new instance of Ezpl if none exists.

        **Notes:**
        Ensures only one instance of Ezpl exists (Singleton pattern).

        **Priority order for configuration (for each parameter):**
        1. Arguments passed directly (highest priority)
        2. Environment variables (EZPL_*)
        3. Configuration file (~/.ezpl/config.json)
        4. Default values (lowest priority)

        **Args:**

            * `log_file` (Path | str, optional): Path to the log file
            * `log_level` (str, optional): Global log level (applies to both printer and logger)
            * `printer_level` (str, optional): Printer log level
            * `file_logger_level` (str, optional): File logger level
            * `log_rotation` (str, optional): Rotation setting (e.g., "10 MB", "1 day")
            * `log_retention` (str, optional): Retention period (e.g., "7 days")
            * `log_compression` (str, optional): Compression format (e.g., "zip", "gz")
            * `indent_step` (int, optional): Indentation step size
            * `indent_symbol` (str, optional): Symbol for indentation
            * `base_indent_symbol` (str, optional): Base indentation symbol

        **Returns:**

            * `Ezpl`: The singleton instance of the Ezpl class.

        **Raises:**

            * `None`.
        """

        # //////
        # Double-checked locking pattern for thread-safe singleton
        if cls._instance is None:
            with cls._lock:
                # Check again after acquiring lock (double-checked locking)
                if cls._instance is None:
                    logger.remove()

                    # Initialize configuration manager
                    cls._config_manager = ConfigurationManager()

                    # Determine configuration values with priority: arg > env > config file > default
                    # Helper function to get value with priority order
                    def get_config_value(
                        arg_value, config_key: str, getter_method
                    ) -> Any:
                        """
                        Get configuration value with priority: arg > env > config file > default

                        Args:
                            arg_value: Value from argument (can be None)
                            config_key: Configuration key name
                            getter_method: Method to get default value from config manager

                        Returns:
                            Final configuration value
                        """
                        # Priority 1: Argument direct
                        if arg_value is not None:
                            return arg_value

                        # Priority 2: Environment variable (already loaded in config_manager)
                        # Priority 3: Config file (already loaded in config_manager)
                        # Priority 4: Default (via getter method)
                        # The config_manager already has the correct priority (env > file > default)
                        config_value = cls._config_manager.get(config_key)
                        if config_value is not None:
                            return config_value

                        # Fallback to default via getter
                        return getter_method()

                    # Log file
                    if log_file:
                        cls._log_file = Path(log_file)
                    else:
                        cls._log_file = cls._config_manager.get_log_file()

                    # Log level (global)
                    final_log_level = get_config_value(
                        log_level, "log-level", cls._config_manager.get_log_level
                    )

                    # Printer level
                    final_printer_level = get_config_value(
                        printer_level,
                        "printer-level",
                        cls._config_manager.get_printer_level,
                    )

                    # File logger level
                    final_file_logger_level = get_config_value(
                        file_logger_level,
                        "file-logger-level",
                        cls._config_manager.get_file_logger_level,
                    )

                    # Rotation settings (can be None)
                    # Priority: arg > env > config file > default
                    # Note: If arg is None (default), we check env/config/default
                    # If user wants to explicitly set None, they can pass None or use configure()
                    final_rotation = (
                        log_rotation
                        if log_rotation is not None
                        else cls._config_manager.get_log_rotation()
                    )
                    final_retention = (
                        log_retention
                        if log_retention is not None
                        else cls._config_manager.get_log_retention()
                    )
                    final_compression = (
                        log_compression
                        if log_compression is not None
                        else cls._config_manager.get_log_compression()
                    )

                    # Indent settings
                    final_indent_step = get_config_value(
                        indent_step, "indent-step", cls._config_manager.get_indent_step
                    )
                    final_indent_symbol = get_config_value(
                        indent_symbol,
                        "indent-symbol",
                        cls._config_manager.get_indent_symbol,
                    )
                    final_base_indent_symbol = get_config_value(
                        base_indent_symbol,
                        "base-indent-symbol",
                        cls._config_manager.get_base_indent_symbol,
                    )

                    instance = object.__new__(cls)
                    assert isinstance(instance, Ezpl)
                    cls._instance = instance

                    # Initialize printer with resolved configuration
                    cls._printer = EzPrinter(
                        level=final_printer_level,
                        indent_step=final_indent_step,
                        indent_symbol=final_indent_symbol,
                        base_indent_symbol=final_base_indent_symbol,
                    )

                    # Initialize logger with resolved configuration
                    cls._logger = EzLogger(
                        log_file=cls._log_file,
                        level=final_file_logger_level,
                        rotation=final_rotation,
                        retention=final_retention,
                        compression=final_compression,
                    )

                    # Apply global log level with priority: specific > global
                    cls._instance._apply_level_priority(
                        printer_level=printer_level,
                        file_logger_level=file_logger_level,
                        global_level=final_log_level,
                    )

        # Type narrowing: _instance is guaranteed to be set at this point
        assert cls._instance is not None
        return cls._instance

    # ///////////////////////////////////////////////////////////////
    # PRIVATE HELPERS
    # ///////////////////////////////////////////////////////////////

    def _apply_level_priority(
        self,
        *,
        printer_level: str | None = None,
        file_logger_level: str | None = None,
        global_level: str | None = None,
    ) -> None:
        """
        Apply log levels with priority: specific level > global level.

        Only sets levels when a non-None value can be resolved.
        If a specific level is not provided, global_level is used as fallback.
        """
        effective_printer = printer_level or global_level
        effective_logger = file_logger_level or global_level
        if effective_printer:
            self.set_printer_level(effective_printer)
        if effective_logger:
            self.set_logger_level(effective_logger)

    # ///////////////////////////////////////////////////////////////
    # GETTER
    # ///////////////////////////////////////////////////////////////

    def get_printer(self) -> EzPrinter:
        """
        Returns the EzPrinter instance.

        **Returns:**

            * EzPrinter: The console printer instance providing info(), debug(), success(), etc.
                Implements PrinterProtocol for type safety.
        """
        return self._printer

    # ///////////////////////////////////////////////////////////////

    def get_logger(self) -> EzLogger:
        """
        Returns the EzLogger instance.

        **Returns:**

            * EzLogger: The file logger instance for file logging.
                Use logger.info(), logger.debug(), etc. directly.
                For advanced loguru features, use logger.get_loguru()
                Implements LoggerProtocol for type safety.
        """
        return self._logger

    # ///////////////////////////////////////////////////////////////
    # UTILS METHODS
    # ///////////////////////////////////////////////////////////////

    def set_level(self, level: str) -> None:
        """
        Définit le niveau de log du printer et du logger en même temps (méthode de compatibilité).

        **Args:**

            * `level` (str): Le niveau de log désiré (ex: "INFO", "WARNING").

        **Returns:**

            * `None`.
        """
        self.set_logger_level(level)
        self.set_printer_level(level)

    def set_printer_level(self, level: str) -> None:
        """
        Définit le niveau de log du printer uniquement.

        **Args:**

            * `level` (str): Le niveau de log désiré pour le printer.

        **Returns:**

            * `None`.
        """
        self._printer.set_level(level)

    def set_logger_level(self, level: str) -> None:
        """
        Définit le niveau de log du logger uniquement.

        **Args:**

            * `level` (str): Le niveau de log désiré pour le logger.

        **Returns:**

            * `None`.
        """
        self._logger.set_level(level)

    # ///////////////////////////////////////////////////////////////

    def add_separator(self) -> None:
        """
        Adds a separator to the log file.

        **Returns:**

            * `None`.
        """
        self._logger.add_separator()

    # ///////////////////////////////////////////////////////////////

    @contextmanager
    def manage_indent(self) -> Generator[None, None, None]:
        """
        Context manager to manage indentation level.

        **Returns:**

            * `None`.
        """
        with self._printer.manage_indent():
            yield

    # ///////////////////////////////////////////////////////////////
    # ENHANCED METHODS
    # ///////////////////////////////////////////////////////////////

    @classmethod
    def reset(cls) -> None:
        """
        Reset the singleton instance (useful for testing).

        Warning: This will destroy the current instance and all its state.
        """
        if cls._instance is not None:
            # Close logger handlers to release file handles (important on Windows)
            try:
                if hasattr(cls._instance, "_logger") and cls._instance._logger:
                    cls._instance._logger.close()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
            cls._instance = None
        # Also reset configuration lock
        cls._config_locked = False

    # ------------------------------------------------
    # CONFIG LOCK CONTROL
    # ------------------------------------------------

    @classmethod
    def lock_config(cls) -> None:
        """
        Lock Ezpl configuration so that future configure() calls are ignored
        unless explicitly forced.

        Intended usage:
            1. Root application configures Ezpl once
            2. Calls Ezpl.lock_config()
            3. Libraries calling configure() later will not override settings
        """
        cls._config_locked = True

    @classmethod
    def unlock_config(cls) -> None:
        """
        Unlock Ezpl configuration.

        Use with care: this allows configure() to change global logging
        configuration again.
        """
        cls._config_locked = False

    def set_log_file(self, log_file: Path | str) -> None:
        """
        Change the log file (requires reinitialization of the logger).

        Args:
            log_file: New path to the log file

        Note: This will reinitialize the file logger but keep the singleton instance.
        """
        new_log_file = Path(log_file)
        if new_log_file != self._log_file:
            self._log_file = new_log_file
            # Update configuration
            self._config_manager.set("log-file", str(new_log_file))
            # Safely close previous logger to avoid duplicated loguru handlers
            try:
                if hasattr(self, "_logger") and self._logger:
                    self._logger.close()
            except Exception as e:
                logger.error(f"Error while closing previous logger: {e}")
            # Reinitialize logger with the new file and current parameters
            self._logger = EzLogger(
                log_file=self._log_file,
                level=self._logger._level,
                rotation=self._config_manager.get_log_rotation(),
                retention=self._config_manager.get_log_retention(),
                compression=self._config_manager.get_log_compression(),
            )

    def get_log_file(self) -> Path:
        """
        Get the current log file path.

        Returns:
            Path to the current log file
        """
        return self._log_file

    def get_config(self) -> ConfigurationManager:
        """
        Get the current configuration manager.

        Returns:
            ConfigurationManager instance for accessing and modifying configuration
        """
        return self._config_manager

    # ///////////////////////////////////////////////////////////////
    # HANDLER OVERRIDE METHODS
    # ///////////////////////////////////////////////////////////////

    def set_printer_class(
        self,
        printer_class: type[EzPrinter] | EzPrinter,
        **init_kwargs: Any,
    ) -> None:
        """
        Replace the current printer with a custom printer class or instance.

        Allows users to override the default printer with a custom class that
        inherits from EzPrinter. The method preserves
        current configuration values (level, indentation settings) unless
        explicitly overridden in init_kwargs.

        Args:
            printer_class: Custom printer class inheriting from EzPrinter,
                or an already instantiated EzPrinter instance
            **init_kwargs: Optional initialization parameters for the printer
                class. If not provided, current configuration values are used.

        Raises:
            TypeError: If printer_class is not a valid class or instance
            ValidationError: If initialization parameters are invalid

        Example:
            >>> from ezpl import Ezpl, EzPrinter
            >>>
            >>> class CustomPrinter(EzPrinter):
            ...     def info(self, message):
            ...         super().info(f"[CUSTOM] {message}")
            >>>
            >>> ezpl = Ezpl()
            >>> ezpl.set_printer_class(CustomPrinter, level="DEBUG")
            >>> ezpl.get_printer().info("Test")
            [CUSTOM] Test
        """
        from .core.exceptions import ValidationError

        # If it's already an instance, use it directly
        if isinstance(printer_class, EzPrinter):
            new_printer = printer_class
        # If it's a class, instantiate it
        elif isinstance(printer_class, type):
            # Validate that it's a subclass of EzPrinter
            if not issubclass(printer_class, EzPrinter):
                raise TypeError(
                    f"printer_class must be a subclass of {EzPrinter.__name__}, "
                    f"got {printer_class.__name__}"
                )

            # Preserve current configuration values if not provided
            current_level = (
                self._printer._level
                if hasattr(self._printer, "_level")
                else self._config_manager.get_printer_level()
            )
            current_indent_step = (
                self._printer._indent_step
                if hasattr(self._printer, "_indent_step")
                else self._config_manager.get_indent_step()
            )
            current_indent_symbol = (
                self._printer._indent_symbol
                if hasattr(self._printer, "_indent_symbol")
                else self._config_manager.get_indent_symbol()
            )
            current_base_indent_symbol = (
                self._printer._base_indent_symbol
                if hasattr(self._printer, "_base_indent_symbol")
                else self._config_manager.get_base_indent_symbol()
            )

            # Merge kwargs with default values
            init_params = {
                "level": init_kwargs.pop("level", current_level),
                "indent_step": init_kwargs.pop("indent_step", current_indent_step),
                "indent_symbol": init_kwargs.pop(
                    "indent_symbol", current_indent_symbol
                ),
                "base_indent_symbol": init_kwargs.pop(
                    "base_indent_symbol", current_base_indent_symbol
                ),
            }
            init_params.update(init_kwargs)

            # Create new instance
            try:
                new_printer = printer_class(**init_params)
            except Exception as e:
                raise ValidationError(
                    f"Failed to initialize printer class {printer_class.__name__}: {e}",
                    "printer_class",
                    str(printer_class),
                ) from e
        else:
            raise TypeError(
                f"printer_class must be a class or an instance of {EzPrinter.__name__}, "
                f"got {type(printer_class).__name__}"
            )

        # Replace the instance
        self._printer = new_printer

    def set_logger_class(
        self,
        logger_class: type[EzLogger] | EzLogger,
        **init_kwargs: Any,
    ) -> None:
        """
        Replace the current logger with a custom logger class or instance.

        Allows users to override the default logger with a custom class that
        inherits from EzLogger. The method preserves current
        configuration values (level, rotation, retention, compression) unless
        explicitly overridden in init_kwargs.

        Args:
            logger_class: Custom logger class inheriting from EzLogger,
                or an already instantiated EzLogger instance
            **init_kwargs: Optional initialization parameters for the logger
                class. If not provided, current configuration values are used.

        Raises:
            TypeError: If logger_class is not a valid class or instance
            ValidationError: If initialization parameters are invalid
            FileOperationError: If file operations fail during logger creation
                (may be raised by the logger class constructor)

        Example:
            >>> from ezpl import Ezpl, EzLogger
            >>>
            >>> class CustomLogger(EzLogger):
            ...     def info(self, message):
            ...         super().info(f"[CUSTOM LOG] {message}")
            >>>
            >>> ezpl = Ezpl()
            >>> ezpl.set_logger_class(CustomLogger, log_file="custom.log")
            >>> ezpl.get_logger().info("Test")
        """
        from .core.exceptions import ValidationError

        # If it's already an instance, use it directly
        if isinstance(logger_class, EzLogger):
            new_logger = logger_class
        # If it's a class, instantiate it
        elif isinstance(logger_class, type):
            # Validate that it's a subclass of EzLogger
            if not issubclass(logger_class, EzLogger):
                raise TypeError(
                    f"logger_class must be a subclass of {EzLogger.__name__}, "
                    f"got {logger_class.__name__}"
                )

            # Preserve current configuration values if not provided
            current_level = (
                self._logger._level
                if hasattr(self._logger, "_level")
                else self._config_manager.get_file_logger_level()
            )
            current_log_file = (
                self._log_file
                if hasattr(self, "_log_file")
                else self._config_manager.get_log_file()
            )
            current_rotation = (
                self._logger._rotation
                if hasattr(self._logger, "_rotation")
                else self._config_manager.get_log_rotation()
            )
            current_retention = (
                self._logger._retention
                if hasattr(self._logger, "_retention")
                else self._config_manager.get_log_retention()
            )
            current_compression = (
                self._logger._compression
                if hasattr(self._logger, "_compression")
                else self._config_manager.get_log_compression()
            )

            # Merge kwargs with default values
            init_params = {
                "log_file": init_kwargs.pop("log_file", current_log_file),
                "level": init_kwargs.pop("level", current_level),
                "rotation": init_kwargs.pop("rotation", current_rotation),
                "retention": init_kwargs.pop("retention", current_retention),
                "compression": init_kwargs.pop("compression", current_compression),
            }
            init_params.update(init_kwargs)

            # Close previous logger before creating new one to avoid resource leaks
            try:
                if hasattr(self, "_logger") and self._logger:
                    self._logger.close()
            except Exception as e:
                logger.error(f"Error while closing previous logger: {e}")

            # Create new instance
            try:
                new_logger = logger_class(**init_params)
            except Exception as e:
                raise ValidationError(
                    f"Failed to initialize logger class {logger_class.__name__}: {e}",
                    "logger_class",
                    str(logger_class),
                ) from e
        else:
            raise TypeError(
                f"logger_class must be a class or an instance of {EzLogger.__name__}, "
                f"got {type(logger_class).__name__}"
            )

        # Replace the instance
        self._logger = new_logger

    # ///////////////////////////////////////////////////////////////
    # CONFIGURATION METHODS
    # ///////////////////////////////////////////////////////////////

    def reload_config(self) -> None:
        """
        Reload configuration from file and environment variables.

        This method reloads the configuration and reapplies it to handlers.
        Useful when environment variables or the config file have changed
        after the singleton was initialized.

        Note: This will reinitialize handlers with the new configuration.
        """
        # Reload configuration
        self._config_manager.reload()

        # Get configuration values
        printer_level = self._config_manager.get_printer_level()
        file_logger_level = self._config_manager.get_file_logger_level()
        global_log_level = self._config_manager.get_log_level()

        # Check if specific levels are explicitly set (not just defaults)
        # Priority: specific levels > global level
        # Only apply global level if specific levels are not explicitly set
        printer_level_explicit = self._config_manager.has_key("printer-level")
        file_logger_level_explicit = self._config_manager.has_key("file-logger-level")
        global_log_level_explicit = self._config_manager.has_key("log-level")

        # Reapply to handlers with priority logic
        self._apply_level_priority(
            printer_level=printer_level if printer_level_explicit else None,
            file_logger_level=file_logger_level if file_logger_level_explicit else None,
            global_level=global_log_level if global_log_level_explicit else None,
        )
        # Fallback: apply config defaults if no explicit override resolved
        if not printer_level_explicit and not global_log_level_explicit:
            self.set_printer_level(printer_level)
        if not file_logger_level_explicit and not global_log_level_explicit:
            self.set_logger_level(file_logger_level)

        # Reinitialize logger with new rotation / retention / compression settings
        # Preserve current level if logger was already initialized
        current_logger_level = (
            self._logger._level
            if hasattr(self, "_logger") and self._logger
            else file_logger_level
        )
        try:
            if hasattr(self, "_logger") and self._logger:
                self._logger.close()
        except Exception as e:
            logger.error(f"Error while closing logger during reload_config: {e}")
        self._logger = EzLogger(
            log_file=self._log_file,
            level=current_logger_level,
            rotation=self._config_manager.get_log_rotation(),
            retention=self._config_manager.get_log_retention(),
            compression=self._config_manager.get_log_compression(),
        )

        # Reinitialize printer with new indent settings
        # Preserve current level if printer was already initialized
        current_printer_level = (
            self._printer._level
            if hasattr(self, "_printer") and self._printer
            else printer_level
        )
        self._printer = EzPrinter(
            level=current_printer_level,
            indent_step=self._config_manager.get_indent_step(),
            indent_symbol=self._config_manager.get_indent_symbol(),
            base_indent_symbol=self._config_manager.get_base_indent_symbol(),
        )

    def configure(self, config_dict: dict[str, Any] | None = None, **kwargs) -> bool:
        """
        Configure Ezpl dynamically.

        Args:
            config_dict: Dictionary of configuration values to update
            **kwargs: Configuration options (alternative to config_dict):
                - log_file or log-file: Path to log file
                - printer_level or printer-level: Printer log level
                - logger_level or file-logger-level: File logger level
                - level or log-level: Set both printer and logger level
                - log_rotation or log-rotation: Rotation setting (e.g., "10 MB", "1 day")
                - log_retention or log-retention: Retention period (e.g., "7 days")
                - log_compression or log-compression: Compression format (e.g., "zip", "gz")
                - indent_step or indent-step: Indentation step size
                - indent_symbol or indent-symbol: Symbol for indentation
                - base_indent_symbol or base-indent-symbol: Base indentation symbol

        Returns:
            True if configuration was applied, False if it was blocked by lock.

        Note: Changes are persisted to the configuration file.
        """
        # Merge config_dict and kwargs
        if config_dict:
            kwargs.update(config_dict)

        # Special control flag (not stored in configuration):
        # - force=True allows configure() even when configuration is locked
        force = kwargs.pop("force", False)

        # If configuration is locked and not forced, warn and return False
        if self._config_locked and not force:
            warnings.warn(
                "Ezpl configuration is locked. Call Ezpl.unlock_config() or "
                "pass force=True to override.",
                UserWarning,
                stacklevel=2,
            )
            return False

        # Normalize keys: convert underscores to hyphens for consistency
        normalized_config = {}
        key_mapping = {
            "log_file": "log-file",
            "printer_level": "printer-level",
            "logger_level": "file-logger-level",
            "level": "log-level",
            "log_rotation": "log-rotation",
            "log_retention": "log-retention",
            "log_compression": "log-compression",
            "indent_step": "indent-step",
            "indent_symbol": "indent-symbol",
            "base_indent_symbol": "base-indent-symbol",
        }

        for key, value in kwargs.items():
            # Use normalized key if mapping exists, otherwise keep original
            normalized_key = key_mapping.get(key, key)
            normalized_config[normalized_key] = value

        # Update configuration manager
        self._config_manager.update(normalized_config)
        self._config_manager.save()

        # Apply changes to handlers
        if "log-file" in normalized_config:
            self.set_log_file(normalized_config["log-file"])

        # Handle log level changes with priority: specific > global
        self._apply_level_priority(
            printer_level=normalized_config.get("printer-level"),
            file_logger_level=normalized_config.get("file-logger-level"),
            global_level=normalized_config.get("log-level"),
        )

        # Reinitialize logger if rotation settings changed
        rotation_changed = any(
            key in normalized_config
            for key in ["log-rotation", "log-retention", "log-compression"]
        )
        if rotation_changed:
            # Save current level before closing logger
            current_logger_level = (
                self._logger._level
                if hasattr(self, "_logger") and self._logger
                else self._config_manager.get_file_logger_level()
            )
            # Close previous logger before creating a new one to avoid duplicate handlers
            try:
                if hasattr(self, "_logger") and self._logger:
                    self._logger.close()
            except Exception as e:
                logger.error(f"Error while closing logger during configure(): {e}")
            self._logger = EzLogger(
                log_file=self._log_file,
                level=self._config_manager.get_file_logger_level()
                or current_logger_level,
                rotation=self._config_manager.get_log_rotation(),
                retention=self._config_manager.get_log_retention(),
                compression=self._config_manager.get_log_compression(),
            )

        # Reinitialize printer if indent settings changed
        indent_changed = any(
            key in normalized_config
            for key in ["indent-step", "indent-symbol", "base-indent-symbol"]
        )
        if indent_changed:
            # Save current level before reinitializing printer
            current_printer_level = (
                self._printer._level
                if hasattr(self, "_printer") and self._printer
                else self._config_manager.get_printer_level()
            )
            self._printer = EzPrinter(
                level=self._config_manager.get_printer_level() or current_printer_level,
                indent_step=self._config_manager.get_indent_step(),
                indent_symbol=self._config_manager.get_indent_symbol(),
                base_indent_symbol=self._config_manager.get_base_indent_symbol(),
            )

        return True
