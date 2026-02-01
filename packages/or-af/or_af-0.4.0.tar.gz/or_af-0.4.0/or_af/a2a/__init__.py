"""
OR-AF A2A (Agent-to-Agent) Module

Wrapper around the official A2A SDK from https://a2a-protocol.org/

The A2A Protocol enables seamless communication between AI agents built
with different frameworks (LangGraph, CrewAI, OR-AF, etc.).

This module provides:
- A2AAgent: Create A2A-compliant agents
- BaseA2AExecutor: Base class for implementing agent logic
- SimpleA2AExecutor: Simple wrapper for handler functions
- create_a2a_agent: Convenience function to create agents
"""

from .protocol import (
    A2AAgent,
    A2AAgentStatus,
    BaseA2AExecutor,
    SimpleA2AExecutor,
    AgentCard,
    AgentCapabilities,
    AgentSkill,
    new_agent_text_message,
    create_a2a_agent,
)
from .compatibility import (
    A2AMessage,
    MessageType,
    # Alias for backwards compatibility
    A2AProtocol,
)

__all__ = [
    # New official SDK wrappers
    "A2AAgent",
    "A2AAgentStatus",
    "BaseA2AExecutor",
    "SimpleA2AExecutor",
    "AgentCard",
    "AgentCapabilities",
    "AgentSkill",
    "new_agent_text_message",
    "create_a2a_agent",
    # Backwards compatibility
    "A2AProtocol",
    "A2AMessage",
    "MessageType",
]
