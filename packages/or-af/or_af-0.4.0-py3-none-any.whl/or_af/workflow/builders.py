"""
OR-AF Workflow - Sequential and Parallel workflows (TensorFlow-like API)
"""

from typing import Any, List, Optional

from .graph import WorkflowGraph
from .nodes import Node, EdgeCondition


class Sequential(WorkflowGraph):
    """
    Sequential workflow - a linear chain of agents.
    
    Similar to tf.keras.Sequential for defining linear workflows.
    
    Example:
        ```python
        workflow = Sequential([
            agent1,
            agent2,
            agent3
        ], name="my_workflow")
        
        result = workflow.run("Initial task")
        ```
    """
    
    def __init__(
        self,
        agents: List[Any] = None,
        name: str = "sequential_workflow"
    ):
        """
        Initialize a sequential workflow.
        
        Args:
            agents: List of agents to chain sequentially
            name: Workflow name
        """
        super().__init__(name=name)
        
        if agents:
            nodes = []
            for i, agent in enumerate(agents):
                node = self.add_node(
                    agent,
                    name=getattr(agent, 'name', f"agent_{i}"),
                    is_entry=(i == 0),
                    is_exit=(i == len(agents) - 1)
                )
                nodes.append(node)
            
            self.connect(*nodes, condition=EdgeCondition.ON_SUCCESS)
            self.compile()
    
    def add(self, agent: Any, name: Optional[str] = None) -> "Sequential":
        """
        Add an agent to the end of the sequence.
        
        Args:
            agent: Agent to add
            name: Optional agent name
            
        Returns:
            Self for method chaining
        """
        last_node = None
        for node in self.nodes.values():
            if node.node_id in self.exit_nodes:
                last_node = node
                break
        
        new_node = self.add_node(agent, name=name, is_exit=True)
        
        if last_node:
            self.exit_nodes.discard(last_node.node_id)
            self.add_edge(last_node, new_node, condition=EdgeCondition.ON_SUCCESS)
        
        self.compiled = False
        return self


class Parallel(WorkflowGraph):
    """
    Parallel workflow - execute multiple agents in parallel and merge results.
    
    Example:
        ```python
        workflow = Parallel([
            researcher_agent,
            analyzer_agent,
            validator_agent
        ], merge_agent=summarizer_agent, name="parallel_research")
        
        result = workflow.run("Research topic")
        ```
    """
    
    def __init__(
        self,
        agents: List[Any] = None,
        merge_agent: Any = None,
        name: str = "parallel_workflow"
    ):
        """
        Initialize a parallel workflow.
        
        Args:
            agents: List of agents to run in parallel
            merge_agent: Optional agent to merge parallel results
            name: Workflow name
        """
        super().__init__(name=name)
        
        if agents:
            router = self.add_node(
                lambda x: x,
                name="router",
                is_entry=True
            )
            
            parallel_nodes = []
            for i, agent in enumerate(agents):
                node = self.add_node(
                    agent,
                    name=getattr(agent, 'name', f"parallel_{i}")
                )
                self.add_edge(router, node)
                parallel_nodes.append(node)
            
            if merge_agent:
                merger = self.add_node(
                    merge_agent,
                    name=getattr(merge_agent, 'name', "merger"),
                    is_exit=True
                )
                self.merge(parallel_nodes, merger)
            else:
                for node in parallel_nodes:
                    self.exit_nodes.add(node.node_id)
            
            self.compile()


def workflow(name: str = "workflow", description: str = "") -> WorkflowGraph:
    """
    Create a new workflow graph.
    
    This is the main entry point for creating workflows.
    
    Example:
        ```python
        wf = workflow("my_workflow")
        n1 = wf.add_node(agent1, name="step1")
        n2 = wf.add_node(agent2, name="step2")
        wf.connect(n1, n2)
        wf.compile()
        result = wf.run("task")
        ```
    """
    return WorkflowGraph(name=name, description=description)
