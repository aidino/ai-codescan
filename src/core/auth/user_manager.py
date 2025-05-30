#!/usr/bin/env python3
"""
AI CodeScan - User Manager

Quản lý users, authentication, và user data operations.
"""

import hashlib
import secrets
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum
from loguru import logger

from .database import DatabaseManager


class UserRole(Enum):
    """User roles."""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


@dataclass
class User:
    """User data structure."""
    id: Optional[int]
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_login_at: Optional[str] = None
    profile_data: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['role'] = self.role.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create User from dictionary."""
        if 'role' in data and isinstance(data['role'], str):
            data['role'] = UserRole(data['role'])
        return cls(**data)


@dataclass
class UserCredentials:
    """User credentials for authentication."""
    username_or_email: str
    password: str


@dataclass
class CreateUserRequest:
    """Request to create new user."""
    username: str
    email: str
    password: str
    role: UserRole = UserRole.USER
    profile_data: Optional[Dict[str, Any]] = None


@dataclass
class UpdateUserRequest:
    """Request to update user."""
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    profile_data: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None


class UserManager:
    """
    User management service.
    
    Handles user creation, authentication, và user data operations.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize UserManager.
        
        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
        logger.info("UserManager initialized")
    
    def create_user(self, request: CreateUserRequest) -> Optional[User]:
        """
        Create new user.
        
        Args:
            request: User creation request
            
        Returns:
            Optional[User]: Created user or None if failed
        """
        try:
            # Validate input
            if not self._validate_username(request.username):
                logger.warning(f"Invalid username: {request.username}")
                return None
            
            if not self._validate_email(request.email):
                logger.warning(f"Invalid email: {request.email}")
                return None
            
            if not self._validate_password(request.password):
                logger.warning("Invalid password")
                return None
            
            # Check if user already exists
            if self.get_user_by_username(request.username):
                logger.warning(f"Username already exists: {request.username}")
                return None
            
            if self.get_user_by_email(request.email):
                logger.warning(f"Email already exists: {request.email}")
                return None
            
            # Hash password
            salt = secrets.token_hex(32)
            password_hash = self._hash_password(request.password, salt)
            
            # Prepare profile data
            profile_json = json.dumps(request.profile_data) if request.profile_data else None
            
            # Insert user
            query = """
            INSERT INTO users (username, email, password_hash, salt, role, profile_data)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            
            user_id = self.db.execute_insert(
                query, 
                (
                    request.username,
                    request.email,
                    password_hash,
                    salt,
                    request.role.value,
                    profile_json
                )
            )
            
            logger.info(f"User created successfully: {request.username} (ID: {user_id})")
            return self.get_user_by_id(user_id)
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return None
    
    def authenticate_user(self, credentials: UserCredentials) -> Optional[User]:
        """
        Authenticate user with credentials.
        
        Args:
            credentials: User credentials
            
        Returns:
            Optional[User]: Authenticated user or None if failed
        """
        try:
            # Get user by username or email
            user = (self.get_user_by_username(credentials.username_or_email) or 
                   self.get_user_by_email(credentials.username_or_email))
            
            if not user:
                logger.warning(f"User not found: {credentials.username_or_email}")
                return None
            
            if not user.is_active:
                logger.warning(f"User account disabled: {user.username}")
                return None
            
            # Get stored password hash và salt
            query = "SELECT password_hash, salt FROM users WHERE id = ?"
            result = self.db.execute_query(query, (user.id,))
            
            if not result:
                return None
            
            stored_hash = result[0]['password_hash']
            salt = result[0]['salt']
            
            # Verify password
            computed_hash = self._hash_password(credentials.password, salt)
            
            if not secrets.compare_digest(stored_hash, computed_hash):
                logger.warning(f"Invalid password for user: {user.username}")
                return None
            
            # Update last login
            self._update_last_login(user.id)
            
            logger.info(f"User authenticated successfully: {user.username}")
            return user
            
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[User]: User or None if not found
        """
        query = """
        SELECT id, username, email, role, is_active, 
               created_at, updated_at, last_login_at, 
               profile_data, preferences
        FROM users WHERE id = ?
        """
        
        result = self.db.execute_query(query, (user_id,))
        
        if result:
            return self._row_to_user(result[0])
        return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username
            
        Returns:
            Optional[User]: User or None if not found
        """
        query = """
        SELECT id, username, email, role, is_active, 
               created_at, updated_at, last_login_at, 
               profile_data, preferences
        FROM users WHERE username = ?
        """
        
        result = self.db.execute_query(query, (username,))
        
        if result:
            return self._row_to_user(result[0])
        return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email: Email address
            
        Returns:
            Optional[User]: User or None if not found
        """
        query = """
        SELECT id, username, email, role, is_active, 
               created_at, updated_at, last_login_at, 
               profile_data, preferences
        FROM users WHERE email = ?
        """
        
        result = self.db.execute_query(query, (email,))
        
        if result:
            return self._row_to_user(result[0])
        return None
    
    def update_user(self, user_id: int, request: UpdateUserRequest) -> bool:
        """
        Update user information.
        
        Args:
            user_id: User ID
            request: Update request
            
        Returns:
            bool: True if updated successfully
        """
        try:
            updates = []
            params = []
            
            if request.username is not None:
                if not self._validate_username(request.username):
                    return False
                updates.append("username = ?")
                params.append(request.username)
            
            if request.email is not None:
                if not self._validate_email(request.email):
                    return False
                updates.append("email = ?")
                params.append(request.email)
            
            if request.role is not None:
                updates.append("role = ?")
                params.append(request.role.value)
            
            if request.is_active is not None:
                updates.append("is_active = ?")
                params.append(request.is_active)
            
            if request.profile_data is not None:
                updates.append("profile_data = ?")
                params.append(json.dumps(request.profile_data))
            
            if request.preferences is not None:
                updates.append("preferences = ?")
                params.append(json.dumps(request.preferences))
            
            if not updates:
                return True  # Nothing to update
            
            # Add updated_at
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(user_id)
            
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            
            affected_rows = self.db.execute_update(query, tuple(params))
            
            return affected_rows > 0
            
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            return False
    
    def change_password(self, user_id: int, new_password: str) -> bool:
        """
        Change user password.
        
        Args:
            user_id: User ID
            new_password: New password
            
        Returns:
            bool: True if changed successfully
        """
        try:
            if not self._validate_password(new_password):
                return False
            
            # Generate new salt và hash
            salt = secrets.token_hex(32)
            password_hash = self._hash_password(new_password, salt)
            
            query = """
            UPDATE users 
            SET password_hash = ?, salt = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """
            
            affected_rows = self.db.execute_update(
                query, 
                (password_hash, salt, user_id)
            )
            
            return affected_rows > 0
            
        except Exception as e:
            logger.error(f"Error changing password: {str(e)}")
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """
        Delete user (soft delete by deactivating).
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            query = """
            UPDATE users 
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """
            
            affected_rows = self.db.execute_update(query, (user_id,))
            return affected_rows > 0
            
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return False
    
    def list_users(self, limit: int = 50, offset: int = 0, 
                   role_filter: Optional[UserRole] = None,
                   active_only: bool = True) -> List[User]:
        """
        List users with pagination và filtering.
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            role_filter: Filter by role
            active_only: Only return active users
            
        Returns:
            List[User]: List of users
        """
        conditions = []
        params = []
        
        if active_only:
            conditions.append("is_active = 1")
        
        if role_filter:
            conditions.append("role = ?")
            params.append(role_filter.value)
        
        where_clause = ""
        if conditions:
            where_clause = f"WHERE {' AND '.join(conditions)}"
        
        query = f"""
        SELECT id, username, email, role, is_active, 
               created_at, updated_at, last_login_at, 
               profile_data, preferences
        FROM users {where_clause}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """
        
        params.extend([limit, offset])
        result = self.db.execute_query(query, tuple(params))
        
        return [self._row_to_user(row) for row in result]
    
    def get_user_stats(self) -> Dict[str, Any]:
        """
        Get user statistics.
        
        Returns:
            Dict[str, Any]: User statistics
        """
        stats = {
            'total_users': 0,
            'active_users': 0,
            'by_role': {},
            'recent_registrations': 0,
            'recent_logins': 0
        }
        
        try:
            # Total và active users
            result = self.db.execute_query("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active
                FROM users
            """)
            
            if result:
                stats['total_users'] = result[0]['total']
                stats['active_users'] = result[0]['active']
            
            # By role
            result = self.db.execute_query("""
                SELECT role, COUNT(*) as count
                FROM users WHERE is_active = 1
                GROUP BY role
            """)
            
            for row in result:
                stats['by_role'][row['role']] = row['count']
            
            # Recent activity (last 7 days)
            result = self.db.execute_query("""
                SELECT 
                    COUNT(*) as registrations
                FROM users 
                WHERE created_at >= datetime('now', '-7 days')
            """)
            
            if result:
                stats['recent_registrations'] = result[0]['registrations']
            
            result = self.db.execute_query("""
                SELECT 
                    COUNT(*) as logins
                FROM users 
                WHERE last_login_at >= datetime('now', '-7 days')
            """)
            
            if result:
                stats['recent_logins'] = result[0]['logins']
                
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
        
        return stats
    
    def _row_to_user(self, row) -> User:
        """Convert database row to User object."""
        profile_data = None
        if row['profile_data']:
            try:
                profile_data = json.loads(row['profile_data'])
            except json.JSONDecodeError:
                pass
        
        preferences = None
        if row['preferences']:
            try:
                preferences = json.loads(row['preferences'])
            except json.JSONDecodeError:
                pass
        
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            role=UserRole(row['role']),
            is_active=bool(row['is_active']),
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            last_login_at=row['last_login_at'],
            profile_data=profile_data,
            preferences=preferences
        )
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt."""
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    
    def _validate_username(self, username: str) -> bool:
        """Validate username."""
        if not username or len(username) < 3 or len(username) > 50:
            return False
        # Allow alphanumeric và underscores/hyphens
        return username.replace('_', '').replace('-', '').isalnum()
    
    def _validate_email(self, email: str) -> bool:
        """Basic email validation."""
        if not email or '@' not in email:
            return False
        parts = email.split('@')
        return len(parts) == 2 and all(len(p) > 0 for p in parts)
    
    def _validate_password(self, password: str) -> bool:
        """Validate password strength."""
        if not password or len(password) < 8:
            return False
        return True
    
    def _update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp."""
        try:
            query = "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?"
            self.db.execute_update(query, (user_id,))
        except Exception as e:
            logger.warning(f"Failed to update last login: {str(e)}") 