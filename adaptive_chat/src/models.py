from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum
import datetime


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)


# class CommunicationStyle(BaseModel):
#     """Model representing a user's communication style preferences."""
#     message_length: str = "medium"  # short, medium, long
#     formality_level: float = 0.5  # 0.0 = very casual, 1.0 = very formal
#     emoji_frequency: float = 0.3  # 0.0 = no emojis, 1.0 = lots of emojis
#     sentence_complexity: float = 0.5  # 0.0 = simple sentences, 1.0 = complex sentences
#     vocabulary_level: float = 0.5  # 0.0 = simple vocabulary, 1.0 = advanced vocabulary


class UserProfile(BaseModel):
    """User profile for Series social network."""
    user_id: str
    conversation_history: List[Dict] = Field(default_factory=list)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    last_updated: datetime.datetime = Field(default_factory=datetime.datetime.now)
    
    # Profile data collected during onboarding
    color: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    three_types_of_people: Optional[List[str]] = None
    who_to_meet: Optional[str] = None
    more_details: Optional[str] = None
    selfie_received: bool = False
    
    # Interest profiling data
    top_passions: Optional[List[str]] = None
    project_or_hobby: Optional[str] = None
    skill_to_improve: Optional[str] = None
    
    # Additional profile data that might be extracted from conversations
    location: Optional[str] = None
    school: Optional[str] = None
    occupation: Optional[str] = None
    current_projects: Optional[List[str]] = None
    goals: Optional[List[str]] = None
    age: Optional[int] = None
    
    # Extracted preferences
    communication_preferences: Dict[str, Any] = Field(default_factory=dict)
    interests: List[str] = Field(default_factory=list)
    
    # Conversation metadata
    last_message_timestamp: Optional[datetime.datetime] = None
    total_messages: int = 0
    
    # Communication style preferences
    # communication_style: CommunicationStyle = Field(default_factory=CommunicationStyle)
    
    # Tracking onboarding progress
    onboarding_step: int = 0
    onboarding_complete: bool = False
    
    def update_from_message(self, message: str) -> None:
        """Update profile fields based on information from a message."""
        # This method could be enhanced with AI-based extraction
        # For now, we'll just update message counts
        self.total_messages += 1
        self.last_message_timestamp = datetime.datetime.now() 