# Agno Memory Component

The Memory component provides agents with the ability to remember past conversations, store important information about users, and maintain context across multiple interactions. This capability is essential for building agents that feel continuous and personalized.

## Core Architecture

Agno's memory system is built around several key abstractions:

- **AgentMemory**: The central class that manages all memory aspects
- **Memory**: Represents a single piece of remembered information
- **SessionSummary**: Concise representation of a conversation
- **MemoryDb**: Interface for persistent storage backends

This architecture enables agents to maintain various types of memory:

1. **Message History**: Complete record of all messages
2. **Run History**: Record of interaction sequences
3. **User Memories**: Specific facts to remember about users
4. **Session Summaries**: Condensed representations of conversations

## AgentMemory Implementation

The `AgentMemory` class (`/libs/agno/agno/memory/memory.py`) is the core of the memory system:

```python
class AgentMemory:
    """Manages an agent's memory including messages, runs, and user memories."""
    
    # Message and run history
    messages: List[Message] = field(default_factory=list)
    runs: List[AgentRun] = field(default_factory=list)
    
    # User memories
    memories: List[Memory] = field(default_factory=list)
    
    # Session information
    session_summary: Optional[SessionSummary] = None
    session_id: Optional[str] = None
    
    # Memory database
    memory_db: Optional[MemoryDb] = None
    
    # Configuration options
    memory_limit: Optional[int] = None
    memory_summarizer_model: Optional[Model] = None
    memory_classifier_model: Optional[Model] = None
    memory_retrieval_method: MemoryRetrieval = MemoryRetrieval.last_n
    # ...other configuration options
```

The AgentMemory class provides methods for:
- Adding and retrieving messages
- Recording agent runs
- Managing user memories
- Creating and updating session summaries
- Persisting memory to storage

## Memory Storage

Agno supports multiple storage backends through the `MemoryDb` interface:

- **SqliteMemoryDb**: File-based SQLite storage
- **PgMemoryDb**: PostgreSQL database storage
- **MongoMemoryDb**: MongoDB document storage

Each implementation handles:
- Schema creation and management
- Serialization and deserialization
- CRUD operations for memories
- Efficient querying for relevant memories

## Memory Summarization

Memory summarization is a key feature that condenses conversations into manageable summaries:

```python
class MemorySummarizer:
    """Creates summaries of conversations."""
    
    model: Optional[Model] = None
    
    def summarize(self, messages: List[Message]) -> SessionSummary:
        """Generate a summary from message history."""
        # Implementation details...
```

The summarization process:
1. Takes a list of messages from the conversation
2. Uses an LLM to generate a concise summary
3. Identifies key topics from the conversation
4. Returns a structured SessionSummary object

## Memory Classification

The `MemoryClassifier` determines what information should be stored as memories:

```python
class MemoryClassifier:
    """Determines if information should be remembered."""
    
    model: Optional[Model] = None
    
    def should_remember(self, message: str) -> bool:
        """Decide if a message contains information worth remembering."""
        # Implementation details...
        
    def classify_memory(self, message: str) -> Optional[Memory]:
        """Extract and classify information to remember."""
        # Implementation details...
```

This classification process:
1. Analyzes user messages for important information
2. Determines if the information is worth remembering
3. Creates a structured Memory object if appropriate
4. Assigns topics/categories to the memory

## Integration with Agents

Memory integrates with agents through several mechanisms:

```python
# Creating an agent with memory
agent = Agent(
    model=OpenAIChat(),
    instructions="You are a helpful assistant with memory.",
    memory=True,  # Enable the default memory system
    read_chat_history=True,  # Include conversation history
)

# Or with more configuration
agent = Agent(
    model=OpenAIChat(),
    instructions="You are a helpful assistant with memory.",
    memory=AgentMemory(
        memory_db=SqliteMemoryDb("memories.db"),
        max_messages=100,
        create_memories=True,
        memory_classifier_model=OpenAIChat(id="gpt-4o"),
        update_session_summary=True
    ),
    read_chat_history=True,
)
```

During agent operation:
1. User messages are recorded in memory
2. The memory system may create new user memories
3. Session summaries are updated
4. Relevant memories are incorporated into the system message
5. The agent's responses are informed by past context

## Key Files

- `/libs/agno/agno/memory/memory.py`: Core AgentMemory implementation
- `/libs/agno/agno/memory/interfaces.py`: Memory-related data classes
- `/libs/agno/agno/memory/db/`: Storage implementations
- `/libs/agno/agno/memory/summarizer.py`: Memory summarization
- `/libs/agno/agno/memory/classifier.py`: Memory classification

## Usage Examples

### Basic Memory

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

# Create an agent with basic memory
agent = Agent(
    model=OpenAIChat(),
    instructions="You are a helpful assistant with memory.",
    memory=True,
    read_chat_history=True,
)

# First interaction
agent.run("My name is Alice.")

# Second interaction - agent remembers the name
agent.run("What's my name?")  # Agent will respond with "Alice"
```

### Persistent Memory with SQLite

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.memory import AgentMemory
from agno.memory.db import SqliteMemoryDb

# Create agent with persistent memory
agent = Agent(
    model=OpenAIChat(),
    instructions="You are a helpful assistant that remembers information.",
    memory=AgentMemory(
        memory_db=SqliteMemoryDb("user_memories.db"),
        create_memories=True,  # Extract memories from conversations
    ),
    read_chat_history=True,
)

# First session
agent.run("My favorite color is blue and I live in Boston.")

# Later session (memory persists across sessions)
agent.run("Where do I live?")  # Agent remembers "Boston"
```

### Session Summaries

```python
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.memory import AgentMemory

# Create agent with session summarization
agent = Agent(
    model=Claude(),
    instructions="You are a helpful assistant that summarizes our conversation.",
    memory=AgentMemory(
        update_session_summary=True,
        update_session_summary_after_run=True,
    ),
    read_chat_history=True,
)

# Have a conversation
agent.run("Let's discuss climate change solutions.")
agent.run("What about solar power?")
agent.run("How does nuclear energy compare?")

# Get the summary
summary = agent.memory.session_summary
print(f"Conversation summary: {summary.summary}")
print(f"Topics discussed: {summary.topics}")
```

### Advanced Memory with PostgreSQL

```python
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.memory import AgentMemory
from agno.memory.db import PgMemoryDb

# Create agent with PostgreSQL memory storage
agent = Agent(
    model=Claude(),
    instructions="You are a helpful assistant with advanced memory capabilities.",
    memory=AgentMemory(
        memory_db=PgMemoryDb(
            db_url="postgresql://user:password@localhost:5432/memory_db",
            table_name="agent_memories"
        ),
        create_memories=True,
        memory_limit=50,
        update_session_summary=True,
    ),
    read_chat_history=True,
)

# Use the agent
agent.run("Remember that my meeting is on Tuesday at 3pm.")
```

## Summary

- **Flexible Memory System**: Multiple types of memory (messages, runs, user memories, summaries)
- **Persistent Storage**: Support for SQLite, PostgreSQL, MongoDB
- **Intelligent Memory**: LLM-powered summarization and classification
- **Configurable**: Extensive options for memory behavior
- **User-Centric**: Focus on remembering important user information
- **Seamless Integration**: Simple interface for enabling memory in agents