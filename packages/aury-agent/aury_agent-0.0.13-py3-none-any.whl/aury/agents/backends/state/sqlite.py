"""SQLite-based state backend for local persistence.

Provides persistent storage using SQLite database.
Ideal for local development and single-user applications.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class SQLiteStateBackend:
    """SQLite-based state backend.
    
    Stores all framework state in a single SQLite database file.
    Supports both key-value storage and message history.
    
    Tables:
    - state: namespace/key/value for general storage
    - messages: session_id/role/content for conversation history
    
    Example:
        backend = SQLiteStateBackend("./data/agent.db")
        
        # Key-value storage
        await backend.set("sessions", "sess_123", {"id": "sess_123"})
        data = await backend.get("sessions", "sess_123")
        
        # Message history
        await backend.add_message("sess_123", {"role": "user", "content": "Hello"})
        messages = await backend.get_messages("sess_123")
    """
    
    def __init__(self, db_path: str | Path = "./data/agent.db"):
        """Initialize SQLite backend.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS state (
                    namespace TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (namespace, key)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    namespace TEXT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    invocation_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session 
                ON messages(session_id, namespace)
            """)
            conn.commit()
        finally:
            conn.close()
    
    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ========== Key-Value Storage ==========
    
    async def get(self, namespace: str, key: str) -> Any | None:
        """Get value by key."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT value FROM state WHERE namespace = ? AND key = ?",
                (namespace, key)
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row["value"])
            return None
        finally:
            conn.close()
    
    async def set(self, namespace: str, key: str, value: Any) -> None:
        """Set value by key."""
        conn = self._get_conn()
        try:
            value_json = json.dumps(value, default=str, ensure_ascii=False)
            conn.execute("""
                INSERT INTO state (namespace, key, value, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(namespace, key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
            """, (namespace, key, value_json))
            conn.commit()
        finally:
            conn.close()
    
    async def delete(self, namespace: str, key: str) -> bool:
        """Delete value by key."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "DELETE FROM state WHERE namespace = ? AND key = ?",
                (namespace, key)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    async def list(self, namespace: str, prefix: str = "") -> list[str]:
        """List keys with optional prefix filter."""
        conn = self._get_conn()
        try:
            if prefix:
                cursor = conn.execute(
                    "SELECT key FROM state WHERE namespace = ? AND key LIKE ?",
                    (namespace, f"{prefix}%")
                )
            else:
                cursor = conn.execute(
                    "SELECT key FROM state WHERE namespace = ?",
                    (namespace,)
                )
            return [row["key"] for row in cursor.fetchall()]
        finally:
            conn.close()
    
    async def exists(self, namespace: str, key: str) -> bool:
        """Check if key exists."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT 1 FROM state WHERE namespace = ? AND key = ?",
                (namespace, key)
            )
            return cursor.fetchone() is not None
        finally:
            conn.close()
    
    # ========== Message Storage ==========
    
    async def add_message(
        self,
        session_id: str,
        message: dict[str, Any],
        namespace: str | None = None,
    ) -> None:
        """Add a message to session history.
        
        Args:
            session_id: Session ID
            message: Message dict with role, content, invocation_id
            namespace: Optional namespace for isolation
        """
        conn = self._get_conn()
        try:
            content = message.get("content", "")
            # Serialize list content (tool_use etc.)
            if isinstance(content, list):
                content = json.dumps(content, ensure_ascii=False)
            
            conn.execute("""
                INSERT INTO messages (session_id, namespace, role, content, invocation_id)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id,
                namespace,
                message.get("role", "user"),
                content,
                message.get("invocation_id"),
            ))
            conn.commit()
        finally:
            conn.close()
    
    async def get_messages(
        self,
        session_id: str,
        namespace: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get all messages for a session.
        
        Args:
            session_id: Session ID
            namespace: Optional namespace filter
            
        Returns:
            List of message dicts in chronological order
        """
        conn = self._get_conn()
        try:
            if namespace is None:
                cursor = conn.execute(
                    "SELECT role, content, invocation_id FROM messages WHERE session_id = ? AND namespace IS NULL ORDER BY id",
                    (session_id,)
                )
            else:
                cursor = conn.execute(
                    "SELECT role, content, invocation_id FROM messages WHERE session_id = ? AND namespace = ? ORDER BY id",
                    (session_id, namespace)
                )
            
            result = []
            for row in cursor.fetchall():
                content = row["content"]
                # Try to parse JSON content (may be tool_use etc.)
                if content and content.startswith("["):
                    try:
                        content = json.loads(content)
                    except json.JSONDecodeError:
                        pass
                
                result.append({
                    "role": row["role"],
                    "content": content,
                    "invocation_id": row["invocation_id"],
                })
            
            return result
        finally:
            conn.close()
    
    async def clear_messages(self, session_id: str) -> int:
        """Clear all messages for a session.
        
        Returns:
            Number of messages deleted
        """
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "DELETE FROM messages WHERE session_id = ?",
                (session_id,)
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()


__all__ = ["SQLiteStateBackend"]
