import pytest
import httpx
from app.tools.deals import count_deals_by_stage, search_deals, get_recent_deals_closed
from app.tools.contacts import get_contact_by_email

@pytest.mark.asyncio
async def test_count_deals_by_stage_happy_path(hubspot_client, mock_hubspot):
    mock_hubspot.post("https://api.hubapi.com/crm/v3/objects/deals/search").respond(
        json={
            "results": [
                {
                    "properties": {
                        "dealname": "Big Deal",
                        "amount": "10000",
                        "dealstage": "qualifiedtobuy",
                        "closedate": "2023-01-01",
                        "createdate": "2022-01-01",
                        "hubspot_owner_id": "123"
                    }
                }
            ]
        }
    )
    mock_hubspot.get("https://api.hubapi.com/crm/v3/owners/123").respond(
        json={"firstName": "Alice", "lastName": "Smith"}
    )
    
    result = await count_deals_by_stage(hubspot_client, "Qualified")
    
    assert "error" not in result
    assert result["count"] == 1
    assert result["total_value"] == 10000.0
    assert result["deals"][0]["name"] == "Big Deal"
    assert result["deals"][0]["owner"] == "Alice Smith"

@pytest.mark.asyncio
async def test_count_deals_by_stage_429(hubspot_client, mock_hubspot):
    mock_hubspot.post("https://api.hubapi.com/crm/v3/objects/deals/search").respond(status_code=429)
    result = await count_deals_by_stage(hubspot_client, "Qualified")
    assert result.get("error") == "rate_limit"

@pytest.mark.asyncio
async def test_count_deals_by_stage_500(hubspot_client, mock_hubspot):
    mock_hubspot.post("https://api.hubapi.com/crm/v3/objects/deals/search").respond(status_code=500)
    result = await count_deals_by_stage(hubspot_client, "Qualified")
    assert result.get("error") == "hubspot_error"

@pytest.mark.asyncio
async def test_count_deals_by_stage_timeout(hubspot_client, mock_hubspot):
    mock_hubspot.post("https://api.hubapi.com/crm/v3/objects/deals/search").mock(
        side_effect=httpx.TimeoutException("Timeout")
    )
    result = await count_deals_by_stage(hubspot_client, "Qualified")
    assert result.get("error") == "timeout"

@pytest.mark.asyncio
async def test_count_deals_by_stage_zero_results(hubspot_client, mock_hubspot):
    mock_hubspot.post("https://api.hubapi.com/crm/v3/objects/deals/search").respond(json={"results": []})
    result = await count_deals_by_stage(hubspot_client, "Qualified")
    assert "error" not in result
    assert result["count"] == 0
    assert result["total_value"] == 0.0

@pytest.mark.asyncio
async def test_search_deals_happy_path(hubspot_client, mock_hubspot):
    mock_hubspot.post("https://api.hubapi.com/crm/v3/objects/deals/search").respond(
        json={
            "results": [
                {
                    "properties": {
                        "dealname": "Acme Industrial",
                        "amount": "5000",
                        "dealstage": "open",
                        "hubspot_owner_id": "456"
                    }
                }
            ]
        }
    )
    mock_hubspot.get("https://api.hubapi.com/crm/v3/owners/456").respond(
        json={"firstName": "Bob", "lastName": "Jones"}
    )
    
    result = await search_deals(hubspot_client, query="Acme", min_amount=1000, stage="open")
    assert "error" not in result
    assert result["total_count"] == 1
    assert result["deals"][0]["name"] == "Acme Industrial"

@pytest.mark.asyncio
async def test_get_recent_deals_closed(hubspot_client, mock_hubspot):
    mock_hubspot.post("https://api.hubapi.com/crm/v3/objects/deals/search").respond(
        json={"results": []}
    )
    result = await get_recent_deals_closed(hubspot_client, days=30)
    assert "error" not in result
    assert result["count"] == 0

@pytest.mark.asyncio
async def test_get_contact_by_email_found(hubspot_client, mock_hubspot):
    mock_hubspot.post("https://api.hubapi.com/crm/v3/objects/contacts/search").respond(
        json={
            "results": [
                {
                    "properties": {
                        "firstname": "Alice",
                        "lastname": "W",
                        "email": "alice@example.com"
                    }
                }
            ]
        }
    )
    result = await get_contact_by_email(hubspot_client, "alice@example.com")
    assert "error" not in result
    assert result["found"] is True
    assert result["contact"]["first_name"] == "Alice"
    assert result["contact"]["email"] == "alice@example.com"

@pytest.mark.asyncio
async def test_get_contact_by_email_not_found(hubspot_client, mock_hubspot):
    mock_hubspot.post("https://api.hubapi.com/crm/v3/objects/contacts/search").respond(
        json={"results": []}
    )
    result = await get_contact_by_email(hubspot_client, "nobody@example.com")
    assert "error" not in result
    assert result["found"] is False
    assert result["contact"] is None

@pytest.mark.asyncio
async def test_tool_error_dict(hubspot_client, mock_hubspot):
    mock_hubspot.post("https://api.hubapi.com/crm/v3/objects/contacts/search").respond(status_code=500)
    result = await get_contact_by_email(hubspot_client, "alice@example.com")
    assert result.get("error") == "hubspot_error"
