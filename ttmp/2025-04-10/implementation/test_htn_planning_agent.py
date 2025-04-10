"""
Unit tests for HTNPlanningAgent class.
"""

import unittest
import asyncio
import json
from task_primitives import Task, TaskStatus
from planning_state import PlanningState
from task_executor import MockAgent
from htn_planning_agent import HTNPlanningAgent


class TestHTNPlanningAgent(unittest.TestCase):
    """Test cases for the HTNPlanningAgent class."""

    def setUp(self):
        """Set up common test objects."""
        self.mock_agent = MockAgent()
        self.planner = HTNPlanningAgent(self.mock_agent)

    def test_initialization(self):
        """Test that agent initializes correctly."""
        self.assertEqual(self.planner.agent, self.mock_agent)
        self.assertIsInstance(self.planner.task_manager, object)
        self.assertIsInstance(self.planner.task_decomposer, object)
        self.assertIsInstance(self.planner.task_executor, object)
        self.assertIsNone(self.planner.state)

    def test_create_plan(self):
        """Test creating a plan."""
        # Create a plan
        root_task_id = asyncio.run(self.planner.create_plan(
            topic="Quantum Computing", 
            goal="explains recent developments"
        ))
        
        # Check that a task was created
        self.assertIsNotNone(root_task_id)
        self.assertEqual(len(self.planner.task_manager.tasks), 1)
        self.assertEqual(len(self.planner.task_manager.root_tasks), 1)
        
        # Check the task properties
        root_task = self.planner.task_manager.get_task(root_task_id)
        self.assertEqual(root_task.name, "Research and Write Report on Quantum Computing")
        self.assertIn("explains recent developments", root_task.description)
        self.assertFalse(root_task.is_primitive)
        
        # Check that state was initialized
        self.assertIsNotNone(self.planner.state)
        self.assertEqual(self.planner.state.topic, "Quantum Computing")

    def test_execute_plan_single_step(self):
        """Test executing a plan for one step."""
        # Create a plan
        root_task_id = asyncio.run(self.planner.create_plan(
            topic="Test Topic", 
            goal="tests the execution"
        ))
        
        # Execute one step (should decompose the root task)
        result = asyncio.run(self.planner.execute_plan(root_task_id, max_steps=1))
        
        # Check that root task was decomposed
        root_task = self.planner.task_manager.get_task(root_task_id)
        self.assertEqual(root_task.status, TaskStatus.DECOMPOSING)
        self.assertGreater(len(root_task.subtasks), 0)
        
        # Check that subtasks were created
        self.assertGreater(len(self.planner.task_manager.tasks), 1)
        
        # Since we only ran one step, the plan shouldn't be complete
        self.assertIn("steps", result)

    def test_get_plan_status(self):
        """Test getting plan status."""
        # Before creating a plan
        status = self.planner.get_plan_status()
        self.assertEqual(status, {"status": "No plan created"})
        
        # Create a plan
        asyncio.run(self.planner.create_plan("Status Test", "tests status reporting"))
        
        # After creating a plan
        status = self.planner.get_plan_status()
        self.assertEqual(status["topic"], "Status Test")
        self.assertEqual(status["total_tasks"], 1)
        self.assertEqual(status["completed"], 0)
        self.assertEqual(status["pending"], 1)
        
        # Run one step to decompose the root task
        asyncio.run(self.planner.execute_plan(self.planner.task_manager.root_tasks[0], max_steps=1))
        
        # After decomposition
        status = self.planner.get_plan_status()
        self.assertGreater(status["total_tasks"], 1)
        self.assertEqual(status["decomposing"], 1)

    def test_visualize_plan(self):
        """Test plan visualization."""
        # Before creating a plan
        visualization = self.planner.visualize_plan()
        self.assertEqual(visualization, "No plan available")
        
        # Create a plan
        asyncio.run(self.planner.create_plan("Visualization Test", "tests visualization"))
        
        # After creating a plan
        visualization = self.planner.visualize_plan()
        self.assertIn("Current Plan Structure", visualization)
        self.assertIn("Research and Write Report on Visualization Test", visualization)
        
        # Run one step to decompose the root task
        asyncio.run(self.planner.execute_plan(self.planner.task_manager.root_tasks[0], max_steps=1))
        
        # After decomposition - should show more tasks
        visualization = self.planner.visualize_plan()
        # This assumes the mock agent creates at least 2 subtasks
        self.assertGreaterEqual(visualization.count('\n'), 3)  # At least 3 lines

    def test_export_import_plan(self):
        """Test exporting and importing a plan."""
        # Create and execute part of a plan
        asyncio.run(self.planner.create_plan("Export Test", "tests export/import"))
        asyncio.run(self.planner.execute_plan(self.planner.task_manager.root_tasks[0], max_steps=2))
        
        # Export the plan
        exported_plan = self.planner.export_plan()
        self.assertIn("plan", exported_plan)
        self.assertIn("state", exported_plan)
        
        # Verify content of exported plan
        self.assertIn("tasks", exported_plan["plan"])
        self.assertIn("root_tasks", exported_plan["plan"])
        self.assertEqual(exported_plan["state"]["topic"], "Export Test")
        
        # Create a new planner and import the plan
        new_planner = HTNPlanningAgent(self.mock_agent)
        new_planner.import_plan(exported_plan)
        
        # Verify that the plan was imported correctly
        self.assertEqual(len(new_planner.task_manager.tasks), len(self.planner.task_manager.tasks))
        self.assertEqual(len(new_planner.task_manager.root_tasks), len(self.planner.task_manager.root_tasks))
        self.assertEqual(new_planner.state.topic, self.planner.state.topic)

    def test_end_to_end_small_plan(self):
        """Test an end-to-end research and report process with a small plan."""
        # Run the complete process with a small max_steps
        report = asyncio.run(self.planner.research_and_write_report(
            topic="Mini Topic",
            goal="creates a mini report",
            max_steps=5  # Small enough to complete quickly, but show progress
        ))
        
        # Verify some output was produced
        self.assertIsNotNone(report)
        self.assertNotEqual(report, "")
        
        # Check plan status
        status = self.planner.get_plan_status()
        self.assertGreater(status["total_tasks"], 1)
        
        # Should have gathered some information
        self.assertGreaterEqual(len(self.planner.state.facts) + 
                               len(self.planner.state.sources) + 
                               len(self.planner.state.sections), 1)


if __name__ == '__main__':
    unittest.main()