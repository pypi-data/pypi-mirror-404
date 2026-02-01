"""Construct Labs CRM Agent Environment SDK.

This package provides a Python client for interacting with the Construct Labs
CRM Agent Environment - a reinforcement learning environment for training
agents to interact with CRM systems.

For more information, see https://docs.construct-labs.com/crm-agent
"""

from .client import CrmAgentEnv
from .models import (
    CRMActionType,
    CrmAgentAction,
    CrmAgentObservation,
    CrmAgentState,
)
from .protocol import ParsedAction

__version__ = "0.1.0"

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
