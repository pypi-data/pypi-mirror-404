"""
Pydantic models for the Agentic Framework
"""

from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, field_validator
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


class MessageRole(str, Enum):
    """Message roles in conversation"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(BaseModel):
    """Represents a message in the conversation"""
    role: MessageRole
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ToolParameter(BaseModel):
    """Represents a tool parameter"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None


class ToolSchema(BaseModel):
    """Schema for a tool"""
    name: str
    description: str
    parameters: Dict[str, Any]
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


class ToolCall(BaseModel):
    """Represents a tool call made by the agent"""
    id: str
    name: str
    arguments: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class ToolResult(BaseModel):
    """Represents the result of a tool execution"""
    tool_call_id: str
    tool_name: str
    result: Any
    error: Optional[str] = None
    execution_time: float  # in seconds
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @property
    def success(self) -> bool:
        """Check if tool execution was successful"""
        return self.error is None


class AgentEvent(BaseModel):
    """Represents an event emitted by the agent"""
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.now)
    iteration: Optional[int] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class IterationState(BaseModel):
    """State of a single iteration"""
    iteration_number: int
    tool_calls: List[ToolCall] = Field(default_factory=list)
    tool_results: List[ToolResult] = Field(default_factory=list)
    thinking: Optional[str] = None
    response: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get iteration duration in seconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class AgentConfig(BaseModel):
    """Configuration for the Agent"""
    system_prompt: str = Field(..., min_length=1, description="System prompt for the agent")
    model_name: Optional[str] = Field(None, description="OpenAI model name")
    temperature: float = Field(1.0, ge=0.0, le=2.0, description="Sampling temperature")
    max_iterations: int = Field(10, ge=1, le=100, description="Maximum iterations")
    stream: bool = Field(True, description="Enable streaming responses")
    verbose: bool = Field(True, description="Enable verbose logging")
    
    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is within acceptable range"""
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v


class AgentResponse(BaseModel):
    """Complete response from the agent"""
    task: str
    response: str
    iterations: List[IterationState]
    total_tool_calls: int
    success: bool
    error_message: Optional[str] = None
    start_time: datetime
    end_time: datetime
    
    @property
    def total_duration(self) -> float:
        """Get total execution duration in seconds"""
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def iteration_count(self) -> int:
        """Get total number of iterations"""
        return len(self.iterations)
