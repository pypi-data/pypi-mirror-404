"""
Agentic Framework - A lightweight framework for creating AI agents

This package provides a simple yet powerful framework for building AI agents
with tool-calling capabilities, streaming support, and comprehensive observability.
"""

from .agent import Agent
from .tool import Tool
from .models import (
    AgentConfig,
    AgentResponse,
    AgentEvent,
    EventType,
    ToolCall,
    ToolResult,
    IterationState,
    Message,
    MessageRole
)
from .callbacks import (
    BaseCallback,
    ConsoleCallback,
    LoggingCallback,
    CallbackManager
)
from .exceptions import (
    AgenticFrameworkError,
    ToolNotFoundError,
    ToolExecutionError,
    MaxIterationsReachedError,
    InvalidConfigurationError,
    OpenAIError
)
from .logger import setup_logger

__version__ = "0.1.0"
__author__ = "Agentic Framework Team"

__all__ = [
    # Core classes
    "Agent",
    "Tool",
    
    # Models
    "AgentConfig",
    "AgentResponse",
    "AgentEvent",
    "EventType",
    "ToolCall",
    "ToolResult",
    "IterationState",
    "Message",
    "MessageRole",
    
    # Callbacks
    "BaseCallback",
    "ConsoleCallback",
    "LoggingCallback",
    "CallbackManager",
    
    # Exceptions
    "AgenticFrameworkError",
    "ToolNotFoundError",
    "ToolExecutionError",
    "MaxIterationsReachedError",
    "InvalidConfigurationError",
    "OpenAIError",
    
    # Utils
    "setup_logger",
]
