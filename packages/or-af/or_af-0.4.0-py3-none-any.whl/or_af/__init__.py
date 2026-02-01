"""
OR-AF (Operations Research Agentic Framework) - A lightweight framework for creating AI agents

This package provides a powerful framework for building AI agents with:
- Official MCP SDK integration (https://modelcontextprotocol.io/)
- Official A2A SDK integration (https://a2a-protocol.org/)
- Workflow graphs for defining complex agent pipelines
- TensorFlow-like API for defining workflows
- Graph visualization capabilities

Key Concepts:
1. Tools are registered with MCP servers using decorators
2. Agents can connect to MCP servers via stdio or HTTP
3. A2A protocol enables inter-agent communication
4. Workflows are defined as directed graphs with agents as nodes
5. Edges can have conditions for dynamic routing

Module Structure:
- core/     : Agent, Tool
- mcp/      : MCPServer, MCPClient (official MCP SDK wrappers)
- workflow/ : WorkflowGraph, Sequential, Parallel, visualization
- a2a/      : A2AAgent, A2AExecutor (official A2A SDK wrappers)
- models/   : Pydantic models
- callbacks/: Event callbacks
- exceptions/: Custom exceptions
- utils/    : Logger and utilities

Official SDK Documentation:
- MCP: https://modelcontextprotocol.io/
- A2A: https://a2a-protocol.org/
"""

# Core classes
from .core import Agent, Tool

# MCP Server (using official MCP SDK)
from .mcp import (
    MCPServer,
    MCPClient,
    MCPServerStatus,
    create_mcp_server,
    connect_mcp_server
)

# Workflow
from .workflow import (
    WorkflowGraph,
    Sequential,
    Parallel,
    Node,
    ConditionalEdge,
    EdgeCondition,
    NodeStatus,
    NodeResult,
    workflow,
    WorkflowVisualizer,
    visualize_workflow
)

# A2A Protocol (using official A2A SDK)
from .a2a import (
    A2AAgent,
    A2AAgentStatus,
    BaseA2AExecutor,
    SimpleA2AExecutor,
    AgentCard,
    AgentCapabilities,
    AgentSkill,
    new_agent_text_message,
    create_a2a_agent
)

# Models
from .models import (
    AgentConfig,
    AgentResponse,
    AgentEvent,
    EventType,
    ToolCall,
    ToolResult,
    ToolSchema,
    IterationState,
    Message,
    MessageRole
)

# Callbacks
from .callbacks import (
    BaseCallback,
    CallbackHandler,
    ConsoleCallback,
    FileCallback,
    MetricsCallback
)

# Exceptions
from .exceptions import (
    ORAFError,
    AgentError,
    AgentConfigurationError,
    AgentExecutionError,
    ToolError,
    ToolNotFoundError,
    ToolExecutionError,
    ToolValidationError,
    MCPError,
    MCPServerError,
    MCPConnectionError,
    MCPToolError,
    WorkflowError,
    InvalidNodeError,
    InvalidEdgeError,
    CycleDetectedError,
    WorkflowExecutionError,
    A2AError,
    A2AMessageError,
    A2ARoutingError,
    CallbackError,
    CallbackExecutionError
)

# Utils
from .utils import default_logger, get_logger, set_log_level, LogLevel

__version__ = "0.4.0"
__author__ = "OR-AF Framework Team"

__all__ = [
    # Core classes
    "Agent",
    "Tool",
    
    # MCP Server (official SDK wrappers)
    "MCPServer",
    "MCPClient",
    "MCPServerStatus",
    "create_mcp_server",
    "connect_mcp_server",
    
    # Workflow
    "WorkflowGraph",
    "Sequential",
    "Parallel",
    "Node",
    "ConditionalEdge",
    "EdgeCondition",
    "NodeStatus",
    "NodeResult",
    "workflow",
    "WorkflowVisualizer",
    "visualize_workflow",
    
    # A2A Protocol (official SDK wrappers)
    "A2AAgent",
    "A2AAgentStatus",
    "BaseA2AExecutor",
    "SimpleA2AExecutor",
    "AgentCard",
    "AgentCapabilities",
    "AgentSkill",
    "new_agent_text_message",
    "create_a2a_agent",
    
    # Models
    "AgentConfig",
    "AgentResponse",
    "AgentEvent",
    "EventType",
    "ToolCall",
    "ToolResult",
    "ToolSchema",
    "IterationState",
    "Message",
    "MessageRole",
    
    # Callbacks
    "BaseCallback",
    "CallbackHandler",
    "ConsoleCallback",
    "FileCallback",
    "MetricsCallback",
    
    # Exceptions
    "ORAFError",
    "AgentError",
    "AgentConfigurationError",
    "AgentExecutionError",
    "ToolError",
    "ToolNotFoundError",
    "ToolExecutionError",
    "ToolValidationError",
    "MCPError",
    "MCPServerError",
    "MCPConnectionError",
    "MCPToolError",
    "WorkflowError",
    "InvalidNodeError",
    "InvalidEdgeError",
    "CycleDetectedError",
    "WorkflowExecutionError",
    "A2AError",
    "A2AMessageError",
    "A2ARoutingError",
    "CallbackError",
    "CallbackExecutionError",
    
    # Utils
    "default_logger",
    "get_logger",
    "set_log_level",
    "LogLevel",
]
