"""
OR-AF MCP Client - Wrapper around official MCP SDK Client

This module provides a simplified interface to connect to MCP servers
using the official Model Context Protocol SDK.
"""

from typing import Callable, Dict, List, Any, Optional, AsyncIterator
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

# Import from official MCP SDK
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
import mcp.types as types

from ..exceptions import MCPServerError
from ..utils.logger import default_logger


class MCPClient:
    """
    MCP Client - Wrapper around official MCP SDK Client.
    
    This class provides a simplified interface to connect to MCP servers
    using the official MCP Python SDK from https://modelcontextprotocol.io/
    
    Example:
        ```python
        from or_af import MCPClient
        
        # Connect to an MCP server via stdio
        async with MCPClient.connect_stdio("uv", ["run", "server.py"]) as client:
            # List available tools
            tools = await client.list_tools()
            print(f"Available tools: {[t.name for t in tools]}")
            
            # Call a tool
            result = await client.call_tool("add", {"a": 5, "b": 3})
            print(f"Result: {result}")
        
        # Connect to an HTTP MCP server
        async with MCPClient.connect_http("http://localhost:8000/mcp") as client:
            tools = await client.list_tools()
        ```
    """
    
    def __init__(self, session: ClientSession):
        """
        Initialize MCP Client with a session.
        
        Note: Use the class methods connect_stdio() or connect_http() instead.
        
        Args:
            session: The MCP ClientSession
        """
        self._session = session
        self.logger = default_logger
        self._initialized = False
    
    @property
    def session(self) -> ClientSession:
        """Access the underlying ClientSession."""
        return self._session
    
    async def initialize(self) -> None:
        """Initialize the connection to the MCP server."""
        if not self._initialized:
            await self._session.initialize()
            self._initialized = True
            self.logger.info("MCP Client initialized")
    
    async def list_tools(self) -> List[types.Tool]:
        """
        List all available tools from the server.
        
        Returns:
            List of Tool objects
        """
        if not self._initialized:
            await self.initialize()
        
        result = await self._session.list_tools()
        return result.tools
    
    async def list_resources(self) -> List[types.Resource]:
        """
        List all available resources from the server.
        
        Returns:
            List of Resource objects
        """
        if not self._initialized:
            await self.initialize()
        
        result = await self._session.list_resources()
        return result.resources
    
    async def list_prompts(self) -> List[types.Prompt]:
        """
        List all available prompts from the server.
        
        Returns:
            List of Prompt objects
        """
        if not self._initialized:
            await self.initialize()
        
        result = await self._session.list_prompts()
        return result.prompts
    
    async def call_tool(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> types.CallToolResult:
        """
        Call a tool on the MCP server.
        
        Args:
            name: The tool name
            arguments: Optional arguments for the tool
        
        Returns:
            CallToolResult with the tool's response
        
        Example:
            ```python
            result = await client.call_tool("add", {"a": 5, "b": 3})
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(content.text)
            ```
        """
        if not self._initialized:
            await self.initialize()
        
        return await self._session.call_tool(name, arguments or {})
    
    async def read_resource(self, uri: str) -> types.ReadResourceResult:
        """
        Read a resource from the MCP server.
        
        Args:
            uri: The resource URI
        
        Returns:
            ReadResourceResult with the resource content
        """
        if not self._initialized:
            await self.initialize()
        
        return await self._session.read_resource(uri)
    
    async def get_prompt(
        self,
        name: str,
        arguments: Optional[Dict[str, str]] = None
    ) -> types.GetPromptResult:
        """
        Get a prompt from the MCP server.
        
        Args:
            name: The prompt name
            arguments: Optional arguments for the prompt
        
        Returns:
            GetPromptResult with the prompt content
        """
        if not self._initialized:
            await self.initialize()
        
        return await self._session.get_prompt(name, arguments)
    
    @classmethod
    @asynccontextmanager
    async def connect_stdio(
        cls,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> AsyncIterator["MCPClient"]:
        """
        Connect to an MCP server via stdio transport.
        
        Args:
            command: The command to run (e.g., "python", "uv")
            args: Command arguments (e.g., ["run", "server.py"])
            env: Environment variables
            **kwargs: Additional parameters for StdioServerParameters
        
        Yields:
            MCPClient instance
        
        Example:
            ```python
            async with MCPClient.connect_stdio("uv", ["run", "server.py"]) as client:
                tools = await client.list_tools()
            ```
        """
        server_params = StdioServerParameters(
            command=command,
            args=args or [],
            env=env,
            **kwargs
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                client = cls(session)
                await client.initialize()
                yield client
    
    @classmethod
    @asynccontextmanager
    async def connect_http(
        cls,
        url: str,
        **kwargs
    ) -> AsyncIterator["MCPClient"]:
        """
        Connect to an MCP server via HTTP transport.
        
        Args:
            url: The server URL (e.g., "http://localhost:8000/mcp")
            **kwargs: Additional parameters for streamable_http_client
        
        Yields:
            MCPClient instance
        
        Example:
            ```python
            async with MCPClient.connect_http("http://localhost:8000/mcp") as client:
                tools = await client.list_tools()
            ```
        """
        async with streamable_http_client(url, **kwargs) as (read, write, _):
            async with ClientSession(read, write) as session:
                client = cls(session)
                await client.initialize()
                yield client


async def connect_mcp_server(
    command: str,
    args: Optional[List[str]] = None,
    **kwargs
) -> AsyncIterator[MCPClient]:
    """
    Convenience function to connect to an MCP server via stdio.
    
    Args:
        command: The command to run
        args: Command arguments
        **kwargs: Additional parameters
    
    Yields:
        MCPClient instance
    
    Example:
        ```python
        async with connect_mcp_server("uv", ["run", "server.py"]) as client:
            result = await client.call_tool("hello", {"name": "World"})
        ```
    """
    async with MCPClient.connect_stdio(command, args, **kwargs) as client:
        yield client
