# coreason-human-layer

[![License: Prosperity 3.0](https://img.shields.io/badge/license-Prosperity%203.0-blue)](https://prosperitylicense.com/versions/3.0.0)
[![Build Status](https://github.com/CoReason-AI/coreason_human_layer/actions/workflows/build.yml/badge.svg)](https://github.com/CoReason-AI/coreason_human_layer/actions)
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Documentation](https://img.shields.io/badge/docs-Product%20Requirements-blue)](docs/product_requirements.md)

**Domain:** HITL, Durable Execution, & RLHF Data Capture
**Role:** The "Switchboard" & "Labeling Factory"

`coreason-human-layer` is the dedicated bridge between autonomous execution and human oversight, operationalizing **Online Alignment** through a **Multiverse Branching Strategy**. Instead of a simple "Stop/Go" model, it allows humans to fork agent reality, capturing decisions as **DPO Triplets** to fuel the model improvement loop.

## Features

### 1. The Stasis Engine (Durable Execution)
Implements an event-sourcing pattern for durable execution.
- **Snapshot:** Stores a pointer to the last event ID rather than a massive state blob.
- **Rehydration:** Replays events to rebuild context.
- **Storage:** Hot storage in Redis Streams, cold archival in S3.

### 2. The Branch Manager (Cognitive Forking)
Manages the tree topology of execution branches.
- **Forking:** `create_fork` API allows instantiating new execution paths with human overrides.
- **Prefix Caching:** Optimizes costs and latency by reusing the KV Cache of the shared prefix (`cached_prefix_id`) on the LLM backend.
- **Topology:** Exposes the conversation tree structure for visualization.

### 3. The Super-Prompt Injector (System Injection)
Ensures the model obeys human overrides.
- **Frame Injection:** Injects a high-priority `[SYSTEM PRIORITY INTERRUPT]` block.
- **Variable Patching:** Parses and hard-updates variables from human overrides (e.g., "Dose = 50mg").

### 4. The Learning Bridge (Auto-DPO)
Converts operational actions into training assets.
- **Trigger:** Merging a fork (approving it) while abandoning another.
- **Auto-DPO:** Automatically constructs a DPO object (`{ prompt, chosen, rejected }`) and pushes it to `coreason-synthesis`.

## Server Mode (The Switchboard)

The library now includes a standalone microservice mode, exposing a REST API for managing branches and forks.

### Deployment (Docker)

```bash
docker build -t coreason-human-layer .
docker run -p 8000:8000 \
  -e REDIS_URL=redis://host.docker.internal:6379 \
  -e SYNTHESIS_BASE_URL=http://host.docker.internal:8001 \
  coreason-human-layer
```

### Endpoints

- `POST /fork`: Create a new execution branch.
- `POST /merge`: Merge two branches (triggers DPO signal).
- `GET /topology/{root_id}`: Get the branch tree structure.
- `GET /health`: Check service health.

## Installation

```bash
pip install coreason-human-layer
```

## Usage (Library)

See `docs/usage.md` for detailed usage examples including the REST API.

```python
from uuid import uuid4
from coreason_human_layer.branch_manager import BranchManager
from coreason_human_layer.stasis import InMemoryStasisEngine

# Initialize engines
stasis = InMemoryStasisEngine()
manager = BranchManager(stasis_engine=stasis)

# Create a root branch
root_id = uuid4()
branch_id = manager.create_fork(
    parent_branch_id=None,
    parent_event_id=None,
    root_id=root_id,
    human_override_text="Initial Start",
    user_context=... # UserContext object
)
```

## License

Copyright (c) 2025 CoReason, Inc.
Licensed under the [Prosperity Public License 3.0](https://prosperitylicense.com/versions/3.0.0).
