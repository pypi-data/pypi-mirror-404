"""
OR-AF Callbacks System

Event-driven callback system for monitoring agent execution.
"""

from typing import Any, Callable, Dict, List, Optional
from enum import Enum
from abc import ABC, abstractmethod
from datetime import datetime

from ..models import EventType, AgentEvent


class BaseCallback(ABC):
    """Base class for all callbacks"""
    
    @abstractmethod
    def on_event(self, event: AgentEvent) -> None:
        """Handle an event"""
        pass


class CallbackHandler(BaseCallback):
    """
    Callback handler for agent events.
    
    Register callbacks for specific event types to monitor
    and respond to agent execution events.
    """
    
    def __init__(self):
        self._callbacks: Dict[EventType, List[Callable[[AgentEvent], None]]] = {
            event_type: [] for event_type in EventType
        }
        self._global_callbacks: List[Callable[[AgentEvent], None]] = []
    
    def register(
        self,
        event_type: EventType,
        callback: Callable[[AgentEvent], None]
    ) -> None:
        """Register a callback for a specific event type"""
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)
    
    def register_global(self, callback: Callable[[AgentEvent], None]) -> None:
        """Register a callback for all events"""
        self._global_callbacks.append(callback)
    
    def unregister(
        self,
        event_type: EventType,
        callback: Callable[[AgentEvent], None]
    ) -> bool:
        """Unregister a callback"""
        if event_type in self._callbacks:
            try:
                self._callbacks[event_type].remove(callback)
                return True
            except ValueError:
                return False
        return False
    
    def on_event(self, event: AgentEvent) -> None:
        """Handle an event by calling registered callbacks"""
        # Call global callbacks
        for callback in self._global_callbacks:
            try:
                callback(event)
            except Exception:
                pass  # Don't let callback errors crash the agent
        
        # Call event-specific callbacks
        event_type = EventType(event.event_type) if isinstance(event.event_type, str) else event.event_type
        if event_type in self._callbacks:
            for callback in self._callbacks[event_type]:
                try:
                    callback(event)
                except Exception:
                    pass
    
    def emit(
        self,
        event_type: EventType,
        iteration: Optional[int] = None,
        **data
    ) -> AgentEvent:
        """Create and emit an event"""
        event = AgentEvent(
            event_type=event_type,
            iteration=iteration,
            data=data
        )
        self.on_event(event)
        return event


class ConsoleCallback(BaseCallback):
    """Callback that prints events to console"""
    
    def __init__(self, verbose: bool = True, colors: bool = True):
        self.verbose = verbose
        self.colors = colors
        self._event_icons = {
            EventType.AGENT_START: "🚀",
            EventType.AGENT_END: "🏁",
            EventType.ITERATION_START: "🔄",
            EventType.ITERATION_END: "✓",
            EventType.THINKING: "💭",
            EventType.TOOL_CALL_START: "🔧",
            EventType.TOOL_CALL_END: "✅",
            EventType.TOOL_ERROR: "❌",
            EventType.STREAM_CHUNK: "📝",
            EventType.ERROR: "⚠️",
            EventType.WARNING: "⚡"
        }
    
    def on_event(self, event: AgentEvent) -> None:
        """Print event to console"""
        if not self.verbose:
            return
        
        event_type = EventType(event.event_type) if isinstance(event.event_type, str) else event.event_type
        icon = self._event_icons.get(event_type, "📌")
        
        timestamp = event.timestamp.strftime("%H:%M:%S")
        iteration = f"[{event.iteration}]" if event.iteration is not None else ""
        
        message = f"{timestamp} {icon} {event_type.value} {iteration}"
        
        if event.data:
            if 'message' in event.data:
                message += f": {event.data['message']}"
            elif 'tool_name' in event.data:
                message += f": {event.data['tool_name']}"
            elif 'chunk' in event.data:
                # For streaming chunks, print the content inline without newline
                print(event.data['chunk'], end='', flush=True)
                return  # Skip the normal message printing
        
        print(message)


class FileCallback(BaseCallback):
    """Callback that writes events to a file"""
    
    def __init__(self, filepath: str, append: bool = True):
        self.filepath = filepath
        self.mode = 'a' if append else 'w'
    
    def on_event(self, event: AgentEvent) -> None:
        """Write event to file"""
        import json
        
        log_entry = {
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type.value if hasattr(event.event_type, 'value') else event.event_type,
            "iteration": event.iteration,
            "data": self._serialize_data(event.data)
        }
        
        with open(self.filepath, self.mode) as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def _serialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize data for JSON output"""
        result = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif hasattr(value, 'model_dump'):
                result[key] = value.model_dump()
            elif hasattr(value, '__dict__'):
                result[key] = str(value)
            else:
                try:
                    import json
                    json.dumps(value)
                    result[key] = value
                except (TypeError, ValueError):
                    result[key] = str(value)
        return result


class MetricsCallback(BaseCallback):
    """Callback that collects metrics about agent execution"""
    
    def __init__(self):
        self.reset()
    
    def reset(self) -> None:
        """Reset all metrics"""
        self.total_iterations = 0
        self.total_tool_calls = 0
        self.successful_tool_calls = 0
        self.failed_tool_calls = 0
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.tool_execution_times: List[float] = []
    
    def on_event(self, event: AgentEvent) -> None:
        """Collect metrics from events"""
        event_type = EventType(event.event_type) if isinstance(event.event_type, str) else event.event_type
        
        if event_type == EventType.AGENT_START:
            self.start_time = event.timestamp
        elif event_type == EventType.AGENT_END:
            self.end_time = event.timestamp
        elif event_type == EventType.ITERATION_END:
            self.total_iterations += 1
        elif event_type == EventType.TOOL_CALL_END:
            self.total_tool_calls += 1
            self.successful_tool_calls += 1
            if 'execution_time' in event.data:
                self.tool_execution_times.append(event.data['execution_time'])
        elif event_type == EventType.TOOL_ERROR:
            self.total_tool_calls += 1
            self.failed_tool_calls += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics"""
        total_time = None
        if self.start_time and self.end_time:
            total_time = (self.end_time - self.start_time).total_seconds()
        
        avg_tool_time = None
        if self.tool_execution_times:
            avg_tool_time = sum(self.tool_execution_times) / len(self.tool_execution_times)
        
        return {
            "total_iterations": self.total_iterations,
            "total_tool_calls": self.total_tool_calls,
            "successful_tool_calls": self.successful_tool_calls,
            "failed_tool_calls": self.failed_tool_calls,
            "total_execution_time": total_time,
            "average_tool_execution_time": avg_tool_time,
            "tool_success_rate": (
                self.successful_tool_calls / self.total_tool_calls
                if self.total_tool_calls > 0 else None
            )
        }
