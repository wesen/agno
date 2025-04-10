"""
Unit tests for PlanningState class.
"""

import unittest
from planning_state import PlanningState


class TestPlanningState(unittest.TestCase):
    """Test cases for the PlanningState class."""

    def test_initialization(self):
        """Test initializing a planning state."""
        state = PlanningState(topic="Test Topic")
        
        self.assertEqual(state.topic, "Test Topic")
        self.assertEqual(state.facts, {})
        self.assertEqual(state.sources, {})
        self.assertEqual(state.sections, {})
        self.assertEqual(state.task_status, {})
        self.assertEqual(state.task_results, {})

    def test_update_facts(self):
        """Test updating facts in the state."""
        state = PlanningState(topic="Fact Test")
        
        # Add a new fact
        state.update_facts("fact1", "Fact 1 value")
        self.assertEqual(state.facts["fact1"], "Fact 1 value")
        
        # Update an existing fact
        state.update_facts("fact1", "Updated fact 1")
        self.assertEqual(state.facts["fact1"], "Updated fact 1")
        
        # Add another fact
        state.update_facts("fact2", "Fact 2 value")
        self.assertEqual(len(state.facts), 2)
        self.assertEqual(state.facts["fact2"], "Fact 2 value")

    def test_add_source(self):
        """Test adding sources to the state."""
        state = PlanningState(topic="Source Test")
        
        state.add_source("source1", "Source 1 content")
        self.assertEqual(state.sources["source1"], "Source 1 content")
        
        state.add_source("source2", "Source 2 content")
        self.assertEqual(len(state.sources), 2)
        self.assertEqual(state.sources["source2"], "Source 2 content")

    def test_add_section(self):
        """Test adding report sections to the state."""
        state = PlanningState(topic="Section Test")
        
        state.add_section("Introduction", "Intro content")
        self.assertEqual(state.sections["Introduction"], "Intro content")
        
        state.add_section("Conclusion", "Conclusion content")
        self.assertEqual(len(state.sections), 2)
        self.assertEqual(state.sections["Conclusion"], "Conclusion content")
        
        # Test updating a section
        state.add_section("Introduction", "Updated intro")
        self.assertEqual(state.sections["Introduction"], "Updated intro")

    def test_get_facts_summary(self):
        """Test getting a summary of facts."""
        state = PlanningState(topic="Facts Summary")
        
        # Test with no facts
        summary = state.get_facts_summary()
        self.assertEqual(summary, "No facts have been gathered yet.")
        
        # Test with facts
        state.update_facts("fact1", "Value 1")
        state.update_facts("fact2", "Value 2")
        
        summary = state.get_facts_summary()
        self.assertIn("- fact1: Value 1", summary)
        self.assertIn("- fact2: Value 2", summary)

    def test_get_sources_summary(self):
        """Test getting a summary of sources."""
        state = PlanningState(topic="Sources Summary")
        
        # Test with no sources
        summary = state.get_sources_summary()
        self.assertEqual(summary, "No sources have been found yet.")
        
        # Test with sources
        state.add_source("source1", "Short source content")
        state.add_source("source2", "A" * 200)  # Long source content
        
        summary = state.get_sources_summary()
        self.assertIn("- Source source1: Short source content", summary)
        self.assertIn("- Source source2: " + "A" * 100 + "...", summary)

    def test_get_state_summary(self):
        """Test getting a complete state summary."""
        state = PlanningState(topic="Summary Test")
        
        # Add sample data
        state.update_facts("fact1", "Value 1")
        state.add_source("source1", "Source content")
        state.add_section("Section", "Section content")
        
        summary = state.get_state_summary()
        
        # Check content of summary
        self.assertIn("Topic: Summary Test", summary)
        self.assertIn("Facts Gathered: 1", summary)
        self.assertIn("Sources Found: 1", summary)
        self.assertIn("Report Sections: 1", summary)
        self.assertIn("- fact1: Value 1", summary)
        self.assertIn("source1", summary)
        self.assertIn("Section", summary)

    def test_to_dict(self):
        """Test converting state to dictionary."""
        state = PlanningState(topic="Dict Test")
        
        # Add sample data
        state.update_facts("fact1", "Value 1")
        state.add_source("source1", "Source content")
        state.add_section("Section", "Section content")
        state.task_status["task1"] = "completed"
        state.task_results["task1"] = "Task 1 results"
        
        state_dict = state.to_dict()
        
        # Check dictionary content
        self.assertEqual(state_dict["topic"], "Dict Test")
        self.assertEqual(state_dict["facts"], {"fact1": "Value 1"})
        self.assertEqual(state_dict["sources"], {"source1": "Source content"})
        self.assertEqual(state_dict["sections"], {"Section": "Section content"})
        self.assertEqual(state_dict["task_status"], {"task1": "completed"})
        self.assertEqual(state_dict["task_results"], {"task1": "Task 1 results"})

    def test_from_dict(self):
        """Test creating state from dictionary."""
        state_dict = {
            "topic": "From Dict",
            "facts": {"fact1": "Value 1", "fact2": "Value 2"},
            "sources": {"source1": "Source 1 content"},
            "sections": {"Intro": "Intro content", "Conclusion": "End content"},
            "task_status": {"task1": "completed", "task2": "pending"},
            "task_results": {"task1": "Task 1 results"}
        }
        
        state = PlanningState.from_dict(state_dict)
        
        # Check state was created correctly
        self.assertEqual(state.topic, "From Dict")
        self.assertEqual(len(state.facts), 2)
        self.assertEqual(state.facts["fact2"], "Value 2")
        self.assertEqual(len(state.sources), 1)
        self.assertEqual(state.sources["source1"], "Source 1 content")
        self.assertEqual(len(state.sections), 2)
        self.assertEqual(state.sections["Conclusion"], "End content")
        self.assertEqual(len(state.task_status), 2)
        self.assertEqual(state.task_status["task2"], "pending")
        self.assertEqual(len(state.task_results), 1)
        self.assertEqual(state.task_results["task1"], "Task 1 results")

    def test_serialization_roundtrip(self):
        """Test serialization and deserialization roundtrip."""
        original_state = PlanningState(topic="Roundtrip Test")
        original_state.update_facts("fact1", "Value 1")
        original_state.add_source("source1", "Source content")
        original_state.add_section("Section", "Section content")
        original_state.task_status["task1"] = "completed"
        original_state.task_results["task1"] = "Task 1 results"
        
        # Convert to dict and back to PlanningState
        state_dict = original_state.to_dict()
        reconstructed_state = PlanningState.from_dict(state_dict)
        
        # Verify all properties match
        self.assertEqual(reconstructed_state.topic, original_state.topic)
        self.assertEqual(reconstructed_state.facts, original_state.facts)
        self.assertEqual(reconstructed_state.sources, original_state.sources)
        self.assertEqual(reconstructed_state.sections, original_state.sections)
        self.assertEqual(reconstructed_state.task_status, original_state.task_status)
        self.assertEqual(reconstructed_state.task_results, original_state.task_results)


if __name__ == '__main__':
    unittest.main()