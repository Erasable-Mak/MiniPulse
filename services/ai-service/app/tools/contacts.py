import structlog
from typing import Dict, Any

logger = structlog.get_logger(__name__)
from ..ai_enums import HubSpotObjectType, HubSpotOperator

async def get_contact_by_email(client, email: str) -> Dict[str, Any]:
    """Look up a CRM contact by their exact email address."""
    filters = [
        {"propertyName": "email", "operator": HubSpotOperator.EQ, "value": email}
    ]
    properties = ["firstname", "lastname", "email", "jobtitle", "company"]

    result = await client.search_objects(HubSpotObjectType.CONTACTS, filters, properties)
    if "error" in result:
        return result

    results = result.get("results", [])
    if not results:
        return {"found": False, "contact": None}

    props = results[0].get("properties", {})
    return {
        "found": True,
        "contact": {
            "first_name": props.get("firstname", ""),
            "last_name": props.get("lastname", ""),
            "email": props.get("email", ""),
            "job_title": props.get("jobtitle", ""),
            "company": props.get("company", "")
        }
    }
