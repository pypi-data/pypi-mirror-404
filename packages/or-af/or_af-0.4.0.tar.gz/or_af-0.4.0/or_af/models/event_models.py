"""
OR-AF Models - Event related models
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Types of events that can be emitted by the agent"""
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    ITERATION_START = "iteration_start"
    ITERATION_END = "iteration_end"
    THINKING = "thinking"
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_END = "tool_call_end"
    TOOL_ERROR = "tool_error"
    STREAM_CHUNK = "stream_chunk"
    ERROR = "error"
    WARNING = "warning"


class AgentEvent(BaseModel):
    """Represents an event emitted by the agent"""
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.now)
    iteration: Optional[int] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True
