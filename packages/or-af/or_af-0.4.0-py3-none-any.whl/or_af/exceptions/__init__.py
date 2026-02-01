"""
OR-AF Exceptions

Custom exception classes for the framework.
"""


class ORAFError(Exception):
    """Base exception for OR-AF framework"""
    pass


# Agent Exceptions
class AgentError(ORAFError):
    """Base exception for agent errors"""
    pass


class AgentConfigurationError(AgentError):
    """Error in agent configuration"""
    pass


class AgentExecutionError(AgentError):
    """Error during agent execution"""
    pass


# Tool Exceptions
class ToolError(ORAFError):
    """Base exception for tool errors"""
    pass


class ToolNotFoundError(ToolError):
    """Tool not found"""
    pass


class ToolExecutionError(ToolError):
    """Error during tool execution"""
    pass


class ToolValidationError(ToolError):
    """Error validating tool parameters"""
    pass


# MCP Exceptions
class MCPError(ORAFError):
    """Base exception for MCP errors"""
    pass


class MCPServerError(MCPError):
    """Error with MCP server"""
    pass


class MCPConnectionError(MCPError):
    """Error connecting to MCP server"""
    pass


class MCPToolError(MCPError):
    """Error executing MCP tool"""
    pass


# Workflow Exceptions
class WorkflowError(ORAFError):
    """Base exception for workflow errors"""
    pass


class InvalidNodeError(WorkflowError):
    """Invalid node in workflow"""
    pass


class InvalidEdgeError(WorkflowError):
    """Invalid edge in workflow"""
    pass


class CycleDetectedError(WorkflowError):
    """Cycle detected in workflow graph"""
    pass


class WorkflowExecutionError(WorkflowError):
    """Error during workflow execution"""
    pass


# A2A Exceptions
class A2AError(ORAFError):
    """Base exception for A2A protocol errors"""
    pass


class A2AMessageError(A2AError):
    """Error with A2A message"""
    pass


class A2ARoutingError(A2AError):
    """Error routing A2A message"""
    pass


# Callback Exceptions
class CallbackError(ORAFError):
    """Base exception for callback errors"""
    pass


class CallbackExecutionError(CallbackError):
    """Error executing callback"""
    pass
