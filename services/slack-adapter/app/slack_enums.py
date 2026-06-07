"""Enums and Constants for the Slack Adapter service."""

from enum import Enum, StrEnum

class SlackEventType(StrEnum):
    """Event types received from Slack."""
    URL_VERIFICATION = "url_verification"
    APP_MENTION = "app_mention"
    MESSAGE = "message"

class SlackChannelType(StrEnum):
    """Types of channels in Slack."""
    IM = "im"

class SlackMessageSubtype(StrEnum):
    """Subtypes for Slack messages."""
    BOT_MESSAGE = "bot_message"

class SlackAPIEndpoints(StrEnum):
    """Slack Web API endpoints."""
    POST_MESSAGE = "https://slack.com/api/chat.postMessage"

class Timeouts(float, Enum):
    """Timeout configurations in seconds."""
    SLACK_API = 10.0
    AI_SERVICE = 60.0

class SignatureConfig(int, Enum):
    """Slack signature validation configurations."""
    MAX_AGE_SECONDS = 300

class BotResponses(StrEnum):
    """Standard text responses for the bot."""
    NO_QUESTION = "I didn't catch a question. How can I help you?"
    ERROR = "An error occurred."
    NO_ANSWER = "I couldn't generate an answer."
    AI_SERVICE_UNAVAILABLE = "I'm having trouble connecting to my AI brain right now. Please try again in a moment."
