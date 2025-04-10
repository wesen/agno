"""
Demo script for the HTN Planning Agent.
"""

import asyncio
import sys
import json
from task_executor import MockAgent
from htn_planning_agent import HTNPlanningAgent

# Create a MockAdapterAgent class to showcase plan adaptation
class MockAdapterAgent(MockAgent):
    """Mock agent that responds to plan adaptation prompts."""
    
    async def arun(self, prompt: str) -> any:
        """Custom arun method to handle plan adaptation."""
        if "Plan Adaptation Request" in prompt:
            # This is a plan adaptation request
            return type('obj', (object,), {
                'content': '''```json
                {
                  "gaps_identified": ["Missing analysis of quantum error correction", "Insufficient focus on industry applications"],
                  "new_tasks": [
                    {
                      "name": "Research quantum error correction",
                      "description": "Find recent breakthroughs in quantum error correction techniques",
                      "is_primitive": true,
                      "priority": 4
                    },
                    {
                      "name": "Analyze industry applications",
                      "description": "Investigate how quantum computing is being applied in different industries",
                      "is_primitive": true,
                      "priority": 3
                    }
                  ],
                  "tasks_to_remove": [],
                  "priority_changes": []
                }
                ```'''
            })
        else:
            # For other prompts, use the standard MockAgent response
            return await super().arun(prompt)


async def run_demo():
    """Run a demonstration of the HTN Planning Agent."""
    # Create a mock agent with adaptation capability
    mock_agent = MockAdapterAgent()
    
    # Create the HTN planning agent
    planner = HTNPlanningAgent(mock_agent)
    
    # For demonstration purposes, set adaptation frequency lower
    planner.adaptation_frequency = 2
    
    # Define research topic and goal from command line args or use defaults
    topic = sys.argv[1] if len(sys.argv) > 1 else "Quantum Computing"
    goal = sys.argv[2] if len(sys.argv) > 2 else "explains recent developments and future prospects"
    max_steps = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    
    print(f"\n===== HTN Planning Agent Demo =====\n")
    print(f"Topic: {topic}")
    print(f"Goal: {goal}")
    print(f"Max Steps: {max_steps}")
    print(f"Plan Adaptation Frequency: Every {planner.adaptation_frequency} tasks")
    print(f"\n===== Planning & Execution =====\n")
    
    # Execute the research and report generation process
    report = await planner.research_and_write_report(topic, goal, max_steps)
    
    # Display the results
    print(f"\n===== Final Report =====\n")
    print(report)
    
    # Display the plan structure
    print(f"\n===== Plan Structure =====\n")
    print(planner.visualize_plan())
    
    # Display the plan status
    print(f"\n===== Plan Status =====\n")
    status = planner.get_plan_status()
    for key, value in status.items():
        print(f"{key}: {value}")
    
    # Display some facts gathered during research
    print(f"\n===== Facts Gathered =====\n")
    if planner.state and planner.state.facts:
        for key, value in planner.state.facts.items():
            print(f"- {key}: {value[:100]}..." if len(value) > 100 else f"- {key}: {value}")
    else:
        print("No facts gathered")
    
    print("\n===== Demo Complete =====\n")

if __name__ == "__main__":
    asyncio.run(run_demo())