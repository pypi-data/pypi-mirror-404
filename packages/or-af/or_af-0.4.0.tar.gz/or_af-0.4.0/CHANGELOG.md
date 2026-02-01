# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-01-31

### Added
- **Official MCP SDK Integration**: Now uses the official MCP Python SDK (`mcp[cli]>=1.2.0`) from https://modelcontextprotocol.io/
- **Official A2A SDK Integration**: Now uses the official A2A Python SDK (`a2a-sdk[http-server]>=0.3.0`) from https://a2a-protocol.org/
- `MCPServer` wrapper around official `FastMCP` with `@server.tool()`, `@server.resource()`, `@server.prompt()` decorators
- `MCPClient` for connecting to external MCP servers via stdio or HTTP transports
- `A2AAgent` wrapper around official A2A SDK with `AgentCard`, `AgentSkill`, `AgentCapabilities`
- `SimpleA2AExecutor` and `BaseA2AExecutor` for implementing A2A agent logic
- Convenience functions: `create_mcp_server()`, `create_a2a_agent()`, `connect_mcp_server()`
- Backwards compatibility layer (`A2AProtocol`, `A2AMessage`, `MessageType`) for existing workflow code

### Changed
- **Breaking**: Requires Python 3.10+ (was 3.8+) due to official SDK requirements
- MCP Server now supports all official MCP SDK features (streaming, HTTP transport, resources, prompts)
- A2A Agent now fully compatible with the A2A ecosystem

### Dependencies
- Added `mcp[cli]>=1.2.0` - Official MCP SDK
- Added `a2a-sdk[http-server]>=0.3.0` - Official A2A SDK  
- Added `httpx>=0.23.0` - HTTP client for MCP/A2A connections

## [0.3.0] - 2026-01-31

### Added
- Restructured into folders following SOLID principles
- MCP Server and Client modules
- Workflow graph with visualization (text, ASCII, Mermaid)
- TensorFlow-like API (`Sequential`, `Parallel`, `workflow()`)
- A2A protocol for agent-to-agent communication

### Changed
- Tools are now only registered with MCP servers
- Agents connect to MCP servers via `mcp_servers=[...]` parameter

## [0.1.0] - 2026-01-31

### Added
- Initial release of OR-AF
- Tool support with automatic schema generation
- Full observability with custom callbacks
- Streaming responses
- Comprehensive logging (console and file)
- Type safety with Pydantic
- Error handling with custom exceptions
- Execution metrics and performance tracking
- Example scripts and Jupyter notebook

### Features
- `Agent` class for creating AI agents
- `Tool` decorator for easy tool registration
- Custom callback system for monitoring
- Logger with colored output
- Exception handling framework
- Model abstractions for OpenAI integration

[0.4.0]: https://github.com/yourusername/or-af/releases/tag/v0.4.0
[0.3.0]: https://github.com/yourusername/or-af/releases/tag/v0.3.0
[0.1.0]: https://github.com/yourusername/or-af/releases/tag/v0.1.0
