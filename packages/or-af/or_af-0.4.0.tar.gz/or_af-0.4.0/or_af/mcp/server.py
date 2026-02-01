"""
OR-AF MCP Module - Wrapper around official MCP SDK

This module provides a simplified interface to the official Model Context Protocol SDK
from https://modelcontextprotocol.io/
"""

from typing import Callable, Dict, List, Any, Optional, TypeVar
from datetime import datetime
from enum import Enum
import uuid

# Import from official MCP SDK
from mcp.server import FastMCP

from ..models.tool_models import ToolResult
from ..exceptions import MCPServerError, ToolNotFoundError
from ..utils.logger import default_logger

T = TypeVar('T')


class MCPServerStatus(str, Enum):
    """Status of an MCP Server"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class MCPServer:
    """
    MCP (Model Context Protocol) Server - Wrapper around official MCP SDK.
    
    This class provides a simplified interface to create MCP servers using
    the official MCP Python SDK from https://modelcontextprotocol.io/
    
    Tools are registered using decorators, following the official MCP pattern.
    
    Example:
        ```python
        from or_af import MCPServer
        
        # Create server using official MCP SDK
        server = MCPServer("calculator")
        
        @server.tool()
        def add(a: int, b: int) -> int:
            '''Add two numbers'''
            return a + b
        
        @server.resource("greeting://{name}")
        def get_greeting(name: str) -> str:
            '''Get a personalized greeting'''
            return f"Hello, {name}!"
        
        # Run server
        server.run()  # Uses stdio transport by default
        ```
    """
    
    def __init__(
        self,
        name: str,
        description: str = "",
        website_url: Optional[str] = None,
        instructions: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize MCP Server wrapping official MCP SDK.
        
        Args:
            name: Server name
            description: Server description
            website_url: Optional website URL for the server
            instructions: Optional instructions for the server
            **kwargs: Additional arguments passed to official MCPServer
        """
        self.server_id = str(uuid.uuid4())
        self.name = name
        self.description = description or f"MCP Server: {name}"
        
        # Create the official MCP server (FastMCP)
        self._mcp = FastMCP(
            name=name,
            instructions=instructions or description,
            **kwargs
        )
        
        self.status = MCPServerStatus.STOPPED
        self.logger = default_logger
        
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        
        # Track registered tools and resources for introspection
        self._registered_tools: Dict[str, Dict[str, Any]] = {}
        self._registered_resources: Dict[str, Dict[str, Any]] = {}
        self._registered_prompts: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info(f"MCP Server '{name}' initialized (using official MCP SDK)")
    
    @property
    def mcp(self) -> FastMCP:
        """Access the underlying official MCP server instance."""
        return self._mcp
    
    def tool(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ) -> Callable:
        """
        Decorator to register a function as an MCP tool.
        
        This wraps the official MCP SDK's @mcp.tool() decorator.
        
        Args:
            name: Optional tool name (defaults to function name)
            description: Optional tool description (defaults to docstring)
            **kwargs: Additional arguments for the official tool decorator
        
        Example:
            ```python
            @server.tool()
            def calculate(expression: str) -> float:
                '''Evaluate a mathematical expression'''
                return eval(expression)
            
            @server.tool(name="weather", description="Get weather data")
            async def get_weather(city: str) -> dict:
                return {"city": city, "temp": 22.5}
            ```
        """
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            tool_desc = description or func.__doc__ or "No description"
            
            # Register with official MCP SDK
            decorated = self._mcp.tool(name=tool_name, description=tool_desc, **kwargs)(func)
            
            # Track for introspection
            self._registered_tools[tool_name] = {
                "name": tool_name,
                "description": tool_desc,
                "function": func,
                "registered_at": datetime.now()
            }
            
            self.logger.info(f"Tool '{tool_name}' registered with MCP server '{self.name}'")
            return decorated
        
        return decorator
    
    def resource(
        self,
        uri_template: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ) -> Callable:
        """
        Decorator to register a function as an MCP resource.
        
        Resources expose data to LLMs (like GET endpoints in REST APIs).
        
        Args:
            uri_template: URI template for the resource (e.g., "file://{path}")
            name: Optional resource name
            description: Optional description
            **kwargs: Additional arguments for the official resource decorator
        
        Example:
            ```python
            @server.resource("config://settings")
            def get_settings() -> str:
                return '{"theme": "dark", "lang": "en"}'
            
            @server.resource("file://documents/{name}")
            def read_document(name: str) -> str:
                return f"Content of {name}"
            ```
        """
        def decorator(func: Callable) -> Callable:
            resource_name = name or func.__name__
            resource_desc = description or func.__doc__ or "No description"
            
            # Register with official MCP SDK
            decorated = self._mcp.resource(uri_template, name=resource_name, description=resource_desc, **kwargs)(func)
            
            # Track for introspection
            self._registered_resources[uri_template] = {
                "uri_template": uri_template,
                "name": resource_name,
                "description": resource_desc,
                "function": func,
                "registered_at": datetime.now()
            }
            
            self.logger.info(f"Resource '{uri_template}' registered with MCP server '{self.name}'")
            return decorated
        
        return decorator
    
    def prompt(
        self,
        name: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ) -> Callable:
        """
        Decorator to register a function as an MCP prompt.
        
        Prompts are reusable templates for LLM interactions.
        
        Args:
            name: Optional prompt name
            title: Optional title for display
            description: Optional description
            **kwargs: Additional arguments for the official prompt decorator
        
        Example:
            ```python
            @server.prompt(title="Code Review")
            def review_code(code: str) -> str:
                return f"Please review this code:\\n\\n{code}"
            ```
        """
        def decorator(func: Callable) -> Callable:
            prompt_name = name or func.__name__
            prompt_title = title or prompt_name
            prompt_desc = description or func.__doc__ or "No description"
            
            # Register with official MCP SDK
            decorated = self._mcp.prompt(name=prompt_name, title=prompt_title, description=prompt_desc, **kwargs)(func)
            
            # Track for introspection
            self._registered_prompts[prompt_name] = {
                "name": prompt_name,
                "title": prompt_title,
                "description": prompt_desc,
                "function": func,
                "registered_at": datetime.now()
            }
            
            self.logger.info(f"Prompt '{prompt_name}' registered with MCP server '{self.name}'")
            return decorated
        
        return decorator
    
    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._registered_tools.keys())
    
    def list_resources(self) -> List[str]:
        """List all registered resource URI templates."""
        return list(self._registered_resources.keys())
    
    def list_prompts(self) -> List[str]:
        """List all registered prompt names."""
        return list(self._registered_prompts.keys())
    
    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a registered tool."""
        return self._registered_tools.get(name)
    
    def run(
        self,
        transport: str = "stdio",
        host: str = "localhost",
        port: int = 8000,
        **kwargs
    ) -> None:
        """
        Run the MCP server.
        
        Args:
            transport: Transport type - "stdio", "streamable-http", or "sse"
            host: Host for HTTP transports
            port: Port for HTTP transports
            **kwargs: Additional arguments for the run method
        
        Example:
            ```python
            # Run with stdio (for Claude Desktop)
            server.run()
            
            # Run with HTTP transport
            server.run(transport="streamable-http", port=8000)
            ```
        """
        self.status = MCPServerStatus.STARTING
        self.started_at = datetime.now()
        
        self.logger.info(f"Starting MCP server '{self.name}' with transport '{transport}'")
        
        try:
            if transport == "streamable-http":
                self._mcp.run(transport=transport, host=host, port=port, **kwargs)
            else:
                self._mcp.run(transport=transport, **kwargs)
            
            self.status = MCPServerStatus.RUNNING
        except Exception as e:
            self.status = MCPServerStatus.ERROR
            self.logger.error(f"Failed to start MCP server: {e}")
            raise MCPServerError(f"Failed to start MCP server '{self.name}': {e}")
    
    def streamable_http_app(self, **kwargs):
        """
        Get a Starlette/ASGI app for mounting the MCP server.
        
        This allows mounting the MCP server in an existing ASGI application.
        
        Args:
            **kwargs: Arguments passed to the official streamable_http_app method
        
        Returns:
            ASGI application
        
        Example:
            ```python
            from starlette.applications import Starlette
            from starlette.routing import Mount
            
            app = Starlette(
                routes=[
                    Mount("/mcp", app=server.streamable_http_app()),
                ]
            )
            ```
        """
        return self._mcp.streamable_http_app(**kwargs)
    
    def sse_app(self, **kwargs):
        """
        Get an SSE ASGI app for mounting the MCP server.
        
        Args:
            **kwargs: Arguments passed to the official sse_app method
        
        Returns:
            ASGI application
        """
        return self._mcp.sse_app(**kwargs)
    
    def __repr__(self) -> str:
        return (
            f"MCPServer(name='{self.name}', "
            f"tools={len(self._registered_tools)}, "
            f"resources={len(self._registered_resources)}, "
            f"prompts={len(self._registered_prompts)}, "
            f"status={self.status.value})"
        )


# Convenience function for creating MCP servers (TensorFlow-like API)
def create_mcp_server(
    name: str,
    description: str = "",
    **kwargs
) -> MCPServer:
    """
    Create an MCP server using the official MCP SDK.
    
    This is a convenience function for creating MCP servers.
    
    Args:
        name: Server name
        description: Server description
        **kwargs: Additional arguments
    
    Returns:
        MCPServer instance
    
    Example:
        ```python
        server = create_mcp_server("my-tools", "My tool server")
        
        @server.tool()
        def hello(name: str) -> str:
            return f"Hello, {name}!"
        ```
    """
    return MCPServer(name=name, description=description, **kwargs)
