"""Background event handlers for processing Slack mentions."""

import httpx
import structlog
import re
import uuid
from typing import Dict, Any
from app.config import settings
from app.slack_enums import SlackAPIEndpoints, Timeouts, BotResponses

logger = structlog.get_logger(__name__)

async def post_to_slack(channel_id: str, thread_ts: str, text: str):
    """Post a message to a Slack channel or thread via the Web API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                SlackAPIEndpoints.POST_MESSAGE,
                headers={
                    "Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}",
                    "Content-Type": "application/json; charset=utf-8"
                },
                json={
                    "channel": channel_id,
                    "thread_ts": thread_ts,
                    "text": text
                },
                timeout=Timeouts.SLACK_API
            )
            response.raise_for_status()
            res_data = response.json()
            if not res_data.get("ok"):
                logger.error("slack_post_message_failed", error=res_data.get("error"))
    except Exception as e:
        logger.error("slack_api_error", error=str(e))

async def handle_mention_background_task(event: Dict[str, Any]):
    """Background task that forwards a user query to the AI service and posts the response.

    Strips the bot mention tag from the message text, sends the cleaned query
    to the AI service endpoint, and posts the resulting answer back into the
    originating Slack thread.
    """
    channel_id = event.get("channel")
    thread_ts = event.get("thread_ts") or event.get("ts")
    text = event.get("text", "")

    query = re.sub(r"<@[A-Z0-9]+>", "", text).strip()

    if not query:
        await post_to_slack(channel_id, thread_ts, BotResponses.NO_QUESTION)
        return

    logger.info("query_dispatched", query_length=len(query), thread_ts=thread_ts)

    try:
        async with httpx.AsyncClient() as client:
            request_id = str(uuid.uuid4())

            response = await client.post(
                f"{settings.AI_SERVICE_URL}/api/query",
                json={
                    "query": query,
                    "thread_id": thread_ts,
                    "request_id": request_id
                },
                timeout=httpx.Timeout(Timeouts.AI_SERVICE)
            )
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                answer = data.get("message", BotResponses.ERROR)
            else:
                answer = data.get("answer", BotResponses.NO_ANSWER)

            await post_to_slack(channel_id, thread_ts, answer)
            logger.info("slack_response_posted", thread_ts=thread_ts)

    except Exception as e:
        logger.error("ai_service_call_failed", error=str(e), thread_ts=thread_ts)
        await post_to_slack(channel_id, thread_ts, BotResponses.AI_SERVICE_UNAVAILABLE)
