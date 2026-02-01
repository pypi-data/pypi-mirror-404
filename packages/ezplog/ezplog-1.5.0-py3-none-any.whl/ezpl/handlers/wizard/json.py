# ///////////////////////////////////////////////////////////////
# EZPL - Wizard JSON Mixin
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
JSON methods mixin for Rich Wizard.

This module provides JSON display functionality for the RichWizard class.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import json

# Third-party imports
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel

# Local imports
from ..utils import safe_str_convert

# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class JsonMixin:
    """
    Mixin providing JSON display methods for RichWizard.

    This mixin adds JSON display functionality with syntax highlighting
    and optional panel wrapping.
    """

    # Type hints for attributes provided by RichWizard
    _console: Console

    # ///////////////////////////////////////////////////////////////
    # JSON METHODS
    # ///////////////////////////////////////////////////////////////

    def json(
        self,
        data: str | dict | list,
        title: str | None = None,
        indent: int | None = None,
        highlight: bool = True,
    ) -> None:
        """
        Display JSON data in a formatted and syntax-highlighted way using Rich.

        Args:
            data: JSON data to display (dict, list, or JSON string)
            title: Optional title for the JSON display
            indent: Number of spaces for indentation (default: 2)
            highlight: Whether to enable syntax highlighting (default: True)

        Examples:
            >>> wizard.json({"name": "Alice", "age": 30})
            >>> wizard.json('{"key": "value"}', title="Config")
            >>> wizard.json([1, 2, 3], indent=4)
        """
        try:
            # Convert data to JSON string if needed
            if isinstance(data, str):
                # Try to parse and re-format for consistency
                try:
                    parsed = json.loads(data)
                    json_str = json.dumps(parsed, ensure_ascii=False)
                except json.JSONDecodeError:
                    # If invalid JSON, use as-is
                    json_str = data
            else:
                # Convert dict/list to JSON string
                json_str = json.dumps(data, ensure_ascii=False)

            # Create Rich JSON object with proper parameters
            # Note: Rich's JSON class handles indentation internally via its indent parameter
            rich_json = JSON(json_str, indent=indent or 2, highlight=highlight)

            # Display with optional title
            if title:
                panel = Panel(rich_json, title=title, border_style="blue")
                self._console.print(panel)
            else:
                self._console.print(rich_json)

        except Exception as e:
            # Fallback: try to display as string
            try:
                fallback_msg = (
                    f"[yellow]JSON Display Error:[/yellow] {type(e).__name__}"
                )
                if title:
                    self._console.print(
                        Panel(fallback_msg, title=title, border_style="red")
                    )
                else:
                    self._console.print(fallback_msg)
                # Also try to print the raw data
                self._console.print(f"[dim]Raw data:[/dim] {safe_str_convert(data)}")
            except Exception as e:
                raise ValueError(f"Failed to display JSON: {e}") from e
