from fastapi import FastAPI, Request, Header, Depends
from fastapi.responses import JSONResponse
import structlog
import asyncio

from app.config import settings
from app.logging import setup_logging
from app.middleware.signature import verify_slack_request
from app.handlers.events import handle_mention_background_task
from app.slack_enums import SlackEventType, SlackChannelType, SlackMessageSubtype

setup_logging(settings.LOG_LEVEL)
logger = structlog.get_logger(__name__)

app = FastAPI(title="MiniPulse Slack Adapter", version="0.1.0")

@app.post("/slack/events", dependencies=[Depends(verify_slack_request)])
async def slack_events(
    request: Request,
    x_slack_retry_num: str = Header(default=None)
):
    """Handle incoming Slack event callbacks.
    Processes url_verification challenges, deduplicates retries,
    filters bot messages, and dispatches valid user mentions
    as background tasks.
    """
    body = await request.json()

    if body.get("type") == SlackEventType.URL_VERIFICATION:
        return JSONResponse(content={"challenge": body.get("challenge")})

    if x_slack_retry_num is not None:
        logger.info("retry_skipped", retry_num=x_slack_retry_num)
        return JSONResponse(content={"ok": True})

    event = body.get("event", {})
    event_type = event.get("type")

    if event.get("bot_id") or event.get("subtype") == SlackMessageSubtype.BOT_MESSAGE:
        return JSONResponse(content={"ok": True})

    if event_type == SlackEventType.APP_MENTION or (event_type == SlackEventType.MESSAGE and event.get("channel_type") == SlackChannelType.IM):
        logger.info("slack_event_received", event_type=event_type)
        asyncio.create_task(handle_mention_background_task(event))

    return JSONResponse(content={"ok": True})

@app.get("/healthz")
async def healthz() -> dict:
    """Liveness probe for container orchestration."""
    return {"status": "healthy", "service": "slack-adapter"}
