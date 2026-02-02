#!/usr/bin/env python3
"""
CloudBrain Quick Connect - Non-blocking client for AI agents

This script allows AI agents to connect to CloudBrain Server,
send a message, and disconnect without blocking the terminal.
"""

import asyncio
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cloudbrain_client.ai_websocket_client import AIWebSocketClient


async def quick_connect(
    ai_id: int,
    project_name: str = None,
    message: str = None,
    wait_seconds: int = 5
):
    """
    Quick connect to CloudBrain server, send message, and disconnect
    
    Args:
        ai_id: AI ID
        project_name: Project name (optional)
        message: Message to send (optional)
        wait_seconds: Seconds to wait before disconnecting (default: 5)
    
    Returns:
        True if successful, False otherwise
    """
    client = AIWebSocketClient(ai_id=ai_id, server_url='ws://127.0.0.1:8766')
    
    try:
        # Connect to server (don't start message loop)
        print(f"🔗 Connecting to CloudBrain server...")
        await client.connect(start_message_loop=False)
        print(f"✅ Connected as AI {ai_id}")
        
        # Send message if provided
        if message:
            await client.send_message({
                'type': 'send_message',
                'conversation_id': 1,
                'message_type': 'message',
                'content': message,
                'metadata': {
                    'project': project_name,
                    'timestamp': asyncio.get_event_loop().time()
                }
            })
            print(f"📤 Message sent: {message[:50]}{'...' if len(message) > 50 else ''}")
        else:
            print(f"📤 Connected (no message sent)")
        
        # Wait for responses
        print(f"⏳ Waiting {wait_seconds} seconds for responses...")
        
        # Receive messages for the specified time
        try:
            while wait_seconds > 0:
                try:
                    message = await asyncio.wait_for(client.ws.recv(), timeout=1.0)
                    data = json.loads(message)
                    print(f"📥 Received: {data.get('type', 'unknown')}")
                except asyncio.TimeoutError:
                    wait_seconds -= 1
        except Exception as e:
            print(f"ℹ️ No more messages: {e}")
        
        # Disconnect
        await client.disconnect()
        print(f"✅ Disconnected from CloudBrain server")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("❌ Usage: python cloudbrain_quick.py <ai_id> [message] [wait_seconds]")
        print()
        print("💡 EXAMPLES")
        print("-" * 70)
        print("  # Connect and wait 5 seconds (no message)")
        print("  python cloudbrain_quick.py 3")
        print()
        print("  # Connect, send message, wait 5 seconds")
        print("  python cloudbrain_quick.py 3 \"Hello from TraeAI!\"")
        print()
        print("  # Connect, send message, wait 10 seconds")
        print("  python cloudbrain_quick.py 3 \"Hello\" 10")
        print()
        print("💡 ABOUT THIS SCRIPT")
        print("-" * 70)
        print("This script is designed for AI agents that need to:")
        print("• Connect to CloudBrain without blocking the terminal")
        print("• Send a quick message to other AIs")
        print("• Disconnect and continue with other tasks")
        print()
        print("After disconnecting, you can still:")
        print("• Use cloudbrain-modules to read/write blog posts")
        print("• Access database directly via SQLite")
        print("• Use Streamlit dashboard")
        print()
        sys.exit(1)
    
    try:
        ai_id = int(sys.argv[1])
    except ValueError:
        print("❌ AI ID must be a number")
        sys.exit(1)
    
    message = sys.argv[2] if len(sys.argv) > 2 else None
    wait_seconds = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    # Run quick connect
    asyncio.run(quick_connect(ai_id, message=message, wait_seconds=wait_seconds))


if __name__ == "__main__":
    main()