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
from typing import Any, List, Protocol
from uuid import UUID

import boto3
from botocore.exceptions import ClientError
from coreason_identity.models import UserContext

from coreason_human_layer.models import Event
from coreason_human_layer.utils.logger import logger


class S3ClientProtocol(Protocol):
    """Protocol for S3 client subset used by Archiver."""

    def put_object(self, Bucket: str, Key: str, Body: str) -> Any:
        """Puts an object into an S3 bucket.

        Args:
            Bucket: The name of the bucket.
            Key: The key of the object.
            Body: The content of the object.

        Returns:
            The response from the S3 service.
        """
        ...


class S3Archiver:
    """Handles the cold storage of event logs to S3."""

    def __init__(self, bucket_name: str, s3_client: Any = None) -> None:
        """Initialize the S3 Archiver.

        Args:
            bucket_name: The name of the S3 bucket.
            s3_client: Optional boto3 client. If None, creates a default one.
                       Typed as Any to allow real boto3 clients which don't easily satisfy
                       strict Protocols without stubs.
        """
        self.bucket_name = bucket_name
        self.s3_client = s3_client or boto3.client("s3")

    def archive_branch(self, root_id: UUID, branch_id: UUID, events: List[Event], *, context: UserContext) -> bool:
        """Serializes and uploads the event history of a branch to S3.

        Key format: archives/{root_id}/{branch_id}.json

        Args:
            root_id: The global identifier for the conversation.
            branch_id: The identifier for the specific execution branch.
            events: The list of events to archive.
            context: The user context for the operation (mandatory).

        Returns:
            True if upload succeeded, False otherwise.
        """
        if context is None:
            raise ValueError("UserContext is mandatory for archive_branch")

        key = f"archives/{root_id}/{branch_id}.json"

        logger.info("Archiving branch to S3", user_id=context.user_id, branch_id=str(branch_id))

        try:
            # Serialize events to a JSON list
            # We use model_dump(mode="json") to handle UUIDs/Datetimes via Pydantic
            data_list = [event.model_dump(mode="json") for event in events]
            serialized_body = json.dumps(data_list, default=str)

            self.s3_client.put_object(Bucket=self.bucket_name, Key=key, Body=serialized_body)

            logger.info(
                "Successfully archived branch to S3",
                root_id=str(root_id),
                branch_id=str(branch_id),
            )
            return True

        except (ClientError, Exception) as e:
            logger.error(
                "Failed to archive branch to S3",
                root_id=str(root_id),
                branch_id=str(branch_id),
                error=str(e),
            )
            return False
