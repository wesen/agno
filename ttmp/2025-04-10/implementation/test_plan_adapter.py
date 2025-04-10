"""
Unit tests for PlanAdapter class.
"""

import unittest
import asyncio
import json
from task_primitives import Task, TaskStatus, TaskManager
from planning_state import PlanningState
from plan_adapter import PlanAdapter


class MockPlanAdapterAgent:
    """Mock agent for testing PlanAdapter."""
    
    async def arun(self, prompt: str) -> object:
        """Return a mock adaptation response."""
        return type('obj', (object,), {
            'content': '''```json
            {
              "gaps_identified": ["Missing analysis of quantum error correction"],
              "new_tasks": [
                {
                  "name": "Research quantum error correction",
                  "description": "Find recent breakthroughs in quantum error correction techniques",
                  "is_primitive": true,
                  "after_task": "task1",
                  "priority": 4
                }
              ],
              "tasks_to_remove": ["task3"],
              "priority_changes": [
                {
                  "task_id": "task2",
                  "new_priority": 5
                }
              ]
            }
            ```'''
        })


class TestPlanAdapter(unittest.TestCase):
    """Test cases for the PlanAdapter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.task_manager = TaskManager()
        self.mock_agent = MockPlanAdapterAgent()
        self.plan_adapter = PlanAdapter(self.mock_agent, self.task_manager)
        self.state = PlanningState(topic="Test Topic")
        
        # Add some tasks to the task manager
        self.task1_id = self.task_manager.create_task(
            name="Task 1",
            description="First task",
            is_primitive=True
        )
        
        self.task2_id = self.task_manager.create_task(
            name="Task 2",
            description="Second task",
            is_primitive=True
        )
        
        self.task3_id = self.task_manager.create_task(
            name="Task 3",
            description="Third task",
            is_primitive=True
        )
        
        # Set task IDs to match mock response
        task1 = self.task_manager.get_task(self.task1_id)
        task1.id = "task1"
        task2 = self.task_manager.get_task(self.task2_id)
        task2.id = "task2"
        task3 = self.task_manager.get_task(self.task3_id)
        task3.id = "task3"
        
        # Update task_manager's internal mappings
        self.task_manager.tasks = {
            "task1": task1,
            "task2": task2,
            "task3": task3
        }
        self.task_manager.root_tasks = ["task1", "task2", "task3"]

    def test_evaluate_plan(self):
        """Test evaluating a plan for adaptations."""
        # Run the evaluation
        adaptations = asyncio.run(self.plan_adapter.evaluate_plan(self.state))
        
        # Check the adaptations
        self.assertEqual(len(adaptations["gaps_identified"]), 1)
        self.assertEqual(adaptations["gaps_identified"][0], "Missing analysis of quantum error correction")
        
        self.assertEqual(len(adaptations["new_tasks"]), 1)
        self.assertEqual(adaptations["new_tasks"][0]["name"], "Research quantum error correction")
        
        self.assertEqual(adaptations["tasks_to_remove"], ["task3"])
        
        self.assertEqual(len(adaptations["priority_changes"]), 1)
        self.assertEqual(adaptations["priority_changes"][0]["task_id"], "task2")
        self.assertEqual(adaptations["priority_changes"][0]["new_priority"], 5)

    def test_adapt_plan(self):
        """Test adapting a plan based on evaluation."""
        # Run the adaptation
        asyncio.run(self.plan_adapter.adapt_plan(self.state))
        
        # Check task prioritization change
        task2 = self.task_manager.get_task("task2")
        self.assertEqual(task2.priority, 5)
        
        # Check task removal (should be marked as completed)
        task3 = self.task_manager.get_task("task3")
        self.assertEqual(task3.status, TaskStatus.COMPLETED)
        self.assertIn("skipped", task3.results)
        
        # Check new task creation
        self.assertGreater(len(self.task_manager.tasks), 3)
        
        # Find the new task by name
        new_task = None
        for task in self.task_manager.tasks.values():
            if task.name == "Research quantum error correction":
                new_task = task
                break
        
        self.assertIsNotNone(new_task)
        self.assertEqual(new_task.description, "Find recent breakthroughs in quantum error correction techniques")
        self.assertTrue(new_task.is_primitive)
        self.assertEqual(new_task.dependencies, {"task1"})
        self.assertEqual(new_task.priority, 4)


if __name__ == '__main__':
    unittest.main()