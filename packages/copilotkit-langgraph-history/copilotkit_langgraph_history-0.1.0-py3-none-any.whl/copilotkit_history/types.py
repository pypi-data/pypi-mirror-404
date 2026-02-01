"""
Type definitions for copilotkit-langgraph-history.

These types match the HistoryClientInterface from the TypeScript package.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ThreadStateValues:
    """
    Values stored in a thread state checkpoint.
    """
    messages: List[Dict[str, Any]] = field(default_factory=list)
    # Additional state fields can be added dynamically
    
    def __init__(self, **kwargs):
        self.messages = kwargs.pop("messages", [])
        # Store any additional fields
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"messages": self.messages}
        for key, value in self.__dict__.items():
            if key != "messages":
                result[key] = value
        return result


@dataclass
class TaskInterrupt:
    """
    Interrupt information for a task.
    """
    value: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value}


@dataclass
class Task:
    """
    Task in a thread state.
    """
    id: str
    name: str
    interrupts: List[TaskInterrupt] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "interrupts": [i.to_dict() for i in self.interrupts],
        }


@dataclass
class HistoryCheckpoint:
    """
    Checkpoint from thread history.
    
    Matches the ThreadState interface in the TypeScript package.
    """
    values: Dict[str, Any]
    next: List[str]
    config: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    parent_config: Optional[Dict[str, Any]] = None
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    checkpoint: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None
    parent_checkpoint: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "values": self.values,
            "next": self.next,
            "config": self.config,
            "created_at": self.created_at,
            "parent_config": self.parent_config,
            "tasks": self.tasks,
            "checkpoint": self.checkpoint,
            "metadata": self.metadata,
            "parent_checkpoint": self.parent_checkpoint,
        }


@dataclass
class HistoryRun:
    """
    Run object returned from runs.list().
    
    Matches the HistoryRun interface in the TypeScript package.
    """
    run_id: str
    status: str  # "running" | "pending" | "success" | "error" | "timeout" | "interrupted"
    thread_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "run_id": self.run_id,
            "status": self.status,
            "thread_id": self.thread_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class HistoryStreamChunk:
    """
    Stream chunk from joinStream().
    
    Matches the HistoryStreamChunk interface in the TypeScript package.
    """
    event: str
    data: Any
    id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "event": self.event,
            "data": self.data,
            "id": self.id,
            "metadata": self.metadata,
        }


