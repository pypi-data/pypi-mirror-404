# OR-AF (Operations Research Agentic Framework)

A lightweight, production-ready framework for creating AI agents with tool-calling capabilities, streaming support, comprehensive logging, and full observability. Designed for operations research and optimization tasks.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- **🔧 Tool Support**: Easy tool registration with automatic schema generation
- **📊 Full Observability**: Custom callbacks for monitoring every step
- **🌊 Streaming Responses**: Real-time streaming of agent responses
- **📝 Comprehensive Logging**: Colored console logging and file logging
- **✅ Type Safety**: Built with Pydantic for full type validation
- **⚡ Lightweight**: Minimal dependencies, maximum performance
- **🎯 Simple API**: Intuitive interface inspired by popular frameworks
- **🔍 Error Handling**: Robust error handling with custom exceptions
- **📈 Metrics**: Built-in execution metrics and performance tracking

## 🚀 Installation

### From Source (Development)

### From Source (Development)

```bash
git clone https://github.com/iaakashRoy/or-af.git
cd or-af
pip install -e .
```

### Using pip (when published)

```bash
pip install or-af
```

## 📋 Requirements

- Python 3.8+
- openai >= 1.0.0
- python-dotenv >= 1.0.0
- pydantic >= 2.0.0

## 🎯 Quick Start

### 1. Configure Environment

Create a `.env` file with your Azure OpenAI credentials:

```env
endpoint = "https://your-endpoint.openai.azure.com/"
deployment = "your-deployment-name"
subscription_key = "your-api-key"
api_version = "2024-12-01-preview"
```

### 2. Create Your First Agent

```python
from or_af import Agent

# Initialize agent with a system prompt
agent = Agent(
    system_prompt="You are a helpful AI assistant.",
    max_iterations=10,
    stream=True,  # Enable streaming
    verbose=True  # Enable detailed logging
)
```

### 3. Add Tools

```python
def calculator(operation: str, x: float, y: float) -> float:
    """Perform basic arithmetic operations."""
    if operation == "add":
        return x + y
    elif operation == "multiply":
        return x * y
    # ... more operations

# Register the tool
agent.add_tool("calculator", calculator, "Perform arithmetic calculations")
```

### 4. Run Tasks

```python
# Run with streaming (default)
response = agent.run("What is 25 multiplied by 4?")

# Access detailed response
print(f"Success: {response.success}")
print(f"Response: {response.response}")
print(f"Iterations: {response.iteration_count}")
print(f"Tools called: {response.total_tool_calls}")
print(f"Duration: {response.total_duration:.2f}s")
```

## 🎨 Advanced Features

### Custom Callbacks for Observability

```python
from or_af import BaseCallback, Agent
from or_af.models import ToolCall, ToolResult

class MyCustomCallback(BaseCallback):
    """Track custom metrics"""
    
    def on_tool_call_start(self, tool_call: ToolCall):
        print(f"Tool starting: {tool_call.name}")
    
    def on_tool_call_end(self, tool_result: ToolResult):
        print(f"Tool completed in {tool_result.execution_time:.3f}s")
    
    def on_thinking(self, iteration: int, thinking: str):
        print(f"Agent is thinking: {thinking}")

# Use custom callback
agent = Agent(
    system_prompt="You are helpful",
    callbacks=[MyCustomCallback()]
)
```

### Streaming vs Non-Streaming

```python
# Streaming mode (real-time output)
response = agent.run("Calculate something", stream=True)

# Non-streaming mode
response = agent.run("Calculate something", stream=False)
```

### Access Detailed Execution Info

```python
response = agent.run("Complex task")

# Iterate through each iteration
for iteration in response.iterations:
    print(f"Iteration {iteration.iteration_number}:")
    print(f"  Duration: {iteration.duration:.2f}s")
    print(f"  Tools called: {len(iteration.tool_calls)}")
    
    for tool_call in iteration.tool_calls:
        print(f"    - {tool_call.name}({tool_call.arguments})")
```

### Custom Logging

```python
from or_af import setup_logger
from pathlib import Path
import logging

# Setup custom logger
logger = setup_logger(
    name="my_agent",
    level=logging.DEBUG,
    log_file=Path("agent.log"),
    use_colors=True
)

# Use with agent
from or_af.callbacks import LoggingCallback
agent = Agent(
    system_prompt="You are helpful",
    callbacks=[LoggingCallback(logger)]
)
```

## 📚 Examples

### Example 1: Simple Calculator

```python
from or_af import Agent

def add(x: float, y: float) -> float:
    """Add two numbers"""
    return x + y

def multiply(x: float, y: float) -> float:
    """Multiply two numbers"""
    return x * y

agent = Agent(system_prompt="You are a math assistant")
agent.add_tool("add", add)
agent.add_tool("multiply", multiply)

response = agent.run("What is (25 + 75) * 2?")
print(response.response)
```

### Example 2: With Error Handling

```python
from or_af import Agent, ToolExecutionError

def divide(x: float, y: float) -> float:
    """Divide two numbers"""
    if y == 0:
        raise ValueError("Cannot divide by zero")
    return x / y

agent = Agent(system_prompt="You are a calculator")
agent.add_tool("divide", divide)

try:
    response = agent.run("Divide 100 by 0")
    if not response.success:
        print(f"Error: {response.error_message}")
except Exception as e:
    print(f"Exception: {e}")
```

## 🏗️ Architecture

### Core Components

1. **Agent**: Main orchestrator that manages conversation flow
2. **Tool**: Wraps Python functions with automatic schema generation
3. **CallbackManager**: Handles observability callbacks
4. **Models**: Pydantic models for type safety and validation
5. **Logger**: Colored console and file logging

### Execution Flow

```
User Task → Agent
    ↓
Agent analyzes task
    ↓
Decides which tools to use
    ↓
Executes tools (with callbacks)
    ↓
Synthesizes response
    ↓
Returns AgentResponse
```

## 📊 Models

### AgentResponse

```python
response = agent.run("task")

# Access properties
response.task              # Original task
response.response          # Final response
response.iterations        # List[IterationState]
response.total_tool_calls  # Number of tools called
response.success           # bool
response.error_message     # Optional error
response.total_duration    # Execution time in seconds
```

### IterationState

```python
for iteration in response.iterations:
    iteration.iteration_number  # int
    iteration.tool_calls        # List[ToolCall]
    iteration.tool_results      # List[ToolResult]
    iteration.thinking          # Agent's reasoning
    iteration.response          # Final response if last iteration
    iteration.duration          # Execution time
```

## 🔧 Configuration

### AgentConfig

```python
agent = Agent(
    system_prompt="Your prompt",      # Required
    model_name="gpt-4",               # Optional, defaults to env
    temperature=1.0,                   # 0.0 to 2.0
    max_iterations=10,                 # Max tool-call loops
    stream=True,                       # Enable streaming
    verbose=True                       # Enable console output
)
```

## 🧪 Running Examples

```bash
# Simple example
python examples/simple_example.py

# Advanced example with all features
python examples/advanced_example.py

# Jupyter notebook
jupyter notebook examples/advanced_example.ipynb
```

## 📝 Logging Levels

- **DEBUG**: Detailed execution information
- **INFO**: General information about operations
- **WARNING**: Warning messages
- **ERROR**: Error messages with stack traces

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [OpenAI](https://openai.com/) for LLM capabilities
- Uses [Pydantic](https://pydantic-docs.helpmanual.io/) for data validation
- Inspired by LangChain and other agent frameworks

## 📞 Support

For issues, questions, or contributions, please visit our [GitHub repository](https://github.com/iaakashRoy/or-af).