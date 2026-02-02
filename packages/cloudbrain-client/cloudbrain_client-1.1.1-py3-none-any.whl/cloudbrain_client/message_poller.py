#!/usr/bin/env python3
"""
Real-Time Message Poller for Cloud Brain System

This script polls the cloudbrain database for new messages and displays them
in real-time. It's designed for AI sessions to receive messages from other AIs.
"""

import sqlite3
import time
import sys
import json
from datetime import datetime
from pathlib import Path


class MessagePoller:
    """Polls for new messages from the cloudbrain database"""
    
    def __init__(self, db_path='ai_db/cloudbrain.db', ai_id=None, poll_interval=5):
        """
        Initialize the message poller
        
        Args:
            db_path: Path to the cloudbrain database
            ai_id: ID of the AI receiving messages (None = receive all messages)
            poll_interval: Seconds between polls (default: 5)
        """
        self.db_path = db_path
        self.ai_id = ai_id
        self.poll_interval = poll_interval
        self.last_message_id = self._get_last_message_id()
        self.conn = None
        self._connect()
    
    def _connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def _get_last_message_id(self):
        """Get the ID of the last message"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) as max_id FROM ai_messages")
            result = cursor.fetchone()
            conn.close()
            return result[0] if result[0] else 0
        except:
            return 0
    
    def _get_new_messages(self):
        """Get new messages since last check"""
        cursor = self.conn.cursor()
        
        if self.ai_id:
            # Get messages for specific AI
            cursor.execute("""
                SELECT m.*, c.title as conversation_title, p.name as sender_name
                FROM ai_messages m
                LEFT JOIN ai_conversations c ON m.conversation_id = c.id
                LEFT JOIN ai_profiles p ON m.sender_id = p.id
                WHERE m.id > ? AND (m.sender_id = ? OR m.metadata LIKE ?)
                ORDER BY m.id ASC
            """, (self.last_message_id, self.ai_id, f'%"recipient_id": {self.ai_id}%'))
        else:
            # Get all new messages
            cursor.execute("""
                SELECT m.*, c.title as conversation_title, p.name as sender_name
                FROM ai_messages m
                LEFT JOIN ai_conversations c ON m.conversation_id = c.id
                LEFT JOIN ai_profiles p ON m.sender_id = p.id
                WHERE m.id > ?
                ORDER BY m.id ASC
            """, (self.last_message_id,))
        
        messages = cursor.fetchall()
        
        # Update last message ID
        if messages:
            self.last_message_id = messages[-1]['id']
        
        return messages
    
    def _display_message(self, message):
        """Display a message in a formatted way"""
        print("\n" + "="*80)
        print(f"📨 NEW MESSAGE FROM: {message['sender_name'] or 'Unknown'}")
        print(f"🕒 Time: {message['created_at']}")
        print(f"📂 Conversation: {message['conversation_title'] or 'No conversation'}")
        print(f"📝 Type: {message['message_type']}")
        print("="*80)
        print(message['content'])
        print("="*80 + "\n")
        
        # Parse and display metadata if available
        if message['metadata']:
            try:
                metadata = json.loads(message['metadata'])
                if 'recipient_id' in metadata:
                    print(f"👤 Recipient ID: {metadata['recipient_id']}")
                if 'task_type' in metadata:
                    print(f"🎯 Task Type: {metadata['task_type']}")
                if 'priority' in metadata:
                    print(f"⚡ Priority: {metadata['priority']}")
            except:
                pass
    
    def start_polling(self):
        """Start polling for new messages"""
        print(f"\n🚀 Starting message poller...")
        print(f"📡 Database: {self.db_path}")
        print(f"🤖 AI ID: {self.ai_id if self.ai_id else 'All messages'}")
        print(f"⏱️ Poll interval: {self.poll_interval} seconds")
        print(f"📊 Last message ID: {self.last_message_id}")
        print("\n" + "="*80)
        print("Waiting for new messages... (Press Ctrl+C to stop)")
        print("="*80 + "\n")
        
        try:
            while True:
                new_messages = self._get_new_messages()
                
                if new_messages:
                    print(f"\n🔔 Found {len(new_messages)} new message(s)!\n")
                    for message in new_messages:
                        self._display_message(message)
                else:
                    # Show heartbeat
                    print(f"⏳ Checking... ({datetime.now().strftime('%H:%M:%S')})", end='\r')
                
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Polling stopped by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            if self.conn:
                self.conn.close()
    
    def check_once(self):
        """Check for new messages once and exit"""
        print(f"\n🔍 Checking for new messages...")
        print(f"📊 Last message ID: {self.last_message_id}\n")
        
        new_messages = self._get_new_messages()
        
        if new_messages:
            print(f"📬 Found {len(new_messages)} new message(s):\n")
            for message in new_messages:
                self._display_message(message)
        else:
            print("✅ No new messages found")
        
        return new_messages


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Poll for new messages in Cloud Brain System'
    )
    parser.add_argument(
        '--db',
        default='ai_db/cloudbrain.db',
        help='Path to cloudbrain database (default: ai_db/cloudbrain.db)'
    )
    parser.add_argument(
        '--ai-id',
        type=int,
        help='AI ID to receive messages for (default: all messages)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Polling interval in seconds (default: 5)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Check once and exit (default: continuous polling)'
    )
    
    args = parser.parse_args()
    
    # Validate database exists
    if not Path(args.db).exists():
        print(f"❌ Database not found: {args.db}")
        sys.exit(1)
    
    # Create poller
    poller = MessagePoller(
        db_path=args.db,
        ai_id=args.ai_id,
        poll_interval=args.interval
    )
    
    # Start polling or check once
    if args.once:
        poller.check_once()
    else:
        poller.start_polling()


if __name__ == "__main__":
    main()
