import sys
from pathlib import Path

ai_service_path = Path(__file__).parent.parent / "services" / "ai-service"
sys.path.append(str(ai_service_path.resolve()))

import pytest
import respx
from app.clients.hubspot import HubSpotClient

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("HUBSPOT_ACCESS_TOKEN", "test-token")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

@pytest.fixture
def hubspot_client(mock_env):
    return HubSpotClient(token="test-token")

@pytest.fixture
def mock_hubspot():
    with respx.mock(assert_all_called=False) as respx_mock:
        yield respx_mock
