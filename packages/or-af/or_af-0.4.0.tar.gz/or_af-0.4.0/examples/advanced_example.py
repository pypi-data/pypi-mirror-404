"""
Advanced Example: Showcasing all features of OR-AF (Operations Research Agentic Framework)

This demonstrates:
1. MCP Servers - The standard way to host and manage tools
2. Agents connected to MCP servers (no direct tool addition)
3. Workflow graphs - TensorFlow-like API for agent pipelines
4. A2A Protocol - Agent-to-Agent communication
5. Custom callbacks for observability
6. Conditional routing in workflows
"""

from or_af import (
    # Core
    Agent,
    MCPServer,
    
    # Workflow
    WorkflowGraph,
    Sequential,
    Parallel,
    EdgeCondition,
    workflow,
    
    # Callbacks & Models
    BaseCallback,
    AgentResponse
)
from or_af.models import ToolCall, ToolResult, IterationState
from or_af.a2a import A2AMessage, MessageType, AgentCard
import time


# =============================================================================
# STEP 1: Define Tool Functions
# =============================================================================

def calculator(operation: str, x: float, y: float) -> float:
    """Perform basic arithmetic operations."""
    if operation == "add":
        return x + y
    elif operation == "subtract":
        return x - y
    elif operation == "multiply":
        return x * y
    elif operation == "divide":
        if y == 0:
            raise ValueError("Division by zero")
        return x / y
    else:
        raise ValueError(f"Unknown operation: {operation}")


def get_time() -> str:
    """Get the current time."""
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")


def analyze_number(number: float) -> dict:
    """Analyze a number and return its properties."""
    import math
    return {
        "value": number,
        "is_positive": number > 0,
        "is_even": int(number) % 2 == 0 if number == int(number) else None,
        "square": number ** 2,
        "square_root": math.sqrt(number) if number >= 0 else None
    }


def summarize_results(data: str) -> str:
    """Summarize results into a concise format."""
    return f"Summary: {data}"


def validate_result(value: float) -> dict:
    """Validate a numerical result."""
    return {
        "value": value,
        "is_valid": value is not None,
        "in_range": 0 <= value <= 1000000 if value else False
    }


# =============================================================================
# STEP 2: Custom Callbacks
# =============================================================================

class MetricsCallback(BaseCallback):
    """Custom callback to collect metrics"""
    
    def __init__(self):
        self.tool_execution_times = []
        self.total_tools_called = 0
        self.errors = []
    
    def on_event(self, event):
        """Handle all events"""
        pass
    
    def on_tool_call_end(self, tool_result: ToolResult):
        self.tool_execution_times.append(tool_result.execution_time)
        self.total_tools_called += 1
    
    def on_tool_error(self, tool_name: str, error: str):
        self.errors.append({"tool": tool_name, "error": error})
    
    def print_metrics(self):
        print("\n" + "="*70)
        print("📊 EXECUTION METRICS")
        print("="*70)
        print(f"Total tools called: {self.total_tools_called}")
        if self.tool_execution_times:
            avg_time = sum(self.tool_execution_times) / len(self.tool_execution_times)
            print(f"Average tool execution time: {avg_time:.3f}s")
            print(f"Total tool execution time: {sum(self.tool_execution_times):.3f}s")
        print(f"Errors encountered: {len(self.errors)}")
        if self.errors:
            for err in self.errors:
                print(f"  - {err['tool']}: {err['error']}")
        print("="*70 + "\n")


# =============================================================================
# STEP 3: Create MCP Servers (Standard way to host tools)
# =============================================================================

def create_mcp_servers():
    """Create MCP servers with different tool categories."""
    
    # Calculator MCP Server
    calc_mcp = MCPServer(
        name="calculator_tools",
        description="Mathematical calculation tools"
    )
    calc_mcp.add_tool("calculator", calculator, "Perform arithmetic operations")
    calc_mcp.add_tool("analyze_number", analyze_number, "Analyze number properties")
    
    # Utility MCP Server
    util_mcp = MCPServer(
        name="utility_tools",
        description="Utility and helper tools"
    )
    util_mcp.add_tool("get_time", get_time, "Get current time")
    
    # Processing MCP Server
    proc_mcp = MCPServer(
        name="processing_tools",
        description="Data processing tools"
    )
    proc_mcp.add_tool("summarize_results", summarize_results, "Summarize data")
    proc_mcp.add_tool("validate_result", validate_result, "Validate results")
    
    # Using decorator style
    @proc_mcp.tool()
    def format_output(value: float, prefix: str = "Result") -> str:
        """Format output with a prefix"""
        return f"{prefix}: {value}"
    
    return calc_mcp, util_mcp, proc_mcp


# =============================================================================
# STEP 4: Create Agents connected to MCP Servers
# =============================================================================

def create_agents(calc_mcp, util_mcp, proc_mcp, metrics_callback):
    """Create specialized agents connected to different MCP servers."""
    
    # Calculator Agent
    calc_agent = Agent(
        name="calculator_agent",
        system_prompt="You are a mathematical calculation expert. Use your tools to perform calculations.",
        mcp_servers=[calc_mcp],  # Connect to calculator MCP
        callbacks=[metrics_callback],
        verbose=True
    )
    
    # Analyzer Agent - can access both calc and utility tools
    analyzer_agent = Agent(
        name="analyzer_agent",
        system_prompt="You are a data analysis expert. Analyze numbers and provide insights.",
        mcp_servers=[calc_mcp, util_mcp],  # Multiple MCP servers
        callbacks=[metrics_callback],
        verbose=True
    )
    
    # Processor Agent
    processor_agent = Agent(
        name="processor_agent",
        system_prompt="You are a data processor. Summarize and format results.",
        mcp_servers=[proc_mcp],
        callbacks=[metrics_callback],
        verbose=True
    )
    
    return calc_agent, analyzer_agent, processor_agent


# =============================================================================
# STEP 5: Create Workflow Graphs (TensorFlow-like API)
# =============================================================================

def create_linear_workflow(calc_agent, processor_agent):
    """
    Create a simple linear workflow.
    
    Similar to tf.keras.Sequential - agents execute in order.
    """
    print("\n📊 Creating Linear (Sequential) Workflow...")
    
    linear_wf = Sequential(
        agents=[calc_agent, processor_agent],
        name="linear_calculation_pipeline"
    )
    
    print(linear_wf.visualize())
    return linear_wf


def create_branching_workflow(calc_agent, analyzer_agent, processor_agent):
    """
    Create a workflow with conditional branching.
    
    This demonstrates how to create complex agent pipelines with
    conditional routing based on results.
    """
    print("\n📊 Creating Branching Workflow...")
    
    wf = WorkflowGraph(
        name="branching_analysis_pipeline",
        description="Workflow with conditional routing based on calculation results"
    )
    
    # Add nodes
    calc_node = wf.add_node(calc_agent, name="calculator", is_entry=True)
    analyzer_node = wf.add_node(analyzer_agent, name="analyzer")
    processor_node = wf.add_node(processor_agent, name="processor", is_exit=True)
    
    # Add conditional edges
    # Calculator -> Analyzer (always)
    wf.add_edge(calc_node, analyzer_node, condition=EdgeCondition.ON_SUCCESS)
    
    # Calculator -> Processor (on failure - skip analyzer)
    wf.add_edge(calc_node, processor_node, condition=EdgeCondition.ON_FAILURE)
    
    # Analyzer -> Processor
    wf.add_edge(analyzer_node, processor_node, condition=EdgeCondition.ON_SUCCESS)
    
    # Compile the workflow
    wf.compile()
    
    print(wf.visualize())
    return wf


def create_parallel_workflow(calc_agent, analyzer_agent, processor_agent):
    """
    Create a workflow with parallel execution.
    
    Multiple agents can process data in parallel before merging.
    """
    print("\n📊 Creating Parallel Workflow...")
    
    parallel_wf = Parallel(
        agents=[calc_agent, analyzer_agent],
        merge_agent=processor_agent,
        name="parallel_processing_pipeline"
    )
    
    print(parallel_wf.visualize())
    return parallel_wf


def create_custom_workflow():
    """
    Create a fully custom workflow using the workflow() helper.
    
    This shows the most flexible way to define complex agent graphs.
    """
    print("\n📊 Creating Custom Workflow with TensorFlow-like API...")
    
    # Create a simple function-based agent for demo
    def research_task(input_data):
        return f"Research complete: {input_data}"
    
    def review_task(input_data):
        return f"Review complete: {input_data}"
    
    def publish_task(input_data):
        return f"Published: {input_data}"
    
    # Use workflow() helper (similar to tf.function)
    wf = workflow("research_pipeline", description="Academic research workflow")
    
    # Add nodes
    researcher = wf.add_node(research_task, name="researcher", is_entry=True)
    reviewer = wf.add_node(review_task, name="reviewer")
    publisher = wf.add_node(publish_task, name="publisher", is_exit=True)
    
    # Chain using connect() for simple linear flow
    wf.connect(researcher, reviewer, publisher, condition=EdgeCondition.ON_SUCCESS)
    
    # Compile
    wf.compile()
    
    print(wf.visualize())
    
    # Execute the workflow
    print("\n🚀 Executing Custom Workflow...")
    result = wf.run("AI Research Topic")
    
    print(f"\n✅ Workflow completed!")
    print(f"   Success: {result['success']}")
    print(f"   Final outputs: {[r.output for r in result['final_outputs']]}")
    
    return wf


# =============================================================================
# STEP 6: Demonstrate A2A Protocol
# =============================================================================

def demonstrate_a2a_protocol():
    """Demonstrate Agent-to-Agent communication protocol."""
    print("\n" + "="*70)
    print("🔗 A2A (Agent-to-Agent) Protocol Demo")
    print("="*70)
    
    # Create agent cards (standard way to describe agent capabilities)
    calc_card = AgentCard(
        agent_id="calc-001",
        name="Calculator Agent",
        description="Performs mathematical calculations",
        capabilities=["arithmetic", "analysis"],
        tags=["math", "calculation"]
    )
    
    proc_card = AgentCard(
        agent_id="proc-001",
        name="Processor Agent",
        description="Processes and formats results",
        capabilities=["formatting", "summarization"],
        tags=["processing", "output"]
    )
    
    print(f"Agent Card 1: {calc_card.name}")
    print(f"  Capabilities: {calc_card.capabilities}")
    print(f"Agent Card 2: {proc_card.name}")
    print(f"  Capabilities: {proc_card.capabilities}")
    
    # Create A2A message
    message = A2AMessage(
        message_type=MessageType.REQUEST,
        source_agent_id=calc_card.agent_id,
        target_agent_id=proc_card.agent_id,
        task="Process calculation result",
        content={"result": 145, "operation": "addition"},
        context={"priority": "high"}
    )
    
    print(f"\nA2A Message:")
    print(f"  Type: {message.message_type}")
    print(f"  From: {message.source_agent_id} -> To: {message.target_agent_id}")
    print(f"  Task: {message.task}")
    print(f"  Content: {message.content}")
    
    # Create response
    response = message.create_response(
        responder_id=proc_card.agent_id,
        content="Processed: Result 145 from addition operation",
        success=True
    )
    
    print(f"\nA2A Response:")
    print(f"  Type: {response.message_type}")
    print(f"  Content: {response.content}")


# =============================================================================
# Main Execution
# =============================================================================

def main():
    print("\n" + "="*70)
    print("🚀 OR-AF Advanced Example: Complete Framework Demo")
    print("="*70)
    
    # Initialize metrics callback
    metrics = MetricsCallback()
    
    # Step 1: Create MCP Servers
    print("\n" + "-"*70)
    print("📦 CREATING MCP SERVERS (Standard way to host tools)")
    print("-"*70)
    calc_mcp, util_mcp, proc_mcp = create_mcp_servers()
    print(f"✓ Calculator MCP: {calc_mcp.list_tools()}")
    print(f"✓ Utility MCP: {util_mcp.list_tools()}")
    print(f"✓ Processing MCP: {proc_mcp.list_tools()}")
    
    # Step 2: Create Agents
    print("\n" + "-"*70)
    print("🤖 CREATING AGENTS (Connected to MCP servers)")
    print("-"*70)
    calc_agent, analyzer_agent, processor_agent = create_agents(
        calc_mcp, util_mcp, proc_mcp, metrics
    )
    print(f"✓ Calculator Agent - MCP servers: {calc_agent.list_mcp_servers()}")
    print(f"✓ Analyzer Agent - MCP servers: {analyzer_agent.list_mcp_servers()}")
    print(f"✓ Processor Agent - MCP servers: {processor_agent.list_mcp_servers()}")
    
    # Step 3: Create Workflows
    print("\n" + "-"*70)
    print("📊 CREATING WORKFLOW GRAPHS (TensorFlow-like API)")
    print("-"*70)
    
    linear_wf = create_linear_workflow(calc_agent, processor_agent)
    branching_wf = create_branching_workflow(calc_agent, analyzer_agent, processor_agent)
    parallel_wf = create_parallel_workflow(calc_agent, analyzer_agent, processor_agent)
    
    # Step 4: Custom Workflow with Execution
    print("\n" + "-"*70)
    print("🔧 CUSTOM WORKFLOW CREATION & EXECUTION")
    print("-"*70)
    create_custom_workflow()
    
    # Step 5: A2A Protocol Demo
    demonstrate_a2a_protocol()
    
    # Step 6: Run single agent task
    print("\n" + "="*70)
    print("🎯 RUNNING SINGLE AGENT TASK")
    print("="*70)
    
    response = calc_agent.run(
        "Calculate (15 * 8) + (100 / 4), then analyze the result.",
        stream=True
    )
    
    print("\n📈 Response Summary:")
    print(f"  - Iterations: {response.iteration_count}")
    print(f"  - Tools called: {response.total_tool_calls}")
    print(f"  - Duration: {response.total_duration:.2f}s")
    print(f"  - Success: {response.success}")
    
    # Print metrics
    metrics.print_metrics()
    
    print("\n" + "="*70)
    print("✅ Advanced Example Completed!")
    print("="*70)
    print("""
Key Takeaways:
1. Tools are registered with MCP Servers (not directly with agents)
2. Agents connect to MCP servers to access tools
3. Workflows are defined as graphs with agents as nodes
4. Conditional edges allow dynamic routing
5. A2A protocol enables agent-to-agent communication
6. TensorFlow-like API makes workflow definition intuitive
    """)


if __name__ == "__main__":
    main()
