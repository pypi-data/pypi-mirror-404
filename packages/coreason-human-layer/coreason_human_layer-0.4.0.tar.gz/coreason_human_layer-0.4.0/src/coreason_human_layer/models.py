# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_human_layer

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Enumeration of supported event types in the Stasis Engine.

    Attributes:
        USER_MSG: A message from the user.
        MODEL_THINK: Internal thought process of the model.
        TOOL_OUTPUT: Output from a tool execution.
        SYSTEM_INJECT: High-priority system instruction injected by the supervisor.
        VARIABLE_PATCH: Data update event for hard-setting variables.
    """

    USER_MSG = "USER_MSG"
    MODEL_THINK = "MODEL_THINK"
    TOOL_OUTPUT = "TOOL_OUTPUT"
    SYSTEM_INJECT = "SYSTEM_INJECT"
    VARIABLE_PATCH = "VARIABLE_PATCH"


class Event(BaseModel):
    """Represents a discrete event in the execution log.

    Attributes:
        id: Unique identifier for the event.
        type: The type of event (e.g., USER_MSG, SYSTEM_INJECT).
        payload: The actual content of the event.
        timestamp: When the event occurred.
        parent_event_id: The ID of the preceding event, if any.
    """

    id: UUID
    type: EventType
    payload: Dict[str, Any]
    timestamp: datetime
    parent_event_id: Optional[UUID] = None


class ExecutionStatus(str, Enum):
    """Enumeration of execution statuses for a branch.

    Attributes:
        RUNNING: The branch is currently active.
        PAUSED: The branch execution is halted.
        COMPLETED: The branch has finished execution naturally.
        MERGED: The branch was selected as the winner in a fork.
        ABANDONED: The branch was rejected in favor of another fork.
    """

    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    MERGED = "MERGED"  # The winner
    ABANDONED = "ABANDONED"  # The loser


class ExecutionBranch(BaseModel):
    """Represents a specific execution path (timeline) in the conversation tree.

    Attributes:
        id: Unique identifier for the branch.
        parent_id: The ID of the parent branch from which this was forked.
        parent_event_id: The ID of the last event in the parent branch before the fork.
        root_id: The global identifier for the entire conversation tree.
        owner_id: The user who created this fork.
        fork_trigger_event: Description of what triggered the fork (e.g., "Human Override").
        override_instruction: The text instruction provided by the human supervisor.
        status: Current status of the branch (e.g., RUNNING, MERGED).
        created_at: When the branch was created.
        kv_cache_pointer: Pointer for Prefix Caching optimization to reuse attention blocks.
    """

    id: UUID
    parent_id: Optional[UUID]
    parent_event_id: Optional[UUID] = None
    root_id: UUID  # The original conversation ID
    owner_id: str  # The user who created this fork

    # The Fork Logic
    fork_trigger_event: str  # "Human Override"
    override_instruction: str

    status: ExecutionStatus
    created_at: datetime

    # SOTA: Prefix Caching Pointer
    # Optimization to avoid re-computing the shared history
    kv_cache_pointer: str


class FeedbackSignal(BaseModel):
    """Represents a Direct Preference Optimization (DPO) triplet for training.

    Generated when a human merges one branch (chosen) and abandons another (rejected).

    Attributes:
        source: Origin of the signal (default: "human-layer-fork").
        timestamp: When the signal was generated.
        author_id: Immutable ID of the user who provided the feedback.
        author_role: List of roles associated with the user.
        prompt_context: The shared history leading up to the fork.
        chosen_response: The output from the winning branch.
        rejected_response: The output from the losing branch.
        metadata: Additional context about the decision (e.g., user role).
    """

    source: str = "human-layer-fork"
    timestamp: datetime

    # Attribution
    author_id: str
    author_role: List[str]

    # DPO Triplet
    prompt_context: List[Dict[str, Any]]  # The conversation history
    chosen_response: str  # The Fork Outcome
    rejected_response: str  # The Original Outcome

    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            "user_role": "Medical Director",
            "override_type": "tone_correction",
        }
    )
