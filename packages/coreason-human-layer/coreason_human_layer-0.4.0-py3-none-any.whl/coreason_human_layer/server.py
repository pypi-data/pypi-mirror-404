from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional, cast
from uuid import UUID

from coreason_identity.models import UserContext
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, SecretStr
from redis.asyncio import Redis

from coreason_human_layer.branch_manager import BranchManagerAsync
from coreason_human_layer.gateways import HttpSynthesisGateway
from coreason_human_layer.models import FeedbackSignal
from coreason_human_layer.stasis import RedisStasisEngine


# Models
class ForkRequest(BaseModel):
    parent_branch_id: Optional[UUID] = None
    parent_event_id: Optional[UUID] = None
    root_id: UUID
    human_override_text: str


class ForkResponse(BaseModel):
    branch_id: UUID
    kv_cache_pointer: str


class MergeRequest(BaseModel):
    winning_branch_id: UUID
    losing_branch_id: UUID


class HealthResponse(BaseModel):
    status: str
    engine: str


# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    synthesis_url = os.getenv("SYNTHESIS_BASE_URL", "http://localhost:8000")

    # decode_responses=False because StasisEngine might handle decoding or expect bytes
    # But StasisEngine code says: raw_data = fields.get("data") or fields.get(b"data")
    # If I use decode_responses=True, "data" will be string.
    # StasisEngine: if isinstance(raw_data, bytes): raw_data = raw_data.decode("utf-8")
    # So it supports both. I'll stick to default (False) or True?
    # Let's use True to be safe with modern redis-py usage, but RedisStasisEngine seems robust.
    # Actually, let's use default (False, bytes) to avoid any double decoding issues
    # if StasisEngine expects bytes initially.
    redis_client: Redis[Any] = Redis.from_url(redis_url, decode_responses=False)

    stasis_engine = RedisStasisEngine(redis_client)
    synthesis_gateway = HttpSynthesisGateway(base_url=synthesis_url)

    manager = BranchManagerAsync(stasis_engine=stasis_engine, synthesis_gateway=synthesis_gateway)

    app.state.manager = manager
    app.state.redis = redis_client

    yield

    # Cleanup
    await redis_client.close()


app = FastAPI(lifespan=lifespan)


# Dependencies
async def get_branch_manager(request: Request) -> BranchManagerAsync:
    return request.app.state.manager


async def get_user_context(
    x_user_id: str = Header(..., alias="X-User-Id"),
    x_user_email: str = Header(..., alias="X-User-Email"),
    x_user_groups: str = Header(default="", alias="X-User-Groups"),
    authorization: str = Header(default="", alias="Authorization"),
) -> UserContext:
    # Handle groups parsing
    groups = [g.strip() for g in x_user_groups.split(",")] if x_user_groups else []

    # Handle token
    token = authorization
    if token.lower().startswith("bearer "):
        token = token[7:]

    return UserContext(
        user_id=x_user_id,
        email=x_user_email,
        groups=groups,
        downstream_token=SecretStr(token),
    )


# Endpoints
@app.post("/fork", response_model=ForkResponse)
async def create_fork(
    request: ForkRequest,
    manager: BranchManagerAsync = Depends(get_branch_manager),
    user_context: UserContext = Depends(get_user_context),
) -> ForkResponse:
    branch_id = await manager.create_fork(
        parent_branch_id=request.parent_branch_id,
        parent_event_id=request.parent_event_id,
        root_id=request.root_id,
        human_override_text=request.human_override_text,
        user_context=user_context,
    )

    # kv_cache_pointer retrieval
    branch = manager.get_branch(branch_id)
    if not branch:
        raise HTTPException(status_code=500, detail="Branch created but not found")

    return ForkResponse(
        branch_id=branch_id,
        kv_cache_pointer=branch.kv_cache_pointer,
    )


@app.post("/merge", response_model=FeedbackSignal)
async def merge_branches(
    request: MergeRequest,
    manager: BranchManagerAsync = Depends(get_branch_manager),
    user_context: UserContext = Depends(get_user_context),
) -> FeedbackSignal:
    try:
        signal = await manager.merge_branches(
            winning_branch_id=request.winning_branch_id,
            losing_branch_id=request.losing_branch_id,
            user_context=user_context,
        )
        return signal
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/topology/{root_id}")
async def get_topology(
    root_id: UUID,
    manager: BranchManagerAsync = Depends(get_branch_manager),
) -> List[Dict[str, Any]]:
    return cast(List[Dict[str, Any]], manager.get_branch_topology(root_id))


@app.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    redis_client: Redis[Any] = request.app.state.redis
    try:
        await redis_client.ping()
        return HealthResponse(status="active", engine="redis")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis connection failed: {str(e)}") from e
