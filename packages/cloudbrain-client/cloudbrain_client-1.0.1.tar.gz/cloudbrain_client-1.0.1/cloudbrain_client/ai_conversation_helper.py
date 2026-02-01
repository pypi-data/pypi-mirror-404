#!/usr/bin/env python3

import sqlite3
import json
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union

try:
    import psycopg2  # PostgreSQL adapter
    from psycopg2.extras import RealDictCursor
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False


class DatabaseAdapter:
    """
    数据库适配器，支持SQLite和PostgreSQL/Cloud SQL
    """
    def __init__(self, db_type: str = "sqlite", connection_string: str = None):
        self.db_type = db_type.lower()
        self.connection_string = connection_string
        
        if self.db_type == "postgresql" and not HAS_POSTGRES:
            raise ImportError("psycopg2 is required for PostgreSQL support. Install with: pip install psycopg2-binary")
    
    def get_connection(self):
        """获取数据库连接"""
        if self.db_type == "sqlite":
            # NOTE: ai_memory.db is deprecated. Use cloudbrain.db instead.
            # Historical reference: ai_memory.db was used in early days (2026-01)
            # All content migrated to cloudbrain.db on 2026-02-01
            conn = sqlite3.connect(self.connection_string or "ai_db/cloudbrain.db")
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            return conn
        elif self.db_type == "postgresql":
            import psycopg2
            from psycopg2.extras import RealDictCursor
            # connection_string should be in format: "host=localhost dbname=mydb user=user password=password"
            conn = psycopg2.connect(self.connection_string, cursor_factory=RealDictCursor)
            return conn
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    def execute(self, sql: str, params: tuple = None) -> int:
        """执行写操作并返回最后插入的ID"""
        with self.get_connection() as conn:
            if self.db_type == "postgresql":
                # PostgreSQL uses %s for parameter placeholders
                sql = sql.replace("?", "%s")
            
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            conn.commit()
            
            last_id = cursor.lastrowid
            cursor.close()
            return last_id if last_id is not None else cursor.rowcount
    
    def query(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """执行查询操作"""
        with self.get_connection() as conn:
            if self.db_type == "postgresql":
                # PostgreSQL uses %s for parameter placeholders
                sql = sql.replace("?", "%s")
            
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            results = cursor.fetchall()
            cursor.close()
            
            # Convert results to list of dicts
            if self.db_type == "sqlite":
                return [self._serialize_row(row) for row in results]
            else:  # PostgreSQL
                return [dict(row) for row in results]
    
    def _serialize_row(self, row: Union[sqlite3.Row, dict]) -> Dict[str, Any]:
        """将数据库行转换为可JSON序列化的字典"""
        result = {}
        if isinstance(row, sqlite3.Row):
            for key in row.keys():
                value = row[key]
                if isinstance(value, bytes):
                    result[key] = value.decode('utf-8', errors='ignore')
                else:
                    result[key] = value
        else:
            # For PostgreSQL rows already converted to dict
            for key, value in row.items():
                if isinstance(value, bytes):
                    result[key] = value.decode('utf-8', errors='ignore')
                else:
                    result[key] = value
        return result


class AIConversationHelper:
    def __init__(self, db_adapter: DatabaseAdapter = None):
        # NOTE: ai_memory.db is deprecated. Use cloudbrain.db instead.
        # Historical reference: ai_memory.db was used in early days (2026-01)
        # All content migrated to cloudbrain.db on 2026-02-01
        self.db_adapter = db_adapter or DatabaseAdapter(db_type="sqlite", connection_string="ai_db/cloudbrain.db")
    
    def query(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        return self.db_adapter.query(sql, params)
    
    def execute(self, sql: str, params: tuple = None) -> int:
        return self.db_adapter.execute(sql, params)
    
    def _parse_json(self, json_str: str) -> Any:
        try:
            return json.loads(json_str) if json_str else None
        except:
            return json_str
    
    def _to_json(self, obj) -> str:
        """将对象转换为JSON字符串"""
        if obj is None:
            return None
        return json.dumps(obj, ensure_ascii=False)
    
    def send_notification(self, sender_id: int, title: str, content: str, 
                         notification_type: str = "general", 
                         priority: str = "normal",
                         recipient_id: int = None,
                         context: str = None,
                         related_conversation_id: int = None,
                         related_document_path: str = None,
                         expires_hours: int = None) -> int:
        """发送通知给指定AI或所有AI"""
        expires_at = None
        if expires_hours:
            expires_at = (datetime.now() + timedelta(hours=expires_hours)).isoformat()

        sql = """
        INSERT INTO ai_notifications 
        (sender_id, recipient_id, notification_type, priority, title, content, context, 
         related_conversation_id, related_document_path, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (sender_id, recipient_id, notification_type, priority, title, content,
                  context, related_conversation_id, related_document_path, expires_at)
        return self.execute(sql, params)

    def get_notifications(self, recipient_id: int = None, unread_only: bool = False, 
                        notification_type: str = None, priority: str = None) -> List[Dict]:
        """获取通知"""
        sql = """
        SELECT n.*, 
               sender.ai_name as sender_name,
               recipient.ai_name as recipient_name
        FROM ai_notifications n
        LEFT JOIN ai_profiles sender ON n.sender_id = sender.id
        LEFT JOIN ai_profiles recipient ON n.recipient_id = recipient.id
        WHERE 1=1
        """
        params = []

        if recipient_id:
            sql += " AND (n.recipient_id = ? OR n.recipient_id IS NULL)"
            params.append(recipient_id)
        if unread_only:
            sql += " AND n.is_read = 0"
        if notification_type:
            sql += " AND n.notification_type = ?"
            params.append(notification_type)
        if priority:
            sql += " AND n.priority = ?"
            params.append(priority)

        sql += " ORDER BY n.priority DESC, n.created_at DESC"
        return self.query(sql, tuple(params))

    def mark_notification_as_read(self, notification_id: int) -> bool:
        """标记通知为已读"""
        sql = "UPDATE ai_notifications SET is_read = 1 WHERE id = ?"
        result = self.execute(sql, (notification_id,))
        return result != -1

    def mark_notification_as_acknowledged(self, notification_id: int) -> bool:
        """标记通知为已确认"""
        sql = "UPDATE ai_notifications SET is_acknowledged = 1 WHERE id = ?"
        result = self.execute(sql, (notification_id,))
        return result != -1

    def get_unread_notifications_count(self, recipient_id: int = None) -> int:
        """获取未读通知数量"""
        sql = "SELECT COUNT(*) as count FROM ai_notifications WHERE is_read = 0"
        params = []
        if recipient_id:
            sql += " AND (recipient_id = ? OR recipient_id IS NULL)"
            params.append(recipient_id)
        result = self.query(sql, tuple(params))
        return result[0]['count'] if result and 'count' in result[0] else 0

    def subscribe_to_notification_type(self, ai_profile_id: int, notification_type: str) -> bool:
        """订阅特定类型的通知"""
        sql = """
        INSERT OR REPLACE INTO ai_notification_subscriptions 
        (ai_profile_id, notification_type, active) 
        VALUES (?, ?, 1)
        """
        result = self.execute(sql, (ai_profile_id, notification_type))
        return result != -1

    def unsubscribe_from_notification_type(self, ai_profile_id: int, notification_type: str) -> bool:
        """取消订阅特定类型的通知"""
        sql = """
        UPDATE ai_notification_subscriptions 
        SET active = 0 
        WHERE ai_profile_id = ? AND notification_type = ?
        """
        result = self.execute(sql, (ai_profile_id, notification_type))
        return result != -1

    def get_notification_stats(self) -> List[Dict]:
        """获取通知统计信息"""
        sql = "SELECT * FROM ai_notification_stats"
        return self.query(sql)

    def get_unread_notifications_view(self) -> List[Dict]:
        """获取未读通知视图"""
        sql = "SELECT * FROM ai_unread_notifications"
        return self.query(sql)
    
    def get_conversations(self, status: str = None, category: str = None) -> List[Dict]:
        """获取对话列表"""
        sql = """
        SELECT c.*, ap.ai_name as creator_name,
               (SELECT COUNT(*) FROM ai_conversation_participants p WHERE p.conversation_id = c.id) as participant_count,
               (SELECT content FROM ai_messages m WHERE m.conversation_id = c.id ORDER BY m.created_at DESC LIMIT 1) as last_message
        FROM ai_conversations c
        LEFT JOIN ai_profiles ap ON c.created_by = ap.id
        WHERE 1=1
        """
        params = []
        if status:
            sql += " AND c.status = ?"
            params.append(status)
        if category:
            sql += " AND c.category = ?"
            params.append(category)
        sql += " ORDER BY c.created_at DESC"
        return self.query(sql, tuple(params))

    def get_messages(self, conversation_id: int) -> List[Dict]:
        """获取对话消息"""
        sql = """
        SELECT m.*, 
               sender.ai_name as sender_name,
               recipient.ai_name as recipient_name
        FROM ai_messages m
        LEFT JOIN ai_profiles sender ON m.sender_id = sender.id
        LEFT JOIN ai_profiles recipient ON m.recipient_id = recipient.id
        WHERE m.conversation_id = ?
        ORDER BY m.created_at ASC
        """
        return self.query(sql, (conversation_id,))

    def leave_note_for_next_session(self, sender_id: int, note_type: str, title: str, content: str,
                                   priority: str = "normal", recipient_id: int = None,
                                   context: str = None, related_files: List[str] = None,
                                   related_tasks: List[str] = None, expected_actions: str = None,
                                   expires_hours: int = None) -> int:
        """留给下一位AI的留言"""
        expires_at = None
        if expires_hours:
            from datetime import timedelta
            expires_at = (datetime.now() + timedelta(hours=expires_hours)).isoformat()

        sql = """
        INSERT INTO ai_next_session_notes (sender_id, recipient_id, note_type, priority, title, content, context, related_files, related_tasks, expected_actions, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute(sql, (sender_id, recipient_id, note_type, priority, title, content, context,
                                  self._to_json(related_files), self._to_json(related_tasks),
                                  expected_actions, expires_at))

    def get_notes_for_next_session(self, recipient_id: int = None, note_type: str = None, 
                                  unread_only: bool = True) -> List[Dict]:
        """获取留给下一位AI的留言"""
        sql = """
        SELECT n.*, 
               sender.ai_name as sender_name,
               recipient.ai_name as recipient_name
        FROM ai_next_session_notes n
        LEFT JOIN ai_profiles sender ON n.sender_id = sender.id
        LEFT JOIN ai_profiles recipient ON n.recipient_id = recipient.id
        WHERE 1=1
        """
        params = []
        if recipient_id:
            sql += " AND (n.recipient_id = ? OR n.recipient_id IS NULL)"
            params.append(recipient_id)
        if note_type:
            sql += " AND n.note_type = ?"
            params.append(note_type)
        if unread_only:
            sql += " AND n.is_actioned = 0"
        sql += " ORDER BY n.priority DESC, n.created_at DESC"
        return self.query(sql, tuple(params))

    def respond_to_previous_session(self, sender_id: int, original_note_id: int, response_type: str,
                                   content: str, actions_taken: str = None, results: str = None) -> int:
        """回应上一位AI的留言"""
        sql = """
        INSERT INTO ai_previous_session_responses (sender_id, original_note_id, response_type, content, actions_taken, results)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        return self.execute(sql, (sender_id, original_note_id, response_type, content, actions_taken, results))

    def get_insights(self, ai_id: int = None, insight_type: str = None) -> List[Dict]:
        """获取见解"""
        sql = """
        SELECT i.*, 
               ap.ai_name as ai_name
        FROM ai_insights i
        LEFT JOIN ai_profiles ap ON i.ai_id = ap.id
        WHERE 1=1
        """
        params = []
        if ai_id:
            sql += " AND i.ai_id = ?"
            params.append(ai_id)
        if insight_type:
            sql += " AND i.insight_type = ?"
            params.append(insight_type)
        sql += " ORDER BY i.created_at DESC"
        return self.query(sql, tuple(params))


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 ai_conversation_helper.py <command> [args...]")
        print("\nCommands:")
        print("  profile <ai_name> [version] [expertise] - Get AI profile")
        print("  conversations [status] [category] - List conversations")
        print("  messages <conversation_id> - Get messages for conversation")
        print("  note <sender_id> <note_type> <title> <content> - Leave note for next session")
        print("  notes [recipient_id] - Get notes for next session")
        print("  respond <sender_id> <note_id> <response_type> <content> - Respond to previous session")
        print("  insights [ai_id] [insight_type] - Get insights")
        print("  stats - Get statistics")
        print("  notify <sender_id> <title> <content> [type] [priority] [recipient_id] - Send notification")
        print("  notifications [recipient_id] [unread_only] - Get notifications")
        print("  notification_stats - Get notification statistics")
        print("  unread_notifications [recipient_id] - Get unread notifications")
        print("  mark_read <notification_id> - Mark notification as read")
        print("  subscribe <ai_profile_id> <notification_type> - Subscribe to notification type")
        sys.exit(1)

    # Check if we're connecting to PostgreSQL
    db_type = "postgresql" if "PGHOST" in os.environ else "sqlite"
    connection_string = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_CONNECTION_STRING")
    
    if db_type == "postgresql" and connection_string:
        db_adapter = DatabaseAdapter(db_type=db_type, connection_string=connection_string)
    else:
        # NOTE: ai_memory.db is deprecated. Use cloudbrain.db instead.
        # Historical reference: ai_memory.db was used in early days (2026-01)
        # All content migrated to cloudbrain.db on 2026-02-01
        # Use relative path to ai_db folder
        db_path = os.path.join(os.path.dirname(__file__), "ai_db/cloudbrain.db")
        db_adapter = DatabaseAdapter(db_type="sqlite", connection_string=db_path)
    
    helper = AIConversationHelper(db_adapter)
    command = sys.argv[1]

    if command == "profile":
        ai_name = sys.argv[2] if len(sys.argv) > 2 else None
        if ai_name:
            # Query for specific AI profile
            sql = "SELECT * FROM ai_profiles WHERE ai_name = ?"
            result = helper.query(sql, (ai_name,))
        else:
            # Get all AI profiles
            sql = "SELECT * FROM ai_profiles ORDER BY id"
            result = helper.query(sql)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif command == "conversations":
        status = sys.argv[2] if len(sys.argv) > 2 else None
        category = sys.argv[3] if len(sys.argv) > 3 else None
        result = helper.get_conversations(status=status, category=category)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif command == "messages":
        if len(sys.argv) < 3:
            print("Usage: messages <conversation_id>")
            sys.exit(1)
        conversation_id = int(sys.argv[2])
        result = helper.get_messages(conversation_id=conversation_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif command == "note":
        if len(sys.argv) < 5:
            print("Usage: note <sender_id> <note_type> <title> <content> [priority] [recipient_id]")
            sys.exit(1)
        sender_id = int(sys.argv[2])
        note_type = sys.argv[3]
        title = sys.argv[4]
        content = sys.argv[5] if len(sys.argv) > 5 else ""
        priority = sys.argv[6] if len(sys.argv) > 6 else "normal"
        recipient_id = int(sys.argv[7]) if len(sys.argv) > 7 else None
        
        result = helper.leave_note_for_next_session(sender_id, note_type, title, content, priority, recipient_id)
        print(json.dumps({"id": result}, indent=2))

    elif command == "notes":
        recipient_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
        result = helper.get_notes_for_next_session(recipient_id=recipient_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif command == "respond":
        if len(sys.argv) < 5:
            print("Usage: respond <sender_id> <original_note_id> <response_type> <content>")
            sys.exit(1)
        sender_id = int(sys.argv[2])
        original_note_id = int(sys.argv[3])
        response_type = sys.argv[4]
        content = sys.argv[5] if len(sys.argv) > 5 else ""
        
        result = helper.respond_to_previous_session(sender_id, original_note_id, response_type, content)
        print(json.dumps({"id": result}, indent=2))

    elif command == "insights":
        ai_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
        insight_type = sys.argv[3] if len(sys.argv) > 3 else None
        result = helper.get_insights(ai_id=ai_id, insight_type=insight_type)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif command == "stats":
        # Get stats from all relevant tables
        stats = {
            "ai_profiles": len(helper.query("SELECT id FROM ai_profiles")),
            "conversations": len(helper.query("SELECT id FROM ai_conversations")),
            "messages": len(helper.query("SELECT id FROM ai_messages")),
            "notes": len(helper.query("SELECT id FROM ai_next_session_notes")),
            "responses": len(helper.query("SELECT id FROM ai_previous_session_responses")),
            "insights": len(helper.query("SELECT id FROM ai_insights")),
            "notifications": len(helper.query("SELECT id FROM ai_notifications")),
            "unread_notifications": len(helper.query("SELECT id FROM ai_notifications WHERE is_read = 0")),
            "collaborations": len(helper.query("SELECT id FROM ai_collaborations"))
        }
        print(json.dumps(stats, indent=2))

    elif command == "notify":
        if len(sys.argv) < 5:
            print("Usage: notify <sender_id> <title> <content> [type] [priority] [recipient_id]")
            sys.exit(1)
        sender_id = int(sys.argv[2])
        title = sys.argv[3]
        content = sys.argv[4]
        notification_type = sys.argv[5] if len(sys.argv) > 5 else "general"
        priority = sys.argv[6] if len(sys.argv) > 6 else "normal"
        recipient_id = int(sys.argv[7]) if len(sys.argv) > 7 else None
        
        result = helper.send_notification(sender_id, title, content, notification_type, priority, recipient_id)
        print(json.dumps({"id": result}, indent=2))

    elif command == "notifications":
        recipient_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
        unread_only = sys.argv[3].lower() == 'true' if len(sys.argv) > 3 else False
        result = helper.get_notifications(recipient_id, unread_only)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif command == "notification_stats":
        result = helper.get_notification_stats()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif command == "unread_notifications":
        recipient_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
        result = helper.get_unread_notifications_view()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif command == "mark_read":
        if len(sys.argv) < 3:
            print("Usage: mark_read <notification_id>")
            sys.exit(1)
        notification_id = int(sys.argv[2])
        result = helper.mark_notification_as_read(notification_id)
        print(json.dumps({"success": result}, indent=2))

    elif command == "subscribe":
        if len(sys.argv) < 4:
            print("Usage: subscribe <ai_profile_id> <notification_type>")
            sys.exit(1)
        ai_profile_id = int(sys.argv[2])
        notification_type = sys.argv[3]
        result = helper.subscribe_to_notification_type(ai_profile_id, notification_type)
        print(json.dumps({"success": result}, indent=2))

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    import os
    main()