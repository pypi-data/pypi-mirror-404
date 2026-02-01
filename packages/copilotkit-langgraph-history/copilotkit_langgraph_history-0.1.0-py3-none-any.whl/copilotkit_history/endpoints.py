"""
FastAPI endpoints for CopilotKit LangGraph history persistence.

These endpoints implement the HistoryClientInterface from the TypeScript package,
enabling self-hosted FastAPI servers to work with copilotkit-langgraph-history.
"""

import json
import asyncio
from typing import Any, Dict, List, Optional, AsyncGenerator, Union
from datetime import datetime

from fastapi import FastAPI, APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.base import BaseCheckpointSaver

from .types import HistoryCheckpoint, HistoryRun


def add_history_endpoints(
    app: FastAPI,
    graph: CompiledStateGraph,
    prefix: str = "",
    *,
    include_join_stream: bool = True,
) -> APIRouter:
    """
    Add history endpoints to a FastAPI app for CopilotKit integration.
    
    These endpoints implement the HistoryClientInterface from the TypeScript
    package `copilotkit-langgraph-history`, enabling thread history persistence
    and resumption for self-hosted LangGraph servers.
    
    Args:
        app: The FastAPI application instance
        graph: A compiled LangGraph StateGraph with a checkpointer
        prefix: Optional URL prefix for the endpoints (e.g., "/api/v1")
        include_join_stream: Whether to include the /runs/{run_id}/join endpoint
                           (requires additional run tracking, defaults to True)
    
    Returns:
        The APIRouter instance (for further customization if needed)
    
    Example:
        ```python
        from fastapi import FastAPI
        from langgraph.checkpoint.postgres import PostgresSaver
        from copilotkit_history import add_history_endpoints
        
        app = FastAPI()
        
        # Create graph with persistent checkpointer
        checkpointer = PostgresSaver.from_conn_string(DATABASE_URL)
        graph = workflow.compile(checkpointer=checkpointer)
        
        # Add history endpoints
        add_history_endpoints(app, graph)
        
        # Now these endpoints are available:
        # GET  /threads/{thread_id}/history
        # GET  /threads/{thread_id}/state
        # GET  /runs
        # POST /runs/{run_id}/join (if include_join_stream=True)
        ```
    
    Note:
        The graph MUST have a checkpointer configured. Using MemorySaver
        is fine for development but won't persist across server restarts.
        For production, use PostgresSaver or another persistent checkpointer.
    """
    router = APIRouter()
    checkpointer = graph.checkpointer
    
    if checkpointer is None:
        raise ValueError(
            "Graph must have a checkpointer configured. "
            "Use MemorySaver for development or PostgresSaver for production."
        )
    
    # Simple in-memory run tracking (for basic functionality)
    # In production, you'd want to persist this or use a proper run manager
    _active_runs: Dict[str, HistoryRun] = {}
    
    @router.get("/threads/{thread_id}/history")
    async def get_thread_history(
        thread_id: str,
        limit: int = Query(default=100, ge=1, le=1000),
    ) -> List[Dict[str, Any]]:
        """
        Fetch checkpoint history for a thread.
        
        Returns checkpoints in newest-first order (the TypeScript library
        reverses them to get chronological order).
        
        Args:
            thread_id: The thread ID to fetch history for
            limit: Maximum number of checkpoints to return (default: 100, max: 1000)
        
        Returns:
            List of checkpoint objects matching the ThreadState interface
        """
        try:
            config = {"configurable": {"thread_id": thread_id}}
            history: List[Dict[str, Any]] = []
            count = 0
            
            # Use alist for async iteration over checkpoints
            async for checkpoint_tuple in checkpointer.alist(config):
                if count >= limit:
                    break
                
                checkpoint_data = checkpoint_tuple.checkpoint
                checkpoint_config = checkpoint_tuple.config
                metadata = checkpoint_tuple.metadata or {}
                
                # Extract channel values (this is where messages live)
                channel_values = checkpoint_data.get("channel_values", {})
                
                # Build the checkpoint response
                history_item: Dict[str, Any] = {
                    "values": channel_values,
                    "next": checkpoint_data.get("pending_sends", []),
                    "config": checkpoint_config,
                    "metadata": metadata,
                    "created_at": metadata.get("created_at") or checkpoint_data.get("ts"),
                    "parent_config": checkpoint_tuple.parent_config,
                    "tasks": [],  # Tasks are typically in the latest state only
                    "checkpoint": None,  # Don't expose raw checkpoint data
                    "parent_checkpoint": None,
                }
                
                history.append(history_item)
                count += 1
            
            return history
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch thread history: {str(e)}"
            )
    
    @router.get("/threads/{thread_id}/state")
    async def get_thread_state(thread_id: str) -> Dict[str, Any]:
        """
        Get the current state of a thread.
        
        Args:
            thread_id: The thread ID to get state for
        
        Returns:
            Current thread state matching the ThreadState interface
        """
        try:
            config = {"configurable": {"thread_id": thread_id}}
            state = await graph.aget_state(config)
            
            if state is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Thread {thread_id} not found"
                )
            
            # Extract tasks with interrupts
            tasks = []
            if hasattr(state, "tasks") and state.tasks:
                for task in state.tasks:
                    task_dict: Dict[str, Any] = {
                        "id": getattr(task, "id", str(id(task))),
                        "name": getattr(task, "name", "unknown"),
                        "interrupts": [],
                    }
                    
                    # Check for interrupts
                    if hasattr(task, "interrupts") and task.interrupts:
                        for interrupt in task.interrupts:
                            task_dict["interrupts"].append({
                                "value": getattr(interrupt, "value", None),
                            })
                    
                    tasks.append(task_dict)
            
            return {
                "values": state.values if hasattr(state, "values") else {},
                "next": list(state.next) if hasattr(state, "next") and state.next else [],
                "config": state.config if hasattr(state, "config") else config,
                "metadata": state.metadata if hasattr(state, "metadata") else {},
                "created_at": state.created_at if hasattr(state, "created_at") else None,
                "tasks": tasks,
                "checkpoint": None,
                "parent_checkpoint": None,
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get thread state: {str(e)}"
            )
    
    @router.get("/runs")
    async def list_runs(
        thread_id: str = Query(..., description="Thread ID to list runs for"),
    ) -> List[Dict[str, Any]]:
        """
        List runs for a thread.
        
        Note: This is a simplified implementation that tracks runs in-memory.
        For production, you should persist run information.
        
        Args:
            thread_id: The thread ID to list runs for
        
        Returns:
            List of run objects matching the HistoryRun interface
        """
        # Filter runs by thread_id
        runs = [
            run.to_dict()
            for run in _active_runs.values()
            if run.thread_id == thread_id
        ]
        
        # Sort by most recent first
        runs.sort(key=lambda r: r.get("updated_at") or "", reverse=True)
        
        return runs
    
    if include_join_stream:
        @router.post("/runs/{run_id}/join")
        async def join_run_stream(
            run_id: str,
            thread_id: str = Query(..., description="Thread ID"),
        ) -> StreamingResponse:
            """
            Join an active run's stream.
            
            This endpoint streams Server-Sent Events (SSE) for an active run.
            
            Note: This is a simplified implementation. For full functionality,
            you would need to integrate with LangGraph's streaming infrastructure.
            
            Args:
                run_id: The run ID to join
                thread_id: The thread ID
            
            Returns:
                SSE stream of run events
            """
            async def event_generator() -> AsyncGenerator[str, None]:
                """Generate SSE events."""
                # Check if run exists and is active
                run = _active_runs.get(run_id)
                
                if not run:
                    # Send error event
                    yield format_sse_event("error", {
                        "error": "run_not_found",
                        "message": f"Run {run_id} not found",
                    })
                    return
                
                if run.status not in ("running", "pending"):
                    # Run already completed - send completion event
                    yield format_sse_event("metadata", {
                        "run_id": run_id,
                        "thread_id": thread_id,
                    })
                    yield format_sse_event("values", {
                        "status": run.status,
                    })
                    return
                
                # For active runs, you would integrate with LangGraph's
                # streaming infrastructure here. This is a placeholder.
                yield format_sse_event("metadata", {
                    "run_id": run_id,
                    "thread_id": thread_id,
                })
                
                # Poll for completion (simplified)
                while True:
                    await asyncio.sleep(0.5)
                    
                    current_run = _active_runs.get(run_id)
                    if not current_run or current_run.status not in ("running", "pending"):
                        break
                
                # Send final state
                try:
                    config = {"configurable": {"thread_id": thread_id}}
                    state = await graph.aget_state(config)
                    if state and hasattr(state, "values"):
                        yield format_sse_event("values", state.values)
                except Exception:
                    pass
            
            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
    
    # Helper to register/update runs (call this from your agent code)
    def register_run(
        run_id: str,
        thread_id: str,
        status: str = "running",
    ) -> HistoryRun:
        """
        Register or update a run.
        
        Call this from your agent code when starting/completing runs.
        
        Args:
            run_id: Unique run identifier
            thread_id: Thread ID for the run
            status: Run status ("running", "pending", "success", "error", etc.)
        
        Returns:
            The HistoryRun object
        """
        now = datetime.utcnow().isoformat() + "Z"
        
        if run_id in _active_runs:
            run = _active_runs[run_id]
            run.status = status
            run.updated_at = now
        else:
            run = HistoryRun(
                run_id=run_id,
                thread_id=thread_id,
                status=status,
                created_at=now,
                updated_at=now,
            )
            _active_runs[run_id] = run
        
        return run
    
    def complete_run(run_id: str, status: str = "success") -> Optional[HistoryRun]:
        """
        Mark a run as completed.
        
        Args:
            run_id: The run ID to complete
            status: Final status ("success", "error", "timeout", "interrupted")
        
        Returns:
            The updated HistoryRun or None if not found
        """
        if run_id in _active_runs:
            run = _active_runs[run_id]
            run.status = status
            run.updated_at = datetime.utcnow().isoformat() + "Z"
            return run
        return None
    
    # Attach helper functions to the router for external access
    router.register_run = register_run  # type: ignore
    router.complete_run = complete_run  # type: ignore
    
    # Mount the router
    app.include_router(router, prefix=prefix)
    
    return router


def format_sse_event(event_type: str, data: Any) -> str:
    """
    Format data as a Server-Sent Event.
    
    Args:
        event_type: The event type/name
        data: Data to serialize as JSON
    
    Returns:
        Formatted SSE string
    """
    json_data = json.dumps(data)
    return f"event: {event_type}\ndata: {json_data}\n\n"


