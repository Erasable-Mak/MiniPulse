"""Slack request signature verification middleware."""

import hmac
import hashlib
import time
import structlog
from fastapi import Request, HTTPException, Header, status
from app.config import settings
from app.slack_enums import SignatureConfig

logger = structlog.get_logger(__name__)

def verify_slack_signature(signing_secret: str, timestamp: str, body: bytes, signature: str) -> bool:
    """Verify the HMAC-SHA256 signature from a Slack request.

    Uses hmac.compare_digest to prevent timing attacks and rejects
    requests with timestamps older than 5 minutes to prevent replay attacks.
    """
    if not signing_secret or not timestamp or not signature:
        return False

    try:
        ts = int(timestamp)
    except ValueError:
        return False

    if abs(time.time() - ts) > SignatureConfig.MAX_AGE_SECONDS:
        return False

    sig_basestring = b"v0:" + timestamp.encode('utf-8') + b":" + body

    my_signature = "v0=" + hmac.new(
        signing_secret.encode('utf-8'),
        sig_basestring,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(my_signature, signature)

async def verify_slack_request(
    request: Request,
    x_slack_request_timestamp: str = Header(default=None),
    x_slack_signature: str = Header(default=None)
):
    """FastAPI dependency that validates incoming Slack webhook requests.

    Reads the raw request body and verifies the HMAC signature
    against the configured signing secret. Raises HTTP 401 on failure.
    """
    if not x_slack_request_timestamp or not x_slack_signature:
        logger.warning("missing_slack_headers")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Slack signature headers")

    body = await request.body()

    is_valid = verify_slack_signature(
        signing_secret=settings.SLACK_SIGNING_SECRET,
        timestamp=x_slack_request_timestamp,
        body=body,
        signature=x_slack_signature
    )

    if not is_valid:
        logger.warning("invalid_slack_signature", timestamp=x_slack_request_timestamp)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Slack signature")
