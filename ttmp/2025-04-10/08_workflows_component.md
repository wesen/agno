# Agno Workflows Component

The Workflows component of Agno enables the orchestration of multi-step processes involving multiple agents. Workflows provide a structured way to build complex applications that require sequential processing, state management, and persistence.

## Core Architecture

The Workflows component is built around the `Workflow` class (`/libs/agno/agno/workflow/workflow.py`), which provides the foundation for creating custom workflow implementations:

```python
class Workflow:
    """Base class for workflows."""
    
    name: str = "Workflow"
    description: str = "Generic workflow"
    workflow_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    storage: Optional[Storage] = None
    debug: bool = False
    # Additional configuration...
    
    def __init__(self, **kwargs):
        self._update_attributes(kwargs)
        self.initialize_workflow()
        self.update_run_method()
    
    def run(self, *args, **kwargs):
        """Default implementation - override in subclasses."""
        raise NotImplementedError("Subclasses must implement run()")
```

Key architectural elements:
- **Workflow**: Base class for creating workflows
- **WorkflowMemory**: Manages workflow execution history
- **WorkflowSession**: Represents persistent workflow state
- **RunResponse**: Encapsulates workflow execution results

## Workflow Execution Model

The workflow execution follows this lifecycle:

1. **Initialization**:
   - Set up workflow configuration (IDs, storage, debug settings)
   - Initialize memory and session state

2. **Execution**:
   - The `run()` method is wrapped with execution infrastructure
   - Input parameters are captured
   - Session state is loaded from storage (if available)
   - User-defined workflow logic is executed
   - Response is processed and returned

3. **Persistence**:
   - Session state is updated
   - Execution details are recorded
   - Data is written to storage

Workflows support both synchronous and streaming execution models:
- Regular return: `return result`
- Streaming: `yield result_chunk`

## Data Flow Between Steps

Workflows manage data flow between steps through several mechanisms:

1. **Agent Execution Chain**:
   ```python
   result1 = self.agent1.run(input_data)
   result2 = self.agent2.run(result1.content)
   return self.agent3.run(result2.content)
   ```

2. **Session State**:
   ```python
   # Store data between runs
   self.session_state["research_results"] = research_results
   
   # Retrieve in a subsequent run
   if "research_results" in self.session_state:
       research_results = self.session_state["research_results"]
   ```

3. **Structured Data Models**:
   ```python
   class BlogPost(BaseModel):
       title: str
       content: str
       summary: str
   
   # Pass structured data between agents
   blog_post = BlogPost(title="...", content="...", summary="...")
   result = self.publisher_agent.run(blog_post.json())
   ```

## Integration with Agents and Teams

Workflows typically integrate with agents in these ways:

1. **Agent Composition**:
   ```python
   class ContentWorkflow(Workflow):
       def __init__(self, **kwargs):
           super().__init__(**kwargs)
           
           # Create specialized agents
           self.researcher = Agent(
               model=OpenAIChat(),
               instructions="Research topics thoroughly."
           )
           
           self.writer = Agent(
               model=Claude(),
               instructions="Write engaging content."
           )
   ```

2. **Sequential Processing**:
   ```python
   def run(self, topic):
       research = self.researcher.run(f"Research about {topic}")
       return self.writer.run(f"Write an article about {topic} using this research: {research.content}")
   ```

3. **Parallel Processing**:
   ```python
   def run(self, topic):
       research_task = asyncio.create_task(self.researcher.arun(f"Research about {topic}"))
       images_task = asyncio.create_task(self.image_finder.arun(f"Find images about {topic}"))
       
       research_result, images_result = await asyncio.gather(research_task, images_task)
       
       return self.assembler.run(f"Create article with: {research_result.content} and images: {images_result.content}")
   ```

## Workflow Storage and Persistence

Workflows use the Storage component for persistence:

```python
from agno.workflow import Workflow
from agno.storage.sqlite import SqliteStorage

class MyWorkflow(Workflow):
    def __init__(self, **kwargs):
        super().__init__(
            storage=SqliteStorage(db_file="workflows.db"),
            **kwargs
        )
```

Storage enables:
- **Session persistence**: Maintain state between runs
- **Run history**: Track all workflow executions
- **Media artifacts**: Store images, videos, and audio
- **Resumable workflows**: Pick up where you left off
- **Data serialization**: Convert complex objects to storable formats

## Key Files

- `/libs/agno/agno/workflow/workflow.py`: Core Workflow implementation
- `/libs/agno/agno/workflow/memory.py`: Workflow memory management
- `/libs/agno/agno/workflow/interfaces.py`: Data models and interfaces
- `/cookbook/workflows/`: Example workflow implementations

## Usage Examples

### Basic Workflow

```python
from agno.workflow import Workflow
from agno.agent import Agent
from agno.models.openai import OpenAIChat

class SummaryWorkflow(Workflow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Create agents
        self.researcher = Agent(
            model=OpenAIChat(),
            instructions="Research topics and find key information."
        )
        
        self.summarizer = Agent(
            model=OpenAIChat(),
            instructions="Create concise summaries of information."
        )
    
    def run(self, topic):
        # Research the topic
        research_result = self.researcher.run(f"Research about: {topic}")
        
        # Generate a summary
        summary_result = self.summarizer.run(f"Summarize this information: {research_result.content}")
        
        return summary_result

# Create and use the workflow
workflow = SummaryWorkflow()
result = workflow.run("renewable energy")
print(result.content)
```

### Workflow with Storage and State

```python
from agno.workflow import Workflow
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.sqlite import SqliteStorage

class ContentCreationWorkflow(Workflow):
    def __init__(self, **kwargs):
        super().__init__(
            name="Content Creator",
            description="Creates blog posts and social media content",
            storage=SqliteStorage(db_file="content_workflow.db"),
            **kwargs
        )
        
        # Initialize agents
        self.planner = Agent(model=Claude(), instructions="Plan content strategy.")
        self.writer = Agent(model=Claude(), instructions="Write high-quality blog posts.")
        self.social_media = Agent(model=Claude(), instructions="Create social media posts.")
    
    def run(self, topic=None, step=None):
        # If workflow is being resumed
        if step is None:
            if "current_step" in self.session_state:
                step = self.session_state["current_step"]
            else:
                step = "plan"
        
        # If topic is provided or already in session
        if topic:
            self.session_state["topic"] = topic
        elif "topic" in self.session_state:
            topic = self.session_state["topic"]
        else:
            return "Please provide a topic"
        
        # Execute workflow step
        if step == "plan":
            result = self.planner.run(f"Create a content plan for topic: {topic}")
            self.session_state["plan"] = result.content
            self.session_state["current_step"] = "write"
            return result
        
        elif step == "write":
            if "plan" not in self.session_state:
                return "Please run the planning step first"
            
            result = self.writer.run(f"Write a blog post about {topic} following this plan: {self.session_state['plan']}")
            self.session_state["blog_post"] = result.content
            self.session_state["current_step"] = "social"
            return result
        
        elif step == "social":
            if "blog_post" not in self.session_state:
                return "Please write the blog post first"
            
            result = self.social_media.run(f"Create 3 social media posts promoting this blog: {self.session_state['blog_post']}")
            self.session_state["current_step"] = "complete"
            return result

# Create workflow
workflow = ContentCreationWorkflow()

# Run workflow steps
step1 = workflow.run("artificial intelligence")  # Planning step
print(step1.content)

# Later, continue the workflow
workflow = ContentCreationWorkflow(session_id=workflow.session_id)
step2 = workflow.run()  # Writing step (continues from session)
print(step2.content)

# Finally, complete the workflow
workflow = ContentCreationWorkflow(session_id=workflow.session_id)
step3 = workflow.run()  # Social media step (continues from session)
print(step3.content)
```

### Complex Workflow with Multiple Agents

```python
from agno.workflow import Workflow
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo_tools import DuckDuckGoTools
from agno.storage.json_storage import JsonStorage
from pydantic import BaseModel
from typing import List

# Define structured data models
class NewsItem(BaseModel):
    title: str
    source: str
    summary: str
    url: str

class NewsReport(BaseModel):
    date: str
    top_stories: List[NewsItem]
    analysis: str

class NewsReporterWorkflow(Workflow):
    def __init__(self, **kwargs):
        super().__init__(
            name="News Reporter",
            description="Creates daily news reports",
            storage=JsonStorage(directory="./workflow_storage"),
            **kwargs
        )
        
        # Initialize specialized agents
        self.researcher = Agent(
            model=OpenAIChat(),
            instructions="Research current news stories.",
            tools=[DuckDuckGoTools()],
            response_model=List[NewsItem]
        )
        
        self.analyst = Agent(
            model=OpenAIChat(),
            instructions="Analyze news stories and identify trends.",
            response_model=str
        )
        
        self.reporter = Agent(
            model=OpenAIChat(),
            instructions="Create comprehensive news reports.",
            response_model=NewsReport
        )
    
    def run(self, topic):
        # Research current news
        news_items = self.researcher.run(f"Find the latest news about {topic}")
        
        # If we have structured output, it's in content
        if hasattr(news_items.content, "__iter__"):
            news_items_list = news_items.content
        else:
            # Fallback for unstructured output
            news_items_list = []
        
        # Analyze the news
        analysis = self.analyst.run(f"Analyze these news items: {news_items_list}")
        
        # Generate the report
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        report = self.reporter.run({
            "date": today,
            "topic": topic,
            "news_items": news_items_list,
            "analysis": analysis.content
        })
        
        return report

# Create and use the workflow
workflow = NewsReporterWorkflow()
result = workflow.run("climate change")
print(result.content.date)
print(result.content.analysis)
for story in result.content.top_stories:
    print(f"- {story.title}: {story.summary}")
```

## Summary

- **Sequential Processing**: Orchestrate multi-step processes with agents
- **State Management**: Maintain context across workflow steps
- **Persistence**: Store workflow state for resumable processes
- **Structured Data**: Pass data between agents in structured formats
- **Flexible Composition**: Combine multiple agents into complex workflows
- **Storage Integration**: Persist workflow state across sessions
- **Streaming Support**: Stream partial results for long-running workflows