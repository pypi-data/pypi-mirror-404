"""
OR-AF Workflow - Graph implementation
"""

import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from datetime import datetime

from .nodes import Node, NodeStatus, NodeResult, EdgeCondition, ConditionalEdge
from ..a2a import A2AProtocol, A2AMessage, MessageType
from ..exceptions import (
    WorkflowError, InvalidNodeError, InvalidEdgeError, CycleDetectedError
)
from ..utils.logger import default_logger


class WorkflowGraph:
    """
    Workflow Graph for defining agent workflows with a TensorFlow-like API.
    
    Example:
        ```python
        workflow = WorkflowGraph(name="research_workflow")
        
        researcher = workflow.add_node(research_agent, name="researcher")
        analyzer = workflow.add_node(analysis_agent, name="analyzer")
        writer = workflow.add_node(writer_agent, name="writer")
        
        workflow.add_edge(researcher, analyzer, condition=EdgeCondition.ON_SUCCESS)
        workflow.add_edge(analyzer, writer, condition=EdgeCondition.ON_SUCCESS)
        
        workflow.compile()
        result = workflow.run("Research AI trends")
        ```
    """
    
    def __init__(self, name: str = "workflow", description: str = ""):
        """
        Initialize the workflow graph.
        
        Args:
            name: Workflow name
            description: Workflow description
        """
        self.workflow_id = str(uuid.uuid4())
        self.name = name
        self.description = description
        
        # Graph structure
        self.nodes: Dict[str, Node] = {}
        self.edges: List[ConditionalEdge] = []
        self.entry_node: Optional[Node] = None
        self.exit_nodes: Set[str] = set()
        
        # A2A Protocol
        self.a2a_protocol = A2AProtocol()
        
        # State
        self.compiled = False
        self.logger = default_logger
        
        # Execution tracking
        self.execution_history: List[Dict[str, Any]] = []
    
    def add_node(
        self,
        agent: Any,
        name: Optional[str] = None,
        description: str = "",
        is_entry: bool = False,
        is_exit: bool = False
    ) -> Node:
        """
        Add a node (agent) to the workflow graph.
        
        Args:
            agent: Agent instance
            name: Optional node name
            description: Node description
            is_entry: Whether this is the entry node
            is_exit: Whether this is an exit node
            
        Returns:
            The created Node
        """
        node = Node(agent=agent, name=name, description=description)
        self.nodes[node.node_id] = node
        
        # Register with A2A protocol
        self.a2a_protocol.register_handler(
            node.node_id,
            lambda msg, n=node: self._handle_node_message(n, msg)
        )
        
        if is_entry or self.entry_node is None:
            self.entry_node = node
        
        if is_exit:
            self.exit_nodes.add(node.node_id)
        
        self.compiled = False
        self.logger.info(f"Node '{node.name}' added to workflow '{self.name}'")
        
        return node
    
    def add_edge(
        self,
        source: Union[Node, str],
        target: Union[Node, str],
        condition: Union[EdgeCondition, Callable[[Any], bool]] = EdgeCondition.ALWAYS,
        transform: Optional[Callable[[Any], Any]] = None,
        name: Optional[str] = None
    ) -> ConditionalEdge:
        """
        Add a conditional edge between two nodes.
        
        Args:
            source: Source node or node name
            target: Target node or node name
            condition: Edge condition
            transform: Optional data transform function
            name: Optional edge name
            
        Returns:
            The created ConditionalEdge
        """
        source_node = self._resolve_node(source)
        target_node = self._resolve_node(target)
        
        if source_node is None:
            raise InvalidNodeError(f"Source node not found: {source}")
        if target_node is None:
            raise InvalidNodeError(f"Target node not found: {target}")
        
        edge = ConditionalEdge(
            source_node=source_node,
            target_node=target_node,
            condition=condition,
            transform=transform,
            name=name
        )
        
        self.edges.append(edge)
        self.compiled = False
        self.logger.info(f"Edge '{edge.name}' added to workflow")
        
        return edge
    
    def connect(
        self,
        *nodes: Node,
        condition: Union[EdgeCondition, Callable[[Any], bool]] = EdgeCondition.ALWAYS
    ) -> "WorkflowGraph":
        """Connect multiple nodes in sequence."""
        for i in range(len(nodes) - 1):
            self.add_edge(nodes[i], nodes[i + 1], condition=condition)
        return self
    
    def branch(
        self,
        source: Node,
        branches: List[Tuple[Node, Callable[[Any], bool]]]
    ) -> "WorkflowGraph":
        """Create conditional branches from a source node."""
        for target, condition in branches:
            self.add_edge(source, target, condition=condition)
        return self
    
    def merge(
        self,
        sources: List[Node],
        target: Node,
        condition: Union[EdgeCondition, Callable[[Any], bool]] = EdgeCondition.ON_SUCCESS
    ) -> "WorkflowGraph":
        """Merge multiple source nodes into a single target."""
        for source in sources:
            self.add_edge(source, target, condition=condition)
        return self
    
    def _resolve_node(self, node_ref: Union[Node, str]) -> Optional[Node]:
        """Resolve a node reference to a Node object"""
        if isinstance(node_ref, Node):
            return node_ref
        
        if node_ref in self.nodes:
            return self.nodes[node_ref]
        
        for node in self.nodes.values():
            if node.name == node_ref:
                return node
        
        return None
    
    def _handle_node_message(self, node: Node, message: A2AMessage) -> Optional[A2AMessage]:
        """Handle A2A message for a node"""
        if message.message_type == MessageType.REQUEST:
            result = node.execute(message.task, message.context)
            return message.create_response(
                responder_id=node.node_id,
                content=result.output,
                success=result.status == NodeStatus.COMPLETED,
                error=result.error
            )
        return None
    
    def _get_outgoing_edges(self, node: Node) -> List[ConditionalEdge]:
        """Get all outgoing edges from a node"""
        return [edge for edge in self.edges if edge.source.node_id == node.node_id]
    
    def _detect_cycles(self) -> bool:
        """Detect cycles in the graph using DFS"""
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for edge in self.edges:
                if edge.source.node_id == node_id:
                    target_id = edge.target.node_id
                    if target_id not in visited:
                        if dfs(target_id):
                            return True
                    elif target_id in rec_stack:
                        return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in self.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    return True
        
        return False
    
    def compile(self, check_cycles: bool = True) -> "WorkflowGraph":
        """
        Compile the workflow graph.
        
        Validates the graph structure and prepares it for execution.
        """
        if not self.nodes:
            raise WorkflowError("Workflow has no nodes")
        
        if self.entry_node is None:
            raise WorkflowError("No entry node defined")
        
        if check_cycles and self._detect_cycles():
            raise CycleDetectedError("Workflow contains cycles")
        
        if not self.exit_nodes:
            nodes_with_outgoing = {e.source.node_id for e in self.edges}
            self.exit_nodes = set(self.nodes.keys()) - nodes_with_outgoing
        
        self.compiled = True
        self.logger.info(f"Workflow '{self.name}' compiled successfully")
        
        return self
    
    def run(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute the workflow."""
        if not self.compiled:
            self.compile()
        
        context = context or {}
        results: Dict[str, NodeResult] = {}
        execution_order: List[str] = []
        
        for node in self.nodes.values():
            node.reset()
        
        current_data = input_data
        nodes_to_execute = [self.entry_node]
        
        while nodes_to_execute:
            node = nodes_to_execute.pop(0)
            
            if node.node_id in results:
                continue
            
            self.logger.info(f"Executing node: {node.name}")
            
            result = node.execute(current_data, context)
            results[node.node_id] = result
            execution_order.append(node.node_id)
            
            if result.status == NodeStatus.COMPLETED:
                current_data = result.output
            
            outgoing_edges = self._get_outgoing_edges(node)
            for edge in outgoing_edges:
                if edge.should_traverse(result):
                    if edge.transform:
                        current_data = edge.transform_data(result.output)
                    else:
                        current_data = result.output
                    nodes_to_execute.append(edge.target)
        
        final_outputs = []
        for exit_id in self.exit_nodes:
            if exit_id in results:
                final_outputs.append(results[exit_id])
        
        execution_record = {
            "workflow_id": self.workflow_id,
            "workflow_name": self.name,
            "input": input_data,
            "results": results,
            "execution_order": execution_order,
            "final_outputs": final_outputs,
            "success": all(r.status == NodeStatus.COMPLETED for r in results.values()),
            "timestamp": datetime.now()
        }
        
        self.execution_history.append(execution_record)
        self.logger.info(f"Workflow '{self.name}' execution completed")
        
        return execution_record
    
    def visualize(self, format: str = "text", show_details: bool = True) -> str:
        """
        Generate a visualization of the workflow.
        
        Args:
            format: Output format ('text', 'mermaid', 'ascii')
            show_details: Include MCP servers and tools in visualization
            
        Returns:
            String representation of the workflow
        """
        from .visualization import WorkflowVisualizer
        visualizer = WorkflowVisualizer(self)
        return visualizer.render(format=format, show_details=show_details)
    
    def __str__(self) -> str:
        return f"WorkflowGraph(name={self.name}, nodes={len(self.nodes)}, edges={len(self.edges)})"
