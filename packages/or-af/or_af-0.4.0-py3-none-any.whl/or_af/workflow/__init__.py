"""
OR-AF Workflow Module

TensorFlow-like API for defining agent workflows as directed graphs.
"""

from .nodes import (
    Node,
    NodeStatus,
    NodeResult,
    EdgeCondition,
    EdgeConfig,
    ConditionalEdge
)
from .graph import WorkflowGraph
from .builders import Sequential, Parallel, workflow
from .visualization import WorkflowVisualizer, visualize_workflow

__all__ = [
    # Node components
    "Node",
    "NodeStatus",
    "NodeResult",
    "EdgeCondition",
    "EdgeConfig",
    "ConditionalEdge",
    # Graph
    "WorkflowGraph",
    # Builders (TensorFlow-like API)
    "Sequential",
    "Parallel",
    "workflow",
    # Visualization
    "WorkflowVisualizer",
    "visualize_workflow",
]
