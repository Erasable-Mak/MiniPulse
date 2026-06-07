"""Enums and Constants for the AI Service."""

from enum import Enum, StrEnum

class HubSpotObjectType(StrEnum):
    """Types of objects in HubSpot."""
    DEALS = "deals"
    CONTACTS = "contacts"

class HubSpotOperator(StrEnum):
    """Operators for HubSpot search filters."""
    EQ = "EQ"
    CONTAINS_TOKEN = "CONTAINS_TOKEN"
    GTE = "GTE"

class DealStage(StrEnum):
    """HubSpot deal stages internal identifiers."""
    QUALIFIED = "qualifiedtobuy"
    APPOINTMENT_SCHEDULED = "appointmentscheduled"
    PRESENTATION_SCHEDULED = "presentationscheduled"
    DECISION_MAKER_BOUGHT_IN = "decisionmakerboughtin"
    CONTRACT_SENT = "contractsent"
    CLOSED_WON = "closedwon"
    CLOSED_LOST = "closedlost"

class LLMRole(StrEnum):
    """Roles for messages in the LLM context."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    FUNCTION = "function"

class LLMModel(StrEnum):
    """LLM model names."""
    DEFAULT = "llama-3.1-8b-instant"

class Timeouts(float, Enum):
    """Timeout configurations in seconds."""
    HUBSPOT_API = 10.0

class MemoryConfig(int, Enum):
    """Configuration for thread memory."""
    DEFAULT_TTL = 1800
    DEFAULT_MAX_MESSAGES = 20
