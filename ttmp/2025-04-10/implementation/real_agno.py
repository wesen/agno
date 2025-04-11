"""
Integration with real Agno agents for HTN Planning Agent.
"""

import json
import re
import os
import time
import uuid
import logging
import datetime
from typing import Any, Dict, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('htn_agent.log')
    ]
)
logger = logging.getLogger('htn_agent')

# Set up trace directory
TRACES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'traces')
os.makedirs(TRACES_DIR, exist_ok=True)

def save_trace(trace_type: str, content: Any, metadata: Dict = None) -> str:
    """
    Save content to a trace file.
    
    Args:
        trace_type: Type of trace (prompt, response, etc.)
        content: Content to save
        metadata: Optional metadata to include
        
    Returns:
        Path to the saved trace file
    """
    # Create a unique ID for the trace
    trace_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    
    # Create trace data
    trace_data = {
        "id": trace_id,
        "type": trace_type,
        "timestamp": timestamp,
        "content": content
    }
    
    if metadata:
        trace_data["metadata"] = metadata
    
    # Create filename and path
    filename = f"{timestamp}_{trace_type}_{trace_id[:8]}.json"
    filepath = os.path.join(TRACES_DIR, filename)
    
    # Save to file
    with open(filepath, 'w') as f:
        json.dump(trace_data, f, indent=2)
    
    logger.debug(f"Saved {trace_type} trace to {filepath}")
    return filepath

class AgnoAgentWrapper:
    """Wrapper for Agno agents to standardize interaction and add error handling."""
    
    def __init__(self, agent: Any, max_retries: int = 3):
        """
        Initialize with an Agno agent.
        
        Args:
            agent: An Agno agent instance
            max_retries: Maximum number of retry attempts on failure
        """
        self.agent = agent
        self.max_retries = max_retries
        logger.info(f"Initialized AgnoAgentWrapper with {type(agent).__name__}")
    
    async def arun(self, prompt: str) -> Any:
        """
        Run the agent with proper error handling and retries.
        
        Args:
            prompt: The prompt to send to the agent
            
        Returns:
            An object with a content property containing the response
            
        Raises:
            Exception: If all retry attempts fail
        """
        retries = 0
        last_error = None
        interaction_id = str(uuid.uuid4())
        
        # Save prompt trace
        prompt_metadata = {
            "interaction_id": interaction_id,
            "attempt": retries,
            "agent_type": type(self.agent).__name__,
            "model_type": type(getattr(self.agent, "model", None)).__name__
        }
        save_trace("prompt", prompt, prompt_metadata)
        
        # Truncate prompt in log message for brevity
        log_prompt = prompt[:100] + "..." if len(prompt) > 100 else prompt
        logger.info(f"Sending prompt to agent: {log_prompt}")
        
        start_time = time.time()
        while retries <= self.max_retries:
            try:
                response = await self.agent.arun(prompt)
                end_time = time.time()
                
                # Save response trace
                response_metadata = {
                    "interaction_id": interaction_id,
                    "attempt": retries,
                    "agent_type": type(self.agent).__name__,
                    "model_type": type(getattr(self.agent, "model", None)).__name__,
                    "duration_seconds": end_time - start_time
                }
                
                # Extract response content for tracing
                response_content = getattr(response, "content", str(response))
                save_trace("response", response_content, response_metadata)
                
                logger.info("Received response from agent")
                logger.debug(f"Response content: {response_content[:200]}...")
                
                return response
            except Exception as e:
                end_time = time.time()
                retries += 1
                last_error = e
                
                # Save error trace
                error_metadata = {
                    "interaction_id": interaction_id,
                    "attempt": retries,
                    "agent_type": type(self.agent).__name__,
                    "model_type": type(getattr(self.agent, "model", None)).__name__,
                    "error_type": type(e).__name__,
                    "duration_seconds": end_time - start_time
                }
                save_trace("error", str(e), error_metadata)
                
                logger.warning(f"Error calling agent (attempt {retries}/{self.max_retries}): {str(e)}")
                if retries <= self.max_retries:
                    logger.info(f"Retrying agent call...")
                    start_time = time.time()  # Reset timer for next attempt
        
        # If we get here, all retries failed
        error_msg = f"Failed to get response from agent after {self.max_retries} attempts: {str(last_error)}"
        logger.error(error_msg)
        
        # Save final failure trace
        failure_metadata = {
            "interaction_id": interaction_id,
            "attempts": retries,
            "agent_type": type(self.agent).__name__,
            "model_type": type(getattr(self.agent, "model", None)).__name__,
            "final_error_type": type(last_error).__name__
        }
        save_trace("final_failure", error_msg, failure_metadata)
        
        raise Exception(error_msg)

def extract_json_from_response(response_content: str) -> Dict:
    """
    Extract and parse JSON from a response that may contain markdown code blocks.
    
    Args:
        response_content: The raw response content from the agent
        
    Returns:
        Parsed JSON data
        
    Raises:
        json.JSONDecodeError: If JSON parsing fails
    """
    logger.info("Extracting JSON from response")
    parsing_id = str(uuid.uuid4())
    
    # Save raw content trace
    save_trace("json_parsing_input", response_content, {"parsing_id": parsing_id})
    
    # Try different patterns for extracting JSON
    try:
        # First try: Extract from markdown code block
        json_pattern = r'```(?:json)?\s*(.+?)```'
        matches = re.findall(json_pattern, response_content, re.DOTALL)
        
        if matches:
            logger.debug(f"Found JSON in markdown code block")
            for i, json_str in enumerate(matches):
                try:
                    parsed_json = json.loads(json_str.strip())
                    
                    # Save successful parsing trace
                    parse_metadata = {
                        "parsing_id": parsing_id,
                        "method": "markdown_code_block",
                        "match_index": i,
                        "successful": True
                    }
                    save_trace("json_parsing_result", parsed_json, parse_metadata)
                    
                    return parsed_json
                except json.JSONDecodeError as e:
                    # Save failed parsing attempt
                    parse_metadata = {
                        "parsing_id": parsing_id,
                        "method": "markdown_code_block",
                        "match_index": i,
                        "successful": False,
                        "error": str(e),
                        "sample": json_str[:200] + ("..." if len(json_str) > 200 else "")
                    }
                    save_trace("json_parsing_attempt", None, parse_metadata)
                    
                    logger.debug(f"Failed to parse JSON from code block, trying next match")
                    continue
        
        # Second try: Look for JSON object pattern
        json_object_pattern = r'(\{.+\})'
        matches = re.findall(json_object_pattern, response_content, re.DOTALL)
        
        if matches:
            logger.debug(f"Found JSON object pattern")
            for i, json_str in enumerate(matches):
                try:
                    parsed_json = json.loads(json_str.strip())
                    
                    # Save successful parsing trace
                    parse_metadata = {
                        "parsing_id": parsing_id,
                        "method": "json_object_pattern",
                        "match_index": i,
                        "successful": True
                    }
                    save_trace("json_parsing_result", parsed_json, parse_metadata)
                    
                    return parsed_json
                except json.JSONDecodeError as e:
                    # Save failed parsing attempt
                    parse_metadata = {
                        "parsing_id": parsing_id,
                        "method": "json_object_pattern",
                        "match_index": i,
                        "successful": False,
                        "error": str(e),
                        "sample": json_str[:200] + ("..." if len(json_str) > 200 else "")
                    }
                    save_trace("json_parsing_attempt", None, parse_metadata)
                    
                    logger.debug(f"Failed to parse JSON from object pattern, trying next match")
                    continue
        
        # Third try: Parse the entire response
        logger.debug(f"Attempting to parse entire response as JSON")
        try:
            parsed_json = json.loads(response_content.strip())
            
            # Save successful parsing trace
            parse_metadata = {
                "parsing_id": parsing_id,
                "method": "entire_response",
                "successful": True
            }
            save_trace("json_parsing_result", parsed_json, parse_metadata)
            
            return parsed_json
        except json.JSONDecodeError as e:
            # Save failed parsing attempt
            parse_metadata = {
                "parsing_id": parsing_id,
                "method": "entire_response",
                "successful": False,
                "error": str(e),
                "sample": response_content[:200] + ("..." if len(response_content) > 200 else "")
            }
            save_trace("json_parsing_attempt", None, parse_metadata)
            raise
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {str(e)}")
        logger.debug(f"Failed JSON content: {response_content[:500]}...")
        
        # Save final parsing error trace
        error_metadata = {
            "parsing_id": parsing_id,
            "successful": False,
            "error": str(e),
            "error_type": "JSONDecodeError"
        }
        save_trace("json_parsing_error", response_content[:500], error_metadata)
        
        raise

def create_agno_agent(model_name: str, api_key: str, instructions: str = None, tools: list = None):
    """
    Create and configure an Agno agent.
    
    Args:
        model_name: The name of the model to use (e.g., 'claude-3-5-sonnet')
        api_key: The API key for the model provider
        instructions: Optional instructions for the agent
        tools: Optional list of tools for the agent
        
    Returns:
        A configured AgnoAgentWrapper
    """
    try:
        # Import Agno components
        from agno.agent import Agent
        
        # Determine which model provider to use based on model_name
        if 'claude' in model_name.lower():
            from agno.models.anthropic import Claude
            model = Claude(api_key=api_key, id=model_name)
            logger.info(f"Created Claude model: {model_name}")
        elif 'gpt' in model_name.lower() or 'openai' in model_name.lower():
            from agno.models.openai import GPT
            model = GPT(api_key=api_key, id=model_name)
            logger.info(f"Created OpenAI GPT model: {model_name}")
        else:
            logger.warning(f"Unknown model type: {model_name}, defaulting to Claude")
            from agno.models.anthropic import Claude
            model = Claude(api_key=api_key, id=model_name)
        
        # Create agent with specified model and optional components
        agent_config = {
            "model": model
        }
        
        if instructions:
            agent_config["instructions"] = instructions
        
        if tools:
            agent_config["tools"] = tools
        
        agent = Agent(**agent_config)
        logger.info(f"Created Agno agent with {model_name}")
        
        # Return wrapped agent
        return AgnoAgentWrapper(agent)
        
    except ImportError as e:
        logger.error(f"Failed to import Agno: {str(e)}")
        logger.error("Please install Agno with: pip install agno")
        raise
    except Exception as e:
        logger.error(f"Error creating Agno agent: {str(e)}")
        raise