"""
OR-AF Models - Agent related models
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from .tool_models import ToolCall, ToolResult


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
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v


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
