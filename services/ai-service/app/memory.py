"""In-memory thread conversation store with TTL expiration and per-thread locking."""

import asyncio
import time
from typing import Dict, List, Any
from app.ai_enums import MemoryConfig

class ThreadMemory:
    """Thread-safe, TTL-based in-memory store for multi-turn conversation history.

    Each thread maintains its own asyncio.Lock to allow concurrent access
    across different threads while serializing access within a single thread.
    Messages are capped at max_messages using FIFO eviction.
    """


    def __init__(self, ttl_seconds: int = MemoryConfig.DEFAULT_TTL, max_messages: int = MemoryConfig.DEFAULT_MAX_MESSAGES):
        self.ttl_seconds = ttl_seconds
        self.max_messages = max_messages
        self._store: Dict[str, List[Dict[str, Any]]] = {}
        self._timestamps: Dict[str, float] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    async def _get_lock(self, thread_id: str) -> asyncio.Lock:
        """Retrieve or create a per-thread lock in a thread-safe manner."""
        async with self._global_lock:
            if thread_id not in self._locks:
                self._locks[thread_id] = asyncio.Lock()
            return self._locks[thread_id]

    async def get(self, thread_id: str) -> List[Dict[str, Any]]:
        """Retrieve a copy of all messages for the given thread."""
        self.cleanup()
        async with await self._get_lock(thread_id):
            return list(self._store.get(thread_id, []))

    async def append(self, thread_id: str, messages: List[Dict[str, Any]]):
        """Append new messages to a thread, enforcing the max_messages cap via FIFO eviction."""
        async with await self._get_lock(thread_id):
            if thread_id not in self._store:
                self._store[thread_id] = []

            self._store[thread_id].extend(messages)

            if len(self._store[thread_id]) > self.max_messages:
                self._store[thread_id] = self._store[thread_id][-self.max_messages:]

            self._timestamps[thread_id] = time.time()

    def cleanup(self):
        """Remove all threads whose last activity exceeds the TTL."""
        now = time.time()
        expired_threads = [
            tid for tid, timestamp in self._timestamps.items()
            if now - timestamp > self.ttl_seconds
        ]

        for tid in expired_threads:
            self._store.pop(tid, None)
            self._timestamps.pop(tid, None)
            self._locks.pop(tid, None)
