# OR-AF (Operations Research Agentic Framework)

A powerful, production-ready framework for creating AI agent workflows with MCP (Model Context Protocol) server support, graph-based workflow definitions, A2A (Agent-to-Agent) protocol, and a TensorFlow-like API. Designed for operations research and complex multi-agent systems.

**v0.4.0**: Now uses the official [MCP SDK](https://modelcontextprotocol.io/) and [A2A SDK](https://a2a-protocol.org/)!

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- **🔌 Official MCP SDK**: Uses [mcp[cli]](https://modelcontextprotocol.io/) for standard protocol support
- **🤖 Official A2A SDK**: Uses [a2a-sdk](https://a2a-protocol.org/) for agent-to-agent communication
- **📊 TensorFlow-like API**: Intuitive Sequential, Parallel, and custom workflow definitions
- **🎯 Conditional Routing**: Dynamic workflow paths based on agent outputs
- **📈 Full Observability**: Custom callbacks for monitoring every step
- **🌊 Streaming Responses**: Real-time streaming of agent responses
- **📝 Comprehensive Logging**: Colored console logging and file logging
- **✅ Type Safety**: Built with Pydantic for full type validation

## 🚀 Installation

### From Source (Development)

```bash
git clone https://github.com/iaakashRoy/or-af.git
cd or-af
pip install -e .
```

### Using pip

```bash
pip install or-af
```

## 📋 Requirements

- Python 3.10+
- openai >= 1.0.0
- mcp[cli] >= 1.2.0 (Official MCP SDK)
- a2a-sdk[http-server] >= 0.3.0 (Official A2A SDK)
- pydantic >= 2.0.0
- httpx >= 0.23.0

## 🎯 Quick Start

### 1. Configure Environment

Create a `.env` file with your Azure OpenAI credentials:

```env
endpoint = "https://your-endpoint.openai.azure.com/"
deployment = "your-deployment-name"
subscription_key = "your-api-key"
api_version = "2024-12-01-preview"
```

### 2. Create MCP Server with Tools (Using Official MCP SDK)

```python
from or_af import create_mcp_server

# Create an MCP server (wraps official mcp.server.FastMCP)
server = create_mcp_server(name="math_tools", description="Mathematical tools")

# Add tools using decorator (official MCP SDK pattern)
@server.tool()
def add(x: float, y: float) -> float:
    """Add two numbers"""
    return x + y

@server.tool()
def multiply(x: float, y: float) -> float:
    """Multiply two numbers"""
    return x * y

# Add resources (official MCP SDK feature)
@server.resource("config://math")
def get_config() -> str:
    """Get math configuration"""
    return '{"precision": 2}'

# Add prompts (official MCP SDK feature)
@server.prompt(title="Math Helper")
def math_prompt(expression: str) -> str:
    """Generate a math helper prompt"""
    return f"Please help me calculate: {expression}"
```

### 3. Create Agent Connected to MCP Server

```python
from or_af import Agent

# Agents access tools through MCP servers
agent = Agent(
    name="math_agent",
    system_prompt="You are a helpful math assistant.",
    mcp_servers=[server],  # Connect to MCP server(s)
    stream=True,
    verbose=True
)
```

### 4. Run Tasks

```python
response = agent.run("What is 25 multiplied by 4?")

print(f"Success: {response.success}")
print(f"Response: {response.response}")
print(f"Iterations: {response.iteration_count}")
```

## 🏗️ Architecture

### Key Concepts

1. **MCP Servers**: Host and manage tools (tools can't be added directly to agents)
2. **Agents**: Connect to MCP servers to access tools
3. **Workflow Graphs**: Define agent pipelines with conditional routing
4. **A2A Protocol**: Standard format for inter-agent communication

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ MCP Server 1│     │ MCP Server 2│     │ MCP Server 3│
│  (Math)     │     │  (Utility)  │     │ (Processing)│
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────┬───────┴───────────┬───────┘
                   │                   │
              ┌────▼────┐         ┌────▼────┐
              │ Agent 1 │◄──A2A──►│ Agent 2 │
              └────┬────┘         └────┬────┘
                   │                   │
                   └─────────┬─────────┘
                             │
                    ┌────────▼────────┐
                    │  Workflow Graph │
                    │  (Conditional   │
                    │   Routing)      │
                    └─────────────────┘
```

## 📊 Workflow Graphs (TensorFlow-like API)

### Sequential Workflow

```python
from or_af import Sequential

# Linear pipeline - agents execute in order
workflow = Sequential(
    agents=[agent1, agent2, agent3],
    name="my_pipeline"
)

result = workflow.run("Initial task")
```

### Custom Graph Workflow

```python
from or_af import WorkflowGraph, EdgeCondition

# Create custom workflow with conditional routing
wf = WorkflowGraph(name="research_pipeline")

# Add agents as nodes
researcher = wf.add_node(research_agent, name="researcher", is_entry=True)
reviewer = wf.add_node(review_agent, name="reviewer")
publisher = wf.add_node(publish_agent, name="publisher", is_exit=True)

# Add conditional edges
wf.add_edge(researcher, reviewer, condition=EdgeCondition.ON_SUCCESS)
wf.add_edge(researcher, publisher, condition=EdgeCondition.ON_FAILURE)
wf.add_edge(reviewer, publisher, condition=EdgeCondition.ON_SUCCESS)

# Compile and run
wf.compile()
result = wf.run("Research AI trends")
```

### Parallel Workflow

```python
from or_af import Parallel

# Parallel execution with merge
workflow = Parallel(
    agents=[analyst1, analyst2, analyst3],
    merge_agent=summarizer,
    name="parallel_analysis"
)

result = workflow.run("Analyze data from multiple perspectives")
```

### Using workflow() Helper (Most Flexible)

```python
from or_af import workflow, EdgeCondition

wf = workflow("my_workflow")

# Add nodes
n1 = wf.add_node(agent1, name="step1", is_entry=True)
n2 = wf.add_node(agent2, name="step2")
n3 = wf.add_node(agent3, name="step3", is_exit=True)

# Chain nodes
wf.connect(n1, n2, n3, condition=EdgeCondition.ON_SUCCESS)

# Or create branches
wf.branch(n1, [
    (n2, lambda x: x.success),      # Go to n2 if success
    (n3, lambda x: not x.success)   # Go to n3 if failure
])

wf.compile()
result = wf.run("Task")
```

## 🔗 A2A Protocol (Using Official A2A SDK)

Create A2A-compliant agents that can communicate with agents built using any framework:

```python
from or_af import create_a2a_agent, SimpleA2AExecutor

# Define your agent's logic
async def handle_message(message: str) -> str:
    """Process incoming messages."""
    return f"Processed: {message}"

# Create an A2A agent (wraps official a2a-sdk)
agent = create_a2a_agent(
    name="My Agent",
    description="A helpful agent",
    skills=[
        {
            "id": "process",
            "name": "Message Processor",
            "description": "Processes incoming messages",
            "tags": ["process", "message"]
        }
    ],
    input_modes=["text"],
    output_modes=["text"]
)

# Set the executor
agent.set_executor(SimpleA2AExecutor(handle_message))

# Run the agent server (FastAPI-based)
# agent.run(port=9999)  # Accessible at http://localhost:9999/

# Access agent card for discovery
print(f"Agent: {agent.card.name}")
print(f"Skills: {[s.name for s in agent.card.skills]}")
print(f"Streaming: {agent.card.capabilities.streaming}")
```

### Custom A2A Executor

```python
from or_af import BaseA2AExecutor, new_agent_text_message

class MyExecutor(BaseA2AExecutor):
    async def execute(self, context, event_queue):
        # Get the user's message
        user_message = self.get_user_message(context)
        
        # Process and respond
        response = f"You said: {user_message}"
        await event_queue.enqueue_event(new_agent_text_message(response))
    
    async def cancel(self, context, event_queue):
        raise Exception("Cancel not supported")

agent.set_executor(MyExecutor())
```

## 🎨 Custom Callbacks

```python
from or_af import BaseCallback
from or_af.models import ToolCall, ToolResult

class MetricsCallback(BaseCallback):
    def __init__(self):
        self.tool_calls = 0
    
    def on_tool_call_start(self, tool_call: ToolCall):
        print(f"Starting: {tool_call.name}")
    
    def on_tool_call_end(self, tool_result: ToolResult):
        self.tool_calls += 1
        print(f"Completed in {tool_result.execution_time:.3f}s")

# Use callback
agent = Agent(
    system_prompt="...",
    mcp_servers=[mcp],
    callbacks=[MetricsCallback()]
)
```

## 📚 Complete Example

```python
from or_af import (
    MCPServer, Agent, WorkflowGraph, 
    Sequential, EdgeCondition
)

# 1. Create MCP servers with tools
math_mcp = MCPServer(name="math")

@math_mcp.tool()
def calculate(x: float, y: float, op: str) -> float:
    """Perform calculation"""
    ops = {"add": x + y, "sub": x - y, "mul": x * y}
    return ops.get(op, 0)

format_mcp = MCPServer(name="format")
format_mcp.add_tool("format_result", lambda x: f"Result: {x}")

# 2. Create agents connected to MCP servers
calculator = Agent(
    name="calculator",
    system_prompt="You are a calculator.",
    mcp_servers=[math_mcp]
)

formatter = Agent(
    name="formatter", 
    system_prompt="Format results nicely.",
    mcp_servers=[format_mcp]
)

# 3. Create workflow graph
wf = WorkflowGraph(name="calc_pipeline")
calc_node = wf.add_node(calculator, is_entry=True)
format_node = wf.add_node(formatter, is_exit=True)
wf.add_edge(calc_node, format_node, condition=EdgeCondition.ON_SUCCESS)
wf.compile()

# 4. Run workflow
result = wf.run("Calculate 15 * 8 and format the result")
print(result)
```

## 🧪 Running Examples

```bash
# Simple example
python examples/simple_example.py

# Advanced example with all features
python examples/advanced_example.py
```

## 📊 Edge Conditions

| Condition | Description |
|-----------|-------------|
| `EdgeCondition.ALWAYS` | Always traverse this edge |
| `EdgeCondition.ON_SUCCESS` | Traverse only if previous node succeeded |
| `EdgeCondition.ON_FAILURE` | Traverse only if previous node failed |
| `EdgeCondition.ON_CONDITION` | Custom condition function |

## 🔧 Configuration

```python
# MCP Server Config
mcp = MCPServer(
    name="my_server",
    host="localhost",
    port=8000,
    description="My tools server"
)

# Agent Config
agent = Agent(
    name="my_agent",
    system_prompt="Your prompt",
    model_name="gpt-4",
    temperature=1.0,
    max_iterations=10,
    stream=True,
    verbose=True,
    mcp_servers=[mcp1, mcp2],
    callbacks=[MyCallback()]
)
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For issues, questions, or contributions, please visit our [GitHub repository](https://github.com/iaakashRoy/or-af).