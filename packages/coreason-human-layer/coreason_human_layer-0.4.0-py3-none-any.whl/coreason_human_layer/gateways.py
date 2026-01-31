# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_human_layer

from typing import Optional, Protocol, runtime_checkable

import httpx
from coreason_identity.models import UserContext

from coreason_human_layer.models import FeedbackSignal
from coreason_human_layer.utils.logger import logger


@runtime_checkable
class SynthesisGateway(Protocol):
    """Protocol for the gateway to the Synthesis service (Learning Loop).

    Abstracts the transport layer for sending FeedbackSignals.
    """

    async def send_feedback(self, signal: FeedbackSignal, user_context: UserContext) -> bool:
        """Sends the feedback signal to the Synthesis service.

        Args:
            signal: The FeedbackSignal object containing the DPO triplet.
            user_context: The context of the user sending the feedback.

        Returns:
            True if successful, False otherwise.
            Should not raise exceptions (must be resilient).
        """
        ...


class HttpSynthesisGateway:
    """HTTP implementation of the SynthesisGateway.

    Sends feedback signals to a configured endpoint via POST.
    """

    def __init__(self, base_url: str, timeout: float = 5.0, client: Optional[httpx.AsyncClient] = None) -> None:
        """Initialize the HTTP Synthesis Gateway.

        Args:
            base_url: The base URL of the Synthesis service (e.g., "http://localhost:8000").
            timeout: Request timeout in seconds.
            client: Optional httpx.AsyncClient. If provided, the gateway will use it.
                    If not, it creates its own client.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.endpoint = "/ingest-feedback"
        self._internal_client = client is None
        self._client = client or httpx.AsyncClient()

    async def __aenter__(self) -> "HttpSynthesisGateway":
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        if self._internal_client:
            await self._client.aclose()

    async def send_feedback(self, signal: FeedbackSignal, user_context: UserContext) -> bool:
        """Sends the feedback signal to the Synthesis service.

        Args:
            signal: The FeedbackSignal object containing the DPO triplet.
            user_context: The context of the user sending the feedback.

        Returns:
            True if successful, False otherwise.
            Failures are logged but not raised to ensure system resilience.
        """
        if str(signal.author_id) != user_context.user_id:
            logger.error(
                "Security Alert: Feedback signal author mismatch",
                signal_author=signal.author_id,
                user_context_id=user_context.user_id,
            )
            return False

        url = f"{self.base_url}{self.endpoint}"
        try:
            # Serialize the signal to JSON
            payload = signal.model_dump(mode="json")

            response = await self._client.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "X-Downstream-Token": user_context.downstream_token.get_secret_value(),
                },
            )

            response.raise_for_status()
            logger.info(
                "Successfully sent feedback signal to Synthesis",
                signal_timestamp=signal.timestamp,
            )
            return True

        except httpx.RequestError as e:
            # Log the error but do not crash.
            # In a real system, we might queue this for retry (Dead Letter Queue).
            logger.error(
                "Failed to send feedback signal to Synthesis",
                url=url,
                error=str(e),
                signal_data=signal.model_dump_json(),  # Log data so it's not lost entirely
            )
            return False
        except httpx.HTTPStatusError as e:
            logger.error(
                "Failed to send feedback signal to Synthesis (HTTP Error)",
                url=url,
                status=e.response.status_code,
                error=str(e),
                signal_data=signal.model_dump_json(),
            )
            return False
