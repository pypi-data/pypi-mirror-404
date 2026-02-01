"""
Callback system for agent observability and control
"""

from typing import Callable, List, Optional, Any, Dict
from abc import ABC, abstractmethod
import logging

from .models import AgentEvent, EventType, ToolCall, ToolResult, IterationState
from .logger import default_logger


class BaseCallback(ABC):
    """Base class for all callbacks"""
    
    @abstractmethod
    def on_event(self, event: AgentEvent) -> None:
        """Called when an event occurs"""
        pass
    
    def on_agent_start(self, task: str) -> None:
        """Called when agent starts processing a task"""
        pass
    
    def on_agent_end(self, response: str, success: bool) -> None:
        """Called when agent finishes processing"""
        pass
    
    def on_iteration_start(self, iteration: int) -> None:
        """Called at the start of each iteration"""
        pass
    
    def on_iteration_end(self, iteration_state: IterationState) -> None:
        """Called at the end of each iteration"""
        pass
    
    def on_thinking(self, iteration: int, thinking: str) -> None:
        """Called when agent is thinking/reasoning"""
        pass
    
    def on_tool_call_start(self, tool_call: ToolCall) -> None:
        """Called before a tool is executed"""
        pass
    
    def on_tool_call_end(self, tool_result: ToolResult) -> None:
        """Called after a tool is executed"""
        pass
    
    def on_tool_error(self, tool_name: str, error: str) -> None:
        """Called when a tool execution fails"""
        pass
    
    def on_stream_chunk(self, chunk: str) -> None:
        """Called when a stream chunk is received"""
        pass
    
    def on_error(self, error: Exception) -> None:
        """Called when an error occurs"""
        pass


class ConsoleCallback(BaseCallback):
    """Callback that prints events to console"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.logger = default_logger
    
    def on_event(self, event: AgentEvent) -> None:
        """Log all events"""
        if self.verbose:
            self.logger.debug(f"Event: {event.event_type} - {event.data}")
    
    def on_agent_start(self, task: str) -> None:
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"🤖 AGENT STARTED")
            print(f"{'='*70}")
            print(f"Task: {task}")
            print(f"{'='*70}\n")
    
    def on_agent_end(self, response: str, success: bool) -> None:
        if self.verbose:
            status = "✓ SUCCESS" if success else "✗ FAILED"
            print(f"\n{'='*70}")
            print(f"🏁 AGENT FINISHED - {status}")
            print(f"{'='*70}")
            print(f"Response: {response}")
            print(f"{'='*70}\n")
    
    def on_iteration_start(self, iteration: int) -> None:
        if self.verbose:
            print(f"\n{'─'*70}")
            print(f"⚙️  ITERATION {iteration}")
            print(f"{'─'*70}")
    
    def on_iteration_end(self, iteration_state: IterationState) -> None:
        if self.verbose:
            duration = iteration_state.duration
            print(f"⏱️  Iteration completed in {duration:.2f}s" if duration else "")
    
    def on_thinking(self, iteration: int, thinking: str) -> None:
        if self.verbose:
            print(f"\n💭 Agent Reasoning:")
            print(f"   {thinking}")
    
    def on_tool_call_start(self, tool_call: ToolCall) -> None:
        if self.verbose:
            print(f"\n🔧 Calling Tool: {tool_call.name}")
            print(f"   Arguments: {tool_call.arguments}")
    
    def on_tool_call_end(self, tool_result: ToolResult) -> None:
        if self.verbose:
            if tool_result.success:
                print(f"   ✓ Result: {tool_result.result}")
                print(f"   ⏱️  Execution time: {tool_result.execution_time:.3f}s")
            else:
                print(f"   ✗ Error: {tool_result.error}")
    
    def on_tool_error(self, tool_name: str, error: str) -> None:
        print(f"\n❌ Tool Error in '{tool_name}': {error}")
    
    def on_stream_chunk(self, chunk: str) -> None:
        print(chunk, end='', flush=True)
    
    def on_error(self, error: Exception) -> None:
        print(f"\n❌ Error: {str(error)}")


class LoggingCallback(BaseCallback):
    """Callback that logs events to logger"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or default_logger
    
    def on_event(self, event: AgentEvent) -> None:
        self.logger.info(f"Event: {event.event_type}", extra={"event_data": event.data})
    
    def on_agent_start(self, task: str) -> None:
        self.logger.info(f"Agent started with task: {task}")
    
    def on_agent_end(self, response: str, success: bool) -> None:
        status = "success" if success else "failed"
        self.logger.info(f"Agent finished with {status}")
    
    def on_iteration_start(self, iteration: int) -> None:
        self.logger.debug(f"Starting iteration {iteration}")
    
    def on_iteration_end(self, iteration_state: IterationState) -> None:
        self.logger.debug(f"Iteration {iteration_state.iteration_number} completed")
    
    def on_thinking(self, iteration: int, thinking: str) -> None:
        self.logger.info(f"Agent thinking (iteration {iteration}): {thinking}")
    
    def on_tool_call_start(self, tool_call: ToolCall) -> None:
        self.logger.info(f"Calling tool: {tool_call.name} with args: {tool_call.arguments}")
    
    def on_tool_call_end(self, tool_result: ToolResult) -> None:
        if tool_result.success:
            self.logger.info(f"Tool {tool_result.tool_name} completed successfully")
        else:
            self.logger.error(f"Tool {tool_result.tool_name} failed: {tool_result.error}")
    
    def on_tool_error(self, tool_name: str, error: str) -> None:
        self.logger.error(f"Tool error in {tool_name}: {error}")
    
    def on_error(self, error: Exception) -> None:
        self.logger.error(f"Error occurred: {str(error)}", exc_info=True)


class CallbackManager:
    """Manages multiple callbacks"""
    
    def __init__(self, callbacks: Optional[List[BaseCallback]] = None):
        self.callbacks: List[BaseCallback] = callbacks or []
    
    def add_callback(self, callback: BaseCallback) -> None:
        """Add a callback"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: BaseCallback) -> None:
        """Remove a callback"""
        self.callbacks.remove(callback)
    
    def emit_event(self, event: AgentEvent) -> None:
        """Emit an event to all callbacks"""
        for callback in self.callbacks:
            try:
                callback.on_event(event)
            except Exception as e:
                default_logger.error(f"Callback error: {e}")
    
    def on_agent_start(self, task: str) -> None:
        for callback in self.callbacks:
            try:
                callback.on_agent_start(task)
            except Exception as e:
                default_logger.error(f"Callback error: {e}")
    
    def on_agent_end(self, response: str, success: bool) -> None:
        for callback in self.callbacks:
            try:
                callback.on_agent_end(response, success)
            except Exception as e:
                default_logger.error(f"Callback error: {e}")
    
    def on_iteration_start(self, iteration: int) -> None:
        for callback in self.callbacks:
            try:
                callback.on_iteration_start(iteration)
            except Exception as e:
                default_logger.error(f"Callback error: {e}")
    
    def on_iteration_end(self, iteration_state: IterationState) -> None:
        for callback in self.callbacks:
            try:
                callback.on_iteration_end(iteration_state)
            except Exception as e:
                default_logger.error(f"Callback error: {e}")
    
    def on_thinking(self, iteration: int, thinking: str) -> None:
        for callback in self.callbacks:
            try:
                callback.on_thinking(iteration, thinking)
            except Exception as e:
                default_logger.error(f"Callback error: {e}")
    
    def on_tool_call_start(self, tool_call: ToolCall) -> None:
        for callback in self.callbacks:
            try:
                callback.on_tool_call_start(tool_call)
            except Exception as e:
                default_logger.error(f"Callback error: {e}")
    
    def on_tool_call_end(self, tool_result: ToolResult) -> None:
        for callback in self.callbacks:
            try:
                callback.on_tool_call_end(tool_result)
            except Exception as e:
                default_logger.error(f"Callback error: {e}")
    
    def on_tool_error(self, tool_name: str, error: str) -> None:
        for callback in self.callbacks:
            try:
                callback.on_tool_error(tool_name, error)
            except Exception as e:
                default_logger.error(f"Callback error: {e}")
    
    def on_stream_chunk(self, chunk: str) -> None:
        for callback in self.callbacks:
            try:
                callback.on_stream_chunk(chunk)
            except Exception as e:
                default_logger.error(f"Callback error: {e}")
    
    def on_error(self, error: Exception) -> None:
        for callback in self.callbacks:
            try:
                callback.on_error(error)
            except Exception as e:
                default_logger.error(f"Callback error: {e}")
