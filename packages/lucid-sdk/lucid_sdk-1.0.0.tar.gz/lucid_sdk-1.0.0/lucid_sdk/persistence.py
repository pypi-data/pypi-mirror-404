"""
Persistence Abstraction for Lucid Auditors

Provides pluggable persistence backends for auditors that need to store state.
This addresses the architecture issue where in-memory stores are lost on restart.

Supported Backends:
- InMemoryBackend: Default, fast but non-persistent (suitable for development/testing)
- Future: Redis, PostgreSQL, SQLite, etc.

Usage:
    from lucid_sdk import PersistenceBackend, InMemoryBackend, create_persistence_backend

    # Using the default in-memory backend
    store = InMemoryBackend[EvaluationResult]()
    await store.set("eval-123", result)
    result = await store.get("eval-123")

    # Using the factory with environment configuration
    store = create_persistence_backend[EvaluationResult]()

    # For synchronous code
    store = InMemoryBackend[str]()
    store.set_sync("key", "value")
    value = store.get_sync("key")
"""

import os
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import (
    Any,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    TypeVar,
    Callable,
    Union,
)
from dataclasses import dataclass, field
from collections import OrderedDict
import threading


# Type variable for stored values
T = TypeVar("T")


@dataclass
class StoredItem(Generic[T]):
    """Wrapper for stored items with metadata."""
    value: T
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if the item has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at


class PersistenceBackend(ABC, Generic[T]):
    """Abstract base class for persistence backends.

    All auditors that need persistence should use this interface to enable
    pluggable storage backends. The default implementation (InMemoryBackend)
    is fast but loses data on restart.

    For production deployments, consider using Redis or database-backed
    implementations for durability across restarts.

    Type Parameter:
        T: The type of values stored in this backend.

    Example:
        class MyAuditor:
            def __init__(self):
                self.store: PersistenceBackend[EvalResult] = InMemoryBackend()

            async def save_result(self, eval_id: str, result: EvalResult):
                await self.store.set(eval_id, result, ttl_seconds=3600)

            async def get_result(self, eval_id: str) -> Optional[EvalResult]:
                return await self.store.get(eval_id)
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[T]:
        """Retrieve a value by key.

        Args:
            key: The unique identifier for the stored value.

        Returns:
            The stored value if found and not expired, None otherwise.
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: T,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Store a value with optional TTL and metadata.

        Args:
            key: The unique identifier for the value.
            value: The value to store.
            ttl_seconds: Optional time-to-live in seconds.
            metadata: Optional metadata to store with the value.

        Returns:
            True if the value was stored successfully, False otherwise.
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value by key.

        Args:
            key: The unique identifier of the value to delete.

        Returns:
            True if a value was deleted, False if key didn't exist.
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired.

        Args:
            key: The unique identifier to check.

        Returns:
            True if the key exists and is not expired, False otherwise.
        """
        pass

    @abstractmethod
    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """List all keys, optionally filtered by pattern.

        Args:
            pattern: Optional glob-style pattern to filter keys.
                     Supports * (match any) and ? (match single character).

        Returns:
            List of matching keys.
        """
        pass

    @abstractmethod
    async def clear(self) -> int:
        """Clear all stored values.

        Returns:
            Number of items cleared.
        """
        pass

    @abstractmethod
    async def size(self) -> int:
        """Get the number of stored items.

        Returns:
            Number of items in the store (excluding expired items).
        """
        pass

    # Optional: Synchronous interface for simple use cases
    def get_sync(self, key: str) -> Optional[T]:
        """Synchronous version of get()."""
        return _run_sync(self.get(key))

    def set_sync(
        self,
        key: str,
        value: T,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Synchronous version of set()."""
        return _run_sync(self.set(key, value, ttl_seconds, metadata))

    def delete_sync(self, key: str) -> bool:
        """Synchronous version of delete()."""
        return _run_sync(self.delete(key))

    def exists_sync(self, key: str) -> bool:
        """Synchronous version of exists()."""
        return _run_sync(self.exists(key))

    def keys_sync(self, pattern: Optional[str] = None) -> List[str]:
        """Synchronous version of keys()."""
        return _run_sync(self.keys(pattern))

    def clear_sync(self) -> int:
        """Synchronous version of clear()."""
        return _run_sync(self.clear())

    def size_sync(self) -> int:
        """Synchronous version of size()."""
        return _run_sync(self.size())


def _run_sync(coro):
    """Run an async coroutine synchronously."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We're in an async context, use thread pool
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)


def _match_pattern(key: str, pattern: str) -> bool:
    """Match a key against a glob-style pattern.

    Supports:
        * - matches any sequence of characters
        ? - matches any single character
    """
    import fnmatch
    return fnmatch.fnmatch(key, pattern)


class InMemoryBackend(PersistenceBackend[T]):
    """In-memory persistence backend.

    This is the default backend for development and testing. It provides
    fast access but data is lost when the process restarts.

    Features:
        - Thread-safe operations
        - Optional TTL support
        - LRU eviction when max_size is reached
        - Automatic cleanup of expired items

    Configuration:
        max_size: Maximum number of items to store (0 = unlimited).
                  When reached, oldest items are evicted (LRU).
        cleanup_interval: Seconds between automatic expired item cleanup.

    Example:
        store = InMemoryBackend[dict](max_size=1000)
        await store.set("key1", {"data": "value"}, ttl_seconds=3600)
    """

    def __init__(
        self,
        max_size: int = 0,
        cleanup_interval: int = 60,
    ):
        """Initialize the in-memory backend.

        Args:
            max_size: Maximum items to store (0 = unlimited).
            cleanup_interval: Seconds between expired item cleanup.
        """
        self._store: OrderedDict[str, StoredItem[T]] = OrderedDict()
        self._lock = threading.RLock()
        self._max_size = max_size
        self._cleanup_interval = cleanup_interval
        self._last_cleanup = datetime.now(timezone.utc)

    def _maybe_cleanup(self) -> None:
        """Perform cleanup if cleanup interval has passed."""
        now = datetime.now(timezone.utc)
        if (now - self._last_cleanup).total_seconds() >= self._cleanup_interval:
            self._cleanup_expired()
            self._last_cleanup = now

    def _cleanup_expired(self) -> int:
        """Remove all expired items."""
        with self._lock:
            expired_keys = [
                key for key, item in self._store.items()
                if item.is_expired()
            ]
            for key in expired_keys:
                del self._store[key]
            return len(expired_keys)

    def _evict_if_needed(self) -> None:
        """Evict oldest items if max_size is exceeded."""
        if self._max_size <= 0:
            return

        with self._lock:
            while len(self._store) >= self._max_size:
                # Pop the first (oldest) item
                self._store.popitem(last=False)

    async def get(self, key: str) -> Optional[T]:
        """Retrieve a value by key."""
        self._maybe_cleanup()

        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None

            if item.is_expired():
                del self._store[key]
                return None

            # Move to end for LRU
            self._store.move_to_end(key)
            return item.value

    async def set(
        self,
        key: str,
        value: T,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Store a value with optional TTL."""
        self._maybe_cleanup()

        expires_at = None
        if ttl_seconds is not None and ttl_seconds > 0:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

        now = datetime.now(timezone.utc)

        with self._lock:
            # Check if updating existing key
            existing = self._store.get(key)
            if existing:
                existing.value = value
                existing.updated_at = now
                existing.expires_at = expires_at
                if metadata:
                    existing.metadata.update(metadata)
                self._store.move_to_end(key)
            else:
                self._evict_if_needed()
                self._store[key] = StoredItem(
                    value=value,
                    created_at=now,
                    updated_at=now,
                    expires_at=expires_at,
                    metadata=metadata or {},
                )

        return True

    async def delete(self, key: str) -> bool:
        """Delete a value by key."""
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return False

            if item.is_expired():
                del self._store[key]
                return False

            return True

    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """List all keys, optionally filtered by pattern."""
        self._maybe_cleanup()

        with self._lock:
            # Filter out expired items
            valid_keys = [
                key for key, item in self._store.items()
                if not item.is_expired()
            ]

            if pattern is None:
                return valid_keys

            return [key for key in valid_keys if _match_pattern(key, pattern)]

    async def clear(self) -> int:
        """Clear all stored values."""
        with self._lock:
            count = len(self._store)
            self._store.clear()
            return count

    async def size(self) -> int:
        """Get the number of stored items (excluding expired)."""
        self._maybe_cleanup()

        with self._lock:
            return sum(
                1 for item in self._store.values()
                if not item.is_expired()
            )

    # Additional methods specific to in-memory backend

    async def get_with_metadata(self, key: str) -> Optional[StoredItem[T]]:
        """Get the full StoredItem including metadata."""
        with self._lock:
            item = self._store.get(key)
            if item is None or item.is_expired():
                return None
            return item

    async def items(self) -> List[tuple[str, T]]:
        """Get all key-value pairs (excluding expired)."""
        self._maybe_cleanup()

        with self._lock:
            return [
                (key, item.value)
                for key, item in self._store.items()
                if not item.is_expired()
            ]

    async def values(self) -> List[T]:
        """Get all values (excluding expired)."""
        self._maybe_cleanup()

        with self._lock:
            return [
                item.value
                for item in self._store.values()
                if not item.is_expired()
            ]

    def items_sync(self) -> List[tuple[str, T]]:
        """Synchronous version of items()."""
        return _run_sync(self.items())

    def values_sync(self) -> List[T]:
        """Synchronous version of values()."""
        return _run_sync(self.values())


class NamespacedBackend(PersistenceBackend[T]):
    """A persistence backend wrapper that adds a namespace prefix to all keys.

    This is useful when multiple auditors share the same backend but need
    isolated key spaces.

    Example:
        base_store = InMemoryBackend()
        eval_store = NamespacedBackend(base_store, "evaluations")
        trace_store = NamespacedBackend(base_store, "traces")

        # Keys are automatically prefixed
        await eval_store.set("eval-1", result)  # Stored as "evaluations:eval-1"
        await trace_store.set("trace-1", data)  # Stored as "traces:trace-1"
    """

    def __init__(
        self,
        backend: PersistenceBackend[T],
        namespace: str,
        separator: str = ":",
    ):
        """Initialize the namespaced backend.

        Args:
            backend: The underlying persistence backend.
            namespace: The namespace prefix for all keys.
            separator: Separator between namespace and key (default: ":").
        """
        self._backend = backend
        self._namespace = namespace
        self._separator = separator

    def _prefix_key(self, key: str) -> str:
        """Add namespace prefix to a key."""
        return f"{self._namespace}{self._separator}{key}"

    def _strip_prefix(self, key: str) -> str:
        """Remove namespace prefix from a key."""
        prefix = f"{self._namespace}{self._separator}"
        if key.startswith(prefix):
            return key[len(prefix):]
        return key

    async def get(self, key: str) -> Optional[T]:
        return await self._backend.get(self._prefix_key(key))

    async def set(
        self,
        key: str,
        value: T,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        return await self._backend.set(
            self._prefix_key(key), value, ttl_seconds, metadata
        )

    async def delete(self, key: str) -> bool:
        return await self._backend.delete(self._prefix_key(key))

    async def exists(self, key: str) -> bool:
        return await self._backend.exists(self._prefix_key(key))

    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        # Prefix the pattern if provided
        if pattern:
            prefixed_pattern = self._prefix_key(pattern)
        else:
            prefixed_pattern = f"{self._namespace}{self._separator}*"

        all_keys = await self._backend.keys(prefixed_pattern)
        return [self._strip_prefix(k) for k in all_keys]

    async def clear(self) -> int:
        # Only clear keys in this namespace
        keys = await self.keys()
        count = 0
        for key in keys:
            if await self.delete(key):
                count += 1
        return count

    async def size(self) -> int:
        keys = await self.keys()
        return len(keys)


# Factory function for creating persistence backends from configuration

def create_persistence_backend(
    backend_type: Optional[str] = None,
    **kwargs: Any,
) -> PersistenceBackend:
    """Factory function to create a persistence backend based on configuration.

    The backend type can be specified directly or via the PERSISTENCE_BACKEND
    environment variable.

    Supported backends:
        - "memory" (default): InMemoryBackend
        - Future: "redis", "postgresql", "sqlite"

    Args:
        backend_type: The type of backend to create. If None, uses
                      PERSISTENCE_BACKEND env var or defaults to "memory".
        **kwargs: Additional arguments passed to the backend constructor.

    Returns:
        A configured PersistenceBackend instance.

    Example:
        # Using environment variable
        os.environ["PERSISTENCE_BACKEND"] = "memory"
        store = create_persistence_backend(max_size=1000)

        # Explicit type
        store = create_persistence_backend("memory", max_size=1000)
    """
    if backend_type is None:
        backend_type = os.getenv("PERSISTENCE_BACKEND", "memory").lower()

    if backend_type == "memory":
        max_size = kwargs.get("max_size", int(os.getenv("PERSISTENCE_MAX_SIZE", "0")))
        cleanup_interval = kwargs.get(
            "cleanup_interval",
            int(os.getenv("PERSISTENCE_CLEANUP_INTERVAL", "60"))
        )
        return InMemoryBackend(max_size=max_size, cleanup_interval=cleanup_interval)

    raise ValueError(f"Unknown persistence backend type: {backend_type}")
