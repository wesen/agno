"""
State tracking for the HTN Planning Agent.
"""

from typing import Dict
from dataclasses import dataclass, field


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