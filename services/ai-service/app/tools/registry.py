"""Tool registry mapping function names to implementations and JSON schema definitions."""

from .deals import count_deals_by_stage, search_deals, get_recent_deals_closed
from .contacts import get_contact_by_email

TOOL_MAP = {
    "count_deals_by_stage": count_deals_by_stage,
    "search_deals": search_deals,
    "get_recent_deals_closed": get_recent_deals_closed,
    "get_contact_by_email": get_contact_by_email,
}

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "count_deals_by_stage",
            "description": "Count the number of deals in a specific pipeline stage and get a summary list of those deals.",
            "parameters": {
                "type": "object",
                "properties": {
                    "stage_name": {
                        "type": "string",
                        "description": "The name of the deal stage (e.g., 'Qualified', 'Closed Won', 'Negotiation')."
                    }
                },
                "required": ["stage_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_deals",
            "description": "Search for deals by name, minimum amount, and optionally by stage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term to match against the deal name."
                    },
                    "min_amount": {
                        "type": "number",
                        "description": "Minimum value of the deal to include."
                    },
                    "stage": {
                        "type": "string",
                        "description": "Optional deal stage filter (e.g., 'open', 'closed won')."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return. Default is 10."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_deals_closed",
            "description": "Get a list and summary of deals that were closed won in the last N days.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back for closed deals. Default is 30."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_contact_by_email",
            "description": "Find a contact in the CRM by their email address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "The exact email address of the contact."
                    }
                },
                "required": ["email"]
            }
        }
    }
]
