# import json
# import os
# from typing import Dict, List, Optional
# import datetime
# from pathlib import Path

# from .models import UserProfile, Message, MessageRole


# class ConversationStore:
#     """
#     A class that manages persistent storage of user profiles and conversation histories.
#     Uses simple JSON file storage, could be replaced with a database in production.
#     """
    
#     def __init__(self, data_dir: str = "data"):
#         """
#         Initialize the conversation store with a data directory.
        
#         Args:
#             data_dir: Directory where user profiles will be stored
#         """
#         self.data_dir = Path(data_dir)
#         self.ensure_data_dir()
#         self.profiles: Dict[str, UserProfile] = {}
#         self.load_all_profiles()
        
#     def ensure_data_dir(self) -> None:
#         """Ensure the data directory exists."""
#         os.makedirs(self.data_dir, exist_ok=True)
        
#     def profile_path(self, user_id: str) -> Path:
#         """Get the file path for a user profile."""
#         return self.data_dir / f"{user_id}.json"
        
#     def load_all_profiles(self) -> None:
#         """Load all user profiles from disk."""
#         for profile_file in self.data_dir.glob("*.json"):
#             user_id = profile_file.stem
#             try:
#                 with open(profile_file, 'r') as f:
#                     profile_data = json.load(f)
#                     # Parse dates from ISO format strings
#                     if "created_at" in profile_data:
#                         profile_data["created_at"] = datetime.datetime.fromisoformat(profile_data["created_at"])
#                     if "last_updated" in profile_data:
#                         profile_data["last_updated"] = datetime.datetime.fromisoformat(profile_data["last_updated"])
                    
#                     # Parse message timestamps
#                     if "conversation_history" in profile_data:
#                         for message in profile_data["conversation_history"]:
#                             if "timestamp" in message:
#                                 message["timestamp"] = datetime.datetime.fromisoformat(message["timestamp"])
                    
#                     self.profiles[user_id] = UserProfile(**profile_data)
#             except Exception as e:
#                 print(f"Error loading profile {user_id}: {str(e)}")
                
#     def get_profile(self, user_id: str) -> UserProfile:
#         """
#         Get a user profile by ID, creating it if it doesn't exist.
        
#         Args:
#             user_id: The user ID to get the profile for
            
#         Returns:
#             The user profile
#         """
#         if user_id not in self.profiles:
#             self.profiles[user_id] = UserProfile(user_id=user_id)
#             self.save_profile(user_id)
#         return self.profiles[user_id]
        
#     def save_profile(self, user_id: str) -> None:
#         """
#         Save a user profile to disk.
        
#         Args:
#             user_id: The user ID to save the profile for
#         """
#         if user_id not in self.profiles:
#             return
            
#         profile = self.profiles[user_id]
        
#         # Update the last updated timestamp
#         profile.last_updated = datetime.datetime.now()
        
#         # Prepare profile data for serialization
#         profile_dict = profile.dict()
        
#         # Convert datetime objects to ISO format strings for JSON serialization
#         profile_dict["created_at"] = profile_dict["created_at"].isoformat()
#         profile_dict["last_updated"] = profile_dict["last_updated"].isoformat()
            
#         # Convert message timestamps
#         for message in profile_dict["conversation_history"]:
#             if "timestamp" in message:
#                 message["timestamp"] = message["timestamp"].isoformat()
                
#         # Save to disk
#         with open(self.profile_path(user_id), 'w') as f:
#             json.dump(profile_dict, f, indent=2)
            
#     def add_message(self, user_id: str, role: MessageRole, content: str) -> None:
#         """
#         Add a message to a user's conversation history.
        
#         Args:
#             user_id: The user ID to add the message for
#             role: The role of the message sender (user or assistant)
#             content: The message content
#         """
#         profile = self.get_profile(user_id)
        
#         message = {
#             "role": role,
#             "content": content,
#             "timestamp": datetime.datetime.now()
#         }
        
#         profile.conversation_history.append(message)
        
#         # Update onboarding step if it's a user message
#         if role == MessageRole.USER and not profile.onboarding_complete:
#             profile.onboarding_step += 1
            
#             # Mark onboarding as complete after all steps plus interest questions
#             if profile.onboarding_step >= 11:  # 8 onboarding steps + 3 interest questions
#                 profile.onboarding_complete = True
        
#         self.save_profile(user_id)
        
#     def get_conversation_history(self, user_id: str, limit: Optional[int] = None) -> List[Message]:
#         """
#         Get the conversation history for a user.
        
#         Args:
#             user_id: The user ID to get the history for
#             limit: Optional limit on the number of messages to return
            
#         Returns:
#             The conversation history as a list of messages
#         """
#         profile = self.get_profile(user_id)
        
#         # Convert dict messages to Message objects
#         messages = []
#         for msg in profile.conversation_history:
#             messages.append(Message(
#                 role=msg["role"],
#                 content=msg["content"],
#                 timestamp=msg["timestamp"]
#             ))
        
#         if limit is not None and limit > 0:
#             return messages[-limit:]
        
#         return messages
        
#     def update_profile(self, user_id: str, profile: UserProfile) -> None:
#         """
#         Update a user profile with new data.
        
#         Args:
#             user_id: The user ID to update the profile for
#             profile: The new profile data
#         """
#         self.profiles[user_id] = profile
#         self.save_profile(user_id)
        
#     def clear_history(self, user_id: str) -> None:
#         """
#         Clear the conversation history for a user.
        
#         Args:
#             user_id: The user ID to clear the history for
#         """
#         profile = self.get_profile(user_id)
#         profile.conversation_history = []
#         profile.onboarding_step = 0
#         profile.onboarding_complete = False
#         self.save_profile(user_id) 