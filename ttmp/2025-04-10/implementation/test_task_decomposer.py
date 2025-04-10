"""
Unit tests for TaskDecomposer class.
"""

import unittest
import asyncio
from task_primitives import Task, TaskStatus
from planning_state import PlanningState
from task_decomposer import TaskDecomposer, MockAgent


class TestTaskDecomposer(unittest.TestCase):
    """Test cases for the TaskDecomposer class."""

    def setUp(self):
        """Set up common test objects."""
        self.mock_agent = MockAgent()
        self.decomposer = TaskDecomposer(self.mock_agent)
        self.state = PlanningState(topic="Test Topic")

    def test_initialization(self):
        """Test that decomposer initializes correctly."""
        self.assertEqual(self.decomposer.agent, self.mock_agent)

    def test_decompose_research_task(self):
        """Test decomposing a research task."""
        # Create a research task
        task = Task(
            id="research1",
            name="Research quantum computing",
            description="Research recent developments in quantum computing",
            is_primitive=False
        )
        
        # Run the decomposition
        subtasks = asyncio.run(self.decomposer.decompose_task(task, self.state))
        
        # Check the results
        self.assertEqual(len(subtasks), 3)
        self.assertEqual(task.status, TaskStatus.DECOMPOSING)
        self.assertEqual(len(task.subtasks), 3)
        
        # Check subtask names
        subtask_names = [subtask.name for subtask in subtasks]
        self.assertIn("Search for recent papers", subtask_names)
        self.assertIn("Identify key researchers", subtask_names)
        self.assertIn("Analyze trends", subtask_names)
        
        # Check that subtasks have the parent set correctly
        for subtask in subtasks:
            self.assertEqual(subtask.parent_id, "research1")
        
        # Check dependencies
        for subtask in subtasks:
            if subtask.name == "Analyze trends":
                # This subtask should depend on the "Search for recent papers" subtask
                self.assertEqual(len(subtask.dependencies), 1)
            else:
                # These subtasks have no dependencies
                self.assertEqual(len(subtask.dependencies), 0)

    def test_decompose_writing_task(self):
        """Test decomposing a writing task."""
        # Create a writing task
        task = Task(
            id="write1",
            name="Write report",
            description="Write a comprehensive report on the findings",
            is_primitive=False
        )
        
        # Run the decomposition
        subtasks = asyncio.run(self.decomposer.decompose_task(task, self.state))
        
        # Check the results
        self.assertEqual(len(subtasks), 3)
        self.assertEqual(task.status, TaskStatus.DECOMPOSING)
        
        # Check subtask names and parent relationships
        subtask_names = [subtask.name for subtask in subtasks]
        self.assertIn("Create outline", subtask_names)
        self.assertIn("Write introduction", subtask_names)
        self.assertIn("Write conclusion", subtask_names)
        
        # Check dependencies chain
        create_outline_id = None
        write_intro_id = None
        
        for subtask in subtasks:
            if subtask.name == "Create outline":
                create_outline_id = subtask.id
                self.assertEqual(len(subtask.dependencies), 0)
            elif subtask.name == "Write introduction":
                write_intro_id = subtask.id
                # Should depend on "Create outline"
                self.assertEqual(len(subtask.dependencies), 1)
            elif subtask.name == "Write conclusion":
                # Should depend on "Write introduction"
                self.assertEqual(len(subtask.dependencies), 1)
        
        # Verify the dependency chain
        intro_task = next(task for task in subtasks if task.name == "Write introduction")
        conclusion_task = next(task for task in subtasks if task.name == "Write conclusion")
        
        self.assertTrue(create_outline_id in intro_task.dependencies)
        self.assertTrue(write_intro_id in conclusion_task.dependencies)

    def test_decompose_generic_task(self):
        """Test decomposing a generic task."""
        # Create a generic task
        task = Task(
            id="generic1",
            name="Generic task",
            description="A task that doesn't match specific patterns",
            is_primitive=False
        )
        
        # Run the decomposition
        subtasks = asyncio.run(self.decomposer.decompose_task(task, self.state))
        
        # Check the results
        self.assertEqual(len(subtasks), 2)
        self.assertEqual(task.status, TaskStatus.DECOMPOSING)
        
        # Check subtask names and parent relationships
        subtask_names = [subtask.name for subtask in subtasks]
        self.assertIn("Generic subtask 1", subtask_names)
        self.assertIn("Generic subtask 2", subtask_names)
        
        # Check specific tasks
        subtask1 = next(task for task in subtasks if task.name == "Generic subtask 1")
        subtask2 = next(task for task in subtasks if task.name == "Generic subtask 2")
        
        # Check properties
        self.assertEqual(subtask1.description, "First generic subtask")
        self.assertTrue(subtask1.is_primitive)
        self.assertEqual(len(subtask1.dependencies), 0)
        
        self.assertEqual(subtask2.description, "Second generic subtask")
        self.assertTrue(subtask2.is_primitive)
        self.assertEqual(len(subtask2.dependencies), 1)
        self.assertTrue(subtask1.id in subtask2.dependencies)

    def test_error_handling(self):
        """Test error handling during decomposition."""
        # Create a task
        task = Task(
            id="error1",
            name="Error task",
            description="A task that will cause an error",
            is_primitive=False
        )
        
        # Create a decomposer with a broken agent
        class BrokenAgent:
            async def arun(self, prompt):
                raise ValueError("Simulated error")
        
        broken_decomposer = TaskDecomposer(BrokenAgent())
        
        # Run the decomposition
        subtasks = asyncio.run(broken_decomposer.decompose_task(task, self.state))
        
        # Check that we get a fallback subtask
        self.assertEqual(len(subtasks), 1)
        self.assertEqual(subtasks[0].name, "Execute Error task")
        self.assertEqual(subtasks[0].description, "Execute the task: A task that will cause an error")
        self.assertTrue(subtasks[0].is_primitive)
        self.assertEqual(subtasks[0].parent_id, "error1")


if __name__ == '__main__':
    unittest.main()