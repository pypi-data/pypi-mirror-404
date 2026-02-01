"""Construct Labs CRM Agent Environment SDK.

This package provides a Python client for interacting with the Construct Labs
CRM Agent Environment - a reinforcement learning environment for training
agents to interact with CRM systems.

For licensing and support, contact hello@construct-labs.com
"""

from importlib.metadata import PackageNotFoundError, version

from .client import CrmAgentEnv
from .models import (
    CRMActionType,
    CrmAgentAction,
    CrmAgentObservation,
    CrmAgentState,
)
from .protocol import ParsedAction

try:
    __version__ = version("construct-labs-crm-env")
except PackageNotFoundError:
    __version__ = "0.0.0+dev"

__all__ = [
    # Main client
    "CrmAgentEnv",
    # Data models
    "CrmAgentAction",
    "CrmAgentObservation",
    "CrmAgentState",
    "CRMActionType",
    # For custom parse_tool_call implementations
    "ParsedAction",
    # Version
    "__version__",
]
