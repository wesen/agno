# Agno Models Component

The Models component of Agno provides a unified interface to interact with different Large Language Model (LLM) providers while abstracting away their implementation details. This allows developers to easily switch between model providers without changing their application code.

## Architecture

The Models component follows a class hierarchy:

- `Model` (abstract base class): Defines the interface all model implementations must follow
- Provider-specific implementations: Concrete classes that implement the `Model` interface for specific providers

Each model provider implementation handles:
- API client initialization and management
- Message formatting for the specific provider
- Response parsing and standardization
- Error handling and retries
- Tool/function calling integration
- Streaming support

## Supported Providers

Agno supports a wide range of model providers, including:

- **Anthropic**: Claude models with thinking capabilities
- **OpenAI**: GPT models with structured output support
- **Azure**: OpenAI and AI Foundry models
- **AWS**: Bedrock and SageMaker models
- **Google**: Gemini models with multimodal capabilities
- **Cohere**: Command models with RAG capabilities
- **Mistral**: Mistral models with various sizes
- **Groq**: High-performance inference for various model types
- **Self-hosted**: Ollama and LMStudio for local deployment
- **Aggregators**: LiteLLM, Together, OpenRouter for accessing multiple providers

Each provider may support different capabilities:
- Multimodal input (text, images, audio, video)
- Structured output (JSON, Pydantic models)
- Function/tool calling
- Reasoning steps (explicit thinking)
- Streaming responses

## Key Abstractions

The Models component uses several key abstractions:

- **Message**: Represents a message in a conversation (role, content, etc.)
- **ModelResponse**: Unified response format across all providers
- **FunctionCall**: Represents a function/tool call and its execution
- **ModelSettings**: Configuration options for model behavior

## Implementation Details

### Base Model Class

The abstract `Model` class (`/libs/agno/agno/models/base.py`) defines methods that all model implementations must provide:

```python
class Model(ABC):
    @abstractmethod
    def invoke(self, messages, **kwargs):
        """Synchronous model invocation"""
        pass

    @abstractmethod
    def ainvoke(self, messages, **kwargs):
        """Asynchronous model invocation"""
        pass

    @abstractmethod
    def invoke_stream(self, messages, **kwargs):
        """Synchronous streaming invocation"""
        pass

    @abstractmethod
    def ainvoke_stream(self, messages, **kwargs):
        """Asynchronous streaming invocation"""
        pass
```

### Provider-Specific Implementation

Each provider implements the base methods using provider-specific API clients:

```python
class Claude(Model):
    id: str = "claude-3-opus-20240229"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    # Other provider-specific settings...

    def invoke(self, messages, **kwargs):
        client = self.get_client()
        response = client.messages.create(
            model=self.id,
            messages=self._format_messages(messages),
            tools=self._format_tools_for_model(kwargs.get("tools")),
            # Other API parameters...
        )
        return self.parse_provider_response(response, messages)
```

### Function/Tool Calling

Models handle function calling through a standardized process:

1. Format tools into provider-specific format
2. Send the formatted tools with the message to the model
3. Parse the model's function call requests
4. Execute the requested functions
5. Return the function results to the model
6. Repeat until the model completes its response

```python
def _format_tools_for_model(self, tools):
    if not tools:
        return None
    
    formatted_tools = []
    for tool in tools:
        formatted_tools.append({
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
            # Provider-specific formatting...
        })
    return formatted_tools
```

## Key Files

- `/libs/agno/agno/models/base.py`: Base `Model` class and common utilities
- `/libs/agno/agno/models/[provider]/`: Provider-specific implementations
- `/cookbook/models/`: Examples of using different model providers

## Usage Examples

### Basic Usage

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

# Create an agent with an OpenAI model
agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    instructions="You are a helpful assistant."
)

# Get a response
response = agent.run("Tell me a joke")
print(response.content)
```

### Using Anthropic Claude

```python
from agno.agent import Agent
from agno.models.anthropic import Claude

# Create an agent with Claude
agent = Agent(
    model=Claude(id="claude-3-5-sonnet-20240620"),
    instructions="You are a helpful assistant."
)

# Get a response
response = agent.run("Explain quantum computing")
print(response.content)
```

### Using Models with Tools

```python
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.calculator_tools import CalculatorTools

# Create an agent with Claude and calculator tools
agent = Agent(
    model=Claude(id="claude-3-5-sonnet-20240620"),
    instructions="You are a math assistant.",
    tools=[CalculatorTools()]
)

# The model will use the calculator tool to solve this
response = agent.run("What is 1728 * 394 - 567?")
print(response.content)
```

### Streaming Responses

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

# Create an agent with streaming enabled
agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    instructions="You are a storyteller.",
    stream=True
)

# Stream the response
for chunk in agent.run("Tell me a short story about space", stream=True):
    print(chunk.content, end="", flush=True)
```

## Design Patterns

The Models component employs several design patterns:

1. **Strategy Pattern**: Different model implementations provide the same interface with different behaviors
2. **Adapter Pattern**: Provider-specific implementations adapt various APIs to a unified interface
3. **Template Method Pattern**: Base `Model` class defines the overall algorithm while subclasses implement specific steps
4. **Factory Pattern**: Methods like `get_client()` create and return appropriately configured clients

## Integration Points

The Models component integrates with other parts of Agno:

- **Agent**: Agents use models to generate responses
- **Tools**: Models interact with tools through function calling
- **Knowledge**: Models can incorporate knowledge through prompt formatting
- **Memory**: Models can access memory through prompt formatting

## Summary

- **Unified Interface**: Consistent API across 30+ model providers
- **Flexible**: Support for diverse model capabilities
- **Extensible**: Easy to add new model providers
- **Full-Featured**: Support for synchronous, asynchronous, and streaming operations
- **Tool Integration**: Standardized function calling across providers
- **Error Handling**: Robust error handling with provider-specific details
- **Performance-Oriented**: Efficient implementation with minimal overhead