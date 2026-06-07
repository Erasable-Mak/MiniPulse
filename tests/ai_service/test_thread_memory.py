import asyncio
import time
import pytest
from app.memory import ThreadMemory

@pytest.mark.asyncio
async def test_store_and_retrieve():
    memory = ThreadMemory()
    await memory.append("thread_1", [{"role": "user", "content": "hello"}])
    
    msgs = await memory.get("thread_1")
    assert len(msgs) == 1
    assert msgs[0]["content"] == "hello"

@pytest.mark.asyncio
async def test_separate_threads():
    memory = ThreadMemory()
    await memory.append("thread_1", [{"role": "user", "content": "1"}])
    await memory.append("thread_2", [{"role": "user", "content": "2"}])
    
    msgs1 = await memory.get("thread_1")
    msgs2 = await memory.get("thread_2")
    
    assert len(msgs1) == 1
    assert msgs1[0]["content"] == "1"
    
    assert len(msgs2) == 1
    assert msgs2[0]["content"] == "2"

@pytest.mark.asyncio
async def test_ttl_expiration(monkeypatch):
    memory = ThreadMemory(ttl_seconds=60)
    
    current_time = 1000.0
    monkeypatch.setattr(time, "time", lambda: current_time)
    
    await memory.append("thread_1", [{"role": "user", "content": "hello"}])
    
    msgs = await memory.get("thread_1")
    assert len(msgs) == 1
    
    current_time = 1061.0
    monkeypatch.setattr(time, "time", lambda: current_time)
    
    msgs = await memory.get("thread_1")
    assert len(msgs) == 0

@pytest.mark.asyncio
async def test_max_cap_eviction():
    memory = ThreadMemory(max_messages=5)
    
    for i in range(6):
        await memory.append("thread_1", [{"role": "user", "content": str(i)}])
        
    msgs = await memory.get("thread_1")
    assert len(msgs) == 5
    assert msgs[0]["content"] == "1"
    assert msgs[-1]["content"] == "5"

@pytest.mark.asyncio
async def test_empty_thread():
    memory = ThreadMemory()
    msgs = await memory.get("nonexistent_thread")
    assert isinstance(msgs, list)
    assert len(msgs) == 0
