import os
from typing import Dict, List, Any, Optional
import datetime
import json
import re
from dotenv import load_dotenv
import requests
import logging

from .models import UserProfile
# from .db_client import SupabaseClient

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class SeriesAIAgent:
    def __init__(self, agent_id: str = "series_ai"):
        self.agent_id = agent_id
        self.user_profiles: Dict[str, UserProfile] = {}
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model_name = os.getenv("MODEL_NAME", "meta-llama/llama-4-maverick:free")
        self.max_context_length = int(os.getenv("MAX_CONTEXT_LENGTH", "30"))
        
        # self.db_client = SupabaseClient()
        
    async def initialize_user(self, user_id: str) -> UserProfile:
        """Create a new user profile if one doesn't exist or fetch from Supabase."""
        if user_id in self.user_profiles:
            return self.user_profiles[user_id]
            
        # if self.db_client.is_connected():
        #     supabase_profile = await self.db_client.fetch_user_profile(user_id)
        #     if supabase_profile:
        #         try:
        #             conversation_history = supabase_profile.pop("conversation_history", [])
                    
        #             # Convert string representations back to appropriate types
        #             for field in ["created_at", "last_updated", "last_message_timestamp"]:
        #                 if field in supabase_profile and isinstance(supabase_profile[field], str):
        #                     try:
        #                         supabase_profile[field] = datetime.datetime.fromisoformat(supabase_profile[field])
        #                     except:
        #                         pass
                    
        #             # Create the user profile
        #             profile = UserProfile(**supabase_profile)
                    
        #             # Add the conversation history
        #             profile.conversation_history = conversation_history
                    
        #             # Store in memory
        #             self.user_profiles[user_id] = profile
        #             return profile
        #         except Exception as e:
        #             logger.error(f"Error converting Supabase profile: {str(e)}")
        
        self.user_profiles[user_id] = UserProfile(
            user_id=user_id
        )
        
        # Store the new profile in Supabase if connected
        # if self.db_client.is_connected():
        #     await self.db_client.store_user_profile(self.user_profiles[user_id].dict())
            
        return self.user_profiles[user_id]
    
    async def process_message(self, message_content: str, user_id: str = "default_user") -> str:
        """Process incoming messages and generate responses based on the SMS onboarding flow."""
        user_profile = await self.initialize_user(user_id)
        
        # Update profile metrics
        user_profile.update_from_message(message_content)
        
        # Store the message in user history locally
        user_profile.conversation_history.append({
            "role": "user",
            "content": message_content,
            "timestamp": datetime.datetime.now()
        })
        
        # Also store in Supabase if connected
        # if self.db_client.is_connected():
        #     await self.db_client.add_message(
        #         user_id=user_id,
        #         role="user",
        #         content=message_content,
        #         timestamp=datetime.datetime.now().isoformat()
        #     )
        
        # Extract information from conversation to update the profile
        # self._update_profile_from_conversation(user_profile)
        
        # Check if this is the first message (user sharing their color)
        is_first_message = len(user_profile.conversation_history) == 1
        
        # If this is the first message, return the standard welcome response
        if is_first_message:
            response = """Hey it's Olivia! Go ahead and save my contact and then we can get started:)

If you got that wrapped up, awesome. Series is the first AI social network—so the way this works is I get to know you, then talk to other AI Friends to connect you to real people based on who you want to meet, kinda like a middleman.

So now I'll ask you a few Qs to create your acct with Series. Alright, let's get this rolling—what's your full name?"""
        else:
            # System message with instructions for the AI
            system_message = {
                "role": "system", 
                "content": """You are SeriesAI (Olivia), an SMS-style onboarding assistant for a social network that matches students and founders.

CONVERSATION STYLE:
- Use a casual, friendly tone with abbreviated text language (u, ur, ppl, etc.)
- Be conversational, warm, and engaging
- Avoid overly formal language
- Use emojis occasionally but not excessively
- Keep responses concise - short paragraphs with line breaks for readability

ONBOARDING SEQUENCE:
1. After user shares their full name, ask for their email (encourage school email if they're a student)
2. Ask for a brief bio about themselves (offer examples like "student @UCLA running a tech startup")
3. Ask about 3 types of people they know (offer examples like "tech founders in SF")
4. Ask who they want to meet (ask for specific details if they're vague)
5. After they confirm they're ready, ask for a selfie to complete their profile

IMPORTANT GUIDELINES:
- Guide the user through the exact sequence above
- If user provides vague or minimal responses, gently ask for more specific details
- If the conversation gets off track, steer it back to the next step in the sequence
- Store important user details to reference later in the conversation
- Match the user's energy level and communication style
- Act as if you've already been connected via text message as "Olivia"
- READ AND REFERENCE THE FULL CONVERSATION HISTORY to provide coherent and contextual responses
- Remember details the user has shared previously and use them appropriately
"""
            }
            
            # Build the conversation history with all past messages
            messages = [system_message]
            
            # Get all conversation history, limited by max_context_length
            # If we have more messages than max_context_length, take the most recent ones
            # But always include the first message for context
            if len(user_profile.conversation_history) > self.max_context_length:
                # Always include the first few messages for context about who they are
                initial_context = user_profile.conversation_history[:3]
                # Then include the most recent messages up to max_context_length - 3
                recent_messages = user_profile.conversation_history[-(self.max_context_length - 3):]
                history_to_include = initial_context + recent_messages
            else:
                history_to_include = user_profile.conversation_history
            
            # Format messages for the LLM
            for message in history_to_include:
                messages.append({
                    "role": message["role"],
                    "content": message["content"]
                })

            response = await self._call_llm_with_messages(messages)
        
        # Store assistant message in history locally
        user_profile.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.datetime.now()
        })
        
        # Also store in Supabase if connected
        # if self.db_client.is_connected():
        #     await self.db_client.add_message(
        #         user_id=user_id,
        #         role="assistant",
        #         content=response,
        #         timestamp=datetime.datetime.now().isoformat()
        #     )
        
        # Update user profile
        user_profile.last_updated = datetime.datetime.now()
        self.user_profiles[user_id] = user_profile
        
        # Store the updated profile in Supabase
        # if self.db_client.is_connected():
        #     await self.db_client.store_user_profile(user_profile.dict())
        
        return response
    
    
    async def _call_llm_with_messages(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """Call OpenRouter API to generate text based on a conversation."""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://series.app"  # Identifying the application
            }
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 1000,
            }
                
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                logger.error(f"Error from OpenRouter API: {response.status_code} - {response.text}")
                return "I'm having trouble connecting right now. Could you try again in a moment?"
                
        except Exception as e:
            logger.error(f"Error calling OpenRouter: {str(e)}")
            return "I'm having trouble connecting right now. Could you try again in a moment?"
        
    def get_state(self) -> Dict:
        """Return the current state of the agent."""
        return {
            "agent_id": self.agent_id,
            "user_profiles": self.user_profiles
        }
        
    def set_state(self, state: Dict) -> None:
        """Set the state of the agent."""
        self.agent_id = state.get("agent_id", self.agent_id)
        self.user_profiles = state.get("user_profiles", {}) 