#!/usr/bin/env python3
"""
iMessage Agent Integration

This script monitors iMessage conversations from the Messages database on macOS,
filters messages that start with a welcome prompt, and responds using the
adaptive_chat agent.

Requirements:
- macOS with Messages app
- Python 3.8+ with dependencies installed
- Access to Messages database (might require Full Disk Access permission)
"""

import sqlite3
import os
import time
import subprocess
import asyncio
import logging
import sys
from typing import Dict, List, Optional, Tuple
import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("imessage_agent.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("imessage_agent")

# Path to the Messages database
DB_PATH = os.path.expanduser("~/Library/Messages/chat.db")

# Import adaptive_chat components
# Add parent directory to Python path to import from adaptive_chat
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from adaptive_chat.src.agent import SeriesAIAgent

# Dictionary to store conversations by handle_id
conversations: Dict[str, Dict] = {}

class iMessageClient:
    """Client for sending iMessages via AppleScript."""
    
    @staticmethod
    def send_message(handle_id: str, text: str) -> bool:
        """
        Send an iMessage to the specified handle_id.
        
        Args:
            handle_id: Phone number or email
            text: Message to send
            
        Returns:
            True if successful, False otherwise
        """
        # Escape double quotes in the message to prevent AppleScript injection
        escaped_text = text.replace('"', '\\"')
        
        applescript = f'''
        tell application "Messages"
          set targetService to 1st service whose service type = iMessage
          set theBuddy to buddy "{handle_id}" of targetService
          send "{escaped_text}" to theBuddy
        end tell
        '''
        
        try:
            subprocess.run(["osascript", "-e", applescript], check=True)
            logger.info(f"Message sent to {handle_id}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to send message: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False

def query_new_greetings(last_rowid: int) -> List[Tuple[int, str, str]]:
    """
    Returns a list of tuples (msg_rowid, handle_id, full_text)
    for any new incoming iMessage whose text starts with our welcome prompt.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # look for any incoming (is_from_me=0) message matching our exact-prefix
    c.execute("""
        SELECT m.ROWID, h.id, m.text
          FROM message AS m
          JOIN handle  AS h ON m.handle_id = h.ROWID
         WHERE m.is_from_me = 0
           AND m.ROWID > ?
           AND m.text LIKE 'Welcome to Series! Text your color to get started:%'
         ORDER BY m.ROWID ASC
    """, (last_rowid,))
    rows = c.fetchall()
    conn.close()
    return rows

def query_new_messages(last_rowid: int, handle_id: Optional[str] = None) -> List[Tuple[int, str, str]]:
    """
    Returns a list of tuples (msg_rowid, handle_id, full_text)
    for any new incoming iMessage from the specified handle_id.
    If handle_id is None, returns messages from all handles.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if handle_id:
        # Get messages from a specific handle_id
        c.execute("""
            SELECT m.ROWID, h.id, m.text
              FROM message AS m
              JOIN handle  AS h ON m.handle_id = h.ROWID
             WHERE m.is_from_me = 0
               AND m.ROWID > ?
               AND h.id = ?
             ORDER BY m.ROWID ASC
        """, (last_rowid, handle_id))
    else:
        # Get messages from any handle
        c.execute("""
            SELECT m.ROWID, h.id, m.text
              FROM message AS m
              JOIN handle  AS h ON m.handle_id = h.ROWID
             WHERE m.is_from_me = 0
               AND m.ROWID > ?
             ORDER BY m.ROWID ASC
        """, (last_rowid,))
        
    rows = c.fetchall()
    conn.close()
    return rows

async def handle_new_conversations(agent: SeriesAIAgent) -> int:
    """
    Check for new conversations starting with the welcome message.
    Returns the highest message rowid processed.
    """
    global conversations
    last_rowid = max(conversation.get("last_rowid", 0) for conversation in conversations.values()) if conversations else 0
    
    # Look for new greeting messages
    new_greetings = query_new_greetings(last_rowid)
    
    for rowid, handle_id, text in new_greetings:
        last_rowid = max(last_rowid, rowid)
        logger.info(f"New conversation from {handle_id}: {text}")
        
        # Start a new conversation for this handle_id
        if handle_id not in conversations:
            conversations[handle_id] = {
                "started_at": datetime.datetime.now(),
                "last_rowid": rowid,
                "last_message_time": datetime.datetime.now()
            }
            
            # Generate welcome response using the agent
            welcome_response = await agent.process_message("START_ONBOARDING", handle_id)
            
            # Send the welcome response
            if iMessageClient.send_message(handle_id, welcome_response):
                logger.info(f"Sent welcome response to {handle_id}")
            else:
                logger.error(f"Failed to send welcome response to {handle_id}")
                
    return last_rowid

async def handle_ongoing_conversations(agent: SeriesAIAgent) -> int:
    """
    Process messages from ongoing conversations.
    Returns the highest message rowid processed.
    """
    global conversations
    last_rowid = max(conversation.get("last_rowid", 0) for conversation in conversations.values()) if conversations else 0
    
    # For each active conversation
    for handle_id, conversation in list(conversations.items()):
        # Check for new messages in this conversation
        conversation_last_rowid = conversation.get("last_rowid", 0)
        new_messages = query_new_messages(conversation_last_rowid, handle_id)
        
        for rowid, handle_id, text in new_messages:
            conversation["last_rowid"] = max(conversation.get("last_rowid", 0), rowid)
            last_rowid = max(last_rowid, rowid)
            conversation["last_message_time"] = datetime.datetime.now()
            
            logger.info(f"Message from {handle_id}: {text}")
            
            # Process the message with the agent
            response = await agent.process_message(text, handle_id)
            
            # Send the response
            if iMessageClient.send_message(handle_id, response):
                logger.info(f"Sent response to {handle_id}")
            else:
                logger.error(f"Failed to send response to {handle_id}")
                
    return last_rowid

async def cleanup_stale_conversations(max_age_hours: int = 24) -> None:
    """Remove conversations that have been inactive for more than max_age_hours."""
    global conversations
    current_time = datetime.datetime.now()
    
    stale_handles = []
    for handle_id, conversation in conversations.items():
        last_message_time = conversation.get("last_message_time", conversation.get("started_at"))
        age = (current_time - last_message_time).total_seconds() / 3600  # in hours
        
        if age > max_age_hours:
            stale_handles.append(handle_id)
            logger.info(f"Removing stale conversation with {handle_id} (inactive for {age:.1f} hours)")
    
    for handle_id in stale_handles:
        del conversations[handle_id]

async def main():
    """Main function to run the iMessage agent integration."""
    logger.info("Starting iMessage agent integration")
    
    # Initialize the agent
    agent = SeriesAIAgent()
    logger.info("Series AI Agent initialized")
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Get the saved conversations if available
    conversations_file = Path("data/conversations.txt")
    if conversations_file.exists():
        with open(conversations_file, "r") as f:
            for line in f:
                parts = line.strip().split(":")
                if len(parts) >= 2:
                    handle_id = parts[0]
                    rowid = int(parts[1])
                    conversations[handle_id] = {
                        "last_rowid": rowid,
                        "started_at": datetime.datetime.now(),
                        "last_message_time": datetime.datetime.now()
                    }
    
    last_rowid = 0
    poll_interval = 5  # seconds
    
    try:
        while True:
            # Handle new conversations
            new_conv_max_rowid = await handle_new_conversations(agent)
            last_rowid = max(last_rowid, new_conv_max_rowid)
            
            # Handle ongoing conversations
            ongoing_max_rowid = await handle_ongoing_conversations(agent)
            last_rowid = max(last_rowid, ongoing_max_rowid)
            
            # Cleanup stale conversations
            await cleanup_stale_conversations()
            
            # Save current conversations state
            with open(conversations_file, "w") as f:
                for handle_id, conversation in conversations.items():
                    f.write(f"{handle_id}:{conversation['last_rowid']}\n")
            
            # Wait before polling again
            await asyncio.sleep(poll_interval)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down")
    except Exception as e:
        logger.error(f"Error in main loop: {str(e)}", exc_info=True)
    finally:
        # Save conversations state before exiting
        with open(conversations_file, "w") as f:
            for handle_id, conversation in conversations.items():
                f.write(f"{handle_id}:{conversation['last_rowid']}\n")
        logger.info("iMessage agent integration shutdown complete")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 