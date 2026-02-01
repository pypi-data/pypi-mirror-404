"""Protocol types for CRM Agent Environment.

This module provides the ParsedAction dataclass used for parsing
tool calls from LLM outputs into environment actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ParsedAction:
    """Result of parsing a tool call into an environment action.

    Attributes:
        action: The parsed action object, or None if parsing failed.
        is_valid: Whether the tool call was successfully parsed.
        error_message: Human-readable error message if parsing failed.
    """

    action: Any | None
    is_valid: bool
    error_message: str | None = None
