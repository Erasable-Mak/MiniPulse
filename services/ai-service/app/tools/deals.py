"""HubSpot deal query tools for the LLM orchestrator."""

import structlog
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone

logger = structlog.get_logger(__name__)
from ..ai_enums import HubSpotObjectType, HubSpotOperator, DealStage

STAGE_MAPPING = {
    "qualified": DealStage.QUALIFIED,
    "appointment scheduled": DealStage.APPOINTMENT_SCHEDULED,
    "presentation scheduled": DealStage.PRESENTATION_SCHEDULED,
    "decision maker bought in": DealStage.DECISION_MAKER_BOUGHT_IN,
    "contract sent": DealStage.CONTRACT_SENT,
    "closed won": DealStage.CLOSED_WON,
    "closed lost": DealStage.CLOSED_LOST,
}

def _map_stage(stage_name: str) -> str:
    """Map a human-readable stage name to its HubSpot internal identifier."""
    cleaned = stage_name.strip().lower()
    return STAGE_MAPPING.get(cleaned, cleaned)

async def _enrich_with_owners(client, deals_list: list) -> None:
    """Enrich a list of deal dicts with resolved owner names."""
    for deal in deals_list:
        owner_id = deal.get("owner_id")
        if owner_id:
            owner_data = await client.get_owner(owner_id)
            if "error" not in owner_data:
                first = owner_data.get("first_name", "")
                last = owner_data.get("last_name", "")
                deal["owner"] = f"{first} {last}".strip()
            else:
                deal["owner"] = "Unknown"
        else:
            deal["owner"] = "Unassigned"

async def count_deals_by_stage(client, stage_name: str) -> Dict[str, Any]:
    """Count deals in a specific pipeline stage and return a summary with total value."""
    internal_stage = _map_stage(stage_name)
    filters = [
        {"propertyName": "dealstage", "operator": HubSpotOperator.EQ, "value": internal_stage}
    ]
    properties = ["dealname", "amount", "dealstage", "closedate", "createdate", "hubspot_owner_id"]

    result = await client.search_objects(HubSpotObjectType.DEALS, filters, properties)
    if "error" in result:
        return result

    results = result.get("results", [])
    deals = []
    total_value = 0.0

    for r in results:
        props = r.get("properties", {})
        amt = float(props.get("amount") or 0.0)
        total_value += amt
        deals.append({
            "name": props.get("dealname", "Unnamed Deal"),
            "amount": amt,
            "owner_id": props.get("hubspot_owner_id")
        })

    await _enrich_with_owners(client, deals)

    for d in deals:
        d.pop("owner_id", None)

    return {
        "count": len(deals),
        "total_value": total_value,
        "deals": deals
    }

async def search_deals(
    client, query: str = "", min_amount: float = 0, stage: Optional[str] = None, limit: int = 10
) -> Dict[str, Any]:
    """Search for deals by name, minimum amount, and optionally by stage."""
    filters = []
    if query:
        filters.append({"propertyName": "dealname", "operator": HubSpotOperator.CONTAINS_TOKEN, "value": query})
    if min_amount > 0:
        filters.append({"propertyName": "amount", "operator": HubSpotOperator.GTE, "value": str(min_amount)})
    if stage:
        internal_stage = _map_stage(stage)
        filters.append({"propertyName": "dealstage", "operator": HubSpotOperator.EQ, "value": internal_stage})

    properties = ["dealname", "amount", "dealstage", "closedate", "hubspot_owner_id"]
    result = await client.search_objects(HubSpotObjectType.DEALS, filters, properties)

    if "error" in result:
        return result

    results = result.get("results", [])[:limit]
    deals = []

    for r in results:
        props = r.get("properties", {})
        amt = float(props.get("amount") or 0.0)
        deals.append({
            "name": props.get("dealname", "Unnamed Deal"),
            "amount": amt,
            "stage": props.get("dealstage", ""),
            "close_date": props.get("closedate"),
            "owner_id": props.get("hubspot_owner_id")
        })

    await _enrich_with_owners(client, deals)

    for d in deals:
        d.pop("owner_id", None)

    return {
        "deals": deals,
        "total_count": len(deals)
    }

async def get_recent_deals_closed(client, days: int = 30) -> Dict[str, Any]:
    """Retrieve deals closed won within the last N days with total value summary."""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_ms = int(cutoff_date.timestamp() * 1000)

    filters = [
        {"propertyName": "dealstage", "operator": HubSpotOperator.EQ, "value": DealStage.CLOSED_WON},
        {"propertyName": "closedate", "operator": HubSpotOperator.GTE, "value": str(cutoff_ms)}
    ]
    properties = ["dealname", "amount", "dealstage", "closedate", "hubspot_owner_id"]

    result = await client.search_objects(HubSpotObjectType.DEALS, filters, properties)
    if "error" in result:
        return result

    results = result.get("results", [])
    deals = []
    total_value = 0.0

    for r in results:
        props = r.get("properties", {})
        amt = float(props.get("amount") or 0.0)
        total_value += amt
        deals.append({
            "name": props.get("dealname", "Unnamed Deal"),
            "amount": amt,
            "close_date": props.get("closedate"),
            "owner_id": props.get("hubspot_owner_id")
        })

    await _enrich_with_owners(client, deals)

    for d in deals:
        d.pop("owner_id", None)

    return {
        "count": len(deals),
        "total_value": total_value,
        "deals": deals
    }
