# Agno Teams Component

The Teams component of Agno enables multiple agents to collaborate on complex tasks. Teams can distribute work among specialized agents, orchestrate multi-step processes, or facilitate discussions between different perspectives.

## Core Architecture

The Teams component is built around the `Team` class (`/libs/agno/agno/team/team.py`), which serves as a container and orchestrator for multiple member agents:

```python
class Team:
    """A team of agents that work together."""
    
    name: str
    instructions: str
    members: List[Union[Agent, "Team"]]
    mode: TeamMode
    model: Optional[Model] = None
    # Additional configuration...
```

Key architectural elements:
- **Team**: The container and orchestrator for member agents
- **TeamMode**: Defines the collaboration pattern (Route, Coordinate, Collaborate)
- **TeamMemory**: Manages conversation history and context
- **TeamContext**: Stores shared information and member interactions
- **TeamRun**: Records execution instances

## Team Modes

Agno supports three distinct team modes, each with different orchestration patterns:

### 1. Route Mode

The route mode forwards user requests to the most appropriate team member:

```python
team = Team(
    name="Support Team",
    mode=TeamMode.route,
    instructions="""Route user queries to the appropriate specialist:
        - Technical questions go to the TechSupport agent
        - Billing questions go to the BillingSupport agent
        - Other questions go to the GeneralSupport agent
    """,
    members=[tech_support, billing_support, general_support]
)
```

In route mode:
- Team leader evaluates each request and selects one agent to handle it
- Only the selected agent processes the request
- Response comes directly from the chosen specialist
- Leader doesn't solve the task; it only routes it

Common use cases: Language routing, specialized support, domain-specific handling

### 2. Coordinate Mode

The coordinate mode orchestrates sequential workflows across multiple agents:

```python
team = Team(
    name="Research Team",
    mode=TeamMode.coordinate,
    instructions="""Coordinate a research workflow:
        1. Searcher finds initial information
        2. Analyzer evaluates and extracts key points
        3. Writer creates a final summary report
    """,
    members=[searcher_agent, analyzer_agent, writer_agent]
)
```

In coordinate mode:
- Team leader breaks down tasks into sequential steps
- Each step is assigned to a specific agent
- Results from one agent are passed to the next
- Leader orchestrates the flow and assembles final results

Common use cases: Content creation pipelines, research workflows, multi-step processes

### 3. Collaborate Mode

The collaborate mode facilitates discussion between multiple agents:

```python
team = Team(
    name="Analysis Team",
    mode=TeamMode.collaborate,
    instructions="""Analyze this problem from multiple perspectives.
        Have a thoughtful discussion considering different viewpoints.
    """,
    members=[business_agent, technical_agent, security_agent]
)
```

In collaborate mode:
- All relevant agents work on the same task
- Agents discuss and share perspectives
- Team leader moderates the discussion
- Final response incorporates multiple viewpoints

Common use cases: Decision making, diverse analysis, brainstorming

## Team Communication

Agents communicate within teams through structured mechanisms:

- **Direct Communication**: In collaborate mode, agents can see each other's responses
- **Sequential Communication**: In coordinate mode, output from one agent becomes input for the next
- **Context Sharing**: Agents can update shared context using special functions
- **Team Leader Mediation**: Team leader controls and directs communication flow

The communication is managed through:
- `TeamContext` storing member interactions
- Context update functions like `set_team_context`
- `TeamMemberInteraction` objects recording tasks and responses

## Team Memory and Context

Teams maintain memory and context at multiple levels:

- **Message History**: Complete record of user-team interactions
- **Run History**: Record of team execution instances
- **Member Interactions**: History of agent contributions
- **Shared Context**: Information accessible to all team members
- **User Memories**: Persistent information about users

Teams can use persistent storage for memory retention across sessions:

```python
team = Team(
    # ...other configuration...
    storage=SqliteStorage(db_file="team_memory.db"),
    memory=TeamMemory(
        create_memories=True,
        update_session_summary=True
    )
)
```

## Key Files

- `/libs/agno/agno/team/team.py`: Core Team implementation
- `/libs/agno/agno/team/memory.py`: Team memory system
- `/libs/agno/agno/team/modes/`: Implementation of different team modes
- `/libs/agno/agno/team/context.py`: Team context management
- `/cookbook/teams/`: Examples of team implementations

## Usage Examples

### Route Mode Example: Multi-Language Support

```python
from agno.agent import Agent
from agno.team import Team, TeamMode
from agno.models.openai import OpenAIChat

# Create specialist agents
english_agent = Agent(
    model=OpenAIChat(),
    name="EnglishSupport",
    instructions="Provide support in English."
)

spanish_agent = Agent(
    model=OpenAIChat(),
    name="SpanishSupport",
    instructions="Provide support in Spanish."
)

french_agent = Agent(
    model=OpenAIChat(),
    name="FrenchSupport",
    instructions="Provide support in French."
)

# Create the routing team
language_team = Team(
    name="LanguageSupport",
    mode=TeamMode.route,
    model=OpenAIChat(),
    instructions="""Route the query to the appropriate language specialist:
        - English questions to EnglishSupport
        - Spanish questions to SpanishSupport
        - French questions to FrenchSupport
    """,
    members=[english_agent, spanish_agent, french_agent]
)

# User interactions
response = language_team.run("Hello, how can you help me?")  # Routes to English agent
response = language_team.run("Bonjour, comment puis-je obtenir de l'aide?")  # Routes to French agent
```

### Coordinate Mode Example: Content Creation

```python
from agno.agent import Agent
from agno.team import Team, TeamMode
from agno.models.anthropic import Claude
from agno.tools.duckduckgo_tools import DuckDuckGoTools

# Create specialist agents
researcher = Agent(
    model=Claude(),
    name="Researcher",
    instructions="Research the topic and gather key information.",
    tools=[DuckDuckGoTools()]
)

writer = Agent(
    model=Claude(),
    name="Writer",
    instructions="Write a blog post based on the research provided."
)

editor = Agent(
    model=Claude(),
    name="Editor",
    instructions="Edit the draft for clarity, grammar, and impact."
)

# Create the coordination team
content_team = Team(
    name="ContentTeam",
    mode=TeamMode.coordinate,
    model=Claude(),
    instructions="""Create high-quality content through a three-step process:
        1. Research: Gather information on the topic
        2. Writing: Create a draft based on the research
        3. Editing: Polish the draft for final publication
    """,
    members=[researcher, writer, editor]
)

# Generate content
response = content_team.run("Create a blog post about climate change solutions.")
```

### Collaborate Mode Example: Decision Analysis

```python
from agno.agent import Agent
from agno.team import Team, TeamMode
from agno.models.openai import OpenAIChat

# Create specialist agents
business_analyst = Agent(
    model=OpenAIChat(),
    name="BusinessAnalyst",
    instructions="Analyze problems from a business perspective, focusing on ROI and market impact."
)

tech_analyst = Agent(
    model=OpenAIChat(),
    name="TechAnalyst",
    instructions="Analyze problems from a technical perspective, focusing on feasibility and implementation."
)

risk_analyst = Agent(
    model=OpenAIChat(),
    name="RiskAnalyst",
    instructions="Analyze problems from a risk perspective, focusing on potential downsides and mitigation."
)

# Create the collaboration team
analysis_team = Team(
    name="AnalysisTeam",
    mode=TeamMode.collaborate,
    model=OpenAIChat(),
    instructions="""Analyze the proposed solution from multiple perspectives.
        Have a thoughtful discussion considering business, technical, and risk factors.
        Each analyst should contribute their expertise, and you should facilitate a discussion
        to reach a comprehensive assessment.
    """,
    members=[business_analyst, tech_analyst, risk_analyst],
    share_member_interactions=True
)

# Analyze a proposal
response = analysis_team.run("Should we migrate our application to a microservices architecture?")
```

## Advanced Features

### Team Memory with Persistence

```python
from agno.agent import Agent
from agno.team import Team, TeamMode
from agno.models.openai import OpenAIChat
from agno.storage.sqlite import SqliteStorage
from agno.team.memory import TeamMemory

team = Team(
    # ...other configuration...
    storage=SqliteStorage(db_file="team_memory.db"),
    memory=TeamMemory(
        create_memories=True,
        update_session_summary=True
    ),
    read_chat_history=True
)
```

### Agentic Context Updates

```python
team = Team(
    # ...other configuration...
    enable_agentic_context=True
)
```

With agentic context enabled, agents can update the shared team context during their operations.

### Team Tools

```python
from agno.tools import tool

@tool
def external_api_call(query: str) -> str:
    """Make an external API call."""
    # Implementation...
    return result

team = Team(
    # ...other configuration...
    tools=[external_api_call]
)
```

## Summary

- **Multi-Agent Collaboration**: Enable complex workflows across specialized agents
- **Flexible Modes**: Choose from route, coordinate, or collaborate patterns
- **Context Sharing**: Share information between team members
- **Memory System**: Track conversation history and outcomes
- **Scalable Design**: Support for nested teams and complex hierarchies
- **Multimodal Support**: Handle text, images, audio, and video
- **Persistent Storage**: Maintain team knowledge across sessions