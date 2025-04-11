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

# Ensure traces directory exists
TRACES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'traces')
os.makedirs(TRACES_DIR, exist_ok=True)

# Set up logging - more verbose in debug mode
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_LEVEL = getattr(logging, LOG_LEVEL) if LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] else logging.INFO

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('htn_agent_demo.log')
    ]
)
logger = logging.getLogger('htn_agent_demo')

# Set module loggers to appropriate level
logging.getLogger('htn_agent').setLevel(LOG_LEVEL)
logging.getLogger('htn_agent.task_decomposer').setLevel(LOG_LEVEL)
logging.getLogger('htn_agent.task_executor').setLevel(LOG_LEVEL)
logging.getLogger('htn_agent.plan_adapter').setLevel(LOG_LEVEL)

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
    # Generate a unique run ID for this demo
    run_id = f"run_{int(asyncio.get_event_loop().time())}"
    run_start_time = asyncio.get_event_loop().time()
    
    # Try to get tracing functionality
    save_trace = None
    try:
        from real_agno import save_trace as real_save_trace
        save_trace = real_save_trace
        logger.info(f"Trace logging enabled for demo run {run_id}")
    except ImportError:
        logger.warning(f"Trace logging not available for demo run {run_id}")
    
    # Log run start
    logger.info(f"Starting HTN Planning Agent demo with {model_name} (Run ID: {run_id})")
    
    # Save run configuration if tracing is available
    if save_trace:
        run_config = {
            "run_id": run_id,
            "topic": topic,
            "goal": goal,
            "max_steps": max_steps,
            "model_name": model_name,
            "adaptation_frequency": adaptation_frequency,
            "timestamp": asyncio.get_event_loop().time(),
            "log_level": LOG_LEVEL
        }
        save_trace("demo_run_start", run_config, {"run_id": run_id})
    
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
        execution_start_time = asyncio.get_event_loop().time()
        report = await planner.research_and_write_report(topic, goal, max_steps)
        execution_end_time = asyncio.get_event_loop().time()
        execution_duration = execution_end_time - execution_start_time
        
        # Save execution metrics if tracing is available
        if save_trace:
            execution_metrics = {
                "run_id": run_id,
                "execution_duration_seconds": execution_duration,
                "tasks_total": len(planner.task_manager.tasks) if hasattr(planner, 'task_manager') else 0,
                "tasks_completed": sum(1 for task in planner.task_manager.tasks.values() if task.status.name == "COMPLETED") if hasattr(planner, 'task_manager') else 0,
                "tasks_failed": sum(1 for task in planner.task_manager.tasks.values() if task.status.name == "FAILED") if hasattr(planner, 'task_manager') else 0,
                "report_length": len(report) if report else 0
            }
            save_trace("demo_execution_metrics", execution_metrics, {"run_id": run_id})
        
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
        
        # Save final plan status if tracing is available
        if save_trace:
            save_trace("demo_final_plan_status", status, {"run_id": run_id})
        
        # Display some facts gathered during research
        logger.info(f"\n===== Facts Gathered =====\n")
        if planner.state and planner.state.facts:
            for key, value in planner.state.facts.items():
                log_value = f"{value[:100]}..." if len(value) > 100 else value
                logger.info(f"- {key}: {log_value}")
            
            # Save facts if tracing is available
            if save_trace:
                save_trace("demo_facts_gathered", planner.state.facts, {"run_id": run_id})
        else:
            logger.info("No facts gathered")
        
        # Log completion time
        run_end_time = asyncio.get_event_loop().time()
        run_duration = run_end_time - run_start_time
        logger.info(f"\n===== Demo Complete =====")
        logger.info(f"Run duration: {run_duration:.2f} seconds")
        
        # Save run completion if tracing is available
        if save_trace:
            completion_data = {
                "run_id": run_id,
                "duration_seconds": run_duration,
                "success": True,
                "task_count": len(planner.task_manager.tasks) if hasattr(planner, 'task_manager') else 0
            }
            save_trace("demo_run_complete", completion_data, {"run_id": run_id})
        
        # Return the report for potential further processing
        return report
        
    except Exception as e:
        # Log error details
        logger.error(f"Error running demo (Run ID: {run_id}): {str(e)}", exc_info=True)
        
        # Save error information if tracing is available
        if save_trace:
            error_data = {
                "run_id": run_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "duration_seconds": asyncio.get_event_loop().time() - run_start_time,
                "success": False
            }
            save_trace("demo_run_error", error_data, {"run_id": run_id})
        
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
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Set debug level if requested
    if args.debug:
        os.environ["LOG_LEVEL"] = "DEBUG"
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger('htn_agent').setLevel(logging.DEBUG)
        logging.getLogger('htn_agent.task_decomposer').setLevel(logging.DEBUG)
        logging.getLogger('htn_agent.task_executor').setLevel(logging.DEBUG)
        logging.getLogger('htn_agent.plan_adapter').setLevel(logging.DEBUG)
        logger.info("Debug logging enabled")
    
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