"""
OR-AF Core Module - Agent implementation
"""

import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from openai import AzureOpenAI
from dotenv import load_dotenv
import os

from ..models.agent_models import AgentConfig, AgentResponse, IterationState
from ..models.tool_models import ToolCall
from ..models.message_models import Message, MessageRole
from ..models.event_models import EventType
from ..callbacks import CallbackHandler, ConsoleCallback
from ..exceptions import (
    ToolNotFoundError, AgentExecutionError,
    AgentConfigurationError, MCPConnectionError
)
from ..utils.logger import default_logger


class Agent:
    """
    Lightweight AI Agent with MCP server support, streaming, and observability.
    
    Agents can only access tools through MCP servers. Tools cannot be added directly.
    
    Example:
        ```python
        # Create MCP server with tools
        mcp = MCPServer(name="math_tools")
        mcp.add_tool("add", add_func, "Add two numbers")
        
        # Create agent with MCP servers
        agent = Agent(
            name="math_agent",
            system_prompt="You are a math assistant",
            mcp_servers=[mcp]
        )
        
        # Run task
        result = agent.run("Calculate 5 + 3")
        ```
    """
    
    def __init__(
        self,
        system_prompt: str,
        name: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 1.0,
        max_iterations: int = 10,
        stream: bool = True,
        verbose: bool = True,
        callbacks: Optional[List] = None,
        mcp_servers: Optional[List] = None
    ):
        """
        Initialize the agent.
        
        Args:
            system_prompt: The system prompt defining agent behavior
            name: Agent name (optional, auto-generated if not provided)
            model_name: OpenAI model name (defaults to env variable)
            temperature: Sampling temperature
            max_iterations: Maximum number of iterations for task execution
            stream: Enable streaming responses
            verbose: Enable verbose output
            callbacks: List of callback objects for observability
            mcp_servers: List of MCP servers to connect to for tools
        """
        load_dotenv()
        
        self.agent_id = str(uuid.uuid4())
        self.name = name or f"agent_{self.agent_id[:8]}"
        
        try:
            self.config = AgentConfig(
                system_prompt=system_prompt,
                model_name=model_name,
                temperature=temperature,
                max_iterations=max_iterations,
                stream=stream,
                verbose=verbose
            )
        except Exception as e:
            raise AgentConfigurationError(f"Invalid configuration: {str(e)}")
        
        self.logger = default_logger
        self.conversation_history: List[Message] = []
        
        self._mcp_servers: Dict[str, Any] = {}
        self._mcp_clients: Dict[str, Any] = {}
        
        if mcp_servers:
            for server in mcp_servers:
                self.connect_mcp(server)
        
        # Setup callback handler
        self.callback_handler = CallbackHandler()
        if verbose:
            self.callback_handler.register_global(
                lambda e: ConsoleCallback(verbose=True).on_event(e)
            )
        
        try:
            self.client = AzureOpenAI(
                api_key=os.getenv("subscription_key"),
                api_version=os.getenv("api_version"),
                azure_endpoint=os.getenv("endpoint")
            )
            self.model_name = model_name or os.getenv("deployment", "gpt-4")
            self.logger.info(f"Agent '{self.name}' initialized with model: {self.model_name}")
        except Exception as e:
            raise AgentExecutionError(f"Failed to initialize OpenAI client: {str(e)}")
    
    def connect_mcp(self, server: Any) -> "Agent":
        """Connect to an MCP server."""
        from ..mcp import MCPServer
        
        if not isinstance(server, MCPServer):
            raise AgentConfigurationError("Expected an MCPServer instance")
        
        # For local MCP servers, we directly reference the server
        # The server already contains the tools and can execute them
        self._mcp_servers[server.name] = server
        
        self.logger.info(f"Agent '{self.name}' connected to MCP server '{server.name}'")
        
        if self.config.verbose:
            tool_count = len(server._registered_tools)
            print(f"✓ Connected to MCP server '{server.name}' ({tool_count} tools)")
        
        return self
    
    def disconnect_mcp(self, server_name: str) -> bool:
        """Disconnect from an MCP server."""
        if server_name in self._mcp_servers:
            del self._mcp_servers[server_name]
            if server_name in self._mcp_clients:
                del self._mcp_clients[server_name]
            self.logger.info(f"Disconnected from MCP server '{server_name}'")
            return True
        return False
    
    def list_mcp_servers(self) -> List[str]:
        """List connected MCP server names."""
        return list(self._mcp_servers.keys())
    
    def list_available_tools(self) -> Dict[str, List[str]]:
        """List all available tools from connected MCP servers."""
        tools = {}
        for name, server in self._mcp_servers.items():
            tools[name] = server.list_tools()
        return tools
    
    def _get_tools_schema(self) -> List[Dict[str, Any]]:
        """Get all tools in OpenAI format from connected MCP servers."""
        schemas = []
        for client in self._mcp_clients.values():
            schemas.extend(client.get_tools())
        return schemas
    
    def _find_tool_server(self, tool_name: str) -> Optional[str]:
        """Find which MCP server has a specific tool."""
        for server_name, server in self._mcp_servers.items():
            if tool_name in server.tools:
                return server_name
        return None
    
    def _execute_tool_call(self, tool_call) -> str:
        """Execute a tool call via MCP server and return the result."""
        tool_name = tool_call.function.name
        
        try:
            arguments = json.loads(tool_call.function.arguments)
            
            tracked_call = ToolCall(
                id=tool_call.id,
                name=tool_name,
                arguments=arguments
            )
            
            self.callback_handler.emit(
                EventType.TOOL_CALL_START,
                tool_name=tool_name,
                arguments=arguments
            )
            
            server_name = self._find_tool_server(tool_name)
            if not server_name:
                error_msg = f"Tool '{tool_name}' not found in any connected MCP server"
                self.callback_handler.emit(EventType.TOOL_ERROR, tool_name=tool_name, error=error_msg)
                raise ToolNotFoundError(error_msg)
            
            client = self._mcp_clients[server_name]
            tool_result = client.execute_tool(tool_name, tool_call.id, **arguments)
            
            self.callback_handler.emit(
                EventType.TOOL_CALL_END,
                tool_name=tool_name,
                result=tool_result.result,
                execution_time=tool_result.execution_time
            )
            
            if tool_result.success:
                return str(tool_result.result)
            else:
                return tool_result.error
        
        except Exception as e:
            error_msg = f"Error executing {tool_name}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.callback_handler.emit(EventType.TOOL_ERROR, tool_name=tool_name, error=str(e))
            return error_msg
    
    def _stream_response(self, messages: List[Dict], iteration: int) -> tuple[str, Any]:
        """Stream response from OpenAI."""
        api_params = {
            "model": self.model_name,
            "messages": messages,
            "stream": True
        }
        
        if self.config.temperature != 1.0:
            api_params["temperature"] = self.config.temperature
        
        tools_schema = self._get_tools_schema()
        if tools_schema:
            api_params["tools"] = tools_schema
            api_params["tool_choice"] = "auto"
        
        try:
            stream = self.client.chat.completions.create(**api_params)
            
            collected_messages = []
            collected_tool_calls = []
            
            for chunk in stream:
                if not chunk.choices:
                    continue
                
                delta = chunk.choices[0].delta
                
                if delta.content:
                    collected_messages.append(delta.content)
                    self.callback_handler.emit(EventType.STREAM_CHUNK, chunk=delta.content)
                
                if delta.tool_calls:
                    for tool_call_chunk in delta.tool_calls:
                        while len(collected_tool_calls) <= tool_call_chunk.index:
                            collected_tool_calls.append({
                                "id": "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""}
                            })
                        
                        if tool_call_chunk.id:
                            collected_tool_calls[tool_call_chunk.index]["id"] = tool_call_chunk.id
                        
                        if tool_call_chunk.function.name:
                            collected_tool_calls[tool_call_chunk.index]["function"]["name"] = tool_call_chunk.function.name
                        
                        if tool_call_chunk.function.arguments:
                            collected_tool_calls[tool_call_chunk.index]["function"]["arguments"] += tool_call_chunk.function.arguments
            
            content = "".join(collected_messages) if collected_messages else None
            
            class MockMessage:
                def __init__(self, content, tool_calls):
                    self.content = content
                    self.tool_calls = None
                    if tool_calls:
                        class MockToolCall:
                            def __init__(self, tc):
                                self.id = tc["id"]
                                self.type = tc["type"]
                                class MockFunction:
                                    def __init__(self, func):
                                        self.name = func["name"]
                                        self.arguments = func["arguments"]
                                self.function = MockFunction(tc["function"])
                        
                        self.tool_calls = [MockToolCall(tc) for tc in tool_calls]
            
            assistant_message = MockMessage(content, collected_tool_calls if collected_tool_calls else None)
            
            return content or "", assistant_message
            
        except Exception as e:
            raise OpenAIError(f"OpenAI API error: {str(e)}")
    
    def _non_stream_response(self, messages: List[Dict]) -> Any:
        """Get non-streaming response from OpenAI."""
        api_params = {
            "model": self.model_name,
            "messages": messages
        }
        
        if self.config.temperature != 1.0:
            api_params["temperature"] = self.config.temperature
        
        tools_schema = self._get_tools_schema()
        if tools_schema:
            api_params["tools"] = tools_schema
            api_params["tool_choice"] = "auto"
        
        try:
            response = self.client.chat.completions.create(**api_params)
            return response.choices[0].message
        except Exception as e:
            raise AgentExecutionError(f"OpenAI API error: {str(e)}")
    
    def run(self, task: str, stream: Optional[bool] = None) -> AgentResponse:
        """
        Run a task using the agent.
        
        Args:
            task: The task/prompt for the agent
            stream: Override default streaming setting
            
        Returns:
            AgentResponse with complete execution details
        """
        start_time = datetime.now()
        use_stream = stream if stream is not None else self.config.stream
        
        self.callback_handler.emit(EventType.AGENT_START, task=task)
        self.logger.info(f"Agent started with task: {task}")
        
        messages = [
            {"role": "system", "content": self.config.system_prompt},
            {"role": "user", "content": task}
        ]
        
        iterations: List[IterationState] = []
        iteration = 0
        final_response = ""
        success = False
        error_message = None
        
        try:
            while iteration < self.config.max_iterations:
                iteration += 1
                iter_start = datetime.now()
                
                self.callback_handler.emit(EventType.ITERATION_START, iteration=iteration)
                self.logger.debug(f"Starting iteration {iteration}")
                
                iteration_state = IterationState(
                    iteration_number=iteration,
                    start_time=iter_start
                )
                
                if use_stream:
                    content, assistant_message = self._stream_response(messages, iteration)
                else:
                    assistant_message = self._non_stream_response(messages)
                    content = assistant_message.content or ""
                
                if content and not assistant_message.tool_calls:
                    iteration_state.thinking = content
                    self.callback_handler.emit(EventType.THINKING, iteration=iteration, content=content)
                
                msg_dict = {"role": "assistant"}
                if assistant_message.content:
                    msg_dict["content"] = assistant_message.content
                if assistant_message.tool_calls:
                    msg_dict["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in assistant_message.tool_calls
                    ]
                messages.append(msg_dict)
                
                if assistant_message.tool_calls:
                    self.logger.info(f"Agent requested {len(assistant_message.tool_calls)} tool(s)")
                    
                    for tool_call in assistant_message.tool_calls:
                        tracked_call = ToolCall(
                            id=tool_call.id,
                            name=tool_call.function.name,
                            arguments=json.loads(tool_call.function.arguments)
                        )
                        iteration_state.tool_calls.append(tracked_call)
                        
                        result = self._execute_tool_call(tool_call)
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result
                        })
                
                else:
                    final_response = assistant_message.content or ""
                    iteration_state.response = final_response
                    success = True
                    
                    iteration_state.end_time = datetime.now()
                    iterations.append(iteration_state)
                    
                    self.callback_handler.emit(EventType.ITERATION_END, iteration=iteration)
                    self.logger.info(f"Task completed in {iteration} iteration(s)")
                    
                    break
                
                iteration_state.end_time = datetime.now()
                iterations.append(iteration_state)
                self.callback_handler.emit(EventType.ITERATION_END, iteration=iteration)
            
            if iteration >= self.config.max_iterations and not success:
                error_message = f"Maximum iterations ({self.config.max_iterations}) reached"
                self.logger.warning(error_message)
                raise AgentExecutionError(error_message)
        
        except Exception as e:
            error_message = str(e)
            self.logger.error(f"Error during execution: {error_message}", exc_info=True)
            self.callback_handler.emit(EventType.ERROR, error=error_message)
            success = False
        
        end_time = datetime.now()
        total_tool_calls = sum(len(iter_state.tool_calls) for iter_state in iterations)
        
        response = AgentResponse(
            task=task,
            response=final_response,
            iterations=iterations,
            total_tool_calls=total_tool_calls,
            success=success,
            error_message=error_message,
            start_time=start_time,
            end_time=end_time
        )
        
        self.callback_handler.emit(EventType.AGENT_END, response=final_response, success=success)
        self.logger.info(f"Agent finished. Success: {success}, Duration: {response.total_duration:.2f}s")
        
        return response
    
    def reset(self) -> None:
        """Reset conversation history."""
        self.conversation_history = []
        self.logger.info("Conversation history cleared")
        if self.config.verbose:
            print("✓ Conversation history cleared")
