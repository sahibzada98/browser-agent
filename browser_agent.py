#!/usr/bin/env python3
"""
Browser Agent - A simple CLI tool to interact with web browsers using AI.
"""

import asyncio
import os
from browser_use import Agent, ChatAnthropic, Controller, ActionResult, BrowserProfile, BrowserSession
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# print BROWSER_USE_LOGGING_LEVEL
print(os.getenv('BROWSER_USE_LOGGING_LEVEL'))

browser_profile = BrowserProfile(
	executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
	user_data_dir='~/.config/browseruse/profiles/real-chrome',
)
browser_session = BrowserSession(browser_profile=browser_profile)


async def main():
    # Check for API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it with: export ANTHROPIC_API_KEY=your_key_here")
        return
    
    # Get user prompt
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
        input("Press Enter to continue...")
        
        print("\n" + "=" * 50)
        print("Task completed successfully!")
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