"""
copilotkit-langgraph-history

FastAPI endpoints for CopilotKit LangGraph history persistence.
Companion to the npm package copilotkit-langgraph-history.

Usage:
    from copilotkit_history import add_history_endpoints
    
    app = FastAPI()
    graph = workflow.compile(checkpointer=checkpointer)
    
    add_history_endpoints(app, graph)
"""

from .endpoints import add_history_endpoints
from .types import (
    HistoryCheckpoint,
    HistoryRun,
    HistoryStreamChunk,
    ThreadStateValues,
)

__version__ = "0.1.0"

__all__ = [
    "add_history_endpoints",
    "HistoryCheckpoint",
    "HistoryRun",
    "HistoryStreamChunk",
    "ThreadStateValues",
]


