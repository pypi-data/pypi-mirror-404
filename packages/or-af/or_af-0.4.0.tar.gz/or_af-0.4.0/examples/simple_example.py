"""
Simple example demonstrating OR-AF (Operations Research Agentic Framework)

This example shows the new architecture:
1. Create tools and add them to MCP servers (standard way to manage tools)
2. Create agents that connect to MCP servers (agents can't have tools directly)
3. Define workflows as graphs with agents as nodes and conditional edges
4. TensorFlow-like API for defining workflows
"""

from or_af import (
    Agent,
    MCPServer,
    WorkflowGraph,
    Sequential,
    EdgeCondition,
    workflow
)


# =============================================================================
# Step 1: Define tool functions
# =============================================================================

def get_square(number: float) -> float:
    """Calculate the square of a number."""
    return number ** 2


def get_sum(x: float, y: float) -> float:
    """Add two numbers together."""
    return x + y


def get_product(x: float, y: float) -> float:
    """Multiply two numbers together."""
    return x * y


def format_result(value: float) -> str:
    """Format a numerical result with explanation."""
    return f"The final result is: {value}"


# =============================================================================
# Step 2: Create MCP Servers and register tools (THE STANDARD WAY)
# =============================================================================

def create_mcp_servers():
    """Create MCP servers with tools."""
    
    # Math operations MCP server
    math_mcp = MCPServer(
        name="math_tools",
        description="Mathematical operations server"
    )
    
    # Add tools using decorator style
    @math_mcp.tool()
    def calculate_square(number: float) -> float:
        """Calculate the square of a number"""
        return number ** 2
    
    # Add tools using method call
    math_mcp.add_tool("get_sum", get_sum, "Add two numbers")
    math_mcp.add_tool("get_product", get_product, "Multiply two numbers")
    
    # Formatting MCP server
    format_mcp = MCPServer(
        name="format_tools",
        description="Formatting utilities server"
    )
    format_mcp.add_tool("format_result", format_result, "Format numerical results")
    
    print(f"✓ Created MCP server: {math_mcp.name} with tools: {math_mcp.list_tools()}")
    print(f"✓ Created MCP server: {format_mcp.name} with tools: {format_mcp.list_tools()}")
    
    return math_mcp, format_mcp


# =============================================================================
# Step 3: Create Agents connected to MCP servers
# =============================================================================

def create_agents(math_mcp, format_mcp):
    """Create agents connected to MCP servers."""
    
    # Math agent - connects to math MCP server
    math_agent = Agent(
        name="math_agent",
        system_prompt="You are a helpful math assistant. Use your tools to solve problems.",
        mcp_servers=[math_mcp]  # Agents take MCP servers, NOT tools directly
    )
    
    # Formatter agent - connects to format MCP server
    formatter_agent = Agent(
        name="formatter_agent",
        system_prompt="You are a formatting assistant. Format results nicely.",
        mcp_servers=[format_mcp]
    )
    
    print(f"✓ Created agent: {math_agent.name}")
    print(f"  Connected MCP servers: {math_agent.list_mcp_servers()}")
    print(f"  Available tools: {math_agent.list_available_tools()}")
    
    return math_agent, formatter_agent


# =============================================================================
# Step 4: Define Workflows as Graphs (TensorFlow-like API)
# =============================================================================

def create_workflow(math_agent, formatter_agent):
    """
    Create a workflow graph connecting agents.
    
    Workflows are defined similar to TensorFlow neural networks:
    - Agents are nodes
    - Conditional edges connect agents
    - Data flows through the graph
    """
    
    # Method 1: Using WorkflowGraph directly (most flexible)
    wf = WorkflowGraph(name="math_pipeline", description="A math processing pipeline")
    
    # Add agents as nodes
    math_node = wf.add_node(math_agent, name="calculator", is_entry=True)
    format_node = wf.add_node(formatter_agent, name="formatter", is_exit=True)
    
    # Connect with conditional edges
    wf.add_edge(
        math_node, 
        format_node, 
        condition=EdgeCondition.ON_SUCCESS  # Only proceed if math succeeds
    )
    
    # Compile the workflow
    wf.compile()
    
    print(f"\n✓ Created workflow: {wf.name}")
    print(wf.visualize())
    
    return wf


def create_sequential_workflow(math_agent, formatter_agent):
    """
    Create a sequential workflow (simpler API).
    
    This is similar to tf.keras.Sequential for linear pipelines.
    """
    
    # Method 2: Using Sequential (for linear workflows)
    seq_wf = Sequential(
        agents=[math_agent, formatter_agent],
        name="sequential_math_pipeline"
    )
    
    print(f"\n✓ Created sequential workflow: {seq_wf.name}")
    print(seq_wf.visualize())
    
    return seq_wf


# =============================================================================
# Main execution
# =============================================================================

def main():
    print("\n" + "="*70)
    print("🚀 OR-AF Framework Demo: MCP Servers, Agents & Workflow Graphs")
    print("="*70)
    
    # Step 1: Create MCP servers with tools
    print("\n📦 STEP 1: Creating MCP Servers (standard way to host tools)")
    print("-"*70)
    math_mcp, format_mcp = create_mcp_servers()
    
    # Step 2: Create agents connected to MCP servers
    print("\n🤖 STEP 2: Creating Agents (connect to MCP servers, not tools)")
    print("-"*70)
    math_agent, formatter_agent = create_agents(math_mcp, format_mcp)
    
    # Step 3: Create workflow graph
    print("\n📊 STEP 3: Creating Workflow Graph (TensorFlow-like API)")
    print("-"*70)
    wf = create_workflow(math_agent, formatter_agent)
    
    # Alternative: Sequential workflow
    print("\n📊 STEP 3b: Alternative Sequential Workflow")
    print("-"*70)
    seq_wf = create_sequential_workflow(math_agent, formatter_agent)
    
    # Step 4: Run a task through the single agent (traditional way)
    print("\n" + "="*70)
    print("🎯 RUNNING TASK: Single Agent")
    print("="*70)
    
    task = "What is the square of 12, and then add 5 to that result?"
    result = math_agent.run(task)
    
    print("\n" + "="*70)
    print("✅ TASK COMPLETED!")
    print("="*70)
    
    # Note: Full workflow execution requires all agents to be properly configured
    # This example demonstrates the structure and API


if __name__ == "__main__":
    main()

