"""
OR-AF MCP Module

Wrapper around the official MCP SDK from https://modelcontextprotocol.io/

This module provides:
- MCPServer: Create MCP servers with tools, resources, and prompts
- MCPClient: Connect to MCP servers via stdio or HTTP
- create_mcp_server: Convenience function to create servers
- connect_mcp_server: Convenience function to connect to servers
"""

from .server import MCPServer, MCPServerStatus, create_mcp_server
from .client import MCPClient, connect_mcp_server

__all__ = [
    "MCPServer",
    "MCPClient",
    "MCPServerStatus",
    "create_mcp_server",
    "connect_mcp_server",
]
