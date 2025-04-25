# import os
# import uuid
# from typing import Dict, List, Optional
# from fastapi import FastAPI, HTTPException, Depends, Request
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse, HTMLResponse
# from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates
# from pydantic import BaseModel
# import uvicorn
# from dotenv import load_dotenv
# import pathlib
# import traceback
# import logging

# from .agent import SeriesAIAgent
# from .models import MessageRole
# from .conversation_store import ConversationStore
# from .imessage_client import iMessageClient

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.StreamHandler(),
#         logging.FileHandler("adaptive_chat.log")
#     ]
# )

# logger = logging.getLogger(__name__)

# # Load environment variables
# load_dotenv()

# # Initialize the app
# app = FastAPI(
#     title="Series AI API",
#     description="An API for an SMS-style onboarding assistant for a social network that matches students and founders",
#     version="1.0.0"
# )

# # CORS settings
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # In production, replace with specific origins
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"]
# )

# # Create directories if they don't exist
# os.makedirs("data", exist_ok=True)

# # Determine static files directory
# base_dir = pathlib.Path(__file__).parent
# static_dir = base_dir / "static"
# os.makedirs(static_dir, exist_ok=True)

# # Mount static files directory
# app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# # Initialize the conversation store
# conversation_store = ConversationStore(data_dir="data")

# # Initialize the agent
# agent = SeriesAIAgent()

# # Initialize iMessage client
# imessage = iMessageClient()


# class UserMessage(BaseModel):
#     """Schema for incoming user messages."""
#     message: str
#     user_id: Optional[str] = None


# class MessageRequest(BaseModel):
#     """Schema for API message requests."""
#     message: str
#     user_id: Optional[str] = None


# class BotResponse(BaseModel):
#     """Schema for outgoing bot responses."""
#     message: str
#     user_id: str


# class SMSMessage(BaseModel):
#     """Schema for sending SMS/iMessage."""
#     phone_number: str
#     message: str


# class SMSResponse(BaseModel):
#     """Schema for SMS/iMessage response."""
#     success: bool
#     message: str
#     phone_number: str


# @app.get("/", response_class=HTMLResponse)
# async def root(request: Request):
#     """Root endpoint that serves the chat interface."""
#     try:
#         # Read the HTML file
#         with open(os.path.join(static_dir, "index.html"), "r") as f:
#             html_content = f.read()
#         return HTMLResponse(content=html_content)
#     except FileNotFoundError:
#         # If HTML file doesn't exist, return the API info
#         return JSONResponse(content={
#             "message": "Series AI API is running",
#             "version": "1.0.0",
#             "endpoints": {
#                 "/chat": "POST - Send a message to the chat agent",
#                 "/users/{user_id}": "GET - Retrieve user profile information",
#                 "/users/{user_id}/history": "GET - Retrieve conversation history for a user",
#                 "/users/{user_id}/clear": "POST - Clear conversation history for a user",
#                 "/imessage/send": "POST - Send a message via iMessage",
#                 "/imessage/status": "GET - Check iMessage status",
#                 "/imessage/conversations": "GET - Get recent iMessage conversations"
#             }
#         })


# @app.get("/api")
# async def api_info():
#     """API information endpoint."""
#     return {
#         "message": "Series AI API is running",
#         "version": "1.0.0",
#         "endpoints": {
#             "/chat": "POST - Send a message to the chat agent",
#             "/users/{user_id}": "GET - Retrieve user profile information",
#             "/users/{user_id}/history": "GET - Retrieve conversation history for a user",
#             "/users/{user_id}/clear": "POST - Clear conversation history for a user",
#             "/imessage/send": "POST - Send a message via iMessage",
#             "/imessage/status": "GET - Check iMessage status",
#             "/imessage/conversations": "GET - Get recent iMessage conversations"
#         }
#     }


# @app.post("/chat", response_model=BotResponse)
# async def chat(request: UserMessage):
#     """
#     Send a message to the chat agent and get a response.
    
#     Args:
#         request: The user message request
        
#     Returns:
#         The bot's response
#     """
#     try:
#         # Generate or use the provided user ID
#         user_id = request.user_id or str(uuid.uuid4())
        
#         # Add the user message to the conversation history 
#         conversation_store.add_message(
#             user_id=user_id,
#             role=MessageRole.USER,
#             content=request.message
#         )
        
#         # Process the message
#         response_text = await agent.process_message(request.message, user_id)
        
#         # Add the agent's response to conversation history
#         conversation_store.add_message(
#             user_id=user_id,
#             role=MessageRole.ASSISTANT,
#             content=response_text
#         )
        
#         # Return the response
#         return BotResponse(
#             message=response_text,
#             user_id=user_id
#         )
        
#     except Exception as e:
#         logger.error(f"Error in chat endpoint: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


# @app.get("/users/{user_id}")
# async def get_user_profile(user_id: str):
#     """
#     Get a user's profile information.
    
#     Args:
#         user_id: The user ID to get the profile for
        
#     Returns:
#         The user profile
#     """
#     try:
#         profile = conversation_store.get_profile(user_id)
#         # Don't include the full conversation history
#         profile_dict = profile.dict()
#         profile_dict.pop("conversation_history", None)
#         return profile_dict
#     except Exception as e:
#         logger.error(f"Error retrieving user profile: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Error retrieving user profile: {str(e)}")


# @app.get("/users/{user_id}/history")
# async def get_conversation_history(user_id: str, limit: Optional[int] = None):
#     """
#     Get a user's conversation history.
    
#     Args:
#         user_id: The user ID to get the history for
#         limit: Optional limit on the number of messages to return
        
#     Returns:
#         The conversation history
#     """
#     try:
#         history = conversation_store.get_conversation_history(user_id, limit)
#         return {"history": [msg.dict() for msg in history]}
#     except Exception as e:
#         logger.error(f"Error retrieving conversation history: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Error retrieving conversation history: {str(e)}")


# @app.post("/users/{user_id}/clear")
# async def clear_conversation_history(user_id: str):
#     """
#     Clear a user's conversation history.
    
#     Args:
#         user_id: The user ID to clear the history for
        
#     Returns:
#         Success message
#     """
#     try:
#         conversation_store.clear_history(user_id)
#         return {"message": "Conversation history cleared successfully"}
#     except Exception as e:
#         logger.error(f"Error clearing conversation history: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Error clearing conversation history: {str(e)}")


# @app.post("/api/process-message")
# async def process_message(request: MessageRequest):
#     """
#     Process a user message and get an AI response.
    
#     Args:
#         request: The message request containing the message text and optional user ID
        
#     Returns:
#         A response object with the AI's reply
#     """
#     try:
#         user_id = request.user_id or "default_user"
#         logger.info(f"Processing message from user {user_id}: {request.message}")
        
#         # Use the standard processing pathway
#         response = await agent.process_message(
#             message_content=request.message,
#             user_id=user_id
#         )
        
#         # Store messages in conversation history
#         conversation_store.add_message(
#             user_id=user_id,
#             role=MessageRole.USER,
#             content=request.message
#         )
            
#         conversation_store.add_message(
#             user_id=user_id,
#             role=MessageRole.ASSISTANT,
#             content=response
#         )
        
#         return {"response": response}
#     except Exception as e:
#         logger.error(f"Error processing message: {str(e)}")
#         traceback.print_exc()
#         return JSONResponse(
#             status_code=500,
#             content={"error": f"Failed to process message: {str(e)}"}
#         )


# # iMessage Integration Endpoints

# @app.post("/imessage/send", response_model=SMSResponse)
# async def send_imessage(message_data: SMSMessage):
#     """
#     Send a message via iMessage.
    
#     Args:
#         message_data: The message data including phone number and content
        
#     Returns:
#         Status of the send operation
#     """
#     if not imessage.is_macos:
#         raise HTTPException(status_code=400, detail="iMessage integration is only available on macOS")
    
#     if not imessage.check_imessage_enabled():
#         raise HTTPException(status_code=400, detail="iMessage is not properly configured on this Mac")
    
#     result = imessage.send_message(
#         phone_number=message_data.phone_number,
#         message=message_data.message
#     )
    
#     if result:
#         return SMSResponse(
#             success=True,
#             message="Message sent successfully",
#             phone_number=message_data.phone_number
#         )
#     else:
#         return SMSResponse(
#             success=False,
#             message="Failed to send message",
#             phone_number=message_data.phone_number
#         )


# @app.post("/imessage/chat-agent/{phone_number}")
# async def chat_agent_via_imessage(phone_number: str, request: MessageRequest):
#     """
#     Process a message with the AI agent and send the response via iMessage.
    
#     Args:
#         phone_number: The recipient's phone number
#         request: The message request
        
#     Returns:
#         Status of the operation
#     """
#     if not imessage.is_macos:
#         raise HTTPException(status_code=400, detail="iMessage integration is only available on macOS")
    
#     if not imessage.check_imessage_enabled():
#         raise HTTPException(status_code=400, detail="iMessage is not properly configured on this Mac")
    
#     try:
#         # Use the phone number as the user ID to maintain conversation context
#         user_id = f"phone_{phone_number}"
        
#         # Process the message with the AI agent
#         response = await agent.process_message(
#             message_content=request.message,
#             user_id=user_id
#         )
        
#         # Store messages in conversation history
#         conversation_store.add_message(
#             user_id=user_id,
#             role=MessageRole.USER,
#             content=request.message
#         )
            
#         conversation_store.add_message(
#             user_id=user_id,
#             role=MessageRole.ASSISTANT,
#             content=response
#         )
        
#         # Send the AI response via iMessage
#         result = imessage.send_message(
#             phone_number=phone_number,
#             message=response
#         )
        
#         return {
#             "success": result,
#             "message": "Response sent via iMessage" if result else "Failed to send response via iMessage",
#             "phone_number": phone_number,
#             "ai_response": response
#         }
        
#     except Exception as e:
#         logger.error(f"Error in chat-agent via iMessage: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


# @app.get("/imessage/status")
# async def check_imessage_status():
#     """
#     Check if iMessage is properly configured and available.
    
#     Returns:
#         Status of iMessage on this Mac
#     """
#     if not imessage.is_macos:
#         return {"available": False, "reason": "Not running on macOS"}
    
#     enabled = imessage.check_imessage_enabled()
#     return {
#         "available": enabled,
#         "reason": "iMessage is enabled and ready" if enabled else "iMessage is not properly configured"
#     }


# @app.get("/imessage/conversations")
# async def get_imessage_conversations(limit: int = 10):
#     """
#     Get a list of recent iMessage conversations.
    
#     Args:
#         limit: Maximum number of conversations to return
        
#     Returns:
#         List of recent conversations
#     """
#     if not imessage.is_macos:
#         raise HTTPException(status_code=400, detail="iMessage integration is only available on macOS")
    
#     conversations = imessage.get_recent_conversations(limit=limit)
#     return {"conversations": conversations, "count": len(conversations)}


# if __name__ == "__main__":
#     uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True) 