"""
OR-AF A2A Compatibility Module

This module provides backwards-compatible classes for the workflow module
while internally using the official A2A SDK.
"""

from typing import Any, Callable, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum
import uuid
from dataclasses import dataclass, field


class MessageType(str, Enum):
    """Type of A2A message"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


@dataclass
class A2AMessage:
    """
    A2A Message for workflow communication.
    
    This is a backwards-compatible message class for internal workflow use.
    For new code, use the official A2A SDK types.
    """
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.REQUEST
    sender_id: str = ""
    receiver_id: str = ""
    task: Any = None
    context: Dict[str, Any] = field(default_factory=dict)
    content: Any = None
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def create_response(
        self,
        responder_id: str,
        content: Any,
        success: bool = True,
        error: Optional[str] = None
    ) -> "A2AMessage":
        """
        Create a response message.
        
        Args:
            responder_id: ID of the responding agent/node
            content: Response content
            success: Whether the operation succeeded
            error: Error message if failed
        
        Returns:
            A2AMessage response
        """
        return A2AMessage(
            message_type=MessageType.RESPONSE if success else MessageType.ERROR,
            sender_id=responder_id,
            receiver_id=self.sender_id,
            content=content if success else error,
            correlation_id=self.message_id,
            context=self.context.copy(),
            metadata={"success": success, "original_task": self.task}
        )


class A2AProtocol:
    """
    A2A Protocol for workflow communication.
    
    This is a backwards-compatible protocol class for internal workflow use.
    For new code, use A2AAgent with the official A2A SDK.
    
    Deprecated: Use A2AAgent instead for new implementations.
    """
    
    def __init__(self):
        """Initialize the A2A protocol handler."""
        self.protocol_id = str(uuid.uuid4())
        self.registered_handlers: Dict[str, Callable] = {}
        self.message_history: List[A2AMessage] = []
    
    def register_handler(
        self,
        message_type: Union[MessageType, str],
        handler: Callable[[A2AMessage], Optional[A2AMessage]]
    ) -> None:
        """
        Register a handler for a message type or identifier.
        
        Args:
            message_type: Type of message to handle (MessageType enum or string ID)
            handler: Handler function
        """
        key = message_type.value if isinstance(message_type, MessageType) else str(message_type)
        self.registered_handlers[key] = handler
    
    def send_message(
        self,
        sender_id: str,
        receiver_id: str,
        task: Any,
        context: Optional[Dict[str, Any]] = None,
        message_type: MessageType = MessageType.REQUEST
    ) -> A2AMessage:
        """
        Create and send a message.
        
        Args:
            sender_id: ID of sender
            receiver_id: ID of receiver
            task: Task data
            context: Optional context
            message_type: Type of message
        
        Returns:
            The created message
        """
        message = A2AMessage(
            message_type=message_type,
            sender_id=sender_id,
            receiver_id=receiver_id,
            task=task,
            context=context or {}
        )
        self.message_history.append(message)
        return message
    
    def handle_message(self, message: A2AMessage) -> Optional[A2AMessage]:
        """
        Process a message using registered handlers.
        
        Args:
            message: The message to process
        
        Returns:
            Response message if any
        """
        handler = self.registered_handlers.get(message.message_type.value)
        if handler:
            response = handler(message)
            if response:
                self.message_history.append(response)
            return response
        return None
    
    def get_message_history(self) -> List[A2AMessage]:
        """Get all message history."""
        return self.message_history.copy()
    
    def clear_history(self) -> None:
        """Clear message history."""
        self.message_history.clear()
