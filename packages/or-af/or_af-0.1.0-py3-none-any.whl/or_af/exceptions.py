"""
Custom exceptions for the Agentic Framework
"""


class AgenticFrameworkError(Exception):
    """Base exception for all framework errors"""
    pass


class ToolNotFoundError(AgenticFrameworkError):
    """Raised when a requested tool is not found"""
    pass


class ToolExecutionError(AgenticFrameworkError):
    """Raised when tool execution fails"""
    pass


class MaxIterationsReachedError(AgenticFrameworkError):
    """Raised when maximum iterations are reached"""
    pass


class InvalidConfigurationError(AgenticFrameworkError):
    """Raised when configuration is invalid"""
    pass


class OpenAIError(AgenticFrameworkError):
    """Raised when OpenAI API call fails"""
    pass
