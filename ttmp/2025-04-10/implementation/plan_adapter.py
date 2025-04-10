"""
Plan adaptation for HTN Planning Agent.
"""

import json
import sys
import os
import logging
from typing import Dict, List, Any, Set

# Configure logging
logger = logging.getLogger('htn_agent.plan_adapter')

# Import directly for test compatibility
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from task_primitives import Task, TaskStatus, TaskManager
from planning_state import PlanningState


class PlanAdapter:
    """Adapts the plan based on execution results and new information."""
    
    def __init__(self, agent: Any, task_manager: TaskManager):
        """Initialize with an agent and task manager."""
        self.agent = agent
        self.task_manager = task_manager
    
    async def evaluate_plan(self, state: PlanningState) -> Dict:
        """
        Evaluate the current plan and suggest adaptations.
        Returns a dictionary of suggestions.
        """
        # Import the JSON extraction utility if not already available
        try:
            from real_agno import extract_json_from_response
            logger.info("Using extract_json_from_response from real_agno")
        except ImportError:
            logger.warning("Could not import extract_json_from_response, using fallback implementation")
            
            # Define a simple fallback version for testing
            def extract_json_from_response(response_content: str) -> Dict:
                """Simple JSON extraction for testing."""
                json_start = response_content.find('```json')
                json_end = response_content.rfind('```')
                
                if json_start != -1 and json_end != -1:
                    json_content = response_content[json_start + 7:json_end].strip()
                    return json.loads(json_content)
                else:
                    return json.loads(response_content)
        
        # Get current plan summary
        tasks = self.task_manager.tasks
        completed_tasks = [t for t in tasks.values() if t.status == TaskStatus.COMPLETED]
        pending_tasks = [t for t in tasks.values() if t.status != TaskStatus.COMPLETED]
        
        logger.info(f"Evaluating plan with {len(completed_tasks)} completed and {len(pending_tasks)} pending tasks")
        
        # Prepare context for evaluation
        plan_summary = f"""
        Total Tasks: {len(tasks)}
        Completed: {len(completed_tasks)}
        Pending: {len(pending_tasks)}
        
        State Summary:
        {state.get_state_summary()}
        
        Completed Tasks:
        {', '.join(t.name for t in completed_tasks)}
        
        Pending Tasks:
        {', '.join(t.name for t in pending_tasks)}
        """
        
        # Ask LLM for adaptation suggestions
        prompt = f"""
        # Plan Adaptation Request
        
        Analyze the current research plan and suggest adaptations based on what we've learned so far.
        
        ## Current Plan Status
        {plan_summary}
        
        ## Adaptation Requirements
        
        1. Identify gaps in the current research
        2. Suggest new tasks that should be added
        3. Identify tasks that may no longer be necessary
        4. Suggest priority changes for remaining tasks
        
        ## Output Format
        
        Your response MUST be valid JSON with no extra text or explanation outside the JSON structure.
        
        Provide your response in the following JSON format:
        
        ```json
        {{
          "gaps_identified": ["gap1", "gap2"],
          "new_tasks": [
            {{
              "name": "New task name",
              "description": "Detailed description",
              "is_primitive": true,
              "after_task": "id of task this should follow",
              "priority": 4
            }}
          ],
          "tasks_to_remove": ["id1", "id2"],
          "priority_changes": [
            {{
              "task_id": "id3",
              "new_priority": 5
            }}
          ]
        }}
        ```
        """
        
        # Track retries
        max_retries = 3
        retries = 0
        
        while retries <= max_retries:
            try:
                # Get adaptation suggestions from LLM
                logger.info(f"Sending plan adaptation request (attempt {retries + 1}/{max_retries + 1})")
                response = await self.agent.arun(prompt)
                content = response.content
                
                # Extract JSON from response using the extraction utility
                try:
                    adaptations = extract_json_from_response(content)
                    logger.info(f"Successfully parsed plan adaptation response")
                    
                    # Validate the response structure
                    expected_keys = ["gaps_identified", "new_tasks", "tasks_to_remove", "priority_changes"]
                    missing_keys = [key for key in expected_keys if key not in adaptations]
                    
                    if missing_keys:
                        logger.warning(f"Adaptation response missing expected keys: {missing_keys}")
                        for key in missing_keys:
                            adaptations[key] = [] if key != "gaps_identified" else ["No gaps identified"]
                    
                    return adaptations
                    
                except json.JSONDecodeError as json_error:
                    logger.error(f"JSON parsing error: {str(json_error)}")
                    logger.debug(f"Problematic content: {content[:500]}...")
                    raise
                
            except Exception as e:
                retries += 1
                logger.warning(f"Error evaluating plan (attempt {retries}/{max_retries + 1}): {str(e)}")
                
                if retries <= max_retries:
                    logger.info(f"Retrying plan evaluation...")
                    # Could add exponential backoff here if needed
                else:
                    # All retries failed
                    logger.error(f"Plan evaluation failed after {max_retries + 1} attempts: {str(e)}")
                    
                    # Return empty defaults
                    return {
                        "gaps_identified": ["Plan adaptation failed, continuing with existing plan"],
                        "new_tasks": [],
                        "tasks_to_remove": [],
                        "priority_changes": []
                    }
    
    async def adapt_plan(self, state: PlanningState) -> None:
        """
        Adapt the current plan based on evaluation.
        """
        # Evaluate the plan
        adaptations = await self.evaluate_plan(state)
        
        # Process priority changes
        for change in adaptations.get("priority_changes", []):
            task_id = change["task_id"]
            new_priority = change["new_priority"]
            
            if task_id in self.task_manager.tasks:
                self.task_manager.update_task(task_id, priority=new_priority)
        
        # Process task removals (mark as completed with null result)
        for task_id in adaptations.get("tasks_to_remove", []):
            if task_id in self.task_manager.tasks:
                self.task_manager.mark_task_complete(task_id, "Task skipped during plan adaptation")
        
        # Process new tasks
        for task_data in adaptations.get("new_tasks", []):
            # Create new task
            after_task_id = task_data.get("after_task")
            parent_id = None
            
            # Find appropriate parent
            if after_task_id and after_task_id in self.task_manager.tasks:
                after_task = self.task_manager.get_task(after_task_id)
                parent_id = after_task.parent_id
            
            # Create and add the task
            task_id = self.task_manager.create_task(
                name=task_data["name"],
                description=task_data["description"],
                is_primitive=task_data.get("is_primitive", True),
                parent_id=parent_id,
                dependencies=set([after_task_id]) if after_task_id else set()
            )
            
            # Set priority after creation
            if "priority" in task_data:
                task = self.task_manager.get_task(task_id)
                task.priority = task_data["priority"]
            
            # If parent exists, add to parent's subtasks
            if parent_id and parent_id in self.task_manager.tasks:
                parent = self.task_manager.get_task(parent_id)
                parent.subtasks.append(task_id)