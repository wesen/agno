# Building an HTN Planning Agent with Agno

## Introduction

This tutorial demonstrates how to create an Agno agent that uses Hierarchical Task Network (HTN) planning to dynamically decompose complex tasks like web research and report generation. HTN planning is a powerful AI planning technique that breaks down high-level tasks into hierarchies of increasingly specific subtasks until reaching directly executable primitive actions.

We'll build a research agent that can:
1. Accept high-level tasks like "write a report on quantum computing advancements"
2. Dynamically decompose tasks into subtasks using LLM reasoning
3. Execute primitive tasks (web searches, content extraction, writing sections)
4. Handle dependencies between tasks
5. Maintain state across the execution flow
6. Adapt the plan as new information emerges

## Prerequisites

- Python 3.8+
- Agno library (`pip install agno`)
- OpenAI or Anthropic API key
- Basic understanding of Agno agents

## Core Concepts

### Hierarchical Task Networks (HTN)

An HTN consists of:
- **Tasks**: Work to be done (e.g., "research quantum computing")
- **Methods**: Ways to decompose tasks into subtasks
- **Operators**: Primitive actions that can be directly executed
- **Planning Domain**: Set of tasks, methods and operators
- **Planning Problem**: Initial state and goal tasks

In our implementation, we'll use LLMs to dynamically generate decomposition methods rather than using a predefined set.

### System Architecture

Our HTN Planning Agent will be built with these components:

1. **Task Manager**: Handles task representation, dependencies, and execution ordering
2. **Task Decomposer**: LLM-powered component that breaks down complex tasks
3. **Task Executor**: Executes primitive tasks using appropriate tools
4. **State Tracker**: Maintains the world state and task results
5. **Planning Controller**: Orchestrates the planning and execution process

## Implementation

### Step 1: Set Up the Project

Create a new Python file named `htn_planning_agent.py`:

```python
import asyncio
from enum import Enum
from typing import Dict, List, Optional, Set, Union
from dataclasses import dataclass, field
import uuid
import json

from agno import Agent
from agno.models.anthropic import Claude
from agno.tools.duckduckgo_tools import DuckDuckGoTools
from agno.tools.calculator_tools import CalculatorTools
from agno.tools.wikipedia_tools import WikipediaTools
from agno.tools import tool
```

### Step 2: Define Task Representations

```python
class TaskStatus(Enum):
    PENDING = "pending"
    DECOMPOSING = "decomposing"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Task:
    """Representation of a task in the HTN."""
    id: str
    name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    parent_id: Optional[str] = None
    is_primitive: bool = False
    dependencies: Set[str] = field(default_factory=set)
    results: Optional[str] = None
    
    # For non-primitive tasks
    subtasks: List[str] = field(default_factory=list)
    
    # Metadata for planning
    estimated_time: Optional[int] = None
    priority: int = 1
    
    def to_dict(self):
        """Convert task to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "parent_id": self.parent_id,
            "is_primitive": self.is_primitive,
            "dependencies": list(self.dependencies),
            "results": self.results,
            "subtasks": self.subtasks,
            "estimated_time": self.estimated_time,
            "priority": self.priority
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create task from dictionary representation."""
        task = cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            status=TaskStatus(data["status"]),
            parent_id=data["parent_id"],
            is_primitive=data["is_primitive"]
        )
        task.dependencies = set(data["dependencies"])
        task.results = data["results"]
        task.subtasks = data["subtasks"]
        task.estimated_time = data["estimated_time"]
        task.priority = data["priority"]
        return task
```

### Step 3: Implement Task Manager

```python
class TaskManager:
    """Manages the task network, dependencies, and execution order."""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.root_tasks: List[str] = []
    
    def add_task(self, task: Task) -> str:
        """Add a task to the network and return its ID."""
        self.tasks[task.id] = task
        if task.parent_id is None:
            self.root_tasks.append(task.id)
        return task.id
    
    def create_task(self, name: str, description: str, 
                   is_primitive: bool = False, 
                   parent_id: Optional[str] = None,
                   dependencies: Optional[Set[str]] = None) -> str:
        """Create and add a new task."""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            name=name,
            description=description,
            is_primitive=is_primitive,
            parent_id=parent_id,
            dependencies=dependencies or set()
        )
        return self.add_task(task)
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, **kwargs) -> None:
        """Update a task's properties."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
    
    def get_next_tasks(self) -> List[Task]:
        """Get the next tasks that are ready to be executed or decomposed."""
        next_tasks = []
        
        for task_id, task in self.tasks.items():
            # Skip completed or already in-progress tasks
            if task.status in (TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS, 
                              TaskStatus.DECOMPOSING):
                continue
            
            # Check if all dependencies are satisfied
            dependencies_met = all(
                self.tasks[dep_id].status == TaskStatus.COMPLETED
                for dep_id in task.dependencies
                if dep_id in self.tasks
            )
            
            if dependencies_met:
                if task.is_primitive:
                    task.status = TaskStatus.READY
                    next_tasks.append(task)
                elif task.status == TaskStatus.PENDING:
                    # Non-primitive tasks need decomposition
                    task.status = TaskStatus.READY
                    next_tasks.append(task)
        
        # Sort by priority (higher first)
        next_tasks.sort(key=lambda t: t.priority, reverse=True)
        return next_tasks
    
    def mark_task_complete(self, task_id: str, results: Optional[str] = None) -> None:
        """Mark a task as completed with optional results."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        task.status = TaskStatus.COMPLETED
        if results:
            task.results = results
        
        # Check if parent task can be marked as complete
        if task.parent_id and task.parent_id in self.tasks:
            parent = self.tasks[task.parent_id]
            all_subtasks_complete = all(
                self.tasks[subtask_id].status == TaskStatus.COMPLETED
                for subtask_id in parent.subtasks
            )
            
            if all_subtasks_complete:
                # Combine results from subtasks
                combined_results = "\n\n".join([
                    f"## {self.tasks[subtask_id].name}\n{self.tasks[subtask_id].results or 'No results'}"
                    for subtask_id in parent.subtasks
                ])
                self.mark_task_complete(parent.id, combined_results)
    
    def get_task_results(self, task_id: str) -> Optional[str]:
        """Get the results of a completed task."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        return task.results if task.status == TaskStatus.COMPLETED else None
    
    def export_plan(self) -> Dict:
        """Export the current plan as a dictionary."""
        return {
            "tasks": {task_id: task.to_dict() for task_id, task in self.tasks.items()},
            "root_tasks": self.root_tasks
        }
    
    def import_plan(self, plan_data: Dict) -> None:
        """Import a plan from a dictionary."""
        self.tasks = {
            task_id: Task.from_dict(task_data)
            for task_id, task_data in plan_data["tasks"].items()
        }
        self.root_tasks = plan_data["root_tasks"]
```

### Step 4: Implement State Tracker

```python
@dataclass
class PlanningState:
    """Maintains the world state during planning and execution."""
    
    # General information about the task
    topic: str
    
    # Knowledge gathered during execution
    facts: Dict[str, str] = field(default_factory=dict)
    
    # Search results and information sources
    sources: Dict[str, str] = field(default_factory=dict)
    
    # Report sections and content
    sections: Dict[str, str] = field(default_factory=dict)
    
    # Task metadata
    task_status: Dict[str, str] = field(default_factory=dict)
    task_results: Dict[str, str] = field(default_factory=dict)
    
    def update_facts(self, key: str, value: str) -> None:
        """Add or update a fact in the knowledge base."""
        self.facts[key] = value
    
    def add_source(self, source_id: str, content: str) -> None:
        """Add a source to the sources collection."""
        self.sources[source_id] = content
    
    def add_section(self, section_name: str, content: str) -> None:
        """Add or update a report section."""
        self.sections[section_name] = content
    
    def get_facts_summary(self) -> str:
        """Get a summary of all facts in the knowledge base."""
        if not self.facts:
            return "No facts have been gathered yet."
        
        return "\n".join([f"- {key}: {value}" for key, value in self.facts.items()])
    
    def get_sources_summary(self) -> str:
        """Get a summary of all sources."""
        if not self.sources:
            return "No sources have been found yet."
        
        return "\n".join([f"- Source {key}: {value[:100]}..." for key, value in self.sources.items()])
    
    def get_state_summary(self) -> str:
        """Get a summary of the current state."""
        return f"""
        Topic: {self.topic}
        
        Facts Gathered: {len(self.facts)}
        Sources Found: {len(self.sources)}
        Report Sections: {len(self.sections)}
        
        Facts Summary:
        {self.get_facts_summary()}
        
        Sources:
        {'; '.join(self.sources.keys())}
        
        Completed Sections:
        {'; '.join(self.sections.keys())}
        """
    
    def to_dict(self) -> Dict:
        """Convert state to dictionary for serialization."""
        return {
            "topic": self.topic,
            "facts": self.facts,
            "sources": self.sources,
            "sections": self.sections,
            "task_status": self.task_status,
            "task_results": self.task_results
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PlanningState':
        """Create state from dictionary."""
        return cls(
            topic=data["topic"],
            facts=data["facts"],
            sources=data["sources"],
            sections=data["sections"],
            task_status=data["task_status"],
            task_results=data["task_results"]
        )
```

### Step 5: Implement Task Decomposer Using LLM

```python
class TaskDecomposer:
    """Uses LLM to decompose non-primitive tasks into subtasks."""
    
    def __init__(self, agent: Agent):
        """Initialize with an Agno agent."""
        self.agent = agent
    
    async def decompose_task(self, task: Task, state: PlanningState) -> List[Task]:
        """
        Decompose a task into subtasks using LLM.
        Returns a list of created subtasks.
        """
        # Mark the task as being decomposed
        task.status = TaskStatus.DECOMPOSING
        
        # Prepare context for the LLM
        state_summary = state.get_state_summary()
        
        # Prompt the LLM to decompose the task
        prompt = f"""
        # Task Decomposition Request
        
        You need to break down the following task into smaller, more manageable subtasks.
        
        ## Current Task
        Name: {task.name}
        Description: {task.description}
        
        ## Current State
        {state_summary}
        
        ## Decomposition Requirements
        
        1. Break this task down into 3-7 subtasks that together will accomplish the parent task
        2. For each subtask, provide:
           - A clear, concise name
           - A detailed description
           - Whether it's a primitive task (can be directly executed) or needs further decomposition
           - Dependencies (IDs of other subtasks it depends on)
           - Estimated time to complete (in minutes)
           - Priority (1-5, with 5 being highest)
        
        ## Output Format
        
        Provide your response in the following JSON format:
        
        ```json
        {
          "subtasks": [
            {
              "name": "Subtask name",
              "description": "Detailed description",
              "is_primitive": true or false,
              "dependencies": ["id1", "id2"],
              "estimated_time": 15,
              "priority": 3
            }
          ]
        }
        ```
        
        Note: For the first subtask, the dependencies list should be empty since there are no other subtasks yet.
        """
        
        try:
            # Get decomposition from LLM
            response = await self.agent.arun(prompt)
            content = response.content
            
            # Extract JSON from response
            json_start = content.find('```json')
            json_end = content.rfind('```')
            
            if json_start != -1 and json_end != -1:
                json_content = content[json_start + 7:json_end].strip()
                decomposition = json.loads(json_content)
            else:
                # Try direct parsing if no code blocks found
                decomposition = json.loads(content)
            
            # Create subtasks from decomposition
            subtasks = []
            for subtask_data in decomposition["subtasks"]:
                # Generate deterministic ID based on parent and subtask name
                subtask_id = str(uuid.uuid4())
                
                # Create subtask
                subtask = Task(
                    id=subtask_id,
                    name=subtask_data["name"],
                    description=subtask_data["description"],
                    is_primitive=subtask_data["is_primitive"],
                    parent_id=task.id,
                    dependencies=set(subtask_data.get("dependencies", [])),
                    estimated_time=subtask_data.get("estimated_time", 10),
                    priority=subtask_data.get("priority", 1)
                )
                
                subtasks.append(subtask)
            
            # Update parent task with subtask references
            task.subtasks = [subtask.id for subtask in subtasks]
            
            return subtasks
            
        except Exception as e:
            print(f"Error decomposing task: {e}")
            # If decomposition fails, create a generic subtask
            subtask = Task(
                id=str(uuid.uuid4()),
                name=f"Execute {task.name}",
                description=f"Execute the task: {task.description}",
                is_primitive=True,
                parent_id=task.id
            )
            task.subtasks = [subtask.id]
            return [subtask]
```

### Step 6: Implement Task Executor

```python
class TaskExecutor:
    """Executes primitive tasks using the appropriate tools."""
    
    def __init__(self, agent: Agent):
        """Initialize with an Agno agent."""
        self.agent = agent
    
    async def execute_task(self, task: Task, state: PlanningState) -> str:
        """
        Execute a primitive task and return the results.
        """
        # Mark task as in progress
        task.status = TaskStatus.IN_PROGRESS
        
        # Get task context
        state_summary = state.get_state_summary()
        
        # Check if dependencies have results
        dependency_results = {}
        for dep_id in task.dependencies:
            if dep_id in state.task_results:
                dependency_results[dep_id] = state.task_results[dep_id]
        
        # Prepare prompt for the task execution
        prompt = f"""
        # Task Execution Request
        
        You need to execute the following primitive task:
        
        ## Task Information
        Name: {task.name}
        Description: {task.description}
        
        ## Current State
        {state_summary}
        
        ## Dependency Results
        {"No dependencies." if not dependency_results else ""}
        {json.dumps(dependency_results, indent=2) if dependency_results else ""}
        
        ## Execution Instructions
        
        1. You have access to web search, Wikipedia, and calculator tools
        2. Use these tools as needed to complete the task
        3. Provide a clear, comprehensive result
        4. If the task involves research, include sources
        5. If the task involves writing content, make it well-structured
        
        ## Your Response
        
        Perform the task described above and provide your results below.
        """
        
        try:
            # Execute task using agent
            response = await self.agent.arun(prompt)
            result = response.content
            
            # Update state with results
            if "search" in task.name.lower() or "research" in task.name.lower():
                # For search tasks, add to sources
                source_id = f"source_{len(state.sources) + 1}"
                state.add_source(source_id, result)
            
            if "write" in task.name.lower() or "draft" in task.name.lower() or "create" in task.name.lower():
                # For writing tasks, add to sections
                section_name = task.name.replace("Write ", "").replace("Draft ", "").replace("Create ", "")
                state.add_section(section_name, result)
            
            # Update task results in state
            state.task_results[task.id] = result
            
            return result
            
        except Exception as e:
            print(f"Error executing task: {e}")
            return f"Failed to execute task: {str(e)}"
```

### Step 7: Implement Planning Controller

```python
class HTNPlanningAgent:
    """Main controller for the HTN planning and execution process."""
    
    def __init__(self, api_key=None):
        """Initialize the planning agent."""
        # Set up Agno agent with necessary tools
        self.agent = Agent(
            model=Claude(api_key=api_key),
            instructions="You are an expert research assistant that helps with web research and report writing.",
            tools=[
                DuckDuckGoTools(),
                WikipediaTools(),
                CalculatorTools()
            ],
            temperature=0.5,
            show_tool_calls=True
        )
        
        # Create components
        self.task_manager = TaskManager()
        self.task_decomposer = TaskDecomposer(self.agent)
        self.task_executor = TaskExecutor(self.agent)
        self.state = None
    
    async def create_plan(self, topic: str, goal: str) -> str:
        """
        Create an initial plan for the given topic and goal.
        Returns the root task ID.
        """
        # Initialize state
        self.state = PlanningState(topic=topic)
        
        # Create root task
        root_task_id = self.task_manager.create_task(
            name=f"Research and Write Report on {topic}",
            description=f"Research the topic '{topic}' and create a comprehensive report that {goal}",
            is_primitive=False
        )
        
        return root_task_id
    
    async def execute_plan(self, root_task_id: str, max_steps: int = 20) -> str:
        """
        Execute the plan starting from the root task.
        Returns the final result (report content).
        """
        steps_executed = 0
        
        while steps_executed < max_steps:
            # Get next tasks to process
            next_tasks = self.task_manager.get_next_tasks()
            
            if not next_tasks:
                # Check if root task is completed
                root_task = self.task_manager.get_task(root_task_id)
                if root_task.status == TaskStatus.COMPLETED:
                    return root_task.results
                elif all(task.status == TaskStatus.COMPLETED for task_id, task in self.task_manager.tasks.items()):
                    # All tasks completed but root not marked complete
                    return "Plan execution completed but no final result available."
                else:
                    # No tasks ready but not all completed - might be a dependency issue
                    return "Plan execution stalled - possible circular dependency."
            
            for task in next_tasks:
                if task.is_primitive:
                    # Execute primitive task
                    print(f"Executing task: {task.name}")
                    results = await self.task_executor.execute_task(task, self.state)
                    self.task_manager.mark_task_complete(task.id, results)
                else:
                    # Decompose non-primitive task
                    print(f"Decomposing task: {task.name}")
                    subtasks = await self.task_decomposer.decompose_task(task, self.state)
                    
                    # Add subtasks to task manager
                    for subtask in subtasks:
                        self.task_manager.add_task(subtask)
                    
                    # Update task status
                    task.status = TaskStatus.COMPLETED if not task.subtasks else TaskStatus.DECOMPOSING
                
                steps_executed += 1
                if steps_executed >= max_steps:
                    break
        
        # Return intermediate results if max steps reached
        return f"Plan execution reached maximum steps ({max_steps}). Partial results available."
    
    async def research_and_write_report(self, topic: str, goal: str) -> str:
        """
        End-to-end process to research a topic and write a report.
        """
        print(f"Creating plan for topic: {topic}")
        root_task_id = await self.create_plan(topic, goal)
        
        print("Executing plan...")
        report = await self.execute_plan(root_task_id)
        
        print("Plan execution completed")
        return report
    
    def export_plan(self) -> Dict:
        """Export the current plan and state."""
        return {
            "plan": self.task_manager.export_plan(),
            "state": self.state.to_dict() if self.state else None
        }
    
    def import_plan(self, data: Dict) -> None:
        """Import a plan and state."""
        self.task_manager.import_plan(data["plan"])
        if data["state"]:
            self.state = PlanningState.from_dict(data["state"])
```

### Step 8: Create Custom Tools for Plan Visualization

```python
@tool
def visualize_plan(task_manager: Dict) -> str:
    """
    Create a visualization of the current plan.
    
    Args:
        task_manager: The task manager dictionary representation
        
    Returns:
        A text representation of the plan structure
    """
    tasks = {task_id: Task.from_dict(task_data) 
             for task_id, task_data in task_manager["tasks"].items()}
    root_tasks = task_manager["root_tasks"]
    
    def print_task_tree(task_id, indent=0):
        task = tasks[task_id]
        status_symbol = {
            TaskStatus.PENDING: "⏱️",
            TaskStatus.DECOMPOSING: "🔄",
            TaskStatus.READY: "✅",
            TaskStatus.IN_PROGRESS: "⚙️",
            TaskStatus.COMPLETED: "✓",
            TaskStatus.FAILED: "❌"
        }[task.status]
        
        result = f"{'  ' * indent}{status_symbol} {task.name} ({task.id[:6]}...)\n"
        
        for subtask_id in task.subtasks:
            if subtask_id in tasks:
                result += print_task_tree(subtask_id, indent + 1)
        
        return result
    
    result = "# Current Plan Structure\n\n"
    for root_id in root_tasks:
        result += print_task_tree(root_id)
    
    return result
```

### Step 9: Create the Main Application

```python
async def main():
    # Replace with your API key
    api_key = "YOUR_API_KEY"
    
    # Create the HTN planning agent
    planner = HTNPlanningAgent(api_key=api_key)
    
    # Define research topic and goal
    topic = "Quantum Computing Recent Advancements"
    goal = "explains the most significant advancements in the last 2 years, current challenges, and future prospects"
    
    # Execute the plan
    report = await planner.research_and_write_report(topic, goal)
    
    # Print final report
    print("\n\n====== FINAL REPORT ======\n\n")
    print(report)
    
    # Visualize the final plan
    plan_data = planner.export_plan()
    plan_viz = visualize_plan(plan_data["plan"])
    print("\n\n====== PLAN STRUCTURE ======\n\n")
    print(plan_viz)

if __name__ == "__main__":
    asyncio.run(main())
```

## Advanced Concepts and Extensions

### Adding Plan Adaptation

To make your HTN planner more flexible, add plan adaptation capabilities:

```python
class PlanAdapter:
    """Adapts the plan based on execution results and new information."""
    
    def __init__(self, agent: Agent, task_manager: TaskManager):
        self.agent = agent
        self.task_manager = task_manager
    
    async def evaluate_plan(self, state: PlanningState) -> Dict:
        """
        Evaluate the current plan and suggest adaptations.
        Returns a dictionary of suggestions.
        """
        # Get current plan summary
        tasks = self.task_manager.tasks
        completed_tasks = [t for t in tasks.values() if t.status == TaskStatus.COMPLETED]
        pending_tasks = [t for t in tasks.values() if t.status != TaskStatus.COMPLETED]
        
        # Prepare context for evaluation
        plan_summary = f"""
        Total Tasks: {len(tasks)}
        Completed: {len(completed_tasks)}
        Pending: {len(pending_tasks)}
        
        State Summary:
        {state.get_state_summary()}
        
        Completed Tasks:
        {', '.join(t.name for t in completed_tasks)}
        
        Pending Tasks:
        {', '.join(t.name for t in pending_tasks)}
        """
        
        # Ask LLM for adaptation suggestions
        prompt = f"""
        # Plan Adaptation Request
        
        Analyze the current research plan and suggest adaptations based on what we've learned so far.
        
        ## Current Plan Status
        {plan_summary}
        
        ## Adaptation Requirements
        
        1. Identify gaps in the current research
        2. Suggest new tasks that should be added
        3. Identify tasks that may no longer be necessary
        4. Suggest priority changes for remaining tasks
        
        ## Output Format
        
        Provide your response in the following JSON format:
        
        ```json
        {{
          "gaps_identified": ["gap1", "gap2"],
          "new_tasks": [
            {{
              "name": "New task name",
              "description": "Detailed description",
              "is_primitive": true,
              "after_task": "id of task this should follow",
              "priority": 4
            }}
          ],
          "tasks_to_remove": ["id1", "id2"],
          "priority_changes": [
            {{
              "task_id": "id3",
              "new_priority": 5
            }}
          ]
        }}
        ```
        """
        
        try:
            # Get adaptation suggestions from LLM
            response = await self.agent.arun(prompt)
            content = response.content
            
            # Extract JSON from response
            json_start = content.find('```json')
            json_end = content.rfind('```')
            
            if json_start != -1 and json_end != -1:
                json_content = content[json_start + 7:json_end].strip()
                adaptations = json.loads(json_content)
            else:
                # Try direct parsing if no code blocks found
                adaptations = json.loads(content)
                
            return adaptations
            
        except Exception as e:
            print(f"Error evaluating plan: {e}")
            return {
                "gaps_identified": [],
                "new_tasks": [],
                "tasks_to_remove": [],
                "priority_changes": []
            }
    
    async def adapt_plan(self, state: PlanningState) -> None:
        """
        Adapt the current plan based on evaluation.
        """
        # Evaluate the plan
        adaptations = await self.evaluate_plan(state)
        
        # Process priority changes
        for change in adaptations.get("priority_changes", []):
            task_id = change["task_id"]
            new_priority = change["new_priority"]
            
            if task_id in self.task_manager.tasks:
                self.task_manager.update_task(task_id, priority=new_priority)
        
        # Process task removals (mark as completed with null result)
        for task_id in adaptations.get("tasks_to_remove", []):
            if task_id in self.task_manager.tasks:
                self.task_manager.mark_task_complete(task_id, "Task skipped during plan adaptation")
        
        # Process new tasks
        for task_data in adaptations.get("new_tasks", []):
            # Create new task
            after_task_id = task_data.get("after_task")
            parent_id = None
            
            # Find appropriate parent
            if after_task_id and after_task_id in self.task_manager.tasks:
                after_task = self.task_manager.get_task(after_task_id)
                parent_id = after_task.parent_id
            
            # Create and add the task
            task_id = self.task_manager.create_task(
                name=task_data["name"],
                description=task_data["description"],
                is_primitive=task_data.get("is_primitive", True),
                parent_id=parent_id,
                dependencies=set([after_task_id]) if after_task_id else set()
            )
            
            # If parent exists, add to parent's subtasks
            if parent_id and parent_id in self.task_manager.tasks:
                parent = self.task_manager.get_task(parent_id)
                parent.subtasks.append(task_id)
```

### Integrating with the Main Agent

Update the HTNPlanningAgent class to include plan adaptation:

```python
class HTNPlanningAgent:
    def __init__(self, api_key=None):
        # Existing code...
        
        # Add plan adapter
        self.plan_adapter = PlanAdapter(self.agent, self.task_manager)
        
        # Add adaptation frequency
        self.adaptation_frequency = 5  # Adapt every 5 tasks
    
    async def execute_plan(self, root_task_id: str, max_steps: int = 20) -> str:
        steps_executed = 0
        tasks_since_adaptation = 0
        
        while steps_executed < max_steps:
            # Check if plan adaptation is needed
            if tasks_since_adaptation >= self.adaptation_frequency:
                print("Adapting plan based on current state...")
                await self.plan_adapter.adapt_plan(self.state)
                tasks_since_adaptation = 0
            
            # Rest of execution code...
            
            tasks_since_adaptation += 1
            steps_executed += 1
            
        # Return results...
```

## Case Study: Quantum Computing Research Agent

Let's work through how this HTN planning agent would handle a research and report generation task on quantum computing.

### 1. Initial Plan Creation

Starting with the high-level task "Research and write a report on quantum computing advancements," the agent would:

1. Create the root task
2. Decompose it into subtasks like:
   - Research recent quantum computing breakthroughs
   - Identify current technical challenges
   - Analyze future prospects
   - Create report outline
   - Write introduction section
   - Write main findings section
   - Write conclusion section

### 2. Task Decomposition

Each non-primitive task gets further decomposed:

"Research recent quantum computing breakthroughs" might become:
- Search for quantum computing news from the last 2 years
- Find academic papers on quantum supremacy
- Research quantum hardware advancements
- Identify key industry players and their progress

### 3. Primitive Task Execution

Primitive tasks are executed using appropriate tools:

"Search for quantum computing news" would:
- Use the DuckDuckGo search tool to find relevant articles
- Extract key information from search results
- Organize findings into a structured format
- Update the state with new knowledge

### 4. Dynamic Plan Adaptation

As research progresses:
- The agent discovers quantum error correction is a major challenge
- It adds a new task: "Research quantum error correction advancements"
- It increases the priority of hardware-related research based on findings
- It adds more specific subtasks for report sections

### 5. Report Generation

Once research tasks are complete:
- Writing tasks are executed in the correct order
- Each section is generated based on gathered information
- The complete report is assembled from section results
- The final report includes properly cited sources

## Conclusion

This tutorial demonstrated how to build an HTN Planning Agent using Agno that can:
- Dynamically decompose complex tasks using LLM reasoning
- Execute primitive tasks with appropriate tools
- Maintain state across execution
- Adapt plans based on new information
- Produce comprehensive research reports

This approach combines the strengths of traditional HTN planning with the flexibility of LLM-based task decomposition, creating an agent that can tackle complex, open-ended tasks with minimal supervision.

The architecture can be extended to handle various domains beyond research, such as:
- Project planning and management
- Complex customer service workflows
- Content creation pipelines
- Educational tutoring systems
- Data analysis workflows

By separating the concerns of task decomposition, execution, and adaptation, this architecture provides a robust foundation for building sophisticated AI agents capable of extended reasoning and planning.