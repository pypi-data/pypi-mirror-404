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
        "description": "List all companies in the CRM. Use filters to search by name, domain, or employee count. Response includes pageInfo with hasNextPage, startCursor, and endCursor for pagination.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 60,
                    "description": "Maximum number of companies to return (1-60). Default and max is 60.",
                },
                "starting_after": {
                    "type": "string",
                    "description": "Cursor for forward pagination - returns companies after this cursor. Use endCursor from previous response's pageInfo.",
                },
                "ending_before": {
                    "type": "string",
                    "description": "Cursor for backward pagination - returns companies before this cursor. Use startCursor from previous response's pageInfo.",
                },
                "order_by": {
                    "type": "string",
                    "description": "Sort order in format 'field[ASC|DESC]'. Examples: 'name[ASC]', 'createdAt[DESC]', 'employees[DESC]'.",
                },
                "filter": {
                    "type": "string",
                    "description": "Filter in format 'field[comparator]:value'. Comparators: eq, neq, gt, gte, lt, lte, in, is, like, ilike, startsWith, containsAny. Quote strings/dates, not numbers. Multiple conditions with comma (AND). Examples: 'name[ilike]:\"%acme%\"', 'employees[gte]:100', 'deletedAt[is]:NULL'. Advanced: 'or(status[eq]:\"active\",employees[gt]:50)'.",
                },
                "depth": {
                    "type": "integer",
                    "default": 1,
                    "description": "Relation depth: 0 returns only company fields, 1 includes related people and opportunities. Default is 1.",
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
        "description": "Get full details of a specific company by its ID, including related contacts and opportunities.",
        "parameters": {
            "type": "object",
            "properties": {
                "record_id": {
                    "type": "string",
                    "description": "The unique identifier (UUID) of the company to retrieve. Get this from list_companies.",
                },
                "depth": {
                    "type": "integer",
                    "default": 1,
                    "description": "Relation depth: 0 returns only company fields, 1 includes related people and opportunities. Default is 1.",
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
        "description": "Create a new company in the CRM. Name is required; add domain, address, and employee count for a complete record.",
        "parameters": {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": "The official name of the company (required). Example: 'Acme Corporation'.",
                },
                "company_domain": {
                    "type": "string",
                    "description": "The company's website domain without protocol. Example: 'acme.com' (not 'https://acme.com').",
                },
                "company_address": {
                    "type": "string",
                    "description": "The company's physical address. Example: '123 Main St, San Francisco, CA 94102'.",
                },
                "company_employees": {
                    "type": "integer",
                    "description": "Approximate number of employees at the company. Example: 250.",
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
        "description": "Update an existing company. Only include fields you want to change.",
        "parameters": {
            "type": "object",
            "properties": {
                "record_id": {
                    "type": "string",
                    "description": "The unique identifier (UUID) of the company to update. Get this from list_companies or get_company.",
                },
                "company_name": {
                    "type": "string",
                    "description": "New name for the company. Leave out to keep unchanged.",
                },
                "company_domain": {
                    "type": "string",
                    "description": "New website domain (e.g., 'acme.com'). Leave out to keep unchanged.",
                },
                "company_address": {
                    "type": "string",
                    "description": "New physical address. Leave out to keep unchanged.",
                },
                "company_employees": {
                    "type": "integer",
                    "description": "Updated employee count. Leave out to keep unchanged.",
                },
            },
            "required": ["record_id"],
        },
    },
}

DELETE_COMPANY: ToolDefinition = {
    "type": "function",
    "function": {
        "name": "delete_company",
        "description": "Permanently delete a company from the CRM. This may also affect related contacts and opportunities.",
        "parameters": {
            "type": "object",
            "properties": {
                "record_id": {
                    "type": "string",
                    "description": "The unique identifier (UUID) of the company to delete. Get this from list_companies or get_company. This action cannot be undone.",
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
        "description": "List all contacts/people in the CRM. Use filters to search by name, email, company, or job title. Response includes pageInfo with hasNextPage, startCursor, and endCursor for pagination.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 60,
                    "description": "Maximum number of contacts to return (1-60). Default and max is 60.",
                },
                "starting_after": {
                    "type": "string",
                    "description": "Cursor for forward pagination - returns contacts after this cursor. Use endCursor from previous response's pageInfo.",
                },
                "ending_before": {
                    "type": "string",
                    "description": "Cursor for backward pagination - returns contacts before this cursor. Use startCursor from previous response's pageInfo.",
                },
                "order_by": {
                    "type": "string",
                    "description": "Sort order in format 'field[ASC|DESC]'. Examples: 'name.firstName[ASC]', 'createdAt[DESC]', 'email[ASC]'.",
                },
                "filter": {
                    "type": "string",
                    "description": "Filter in format 'field[comparator]:value'. Comparators: eq, neq, gt, gte, lt, lte, in, is, like, ilike, startsWith, containsAny. Quote strings/dates, not numbers. Use dot notation for nested fields. Examples: 'email[ilike]:\"%@acme.com\"', 'name.firstName[eq]:\"John\"', 'company.name[ilike]:\"%tech%\"'. Advanced: 'or(jobTitle[ilike]:\"%CEO%\",jobTitle[ilike]:\"%CTO%\")'.",
                },
                "depth": {
                    "type": "integer",
                    "default": 1,
                    "description": "Relation depth: 0 returns only person fields, 1 includes related company data. Default is 1.",
                },
            },
            "required": [],
        },
    },
}

GET_PERSON: ToolDefinition = {
    "type": "function",
    "function": {
        "name": "get_person",
        "description": "Get full details of a specific contact/person by their ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "record_id": {
                    "type": "string",
                    "description": "The unique identifier (UUID) of the contact to retrieve. Get this from list_people.",
                },
                "depth": {
                    "type": "integer",
                    "default": 1,
                    "description": "Relation depth: 0 returns only person fields, 1 includes related company and opportunity data. Default is 1.",
                },
            },
            "required": ["record_id"],
        },
    },
}

CREATE_PERSON: ToolDefinition = {
    "type": "function",
    "function": {
        "name": "create_person",
        "description": "Create a new contact/person in the CRM. First and last name are required; other fields are optional.",
        "parameters": {
            "type": "object",
            "properties": {
                "person_first_name": {
                    "type": "string",
                    "description": "The contact's first name (required).",
                },
                "person_last_name": {
                    "type": "string",
                    "description": "The contact's last name (required).",
                },
                "person_email": {
                    "type": "string",
                    "description": "The contact's email address. Format: 'user@domain.com'.",
                },
                "person_phone": {
                    "type": "string",
                    "description": "The contact's phone number. Any format accepted (e.g., '+1-555-123-4567').",
                },
                "person_company_id": {
                    "type": "string",
                    "description": "UUID of the company this person works for. Get this from list_companies or create_company.",
                },
                "person_job_title": {
                    "type": "string",
                    "description": "The contact's job title or role (e.g., 'CEO', 'Sales Manager', 'Software Engineer').",
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
        "description": "Update an existing contact. Only include fields you want to change.",
        "parameters": {
            "type": "object",
            "properties": {
                "record_id": {
                    "type": "string",
                    "description": "The unique identifier (UUID) of the contact to update. Get this from list_people or get_person.",
                },
                "person_first_name": {
                    "type": "string",
                    "description": "New first name. Leave out to keep unchanged.",
                },
                "person_last_name": {
                    "type": "string",
                    "description": "New last name. Leave out to keep unchanged.",
                },
                "person_email": {
                    "type": "string",
                    "description": "New email address. Leave out to keep unchanged.",
                },
                "person_phone": {
                    "type": "string",
                    "description": "New phone number. Leave out to keep unchanged.",
                },
                "person_job_title": {
                    "type": "string",
                    "description": "New job title. Leave out to keep unchanged.",
                },
            },
            "required": ["record_id"],
        },
    },
}

DELETE_PERSON: ToolDefinition = {
    "type": "function",
    "function": {
        "name": "delete_person",
        "description": "Permanently delete a contact/person from the CRM. This may also affect related opportunities and notes.",
        "parameters": {
            "type": "object",
            "properties": {
                "record_id": {
                    "type": "string",
                    "description": "The unique identifier (UUID) of the contact to delete. Get this from list_people or get_person. This action cannot be undone.",
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
        "description": "List all opportunities/deals in the CRM. Use filters to search by stage, amount, company, or close date. Response includes pageInfo with hasNextPage, startCursor, and endCursor for pagination.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 60,
                    "description": "Maximum number of opportunities to return (1-60). Default and max is 60.",
                },
                "starting_after": {
                    "type": "string",
                    "description": "Cursor for forward pagination - returns opportunities after this cursor. Use endCursor from previous response's pageInfo.",
                },
                "ending_before": {
                    "type": "string",
                    "description": "Cursor for backward pagination - returns opportunities before this cursor. Use startCursor from previous response's pageInfo.",
                },
                "order_by": {
                    "type": "string",
                    "description": "Sort order in format 'field[ASC|DESC]'. Examples: 'amount[DESC]', 'closeDate[ASC]', 'stage[ASC]'.",
                },
                "filter": {
                    "type": "string",
                    "description": "Filter in format 'field[comparator]:value'. Comparators: eq, neq, gt, gte, lt, lte, in, is, like, ilike, startsWith, containsAny. Quote strings/dates, not numbers. Examples: 'stage[eq]:\"WON\"', 'amount[gte]:10000', 'closeDate[gte]:\"2026-01-01\"', 'company.name[ilike]:\"%acme%\"'. Advanced: 'or(stage[eq]:\"WON\",stage[eq]:\"PROPOSAL\")'.",
                },
                "depth": {
                    "type": "integer",
                    "default": 1,
                    "description": "Relation depth: 0 returns only opportunity fields, 1 includes related company and person data. Default is 1.",
                },
            },
            "required": [],
        },
    },
}

GET_OPPORTUNITY: ToolDefinition = {
    "type": "function",
    "function": {
        "name": "get_opportunity",
        "description": "Get full details of a specific opportunity/deal by its ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "record_id": {
                    "type": "string",
                    "description": "The unique identifier (UUID) of the opportunity to retrieve. Get this from list_opportunities.",
                },
                "depth": {
                    "type": "integer",
                    "default": 1,
                    "description": "Relation depth: 0 returns only opportunity fields, 1 includes related company and person data. Default is 1.",
                },
            },
            "required": ["record_id"],
        },
    },
}

CREATE_OPPORTUNITY: ToolDefinition = {
    "type": "function",
    "function": {
        "name": "create_opportunity",
        "description": "Create a new sales opportunity/deal in the CRM. Name is required; link to company and contact for full tracking.",
        "parameters": {
            "type": "object",
            "properties": {
                "opportunity_name": {
                    "type": "string",
                    "description": "A descriptive name for the deal (required). Example: 'Acme Corp - Enterprise License Q1'.",
                },
                "opportunity_amount": {
                    "type": "number",
                    "description": "The monetary value of the deal in dollars. Example: 50000 for a $50,000 deal.",
                },
                "opportunity_stage": {
                    "type": "string",
                    "enum": ["NEW", "MEETING", "PROPOSAL", "WON", "LOST"],
                    "description": "Current stage in the sales pipeline. NEW: initial lead, MEETING: scheduled/had meeting, PROPOSAL: sent proposal, WON: closed won, LOST: closed lost.",
                },
                "opportunity_close_date": {
                    "type": "string",
                    "description": "Expected or actual close date in ISO 8601 format. Example: '2026-03-15' or '2026-03-15T00:00:00Z'.",
                },
                "opportunity_company_id": {
                    "type": "string",
                    "description": "UUID of the company this opportunity is with. Get this from list_companies or create_company.",
                },
                "opportunity_person_id": {
                    "type": "string",
                    "description": "UUID of the primary contact/person for this deal. Get this from list_people or create_person.",
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
        "description": "Update an existing opportunity. Only include fields you want to change. Use this to advance deals through the pipeline.",
        "parameters": {
            "type": "object",
            "properties": {
                "record_id": {
                    "type": "string",
                    "description": "The unique identifier (UUID) of the opportunity to update. Get this from list_opportunities or get_opportunity.",
                },
                "opportunity_name": {
                    "type": "string",
                    "description": "New name for the opportunity. Leave out to keep unchanged.",
                },
                "opportunity_amount": {
                    "type": "number",
                    "description": "Updated deal value in dollars. Leave out to keep unchanged.",
                },
                "opportunity_stage": {
                    "type": "string",
                    "enum": ["NEW", "MEETING", "PROPOSAL", "WON", "LOST"],
                    "description": "New pipeline stage. NEW: initial lead, MEETING: scheduled/had meeting, PROPOSAL: sent proposal, WON: closed won, LOST: closed lost.",
                },
                "opportunity_close_date": {
                    "type": "string",
                    "description": "Updated close date in ISO 8601 format (e.g., '2026-03-15'). Leave out to keep unchanged.",
                },
            },
            "required": ["record_id"],
        },
    },
}

DELETE_OPPORTUNITY: ToolDefinition = {
    "type": "function",
    "function": {
        "name": "delete_opportunity",
        "description": "Permanently delete an opportunity/deal from the CRM. Consider marking as LOST instead to preserve history.",
        "parameters": {
            "type": "object",
            "properties": {
                "record_id": {
                    "type": "string",
                    "description": "The unique identifier (UUID) of the opportunity to delete. Get this from list_opportunities or get_opportunity. This action cannot be undone.",
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
        "description": "List all notes in the CRM. Notes are attached to companies, people, or opportunities and contain meeting summaries, call logs, and updates.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum number of notes to return. Default is 10. Use higher values to see more history.",
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
        "description": "Create a note attached to a company, person, or opportunity. Use for meeting notes, call logs, important updates.",
        "parameters": {
            "type": "object",
            "properties": {
                "note_body": {
                    "type": "string",
                    "description": "The text content of the note (required). Can include meeting summaries, call notes, action items, etc.",
                },
                "note_target_id": {
                    "type": "string",
                    "description": "UUID of the record to attach this note to. Get from list_companies, list_people, or list_opportunities.",
                },
                "note_target_type": {
                    "type": "string",
                    "enum": ["company", "person", "opportunity"],
                    "description": "The type of record to attach to: 'company', 'person', or 'opportunity'. Must match the type of note_target_id.",
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
        "description": "List all tasks in the CRM. Tasks represent follow-ups, reminders, and action items that may be linked to companies, people, or opportunities.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum number of tasks to return. Default is 10. Use higher values to see more tasks.",
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
        "description": "Create a follow-up task, optionally linked to a company, person, or opportunity. Use for reminders, action items, and scheduled activities.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_title": {
                    "type": "string",
                    "description": "Short title describing the task (required). Example: 'Follow up on proposal', 'Schedule demo call'.",
                },
                "task_body": {
                    "type": "string",
                    "description": "Detailed description of what needs to be done. Include context, steps, or relevant information.",
                },
                "task_due_date": {
                    "type": "string",
                    "description": "When the task should be completed, in ISO 8601 format. Example: '2026-02-15' or '2026-02-15T14:00:00Z'.",
                },
                "task_status": {
                    "type": "string",
                    "enum": ["TODO", "IN_PROGRESS", "DONE"],
                    "description": "Current status: TODO (not started), IN_PROGRESS (being worked on), DONE (completed). Defaults to TODO if not specified.",
                },
                "task_target_id": {
                    "type": "string",
                    "description": "UUID of the record to link this task to. Get from list_companies, list_people, or list_opportunities.",
                },
                "task_target_type": {
                    "type": "string",
                    "enum": ["company", "person", "opportunity"],
                    "description": "The type of record to link to: 'company', 'person', or 'opportunity'. Must match the type of task_target_id.",
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
        "description": "Update an existing task. Only include fields you want to change. Use complete_task to mark as done.",
        "parameters": {
            "type": "object",
            "properties": {
                "record_id": {
                    "type": "string",
                    "description": "The unique identifier (UUID) of the task to update. Get this from list_tasks.",
                },
                "task_title": {
                    "type": "string",
                    "description": "New title for the task. Leave out to keep unchanged.",
                },
                "task_body": {
                    "type": "string",
                    "description": "New description for the task. Leave out to keep unchanged.",
                },
                "task_due_date": {
                    "type": "string",
                    "description": "New due date in ISO 8601 format (e.g., '2026-02-15'). Leave out to keep unchanged.",
                },
            },
            "required": ["record_id"],
        },
    },
}

COMPLETE_TASK: ToolDefinition = {
    "type": "function",
    "function": {
        "name": "complete_task",
        "description": "Mark a task as complete (sets status to DONE). Use this when a task has been finished.",
        "parameters": {
            "type": "object",
            "properties": {
                "record_id": {
                    "type": "string",
                    "description": "The unique identifier (UUID) of the task to mark as complete. Get this from list_tasks.",
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
        "description": "Submit your final answer to complete the task. Call this when you have gathered all necessary information and are ready to respond. This ends the session.",
        "parameters": {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "Your complete answer to the user's question, based on the CRM data you retrieved. Be specific and include relevant details like names, amounts, dates, or counts.",
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
