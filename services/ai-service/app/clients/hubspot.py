"""Async HubSpot CRM API client with structured error handling."""

import httpx
import structlog
from typing import Dict, Any, Optional, List, Union
from ..config import settings
from ..ai_enums import Timeouts

logger = structlog.get_logger(__name__)

class HubSpotClient:
    """Async HTTP client for the HubSpot CRM v3 API.
    Handles authentication, error classification (rate limits, auth failures,
    server errors, timeouts), and provides an in-memory cache for owner lookups.
    Never raises exceptions; returns structured error dicts instead.
    """

    def __init__(self, token: str = settings.HUBSPOT_ACCESS_TOKEN):
        self.token = token
        self.base_url = "https://api.hubapi.com"
        self._owner_cache: Dict[str, Dict[str, Any]] = {}

    async def _make_request(
        self, method: str, endpoint: str, json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute an authenticated HTTP request against the HubSpot API.
        Returns the parsed JSON response on success, or a structured error
        dict on failure (rate limit, auth error, timeout, server error).
        """
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}{endpoint}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data,
                    timeout=Timeouts.HUBSPOT_API
                )

            if response.status_code == httpx.codes.TOO_MANY_REQUESTS:
                return {
                    "error": "rate_limit",
                    "message": "HubSpot rate limit exceeded.",
                    "status_code": httpx.codes.TOO_MANY_REQUESTS
                }
            elif response.status_code >= httpx.codes.INTERNAL_SERVER_ERROR:
                return {
                    "error": "hubspot_error",
                    "message": "HubSpot internal server error.",
                    "status_code": response.status_code
                }
            elif response.status_code == httpx.codes.UNAUTHORIZED:
                return {
                    "error": "auth_error",
                    "message": "HubSpot authentication failed.",
                    "status_code": httpx.codes.UNAUTHORIZED
                }

            response.raise_for_status()
            return response.json()

        except httpx.TimeoutException:
            return {
                "error": "timeout",
                "message": "Request to HubSpot timed out."
            }
        except httpx.HTTPStatusError as e:
            return {
                "error": "http_error",
                "message": f"HTTP error {e.response.status_code}",
                "status_code": e.response.status_code
            }
        except Exception as e:
            return {
                "error": "parse_error",
                "message": "Failed to parse response or unknown error occurred."
            }

    async def search_objects(
        self, object_type: str, filters: List[Dict[str, Any]], properties: List[str]
    ) -> Dict[str, Any]:
        """Search HubSpot CRM objects using filters and return requested properties."""
        endpoint = f"/crm/v3/objects/{object_type}/search"
        payload = {
            "filterGroups": [{"filters": filters}] if filters else [],
            "properties": properties,
        }
        return await self._make_request("POST", endpoint, json_data=payload)

    async def get_owner(self, owner_id: Union[str, int]) -> Dict[str, Any]:
        """Fetch owner details by ID with in-memory caching."""
        owner_id_str = str(owner_id)
        if owner_id_str in self._owner_cache:
            return self._owner_cache[owner_id_str]

        endpoint = f"/crm/v3/owners/{owner_id_str}"
        result = await self._make_request("GET", endpoint)

        if "error" in result:
            return result

        owner_data = {
            "first_name": result.get("firstName", ""),
            "last_name": result.get("lastName", "")
        }
        self._owner_cache[owner_id_str] = owner_data
        return owner_data
