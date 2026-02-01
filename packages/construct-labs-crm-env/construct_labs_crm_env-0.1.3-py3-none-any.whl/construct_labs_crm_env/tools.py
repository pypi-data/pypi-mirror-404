"""Tool definitions for the CRM Agent Environment.

This module contains the static tool definitions in OpenAI function calling format.
These define the available actions an agent can take in the CRM environment.
"""

from typing import Any

# Type alias for tool definitions
ToolDefinition = dict[str, Any]

# =============================================================================
# Company Tools
# =============================================================================

LIST_COMPANIES: ToolDefinition = {
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
}

GET_COMPANY: ToolDefinition = {
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
}

CREATE_COMPANY: ToolDefinition = {
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
}

UPDATE_COMPANY: ToolDefinition = {
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
}

DELETE_COMPANY: ToolDefinition = {
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
}

# =============================================================================
# Person/Contact Tools
# =============================================================================

LIST_PEOPLE: ToolDefinition = {
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
}

GET_PERSON: ToolDefinition = {
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
}

CREATE_PERSON: ToolDefinition = {
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
}

UPDATE_PERSON: ToolDefinition = {
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
}

DELETE_PERSON: ToolDefinition = {
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
}

# =============================================================================
# Opportunity Tools
# =============================================================================

LIST_OPPORTUNITIES: ToolDefinition = {
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
}

GET_OPPORTUNITY: ToolDefinition = {
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
}

CREATE_OPPORTUNITY: ToolDefinition = {
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
}

UPDATE_OPPORTUNITY: ToolDefinition = {
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
}

DELETE_OPPORTUNITY: ToolDefinition = {
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
}

# =============================================================================
# Note Tools
# =============================================================================

LIST_NOTES: ToolDefinition = {
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
}

CREATE_NOTE: ToolDefinition = {
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
}

# =============================================================================
# Task Tools
# =============================================================================

LIST_TASKS: ToolDefinition = {
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
}

CREATE_TASK: ToolDefinition = {
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
}

UPDATE_TASK: ToolDefinition = {
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
}

COMPLETE_TASK: ToolDefinition = {
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
}

# =============================================================================
# Submit Answer Tool
# =============================================================================

SUBMIT_ANSWER: ToolDefinition = {
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
}

# =============================================================================
# All Tools - Combined list
# =============================================================================

DEFAULT_TOOLS: list[ToolDefinition] = [
    # Company
    LIST_COMPANIES,
    GET_COMPANY,
    CREATE_COMPANY,
    UPDATE_COMPANY,
    DELETE_COMPANY,
    # Person
    LIST_PEOPLE,
    GET_PERSON,
    CREATE_PERSON,
    UPDATE_PERSON,
    DELETE_PERSON,
    # Opportunity
    LIST_OPPORTUNITIES,
    GET_OPPORTUNITY,
    CREATE_OPPORTUNITY,
    UPDATE_OPPORTUNITY,
    DELETE_OPPORTUNITY,
    # Note
    LIST_NOTES,
    CREATE_NOTE,
    # Task
    LIST_TASKS,
    CREATE_TASK,
    UPDATE_TASK,
    COMPLETE_TASK,
    # Answer
    SUBMIT_ANSWER,
]
