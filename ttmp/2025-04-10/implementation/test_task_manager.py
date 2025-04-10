"""
Unit tests for TaskManager class.
"""

import unittest
from task_primitives import Task, TaskStatus, TaskManager


class TestTaskManager(unittest.TestCase):
    """Test cases for the TaskManager class."""

    def setUp(self):
        """Set up a task manager for each test."""
        self.manager = TaskManager()

    def test_empty_manager(self):
        """Test a new task manager is empty."""
        self.assertEqual(len(self.manager.tasks), 0)
        self.assertEqual(len(self.manager.root_tasks), 0)
        self.assertEqual(self.manager.get_next_tasks(), [])

    def test_add_task(self):
        """Test adding a task to the manager."""
        task = Task(
            id="task1",
            name="Test Task",
            description="Test Description"
        )
        
        task_id = self.manager.add_task(task)
        
        self.assertEqual(task_id, "task1")
        self.assertEqual(len(self.manager.tasks), 1)
        self.assertIn("task1", self.manager.tasks)
        self.assertEqual(self.manager.tasks["task1"], task)
        self.assertIn("task1", self.manager.root_tasks)

    def test_add_child_task(self):
        """Test adding a child task."""
        parent = Task(
            id="parent1",
            name="Parent Task",
            description="Parent Description"
        )
        
        child = Task(
            id="child1",
            name="Child Task",
            description="Child Description",
            parent_id="parent1"
        )
        
        self.manager.add_task(parent)
        self.manager.add_task(child)
        
        self.assertEqual(len(self.manager.tasks), 2)
        self.assertEqual(len(self.manager.root_tasks), 1)
        self.assertIn("parent1", self.manager.root_tasks)
        self.assertNotIn("child1", self.manager.root_tasks)

    def test_create_task(self):
        """Test creating a task through the manager."""
        task_id = self.manager.create_task(
            name="Created Task",
            description="Created Description",
            is_primitive=True
        )
        
        self.assertEqual(len(self.manager.tasks), 1)
        self.assertEqual(len(self.manager.root_tasks), 1)
        
        created_task = self.manager.get_task(task_id)
        self.assertEqual(created_task.name, "Created Task")
        self.assertEqual(created_task.description, "Created Description")
        self.assertTrue(created_task.is_primitive)

    def test_get_task(self):
        """Test getting a task by ID."""
        task_id = self.manager.create_task(
            name="Get Task",
            description="Test get_task method"
        )
        
        # Get existing task
        task = self.manager.get_task(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task.name, "Get Task")
        
        # Get non-existent task
        nonexistent = self.manager.get_task("nonexistent")
        self.assertIsNone(nonexistent)

    def test_update_task(self):
        """Test updating a task's properties."""
        task_id = self.manager.create_task(
            name="Update Task",
            description="Before update"
        )
        
        self.manager.update_task(
            task_id,
            description="After update",
            is_primitive=True,
            priority=3
        )
        
        updated_task = self.manager.get_task(task_id)
        self.assertEqual(updated_task.description, "After update")
        self.assertTrue(updated_task.is_primitive)
        self.assertEqual(updated_task.priority, 3)
        
        # Test updating non-existent task
        with self.assertRaises(ValueError):
            self.manager.update_task("nonexistent", description="Error")

    def test_get_next_tasks_empty(self):
        """Test get_next_tasks with no tasks."""
        next_tasks = self.manager.get_next_tasks()
        self.assertEqual(next_tasks, [])

    def test_get_next_tasks_with_dependencies(self):
        """Test get_next_tasks with dependencies."""
        # Create tasks with dependencies
        task1_id = self.manager.create_task(
            name="Task 1",
            description="First task",
            is_primitive=True
        )
        
        task2_id = self.manager.create_task(
            name="Task 2",
            description="Second task",
            is_primitive=True,
            dependencies={task1_id}
        )
        
        # Initially, only task1 should be ready (no dependencies)
        next_tasks = self.manager.get_next_tasks()
        self.assertEqual(len(next_tasks), 1)
        self.assertEqual(next_tasks[0].id, task1_id)
        
        # Mark task1 as complete
        self.manager.mark_task_complete(task1_id, "Task 1 results")
        
        # Now task2 should be ready
        next_tasks = self.manager.get_next_tasks()
        self.assertEqual(len(next_tasks), 1)
        self.assertEqual(next_tasks[0].id, task2_id)

    def test_get_next_tasks_priority_order(self):
        """Test get_next_tasks returns tasks in priority order."""
        # Create tasks with different priorities
        task1_id = self.manager.create_task(
            name="Low Priority",
            description="Priority 1",
            is_primitive=True
        )
        # Set priority after creation
        task1 = self.manager.get_task(task1_id)
        task1.priority = 1
        
        task2_id = self.manager.create_task(
            name="High Priority",
            description="Priority 5",
            is_primitive=True
        )
        # Set priority after creation
        task2 = self.manager.get_task(task2_id)
        task2.priority = 5
        
        task3_id = self.manager.create_task(
            name="Medium Priority",
            description="Priority 3",
            is_primitive=True
        )
        # Set priority after creation
        task3 = self.manager.get_task(task3_id)
        task3.priority = 3
        
        # Get tasks in priority order
        next_tasks = self.manager.get_next_tasks()
        self.assertEqual(len(next_tasks), 3)
        
        # Should be sorted highest priority first
        self.assertEqual(next_tasks[0].id, task2_id)  # Priority 5
        self.assertEqual(next_tasks[1].id, task3_id)  # Priority 3
        self.assertEqual(next_tasks[2].id, task1_id)  # Priority 1

    def test_mark_task_complete(self):
        """Test marking a task as complete."""
        task_id = self.manager.create_task(
            name="Complete Task",
            description="Test completion",
            is_primitive=True
        )
        
        # Before completion
        task = self.manager.get_task(task_id)
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertIsNone(task.results)
        
        # Mark complete with results
        self.manager.mark_task_complete(task_id, "Completion results")
        
        # After completion
        task = self.manager.get_task(task_id)
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertEqual(task.results, "Completion results")
        
        # Test completing non-existent task
        with self.assertRaises(ValueError):
            self.manager.mark_task_complete("nonexistent")

    def test_parent_task_auto_completion(self):
        """Test that parent tasks are marked complete when all subtasks are complete."""
        # Create a parent task
        parent_id = self.manager.create_task(
            name="Parent Task",
            description="Parent for auto-completion test"
        )
        
        # Create child tasks
        child1_id = self.manager.create_task(
            name="Child 1",
            description="First child",
            is_primitive=True,
            parent_id=parent_id
        )
        
        child2_id = self.manager.create_task(
            name="Child 2",
            description="Second child",
            is_primitive=True,
            parent_id=parent_id
        )
        
        # Set up parent-child relationship
        parent = self.manager.get_task(parent_id)
        parent.subtasks = [child1_id, child2_id]
        
        # Complete first child
        self.manager.mark_task_complete(child1_id, "Child 1 results")
        
        # Parent should not be complete yet
        parent = self.manager.get_task(parent_id)
        self.assertNotEqual(parent.status, TaskStatus.COMPLETED)
        
        # Complete second child
        self.manager.mark_task_complete(child2_id, "Child 2 results")
        
        # Parent should now be complete
        parent = self.manager.get_task(parent_id)
        self.assertEqual(parent.status, TaskStatus.COMPLETED)
        
        # Check parent results combine child results
        self.assertIn("Child 1", parent.results)
        self.assertIn("Child 1 results", parent.results)
        self.assertIn("Child 2", parent.results)
        self.assertIn("Child 2 results", parent.results)

    def test_get_task_results(self):
        """Test getting results from a completed task."""
        task_id = self.manager.create_task(
            name="Results Task",
            description="Test results getter",
            is_primitive=True
        )
        
        # Before completion
        with self.assertRaises(ValueError) as context:
            self.manager.get_task_results("nonexistent")
        self.assertIn("not found", str(context.exception))
        
        results = self.manager.get_task_results(task_id)
        self.assertIsNone(results)
        
        # Mark complete with results
        self.manager.mark_task_complete(task_id, "Task results here")
        
        # After completion
        results = self.manager.get_task_results(task_id)
        self.assertEqual(results, "Task results here")

    def test_export_import_plan(self):
        """Test exporting and importing a plan."""
        # Create a completely new manager
        manager = TaskManager()
        
        # Create some tasks
        task1_id = manager.create_task(
            name="Task 1",
            description="First task for export",
            is_primitive=True
        )
        
        task2_id = manager.create_task(
            name="Task 2",
            description="Second task for export",
            is_primitive=True,
            dependencies={task1_id}
        )
        
        # Mark first task complete
        manager.mark_task_complete(task1_id, "Task 1 export results")
        
        # Check initial state
        print(f"Original root_tasks: {manager.root_tasks}")
        
        # Export the plan
        exported_plan = manager.export_plan()
        print(f"Exported root_tasks: {exported_plan['root_tasks']}")
        
        # Create a new manager and import the plan
        new_manager = TaskManager()
        new_manager.import_plan(exported_plan)
        
        # Check imported state
        print(f"Imported root_tasks: {new_manager.root_tasks}")
        
        # Verify tasks were imported correctly
        self.assertEqual(len(new_manager.tasks), 2)
        self.assertEqual(len(new_manager.root_tasks), len(manager.root_tasks))
        
        imported_task1 = new_manager.get_task(task1_id)
        imported_task2 = new_manager.get_task(task2_id)
        
        self.assertEqual(imported_task1.name, "Task 1")
        self.assertEqual(imported_task1.status, TaskStatus.COMPLETED)
        self.assertEqual(imported_task1.results, "Task 1 export results")
        
        self.assertEqual(imported_task2.name, "Task 2")
        self.assertEqual(imported_task2.status, TaskStatus.PENDING)
        self.assertEqual(imported_task2.dependencies, {task1_id})


if __name__ == '__main__':
    unittest.main()