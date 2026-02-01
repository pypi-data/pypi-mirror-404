"""Data models for the CRM Agent Environment.

This module provides the core data types for interacting with the CRM Agent
Environment, including actions, observations, and state representations.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from openenv.core import Action, Observation, State
from pydantic import ConfigDict, Field


class CRMActionType(str, Enum):
    """Types of actions available in the CRM environment.

    Actions are grouped by the CRM entity they operate on:
    - Company: CRUD operations for company records
    - Person: CRUD operations for contact/person records
    - Opportunity: CRUD operations for sales opportunities
    - Note: Create and list notes attached to records
    - Task: CRUD operations for tasks
    - Answer: Submit final answer for evaluation
    """

    # Company actions
    CREATE_COMPANY = "create_company"
    UPDATE_COMPANY = "update_company"
    DELETE_COMPANY = "delete_company"
    LIST_COMPANIES = "list_companies"
    GET_COMPANY = "get_company"

    # Person/Contact actions
    CREATE_PERSON = "create_person"
    UPDATE_PERSON = "update_person"
    DELETE_PERSON = "delete_person"
    LIST_PEOPLE = "list_people"
    GET_PERSON = "get_person"

    # Opportunity actions
    CREATE_OPPORTUNITY = "create_opportunity"
    UPDATE_OPPORTUNITY = "update_opportunity"
    DELETE_OPPORTUNITY = "delete_opportunity"
    LIST_OPPORTUNITIES = "list_opportunities"
    GET_OPPORTUNITY = "get_opportunity"

    # Note actions
    CREATE_NOTE = "create_note"
    LIST_NOTES = "list_notes"

    # Task actions
    CREATE_TASK = "create_task"
    UPDATE_TASK = "update_task"
    COMPLETE_TASK = "complete_task"
    LIST_TASKS = "list_tasks"

    # Final answer
    SUBMIT_ANSWER = "submit_answer"


class CrmAgentAction(Action):
    """Action to execute in the CRM environment.

    This model represents all possible actions an agent can take. The `action_type`
    field determines which operation to perform, and the relevant fields for that
    action type should be populated.

    Example:
        >>> # List companies
        >>> action = CrmAgentAction(
        ...     action_type=CRMActionType.LIST_COMPANIES,
        ...     limit=10
        ... )

        >>> # Create a company
        >>> action = CrmAgentAction(
        ...     action_type=CRMActionType.CREATE_COMPANY,
        ...     company_name="Acme Corp",
        ...     company_domain="acme.com"
        ... )

        >>> # Submit final answer
        >>> action = CrmAgentAction(
        ...     action_type=CRMActionType.SUBMIT_ANSWER,
        ...     answer="The total revenue is $1.5M"
        ... )
    """

    model_config = ConfigDict(extra="allow")

    action_type: CRMActionType = Field(..., description="Type of CRM action to perform")

    # Common fields
    record_id: str | None = Field(
        default=None,
        description="ID of the record to operate on (for get/update/delete)",
    )

    # Company fields
    company_name: str | None = Field(default=None, description="Name of the company")
    company_domain: str | None = Field(
        default=None, description="Domain/website of the company"
    )
    company_address: str | None = Field(
        default=None, description="Address of the company"
    )
    company_employees: int | None = Field(
        default=None, description="Number of employees"
    )

    # Person fields
    person_first_name: str | None = Field(
        default=None, description="First name of the person"
    )
    person_last_name: str | None = Field(
        default=None, description="Last name of the person"
    )
    person_email: str | None = Field(default=None, description="Email of the person")
    person_phone: str | None = Field(
        default=None, description="Phone number of the person"
    )
    person_company_id: str | None = Field(
        default=None, description="ID of the company this person belongs to"
    )
    person_job_title: str | None = Field(
        default=None, description="Job title of the person"
    )

    # Opportunity fields
    opportunity_name: str | None = Field(
        default=None, description="Name of the opportunity"
    )
    opportunity_amount: float | None = Field(default=None, description="Deal amount")
    opportunity_stage: str | None = Field(
        default=None,
        description="Stage: 'NEW', 'MEETING', 'PROPOSAL', 'WON', or 'LOST'",
    )
    opportunity_close_date: str | None = Field(
        default=None, description="Expected close date (ISO format)"
    )
    opportunity_company_id: str | None = Field(
        default=None, description="ID of the company for this opportunity"
    )
    opportunity_person_id: str | None = Field(
        default=None, description="ID of the contact person for this opportunity"
    )

    # Note fields
    note_body: str | None = Field(default=None, description="Content of the note")
    note_title: str | None = Field(default=None, description="Title of the note")
    note_target_person_id: str | None = Field(
        default=None, description="ID of the person to link this note to"
    )
    note_target_company_id: str | None = Field(
        default=None, description="ID of the company to link this note to"
    )
    note_target_opportunity_id: str | None = Field(
        default=None, description="ID of the opportunity to link this note to"
    )

    # Task fields
    task_title: str | None = Field(default=None, description="Title of the task")
    task_body: str | None = Field(default=None, description="Description of the task")
    task_due_date: str | None = Field(default=None, description="Due date (ISO format)")
    task_assignee_id: str | None = Field(
        default=None, description="ID of the user to assign the task to"
    )
    task_status: str | None = Field(default=None, description="Status of the task")
    task_target_person_id: str | None = Field(
        default=None, description="ID of the person to link this task to"
    )
    task_target_company_id: str | None = Field(
        default=None, description="ID of the company to link this task to"
    )
    task_target_opportunity_id: str | None = Field(
        default=None, description="ID of the opportunity to link this task to"
    )

    # Final answer
    answer: str | None = Field(default=None, description="The final answer to submit")

    # Pagination and filtering
    limit: int | None = Field(
        default=60, description="Maximum number of results to return (max 200)"
    )
    cursor: str | None = Field(
        default=None, description="Pagination cursor (legacy, use starting_after)"
    )
    starting_after: str | None = Field(
        default=None, description="Returns objects starting after this cursor"
    )
    ending_before: str | None = Field(
        default=None, description="Returns objects ending before this cursor"
    )
    order_by: str | None = Field(
        default=None, description="Order by: field_name_1,field_name_2[DIRECTION]"
    )
    filter: str | None = Field(
        default=None, description="Filter: field[COMPARATOR]:value"
    )
    depth: int | None = Field(
        default=1, description="Nesting depth: 0=primary, 1=direct relations"
    )


class CrmAgentObservation(Observation):
    """Observation returned after executing an action.

    Contains the result of the action, including any data returned by the CRM
    and error information if the action failed.

    Attributes:
        success: Whether the action completed successfully.
        error: Error message if the action failed, None otherwise.
        data: Raw response data from the CRM server.
        done: Whether the episode has ended (inherited from Observation).
        reward: Reward signal if applicable (inherited from Observation).
    """

    success: bool = Field(default=True, description="Whether the action succeeded")
    error: str | None = Field(
        default=None, description="Error message if action failed"
    )
    data: dict[str, Any] = Field(
        default_factory=dict, description="Raw response data from server"
    )


class CrmAgentState(State):
    """Internal state of the CRM environment session.

    Tracks metadata about the current episode including entity counts
    and session information.

    Attributes:
        env_name: Name of the environment.
        done: Whether the episode has ended.
        terminated: Whether the episode terminated normally.
        truncated: Whether the episode was truncated (e.g., step limit).
        success: Whether the task was completed successfully.
        companies_count: Number of companies in the CRM.
        people_count: Number of people/contacts in the CRM.
        opportunities_count: Number of opportunities in the CRM.
        last_action: String representation of the last action taken.
        api_url: The CRM API endpoint URL.
    """

    env_name: str = "crm-agent"
    done: bool = False
    terminated: bool = False
    truncated: bool = False
    success: bool = False
    companies_count: int = 0
    people_count: int = 0
    opportunities_count: int = 0
    last_action: str | None = None
    api_url: str = ""
