"""
Integration with real Agno agents for HTN Planning Agent.
"""

import json
import re
import logging
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
        
        # Truncate prompt in log message for brevity
        log_prompt = prompt[:100] + "..." if len(prompt) > 100 else prompt
        logger.info(f"Sending prompt to agent: {log_prompt}")
        
        while retries <= self.max_retries:
            try:
                response = await self.agent.arun(prompt)
                logger.info("Received response from agent")
                logger.debug(f"Response content: {response.content[:200]}...")
                return response
            except Exception as e:
                retries += 1
                last_error = e
                logger.warning(f"Error calling agent (attempt {retries}/{self.max_retries}): {str(e)}")
                if retries <= self.max_retries:
                    logger.info(f"Retrying agent call...")
                    # Could add exponential backoff here if needed
        
        # If we get here, all retries failed
        error_msg = f"Failed to get response from agent after {self.max_retries} attempts: {str(last_error)}"
        logger.error(error_msg)
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
    
    # Try different patterns for extracting JSON
    try:
        # First try: Extract from markdown code block
        json_pattern = r'```(?:json)?\s*(.+?)```'
        matches = re.findall(json_pattern, response_content, re.DOTALL)
        
        if matches:
            logger.debug(f"Found JSON in markdown code block")
            for json_str in matches:
                try:
                    return json.loads(json_str.strip())
                except json.JSONDecodeError:
                    logger.debug(f"Failed to parse JSON from code block, trying next match")
                    continue
        
        # Second try: Look for JSON object pattern
        json_object_pattern = r'(\{.+\})'
        matches = re.findall(json_object_pattern, response_content, re.DOTALL)
        
        if matches:
            logger.debug(f"Found JSON object pattern")
            for json_str in matches:
                try:
                    return json.loads(json_str.strip())
                except json.JSONDecodeError:
                    logger.debug(f"Failed to parse JSON from object pattern, trying next match")
                    continue
        
        # Third try: Parse the entire response
        logger.debug(f"Attempting to parse entire response as JSON")
        return json.loads(response_content.strip())
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {str(e)}")
        logger.debug(f"Failed JSON content: {response_content[:500]}...")
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