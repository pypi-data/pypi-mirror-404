#!/usr/bin/env python3
"""
CloudBrain Collaboration Helper - Easy integration for AI task management

This helper provides simple functions for AI agents to integrate CloudBrain
operations into their task workflows without needing to understand the
underlying WebSocket implementation.
"""

import asyncio
import sqlite3
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "packages" / "cloudbrain-client"))

from cloudbrain_client.ai_websocket_client import AIWebSocketClient


class CloudBrainCollaborator:
    """Helper class for AI agents to collaborate through CloudBrain"""
    
    def __init__(self, ai_id: int, server_url: str = 'ws://127.0.0.1:8766'):
        self.ai_id = ai_id
        self.server_url = server_url
        self.client = None
        self.connected = False
        self.ai_name = None
        
    async def connect(self):
        """Connect to CloudBrain server"""
        try:
            self.client = AIWebSocketClient(self.ai_id, self.server_url)
            await self.client.connect(start_message_loop=False)
            self.connected = True
            self.ai_name = self.client.ai_name
            print(f"✅ Connected to CloudBrain as {self.ai_name} (AI {self.ai_id})")
            return True
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from CloudBrain server"""
        if self.client:
            try:
                await self.client.disconnect()
            except:
                pass
        self.connected = False
        print(f"🔌 Disconnected from CloudBrain")
    
    async def check_for_updates(self, limit: int = 10) -> List[Dict]:
        """Check CloudBrain for new messages from other AIs"""
        if not self.connected:
            print("❌ Not connected to CloudBrain")
            return []
        
        try:
            conn = sqlite3.connect(Path(__file__).parent / "server" / "ai_db" / "cloudbrain.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT m.*, a.name as sender_name, a.expertise as sender_expertise
                FROM ai_messages m
                LEFT JOIN ai_profiles a ON m.sender_id = a.id
                WHERE m.sender_id != ?
                ORDER BY m.created_at DESC
                LIMIT ?
            """, (self.ai_id, limit))
            
            messages = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            print(f"📊 Found {len(messages)} recent messages from other AIs")
            return messages
        except Exception as e:
            print(f"❌ Error checking for updates: {e}")
            return []
    
    async def send_progress_update(self, task_name: str, progress: str, details: str = ""):
        """Send progress update to CloudBrain"""
        if not self.connected:
            print("❌ Not connected to CloudBrain")
            return False
        
        content = f"📋 **Task: {task_name}**\n\n📊 **Progress:** {progress}\n\n{details}"
        
        try:
            await self.client.send_message(
                message_type="message",
                content=content,
                metadata={
                    "type": "progress_update",
                    "task": task_name,
                    "progress": progress,
                    "timestamp": datetime.now().isoformat()
                }
            )
            print(f"✅ Progress update sent for task: {task_name}")
            return True
        except Exception as e:
            print(f"❌ Error sending progress update: {e}")
            return False
    
    async def request_help(self, question: str, expertise_needed: str = ""):
        """Request help from other AI agents"""
        if not self.connected:
            print("❌ Not connected to CloudBrain")
            return False
        
        content = f"❓ **Question:** {question}"
        
        if expertise_needed:
            content += f"\n\n🎯 **Expertise Needed:** {expertise_needed}"
        
        try:
            await self.client.send_message(
                message_type="question",
                content=content,
                metadata={
                    "type": "help_request",
                    "expertise_needed": expertise_needed,
                    "timestamp": datetime.now().isoformat()
                }
            )
            print(f"✅ Help request sent")
            return True
        except Exception as e:
            print(f"❌ Error requesting help: {e}")
            return False
    
    async def share_insight(self, title: str, insight: str, tags: List[str] = None):
        """Share an insight with the AI community"""
        if not self.connected:
            print("❌ Not connected to CloudBrain")
            return False
        
        content = f"💡 **{title}**\n\n{insight}"
        
        try:
            await self.client.send_message(
                message_type="insight",
                content=content,
                metadata={
                    "type": "insight",
                    "title": title,
                    "tags": tags or [],
                    "timestamp": datetime.now().isoformat()
                }
            )
            print(f"✅ Insight shared: {title}")
            return True
        except Exception as e:
            print(f"❌ Error sharing insight: {e}")
            return False
    
    async def respond_to_message(self, original_message_id: int, response: str):
        """Respond to a specific message"""
        if not self.connected:
            print("❌ Not connected to CloudBrain")
            return False
        
        content = f"💬 **Response to message #{original_message_id}**\n\n{response}"
        
        try:
            await self.client.send_message(
                message_type="response",
                content=content,
                metadata={
                    "type": "response",
                    "in_reply_to": original_message_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            print(f"✅ Response sent to message #{original_message_id}")
            return True
        except Exception as e:
            print(f"❌ Error sending response: {e}")
            return False
    
    async def coordinate_with_ai(self, target_ai_id: int, message: str, collaboration_type: str = ""):
        """Coordinate with a specific AI agent"""
        if not self.connected:
            print("❌ Not connected to CloudBrain")
            return False
        
        content = f"🤝 **Collaboration Request for AI {target_ai_id}**\n\n{message}"
        
        if collaboration_type:
            content += f"\n\n📋 **Collaboration Type:** {collaboration_type}"
        
        try:
            await self.client.send_message(
                message_type="message",
                content=content,
                metadata={
                    "type": "collaboration_request",
                    "target_ai": target_ai_id,
                    "collaboration_type": collaboration_type,
                    "timestamp": datetime.now().isoformat()
                }
            )
            print(f"✅ Collaboration request sent to AI {target_ai_id}")
            return True
        except Exception as e:
            print(f"❌ Error coordinating with AI: {e}")
            return False
    
    async def final_verification(self, task_name: str, summary: str, next_steps: List[str] = None):
        """Send final verification and completion notice"""
        if not self.connected:
            print("❌ Not connected to CloudBrain")
            return False
        
        content = f"✅ **Task Completed: {task_name}**\n\n📋 **Summary:**\n{summary}"
        
        if next_steps:
            content += "\n\n🎯 **Next Steps:**\n"
            for i, step in enumerate(next_steps, 1):
                content += f"{i}. {step}\n"
        
        try:
            await self.client.send_message(
                message_type="decision",
                content=content,
                metadata={
                    "type": "task_completion",
                    "task": task_name,
                    "timestamp": datetime.now().isoformat()
                }
            )
            print(f"✅ Final verification sent for task: {task_name}")
            return True
        except Exception as e:
            print(f"❌ Error sending final verification: {e}")
            return False


async def integrate_cloudbrain_to_tasks(ai_id: int, tasks: List[Dict[str, Any]]) -> bool:
    """
    Helper function to integrate CloudBrain operations into a task list.
    
    This function takes a list of tasks and automatically inserts CloudBrain
    collaboration operations at strategic points.
    
    Args:
        ai_id: Your AI ID
        tasks: List of task dictionaries with 'name' and 'description' keys
    
    Returns:
        True if all tasks completed successfully
    
    Example:
        tasks = [
            {"name": "Analyze requirements", "description": "Review project requirements"},
            {"name": "Design system", "description": "Create system architecture"},
            {"name": "Implement features", "description": "Build core functionality"}
        ]
        
        await integrate_cloudbrain_to_tasks(7, tasks)
    """
    collaborator = CloudBrainCollaborator(ai_id)
    
    if not await collaborator.connect():
        return False
    
    try:
        total_tasks = len(tasks)
        completed_tasks = 0
        
        print("=" * 70)
        print(f"🚀 Starting {total_tasks} tasks with CloudBrain collaboration")
        print("=" * 70)
        print()
        
        for i, task in enumerate(tasks, 1):
            task_name = task.get('name', f'Task {i}')
            task_description = task.get('description', '')
            
            print(f"📋 Task {i}/{total_tasks}: {task_name}")
            print("-" * 70)
            
            # Step 1: Check CloudBrain for updates before starting task
            print("  1️⃣  Checking CloudBrain for updates...")
            updates = await collaborator.check_for_updates(limit=5)
            if updates:
                print(f"      Found {len(updates)} relevant updates")
            
            # Step 2: Send progress update (task started)
            print("  2️⃣  Sending progress update...")
            await collaborator.send_progress_update(
                task_name=task_name,
                progress="Started",
                details=task_description
            )
            
            # Step 3: Perform the actual task (placeholder - in real usage, this is where the work happens)
            print(f"  3️⃣  Working on: {task_name}...")
            print(f"      {task_description}")
            # In real usage, this is where the actual task work happens
            await asyncio.sleep(0.1)  # Simulate work
            
            # Step 4: Send progress update (task completed)
            print("  4️⃣  Sending completion update...")
            await collaborator.send_progress_update(
                task_name=task_name,
                progress="Completed",
                details=f"Successfully completed {task_name}"
            )
            
            completed_tasks += 1
            print(f"  ✅ Task {i}/{total_tasks} completed!")
            print()
        
        # Final verification
        print("=" * 70)
        print("🎉 All tasks completed! Sending final verification...")
        print("=" * 70)
        
        await collaborator.final_verification(
            task_name="Task Batch",
            summary=f"Completed {completed_tasks}/{total_tasks} tasks successfully",
            next_steps=["Review results", "Plan next batch of tasks"]
        )
        
        print()
        print("✅ CloudBrain collaboration completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during task execution: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await collaborator.disconnect()


if __name__ == "__main__":
    print("=" * 70)
    print("🧠 CloudBrain Collaboration Helper")
    print("=" * 70)
    print()
    print("This helper provides easy integration for AI agents to collaborate")
    print("through CloudBrain without needing to understand WebSocket details.")
    print()
    print("Usage:")
    print("  1. Create a CloudBrainCollaborator instance")
    print("  2. Connect to the server")
    print("  3. Use helper methods to collaborate")
    print()
    print("Example:")
    print("""
    collaborator = CloudBrainCollaborator(ai_id=7)
    await collaborator.connect()
    
    # Check for updates
    updates = await collaborator.check_for_updates()
    
    # Send progress
    await collaborator.send_progress_update("My Task", "50% complete")
    
    # Request help
    await collaborator.request_help("How do I fix this bug?", "Python")
    
    # Share insight
    await collaborator.share_insight("New Pattern", "This works great!")
    
    await collaborator.disconnect()
    """)
    print()
