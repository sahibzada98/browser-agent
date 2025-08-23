#!/usr/bin/env python3
"""
Browser Agent - A simple CLI tool to interact with web browsers using AI.
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from browser_use import Agent, ChatAnthropic, Controller, ActionResult, BrowserProfile, BrowserSession
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# print BROWSER_USE_LOGGING_LEVEL
print(os.getenv('BROWSER_USE_LOGGING_LEVEL'))

# Create a clean temporary browser profile for testing
import tempfile
import uuid

# Use unique temporary directory to avoid conflicts
profile_dir = tempfile.mkdtemp(prefix=f"browser-agent-{uuid.uuid4().hex[:8]}-")
browser_profile = BrowserProfile(
    user_data_dir=profile_dir,
    headless=False,  # Visual mode for debugging
)
browser_session = BrowserSession(browser_profile=browser_profile)


def extract_parameters_from_task(task: str) -> dict[str, str]:
    """Extract parameters from the original user task."""
    parameters = {}
    task_lower = task.lower()
    
    # Extract website parameter
    websites = ["google.com", "bing.com", "github.com", "example.com", "youtube.com"]
    for website in websites:
        if website in task_lower:
            parameters["website"] = website
            break
    
    # Extract search term parameter
    if "search for" in task_lower:
        parts = task.split("search for")
        if len(parts) > 1:
            search_term = parts[1].strip()
            # Remove common endings like "on google", "tutorials", etc.
            search_term = search_term.replace(" on google", "").replace(" on bing", "")
            parameters["search_term"] = search_term
    
    return parameters


def extract_parameters_from_flow(flow_data: dict) -> dict[str, str]:
    """Extract potential parameters from a flow - check original task first."""
    # Try to get parameters from original user task first
    original_task = flow_data.get("original_user_task")
    if original_task:
        parameters = extract_parameters_from_task(original_task)
        if parameters:
            return parameters
    
    # Fallback to extracting from actions (old method)
    parameters = {}
    history = flow_data.get("history", [])
    for step in history:
        model_output = step.get("model_output", {})
        actions = model_output.get("action", [])
        
        for action in actions:
            for action_type, action_params in action.items():
                # Extract URL parameters
                if action_type == "go_to_url" and "url" in action_params:
                    url = action_params["url"]
                    # Simple heuristic: extract domain as parameter
                    if "://" in url:
                        domain = url.split("://")[1].split("/")[0]
                        if not domain.startswith("www."):
                            parameters["website"] = domain
                        else:
                            parameters["website"] = domain[4:]  # Remove www.
                
                # Extract text parameters
                if action_type == "input_text" and "text" in action_params:
                    text = action_params["text"]
                    if len(text.strip()) > 0:
                        parameters["search_term"] = text
    
    return parameters


def substitute_parameters_in_task(original_task: str, param_values: dict[str, str], original_params: dict[str, str]) -> str:
    """Substitute parameters in the original task using simple string replacement."""
    new_task = original_task
    
    for param_name, new_value in param_values.items():
        if param_name == "website" and param_name in original_params:
            # Replace the original website with new one
            old_website = original_params[param_name]
            new_task = new_task.replace(old_website, new_value)
        elif param_name == "search_term" and param_name in original_params:
            # Replace the original search term with new one
            old_search_term = original_params[param_name]
            new_task = new_task.replace(old_search_term, new_value)
    
    return new_task


async def replay_flow_with_params(flow_name: str, api_key: str):
    """Replay a saved flow with parameter substitution."""
    flows_dir = Path("flows")
    flow_path = flows_dir / f"{flow_name}.json"
    
    if not flow_path.exists():
        print(f"Error: Flow '{flow_name}' not found at {flow_path}")
        return
    
    print(f"🔄 Loading flow: {flow_path}")
    
    try:
        with open(flow_path, 'r') as f:
            flow_data = json.load(f)
        
        history = flow_data.get("history", [])
        if not history:
            print("Error: No history found in flow")
            return
        
        # Extract the clean original user task
        original_task = flow_data.get("original_user_task")
        
        if not original_task:
            # Fallback to AI reasoning if original task not available
            first_step = history[0]
            original_task = first_step.get("model_output", {}).get("thinking", "Replay saved flow")
            print("⚠️ Using AI reasoning as task (old flow format)")
        
        print(f"📝 Original task: {original_task}")
        
        # Extract parameters from the flow
        parameters = extract_parameters_from_flow(flow_data)
        
        if not parameters:
            print("❌ No parameters found in this flow. Use --replay-flow instead.")
            return
        
        print(f"\n🔧 Parameters found:")
        param_values = {}
        
        for param_name, default_value in parameters.items():
            print(f"   • {param_name}: {default_value}")
            new_value = input(f"Enter new value for '{param_name}' (press Enter for default): ").strip()
            
            if new_value:
                param_values[param_name] = new_value
                print(f"   ✅ Will use: {new_value}")
            else:
                param_values[param_name] = default_value
                print(f"   ⏯️ Using default: {default_value}")
        
        # Substitute parameters in the original task
        new_task = substitute_parameters_in_task(original_task, param_values, parameters)
        
        print(f"\n🔄 New task: {new_task}")
        print("=" * 50)
        
        # Initialize browser components
        llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=api_key,
            timeout=100
        )
        controller = Controller()
        
        # Create agent to execute the parameterized task
        agent = Agent(
            task=new_task,
            llm=llm,
            controller=controller,
            keep_browser_open=True,
            browser_session=browser_session
        )
        
        print("🚀 Executing parameterized task...")
        
        # Execute the parameterized task
        result = await agent.run()
        
        print("=" * 50)
        print("✅ Parameterized flow replay completed!")
        print(f"📄 Final result: {result}")
        
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in flow file {flow_path}")
    except Exception as e:
        print(f"❌ Error replaying flow with parameters: {e}")
        import traceback
        traceback.print_exc()


async def replay_flow(flow_name: str, api_key: str):
    """Replay a saved flow."""
    flows_dir = Path("flows")
    flow_path = flows_dir / f"{flow_name}.json"
    
    if not flow_path.exists():
        print(f"Error: Flow '{flow_name}' not found at {flow_path}")
        return
    
    print(f"Loading flow: {flow_path}")
    
    try:
        with open(flow_path, 'r') as f:
            flow_data = json.load(f)
        
        history = flow_data.get("history", [])
        if not history:
            print("Error: No history found in flow")
            return
        
        print(f"Found {len(history)} steps in flow")
        print("=" * 50)
        
        # Initialize browser components
        llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=api_key,
            timeout=100
        )
        controller = Controller()
        
        # Extract the original task from the first step
        first_step = history[0]
        original_task = first_step.get("model_output", {}).get("thinking", "Replay saved flow")
        
        # Create agent to replay the flow
        agent = Agent(
            task=f"Replay this flow: {original_task}",
            llm=llm,
            controller=controller,
            keep_browser_open=True,
            browser_session=browser_session
        )
        
        print(f"🔄 Replaying flow with {len(history)} steps...")
        
        # For now, we'll recreate the actions from the flow
        # This is a simplified replay - in the future we can make it more sophisticated
        for i, step in enumerate(history, 1):
            model_output = step.get("model_output", {})
            actions = model_output.get("action", [])
            
            print(f"Step {i}: {model_output.get('next_goal', 'Unknown goal')}")
            
            for action in actions:
                for action_type, action_params in action.items():
                    print(f"  🦾 {action_type}: {action_params}")
        
        # Execute the task (simplified version for now)
        result = await agent.run()
        
        print("=" * 50)
        print("✅ Flow replay completed!")
        
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in flow file {flow_path}")
    except Exception as e:
        print(f"Error replaying flow: {e}")


async def main():
    # Parse command line arguments
    save_flow_name = None
    replay_flow_name = None
    
    if "--save-flow" in sys.argv:
        try:
            flow_index = sys.argv.index("--save-flow")
            save_flow_name = sys.argv[flow_index + 1]
        except (IndexError, ValueError):
            print("Error: --save-flow requires a flow name")
            print("Usage: python browser_agent.py --save-flow \"flow_name\"")
            return
    
    if "--replay-flow" in sys.argv:
        try:
            flow_index = sys.argv.index("--replay-flow")
            replay_flow_name = sys.argv[flow_index + 1]
        except (IndexError, ValueError):
            print("Error: --replay-flow requires a flow name")
            print("Usage: python browser_agent.py --replay-flow \"flow_name\"")
            return
    
    if "--replay-flow-with-params" in sys.argv:
        try:
            flow_index = sys.argv.index("--replay-flow-with-params")
            replay_flow_name = sys.argv[flow_index + 1]
        except (IndexError, ValueError):
            print("Error: --replay-flow-with-params requires a flow name")
            print("Usage: python browser_agent.py --replay-flow-with-params \"flow_name\"")
            return
    
    # Check for API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it with: export ANTHROPIC_API_KEY=your_key_here")
        return
    
    # Handle flow replay
    if replay_flow_name:
        if "--replay-flow-with-params" in sys.argv:
            await replay_flow_with_params(replay_flow_name, api_key)
        else:
            await replay_flow(replay_flow_name, api_key)
        return
    
    # Get user prompt
    if save_flow_name:
        task_prompt = input("Enter the task to record: ")
        if not task_prompt.strip():
            print("No task provided. Exiting.")
            return
        prompt = task_prompt
    else:
        prompt = "never call done, if you dont know what to do use ask_human_for_new_task"
    
    if not prompt.strip():
        print("No task provided. Exiting.")
        return
    
    print(f"\nStarting browser agent with task: {prompt}")
    print("=" * 50)
    
    try:
        # Initialize the Anthropic client
        llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=api_key,
            timeout=100
        )
        controller = Controller( )
        @controller.action("ask_human_for_new_task")
        def ask_human_for_new_task(text: str):
            print(f"Done: {text}")
            answer = input("New task: ")
            response = "This is your new user_task: " + answer
            output = ActionResult(long_term_memory=response)

            return output
        
        # Create and run the browser agent
        agent = Agent(
            task=prompt,
            llm=llm,
            controller=controller,
            keep_browser_open=True,  # Keep browser open after task completion
            browser_session=browser_session
        )
        
        # Execute the task
        result = await agent.run()
        
        # Save flow if requested
        if save_flow_name:
            # Create flows directory
            flows_dir = Path("flows")
            flows_dir.mkdir(exist_ok=True)
            
            # Save the flow with original user task
            flow_path = flows_dir / f"{save_flow_name}.json"
            
            # Get the default flow data
            flow_data = result.model_dump()
            
            # Add the original user task for better replay
            flow_data["original_user_task"] = prompt
            
            # Save enhanced flow data
            with open(flow_path, 'w', encoding='utf-8') as f:
                json.dump(flow_data, f, indent=2)
            
            print(f"\n✅ Flow saved as: {flow_path}")
            print(f"   Original task: {prompt}")
            print(f"   Total steps: {result.number_of_steps()}")
            print(f"   Actions recorded: {len(result.model_actions())}")
            print(f"   Duration: {result.total_duration_seconds():.1f}s")
        
        input("Press Enter to continue...")
        
        print("\n" + "=" * 50)
        print("Task completed successfully!")
        
        if not save_flow_name:
            print(f"Result: {result}")
            
            # Keep browser open for manual interaction
            print("\n" + "=" * 50)
            print("Browser is still open for manual interaction.")
            print("Handle any login/credentials manually, then press Enter to continue...")
            input("Press Enter when done with manual steps: ")
            
            print("You can now continue using the browser or close it manually.")
        
    except Exception as e:
        print(f"\nError occurred: {e}")
        print("Make sure you have:")
        print("1. Set ANTHROPIC_API_KEY environment variable")
        print("2. Installed browser-use and dependencies")
        print("3. Chromium browser available via Playwright")


if __name__ == "__main__":
    asyncio.run(main())