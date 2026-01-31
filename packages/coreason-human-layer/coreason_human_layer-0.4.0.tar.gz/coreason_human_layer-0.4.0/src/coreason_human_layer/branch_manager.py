# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_human_layer

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import anyio
import httpx
from coreason_identity.models import UserContext

from coreason_human_layer.gateways import SynthesisGateway
from coreason_human_layer.models import (
    Event,
    EventType,
    ExecutionBranch,
    ExecutionStatus,
    FeedbackSignal,
)
from coreason_human_layer.stasis import StasisEngine
from coreason_human_layer.utils.formatter import RuntimeFormatter
from coreason_human_layer.utils.logger import logger


class BranchManagerAsync:
    """Manages the lifecycle of ExecutionBranches and the tree topology (Async).

    Acts as the 'Forker', handling the creation of new branches, prefix caching pointers,
    and reconstructing lineage.
    """

    def __init__(
        self,
        stasis_engine: StasisEngine,
        synthesis_gateway: Optional[SynthesisGateway] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        """Initialize the Branch Manager Async.

        Args:
            stasis_engine: The storage engine for durable execution events.
            synthesis_gateway: Optional gateway for sending feedback signals.
            client: Optional httpx.AsyncClient. Used to construct the gateway if not provided,
                    or passed to the gateway if it needs one (conceptually).
        """
        self.stasis = stasis_engine
        self.synthesis_gateway = synthesis_gateway
        self._internal_client = client is None
        self._client = client or httpx.AsyncClient()

        # In-memory storage for branches: branch_id -> ExecutionBranch
        self._branches: Dict[UUID, ExecutionBranch] = {}

    async def __aenter__(self) -> "BranchManagerAsync":
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        if self._internal_client:
            await self._client.aclose()

        # If gateway is HttpSynthesisGateway and we own it/it has cleanup, we might need to close it.
        # But typically if we created it, we should close it.
        # Here we only managed the client.
        # If synthesis_gateway was injected, we assume caller manages it.
        # If we had logic to create synthesis_gateway internally using self._client, we would clean it up.
        # Currently, the prompt assumes ServiceAsync manages the client.

    def _get_last_agent_output(self, events: List[Event]) -> str:
        """Traverses backwards to find the last valid output event."""
        for event in reversed(events):
            if event.type in [EventType.TOOL_OUTPUT, EventType.MODEL_THINK]:
                return str(RuntimeFormatter.format_event_payload(event))
        return ""

    def _get_ancestry_chain(self, branch_id: UUID) -> List[ExecutionBranch]:
        """Traverses the ancestry chain upwards from the given branch_id to the root."""
        chain: List[ExecutionBranch] = []
        current_id: Optional[UUID] = branch_id

        while current_id:
            branch = self.get_branch(current_id)
            if not branch:
                break
            chain.append(branch)
            current_id = branch.parent_id

        return list(reversed(chain))

    def _filter_events_until(self, events: List[Event], until_event_id: Optional[UUID]) -> List[Event]:
        """Filters events to include only those up to (and including) until_event_id."""
        if until_event_id is None:
            return events

        filtered: List[Event] = []
        found = False
        for event in events:
            filtered.append(event)
            if event.id == until_event_id:
                found = True
                break

        return filtered if found else events

    async def get_full_context_events(
        self, branch_id: UUID, user_context: UserContext, cutoff_event_id: Optional[UUID] = None
    ) -> List[Event]:
        """Retrieves the full event history for a branch, traversing its ancestry."""
        branch = self.get_branch(branch_id)
        if not branch:
            return []

        chain = self._get_ancestry_chain(branch_id)
        all_events: List[Event] = []

        for i, current_branch in enumerate(chain):
            limit_id = None
            if i < len(chain) - 1:
                next_branch = chain[i + 1]
                limit_id = next_branch.parent_event_id
            else:
                limit_id = cutoff_event_id

            events = await self.stasis.get_events(current_branch.root_id, current_branch.id, context=user_context)

            if limit_id:
                events = self._filter_events_until(events, limit_id)

            all_events.extend(events)

        return all_events

    async def create_fork(
        self,
        parent_branch_id: Optional[UUID],
        parent_event_id: Optional[UUID],
        root_id: UUID,
        human_override_text: str,
        user_context: UserContext,
        kv_cache_pointer: str = "",
    ) -> UUID:
        """Creates a new execution branch (fork)."""
        new_branch_id = uuid4()
        timestamp = datetime.now(timezone.utc)

        if not kv_cache_pointer.strip() and parent_branch_id:
            kv_cache_pointer = str(parent_branch_id)

        branch = ExecutionBranch(
            id=new_branch_id,
            parent_id=parent_branch_id,
            parent_event_id=parent_event_id,
            root_id=root_id,
            owner_id=user_context.user_id,
            fork_trigger_event="Human Override",
            override_instruction=human_override_text,
            status=ExecutionStatus.RUNNING,
            created_at=timestamp,
            kv_cache_pointer=kv_cache_pointer,
        )
        self._branches[new_branch_id] = branch

        patch_pattern = r"^\s*(\w+)\s*=\s*(.+)\s*$"
        match = re.match(patch_pattern, human_override_text)

        if match:
            variable = match.group(1)
            value = match.group(2).strip()

            patch_event = Event(
                id=uuid4(),
                type=EventType.VARIABLE_PATCH,
                payload={"variable": variable, "value": value},
                timestamp=timestamp,
                parent_event_id=parent_event_id,
            )
            await self.stasis.append_event(root_id, new_branch_id, patch_event, context=user_context)
            parent_event_id = patch_event.id

        injection_payload = {
            "directive": human_override_text,
            "instruction": "You must disregard previous plans that conflict with this directive. Execute immediately.",
            "authority": "Verified Human Supervisor",
        }

        event = Event(
            id=uuid4(),
            type=EventType.SYSTEM_INJECT,
            payload=injection_payload,
            timestamp=timestamp,
            parent_event_id=parent_event_id,
        )

        await self.stasis.append_event(root_id, new_branch_id, event, context=user_context)

        return new_branch_id

    def get_branch(self, branch_id: UUID) -> Optional[ExecutionBranch]:
        """Retrieves a branch by ID. (In-memory, synchronous)"""
        return self._branches.get(branch_id)

    def get_branch_topology(self, root_id: UUID) -> List[Dict[str, Any]]:
        """Reconstructs the tree topology of branches for a given root_id. (In-memory, synchronous)"""
        root_branches = [b for b in self._branches.values() if b.root_id == root_id]

        if not root_branches:
            return []

        children_map: Dict[Optional[UUID], List[ExecutionBranch]] = {}
        for branch in root_branches:
            parent_id = branch.parent_id
            if parent_id not in children_map:
                children_map[parent_id] = []
            children_map[parent_id].append(branch)

        def build_node(branch: ExecutionBranch) -> Dict[str, Any]:
            node: Dict[str, Any] = {
                "id": str(branch.id),
                "data": branch.model_dump(),
                "children": [],
            }
            children = children_map.get(branch.id, [])
            for child in children:
                node["children"].append(build_node(child))
            return node

        roots = children_map.get(None, [])

        return [build_node(root) for root in roots]

    async def merge_branches(
        self, winning_branch_id: UUID, losing_branch_id: UUID, user_context: UserContext
    ) -> FeedbackSignal:
        """Merges two branches, marking one as MERGED and the other as ABANDONED."""
        if winning_branch_id == losing_branch_id:
            raise ValueError("Cannot merge a branch with itself.")

        winner = self.get_branch(winning_branch_id)
        loser = self.get_branch(losing_branch_id)

        if not winner or not loser:
            raise ValueError("One or both branches do not exist.")

        if winner.root_id != loser.root_id:
            raise ValueError("Branches must belong to the same root execution.")

        if winner.status == ExecutionStatus.ABANDONED or loser.status == ExecutionStatus.ABANDONED:
            raise ValueError("Cannot merge branches that are already ABANDONED.")

        winner.status = ExecutionStatus.MERGED
        loser.status = ExecutionStatus.ABANDONED

        parent_events_formatted: List[Dict[str, Any]] = []
        if winner.parent_id:
            raw_events = await self.get_full_context_events(
                winner.parent_id, user_context, cutoff_event_id=winner.parent_event_id
            )
            parent_events_formatted = list(RuntimeFormatter.events_to_chat_format(raw_events))

        winner_events = await self.stasis.get_events(winner.root_id, winner.id, context=user_context)
        chosen_text = self._get_last_agent_output(winner_events)

        loser_events = await self.stasis.get_events(loser.root_id, loser.id, context=user_context)
        rejected_text = self._get_last_agent_output(loser_events)

        signal = FeedbackSignal(
            timestamp=datetime.now(timezone.utc),
            author_id=user_context.user_id,
            author_role=user_context.groups,
            prompt_context=parent_events_formatted,
            chosen_response=chosen_text,
            rejected_response=rejected_text,
            metadata={
                "winning_branch_id": str(winning_branch_id),
                "losing_branch_id": str(losing_branch_id),
                "trigger": "merge_operation",
            },
        )

        if self.synthesis_gateway:
            try:
                await self.synthesis_gateway.send_feedback(signal, user_context)
            except Exception as e:
                logger.error("Unexpected error in SynthesisGateway", error=str(e))

        return signal


class BranchManager:
    """Sync Facade for BranchManagerAsync."""

    def __init__(
        self,
        stasis_engine: StasisEngine,
        synthesis_gateway: Optional[SynthesisGateway] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        """Initialize the Sync Facade."""
        self._async = BranchManagerAsync(stasis_engine, synthesis_gateway, client)

    def __enter__(self) -> "BranchManager":
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        # Pass explicit arguments to resolve mypy error about *args incompatibility
        anyio.run(self._async.__aexit__, exc_type, exc_val, exc_tb)

    def get_full_context_events(
        self, branch_id: UUID, user_context: UserContext, cutoff_event_id: Optional[UUID] = None
    ) -> List[Event]:
        return anyio.run(self._async.get_full_context_events, branch_id, user_context, cutoff_event_id)

    def create_fork(
        self,
        parent_branch_id: Optional[UUID],
        parent_event_id: Optional[UUID],
        root_id: UUID,
        human_override_text: str,
        user_context: UserContext,
        kv_cache_pointer: str = "",
    ) -> UUID:
        return anyio.run(
            self._async.create_fork,
            parent_branch_id,
            parent_event_id,
            root_id,
            human_override_text,
            user_context,
            kv_cache_pointer,
        )

    def get_branch(self, branch_id: UUID) -> Optional[ExecutionBranch]:
        # Synchronous method, call directly
        return self._async.get_branch(branch_id)

    def get_branch_topology(self, root_id: UUID) -> List[Dict[str, Any]]:
        # Synchronous method, call directly
        return self._async.get_branch_topology(root_id)

    def merge_branches(
        self, winning_branch_id: UUID, losing_branch_id: UUID, user_context: UserContext
    ) -> FeedbackSignal:
        return anyio.run(self._async.merge_branches, winning_branch_id, losing_branch_id, user_context)
