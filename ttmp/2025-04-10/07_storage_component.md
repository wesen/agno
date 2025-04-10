# Agno Storage Component

The Storage component provides persistence capabilities for Agents, Teams, and Workflows in the Agno framework. It enables conversation history, agent state, and other data to be saved and retrieved across sessions and application restarts.

## Core Architecture

The Storage component is built around several key abstractions:

- **Storage**: The abstract base class that defines the interface for all storage implementations
- **Session**: Data classes representing the state to be stored (AgentSession, TeamSession, WorkflowSession)
- **Backend Implementations**: Concrete storage implementations for different persistence mechanisms

This architecture enables a flexible and pluggable storage system where different backends can be used interchangeably.

## Storage Interface

The `Storage` abstract class (`/libs/agno/agno/storage/base.py`) defines the core interface:

```python
class Storage(ABC):
    """Base class for storage implementations."""
    
    storage_type: StorageType  # agent, team, or workflow
    
    @abstractmethod
    def create(self, session: Union[AgentSession, TeamSession, WorkflowSession]) -> None:
        """Create a new session."""
        pass
    
    @abstractmethod
    def read(self, session_id: str, user_id: Optional[str] = None) -> Optional[Union[AgentSession, TeamSession, WorkflowSession]]:
        """Read a session."""
        pass
    
    @abstractmethod
    def upsert(self, session: Union[AgentSession, TeamSession, WorkflowSession]) -> None:
        """Update or insert a session."""
        pass
    
    @abstractmethod
    def delete_session(self, session_id: str, user_id: Optional[str] = None) -> None:
        """Delete a session."""
        pass
    
    @abstractmethod
    def list_sessions(self, user_id: Optional[str] = None) -> List[Union[AgentSession, TeamSession, WorkflowSession]]:
        """List all sessions."""
        pass
```

## Session Data Model

Sessions are the core data structures that represent the state to be persisted:

```python
@dataclass
class AgentSession:
    """Represents an agent session."""
    
    session_id: str
    agent_id: str
    user_id: Optional[str] = None
    memory: Optional[Dict[str, Any]] = None
    session_name: Optional[str] = None
    session_state: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    agent_data: Optional[Dict[str, Any]] = None
    team_session_id: Optional[str] = None
    images: Optional[List[Dict[str, Any]]] = None
    videos: Optional[List[Dict[str, Any]]] = None
    audio: Optional[List[Dict[str, Any]]] = None
    extra_data: Optional[Dict[str, Any]] = None
```

Similar classes exist for `TeamSession` and `WorkflowSession` with entity-specific fields.

## Supported Storage Backends

Agno provides implementations for multiple storage backends:

### File-Based Storage

- **JSONStorage**: Simple file-based storage using JSON files
- **YAMLStorage**: File-based storage using YAML files

These are ideal for development, testing, or simple applications.

### Relational Databases

- **SQLiteStorage**: Lightweight file-based SQL database
- **PostgresStorage**: Enterprise-grade relational database
- **SingleStoreStorage**: Distributed SQL database optimized for real-time analytics

These provide robust persistence with transaction support.

### Document Databases

- **MongoDBStorage**: Document-oriented NoSQL database

Ideal for flexible schema requirements and document-oriented data.

### Cloud Storage

- **DynamoDBStorage**: AWS DynamoDB-based storage
- **GCSJsonStorage**: Google Cloud Storage-based JSON storage

These provide cloud-native persistence options.

## Integration with Agents and Teams

Agents and Teams integrate with storage through a simple configuration interface:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.storage.sqlite import SqliteStorage

# Create an agent with storage
agent = Agent(
    model=OpenAIChat(),
    instructions="You are a helpful assistant.",
    storage=SqliteStorage(db_file="agent_sessions.db"),
    read_chat_history=True  # Include previous conversation history
)
```

When an agent with storage is used:
1. On first run, a new session is created
2. After each interaction, the session is updated
3. When restarted with the same session ID, previous state is loaded
4. Memory, conversation history, and custom state can persist across sessions

## Key Files

- `/libs/agno/agno/storage/base.py`: Core Storage interface
- `/libs/agno/agno/storage/json_storage/`: JSON file-based storage implementation
- `/libs/agno/agno/storage/yaml_storage/`: YAML file-based storage implementation
- `/libs/agno/agno/storage/sqlite_storage/`: SQLite database storage
- `/libs/agno/agno/storage/postgres_storage/`: PostgreSQL database storage
- `/libs/agno/agno/storage/mongodb_storage/`: MongoDB document storage
- `/libs/agno/agno/storage/dynamodb_storage/`: AWS DynamoDB storage
- `/libs/agno/agno/storage/gcs_storage/`: Google Cloud Storage implementation

## Usage Examples

### JSON Storage

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.storage.json_storage import JsonStorage

# Create an agent with JSON storage
agent = Agent(
    model=OpenAIChat(),
    instructions="You are a helpful assistant.",
    storage=JsonStorage(directory="./storage"),
    read_chat_history=True
)

# First run creates a new session
response = agent.run("Hello, my name is Alex.")

# Second run continues the same session
response = agent.run("What's my name?")  # Agent remembers "Alex"
```

### SQLite Storage

```python
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.sqlite_storage import SqliteStorage

# Create agent with SQLite storage
agent = Agent(
    model=Claude(),
    instructions="You are a helpful assistant.",
    storage=SqliteStorage(
        db_file="assistant.db",
        table_name="agent_sessions"
    ),
    read_chat_history=True
)

# Session persists in SQLite database
response = agent.run("Remember that my favorite color is blue.")
```

### PostgreSQL Storage for Teams

```python
from agno.team import Team, TeamMode
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.storage.postgres_storage import PostgresStorage

# Create agents
agent_a = Agent(
    model=OpenAIChat(),
    name="AgentA",
    instructions="You are Agent A."
)

agent_b = Agent(
    model=OpenAIChat(),
    name="AgentB",
    instructions="You are Agent B."
)

# Create team with PostgreSQL storage
team = Team(
    name="TeamAB",
    mode=TeamMode.collaborate,
    instructions="Work together to solve problems.",
    members=[agent_a, agent_b],
    storage=PostgresStorage(
        db_url="postgresql://user:password@localhost:5432/agno_db",
        table_name="team_sessions"
    ),
    read_chat_history=True
)

# Team interactions are stored in PostgreSQL
response = team.run("Discuss the benefits of renewable energy.")
```

### MongoDB Storage

```python
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.mongodb_storage import MongoDBStorage

# Create agent with MongoDB storage
agent = Agent(
    model=Claude(),
    instructions="You are a helpful assistant.",
    storage=MongoDBStorage(
        connection_string="mongodb://localhost:27017/",
        database_name="agno_db",
        collection_name="agent_sessions"
    ),
    read_chat_history=True
)

# Session persists in MongoDB
response = agent.run("What's the weather like today?")
```

### Custom Session Management

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.storage.json_storage import JsonStorage

# Create agent with storage
storage = JsonStorage(directory="./storage")
agent = Agent(
    model=OpenAIChat(),
    instructions="You are a helpful assistant.",
    storage=storage,
    read_chat_history=True
)

# First session
agent.run("My name is Taylor.")

# Save session ID
session_id = agent.session_id

# Later, resume the same session
new_agent = Agent(
    model=OpenAIChat(),
    instructions="You are a helpful assistant.",
    storage=storage,
    session_id=session_id,  # Reuse the previous session
    read_chat_history=True
)

# Agent remembers the user's name
new_agent.run("What's my name?")  # Responds with "Taylor"
```

## Summary

- **Flexible Persistence**: Multiple storage options from simple files to enterprise databases
- **Unified Interface**: Consistent API across all storage implementations
- **Session Management**: Structured data model for agent, team, and workflow state
- **Multimodal Support**: Store text, images, audio, and video
- **Cloud Options**: Support for AWS DynamoDB and Google Cloud Storage
- **Simple Integration**: Easy to add storage to agents and teams
- **Stateful Conversations**: Enable persistent, context-aware interactions