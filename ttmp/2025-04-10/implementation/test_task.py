"""
Unit tests for Task class.
"""

import unittest
from task_primitives import Task, TaskStatus


class TestTask(unittest.TestCase):
    """Test cases for the Task class."""

    def test_task_initialization(self):
        """Test that a task can be initialized with basic properties."""
        task = Task(
            id="123", 
            name="Test Task", 
            description="This is a test task"
        )
        
        self.assertEqual(task.id, "123")
        self.assertEqual(task.name, "Test Task")
        self.assertEqual(task.description, "This is a test task")
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertIsNone(task.parent_id)
        self.assertFalse(task.is_primitive)
        self.assertEqual(task.dependencies, set())
        self.assertIsNone(task.results)
        self.assertEqual(task.subtasks, [])
        self.assertIsNone(task.estimated_time)
        self.assertEqual(task.priority, 1)

    def test_task_with_custom_values(self):
        """Test that a task can be initialized with custom values."""
        task = Task(
            id="456", 
            name="Complex Task", 
            description="A complex task",
            status=TaskStatus.IN_PROGRESS,
            parent_id="parent123",
            is_primitive=True,
            dependencies={"dep1", "dep2"},
            results="Some results",
            subtasks=["subtask1", "subtask2"],
            estimated_time=30,
            priority=5
        )
        
        self.assertEqual(task.id, "456")
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(task.parent_id, "parent123")
        self.assertTrue(task.is_primitive)
        self.assertEqual(task.dependencies, {"dep1", "dep2"})
        self.assertEqual(task.results, "Some results")
        self.assertEqual(task.subtasks, ["subtask1", "subtask2"])
        self.assertEqual(task.estimated_time, 30)
        self.assertEqual(task.priority, 5)

    def test_to_dict_method(self):
        """Test that a task can be converted to a dictionary."""
        task = Task(
            id="789", 
            name="Dict Task", 
            description="Test to_dict",
            status=TaskStatus.COMPLETED,
            dependencies={"dep3"},
            results="Dict results"
        )
        
        task_dict = task.to_dict()
        
        self.assertEqual(task_dict["id"], "789")
        self.assertEqual(task_dict["name"], "Dict Task")
        self.assertEqual(task_dict["description"], "Test to_dict")
        self.assertEqual(task_dict["status"], "completed")
        self.assertEqual(task_dict["dependencies"], ["dep3"])
        self.assertEqual(task_dict["results"], "Dict results")

    def test_from_dict_method(self):
        """Test that a task can be created from a dictionary."""
        task_dict = {
            "id": "abc",
            "name": "From Dict",
            "description": "Created from dict",
            "status": "ready",
            "parent_id": "parent456",
            "is_primitive": True,
            "dependencies": ["dep4", "dep5"],
            "results": None,
            "subtasks": [],
            "estimated_time": 15,
            "priority": 3
        }
        
        task = Task.from_dict(task_dict)
        
        self.assertEqual(task.id, "abc")
        self.assertEqual(task.name, "From Dict")
        self.assertEqual(task.status, TaskStatus.READY)
        self.assertEqual(task.parent_id, "parent456")
        self.assertTrue(task.is_primitive)
        self.assertEqual(task.dependencies, {"dep4", "dep5"})
        self.assertIsNone(task.results)
        self.assertEqual(task.subtasks, [])
        self.assertEqual(task.estimated_time, 15)
        self.assertEqual(task.priority, 3)

    def test_serialization_roundtrip(self):
        """Test serialization and deserialization roundtrip."""
        original_task = Task(
            id="xyz", 
            name="Roundtrip",
            description="Test serialization roundtrip",
            status=TaskStatus.FAILED,
            parent_id="parentXYZ",
            is_primitive=False,
            dependencies={"dep6", "dep7"},
            results="Roundtrip results",
            subtasks=["sub1", "sub2", "sub3"],
            estimated_time=45,
            priority=2
        )
        
        # Convert to dict and back to Task
        task_dict = original_task.to_dict()
        reconstructed_task = Task.from_dict(task_dict)
        
        # Verify all properties match
        self.assertEqual(reconstructed_task.id, original_task.id)
        self.assertEqual(reconstructed_task.name, original_task.name)
        self.assertEqual(reconstructed_task.description, original_task.description)
        self.assertEqual(reconstructed_task.status, original_task.status)
        self.assertEqual(reconstructed_task.parent_id, original_task.parent_id)
        self.assertEqual(reconstructed_task.is_primitive, original_task.is_primitive)
        self.assertEqual(reconstructed_task.dependencies, original_task.dependencies)
        self.assertEqual(reconstructed_task.results, original_task.results)
        self.assertEqual(reconstructed_task.subtasks, original_task.subtasks)
        self.assertEqual(reconstructed_task.estimated_time, original_task.estimated_time)
        self.assertEqual(reconstructed_task.priority, original_task.priority)


if __name__ == '__main__':
    unittest.main()