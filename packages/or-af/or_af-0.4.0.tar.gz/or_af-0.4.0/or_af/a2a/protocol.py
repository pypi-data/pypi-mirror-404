"""
OR-AF A2A Module - Wrapper around official A2A SDK

This module provides a simplified interface to the official Agent2Agent (A2A) Protocol SDK
from https://a2a-protocol.org/

The A2A Protocol enables seamless communication between AI agents built with different
frameworks (LangGraph, CrewAI, OR-AF, etc.).
"""

from typing import Callable, Dict, List, Any, Optional, AsyncIterator
from datetime import datetime
from enum import Enum
import uuid
import asyncio
from abc import ABC, abstractmethod

# Import from official A2A SDK
from a2a.types import (
    AgentCard,
    AgentCapabilities,
    AgentSkill,
    Message,
    Part,
    TextPart,
    Task,
    TaskState,
)
from a2a.server.agent_execution import AgentExecutor
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.utils import new_agent_text_message

from ..exceptions import A2AError
from ..utils.logger import default_logger


class A2AAgentStatus(str, Enum):
    """Status of an A2A Agent"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class BaseA2AExecutor(AgentExecutor):
    """
    Base class for A2A Agent Executors.
    
    Extend this class to implement your agent's logic.
    
    Example:
        ```python
        from or_af.a2a import BaseA2AExecutor, A2AAgent, new_agent_text_message
        
        class MyAgentExecutor(BaseA2AExecutor):
            async def execute(self, context, event_queue):
                # Get user's message
                user_message = self.get_user_message(context)
                
                # Process and respond
                response = f"You said: {user_message}"
                await event_queue.enqueue_event(new_agent_text_message(response))
            
            async def cancel(self, context, event_queue):
                raise Exception("Cancel not supported")
        ```
    """
    
    def get_user_message(self, context) -> str:
        """
        Extract the user's text message from the request context.
        
        Args:
            context: The RequestContext from A2A
        
        Returns:
            The user's message as a string
        """
        if context.message and context.message.parts:
            for part in context.message.parts:
                if hasattr(part, 'root') and hasattr(part.root, 'text'):
                    return part.root.text
                elif hasattr(part, 'text'):
                    return part.text
        return ""
    
    @abstractmethod
    async def execute(self, context, event_queue: EventQueue) -> None:
        """
        Handle incoming requests. Implement this in your subclass.
        
        Args:
            context: RequestContext with message and task info
            event_queue: EventQueue to send responses back
        """
        pass
    
    @abstractmethod
    async def cancel(self, context, event_queue: EventQueue) -> None:
        """
        Handle cancellation requests. Implement this in your subclass.
        
        Args:
            context: RequestContext with task info
            event_queue: EventQueue for responses
        """
        pass


class SimpleA2AExecutor(BaseA2AExecutor):
    """
    A simple A2A executor that wraps a callable function.
    
    Example:
        ```python
        async def my_handler(message: str) -> str:
            return f"Echo: {message}"
        
        executor = SimpleA2AExecutor(my_handler)
        ```
    """
    
    def __init__(self, handler: Callable[[str], Any]):
        """
        Initialize with a handler function.
        
        Args:
            handler: A function that takes a message string and returns a response.
                     Can be sync or async.
        """
        self.handler = handler
    
    async def execute(self, context, event_queue: EventQueue) -> None:
        """Execute the handler with the user's message."""
        user_message = self.get_user_message(context)
        
        # Call handler (support both sync and async)
        if asyncio.iscoroutinefunction(self.handler):
            result = await self.handler(user_message)
        else:
            result = self.handler(user_message)
        
        # Send response
        await event_queue.enqueue_event(new_agent_text_message(str(result)))
    
    async def cancel(self, context, event_queue: EventQueue) -> None:
        """Cancel is not supported by default."""
        raise Exception("Cancel not supported")


class A2AAgent:
    """
    A2A Agent - Wrapper around official A2A SDK.
    
    This class provides a simplified interface to create A2A-compliant agents
    using the official A2A Python SDK from https://a2a-protocol.org/
    
    Example:
        ```python
        from or_af.a2a import A2AAgent, SimpleA2AExecutor
        
        # Define your agent's logic
        async def handle_message(message: str) -> str:
            return f"Hello! You said: {message}"
        
        # Create the agent
        agent = A2AAgent(
            name="My Agent",
            description="A friendly greeting agent",
            skills=[{
                "id": "greet",
                "name": "Greeting",
                "description": "Greets the user",
                "tags": ["greeting", "hello"]
            }]
        )
        
        # Set the executor
        agent.set_executor(SimpleA2AExecutor(handle_message))
        
        # Run the agent server
        agent.run(port=9999)
        ```
    """
    
    def __init__(
        self,
        name: str,
        description: str = "",
        version: str = "1.0.0",
        url: str = "http://localhost:9999/",
        skills: Optional[List[Dict[str, Any]]] = None,
        capabilities: Optional[Dict[str, bool]] = None,
        input_modes: Optional[List[str]] = None,
        output_modes: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize A2A Agent.
        
        Args:
            name: Agent name
            description: Agent description
            version: Agent version
            url: Base URL for the agent server
            skills: List of skill definitions (dicts with id, name, description, tags)
            capabilities: Agent capabilities (streaming, pushNotifications, etc.)
            input_modes: Supported input MIME types (default: ["text"])
            output_modes: Supported output MIME types (default: ["text"])
            **kwargs: Additional AgentCard parameters
        """
        self.agent_id = str(uuid.uuid4())
        self.name = name
        self.description = description or f"A2A Agent: {name}"
        self.version = version
        self.url = url
        
        self.status = A2AAgentStatus.STOPPED
        self.logger = default_logger
        
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        
        # Build skills
        self._skills: List[AgentSkill] = []
        if skills:
            for skill_def in skills:
                self._skills.append(AgentSkill(
                    id=skill_def.get("id", str(uuid.uuid4())),
                    name=skill_def.get("name", "Unnamed Skill"),
                    description=skill_def.get("description", ""),
                    tags=skill_def.get("tags", []),
                    examples=skill_def.get("examples", []),
                    inputModes=skill_def.get("inputModes", ["text"]),
                    outputModes=skill_def.get("outputModes", ["text"]),
                ))
        
        # Build capabilities
        self._capabilities = AgentCapabilities(
            streaming=capabilities.get("streaming", True) if capabilities else True,
            pushNotifications=capabilities.get("pushNotifications", False) if capabilities else False,
        )
        
        # Build agent card
        self._agent_card = AgentCard(
            name=name,
            description=description,
            url=url,
            version=version,
            defaultInputModes=input_modes or ["text"],
            defaultOutputModes=output_modes or ["text"],
            capabilities=self._capabilities,
            skills=self._skills,
            **kwargs
        )
        
        self._executor: Optional[AgentExecutor] = None
        self._request_handler: Optional[DefaultRequestHandler] = None
        
        self.logger.info(f"A2A Agent '{name}' initialized (using official A2A SDK)")
    
    @property
    def agent_card(self) -> AgentCard:
        """Get the agent's card (discovery information)."""
        return self._agent_card
    
    @property
    def card(self) -> AgentCard:
        """Alias for agent_card - get the agent's card (discovery information)."""
        return self._agent_card
    
    @property
    def skills(self) -> List[AgentSkill]:
        """Get the agent's skills."""
        return self._skills
    
    def add_skill(
        self,
        skill_id: str,
        name: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        examples: Optional[List[str]] = None,
        **kwargs
    ) -> None:
        """
        Add a skill to the agent.
        
        Args:
            skill_id: Unique skill identifier
            name: Skill name
            description: Skill description
            tags: Keywords for discovery
            examples: Example prompts
            **kwargs: Additional AgentSkill parameters
        """
        skill = AgentSkill(
            id=skill_id,
            name=name,
            description=description,
            tags=tags or [],
            examples=examples or [],
            **kwargs
        )
        self._skills.append(skill)
        self._agent_card.skills = self._skills
        
        self.logger.info(f"Skill '{name}' added to A2A Agent '{self.name}'")
    
    def set_executor(self, executor: AgentExecutor) -> None:
        """
        Set the agent executor that handles requests.
        
        Args:
            executor: An AgentExecutor implementation
        
        Example:
            ```python
            agent.set_executor(SimpleA2AExecutor(my_handler))
            ```
        """
        self._executor = executor
        self.logger.info(f"Executor set for A2A Agent '{self.name}'")
    
    def set_handler(self, handler: Callable[[str], Any]) -> None:
        """
        Convenience method to set a simple handler function.
        
        Args:
            handler: A function that takes a message and returns a response
        
        Example:
            ```python
            agent.set_handler(lambda msg: f"Echo: {msg}")
            ```
        """
        self.set_executor(SimpleA2AExecutor(handler))
    
    def run(
        self,
        host: str = "0.0.0.0",
        port: int = 9999,
        **kwargs
    ) -> None:
        """
        Run the A2A agent server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            **kwargs: Additional server parameters
        
        Example:
            ```python
            agent.run(port=9999)
            ```
        """
        if not self._executor:
            raise A2AError("No executor set. Call set_executor() or set_handler() first.")
        
        self.status = A2AAgentStatus.STARTING
        self.started_at = datetime.now()
        
        # Update URL with actual port
        self._agent_card.url = f"http://{host}:{port}/"
        
        self.logger.info(f"Starting A2A Agent '{self.name}' on {host}:{port}")
        
        try:
            # Import here to avoid circular imports
            from a2a.server.apps import A2AStarletteApplication
            
            # Create request handler
            task_store = InMemoryTaskStore()
            self._request_handler = DefaultRequestHandler(
                agent_executor=self._executor,
                task_store=task_store,
            )
            
            # Create and run application
            app = A2AStarletteApplication(
                agent_card=self._agent_card,
                http_handler=self._request_handler,
            )
            
            import uvicorn
            self.status = A2AAgentStatus.RUNNING
            uvicorn.run(app.build(), host=host, port=port, **kwargs)
            
        except Exception as e:
            self.status = A2AAgentStatus.ERROR
            self.logger.error(f"Failed to start A2A Agent: {e}")
            raise A2AError(f"Failed to start A2A Agent '{self.name}': {e}")
    
    def get_starlette_app(self):
        """
        Get the Starlette application for mounting.
        
        Returns:
            Starlette application
        
        Example:
            ```python
            from starlette.applications import Starlette
            from starlette.routing import Mount
            
            app = Starlette(routes=[
                Mount("/agent", app=agent.get_starlette_app()),
            ])
            ```
        """
        if not self._executor:
            raise A2AError("No executor set. Call set_executor() or set_handler() first.")
        
        from a2a.server.apps import A2AStarletteApplication
        
        task_store = InMemoryTaskStore()
        self._request_handler = DefaultRequestHandler(
            agent_executor=self._executor,
            task_store=task_store,
        )
        
        app = A2AStarletteApplication(
            agent_card=self._agent_card,
            http_handler=self._request_handler,
        )
        
        return app.build()
    
    def __repr__(self) -> str:
        return (
            f"A2AAgent(name='{self.name}', "
            f"skills={len(self._skills)}, "
            f"status={self.status.value})"
        )


# Re-export useful types from official SDK
__all__ = [
    "A2AAgent",
    "A2AAgentStatus",
    "BaseA2AExecutor",
    "SimpleA2AExecutor",
    "AgentCard",
    "AgentCapabilities",
    "AgentSkill",
    "new_agent_text_message",
]


# Convenience function for creating A2A agents (TensorFlow-like API)
def create_a2a_agent(
    name: str,
    description: str = "",
    handler: Optional[Callable[[str], Any]] = None,
    **kwargs
) -> A2AAgent:
    """
    Create an A2A agent using the official A2A SDK.
    
    Args:
        name: Agent name
        description: Agent description
        handler: Optional handler function
        **kwargs: Additional arguments
    
    Returns:
        A2AAgent instance
    
    Example:
        ```python
        agent = create_a2a_agent(
            "greeter",
            "A greeting agent",
            handler=lambda msg: f"Hello! {msg}"
        )
        agent.run(port=9999)
        ```
    """
    agent = A2AAgent(name=name, description=description, **kwargs)
    if handler:
        agent.set_handler(handler)
    return agent
