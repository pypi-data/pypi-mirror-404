"""
Advanced Example: Showcasing all features of OR-AF (Operations Research Agentic Framework)
- Custom callbacks for observability
- Streaming responses
- Logging
- Error handling
- Multiple tools
"""

from or_af import Agent, BaseCallback, AgentResponse
from or_af.models import ToolCall, ToolResult, IterationState
import time


# Define tools
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


# Custom callback to track metrics
class MetricsCallback(BaseCallback):
    """Custom callback to collect metrics"""
    
    def __init__(self):
        self.tool_execution_times = []
        self.total_tools_called = 0
        self.errors = []
    
    def on_event(self, event):
        """Handle all events"""
        pass  # We handle specific events below
    
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


def main():
    print("🚀 OR-AF (Operations Research Agentic Framework) - Advanced Example\n")
    
    # Initialize custom callback
    metrics = MetricsCallback()
    
    # Initialize agent with custom callback
    agent = Agent(
        system_prompt="You are a helpful AI assistant with access to various tools. "
                     "Use them to solve problems step by step.",
        temperature=1.0,
        max_iterations=15,
        stream=True,  # Enable streaming
        verbose=True,
        callbacks=[metrics]  # Add custom callback
    )
    
    # Register tools
    agent.add_tool("calculator", calculator, "Perform arithmetic operations")
    agent.add_tool("get_time", get_time, "Get current time")
    agent.add_tool("analyze_number", analyze_number, "Analyze number properties")
    
    print("\n" + "="*70)
    print("TEST 1: Multi-step calculation with streaming")
    print("="*70)
    
    # Test 1: Complex calculation
    response1: AgentResponse = agent.run(
        "Calculate (15 * 8) + (100 / 4), then analyze the result. "
        "What time is it now?",
        stream=True
    )
    
    print("\n📈 Response Summary:")
    print(f"  - Iterations: {response1.iteration_count}")
    print(f"  - Tools called: {response1.total_tool_calls}")
    print(f"  - Duration: {response1.total_duration:.2f}s")
    print(f"  - Success: {response1.success}")
    
    # Print metrics
    metrics.print_metrics()
    
    print("\n" + "="*70)
    print("TEST 2: Error handling")
    print("="*70)
    
    # Test 2: Division by zero to test error handling
    response2: AgentResponse = agent.run(
        "Try to divide 100 by 0",
        stream=True
    )
    
    print("\n📈 Response Summary:")
    print(f"  - Iterations: {response2.iteration_count}")
    print(f"  - Success: {response2.success}")
    if response2.error_message:
        print(f"  - Error: {response2.error_message}")
    
    # Print final metrics
    metrics.print_metrics()
    
    print("\n" + "="*70)
    print("TEST 3: Non-streaming mode")
    print("="*70)
    
    # Test 3: Non-streaming
    response3: AgentResponse = agent.run(
        "What is 25 + 75?",
        stream=False  # Disable streaming for this call
    )
    
    print("\n📈 Response Summary:")
    print(f"  - Response: {response3.response}")
    print(f"  - Duration: {response3.total_duration:.2f}s")
    
    # Access detailed iteration information
    print("\n📝 Detailed Iteration Breakdown:")
    for iteration in response3.iterations:
        print(f"\n  Iteration {iteration.iteration_number}:")
        if iteration.thinking:
            print(f"    Thinking: {iteration.thinking[:100]}...")
        if iteration.tool_calls:
            for tool_call in iteration.tool_calls:
                print(f"    Tool: {tool_call.name}({tool_call.arguments})")
        if iteration.duration:
            print(f"    Duration: {iteration.duration:.3f}s")
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    main()
