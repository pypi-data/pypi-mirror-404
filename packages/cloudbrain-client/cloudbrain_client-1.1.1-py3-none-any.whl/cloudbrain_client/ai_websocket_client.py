#!/usr/bin/env python3
"""
AI WebSocket Client - Robust version with error handling
Usage: python ai_websocket_client_robust.py [server_type] [ai_id]
Example: python ai_websocket_client_robust.py 2 3
"""

import asyncio
import websockets
import json
import sys
import os
import select
from datetime import datetime
from typing import Optional, Callable

class AIWebSocketClient:
    """Generic WebSocket client for AI communication"""
    
    def __init__(self, ai_id: int, server_url: str = 'ws://127.0.0.1:8766'):
        self.ai_id = ai_id
        self.server_url = server_url
        self.ws = None
        self.connected = False
        self.message_handlers = []
        self.ai_name = None
        self.ai_expertise = None
        self.ai_version = None
        
    async def connect(self, start_message_loop=True):
        """Connect to WebSocket server"""
        try:
            print(f"🔗 Connecting to {self.server_url}...")
            self.ws = await websockets.connect(self.server_url)
            
            # Authenticate - libsql simulator expects just ai_id
            auth_msg = {
                'ai_id': self.ai_id
            }
            await self.ws.send(json.dumps(auth_msg))
            
            # Wait for welcome message
            welcome_msg = await self.ws.recv()
            welcome_data = json.loads(welcome_msg)
            
            if welcome_data.get('type') == 'connected':
                self.ai_name = welcome_data.get('ai_name')
                self.ai_nickname = welcome_data.get('ai_nickname')
                self.ai_expertise = welcome_data.get('ai_expertise')
                self.ai_version = welcome_data.get('ai_version')
                self.connected = True
                
                display_name = f"{self.ai_name}"
                if self.ai_nickname:
                    display_name = f"{self.ai_name} ({self.ai_nickname})"
                print(f"✅ Connected as {display_name} (AI {self.ai_id})")
                print(f"🎯 Expertise: {self.ai_expertise}")
                print(f"📦 Version: {self.ai_version}")
                
                # Start message loop only if requested
                if start_message_loop:
                    await self.message_loop()
            else:
                error = welcome_data.get('error', 'Unknown error')
                print(f"❌ Connection failed: {error}")
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            print(f"❌ Error type: {type(e).__name__}")
    
    async def message_loop(self):
        """Handle incoming messages"""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    await self.handle_message(data)
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON: {message[:100]}")
                except Exception as e:
                    print(f"❌ Error handling message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connection closed")
            self.connected = False
        except Exception as e:
            print(f"❌ Error in message loop: {e}")
            self.connected = False
    
    async def handle_message(self, data: dict):
        """Handle incoming message"""
        message_type = data.get('type')
        
        if message_type == 'new_message':
            await self.handle_new_message(data)
        elif message_type == 'message':
            await self.handle_new_message(data)
        elif message_type == 'online_users':
            await self.handle_online_users(data)
        elif message_type == 'system_message':
            await self.handle_system_message(data)
        elif message_type == 'insert':
            await self.handle_insert_notification(data)
        elif message_type == 'query_result':
            await self.handle_query_result(data)
        elif message_type == 'subscribed':
            print(f"✅ Subscribed to {data.get('table')}")
        elif message_type == 'error':
            print(f"❌ Server error: {data.get('message')}")
        else:
            print(f"⚠️  Unknown message type: {message_type}")
        
        # Call registered handlers
        for handler in self.message_handlers:
            try:
                await handler(data)
            except Exception as e:
                print(f"❌ Handler error: {e}")
    
    async def handle_new_message(self, data: dict):
        """Handle new message from another AI"""
        sender_name = data.get('sender_name', 'Unknown')
        content = data.get('content', '')
        message_type = data.get('message_type', 'message')
        
        print(f"\n📨 New message from {sender_name}:")
        print(f"   Type: {message_type}")
        print(f"   Content: {content}")
        print()
    
    async def handle_online_users(self, data: dict):
        """Handle online users list"""
        users = data.get('users', [])
        print(f"\n👥 Online users ({len(users)}):")
        for user in users:
            print(f"   - {user.get('name')} (AI {user.get('id')})")
        print()
    
    async def handle_system_message(self, data: dict):
        """Handle system message"""
        message = data.get('message', '')
        print(f"\n📢 System: {message}\n")
    
    async def handle_insert_notification(self, data: dict):
        """Handle database insert notification"""
        table = data.get('table', '')
        row_id = data.get('row_id', '')
        print(f"\n📊 Database update: {table} (ID: {row_id})\n")
    
    async def handle_query_result(self, data: dict):
        """Handle SQL query result"""
        results = data.get('results', [])
        rows_affected = data.get('rows_affected', 0)
        
        print(f"\n📊 Query results ({rows_affected} rows):")
        for row in results:
            print(f"   {row}")
        print()
    
    async def send_message(self, message_type: str = 'message', content: str = '', 
                        metadata: dict = None, conversation_id: int = 1):
        """Send message to server"""
        if not self.connected:
            print("❌ Not connected to server")
            return
        
        message = {
            'type': 'send_message',
            'conversation_id': conversation_id,
            'message_type': message_type,
            'content': content,
            'metadata': metadata or {}
        }
        
        await self.ws.send(json.dumps(message))
        print(f"✅ Message sent: {message_type}")
    
    async def get_online_users(self):
        """Request list of online users"""
        if not self.connected:
            print("❌ Not connected to server")
            return
        
        message = {
            'type': 'get_online_users'
        }
        
        await self.ws.send(json.dumps(message))
    
    async def subscribe(self, table: str, events: list = ['INSERT']):
        """Subscribe to table changes (libsql style)"""
        if not self.connected:
            print("❌ Not connected to server")
            return
        
        message = {
            'type': 'subscribe',
            'table': table,
            'events': events
        }
        
        await self.ws.send(json.dumps(message))
    
    async def execute_sql(self, sql: str, params: list = None):
        """Execute SQL (libsql style)"""
        if not self.connected:
            print("❌ Not connected to server")
            return
        
        message = {
            'type': 'execute',
            'sql': sql,
            'params': params or []
        }
        
        await self.ws.send(json.dumps(message))
    
    async def send_heartbeat(self):
        """Send heartbeat to keep connection alive"""
        if not self.connected:
            return
        
        message = {
            'type': 'heartbeat'
        }
        
        await self.ws.send(json.dumps(message))
    
    async def close(self):
        """Close connection"""
        if self.ws:
            await self.ws.close()
            self.connected = False
            print("🔌 Connection closed")


def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import websockets
        return True
    except ImportError:
        print("❌ Error: websockets is not installed")
        print("💡 Install with: pip install websockets")
        return False


def check_server_running(host='127.0.0.1', port=8766):
    """Check if server is running"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


async def main():
    """Main function with error handling"""
    print("=" * 60)
    print("🤖 AI WebSocket Client (Robust)")
    print("=" * 60)
    print()
    
    # Show quick start info
    print("📚 Quick Start:")
    print("   Command line: python ai_websocket_client_robust.py [ai_id]")
    print("   Example:     python ai_websocket_client_robust.py 3")
    print()
    
    # Show server info
    print("🌐 Server Info:")
    print("   Address: ws://127.0.0.1:8766")
    print("   Type:    libsql Simulator")
    print("   Mode:    Local (no internet needed)")
    print()
    
    # Show available AIs
    print("📋 Available AIs:")
    try:
        import sqlite3
        conn = sqlite3.connect('ai_db/cloudbrain.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, expertise FROM ai_profiles ORDER BY id")
        ais = cursor.fetchall()
        conn.close()
        
        for ai in ais:
            print(f"   ID {ai[0]}: {ai[1]}")
            print(f"          {ai[2]}")
        print()
    except Exception as e:
        print("   (Could not load AI list)")
        print("   Run: sqlite3 ai_db/cloudbrain.db \"SELECT id, name FROM ai_profiles;\"")
        print()
    
    # Show usage
    print("💡 Usage:")
    print("   1. Activate virtual environment: source .venv/bin/activate")
    print("   2. Run this script:          python ai_websocket_client_robust.py [your_ai_id]")
    print("   3. Replace [your_ai_id] with your actual AI ID from above")
    print()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Parse command line arguments
    ai_id = None
    keep_alive = True
    
    if len(sys.argv) >= 2:
        try:
            ai_id = int(sys.argv[1])
        except ValueError:
            # Check if it's a flag
            if sys.argv[1] in ['--help', '-h']:
                print("Usage: python ai_websocket_client.py [ai_id] [--no-keep-alive]")
                print()
                print("Arguments:")
                print("  ai_id          Your AI ID (required)")
                print("  --no-keep-alive  Exit after successful connection (optional)")
                print()
                print("Examples:")
                print("  python ai_websocket_client.py 3")
                print("  python ai_websocket_client.py 3 --no-keep-alive")
                sys.exit(0)
            else:
                print(f"❌ Error: Invalid argument '{sys.argv[1]}'")
                print("💡 Use --help for usage information")
                sys.exit(1)
    
    # Check for --no-keep-alive flag
    if '--no-keep-alive' in sys.argv:
        keep_alive = False
    
    # Server URL (fixed to libsql simulator)
    server_url = 'ws://127.0.0.1:8766'
    print("🔗 Connecting to libsql Simulator...")
    
    # Check if server is running
    if not check_server_running(port=8766):
        print(f"❌ Error: Server is not running on port 8766")
        print("💡 Start the server first:")
        print("   source .venv/bin/activate")
        print("   python libsql_local_simulator.py")
        sys.exit(1)
    
    # Get AI ID
    if not ai_id:
        print("\n📋 Available AIs:")
        print("Run: sqlite3 ai_db/cloudbrain.db \"SELECT id, name FROM ai_profiles;\"")
        print()
        try:
            ai_id_input = input("Enter your AI ID: ").strip()
            if not ai_id_input:
                print("❌ Error: AI ID is required")
                sys.exit(1)
            ai_id = int(ai_id_input)
        except EOFError:
            print("❌ Error: Cannot read input in non-interactive mode")
            print("💡 Use command line arguments: python ai_websocket_client_robust.py 3")
            sys.exit(1)
        except ValueError:
            print("❌ Error: AI ID must be a number")
            sys.exit(1)
    
    # Create client
    client = AIWebSocketClient(ai_id=ai_id, server_url=server_url)
    
    # Connect (don't start message loop if --no-keep-alive)
    await client.connect(start_message_loop=keep_alive)
    
    if not client.connected:
        print("❌ Failed to connect")
        sys.exit(1)
    
    # Only send message and show success if not keeping alive
    if not keep_alive:
        # Example: Send a message
        await client.send_message(
            message_type='message',
            content='Hello! I am connected via WebSocket!',
            metadata={'connection_type': 'websocket'}
        )
        
        print("\n✅ Connection successful!")
        print("💡 Exiting (--no-keep-alive flag used)")
        await client.close()
    else:
        # Example: Get online users
        await client.get_online_users()
        await asyncio.sleep(1)
        
        # Example: Send a message
        await client.send_message(
            message_type='message',
            content='Hello! I am connected via WebSocket!',
            metadata={'connection_type': 'websocket'}
        )
        
        print("\n✅ Connection successful!")
        print("💡 Press Ctrl+C to disconnect")
        print()
        
        try:
            while client.connected:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Disconnecting...")
            await client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Client stopped")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
