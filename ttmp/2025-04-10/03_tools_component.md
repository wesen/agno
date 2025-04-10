# Agno Tools Component

The Tools component enables Agno agents to perform actions and interact with external systems. Tools provide a powerful extension mechanism that allows agents to go beyond just generating text by accessing information, performing calculations, interacting with APIs, and manipulating data.

## Architecture

The Tools component is built around several key abstractions:

- **Function**: The base class that represents a callable function with metadata
- **FunctionCall**: Represents an execution instance of a function
- **Toolkit**: A collection of related functions/tools
- **tool**: A decorator for easily converting Python functions into Agno tools

This architecture enables a flexible and extensible system for tool creation and execution.

## Core Concepts

### Function Class

The `Function` class (`/libs/agno/agno/tools/function.py`) is the fundamental building block:

```python
class Function:
    name: str
    description: str
    parameters: dict
    execute_fn: Callable
    is_async: bool
    # Other properties...
    
    def execute(self, **kwargs):
        # Execute the function and handle results
        
    async def aexecute(self, **kwargs):
        # Async execution
```

Each Function has:
- A name and description
- A parameter schema (JSON Schema format)
- An execution function (sync or async)
- Optional hooks (pre-execution, post-execution)
- Error handling and result formatting logic

### Toolkit Class

The `Toolkit` class (`/libs/agno/agno/tools/toolkit.py`) groups related functions:

```python
class Toolkit:
    name: str
    functions: List[Function]
    
    def register(self, function):
        # Register a function to this toolkit
        
    def get_functions(self):
        # Return all registered functions
```

### Tool Decorator

The `@tool` decorator simplifies creating tools:

```python
@tool
def search_web(query: str) -> str:
    """Search the web for information.
    
    Args:
        query: The search query
        
    Returns:
        Search results as a string
    """
    # Implementation
    return results
```

The decorator:
- Extracts name, description, and parameter schema from the function
- Handles both sync and async functions
- Manages execution context (pre/post hooks, error handling)

## Available Tool Categories

Agno provides a wide range of built-in tools:

1. **Search and Information Retrieval**
   - Web search (DuckDuckGo, Google, Tavily)
   - Knowledge bases (Wikipedia, Arxiv)
   - News (HackerNews, Reddit)

2. **Data Processing**
   - CSV and JSON manipulation
   - Pandas data analysis
   - Data visualization

3. **API Integrations**
   - GitHub, Twitter, Reddit
   - Slack, Discord, Telegram
   - Email, Calendar, Trello

4. **Financial Tools**
   - YFinance for stock data
   - Financial datasets
   - OpenBB integration

5. **Computational**
   - Calculator for math operations
   - Python code execution

6. **Database**
   - SQL querying (PostgreSQL, DuckDB)
   - Vector database interactions

7. **File Operations**
   - Reading and writing files
   - File conversion

8. **Media**
   - Image generation (DALL-E)
   - Video processing (Replicate)
   - Audio tools (ElevenLabs)

## Creating Custom Tools

There are several ways to create custom tools in Agno:

### Method 1: Using the @tool Decorator

```python
from agno.tools import tool

@tool
def get_weather(location: str, unit: str = "celsius") -> str:
    """Get the current weather for a location.
    
    Args:
        location: City or location name
        unit: Temperature unit (celsius or fahrenheit)
        
    Returns:
        Current weather information
    """
    # Implementation
    return f"It's 25°C and sunny in {location}"
```

### Method 2: Creating a Custom Toolkit

```python
from agno.tools import Toolkit, tool

class WeatherToolkit(Toolkit):
    def __init__(self, api_key=None, **kwargs):
        super().__init__(name="weather_tools", **kwargs)
        self.api_key = api_key
        
        # Register tools
        self.register(self.get_weather)
        self.register(self.get_forecast)
    
    def get_weather(self, location: str) -> str:
        """Get current weather"""
        # Implementation
        return f"It's 25°C and sunny in {location}"
    
    def get_forecast(self, location: str, days: int = 5) -> str:
        """Get weather forecast"""
        # Implementation
        return f"5-day forecast for {location}..."
```

### Method 3: Advanced Features

```python
# Tool with pre/post hooks
def pre_hook(kwargs):
    print(f"About to execute with {kwargs}")
    return kwargs

def post_hook(result):
    print(f"Execution finished with {result}")
    return result

@tool(pre_hook=pre_hook, post_hook=post_hook)
def enhanced_tool(param: str) -> str:
    return f"Processed: {param}"

# Async tool
@tool
async def async_tool(param: str) -> str:
    await asyncio.sleep(1)  # Async operation
    return f"Async result: {param}"

# Tool with agent access
@tool
def agent_aware_tool(param: str, agent=None) -> str:
    # Access agent context
    user_name = agent.context.get("user_name", "User")
    return f"Hello {user_name}, you asked about {param}"
```

## Tool Execution Flow

When an agent uses a tool, the following process occurs:

1. Agent passes the user message to the model
2. Model decides to call a function based on its capabilities
3. Agent intercepts the function call request
4. Agent locates the appropriate function
5. Agent executes the function with provided parameters
6. Function returns a result
7. Result is passed back to the model
8. Model incorporates the result into its response

## Advanced Features

### Caching Tool Results

```python
from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools

agent = Agent(
    tools=[DuckDuckGoTools(cache_results=True, cache_ttl=3600)],
    show_tool_calls=True
)
```

### Streaming Tool Results

```python
@tool
def streaming_tool() -> Iterator[str]:
    for i in range(5):
        yield f"Result chunk {i}"
        time.sleep(0.5)
```

### Stopping After Tool Call

```python
@tool(stop_after_tool_call=True)
def final_action(input: str) -> str:
    # This will be the final action in the agent's execution
    return f"Final result: {input}"
```

## Key Files

- `/libs/agno/agno/tools/function.py`: Core Function class
- `/libs/agno/agno/tools/toolkit.py`: Toolkit implementation
- `/libs/agno/agno/tools/tool.py`: Tool decorator implementation
- `/cookbook/tool_concepts/`: Tool usage patterns and examples
- `/cookbook/tools/`: Examples of specific tool integrations

## Usage Examples

### Basic Tool Usage

```python
from agno.agent import Agent
from agno.tools.calculator_tools import CalculatorTools

agent = Agent(
    instructions="You are a math assistant.",
    tools=[CalculatorTools()],
    show_tool_calls=True
)

agent.run("What is the square root of 144 plus 50?")
```

### Multiple Tools

```python
from agno.agent import Agent
from agno.tools.calculator_tools import CalculatorTools
from agno.tools.duckduckgo_tools import DuckDuckGoTools
from agno.tools.wikipedia_tools import WikipediaTools

agent = Agent(
    instructions="You can help with math and research.",
    tools=[
        CalculatorTools(),
        DuckDuckGoTools(),
        WikipediaTools()
    ],
    show_tool_calls=True
)

agent.run("Calculate 15% of $85, and also tell me who invented calculus.")
```

### Creating and Using a Custom Tool

```python
from agno.agent import Agent
from agno.tools import tool

@tool
def factorial(n: int) -> int:
    """Calculate the factorial of a number.
    
    Args:
        n: The number to calculate factorial for
        
    Returns:
        The factorial value
    """
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

agent = Agent(
    instructions="You can calculate factorials.",
    tools=[factorial],
    show_tool_calls=True
)

agent.run("What is the factorial of 5?")
```

## Summary

- **Extensible**: Easy to create custom tools for any functionality
- **Flexible**: Support for sync/async, streaming, and context-aware tools
- **Comprehensive**: 100+ built-in tools for common tasks
- **Structured**: Clear interfaces for parameter validation and result handling
- **Performance-Oriented**: Features like caching for efficiency
- **Developer-Friendly**: Simple decorator-based API for custom tools