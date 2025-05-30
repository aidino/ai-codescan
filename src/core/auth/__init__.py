"""
AI CodeScan - Authentication Core Module

Provides user authentication, session management, and user-specific data handling.
"""

from .user_manager import UserManager, User, UserRole, CreateUserRequest, UpdateUserRequest, UserCredentials
from .auth_service import AuthService, AuthResult, AuthSession, SessionInfo
from .session_manager import (
    AuthenticatedSessionManager, 
    AuthenticatedSessionHistory, 
    AuthenticatedScanResult, 
    AuthenticatedChatMessage
)
from .database import DatabaseManager, init_auth_database, DatabaseConfig

__all__ = [
    'UserManager',
    'User',
    'UserRole',
    'CreateUserRequest',
    'UpdateUserRequest',
    'UserCredentials',
    'AuthService',
    'AuthResult',
    'AuthSession',
    'SessionInfo',
    'AuthenticatedSessionManager',
    'AuthenticatedSessionHistory',
    'AuthenticatedScanResult',
    'AuthenticatedChatMessage',
    'DatabaseManager',
    'DatabaseConfig',
    'init_auth_database'
] 