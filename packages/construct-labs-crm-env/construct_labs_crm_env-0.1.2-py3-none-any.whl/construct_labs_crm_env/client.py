"""CRM Agent Environment Client.

This module provides the client for connecting to the Construct Labs CRM Agent
Environment. The client handles authentication, WebSocket communication, and
provides an extensible interface for customizing agent behavior.

Example:
    >>> from construct_labs_crm_env import CrmAgentEnv, CrmAgentAction, CRMActionType
    >>>
    >>> with CrmAgentEnv(
    ...     base_url="https://api.construct-labs.com",
    ...     api_key="your-api-key"
    ... ) as env:
    ...     result = env.reset()
    ...     result = env.step(CrmAgentAction(
    ...         action_type=CRMActionType.LIST_COMPANIES,
    ...         limit=10
    ...     ))
"""

from __future__ import annotations

import json
import os
from typing import Any, cast

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from websockets.sync.client import connect as ws_connect

from .models import (
    CRMActionType,
    CrmAgentAction,
    CrmAgentObservation,
    CrmAgentState,
)
from .protocol import ParsedAction

# Type alias for JSON-serializable dictionaries
JsonDict = dict[str, Any]

# Protocol version for API compatibility
_PROTOCOL_VERSION = "v1"


class CrmAgentEnv(EnvClient[CrmAgentAction, CrmAgentObservation, CrmAgentState]):
    """Client for the Construct Labs CRM Agent Environment.

    This client connects to the CRM environment server via WebSocket and
    provides methods for interacting with CRM data. It supports customization
    through subclassing - override `system_prompt`, `tools`, or
    `format_observation` to customize agent behavior.

    Args:
        base_url: Base URL of the CRM environment server.
        api_key: API key for authentication. Get one at https://construct-labs.com
        connect_timeout_s: Timeout for establishing connection (default: 10s).
        message_timeout_s: Timeout for receiving responses (default: 60s).

    Example:
        >>> # Basic usage
        >>> with CrmAgentEnv(
        ...     base_url="https://api.construct-labs.com",
        ...     api_key="cl_live_xxx"
        ... ) as env:
        ...     result = env.reset()
        ...     print(env.system_prompt)

    Example (custom subclass):
        >>> class SalesAgent(CrmAgentEnv):
        ...     @property
        ...     def system_prompt(self) -> str:
        ...         return "You are a sales assistant..."
        ...
        ...     @property
        ...     def tools(self) -> list[dict]:
        ...         # Only expose company and opportunity tools
        ...         return [t for t in self._default_tools()
        ...                 if 'company' in t['function']['name']
        ...                 or 'opportunity' in t['function']['name']]
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        connect_timeout_s: float = 10.0,
        message_timeout_s: float = 60.0,
    ) -> None:
        """Initialize the CRM environment client.

        Args:
            base_url: Base URL of the CRM environment server.
            api_key: API key for authentication. Can also be set via
                CRM_AGENT_API_KEY environment variable.
            connect_timeout_s: Timeout for establishing WebSocket connection.
            message_timeout_s: Timeout for receiving responses.

        Raises:
            ValueError: If no API key is provided or found in environment.
        """
        # Resolve API key from parameter or environment
        resolved_api_key = api_key or os.environ.get("CRM_AGENT_API_KEY")
        if not resolved_api_key:
            raise ValueError(
                "API key is required. Pass api_key parameter or set "
                "CRM_AGENT_API_KEY environment variable. "
                "Get your API key by contacting hello@construct-labs.com"
            )

        self._api_key = resolved_api_key

        # Initialize parent class (but don't connect yet)
        super().__init__(
            base_url=base_url,
            connect_timeout_s=connect_timeout_s,
            message_timeout_s=message_timeout_s,
        )

    def connect(self) -> CrmAgentEnv:
        """Establish authenticated WebSocket connection to the server.

        The API key is transmitted via WebSocket subprotocol for secure
        authentication during the handshake.

        Returns:
            self for method chaining.

        Raises:
            ConnectionError: If connection cannot be established or
                authentication fails.
        """
        if self._ws is not None:
            return self

        # Bypass proxy for localhost connections
        ws_url_lower = self._ws_url.lower()
        is_localhost = "localhost" in ws_url_lower or "127.0.0.1" in ws_url_lower

        old_no_proxy = os.environ.get("NO_PROXY")
        if is_localhost:
            current_no_proxy = old_no_proxy or ""
            if "localhost" not in current_no_proxy.lower():
                os.environ["NO_PROXY"] = (
                    f"{current_no_proxy},localhost,127.0.0.1"
                    if current_no_proxy
                    else "localhost,127.0.0.1"
                )

        try:
            # Authenticate via WebSocket subprotocol
            # Format: crm-{version}.{api_key}
            auth_subprotocol = f"crm-{_PROTOCOL_VERSION}.{self._api_key}"

            self._ws = ws_connect(
                self._ws_url,
                open_timeout=self._connect_timeout,
                subprotocols=[auth_subprotocol],
            )
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "403" in error_msg or "4001" in error_msg:
                raise ConnectionError(
                    "Authentication failed. Please verify your API key. "
                    "Get a valid key at https://construct-labs.com/api-keys"
                ) from e
            raise ConnectionError(f"Failed to connect to {self._ws_url}: {e}") from e
        finally:
            # Restore original NO_PROXY value
            if is_localhost:
                if old_no_proxy is None:
                    os.environ.pop("NO_PROXY", None)
                else:
                    os.environ["NO_PROXY"] = old_no_proxy

        return self

    def _step_payload(self, action: CrmAgentAction) -> JsonDict:
        """Convert CrmAgentAction to JSON payload for step request."""
        return action.model_dump()

    def _parse_result(self, payload: JsonDict) -> StepResult[CrmAgentObservation]:
        """Parse server response into StepResult."""
        obs_data = payload.get("observation", {})
        observation = CrmAgentObservation.model_validate(obs_data)

        return StepResult(
            observation=observation,
            reward=payload.get("reward", observation.reward),
            done=payload.get("done", observation.done),
        )

    def _parse_state(self, payload: JsonDict) -> CrmAgentState:
        """Parse server response into CrmAgentState."""
        return CrmAgentState.model_validate(payload)

    def _reset_payload(self, seed: int | None = None) -> JsonDict:
        """Create payload for reset request."""
        if seed is not None:
            return {"seed": seed}
        return {}

    # =========================================================================
    # Extensible Properties - Override these in subclasses
    # =========================================================================

    @property
    def system_prompt(self) -> str:
        """System prompt for the CRM agent.

        Override this property in a subclass to customize the agent's behavior
        and instructions.

        Returns:
            The system prompt string to use for the agent.

        Example:
            >>> class CustomAgent(CrmAgentEnv):
            ...     @property
            ...     def system_prompt(self) -> str:
            ...         return '''You are a data entry assistant.
            ...         Focus on accuracy and completeness.'''
        """
        return self._default_system_prompt()

    def _default_system_prompt(self) -> str:
        """Return the default system prompt.

        Subclasses can call this to get the default prompt and extend it.

        Returns:
            The default system prompt string.
        """
        return """You are a tool-using agent interacting with a CRM (Customer Relationship Management) system.

GOAL: Complete CRM tasks by creating, updating, and managing business data.

AVAILABLE OPERATIONS:
- Companies: list, get, create, update, delete
- People/Contacts: list, get, create, update, delete
- Opportunities: list, get, create, update, delete
- Notes: list, create (attach to companies, people, or opportunities)
- Tasks: list, create, update, complete

EXAMPLES:

1. List companies:
<tool_call>
{"name": "list_companies", "arguments": {"limit": 10}}
</tool_call>

2. Create a company:
<tool_call>
{"name": "create_company", "arguments": {"company_name": "Acme Corp", "company_domain": "acme.com"}}
</tool_call>

3. Create a contact:
<tool_call>
{"name": "create_person", "arguments": {"person_first_name": "John", "person_last_name": "Doe", "person_email": "john@acme.com"}}
</tool_call>

4. Submit final answer:
<tool_call>
{"name": "submit_answer", "arguments": {"answer": "The total pipeline value is $1.5M"}}
</tool_call>

IMPORTANT: Output ONLY a tool_call, no other text."""

    @property
    def tools(self) -> list[JsonDict]:
        """Tool definitions for the CRM environment.

        Override this property in a subclass to customize available tools.
        You can filter, extend, or replace the default tool set.

        Returns:
            List of tool definitions in OpenAI function calling format.

        Example:
            >>> class ReadOnlyAgent(CrmAgentEnv):
            ...     @property
            ...     def tools(self) -> list[dict]:
            ...         # Only allow read operations
            ...         read_ops = {'list_', 'get_', 'submit_answer'}
            ...         return [t for t in self._default_tools()
            ...                 if any(op in t['function']['name'] for op in read_ops)]
        """
        return self._default_tools()

    def _default_tools(self) -> list[JsonDict]:
        """Return the default tool definitions.

        Subclasses can call this to get all default tools and filter/extend them.

        Returns:
            Complete list of CRM tool definitions.
        """
        return [
            # =================================================================
            # Company Tools
            # =================================================================
            {
                "type": "function",
                "function": {
                    "name": "list_companies",
                    "description": "List all companies in the CRM",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "default": 60,
                                "description": "Maximum number of companies to return (max 200)",
                            },
                            "starting_after": {
                                "type": "string",
                                "description": "Cursor for pagination - returns objects after this ID",
                            },
                            "ending_before": {
                                "type": "string",
                                "description": "Cursor for pagination - returns objects before this ID",
                            },
                            "order_by": {
                                "type": "string",
                                "description": "Order by: field_name[ASC|DESC]",
                            },
                            "filter": {
                                "type": "string",
                                "description": "Filter: field[eq|gt|lt|contains]:value",
                            },
                            "depth": {
                                "type": "integer",
                                "default": 1,
                                "description": "Relation depth: 0=primary only, 1=include relations",
                            },
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_company",
                    "description": "Get details of a specific company",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "record_id": {
                                "type": "string",
                                "description": "ID of the company to retrieve",
                            },
                            "depth": {
                                "type": "integer",
                                "default": 1,
                                "description": "Relation depth: 0=primary only, 1=include relations",
                            },
                        },
                        "required": ["record_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_company",
                    "description": "Create a new company in the CRM",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "company_name": {
                                "type": "string",
                                "description": "Name of the company",
                            },
                            "company_domain": {
                                "type": "string",
                                "description": "Domain/website of the company",
                            },
                            "company_address": {
                                "type": "string",
                                "description": "Address of the company",
                            },
                            "company_employees": {
                                "type": "integer",
                                "description": "Number of employees",
                            },
                        },
                        "required": ["company_name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "update_company",
                    "description": "Update an existing company",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "record_id": {
                                "type": "string",
                                "description": "ID of the company to update",
                            },
                            "company_name": {"type": "string"},
                            "company_domain": {"type": "string"},
                            "company_address": {"type": "string"},
                            "company_employees": {"type": "integer"},
                        },
                        "required": ["record_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_company",
                    "description": "Delete a company from the CRM",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "record_id": {
                                "type": "string",
                                "description": "ID of the company to delete",
                            },
                        },
                        "required": ["record_id"],
                    },
                },
            },
            # =================================================================
            # Person/Contact Tools
            # =================================================================
            {
                "type": "function",
                "function": {
                    "name": "list_people",
                    "description": "List all contacts/people in the CRM",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "default": 60,
                                "description": "Maximum number of contacts to return (max 200)",
                            },
                            "starting_after": {"type": "string"},
                            "ending_before": {"type": "string"},
                            "order_by": {"type": "string"},
                            "filter": {"type": "string"},
                            "depth": {"type": "integer", "default": 1},
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_person",
                    "description": "Get details of a specific contact",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "record_id": {
                                "type": "string",
                                "description": "ID of the contact to retrieve",
                            },
                            "depth": {"type": "integer", "default": 1},
                        },
                        "required": ["record_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_person",
                    "description": "Create a new contact/person in the CRM",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "person_first_name": {
                                "type": "string",
                                "description": "First name",
                            },
                            "person_last_name": {
                                "type": "string",
                                "description": "Last name",
                            },
                            "person_email": {
                                "type": "string",
                                "description": "Email address",
                            },
                            "person_phone": {
                                "type": "string",
                                "description": "Phone number",
                            },
                            "person_company_id": {
                                "type": "string",
                                "description": "ID of associated company",
                            },
                            "person_job_title": {
                                "type": "string",
                                "description": "Job title",
                            },
                        },
                        "required": ["person_first_name", "person_last_name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "update_person",
                    "description": "Update an existing contact",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "record_id": {
                                "type": "string",
                                "description": "ID of the contact to update",
                            },
                            "person_first_name": {"type": "string"},
                            "person_last_name": {"type": "string"},
                            "person_email": {"type": "string"},
                            "person_phone": {"type": "string"},
                            "person_job_title": {"type": "string"},
                        },
                        "required": ["record_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_person",
                    "description": "Delete a contact from the CRM",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "record_id": {
                                "type": "string",
                                "description": "ID of the contact to delete",
                            },
                        },
                        "required": ["record_id"],
                    },
                },
            },
            # =================================================================
            # Opportunity Tools
            # =================================================================
            {
                "type": "function",
                "function": {
                    "name": "list_opportunities",
                    "description": "List all opportunities/deals in the CRM",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "default": 60,
                                "description": "Maximum number to return (max 200)",
                            },
                            "starting_after": {"type": "string"},
                            "ending_before": {"type": "string"},
                            "order_by": {"type": "string"},
                            "filter": {"type": "string"},
                            "depth": {"type": "integer", "default": 1},
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_opportunity",
                    "description": "Get details of a specific opportunity",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "record_id": {
                                "type": "string",
                                "description": "ID of the opportunity",
                            },
                            "depth": {"type": "integer", "default": 1},
                        },
                        "required": ["record_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_opportunity",
                    "description": "Create a new opportunity/deal",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "opportunity_name": {
                                "type": "string",
                                "description": "Name of the opportunity",
                            },
                            "opportunity_amount": {
                                "type": "number",
                                "description": "Deal value",
                            },
                            "opportunity_stage": {
                                "type": "string",
                                "enum": ["NEW", "MEETING", "PROPOSAL", "WON", "LOST"],
                                "description": "Sales stage",
                            },
                            "opportunity_close_date": {
                                "type": "string",
                                "description": "Expected close date (ISO format)",
                            },
                            "opportunity_company_id": {
                                "type": "string",
                                "description": "Associated company ID",
                            },
                            "opportunity_person_id": {
                                "type": "string",
                                "description": "Point of contact ID",
                            },
                        },
                        "required": ["opportunity_name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "update_opportunity",
                    "description": "Update an existing opportunity",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "record_id": {
                                "type": "string",
                                "description": "ID of the opportunity to update",
                            },
                            "opportunity_name": {"type": "string"},
                            "opportunity_amount": {"type": "number"},
                            "opportunity_stage": {
                                "type": "string",
                                "enum": ["NEW", "MEETING", "PROPOSAL", "WON", "LOST"],
                            },
                            "opportunity_close_date": {"type": "string"},
                        },
                        "required": ["record_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_opportunity",
                    "description": "Delete an opportunity",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "record_id": {
                                "type": "string",
                                "description": "ID of the opportunity to delete",
                            },
                        },
                        "required": ["record_id"],
                    },
                },
            },
            # =================================================================
            # Note Tools
            # =================================================================
            {
                "type": "function",
                "function": {
                    "name": "list_notes",
                    "description": "List all notes in the CRM",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "default": 10,
                                "description": "Maximum number of notes to return",
                            },
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_note",
                    "description": "Create a note attached to a record",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "note_body": {
                                "type": "string",
                                "description": "Content of the note",
                            },
                            "note_target_id": {
                                "type": "string",
                                "description": "ID of record to attach note to",
                            },
                            "note_target_type": {
                                "type": "string",
                                "enum": ["company", "person", "opportunity"],
                                "description": "Type of record",
                            },
                        },
                        "required": ["note_body"],
                    },
                },
            },
            # =================================================================
            # Task Tools
            # =================================================================
            {
                "type": "function",
                "function": {
                    "name": "list_tasks",
                    "description": "List all tasks in the CRM",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "default": 10,
                                "description": "Maximum number of tasks to return",
                            },
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_task",
                    "description": "Create a task, optionally linked to a record",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_title": {
                                "type": "string",
                                "description": "Title of the task",
                            },
                            "task_body": {
                                "type": "string",
                                "description": "Description",
                            },
                            "task_due_date": {
                                "type": "string",
                                "description": "Due date (ISO format)",
                            },
                            "task_status": {
                                "type": "string",
                                "enum": ["TODO", "IN_PROGRESS", "DONE"],
                                "description": "Status",
                            },
                            "task_target_id": {
                                "type": "string",
                                "description": "ID of record to link task to",
                            },
                            "task_target_type": {
                                "type": "string",
                                "enum": ["company", "person", "opportunity"],
                                "description": "Type of record",
                            },
                        },
                        "required": ["task_title"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "update_task",
                    "description": "Update an existing task",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "record_id": {
                                "type": "string",
                                "description": "ID of the task to update",
                            },
                            "task_title": {"type": "string"},
                            "task_body": {"type": "string"},
                            "task_due_date": {"type": "string"},
                        },
                        "required": ["record_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "complete_task",
                    "description": "Mark a task as complete",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "record_id": {
                                "type": "string",
                                "description": "ID of the task to complete",
                            },
                        },
                        "required": ["record_id"],
                    },
                },
            },
            # =================================================================
            # Submit Answer Tool
            # =================================================================
            {
                "type": "function",
                "function": {
                    "name": "submit_answer",
                    "description": "Submit final answer and end the session",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "answer": {
                                "type": "string",
                                "description": "The final answer based on CRM data",
                            },
                        },
                        "required": ["answer"],
                    },
                },
            },
        ]

    # =========================================================================
    # Tool Parsing and Observation Formatting
    # =========================================================================

    def parse_tool_call(self, tool_call: JsonDict) -> ParsedAction:
        """Parse a tool call from the LLM into a CrmAgentAction.

        This method maps tool names to action types and extracts arguments.
        Override this in a subclass to handle custom tools.

        Args:
            tool_call: Dictionary with 'name' and 'arguments' from LLM output.

        Returns:
            ParsedAction with the action and validity status.
        """
        tool_name = str(tool_call.get("name", "")).lower().strip()
        arguments_raw = tool_call.get("arguments")

        # Parse arguments
        if isinstance(arguments_raw, dict):
            arguments = cast(JsonDict, arguments_raw)
        elif isinstance(arguments_raw, str):
            try:
                arguments = json.loads(arguments_raw)
            except json.JSONDecodeError:
                return ParsedAction(
                    action=None,
                    is_valid=False,
                    error_message=f"Invalid JSON in arguments: {arguments_raw}",
                )
        else:
            return ParsedAction(
                action=None,
                is_valid=False,
                error_message=f"Arguments must be dict or JSON string, got: {type(arguments_raw)}",
            )

        # Map tool names to action types
        tool_to_action_type: dict[str, CRMActionType] = {
            # Company
            "list_companies": CRMActionType.LIST_COMPANIES,
            "get_company": CRMActionType.GET_COMPANY,
            "create_company": CRMActionType.CREATE_COMPANY,
            "update_company": CRMActionType.UPDATE_COMPANY,
            "delete_company": CRMActionType.DELETE_COMPANY,
            # Person
            "list_people": CRMActionType.LIST_PEOPLE,
            "get_person": CRMActionType.GET_PERSON,
            "create_person": CRMActionType.CREATE_PERSON,
            "update_person": CRMActionType.UPDATE_PERSON,
            "delete_person": CRMActionType.DELETE_PERSON,
            # Opportunity
            "list_opportunities": CRMActionType.LIST_OPPORTUNITIES,
            "get_opportunity": CRMActionType.GET_OPPORTUNITY,
            "create_opportunity": CRMActionType.CREATE_OPPORTUNITY,
            "update_opportunity": CRMActionType.UPDATE_OPPORTUNITY,
            "delete_opportunity": CRMActionType.DELETE_OPPORTUNITY,
            # Note
            "list_notes": CRMActionType.LIST_NOTES,
            "create_note": CRMActionType.CREATE_NOTE,
            # Task
            "list_tasks": CRMActionType.LIST_TASKS,
            "create_task": CRMActionType.CREATE_TASK,
            "update_task": CRMActionType.UPDATE_TASK,
            "complete_task": CRMActionType.COMPLETE_TASK,
            # Answer
            "submit_answer": CRMActionType.SUBMIT_ANSWER,
        }

        if not tool_name:
            return ParsedAction(
                action=None,
                is_valid=False,
                error_message="Tool name is required",
            )

        action_type = tool_to_action_type.get(tool_name)
        if action_type is None:
            return ParsedAction(
                action=None,
                is_valid=False,
                error_message=f"Unknown tool: '{tool_name}'. "
                f"Valid tools: {list(tool_to_action_type.keys())}",
            )

        # Build action with all valid fields
        action_kwargs: JsonDict = {"action_type": action_type}

        valid_fields = {
            "record_id",
            "company_name",
            "company_domain",
            "company_address",
            "company_employees",
            "person_first_name",
            "person_last_name",
            "person_email",
            "person_phone",
            "person_company_id",
            "person_job_title",
            "opportunity_name",
            "opportunity_amount",
            "opportunity_stage",
            "opportunity_close_date",
            "opportunity_company_id",
            "opportunity_person_id",
            "note_body",
            "note_target_id",
            "note_target_type",
            "task_title",
            "task_body",
            "task_due_date",
            "task_assignee_id",
            "task_status",
            "task_target_id",
            "task_target_type",
            "limit",
            "cursor",
            "starting_after",
            "ending_before",
            "order_by",
            "filter",
            "depth",
            "answer",
        }

        for field in valid_fields:
            if field in arguments and arguments[field] is not None:
                action_kwargs[field] = arguments[field]

        try:
            action = CrmAgentAction(**action_kwargs)
            return ParsedAction(action=action, is_valid=True)
        except Exception as e:
            return ParsedAction(
                action=None,
                is_valid=False,
                error_message=f"Failed to create action: {e}",
            )

    def format_observation(self, observation: CrmAgentObservation) -> str:
        """Format an observation as a string for the LLM.

        Override this in a subclass to customize how observations are
        presented to the agent.

        Args:
            observation: The observation to format.

        Returns:
            String representation for the LLM.

        Example:
            >>> class VerboseAgent(CrmAgentEnv):
            ...     def format_observation(self, obs):
            ...         base = super().format_observation(obs)
            ...         return f"=== CRM Response ===\\n{base}\\n=== End ==="
        """
        import json

        lines: list[str] = [json.dumps(observation.data)]

        if observation.error:
            lines.append(f"Error: {observation.error}")

        return "\n".join(lines)
