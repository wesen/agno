"""
Task representation and management primitives for HTN Planning Agent.
"""

import uuid
from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field


class TaskStatus(Enum):
    """
    Represents the status of a task in the HTN planning system.
    """
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
                if subtask_id in self.tasks
            )
            
            if all_subtasks_complete:
                # Combine results from subtasks
                combined_results = "\n\n".join([
                    f"## {self.tasks[subtask_id].name}\n{self.tasks[subtask_id].results or 'No results'}"
                    for subtask_id in parent.subtasks
                    if subtask_id in self.tasks
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
        # Clear existing data first
        self.tasks = {}
        self.root_tasks = []
        
        # Import tasks
        self.tasks = {
            task_id: Task.from_dict(task_data)
            for task_id, task_data in plan_data["tasks"].items()
        }
        
        # Import root tasks
        self.root_tasks = plan_data["root_tasks"].copy()