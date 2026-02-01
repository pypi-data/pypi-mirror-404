"""
CloudBrain Client - AI collaboration and communication system

This package provides a Python client for connecting to CloudBrain Server
for real-time AI collaboration and communication.
"""

__version__ = "1.0.0"

from .cloudbrain_client import CloudBrainClient
from .ai_websocket_client import AIWebSocketClient
from .message_poller import MessagePoller
from .ai_conversation_helper import AIConversationHelper

__all__ = [
    "CloudBrainClient",
    "AIWebSocketClient",
    "MessagePoller",
    "AIConversationHelper",
]


def main():
    """Main entry point for command-line usage"""
    import sys
    import asyncio
    
    if len(sys.argv) < 2:
        print("Usage: cloudbrain <ai_id> [project_name]")
        print("\nExamples:")
        print("  cloudbrain 2")
        print("  cloudbrain 2 cloudbrain")
        sys.exit(1)
    
    ai_id = int(sys.argv[1])
    project_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    async def run_client():
        client = CloudBrainClient(ai_id=ai_id, project_name=project_name)
        await client.run()
    
    asyncio.run(run_client())


if __name__ == "__main__":
    main()