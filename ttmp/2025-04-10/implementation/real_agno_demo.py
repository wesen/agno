"""
Demo script for the HTN Planning Agent with real Agno agent integration.
"""

import asyncio
import sys
import os
import json
import logging
import argparse
from typing import Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('htn_agent_demo.log')
    ]
)
logger = logging.getLogger('htn_agent_demo')

# Import HTN Planning Agent components
from htn_planning_agent import HTNPlanningAgent
from real_agno import create_agno_agent, AgnoAgentWrapper


async def run_demo(topic: str, goal: str, max_steps: int, model_name: str, api_key: str, adaptation_frequency: int = 2):
    """
    Run a demonstration of the HTN Planning Agent with a real Agno agent.
    
    Args:
        topic: The research topic
        goal: The goal or purpose of the research
        max_steps: Maximum number of steps to execute
        model_name: The name of the LLM model to use
        api_key: The API key for the model provider
        adaptation_frequency: How often to adapt the plan
    """
    logger.info(f"Starting HTN Planning Agent demo with {model_name}")
    
    try:
        # Create a real Agno agent
        logger.info(f"Creating Agno agent with model: {model_name}")
        agent = create_agno_agent(
            model_name=model_name,
            api_key=api_key,
            instructions="You are an AI research assistant that helps with research and writing tasks.",
            tools=[]  # Add any tools you want to include
        )
        
        # Create the HTN planning agent
        logger.info("Creating HTN Planning Agent")
        planner = HTNPlanningAgent(agent)
        
        # Set the adaptation frequency
        planner.adaptation_frequency = adaptation_frequency
        
        logger.info(f"\n===== HTN Planning Agent Demo =====\n")
        logger.info(f"Topic: {topic}")
        logger.info(f"Goal: {goal}")
        logger.info(f"Max Steps: {max_steps}")
        logger.info(f"Model: {model_name}")
        logger.info(f"Plan Adaptation Frequency: Every {planner.adaptation_frequency} tasks")
        logger.info(f"\n===== Planning & Execution =====\n")
        
        # Execute the research and report generation process
        logger.info("Starting research and report generation process")
        report = await planner.research_and_write_report(topic, goal, max_steps)
        
        # Display the results
        logger.info(f"\n===== Final Report =====\n")
        logger.info(report)
        
        # Display the plan structure
        logger.info(f"\n===== Plan Structure =====\n")
        plan_structure = planner.visualize_plan()
        logger.info(plan_structure)
        
        # Display the plan status
        logger.info(f"\n===== Plan Status =====\n")
        status = planner.get_plan_status()
        for key, value in status.items():
            logger.info(f"{key}: {value}")
        
        # Display some facts gathered during research
        logger.info(f"\n===== Facts Gathered =====\n")
        if planner.state and planner.state.facts:
            for key, value in planner.state.facts.items():
                log_value = f"{value[:100]}..." if len(value) > 100 else value
                logger.info(f"- {key}: {log_value}")
        else:
            logger.info("No facts gathered")
        
        logger.info("\n===== Demo Complete =====\n")
        
        # Return the report for potential further processing
        return report
        
    except Exception as e:
        logger.error(f"Error running demo: {str(e)}", exc_info=True)
        return f"Error running demo: {str(e)}"


def get_api_key(api_key_env_var: str) -> Optional[str]:
    """
    Get the API key from the environment variable.
    
    Args:
        api_key_env_var: The name of the environment variable
        
    Returns:
        The API key or None if not found
    """
    api_key = os.environ.get(api_key_env_var)
    if not api_key:
        logger.error(f"API key environment variable {api_key_env_var} not set")
        print(f"Error: API key environment variable {api_key_env_var} not set")
        print(f"Please set the environment variable {api_key_env_var} to your API key")
        print(f"For example: export {api_key_env_var}=your-api-key")
        return None
    return api_key


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Run HTN Planning Agent demo with real Agno agent")
    parser.add_argument("--topic", type=str, default="Quantum Computing", help="Research topic")
    parser.add_argument("--goal", type=str, default="explains recent developments and future prospects", help="Research goal")
    parser.add_argument("--steps", type=int, default=10, help="Maximum number of execution steps")
    parser.add_argument("--model", type=str, default="claude-3-sonnet-20240229", help="LLM model to use")
    parser.add_argument("--api-key-env", type=str, default="ANTHROPIC_API_KEY", help="Environment variable name for API key")
    parser.add_argument("--adaptation-frequency", type=int, default=2, help="How often to adapt the plan")
    
    args = parser.parse_args()
    
    # Get API key from environment
    api_key = get_api_key(args.api_key_env)
    if not api_key:
        sys.exit(1)
    
    # Run the demo
    asyncio.run(run_demo(
        topic=args.topic,
        goal=args.goal,
        max_steps=args.steps,
        model_name=args.model,
        api_key=api_key,
        adaptation_frequency=args.adaptation_frequency
    ))