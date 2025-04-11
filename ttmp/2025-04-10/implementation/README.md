# HTN Planning Agent Implementation

This directory contains the implementation of the Hierarchical Task Network (HTN) Planning Agent described in the tutorial document.

## Components

The implementation is divided into the following components:

- `task_primitives.py`: Core classes for task representation and management 
- `planning_state.py`: State tracking for the planning process
- `task_decomposer.py`: LLM-based task decomposition
- `task_executor.py`: Task execution with LLM
- `plan_adapter.py`: Dynamic plan adaptation based on execution results
- `htn_planning_agent.py`: Main controller for the planning agent
- `demo.py`: Demo script showing the agent in action with mock LLM
- `real_agno.py`: Integration with real Agno agents, including error handling and JSON parsing
- `real_agno_demo.py`: Demo script using real Agno agent

## Unit Tests

Each component has associated unit tests:

- `test_task.py`: Tests for the Task class
- `test_task_manager.py`: Tests for the TaskManager class
- `test_planning_state.py`: Tests for the PlanningState class
- `test_task_decomposer.py`: Tests for the TaskDecomposer class
- `test_task_executor.py`: Tests for the TaskExecutor class
- `test_plan_adapter.py`: Tests for the PlanAdapter class
- `test_htn_planning_agent.py`: Tests for the HTNPlanningAgent class

## Running Tests

To run all tests:

```bash
cd /path/to/implementation
python -m unittest discover
```

To run a specific test:

```bash
python -m unittest test_task_manager
```

## Running the Mock Demo

To run the demo with mocked LLM responses (no API key required):

```bash
python demo.py
```

With custom parameters:

```bash
python demo.py "Artificial Intelligence" "covers recent breakthroughs and applications" 15
```

Parameters:
1. Research topic
2. Research goal
3. Maximum number of plan execution steps

## Running with Real Agno Agent

To run the demo with a real Agno agent:

1. Install Agno if you haven't already:
   ```bash
   pip install agno
   ```

2. Set your API key as an environment variable:
   ```bash
   export ANTHROPIC_API_KEY=your-api-key
   # Or for OpenAI models:
   export OPENAI_API_KEY=your-api-key
   ```

3. Run the real Agno demo:
   ```bash
   python real_agno_demo.py --topic "Quantum Computing" --goal "explains recent developments" --steps 10 --model "claude-3-sonnet-20240229" --api-key-env "ANTHROPIC_API_KEY"
   ```

Command-line options:

```
--topic          Research topic (default: "Quantum Computing")
--goal           Research goal (default: "explains recent developments and future prospects")
--steps          Maximum number of execution steps (default: 10)
--model          LLM model to use (default: "claude-3-sonnet-20240229")
--api-key-env    Environment variable name for API key (default: "ANTHROPIC_API_KEY")
--adaptation-frequency  How often to adapt the plan (default: 2)
--debug          Enable debug logging (saves detailed traces to traces/ directory)
```

## Using in Your Own Code

To use the HTN Planning Agent in your own code:

```python
from real_agno import create_agno_agent
from htn_planning_agent import HTNPlanningAgent
import asyncio

async def main():
    # Create Agno agent
    agent = create_agno_agent(
        model_name="claude-3-sonnet-20240229",
        api_key="your-api-key",
        instructions="You are an expert researcher and writer"
    )
    
    # Create HTN planning agent
    planner = HTNPlanningAgent(agent)
    
    # Use the planner
    report = await planner.research_and_write_report(
        topic="Your Research Topic",
        goal="your research goal description",
        max_steps=15
    )
    
    print(report)

# Run the async function
asyncio.run(main())
```

## Features

### Robust JSON Parsing

The implementation includes a robust JSON parsing mechanism that can handle various response formats:

- Extracts JSON from markdown code blocks
- Handles responses that may have additional text around the JSON
- Validates JSON structure and provides fallback defaults

### Error Handling and Retries

The implementation includes comprehensive error handling:

- Automatic retries with configurable max attempts
- Detailed logging of errors and retry attempts
- Fallback mechanisms when operations fail
- Structured error messages in the logs

### Logging

Detailed logging is implemented throughout the codebase:

- Hierarchical log structure with different levels (INFO, DEBUG, WARNING, ERROR)
- Both console and file logging
- Configurable log levels
- Contextual information in log messages

### Tracing

The implementation includes an extensive tracing system that saves detailed information about each step of the planning and execution process to JSON files in the `traces/` directory:

- **LLM Interactions**: All prompts sent to the LLM and their responses are saved
- **Task Decomposition**: The process of breaking down tasks, including raw and parsed JSON responses
- **Task Execution**: Details about task execution, including retry attempts and results
- **Error Handling**: Comprehensive error information, including retry attempts and stack traces
- **JSON Parsing**: The entire JSON parsing process is traced, showing each attempt and method
- **Run Metrics**: Overall metrics for each run, including durations, task counts, and success rates

To enable more verbose tracing, use the `--debug` flag:

```bash
python real_agno_demo.py --topic "Quantum Computing" --debug
```

Alternatively, set the LOG_LEVEL environment variable:

```bash
LOG_LEVEL=DEBUG python real_agno_demo.py
```

The traces are saved as JSON files in the `traces/` directory with timestamps and unique IDs, making it easy to analyze the execution flow and debug issues.

## Architecture

The architecture follows the design described in the tutorial:

- **Task Manager**: Handles task representation, dependencies, and execution ordering
- **Task Decomposer**: LLM-powered component that breaks down complex tasks
- **Task Executor**: Executes primitive tasks using appropriate tools
- **State Tracker**: Maintains the world state and task results
- **Plan Adapter**: Dynamically adapts plans based on execution results
- **Planning Controller**: Orchestrates the planning and execution process

This implementation demonstrates how to use LLMs for both task decomposition and execution within an HTN planning framework, with production-ready features like error handling, retries, and logging.