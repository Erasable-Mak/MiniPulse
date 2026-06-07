import pytest
import time
import hmac
import hashlib
from app.middleware.signature import verify_slack_signature, verify_slack_request
import app.middleware.signature
from fastapi import HTTPException
import app.config

def test_valid_signature(monkeypatch):
    secret = "my_secret"
    body = b"hello world"
    timestamp = "1234567890"
    
    monkeypatch.setattr(time, "time", lambda: 1234567890.0)
    
    sig_basestring = b"v0:" + timestamp.encode('utf-8') + b":" + body
    valid_sig = "v0=" + hmac.new(secret.encode('utf-8'), sig_basestring, hashlib.sha256).hexdigest()
    
    assert verify_slack_signature(secret, timestamp, body, valid_sig) is True

def test_invalid_signature(monkeypatch):
    secret = "my_secret"
    body = b"hello world"
    timestamp = "1234567890"
    
    monkeypatch.setattr(time, "time", lambda: 1234567890.0)
    
    assert verify_slack_signature(secret, timestamp, body, "v0=invalid_sig") is False

def test_expired_timestamp(monkeypatch):
    secret = "my_secret"
    body = b"hello world"
    timestamp = "1234567890"
    
    monkeypatch.setattr(time, "time", lambda: 1234567890.0 + 361)
    
    sig_basestring = b"v0:" + timestamp.encode('utf-8') + b":" + body
    valid_sig = "v0=" + hmac.new(secret.encode('utf-8'), sig_basestring, hashlib.sha256).hexdigest()
    
    assert verify_slack_signature(secret, timestamp, body, valid_sig) is False

def test_missing_params():
    assert verify_slack_signature("", "1234567890", b"body", "sig") is False
    assert verify_slack_signature("secret", "", b"body", "sig") is False
    assert verify_slack_signature("secret", "1234567890", b"body", "") is False

def test_invalid_timestamp_format():
    assert verify_slack_signature("secret", "not_a_number", b"body", "sig") is False

@pytest.mark.asyncio
async def test_fastapi_dependency_missing_headers():

    
    class MockRequest:
        async def body(self):
            return b""
            
    with pytest.raises(HTTPException) as exc:
        await verify_slack_request(MockRequest(), None, None)
    assert exc.value.status_code == 401

@pytest.mark.asyncio
async def test_fastapi_dependency_invalid_signature(monkeypatch):

    class MockSettings:
        SLACK_SIGNING_SECRET = "secret"
    monkeypatch.setattr(app.middleware.signature, "settings", MockSettings())
    
    class MockRequest:
        async def body(self):
            return b"body"
            
    with pytest.raises(HTTPException) as exc:
        await verify_slack_request(MockRequest(), "1234567890", "v0=invalid")
    assert exc.value.status_code == 401
