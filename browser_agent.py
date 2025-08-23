#!/usr/bin/env python3
"""
Browser Agent - A simple CLI tool to interact with web browsers using AI.
"""

import asyncio
import os
from browser_use import Agent, ChatAnthropic
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


async def main():
    # Check for API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it with: export ANTHROPIC_API_KEY=your_key_here")
        return
    
    # Get user prompt
    prompt = input("Enter your task for the browser agent: ")
    
    if not prompt.strip():
        print("No task provided. Exiting.")
        return
    
    print(f"\nStarting browser agent with task: {prompt}")
    print("=" * 50)
    
    try:
        # Initialize the Anthropic client
        llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=api_key
        )
        
        # Create and run the browser agent
        agent = Agent(
            task=prompt,
            llm=llm,
        )
        
        # Execute the task
        result = await agent.run()
        
        print("\n" + "=" * 50)
        print("Task completed successfully!")
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"\nError occurred: {e}")
        print("Make sure you have:")
        print("1. Set ANTHROPIC_API_KEY environment variable")
        print("2. Installed browser-use and dependencies")
        print("3. Chromium browser available via Playwright")


if __name__ == "__main__":
    asyncio.run(main())