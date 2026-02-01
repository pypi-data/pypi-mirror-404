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
from .tools import DEFAULT_TOOLS

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
                "Contact hello@construct-labs.com to obtain an API key."
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
                    "Contact hello@construct-labs.com if you need assistance."
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

## GOAL

Complete CRM tasks by creating, updating, retrieving, and managing business data.

## DATA MODEL

- Companies: Organizations you do business with
- People: Contacts who work at companies (linked via person_company_id)
- Opportunities: Sales deals linked to a company and a person (point of contact)
- Notes: Free-text records attached to any company, person, or opportunity
- Tasks: Action items with due dates, attached to any company, person, or opportunity

## AVAILABLE TOOLS

- Companies: list_companies, get_company, create_company, update_company, delete_company
- People: list_people, get_person, create_person, update_person, delete_person
- Opportunities: list_opportunities, get_opportunity, create_opportunity, update_opportunity, delete_opportunity
- Notes: list_notes, create_note
- Tasks: list_tasks, create_task, update_task, complete_task
- Answer: submit_answer

## FILTERING AND PAGINATION

Use the filter parameter to search records. Format: field[comparator]:value

Comparators: eq, neq, gt, gte, lt, lte, ilike (case-insensitive like), in, is, startsWith, containsAny

Examples:
- name[ilike]:"%acme%" - names containing "acme"
- stage[eq]:"WON" - opportunities with stage WON
- amount[gte]:10000 - deals worth $10,000 or more
- createdAt[gte]:"2026-01-01" - records created this year
- deletedAt[is]:NULL - non-deleted records

Rules: Quote strings and dates. Do not quote numbers. Combine with comma for AND: field1[eq]:"a",field2[gt]:5

Pagination: Results return max 60 records. Use starting_after with the endCursor from pageInfo to get more.

## WORKFLOW

For complex tasks, make multiple tool calls:
1. First, list or search to find relevant records
2. Then, get details or create/update as needed
3. Finally, call submit_answer with your findings

## OUTPUT FORMAT

Think briefly about which tool to use, then output exactly one tool call:
<tool_call>
{"name": "tool_name", "arguments": {...}}
</tool_call>

## EXAMPLES

List companies:
<tool_call>
{"name": "list_companies", "arguments": {"limit": 10}}
</tool_call>

Find companies by name:
<tool_call>
{"name": "list_companies", "arguments": {"filter": "name[ilike]:\"%tech%\""}}
</tool_call>

Create a company:
<tool_call>
{"name": "create_company", "arguments": {"company_name": "Acme Corp", "company_domain": "acme.com"}}
</tool_call>

Create a contact linked to a company:
<tool_call>
{"name": "create_person", "arguments": {"person_first_name": "John", "person_last_name": "Doe", "person_email": "john@acme.com", "person_company_id": "company-uuid-here"}}
</tool_call>

Submit final answer:
<tool_call>
{"name": "submit_answer", "arguments": {"answer": "The total pipeline value is $1.5M across 12 open opportunities."}}
</tool_call>"""

    @property
    def tools(self) -> list[JsonDict]:
        """Tool definitions for the CRM environment.

        Returns tool definitions formatted by `format_tools()`. Override
        `format_tools()` to transform the tool schema for different providers
        (e.g., Anthropic, Google).

        Returns:
            List of tool definitions (OpenAI format by default).

        Example:
            >>> class ReadOnlyAgent(CrmAgentEnv):
            ...     @property
            ...     def tools(self) -> list[dict]:
            ...         # Only allow read operations
            ...         read_ops = {'list_', 'get_', 'submit_answer'}
            ...         return [t for t in self._default_tools()
            ...                 if any(op in t['function']['name'] for op in read_ops)]
        """
        return self.format_tools(self._default_tools())

    def format_tools(self, tools: list[JsonDict]) -> list[JsonDict]:
        """Format tool definitions for the target LLM provider.

        Override this method to transform tool schemas for different providers.
        The default implementation returns OpenAI-compatible format unchanged.

        Args:
            tools: List of tool definitions in OpenAI format.

        Returns:
            Formatted tool definitions for your target provider.

        Example (Anthropic format):
            >>> class AnthropicCrmAgent(CrmAgentEnv):
            ...     def format_tools(self, tools):
            ...         # Convert OpenAI format to Anthropic format
            ...         return [
            ...             {
            ...                 "name": t["function"]["name"],
            ...                 "description": t["function"]["description"],
            ...                 "input_schema": t["function"]["parameters"],
            ...             }
            ...             for t in tools
            ...         ]
        """
        return tools

    def _default_tools(self) -> list[JsonDict]:
        """Return the default tool definitions.

        Subclasses can call this to get all default tools and filter/extend them.

        Returns:
            Complete list of CRM tool definitions in OpenAI format.
        """
        return list(DEFAULT_TOOLS)

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

        # Convert generic note_target_id/type to specific fields
        # Tool schema uses: note_target_id + note_target_type
        # Server expects: note_target_person_id, note_target_company_id, etc.
        note_target_id = action_kwargs.pop("note_target_id", None)
        note_target_type = action_kwargs.pop("note_target_type", None)
        if note_target_id and note_target_type:
            target_type = str(note_target_type).lower()
            if target_type == "person":
                action_kwargs["note_target_person_id"] = note_target_id
            elif target_type == "company":
                action_kwargs["note_target_company_id"] = note_target_id
            elif target_type == "opportunity":
                action_kwargs["note_target_opportunity_id"] = note_target_id

        # Same conversion for tasks
        task_target_id = action_kwargs.pop("task_target_id", None)
        task_target_type = action_kwargs.pop("task_target_type", None)
        if task_target_id and task_target_type:
            target_type = str(task_target_type).lower()
            if target_type == "person":
                action_kwargs["task_target_person_id"] = task_target_id
            elif target_type == "company":
                action_kwargs["task_target_company_id"] = task_target_id
            elif target_type == "opportunity":
                action_kwargs["task_target_opportunity_id"] = task_target_id

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
