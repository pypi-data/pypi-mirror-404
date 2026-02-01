"""
Agent implementation for the Agentic Framework
"""

import json
import time
from typing import Callable, Dict, List, Any, Optional, Generator
from datetime import datetime
from openai import AzureOpenAI
from dotenv import load_dotenv
import os

from .models import (
    AgentConfig, AgentResponse, AgentEvent, EventType,
    IterationState, ToolCall, Message, MessageRole
)
from .tool import Tool
from .callbacks import CallbackManager, ConsoleCallback, LoggingCallback
from .exceptions import (
    ToolNotFoundError, MaxIterationsReachedError,
    OpenAIError, InvalidConfigurationError
)
from .logger import default_logger


class Agent:
    """Lightweight AI Agent with tool support, streaming, and observability"""
    
    def __init__(
        self,
        system_prompt: str,
        model_name: Optional[str] = None,
        temperature: float = 1.0,
        max_iterations: int = 10,
        stream: bool = True,
        verbose: bool = True,
        callbacks: Optional[List] = None
    ):
        """
        Initialize the agent
        
        Args:
            system_prompt: The system prompt defining agent behavior
            model_name: OpenAI model name (defaults to env variable)
            temperature: Sampling temperature
            max_iterations: Maximum number of iterations for task execution
            stream: Enable streaming responses
            verbose: Enable verbose output
            callbacks: List of callback objects for observability
        """
        # Load environment variables
        load_dotenv()
        
        # Validate configuration
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
            raise InvalidConfigurationError(f"Invalid configuration: {str(e)}")
        
        # Initialize components
        self.logger = default_logger
        self.tools: Dict[str, Tool] = {}
        self.conversation_history: List[Message] = []
        
        # Setup callbacks
        self.callback_manager = CallbackManager(callbacks or [])
        if verbose:
            self.callback_manager.add_callback(ConsoleCallback(verbose=True))
        self.callback_manager.add_callback(LoggingCallback(self.logger))
        
        # Initialize Azure OpenAI client
        try:
            self.client = AzureOpenAI(
                api_key=os.getenv("subscription_key"),
                api_version=os.getenv("api_version"),
                azure_endpoint=os.getenv("endpoint")
            )
            self.model_name = model_name or os.getenv("deployment", "gpt-4")
            self.logger.info(f"Agent initialized with model: {self.model_name}")
        except Exception as e:
            raise OpenAIError(f"Failed to initialize OpenAI client: {str(e)}")
    
    def add_tool(self, name: str, func: Callable, description: Optional[str] = None) -> None:
        """
        Add a tool to the agent
        
        Args:
            name: Tool name
            func: Callable function
            description: Tool description
        """
        tool = Tool(name=name, func=func, description=description)
        self.tools[name] = tool
        self.logger.info(f"Tool '{name}' registered")
        
        if self.config.verbose:
            print(f"✓ Tool '{name}' registered")
    
    def add_tools(self, tools: List[tuple]) -> None:
        """
        Add multiple tools at once
        
        Args:
            tools: List of (name, func, description) tuples
        """
        for tool_info in tools:
            if len(tool_info) == 2:
                name, func = tool_info
                self.add_tool(name, func)
            else:
                name, func, desc = tool_info
                self.add_tool(name, func, desc)
    
    def _get_tools_schema(self) -> List[Dict[str, Any]]:
        """Get all tools in OpenAI format"""
        return [tool.to_openai_format() for tool in self.tools.values()]
    
    def _execute_tool_call(self, tool_call) -> str:
        """Execute a tool call and return the result"""
        tool_name = tool_call.function.name
        
        try:
            # Parse arguments
            arguments = json.loads(tool_call.function.arguments)
            
            # Create ToolCall object for tracking
            tracked_call = ToolCall(
                id=tool_call.id,
                name=tool_name,
                arguments=arguments
            )
            
            # Emit tool call start event
            self.callback_manager.on_tool_call_start(tracked_call)
            
            # Execute tool
            if tool_name not in self.tools:
                error_msg = f"Tool '{tool_name}' not found"
                self.callback_manager.on_tool_error(tool_name, error_msg)
                raise ToolNotFoundError(error_msg)
            
            tool_result = self.tools[tool_name].execute(tool_call.id, **arguments)
            
            # Emit tool call end event
            self.callback_manager.on_tool_call_end(tool_result)
            
            if tool_result.success:
                return str(tool_result.result)
            else:
                return tool_result.error
        
        except Exception as e:
            error_msg = f"Error executing {tool_name}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.callback_manager.on_tool_error(tool_name, str(e))
            return error_msg
    
    def _stream_response(self, messages: List[Dict], iteration: int) -> tuple[str, Any]:
        """
        Stream response from OpenAI
        
        Returns:
            Tuple of (complete_response, assistant_message)
        """
        api_params = {
            "model": self.model_name,
            "messages": messages,
            "stream": True
        }
        
        # Add temperature if not default
        if self.config.temperature != 1.0:
            api_params["temperature"] = self.config.temperature
        
        # Add tools if available
        if self.tools:
            api_params["tools"] = self._get_tools_schema()
            api_params["tool_choice"] = "auto"
        
        try:
            stream = self.client.chat.completions.create(**api_params)
            
            collected_messages = []
            collected_tool_calls = []
            
            for chunk in stream:
                if not chunk.choices:
                    continue
                
                delta = chunk.choices[0].delta
                
                # Handle content
                if delta.content:
                    collected_messages.append(delta.content)
                    self.callback_manager.on_stream_chunk(delta.content)
                
                # Handle tool calls
                if delta.tool_calls:
                    for tool_call_chunk in delta.tool_calls:
                        # Initialize or update tool call
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
            
            # Construct complete message
            content = "".join(collected_messages) if collected_messages else None
            
            # Create a mock assistant message object
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
        """Get non-streaming response from OpenAI"""
        api_params = {
            "model": self.model_name,
            "messages": messages
        }
        
        # Add temperature if not default
        if self.config.temperature != 1.0:
            api_params["temperature"] = self.config.temperature
        
        # Add tools if available
        if self.tools:
            api_params["tools"] = self._get_tools_schema()
            api_params["tool_choice"] = "auto"
        
        try:
            response = self.client.chat.completions.create(**api_params)
            return response.choices[0].message
        except Exception as e:
            raise OpenAIError(f"OpenAI API error: {str(e)}")
    
    def run(self, task: str, stream: Optional[bool] = None) -> AgentResponse:
        """
        Run a task using the agent
        
        Args:
            task: The task/prompt for the agent
            stream: Override default streaming setting
            
        Returns:
            AgentResponse with complete execution details
        """
        start_time = datetime.now()
        use_stream = stream if stream is not None else self.config.stream
        
        # Emit agent start event
        self.callback_manager.on_agent_start(task)
        self.logger.info(f"Agent started with task: {task}")
        
        # Initialize conversation
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
                
                # Emit iteration start event
                self.callback_manager.on_iteration_start(iteration)
                self.logger.debug(f"Starting iteration {iteration}")
                
                # Create iteration state
                iteration_state = IterationState(
                    iteration_number=iteration,
                    start_time=iter_start
                )
                
                # Get response from OpenAI
                if use_stream:
                    content, assistant_message = self._stream_response(messages, iteration)
                else:
                    assistant_message = self._non_stream_response(messages)
                    content = assistant_message.content or ""
                
                # Track thinking/reasoning
                if content and not assistant_message.tool_calls:
                    iteration_state.thinking = content
                    self.callback_manager.on_thinking(iteration, content)
                
                # Add assistant response to messages
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
                
                # Check if there are tool calls
                if assistant_message.tool_calls:
                    self.logger.info(f"Agent requested {len(assistant_message.tool_calls)} tool(s)")
                    
                    # Execute each tool call
                    for tool_call in assistant_message.tool_calls:
                        # Track tool call
                        tracked_call = ToolCall(
                            id=tool_call.id,
                            name=tool_call.function.name,
                            arguments=json.loads(tool_call.function.arguments)
                        )
                        iteration_state.tool_calls.append(tracked_call)
                        
                        # Execute tool
                        result = self._execute_tool_call(tool_call)
                        
                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result
                        })
                
                else:
                    # No tool calls, agent has finished
                    final_response = assistant_message.content or ""
                    iteration_state.response = final_response
                    success = True
                    
                    # Mark iteration end
                    iteration_state.end_time = datetime.now()
                    iterations.append(iteration_state)
                    
                    self.callback_manager.on_iteration_end(iteration_state)
                    self.logger.info(f"Task completed in {iteration} iteration(s)")
                    
                    break
                
                # Mark iteration end
                iteration_state.end_time = datetime.now()
                iterations.append(iteration_state)
                self.callback_manager.on_iteration_end(iteration_state)
            
            # Check if max iterations reached
            if iteration >= self.config.max_iterations and not success:
                error_message = f"Maximum iterations ({self.config.max_iterations}) reached"
                self.logger.warning(error_message)
                raise MaxIterationsReachedError(error_message)
        
        except Exception as e:
            error_message = str(e)
            self.logger.error(f"Error during execution: {error_message}", exc_info=True)
            self.callback_manager.on_error(e)
            success = False
        
        # Create response object
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
        
        # Emit agent end event
        self.callback_manager.on_agent_end(final_response, success)
        self.logger.info(f"Agent finished. Success: {success}, Duration: {response.total_duration:.2f}s")
        
        return response
    
    def reset(self) -> None:
        """Reset conversation history"""
        self.conversation_history = []
        self.logger.info("Conversation history cleared")
        if self.config.verbose:
            print("✓ Conversation history cleared")
