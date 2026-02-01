# ///////////////////////////////////////////////////////////////
# EZPL - Enums Module
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Enums module for Ezpl logging framework.

This module contains all enumeration types used in Ezpl.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Local imports
from .log_level import LogLevel
from .patterns import (
    PATTERN_COLORS,
    Pattern,
    get_pattern_color,
    get_pattern_color_by_name,
)

# ///////////////////////////////////////////////////////////////
# PUBLIC API
# ///////////////////////////////////////////////////////////////

__all__ = [
    # Log level exports
    "LogLevel",
    # Pattern exports
    "Pattern",
    "PATTERN_COLORS",
    "get_pattern_color",
    "get_pattern_color_by_name",
]
