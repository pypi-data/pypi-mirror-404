"""
OR-AF Workflow - Node and Edge models
"""

import uuid
import time
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


@dataclass
class NodeCard:
    """
    Simple card for workflow nodes (internal use).
    
    This is a simplified version for internal workflow tracking,
    not the full A2A AgentCard from the official SDK.
    """
    node_id: str
    name: str
    description: str = ""
    capabilities: List[str] = field(default_factory=lambda: ["task_execution"])


class NodeStatus(str, Enum):
    """Status of a workflow node"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class EdgeCondition(str, Enum):
    """Built-in edge conditions"""
    ALWAYS = "always"
    ON_SUCCESS = "on_success"
    ON_FAILURE = "on_failure"
    ON_CONDITION = "on_condition"


@dataclass
class NodeResult:
    """Result from executing a node"""
    node_id: str
    status: NodeStatus
    output: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EdgeConfig:
    """Configuration for an edge between nodes"""
    source: str
    target: str
    condition: EdgeCondition = EdgeCondition.ALWAYS
    condition_func: Optional[Callable[[Any], bool]] = None
    transform_func: Optional[Callable[[Any], Any]] = None
    priority: int = 0


class Node:
    """
    Base class for workflow nodes.
    
    Nodes represent agents in the workflow graph.
    """
    
    def __init__(
        self,
        agent: Any,
        name: Optional[str] = None,
        description: str = ""
    ):
        """
        Initialize a workflow node.
        
        Args:
            agent: The agent instance for this node
            name: Optional name override
            description: Description of the node's purpose
        """
        self.node_id = str(uuid.uuid4())
        self.agent = agent
        self.name = name or getattr(agent, 'name', f"node_{self.node_id[:8]}")
        self.description = description
        self.status = NodeStatus.PENDING
        self.last_result: Optional[NodeResult] = None
        
        # Create node card for internal tracking
        self.agent_card = NodeCard(
            node_id=self.node_id,
            name=self.name,
            description=self.description or f"Workflow node: {self.name}",
            capabilities=["task_execution"]
        )
    
    def execute(self, input_data: Any, context: Dict[str, Any] = None) -> NodeResult:
        """Execute the node with given input."""
        start_time = time.time()
        self.status = NodeStatus.RUNNING
        
        try:
            if hasattr(self.agent, 'run'):
                result = self.agent.run(input_data)
                output = result.response if hasattr(result, 'response') else result
                success = result.success if hasattr(result, 'success') else True
            elif callable(self.agent):
                output = self.agent(input_data)
                success = True
            else:
                raise ValueError(f"Agent must have 'run' method or be callable")
            
            execution_time = time.time() - start_time
            
            if success:
                self.status = NodeStatus.COMPLETED
                node_result = NodeResult(
                    node_id=self.node_id,
                    status=NodeStatus.COMPLETED,
                    output=output,
                    execution_time=execution_time
                )
            else:
                self.status = NodeStatus.FAILED
                node_result = NodeResult(
                    node_id=self.node_id,
                    status=NodeStatus.FAILED,
                    error="Agent execution failed",
                    execution_time=execution_time
                )
        
        except Exception as e:
            execution_time = time.time() - start_time
            self.status = NodeStatus.FAILED
            node_result = NodeResult(
                node_id=self.node_id,
                status=NodeStatus.FAILED,
                error=str(e),
                execution_time=execution_time
            )
        
        self.last_result = node_result
        return node_result
    
    def reset(self) -> None:
        """Reset node state"""
        self.status = NodeStatus.PENDING
        self.last_result = None
    
    def __str__(self) -> str:
        return f"Node(name={self.name}, status={self.status.value})"


class ConditionalEdge:
    """
    Represents a conditional edge between two nodes in the workflow.
    """
    
    def __init__(
        self,
        source_node: Node,
        target_node: Node,
        condition: Union[EdgeCondition, Callable[[Any], bool]] = EdgeCondition.ALWAYS,
        transform: Optional[Callable[[Any], Any]] = None,
        name: Optional[str] = None
    ):
        """
        Initialize a conditional edge.
        
        Args:
            source_node: Source node
            target_node: Target node
            condition: Condition for traversal
            transform: Optional transform function
            name: Optional edge name
        """
        self.edge_id = str(uuid.uuid4())
        self.source = source_node
        self.target = target_node
        self.name = name or f"{source_node.name}->{target_node.name}"
        self.transform = transform
        
        if isinstance(condition, EdgeCondition):
            self.condition_type = condition
            self.condition_func = self._get_builtin_condition(condition)
        else:
            self.condition_type = EdgeCondition.ON_CONDITION
            self.condition_func = condition
    
    def _get_builtin_condition(self, condition: EdgeCondition) -> Callable[[Any], bool]:
        """Get built-in condition function"""
        if condition == EdgeCondition.ALWAYS:
            return lambda x: True
        elif condition == EdgeCondition.ON_SUCCESS:
            return lambda x: x.status == NodeStatus.COMPLETED if hasattr(x, 'status') else True
        elif condition == EdgeCondition.ON_FAILURE:
            return lambda x: x.status == NodeStatus.FAILED if hasattr(x, 'status') else False
        else:
            return lambda x: True
    
    def should_traverse(self, source_result: NodeResult) -> bool:
        """Check if this edge should be traversed"""
        return self.condition_func(source_result)
    
    def transform_data(self, data: Any) -> Any:
        """Transform data passing through the edge"""
        if self.transform:
            return self.transform(data)
        return data
    
    def __str__(self) -> str:
        condition_str = self.condition_type.value if isinstance(self.condition_type, EdgeCondition) else str(self.condition_type)
        return f"Edge({self.name}, condition={condition_str})"
