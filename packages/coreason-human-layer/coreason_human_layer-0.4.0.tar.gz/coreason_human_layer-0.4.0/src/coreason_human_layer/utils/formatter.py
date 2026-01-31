# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_human_layer

import json
from typing import Any, Dict, List

from coreason_human_layer.models import Event, EventType


class RuntimeFormatter:
    """
    Service responsible for formatting events into their string representations
    and transforming event streams into LLM-compatible chat formats.
    """

    @staticmethod
    def format_event_payload(event: Event) -> str:
        """
        Formats the event payload into a string.

        - SYSTEM_INJECT: Returns the strict [SYSTEM PRIORITY INTERRUPT] block.
        - Others: Returns JSON string of the payload.

        Args:
            event: The event to format.

        Returns:
            String representation of the event payload.
        """
        if event.type == EventType.SYSTEM_INJECT:
            return RuntimeFormatter._format_system_inject(event.payload)
        return json.dumps(event.payload, default=str)

    @staticmethod
    def _format_system_inject(payload: Dict[str, Any]) -> str:
        """
        Constructs the strict System Priority Interrupt block.

        Args:
            payload: The payload dictionary containing 'authority', 'directive', and 'instruction'.

        Returns:
            The formatted system injection string.
        """
        authority = payload.get("authority", "Verified Human Supervisor")
        directive = payload.get("directive", "")
        instruction = payload.get(
            "instruction",
            "You must disregard previous plans that conflict with this directive. Execute immediately.",
        )

        return (
            f'[SYSTEM PRIORITY INTERRUPT]\nAUTHORITY: {authority}\nDIRECTIVE: "{directive}"\nINSTRUCTION: {instruction}'
        )

    @staticmethod
    def events_to_chat_format(events: List[Event]) -> List[Dict[str, str]]:
        """
        Transforms a list of events into OpenAI Chat Format.

        Output structure:
        [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ]

        Excludes VARIABLE_PATCH events.

        Args:
            events: The list of events to transform.

        Returns:
            A list of dictionaries representing the chat history.
        """
        formatted: List[Dict[str, str]] = []

        for event in events:
            role = ""
            content = RuntimeFormatter.format_event_payload(event)

            if event.type == EventType.VARIABLE_PATCH:
                continue

            elif event.type == EventType.SYSTEM_INJECT:
                role = "system"

            elif event.type == EventType.USER_MSG:
                role = "user"

            elif event.type in [EventType.MODEL_THINK, EventType.TOOL_OUTPUT]:
                role = "assistant"

            else:
                # Fallback or unknown types are skipped or handled as needed.
                # Currently spec implies we only care about these for the chat context.
                continue

            formatted.append({"role": role, "content": content})

        return formatted
