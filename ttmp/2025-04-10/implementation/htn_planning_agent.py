"""
HTN Planning Agent implementation.

This module provides the main controller for the HTN planning and execution process.
"""

import asyncio
import sys
import os
from typing import Dict, List, Optional, Any

# Import directly for test compatibility
# In regular package use, these would already be imported from the package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from task_primitives import Task, TaskStatus, TaskManager
from planning_state import PlanningState
from task_decomposer import TaskDecomposer
from task_executor import TaskExecutor
from plan_adapter import PlanAdapter


class HTNPlanningAgent:
    """Main controller for the HTN planning and execution process."""
    
    def __init__(self, agent: Any):
        """
        Initialize the planning agent.
        
        Args:
            agent: An Agno agent or compatible interface that provides an arun method.
        """
        self.agent = agent
        
        # Create components
        self.task_manager = TaskManager()
        self.task_decomposer = TaskDecomposer(agent)
        self.task_executor = TaskExecutor(agent)
        self.plan_adapter = PlanAdapter(agent, self.task_manager)
        self.state = None
        
        # Configuration
        self.adaptation_frequency = 5  # Adapt every 5 tasks
    
    async def create_plan(self, topic: str, goal: str) -> str:
        """
        Create an initial plan for the given topic and goal.
        
        Args:
            topic: The research topic
            goal: The goal or purpose of the research
            
        Returns:
            The root task ID
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
        
        Args:
            root_task_id: The ID of the root task
            max_steps: Maximum number of steps to execute
            
        Returns:
            The final result (report content)
        """
        steps_executed = 0
        tasks_since_adaptation = 0
        
        while steps_executed < max_steps:
            # Check if plan adaptation is needed
            if tasks_since_adaptation >= self.adaptation_frequency:
                print("Adapting plan based on current state...")
                await self.plan_adapter.adapt_plan(self.state)
                tasks_since_adaptation = 0
                
            # Get next tasks to process
            next_tasks = self.task_manager.get_next_tasks()
            
            if not next_tasks:
                # Check if root task is completed
                root_task = self.task_manager.get_task(root_task_id)
                if root_task and root_task.status == TaskStatus.COMPLETED:
                    return root_task.results
                elif all(task.status == TaskStatus.COMPLETED 
                        for task_id, task in self.task_manager.tasks.items()):
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
                    
                    # Update task status if it has no subtasks
                    if not task.subtasks:
                        task.status = TaskStatus.COMPLETED
                
                steps_executed += 1
                tasks_since_adaptation += 1
                if steps_executed >= max_steps:
                    break
        
        # Return intermediate results if max steps reached
        return f"Plan execution reached maximum steps ({max_steps}). Partial results available."
    
    async def research_and_write_report(self, topic: str, goal: str, max_steps: int = 20) -> str:
        """
        End-to-end process to research a topic and write a report.
        
        Args:
            topic: The research topic
            goal: The goal or purpose of the research
            max_steps: Maximum number of steps to execute
            
        Returns:
            The final report content
        """
        print(f"Creating plan for topic: {topic}")
        root_task_id = await self.create_plan(topic, goal)
        
        print("Executing plan...")
        report = await self.execute_plan(root_task_id, max_steps)
        
        print("Plan execution completed")
        return report
    
    def export_plan(self) -> Dict:
        """
        Export the current plan and state.
        
        Returns:
            Dictionary with plan and state
        """
        return {
            "plan": self.task_manager.export_plan(),
            "state": self.state.to_dict() if self.state else None
        }
    
    def import_plan(self, data: Dict) -> None:
        """
        Import a plan and state.
        
        Args:
            data: Dictionary with plan and state
        """
        self.task_manager.import_plan(data["plan"])
        if data["state"]:
            self.state = PlanningState.from_dict(data["state"])
    
    def get_plan_status(self) -> Dict:
        """
        Get the current status of the plan.
        
        Returns:
            Dictionary with plan status information
        """
        if not self.state:
            return {"status": "No plan created"}
        
        tasks = self.task_manager.tasks
        completed_count = sum(1 for t in tasks.values() if t.status == TaskStatus.COMPLETED)
        pending_count = sum(1 for t in tasks.values() if t.status == TaskStatus.PENDING)
        in_progress_count = sum(1 for t in tasks.values() if t.status == TaskStatus.IN_PROGRESS)
        decomposing_count = sum(1 for t in tasks.values() if t.status == TaskStatus.DECOMPOSING)
        failed_count = sum(1 for t in tasks.values() if t.status == TaskStatus.FAILED)
        
        return {
            "topic": self.state.topic,
            "total_tasks": len(tasks),
            "completed": completed_count,
            "pending": pending_count,
            "in_progress": in_progress_count,
            "decomposing": decomposing_count,
            "failed": failed_count,
            "facts_gathered": len(self.state.facts),
            "sources_found": len(self.state.sources),
            "sections_written": len(self.state.sections)
        }
    
    def visualize_plan(self) -> str:
        """
        Create a visualization of the current plan.
        
        Returns:
            A text representation of the plan structure
        """
        if not self.task_manager.tasks:
            return "No plan available"
        
        result = "# Current Plan Structure\n\n"
        
        def print_task_tree(task_id, indent=0):
            task = self.task_manager.get_task(task_id)
            if not task:
                return f"{'  ' * indent}Task {task_id} not found\n"
            
            status_symbol = {
                TaskStatus.PENDING: "⏱️",
                TaskStatus.DECOMPOSING: "🔄",
                TaskStatus.READY: "✅",
                TaskStatus.IN_PROGRESS: "⚙️",
                TaskStatus.COMPLETED: "✓",
                TaskStatus.FAILED: "❌"
            }[task.status]
            
            task_output = f"{'  ' * indent}{status_symbol} {task.name} ({task.id[:6]}...)\n"
            
            for subtask_id in task.subtasks:
                task_output += print_task_tree(subtask_id, indent + 1)
            
            return task_output
        
        for root_id in self.task_manager.root_tasks:
            result += print_task_tree(root_id)
        
        return result