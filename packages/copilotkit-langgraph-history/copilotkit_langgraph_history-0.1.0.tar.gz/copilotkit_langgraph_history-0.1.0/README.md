# copilotkit-langgraph-history (Python)

[![PyPI version](https://img.shields.io/pypi/v/copilotkit-langgraph-history.svg)](https://pypi.org/project/copilotkit-langgraph-history/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)

**FastAPI endpoints for CopilotKit LangGraph history persistence.** Companion to the npm package [copilotkit-langgraph-history](https://www.npmjs.com/package/copilotkit-langgraph-history).

## The Problem

Using CopilotKit with a self-hosted LangGraph FastAPI server? The npm package `copilotkit-langgraph-history` provides thread history persistence, but it needs specific API endpoints on your server.

**This package provides those endpoints with a single function call.**

## Installation

```bash
pip install copilotkit-langgraph-history
```

## Quick Start

```python
from fastapi import FastAPI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from copilotkit_history import add_history_endpoints

# Your existing FastAPI app
app = FastAPI()

# Your LangGraph graph with a checkpointer
checkpointer = MemorySaver()  # Use PostgresSaver for production
graph = workflow.compile(checkpointer=checkpointer)

# Add history endpoints - that's it!
add_history_endpoints(app, graph)
```

This adds the following endpoints to your FastAPI app:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/threads/{thread_id}/history` | GET | Fetch checkpoint history |
| `/threads/{thread_id}/state` | GET | Get current thread state |
| `/runs` | GET | List runs for a thread |
| `/runs/{run_id}/join` | POST | Join an active run stream |

## Full Example

Here's a complete example with `LangGraphAGUIAgent`:

```python
import os
from fastapi import FastAPI
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import StateGraph
from copilotkit import LangGraphAGUIAgent
from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from copilotkit_history import add_history_endpoints

app = FastAPI()

# Use a persistent checkpointer for production
DATABASE_URL = os.getenv("DATABASE_URL")
checkpointer = PostgresSaver.from_conn_string(DATABASE_URL)

# Build your graph
workflow = StateGraph(AgentState)
# ... add nodes and edges ...
graph = workflow.compile(checkpointer=checkpointer)

# Add the standard AG-UI endpoint for CopilotKit
add_langgraph_fastapi_endpoint(
    app=app,
    agent=LangGraphAGUIAgent(
        name="my_agent",
        graph=graph,
    ),
    path="/",
)

# Add history endpoints for thread persistence
add_history_endpoints(app, graph)

# Now your server supports:
# - AG-UI protocol (via add_langgraph_fastapi_endpoint)
# - History hydration (via add_history_endpoints)
```

## TypeScript Integration

On the TypeScript side, use `copilotkit-langgraph-history` with a custom client:

```typescript
import {
  HistoryHydratingAgentRunner,
  HistoryClientInterface,
} from "copilotkit-langgraph-history";

const FASTAPI_URL = "http://localhost:8000";

// Create a client that talks to your FastAPI endpoints
const customClient: HistoryClientInterface = {
  threads: {
    getHistory: async (threadId, options) => {
      const res = await fetch(
        `${FASTAPI_URL}/threads/${threadId}/history?limit=${options?.limit ?? 100}`
      );
      return res.json();
    },
    getState: async (threadId) => {
      const res = await fetch(`${FASTAPI_URL}/threads/${threadId}/state`);
      return res.json();
    },
  },
  runs: {
    list: async (threadId) => {
      const res = await fetch(`${FASTAPI_URL}/runs?thread_id=${threadId}`);
      return res.json();
    },
    joinStream: async function* (threadId, runId) {
      const res = await fetch(
        `${FASTAPI_URL}/runs/${runId}/join?thread_id=${threadId}`,
        {
          method: "POST",
          headers: { Accept: "text/event-stream" },
        }
      );
      // Parse SSE stream...
      // (implement based on your needs)
    },
  },
};

// Use with the runner
const runner = new HistoryHydratingAgentRunner({
  agent,
  client: customClient,
  historyLimit: 100,
});
```

## Configuration

### `add_history_endpoints()` Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app` | `FastAPI` | **required** | Your FastAPI application |
| `graph` | `CompiledStateGraph` | **required** | LangGraph graph with checkpointer |
| `prefix` | `str` | `""` | URL prefix (e.g., `/api/v1`) |
| `include_join_stream` | `bool` | `True` | Include the join stream endpoint |

### Example with Prefix

```python
add_history_endpoints(app, graph, prefix="/api/v1")

# Endpoints are now:
# GET /api/v1/threads/{thread_id}/history
# GET /api/v1/threads/{thread_id}/state
# etc.
```

## Checkpointer Requirements

**Important:** The graph MUST have a checkpointer configured.

| Checkpointer | Use Case |
|--------------|----------|
| `MemorySaver` | Development only (data lost on restart) |
| `PostgresSaver` | Production (persistent) |
| `SqliteSaver` | Development/testing with persistence |

```python
# Development
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()

# Production
from langgraph.checkpoint.postgres import PostgresSaver
checkpointer = PostgresSaver.from_conn_string(DATABASE_URL)

graph = workflow.compile(checkpointer=checkpointer)
```

## Run Tracking

The package includes basic in-memory run tracking. For production use with active run joining, you can use the helper functions:

```python
router = add_history_endpoints(app, graph)

# When starting a run
router.register_run(run_id="abc123", thread_id="thread-1", status="running")

# When completing a run
router.complete_run(run_id="abc123", status="success")
```

For full production run tracking, consider integrating with your own database or using LangGraph Platform.

## API Response Format

### GET /threads/{thread_id}/history

Returns an array of checkpoints (newest first):

```json
[
  {
    "values": {
      "messages": [...],
      "custom_field": "value"
    },
    "next": [],
    "config": {"configurable": {"thread_id": "..."}},
    "metadata": {},
    "created_at": "2024-01-01T00:00:00Z",
    "tasks": []
  }
]
```

### GET /threads/{thread_id}/state

Returns the current thread state:

```json
{
  "values": {
    "messages": [...],
    "custom_field": "value"
  },
  "next": ["node_name"],
  "tasks": [
    {
      "id": "task-1",
      "name": "chat_node",
      "interrupts": []
    }
  ]
}
```

## License

MIT License - see [LICENSE](../LICENSE) for details.

## Related

- [copilotkit-langgraph-history (npm)](https://www.npmjs.com/package/copilotkit-langgraph-history) - TypeScript package for CopilotKit runtime
- [CopilotKit](https://copilotkit.ai) - Build AI copilots for your apps
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Build stateful AI agents


