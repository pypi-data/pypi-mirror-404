"""
Simple example demonstrating OR-AF (Operations Research Agentic Framework)
"""

from or_af import Agent


# Define a simple tool
def get_square(number: float) -> float:
    """Calculate the square of a number."""
    return number ** 2


def get_sum(x: float, y: float) -> float:
    """Add two numbers together."""
    return x + y


def main():
    # Initialize agent
    print("🤖 Initializing Agent...")
    agent = Agent(
        system_prompt="You are a helpful math assistant. Use your tools to solve problems."
    )
    
    # Register tools
    print("\n🔧 Registering tools...")
    agent.add_tool("get_square", get_square)
    agent.add_tool("get_sum", get_sum)
    
    # Run a task
    print("\n" + "="*60)
    print("RUNNING TASK")
    print("="*60)
    
    task = "What is the square of 12, and then add 5 to that result?"
    result = agent.run(task)
    
    print("\n" + "="*60)
    print("✅ DONE!")
    print("="*60)


if __name__ == "__main__":
    main()
