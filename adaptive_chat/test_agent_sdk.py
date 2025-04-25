#!/usr/bin/env python3
"""
Test script for Agent SDK integration with the SeriesAI agent using Meta Llama 4 Maverick model.
"""

import asyncio
from dotenv import load_dotenv
import os

from src.agent import SeriesAIAgent

async def test_agent_sdk():
    """Test the SeriesAI agent with the OpenAI Agents SDK using Meta Llama 4 Maverick model."""
    print("Testing SeriesAI Agent with the OpenAI Agents SDK using Meta Llama 4 Maverick model...")
    
    # Initialize the agent
    agent = SeriesAIAgent()
    
    # Set up a test message and user ID
    message = "Hi, I'm interested in connecting with other students."
    user_id = "test_user_123"
    
    # Check if required API keys are set
    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "sk-your-openai-api-key":
        print("\nWARNING: No valid OpenAI API key provided in the .env file.")
        print("The test will fall back to using the regular processing method.")
        print("To use the OpenAI Agents SDK, please add your OpenAI API key to the .env file.\n")
    
    if not os.getenv("OPENROUTER_API_KEY"):
        print("\nWARNING: No valid OpenRouter API key provided in the .env file.")
        print("This is required to use the Meta Llama 4 Maverick model through OpenRouter.\n")
    
    model_name = os.getenv("MODEL_NAME", "meta-llama/llama-4-maverick:free")
    print(f"Using model: {model_name}")
    
    try:
        # Process the message using the SDK integration with Meta Llama 4 Maverick
        # The agent will automatically fall back to regular processing if SDK fails
        response = await agent.process_with_sdk(message, user_id)
        print(f"\nResponse from Meta Llama 4 Maverick via SDK: {response}\n")
        
        # For comparison, also test the regular method
        response2 = await agent.process_message(message, user_id)
        print(f"\nResponse from regular method using OpenRouter directly: {response2}\n")
        
        print("Test completed successfully!")
    except Exception as e:
        print(f"Error during test: {str(e)}")
        print("Please make sure all environment variables are properly set in the .env file.")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Temporarily set USE_AGENT_SDK to true for testing
    os.environ["USE_AGENT_SDK"] = "true"
    
    # Run the test
    asyncio.run(test_agent_sdk()) 