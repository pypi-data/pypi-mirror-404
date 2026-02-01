# ///////////////////////////////////////////////////////////////
# EZPL - Main Module
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Ezpl - Modern Python logging framework.

Ezpl is a modern Python library for advanced log management, using **Rich**
for console output and **loguru** for file logging, with a simple and typed API,
suitable for professional and industrial applications.

**Main Features:**
    - Singleton pattern for global logging instance
    - Rich-based console output with colors and formatting
    - Loguru-based file logging with rotation support
    - Contextual indentation management
    - Pattern-based logging (SUCCESS, ERROR, WARN, TIP, etc.)
    - JSON display support
    - Robust error handling

**Quick Start:**
    >>> from ezpl import Ezpl
    >>> ezpl = Ezpl()
    >>> printer = ezpl.get_printer()
    >>> logger = ezpl.get_logger()
    >>> printer.info("Hello, Ezpl!")
    >>> logger.info("Logged to file")
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import sys

# Local imports
from .config import ConfigurationManager
from .core.exceptions import (
    ConfigurationError,
    EzplError,
    FileOperationError,
    HandlerError,
    InitializationError,
    LoggingError,
    ValidationError,
)
from .ezpl import Ezpl
from .handlers import EzLogger, EzPrinter, RichWizard
from .types import (
    PATTERN_COLORS,
    LoggerProtocol,
    LogLevel,
    Pattern,
    PrinterProtocol,
    get_pattern_color,
    get_pattern_color_by_name,
)

# ///////////////////////////////////////////////////////////////
# META INFORMATIONS
# ///////////////////////////////////////////////////////////////

__version__ = "1.5.0"
__author__ = "Neuraaak"
__maintainer__ = "Neuraaak"
__description__ = "A module for easier logging"
__python_requires__ = ">=3.10"
__keywords__ = ["logging", "rich", "loguru", "console", "file"]
__url__ = "https://github.com/neuraaak/ezplog"
__repository__ = "https://github.com/neuraaak/ezplog"

# ///////////////////////////////////////////////////////////////
# PYTHON VERSION CHECK
# ///////////////////////////////////////////////////////////////

if sys.version_info < (3, 10):  # noqa: UP036
    raise RuntimeError(
        f"ezpl {__version__} requires Python 3.10 or higher. "
        f"Current version: {sys.version}"
    )

# ///////////////////////////////////////////////////////////////
# TYPE ALIASES
# ///////////////////////////////////////////////////////////////

Printer = EzPrinter
"""Type alias for EzPrinter (console printer handler).
Use this type when you want to annotate a variable that represents a printer.

Example:
    >>> from ezpl import Ezpl, Printer
    >>> ezpl = Ezpl()
    >>> printer: Printer = ezpl.get_printer()
    >>> printer.info("Hello!")
    >>> printer.success("Done!")
    >>> printer.print_json({"key": "value"})
"""

Logger = EzLogger
"""Type alias for EzLogger (file logger handler).
Use this type when you want to annotate a variable that represents a logger.

Example:
    >>> from ezpl import Ezpl, Logger
    >>> ezpl = Ezpl()
    >>> logger: Logger = ezpl.get_logger()
    >>> logger.info("Logged to file")
"""

# ///////////////////////////////////////////////////////////////
# PUBLIC API
# ///////////////////////////////////////////////////////////////

__all__ = [
    # Main class exports
    "Ezpl",
    # Handler class exports
    "EzPrinter",
    "EzLogger",
    "RichWizard",
    # Configuration exports
    "ConfigurationManager",
    # Type aliases exports
    "Printer",
    "Logger",
    # Type & pattern exports
    "LogLevel",
    "Pattern",
    "PATTERN_COLORS",
    "get_pattern_color",
    "get_pattern_color_by_name",
    # Protocol exports
    "PrinterProtocol",
    "LoggerProtocol",
    # Exception exports
    "EzplError",
    "ConfigurationError",
    "LoggingError",
    "ValidationError",
    "InitializationError",
    "FileOperationError",
    "HandlerError",
    # Metadata exports
    "__version__",
    "__author__",
    "__maintainer__",
    "__description__",
    "__python_requires__",
    "__keywords__",
    "__url__",
    "__repository__",
]
