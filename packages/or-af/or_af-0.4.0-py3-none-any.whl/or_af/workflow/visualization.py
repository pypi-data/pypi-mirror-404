"""
OR-AF Workflow - Visualization module

Provides various visualization formats for workflow graphs including
text-based, ASCII art, and Mermaid diagram outputs.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .graph import WorkflowGraph
    from .nodes import Node


class WorkflowVisualizer:
    """
    Visualizes workflow graphs in various formats.
    
    Supports:
    - text: Simple text representation
    - ascii: ASCII art diagram
    - mermaid: Mermaid diagram syntax for rendering
    """
    
    def __init__(self, workflow: "WorkflowGraph"):
        self.workflow = workflow
    
    def render(self, format: str = "text", show_details: bool = True) -> str:
        """
        Render the workflow visualization.
        
        Args:
            format: Output format ('text', 'ascii', 'mermaid')
            show_details: Include MCP servers and tools
            
        Returns:
            String visualization
        """
        if format == "text":
            return self._render_text(show_details)
        elif format == "ascii":
            return self._render_ascii(show_details)
        elif format == "mermaid":
            return self._render_mermaid(show_details)
        else:
            raise ValueError(f"Unknown format: {format}. Use 'text', 'ascii', or 'mermaid'")
    
    def _render_text(self, show_details: bool = True) -> str:
        """Render as plain text"""
        wf = self.workflow
        lines = [
            "=" * 60,
            f"📊 Workflow: {wf.name}",
            "=" * 60,
        ]
        
        if wf.description:
            lines.append(f"📝 Description: {wf.description}")
        
        lines.extend([
            f"🔢 Nodes: {len(wf.nodes)} | Edges: {len(wf.edges)}",
            "",
            "🔷 NODES:",
            "-" * 40
        ])
        
        for node in wf.nodes.values():
            entry_marker = " 🚀[ENTRY]" if node == wf.entry_node else ""
            exit_marker = " 🏁[EXIT]" if node.node_id in wf.exit_nodes else ""
            status_icon = self._get_status_icon(node.status.value)
            lines.append(f"  {status_icon} {node.name}{entry_marker}{exit_marker}")
            
            if show_details:
                agent = node.agent
                if hasattr(agent, '_mcp_servers') and agent._mcp_servers:
                    lines.append(f"      📡 MCP Servers:")
                    for server_name, client in agent._mcp_servers.items():
                        lines.append(f"          └─ {server_name}")
                        if hasattr(client, 'get_tools_schema'):
                            tools = client.get_tools_schema()
                            if tools:
                                for tool in tools:
                                    tool_name = tool.get('function', {}).get('name', 'unknown')
                                    lines.append(f"              └─ 🔧 {tool_name}")
        
        lines.extend([
            "",
            "🔗 EDGES:",
            "-" * 40
        ])
        
        for edge in wf.edges:
            condition_icon = self._get_condition_icon(edge.condition_type.value)
            lines.append(f"  {edge.source.name} {condition_icon}──▶ {edge.target.name}")
            lines.append(f"      Condition: {edge.condition_type.value}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def _render_ascii(self, show_details: bool = True) -> str:
        """Render as ASCII art diagram"""
        wf = self.workflow
        lines = []
        
        # Header
        title = f" {wf.name} "
        lines.append("+" + "=" * 58 + "+")
        lines.append("|" + title.center(58) + "|")
        lines.append("+" + "=" * 58 + "+")
        lines.append("")
        
        # Build graph representation
        node_list = list(wf.nodes.values())
        node_positions: Dict[str, int] = {}
        
        # Simple layout: entry node first, then others
        if wf.entry_node:
            sorted_nodes = [wf.entry_node] + [n for n in node_list if n != wf.entry_node]
        else:
            sorted_nodes = node_list
        
        for i, node in enumerate(sorted_nodes):
            node_positions[node.node_id] = i
            
            # Node box
            entry_mark = "[ENTRY]" if node == wf.entry_node else ""
            exit_mark = "[EXIT]" if node.node_id in wf.exit_nodes else ""
            
            node_label = f"{node.name} {entry_mark}{exit_mark}".strip()
            box_width = max(len(node_label) + 4, 20)
            
            lines.append("+" + "-" * (box_width - 2) + "+")
            lines.append("|" + node_label.center(box_width - 2) + "|")
            
            if show_details:
                agent = node.agent
                if hasattr(agent, '_mcp_servers') and agent._mcp_servers:
                    for server_name, client in agent._mcp_servers.items():
                        mcp_line = f"[MCP: {server_name}]"
                        lines.append("|" + mcp_line.center(box_width - 2) + "|")
                        
                        if hasattr(client, 'get_tools_schema'):
                            tools = client.get_tools_schema()
                            if tools:
                                for tool in tools:
                                    tool_name = tool.get('function', {}).get('name', '?')
                                    tool_line = f"  > {tool_name}"
                                    if len(tool_line) > box_width - 4:
                                        tool_line = tool_line[:box_width-7] + "..."
                                    lines.append("|" + tool_line.ljust(box_width - 2) + "|")
            
            lines.append("+" + "-" * (box_width - 2) + "+")
            
            # Draw edges from this node
            outgoing = [e for e in wf.edges if e.source.node_id == node.node_id]
            for edge in outgoing:
                condition = edge.condition_type.value
                lines.append(f"     |")
                lines.append(f"     | ({condition})")
                lines.append(f"     v")
            
            if not outgoing and node.node_id not in wf.exit_nodes:
                lines.append("")
        
        return "\n".join(lines)
    
    def _render_mermaid(self, show_details: bool = True) -> str:
        """Render as Mermaid diagram syntax"""
        wf = self.workflow
        lines = [
            "```mermaid",
            "flowchart TD",
        ]
        
        # Define subgraphs for MCP servers if showing details
        mcp_subgraphs: Dict[str, List[str]] = {}
        
        # Add nodes
        for node in wf.nodes.values():
            node_id = node.name.replace(" ", "_").replace("-", "_")
            
            if node == wf.entry_node:
                lines.append(f'    {node_id}[["🚀 {node.name}"]]')
            elif node.node_id in wf.exit_nodes:
                lines.append(f'    {node_id}(("{node.name} 🏁"))')
            else:
                lines.append(f'    {node_id}["{node.name}"]')
            
            # Collect MCP server info
            if show_details:
                agent = node.agent
                if hasattr(agent, '_mcp_servers') and agent._mcp_servers:
                    for server_name, client in agent._mcp_servers.items():
                        safe_server = server_name.replace(" ", "_").replace("-", "_")
                        if safe_server not in mcp_subgraphs:
                            mcp_subgraphs[safe_server] = []
                        
                        if hasattr(client, 'get_tools_schema'):
                            tools = client.get_tools_schema()
                            if tools:
                                for tool in tools:
                                    tool_name = tool.get('function', {}).get('name', 'tool')
                                    mcp_subgraphs[safe_server].append(tool_name)
        
        lines.append("")
        
        # Add edges
        for edge in wf.edges:
            source_id = edge.source.name.replace(" ", "_").replace("-", "_")
            target_id = edge.target.name.replace(" ", "_").replace("-", "_")
            condition = edge.condition_type.value
            
            if condition == "always":
                lines.append(f'    {source_id} --> {target_id}')
            else:
                lines.append(f'    {source_id} -->|{condition}| {target_id}')
        
        # Add MCP server subgraphs
        if show_details and mcp_subgraphs:
            lines.append("")
            for server_name, tools in mcp_subgraphs.items():
                lines.append(f'    subgraph {server_name}["📡 MCP: {server_name}"]')
                for i, tool in enumerate(tools):
                    safe_tool = f"{server_name}_{tool.replace(' ', '_')}_{i}"
                    lines.append(f'        {safe_tool}["🔧 {tool}"]')
                lines.append('    end')
        
        # Styling
        lines.extend([
            "",
            "    %% Styling",
            "    classDef entry fill:#90EE90,stroke:#228B22",
            "    classDef exit fill:#FFB6C1,stroke:#DC143C",
            "    classDef mcp fill:#E6E6FA,stroke:#9370DB",
        ])
        
        lines.append("```")
        
        return "\n".join(lines)
    
    def _get_status_icon(self, status: str) -> str:
        """Get icon for node status"""
        icons = {
            "pending": "⏳",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
            "skipped": "⏭️"
        }
        return icons.get(status, "❓")
    
    def _get_condition_icon(self, condition: str) -> str:
        """Get icon for edge condition"""
        icons = {
            "always": "──",
            "on_success": "✅",
            "on_failure": "❌",
            "on_condition": "❓"
        }
        return icons.get(condition, "──")


def visualize_workflow(
    workflow: "WorkflowGraph",
    format: str = "text",
    show_details: bool = True
) -> str:
    """
    Convenience function to visualize a workflow.
    
    Args:
        workflow: The workflow graph to visualize
        format: Output format ('text', 'ascii', 'mermaid')
        show_details: Include MCP servers and tools
        
    Returns:
        String visualization
        
    Example:
        ```python
        print(visualize_workflow(my_workflow, format="mermaid"))
        ```
    """
    visualizer = WorkflowVisualizer(workflow)
    return visualizer.render(format=format, show_details=show_details)
