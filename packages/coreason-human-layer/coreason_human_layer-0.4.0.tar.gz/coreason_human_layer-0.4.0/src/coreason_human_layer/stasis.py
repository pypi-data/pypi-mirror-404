# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_human_layer

from __future__ import annotations

from typing import Any, List, Protocol
from uuid import UUID

from coreason_identity.models import UserContext
from redis.asyncio import Redis

from coreason_human_layer.models import Event
from coreason_human_layer.utils.logger import logger


class StasisEngine(Protocol):
    """Protocol for the Stasis Engine (Durable Execution).

    Manages the append-only log of events for agent execution.
    Implements the event sourcing pattern.
    """

    async def append_event(self, root_id: UUID, branch_id: UUID, event: Event, *, context: UserContext) -> None:
        """Appends an event to the log for a given root execution ID and branch ID.

        Args:
            root_id: The global identifier for the conversation.
            branch_id: The identifier for the specific execution branch.
            event: The event object to append.
            context: The user context for the operation (mandatory).
        """
        ...

    async def get_events(self, root_id: UUID, branch_id: UUID, *, context: UserContext) -> List[Event]:
        """Retrieves all events for a given root execution ID and branch ID.

        Args:
            root_id: The global identifier for the conversation.
            branch_id: The identifier for the specific execution branch.
            context: The user context for the operation (mandatory).

        Returns:
            A list of Event objects associated with the branch.
        """
        ...


class InMemoryStasisEngine:
    """In-memory implementation of StasisEngine for testing and local development.

    Stores events in a dictionary keyed by (root_id, branch_id).
    Useful for unit tests where Redis is not available.
    """

    def __init__(self) -> None:
        """Initializes the in-memory store."""
        self._store: dict[tuple[UUID, UUID], List[Event]] = {}

    async def append_event(self, root_id: UUID, branch_id: UUID, event: Event, *, context: UserContext) -> None:
        """Appends an event to the in-memory store.

        Args:
            root_id: The global identifier for the conversation.
            branch_id: The identifier for the specific execution branch.
            event: The event object to append.
            context: The user context for the operation (mandatory).
        """
        if context is None:
            raise ValueError("UserContext is mandatory for append_event")

        logger.debug("Appending event to stasis", user_id=context.user_id, root_id=str(root_id))

        key = (root_id, branch_id)
        if key not in self._store:
            self._store[key] = []
        self._store[key].append(event)

    async def get_events(self, root_id: UUID, branch_id: UUID, *, context: UserContext) -> List[Event]:
        """Retrieves events from the in-memory store.

        Args:
            root_id: The global identifier for the conversation.
            branch_id: The identifier for the specific execution branch.
            context: The user context for the operation (mandatory).

        Returns:
            A list of Event objects.
        """
        if context is None:
            raise ValueError("UserContext is mandatory for get_events")

        logger.debug("Retrieving event stream", user_id=context.user_id, root_id=str(root_id))

        return self._store.get((root_id, branch_id), [])


class RedisStasisEngine:
    """Redis-backed implementation of StasisEngine using Redis Streams.

    Implements durable execution by persisting events to a Redis Stream.
    Keys are formatted as: agent:{root_id}:branch:{branch_id}:events
    """

    def __init__(self, redis_client: Redis[Any]) -> None:
        """Initialize the Redis Stasis Engine.

        Args:
            redis_client: An initialized Redis client instance.
        """
        self.redis = redis_client

    def _get_key(self, root_id: UUID, branch_id: UUID) -> str:
        """Helper to construct the Redis key for a branch's event stream.

        Args:
            root_id: The global identifier for the conversation.
            branch_id: The identifier for the specific execution branch.

        Returns:
            The Redis key string.
        """
        return f"agent:{root_id}:branch:{branch_id}:events"

    async def append_event(self, root_id: UUID, branch_id: UUID, event: Event, *, context: UserContext) -> None:
        """Appends an event to the Redis Stream.

        Args:
            root_id: The global identifier for the conversation.
            branch_id: The identifier for the specific execution branch.
            event: The event object to append.
            context: The user context for the operation (mandatory).
        """
        if context is None:
            raise ValueError("UserContext is mandatory for append_event")

        logger.debug("Appending event to stasis", user_id=context.user_id, root_id=str(root_id))

        key = self._get_key(root_id, branch_id)
        # Store the JSON payload in a field named 'data'
        await self.redis.xadd(key, {"data": event.model_dump_json()})

    async def get_events(self, root_id: UUID, branch_id: UUID, *, context: UserContext) -> List[Event]:
        """Retrieves events from the Redis Stream.

        Args:
            root_id: The global identifier for the conversation.
            branch_id: The identifier for the specific execution branch.
            context: The user context for the operation (mandatory).

        Returns:
            A list of Event objects reconstructed from the stream.
        """
        if context is None:
            raise ValueError("UserContext is mandatory for get_events")

        logger.debug("Retrieving event stream", user_id=context.user_id, root_id=str(root_id))

        key = self._get_key(root_id, branch_id)
        # xrange returns a list of (stream_id, fields_dict)
        stream_entries: Any = await self.redis.xrange(key)

        events: List[Event] = []

        if not stream_entries:
            return events

        # Iterate over the raw list
        for _, fields in stream_entries:
            # fields is a dictionary (bytes key -> bytes value)
            # We stored our data in the 'data' field.
            # Redis-py decodes keys/values if decode_responses=True is set on client,
            # otherwise they are bytes.

            raw_data = fields.get("data") or fields.get(b"data")
            if raw_data:
                # If it's bytes, decode it.
                if isinstance(raw_data, bytes):
                    raw_data = raw_data.decode("utf-8")
                events.append(Event.model_validate_json(raw_data))

        return events
