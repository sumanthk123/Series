# import os
# from typing import Dict, List, Any, Optional
# import logging
# import datetime
# from supabase import create_client, Client
# from dotenv import load_dotenv

# # Import the serializer for datetime objects
# from .datetime_serializer import serialize_for_supabase

# # Configure logging
# logger = logging.getLogger(__name__)

# # Load environment variables
# load_dotenv()

# class SupabaseClient:
#     """
#     Client for interacting with Supabase to store user data and conversation history.
#     """
    
#     def __init__(self):
#         """Initialize the Supabase client with credentials."""
#         # Get credentials from environment variables, with fallback to hardcoded values
#         self.supabase_url = os.getenv("SUPABASE_URL", "https://ktqnotvhfnugqfqcpabf.supabase.co")
#         self.supabase_key = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt0cW5vdHZoZm51Z3FmcWNwYWJmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDUxODM5NzAsImV4cCI6MjA2MDc1OTk3MH0.mobmfobpT7sb_LgmoeFykHfVb4KGH1YHY6m8_Y_ytvw")
        
#         # Initialize Supabase client
#         try:
#             self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
#             logger.info("Supabase client initialized successfully")
#         except Exception as e:
#             logger.error(f"Failed to initialize Supabase client: {str(e)}")
#             self.supabase = None
            
#     def is_connected(self) -> bool:
#         """Check if the Supabase client is properly connected."""
#         return self.supabase is not None
    
#     async def store_user_profile(self, user_profile: Dict) -> bool:
#         """
#         Store or update a user profile in Supabase.
        
#         Args:
#             user_profile: Dictionary containing user profile data
            
#         Returns:
#             True if operation was successful, False otherwise
#         """
#         if not self.is_connected():
#             logger.error("Cannot store user profile: Supabase client not connected")
#             return False
            
#         try:
#             # Prepare the data for Supabase
#             # Remove conversation_history from the profile as we'll store that separately
#             profile_data = user_profile.copy()
#             conversation_history = profile_data.pop("conversation_history", [])
            
#             # Serialize the data for Supabase (handle datetime objects)
#             # profile_data = serialize_for_supabase(profile_data)
            
#             # Use user_id as the primary key
#             user_id = profile_data.get("user_id")
#             if not user_id:
#                 logger.error("Cannot store user profile: missing user_id")
#                 return False
                
#             # Upsert the user profile (insert if not exists, update if exists)
#             result = self.supabase.table("user_profiles").upsert(
#                 profile_data, 
#                 on_conflict="user_id"
#             ).execute()
            
#             # Also store the conversation history
#             if conversation_history:
#                 await self.store_conversation_history(user_id, conversation_history)
                
#             logger.info(f"Successfully stored user profile for user_id: {user_id}")
#             return True
            
#         except Exception as e:
#             logger.error(f"Error storing user profile: {str(e)}")
#             return False
    
#     async def store_conversation_history(self, user_id: str, messages: List[Dict]) -> bool:
#         """
#         Store conversation history for a user in Supabase.
        
#         Args:
#             user_id: The ID of the user
#             messages: List of message dictionaries
            
#         Returns:
#             True if operation was successful, False otherwise
#         """
#         if not self.is_connected():
#             logger.error("Cannot store conversation: Supabase client not connected")
#             return False
            
#         try:
#             # First ensure user profile exists
#             await self._ensure_user_profile_exists(user_id)
            
#             # Process each message and add user_id to link them to the user
#             processed_messages = []
#             for msg in messages:
#                 # Make a copy to avoid modifying the original
#                 message_data = msg.copy()
                
#                 # Add the user_id to link this message to the user
#                 message_data["user_id"] = user_id
                
#                 # Generate a unique message_id if not present
#                 if "message_id" not in message_data:
#                     # Get timestamp or create a new one
#                     timestamp = message_data.get("timestamp", datetime.datetime.now())
#                     if hasattr(timestamp, "isoformat"):
#                         timestamp_str = timestamp.isoformat()
#                     else:
#                         timestamp_str = str(timestamp)
#                     message_data["message_id"] = f"{user_id}_{timestamp_str}"
                
#                 # Serialize the data for Supabase (handle datetime objects)
#                 message_data = serialize_for_supabase(message_data)
                
#                 processed_messages.append(message_data)
                
#             # Batch insert the messages
#             if processed_messages:
#                 result = self.supabase.table("conversations").upsert(
#                     processed_messages,
#                     on_conflict="message_id"
#                 ).execute()
                
#                 logger.info(f"Successfully stored {len(processed_messages)} messages for user_id: {user_id}")
                
#             return True
            
#         except Exception as e:
#             logger.error(f"Error storing conversation history: {str(e)}")
#             return False
    
#     async def fetch_user_profile(self, user_id: str) -> Optional[Dict]:
#         """
#         Fetch a user profile from Supabase.
        
#         Args:
#             user_id: The ID of the user to fetch
            
#         Returns:
#             The user profile dictionary, or None if not found or an error occurred
#         """
#         if not self.is_connected():
#             logger.error("Cannot fetch user profile: Supabase client not connected")
#             return None
            
#         try:
#             result = self.supabase.table("user_profiles").select("*").eq("user_id", user_id).execute()
            
#             if result.data and len(result.data) > 0:
#                 user_profile = result.data[0]
                
#                 # Fetch the conversation history for this user
#                 conversation_result = self.supabase.table("conversations") \
#                     .select("*") \
#                     .eq("user_id", user_id) \
#                     .order("timestamp") \
#                     .execute()
                    
#                 # Add the conversation history to the profile
#                 user_profile["conversation_history"] = conversation_result.data if conversation_result.data else []
                
#                 return user_profile
                
#             return None
            
#         except Exception as e:
#             logger.error(f"Error fetching user profile: {str(e)}")
#             return None
            
#     async def add_message(self, user_id: str, role: str, content: str, timestamp=None) -> bool:
#         """
#         Add a single message to the conversation history.
        
#         Args:
#             user_id: The ID of the user
#             role: The role of the message sender (user, assistant, system)
#             content: The message content
#             timestamp: Optional timestamp for the message
            
#         Returns:
#             True if operation was successful, False otherwise
#         """
#         if not self.is_connected():
#             logger.error("Cannot add message: Supabase client not connected")
#             return False
            
#         try:
#             # Ensure user profile exists first
#             await self._ensure_user_profile_exists(user_id)
            
#             # Create a timestamp if not provided
#             if timestamp is None:
#                 timestamp = datetime.datetime.now()
                
#             # Convert timestamp to ISO format string if it's a datetime
#             timestamp_str = timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp)
                
#             # Create the message object
#             message_data = {
#                 "user_id": user_id,
#                 "role": role,
#                 "content": content,
#                 "timestamp": timestamp_str,
#                 "message_id": f"{user_id}_{timestamp_str}"
#             }
            
#             # Insert the message
#             result = self.supabase.table("conversations").insert(message_data).execute()
            
#             logger.info(f"Added message for user_id: {user_id}")
#             return True
            
#         except Exception as e:
#             logger.error(f"Error adding message: {str(e)}")
#             return False
            
#     async def clear_conversation_history(self, user_id: str) -> bool:
#         """
#         Clear the conversation history for a user.
        
#         Args:
#             user_id: The ID of the user
            
#         Returns:
#             True if operation was successful, False otherwise
#         """
#         if not self.is_connected():
#             logger.error("Cannot clear conversation: Supabase client not connected")
#             return False
            
#         try:
#             # Delete all messages for the specified user
#             result = self.supabase.table("conversations").delete().eq("user_id", user_id).execute()
            
#             # Reset the message count
#             await self._reset_message_count(user_id)
            
#             logger.info(f"Cleared conversation history for user_id: {user_id}")
#             return True
            
#         except Exception as e:
#             logger.error(f"Error clearing conversation history: {str(e)}")
#             return False
    
#     async def _ensure_user_profile_exists(self, user_id: str) -> bool:
#         """
#         Ensure a user profile exists in the database.
#         Creates it if it doesn't exist.
        
#         Args:
#             user_id: The ID of the user
            
#         Returns:
#             True if successful, False if failed
#         """
#         try:
#             # Check if user profile exists
#             result = self.supabase.table("user_profiles").select("user_id").eq("user_id", user_id).execute()
            
#             # If user doesn't exist, create a minimal profile
#             if not result.data or len(result.data) == 0:
#                 logger.info(f"Creating new user profile for user_id: {user_id}")
#                 profile_data = {
#                     "user_id": user_id,
#                     "created_at": datetime.datetime.now().isoformat(),
#                     "last_updated": datetime.datetime.now().isoformat()
#                 }
                
#                 result = self.supabase.table("user_profiles").insert(profile_data).execute()
                
#             return True
#         except Exception as e:
#             logger.error(f"Error ensuring user profile exists: {str(e)}")
#             return False
    
#     async def _reset_message_count(self, user_id: str) -> bool:
#         """Reset the message count for a user to zero.
        
#         Args:
#             user_id: The ID of the user
            
#         Returns:
#             True if successful, False if failed
#         """
#         try:
#             update_data = {
#                 "total_messages": 0,
#                 "last_updated": datetime.datetime.now().isoformat()
#             }
            
#             result = self.supabase.table("user_profiles").update(update_data).eq("user_id", user_id).execute()
#             return True
#         except Exception as e:
#             logger.error(f"Error resetting message count: {str(e)}")
#             return False 