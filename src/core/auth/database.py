#!/usr/bin/env python3
"""
AI CodeScan - Database Manager for Authentication

Quản lý database SQLite cho user authentication và session storage.
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from loguru import logger


@dataclass
class DatabaseConfig:
    """Database configuration."""
    db_path: str = "data/ai_codescan.db"
    timeout: float = 30.0
    enable_foreign_keys: bool = True


class DatabaseManager:
    """
    Database manager cho authentication system.
    
    Manages SQLite database cho user accounts, sessions, và related data.
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize database manager.
        
        Args:
            config: Database configuration
        """
        self.config = config or DatabaseConfig()
        self.db_path = Path(self.config.db_path)
        
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Database manager initialized: {self.db_path}")
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get database connection.
        
        Returns:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=self.config.timeout,
            check_same_thread=False
        )
        
        # Enable foreign keys
        if self.config.enable_foreign_keys:
            conn.execute("PRAGMA foreign_keys = ON")
        
        # Set row factory to return dict-like objects
        conn.row_factory = sqlite3.Row
        
        return conn
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[sqlite3.Row]:
        """
        Execute SELECT query và return results.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            List[sqlite3.Row]: Query results
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Execute INSERT/UPDATE/DELETE query.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            int: Number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.rowcount
    
    def execute_insert(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Execute INSERT query và return last row ID.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            int: Last inserted row ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.lastrowid
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if table exists.
        
        Args:
            table_name: Name of table to check
            
        Returns:
            bool: True if table exists
        """
        query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
        """
        result = self.execute_query(query, (table_name,))
        return len(result) > 0


def init_auth_database(db_path: str = "data/ai_codescan.db") -> DatabaseManager:
    """
    Initialize authentication database with required tables.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        DatabaseManager: Initialized database manager
    """
    config = DatabaseConfig(db_path=db_path)
    db_manager = DatabaseManager(config)
    
    # Create tables
    create_tables(db_manager)
    
    logger.info("Authentication database initialized successfully")
    return db_manager


def create_tables(db_manager: DatabaseManager) -> None:
    """
    Create required tables cho authentication system.
    
    Args:
        db_manager: Database manager instance
    """
    # Users table
    users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        is_active BOOLEAN NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login_at TIMESTAMP,
        profile_data TEXT,  -- JSON string for additional profile data
        preferences TEXT    -- JSON string for user preferences
    )
    """
    
    # Sessions table (cho authentication sessions)
    auth_sessions_table = """
    CREATE TABLE IF NOT EXISTS auth_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_token TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT,
        user_agent TEXT,
        is_active BOOLEAN NOT NULL DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    """
    
    # User sessions table (cho scan/chat sessions)
    user_sessions_table = """
    CREATE TABLE IF NOT EXISTS user_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        session_type TEXT NOT NULL,  -- repository_analysis, pr_review, code_qna
        status TEXT NOT NULL DEFAULT 'in_progress',
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        metadata TEXT,  -- JSON string for additional metadata
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    """
    
    # Scan results table
    scan_results_table = """
    CREATE TABLE IF NOT EXISTS scan_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        repository_url TEXT,
        repository_name TEXT,
        analysis_type TEXT NOT NULL,
        findings_count INTEGER DEFAULT 0,
        severity_breakdown TEXT,  -- JSON string
        summary TEXT,
        detailed_results TEXT,   -- JSON string
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (session_id) REFERENCES user_sessions (session_id) ON DELETE CASCADE
    )
    """
    
    # Chat messages table
    chat_messages_table = """
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        role TEXT NOT NULL,  -- user, assistant
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        metadata TEXT,  -- JSON string for additional metadata
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (session_id) REFERENCES user_sessions (session_id) ON DELETE CASCADE
    )
    """
    
    # Create all tables
    tables = [
        users_table,
        auth_sessions_table,
        user_sessions_table,
        scan_results_table,
        chat_messages_table
    ]
    
    for table_sql in tables:
        db_manager.execute_update(table_sql)
    
    # Create indexes
    create_indexes(db_manager)
    
    logger.info("All authentication tables created successfully")


def create_indexes(db_manager: DatabaseManager) -> None:
    """
    Create indexes for better query performance.
    
    Args:
        db_manager: Database manager instance
    """
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)",
        "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users (is_active)",
        "CREATE INDEX IF NOT EXISTS idx_auth_sessions_token ON auth_sessions (session_token)",
        "CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON auth_sessions (user_id)",
        "CREATE INDEX IF NOT EXISTS idx_auth_sessions_expires ON auth_sessions (expires_at)",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions (user_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_type ON user_sessions (session_type)",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_status ON user_sessions (status)",
        "CREATE INDEX IF NOT EXISTS idx_scan_results_session_id ON scan_results (session_id)",
        "CREATE INDEX IF NOT EXISTS idx_scan_results_user_id ON scan_results (user_id)",
        "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages (session_id)",
        "CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON chat_messages (user_id)"
    ]
    
    for index_sql in indexes:
        db_manager.execute_update(index_sql) 