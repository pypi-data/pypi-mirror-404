"""
OR-AF Models - Tool related models
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


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
    execution_time: float
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @property
    def success(self) -> bool:
        """Check if tool execution was successful"""
        return self.error is None
