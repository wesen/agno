"""
Task decomposition using LLM for HTN Planning Agent.
"""

import json
import uuid
import logging
import re
from typing import List, Optional, Dict, Any
import asyncio

# Configure logging
logger = logging.getLogger('htn_agent.task_decomposer')

# Import real Agno wrapper and JSON extraction utility
try:
    from real_agno import extract_json_from_response
except ImportError:
    logger.warning("Could not import real_agno. Mock implementation will be used.")
    
    # Define a simple version for testing if real_agno is not available
    def extract_json_from_response(response_content: str) -> Dict:
        """Simple JSON extraction for testing."""
        json_start = response_content.find('```json')
        json_end = response_content.rfind('```')
        
        if json_start != -1 and json_end != -1:
            json_content = response_content[json_start + 7:json_end].strip()
            return json.loads(json_content)
        else:
            return json.loads(response_content)

# For testing without requiring API keys
class MockAgent:
    """A mock agent for testing purposes."""
    
    async def arun(self, prompt: str) -> Any:
        """Mock implementation of agent.arun."""
        logger.debug(f"MockAgent received prompt: {prompt[:100]}...")
        
        # Return a simple mock response based on the task name
        if "research" in prompt.lower():
            return MockResponse(
                content='''```json
                {
                  "subtasks": [
                    {
                      "name": "Search for recent papers",
                      "description": "Find academic papers from the last 2 years",
                      "is_primitive": true,
                      "dependencies": [],
                      "estimated_time": 15,
                      "priority": 4
                    },
                    {
                      "name": "Identify key researchers",
                      "description": "Find the most cited researchers in this field",
                      "is_primitive": true,
                      "dependencies": [],
                      "estimated_time": 10,
                      "priority": 3
                    },
                    {
                      "name": "Analyze trends",
                      "description": "Identify common themes and trends",
                      "is_primitive": false,
                      "dependencies": ["$PARENT_DEP$"],
                      "estimated_time": 30,
                      "priority": 5
                    }
                  ]
                }
                ```'''.replace("$PARENT_DEP$", "Search for recent papers")
            )
        elif "write" in prompt.lower():
            return MockResponse(
                content='''```json
                {
                  "subtasks": [
                    {
                      "name": "Create outline",
                      "description": "Develop a structured outline for the document",
                      "is_primitive": true,
                      "dependencies": [],
                      "estimated_time": 10,
                      "priority": 5
                    },
                    {
                      "name": "Write introduction",
                      "description": "Write an engaging introduction",
                      "is_primitive": true,
                      "dependencies": ["Create outline"],
                      "estimated_time": 20,
                      "priority": 4
                    },
                    {
                      "name": "Write conclusion",
                      "description": "Summarize findings and provide conclusion",
                      "is_primitive": true,
                      "dependencies": ["Write introduction"],
                      "estimated_time": 15,
                      "priority": 3
                    }
                  ]
                }
                ```'''
            )
        else:
            return MockResponse(
                content='''```json
                {
                  "subtasks": [
                    {
                      "name": "Generic subtask 1",
                      "description": "First generic subtask",
                      "is_primitive": true,
                      "dependencies": [],
                      "estimated_time": 10,
                      "priority": 3
                    },
                    {
                      "name": "Generic subtask 2",
                      "description": "Second generic subtask",
                      "is_primitive": true,
                      "dependencies": ["Generic subtask 1"],
                      "estimated_time": 10,
                      "priority": 2
                    }
                  ]
                }
                ```'''
            )


class MockResponse:
    """A mock response from an agent."""
    
    def __init__(self, content: str):
        self.content = content


class TaskDecomposer:
    """Uses LLM to decompose non-primitive tasks into subtasks."""
    
    def __init__(self, agent: Any):
        """Initialize with an Agno agent."""
        self.agent = agent
    
    async def decompose_task(self, task: 'Task', state: 'PlanningState') -> List['Task']:
        """
        Decompose a task into subtasks using LLM.
        Returns a list of created subtasks.
        """
        # Import directly for test compatibility
        # In regular package use, these would already be imported from the package
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from task_primitives import Task, TaskStatus
        
        logger.info(f"Decomposing task: {task.id} - {task.name}")
        
        # Mark the task as being decomposed
        task.status = TaskStatus.DECOMPOSING
        
        # Prepare context for the LLM
        state_summary = state.get_state_summary()
        
        # Prompt the LLM to decompose the task
        prompt = f"""
        # Task Decomposition Request
        
        You need to break down the following task into smaller, more manageable subtasks.
        
        ## Current Task
        Name: {task.name}
        Description: {task.description}
        
        ## Current State
        {state_summary}
        
        ## Decomposition Requirements
        
        1. Break this task down into 3-7 subtasks that together will accomplish the parent task
        2. For each subtask, provide:
           - A clear, concise name
           - A detailed description
           - Whether it's a primitive task (can be directly executed) or needs further decomposition
           - Dependencies (IDs of other subtasks it depends on)
           - Estimated time to complete (in minutes)
           - Priority (1-5, with 5 being highest)
        
        ## Output Format
        
        Your response MUST be valid JSON with no extra text or explanation outside the JSON structure.
        
        Provide your response in the following JSON format:
        
        ```json
        {{
          "subtasks": [
            {{
              "name": "Subtask name",
              "description": "Detailed description",
              "is_primitive": true or false,
              "dependencies": ["id1", "id2"],
              "estimated_time": 15,
              "priority": 3
            }}
          ]
        }}
        ```
        
        Note: For the first subtask, the dependencies list should be empty since there are no other subtasks yet.
        """
        
        try:
            # Get decomposition from LLM
            logger.info(f"Sending decomposition request for task {task.id}")
            response = await self.agent.arun(prompt)
            content = response.content
            
            # Extract JSON from response using enhanced parser
            try:
                decomposition = extract_json_from_response(content)
                logger.info(f"Successfully parsed JSON response for task {task.id}")
                logger.debug(f"Extracted JSON: {decomposition}")
                
                # Validate the expected structure
                if "subtasks" not in decomposition:
                    logger.error(f"Missing 'subtasks' in decomposition response: {decomposition}")
                    raise ValueError("Missing 'subtasks' in decomposition response")
                
                if not isinstance(decomposition["subtasks"], list):
                    logger.error(f"'subtasks' is not a list in response: {decomposition}")
                    raise ValueError("'subtasks' is not a list in decomposition response")
                
                if len(decomposition["subtasks"]) == 0:
                    logger.warning(f"Empty subtasks list for task {task.id}")
                    raise ValueError("Empty subtasks list in decomposition response")
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"JSON parsing error for task {task.id}: {str(e)}")
                logger.debug(f"Problematic content: {content[:500]}...")
                raise
            
            # Create subtasks from decomposition
            subtasks = []
            created_subtasks = {}  # Map of name to id for dependency resolution
            
            logger.info(f"Creating {len(decomposition['subtasks'])} subtasks for task {task.id}")
            
            for subtask_data in decomposition["subtasks"]:
                # Validate required fields
                required_fields = ["name", "description", "is_primitive"]
                for field in required_fields:
                    if field not in subtask_data:
                        logger.warning(f"Missing required field '{field}' in subtask data: {subtask_data}")
                        subtask_data[field] = "Missing" if field in ["name", "description"] else True
                
                # Generate ID for new subtask
                subtask_id = str(uuid.uuid4())
                created_subtasks[subtask_data["name"]] = subtask_id
                
                logger.debug(f"Creating subtask: {subtask_data['name']}")
                
                # Create subtask (with empty dependencies for now)
                subtask = Task(
                    id=subtask_id,
                    name=subtask_data["name"],
                    description=subtask_data["description"],
                    is_primitive=subtask_data["is_primitive"],
                    parent_id=task.id,
                    dependencies=set(),  # We'll fill these in after creating all subtasks
                    estimated_time=subtask_data.get("estimated_time", 10),
                    priority=subtask_data.get("priority", 1)
                )
                
                subtasks.append(subtask)
            
            # Resolve dependencies now that all subtasks are created
            logger.info(f"Resolving dependencies for {len(subtasks)} subtasks")
            
            for i, subtask_data in enumerate(decomposition["subtasks"]):
                dependency_names = subtask_data.get("dependencies", [])
                dependency_ids = set()
                
                for dep_name in dependency_names:
                    if dep_name in created_subtasks:
                        dependency_ids.add(created_subtasks[dep_name])
                    else:
                        logger.warning(f"Referenced dependency '{dep_name}' not found in created subtasks")
                
                subtasks[i].dependencies = dependency_ids
                logger.debug(f"Subtask {subtasks[i].name} has dependencies: {dependency_ids}")
            
            # Update parent task with subtask references
            task.subtasks = [subtask.id for subtask in subtasks]
            logger.info(f"Task {task.id} decomposed into {len(subtasks)} subtasks")
            
            return subtasks
            
        except Exception as e:
            logger.error(f"Error decomposing task {task.id}: {str(e)}")
            
            # If decomposition fails, create a generic subtask as fallback
            subtask_id = str(uuid.uuid4())
            logger.info(f"Creating fallback subtask {subtask_id} for failed decomposition")
            
            subtask = Task(
                id=subtask_id,
                name=f"Execute {task.name}",
                description=f"Execute the task: {task.description}",
                is_primitive=True,
                parent_id=task.id
            )
            task.subtasks = [subtask.id]
            return [subtask]