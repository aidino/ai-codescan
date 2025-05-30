#!/usr/bin/env python3
"""
AI CodeScan - Authentication System Tests

Unit tests cho authentication system including user management,
auth service, và session management.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from src.core.auth import (
    init_auth_database,
    DatabaseManager,
    UserManager,
    AuthService,
    AuthenticatedSessionManager,
    CreateUserRequest,
    UpdateUserRequest,
    UserCredentials,
    UserRole
)

from src.agents.interaction_tasking.history_manager import SessionType, SessionStatus


class TestDatabaseManager:
    """Test DatabaseManager functionality."""
    
    def setup_method(self):
        """Setup test database."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db_manager = init_auth_database(self.temp_db.name)
    
    def teardown_method(self):
        """Cleanup test database."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test database initialization."""
        assert self.db_manager is not None
        assert self.db_manager.table_exists('users')
        assert self.db_manager.table_exists('auth_sessions')
        assert self.db_manager.table_exists('user_sessions')
        assert self.db_manager.table_exists('scan_results')
        assert self.db_manager.table_exists('chat_messages')
    
    def test_execute_query(self):
        """Test query execution."""
        result = self.db_manager.execute_query("SELECT COUNT(*) as count FROM users")
        assert len(result) == 1
        assert result[0]['count'] == 0
    
    def test_execute_insert(self):
        """Test insert operation."""
        query = "INSERT INTO users (username, email, password_hash, salt, role) VALUES (?, ?, ?, ?, ?)"
        user_id = self.db_manager.execute_insert(
            query, 
            ('testuser', 'test@example.com', 'hash', 'salt', 'user')
        )
        assert user_id > 0
    
    def test_execute_update(self):
        """Test update operation."""
        # Insert test user first
        insert_query = "INSERT INTO users (username, email, password_hash, salt, role) VALUES (?, ?, ?, ?, ?)"
        user_id = self.db_manager.execute_insert(
            insert_query, 
            ('testuser', 'test@example.com', 'hash', 'salt', 'user')
        )
        
        # Update user
        update_query = "UPDATE users SET email = ? WHERE id = ?"
        affected_rows = self.db_manager.execute_update(update_query, ('newemail@example.com', user_id))
        assert affected_rows == 1


class TestUserManager:
    """Test UserManager functionality."""
    
    def setup_method(self):
        """Setup test database and user manager."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db_manager = init_auth_database(self.temp_db.name)
        self.user_manager = UserManager(self.db_manager)
    
    def teardown_method(self):
        """Cleanup test database."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_create_user_success(self):
        """Test successful user creation."""
        request = CreateUserRequest(
            username="testuser",
            email="test@example.com",
            password="password123",
            role=UserRole.USER
        )
        
        user = self.user_manager.create_user(request)
        
        assert user is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.id is not None
    
    def test_create_user_duplicate_username(self):
        """Test user creation với duplicate username."""
        request1 = CreateUserRequest(
            username="testuser",
            email="test1@example.com",
            password="password123"
        )
        
        request2 = CreateUserRequest(
            username="testuser",
            email="test2@example.com",
            password="password123"
        )
        
        user1 = self.user_manager.create_user(request1)
        user2 = self.user_manager.create_user(request2)
        
        assert user1 is not None
        assert user2 is None  # Should fail due to duplicate username
    
    def test_create_user_duplicate_email(self):
        """Test user creation với duplicate email."""
        request1 = CreateUserRequest(
            username="testuser1",
            email="test@example.com",
            password="password123"
        )
        
        request2 = CreateUserRequest(
            username="testuser2",
            email="test@example.com",
            password="password123"
        )
        
        user1 = self.user_manager.create_user(request1)
        user2 = self.user_manager.create_user(request2)
        
        assert user1 is not None
        assert user2 is None  # Should fail due to duplicate email
    
    def test_create_user_invalid_data(self):
        """Test user creation với invalid data."""
        # Invalid username (too short)
        request1 = CreateUserRequest(
            username="ab",
            email="test@example.com",
            password="password123"
        )
        
        user1 = self.user_manager.create_user(request1)
        assert user1 is None
        
        # Invalid email
        request2 = CreateUserRequest(
            username="testuser",
            email="invalid-email",
            password="password123"
        )
        
        user2 = self.user_manager.create_user(request2)
        assert user2 is None
        
        # Invalid password (too short)
        request3 = CreateUserRequest(
            username="testuser",
            email="test@example.com",
            password="short"
        )
        
        user3 = self.user_manager.create_user(request3)
        assert user3 is None
    
    def test_authenticate_user_success(self):
        """Test successful user authentication."""
        # Create user
        request = CreateUserRequest(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        created_user = self.user_manager.create_user(request)
        assert created_user is not None
        
        # Authenticate with username
        credentials1 = UserCredentials(
            username_or_email="testuser",
            password="password123"
        )
        
        authenticated_user1 = self.user_manager.authenticate_user(credentials1)
        assert authenticated_user1 is not None
        assert authenticated_user1.username == "testuser"
        
        # Authenticate with email
        credentials2 = UserCredentials(
            username_or_email="test@example.com",
            password="password123"
        )
        
        authenticated_user2 = self.user_manager.authenticate_user(credentials2)
        assert authenticated_user2 is not None
        assert authenticated_user2.email == "test@example.com"
    
    def test_authenticate_user_invalid_credentials(self):
        """Test authentication với invalid credentials."""
        # Create user
        request = CreateUserRequest(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        created_user = self.user_manager.create_user(request)
        assert created_user is not None
        
        # Wrong password
        credentials1 = UserCredentials(
            username_or_email="testuser",
            password="wrongpassword"
        )
        
        authenticated_user1 = self.user_manager.authenticate_user(credentials1)
        assert authenticated_user1 is None
        
        # Non-existent user
        credentials2 = UserCredentials(
            username_or_email="nonexistent",
            password="password123"
        )
        
        authenticated_user2 = self.user_manager.authenticate_user(credentials2)
        assert authenticated_user2 is None
    
    def test_get_user_by_id(self):
        """Test getting user by ID."""
        # Create user
        request = CreateUserRequest(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        created_user = self.user_manager.create_user(request)
        assert created_user is not None
        
        # Get user by ID
        retrieved_user = self.user_manager.get_user_by_id(created_user.id)
        assert retrieved_user is not None
        assert retrieved_user.username == created_user.username
        assert retrieved_user.email == created_user.email
    
    def test_get_user_by_username(self):
        """Test getting user by username."""
        # Create user
        request = CreateUserRequest(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        created_user = self.user_manager.create_user(request)
        assert created_user is not None
        
        # Get user by username
        retrieved_user = self.user_manager.get_user_by_username("testuser")
        assert retrieved_user is not None
        assert retrieved_user.username == "testuser"
    
    def test_get_user_by_email(self):
        """Test getting user by email."""
        # Create user
        request = CreateUserRequest(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        created_user = self.user_manager.create_user(request)
        assert created_user is not None
        
        # Get user by email
        retrieved_user = self.user_manager.get_user_by_email("test@example.com")
        assert retrieved_user is not None
        assert retrieved_user.email == "test@example.com"
    
    def test_update_user(self):
        """Test updating user information."""
        # Create user
        request = CreateUserRequest(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        created_user = self.user_manager.create_user(request)
        assert created_user is not None
        
        # Update user
        update_request = UpdateUserRequest(
            username="updateduser",
            email="updated@example.com"
        )
        
        success = self.user_manager.update_user(created_user.id, update_request)
        assert success is True
        
        # Verify update
        updated_user = self.user_manager.get_user_by_id(created_user.id)
        assert updated_user.username == "updateduser"
        assert updated_user.email == "updated@example.com"
    
    def test_change_password(self):
        """Test changing user password."""
        # Create user
        request = CreateUserRequest(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        created_user = self.user_manager.create_user(request)
        assert created_user is not None
        
        # Change password
        success = self.user_manager.change_password(created_user.id, "newpassword123")
        assert success is True
        
        # Verify old password doesn't work
        old_credentials = UserCredentials(
            username_or_email="testuser",
            password="password123"
        )
        
        authenticated_user1 = self.user_manager.authenticate_user(old_credentials)
        assert authenticated_user1 is None
        
        # Verify new password works
        new_credentials = UserCredentials(
            username_or_email="testuser",
            password="newpassword123"
        )
        
        authenticated_user2 = self.user_manager.authenticate_user(new_credentials)
        assert authenticated_user2 is not None
    
    def test_delete_user(self):
        """Test deleting (deactivating) user."""
        # Create user
        request = CreateUserRequest(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        created_user = self.user_manager.create_user(request)
        assert created_user is not None
        
        # Delete user
        success = self.user_manager.delete_user(created_user.id)
        assert success is True
        
        # Verify user is deactivated
        user = self.user_manager.get_user_by_id(created_user.id)
        assert user.is_active is False
    
    def test_list_users(self):
        """Test listing users."""
        # Create multiple users
        for i in range(5):
            request = CreateUserRequest(
                username=f"testuser{i}",
                email=f"test{i}@example.com",
                password="password123"
            )
            self.user_manager.create_user(request)
        
        # List users
        users = self.user_manager.list_users(limit=10)
        assert len(users) == 5
        
        # Test pagination
        users_page1 = self.user_manager.list_users(limit=2, offset=0)
        users_page2 = self.user_manager.list_users(limit=2, offset=2)
        
        assert len(users_page1) == 2
        assert len(users_page2) == 2
        assert users_page1[0].id != users_page2[0].id
    
    def test_get_user_stats(self):
        """Test getting user statistics."""
        # Create users với different roles
        admin_request = CreateUserRequest(
            username="admin",
            email="admin@example.com",
            password="password123",
            role=UserRole.ADMIN
        )
        
        user_request = CreateUserRequest(
            username="user",
            email="user@example.com",
            password="password123",
            role=UserRole.USER
        )
        
        self.user_manager.create_user(admin_request)
        self.user_manager.create_user(user_request)
        
        # Get stats
        stats = self.user_manager.get_user_stats()
        
        assert stats['total_users'] == 2
        assert stats['active_users'] == 2
        assert stats['by_role']['admin'] == 1
        assert stats['by_role']['user'] == 1


class TestAuthService:
    """Test AuthService functionality."""
    
    def setup_method(self):
        """Setup test database and auth service."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db_manager = init_auth_database(self.temp_db.name)
        self.user_manager = UserManager(self.db_manager)
        self.auth_service = AuthService(self.db_manager)
        
        # Create test user
        request = CreateUserRequest(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        self.test_user = self.user_manager.create_user(request)
    
    def teardown_method(self):
        """Cleanup test database."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_login_success(self):
        """Test successful login."""
        credentials = UserCredentials(
            username_or_email="testuser",
            password="password123"
        )
        
        result = self.auth_service.login(credentials)
        
        assert result.success is True
        assert result.user is not None
        assert result.user.username == "testuser"
        assert result.session_token is not None
        assert result.expires_at is not None
    
    def test_login_invalid_credentials(self):
        """Test login với invalid credentials."""
        credentials = UserCredentials(
            username_or_email="testuser",
            password="wrongpassword"
        )
        
        result = self.auth_service.login(credentials)
        
        assert result.success is False
        assert result.user is None
        assert result.session_token is None
        assert result.error_message is not None
    
    def test_validate_session(self):
        """Test session validation."""
        # Login to get session token
        credentials = UserCredentials(
            username_or_email="testuser",
            password="password123"
        )
        
        login_result = self.auth_service.login(credentials)
        assert login_result.success is True
        
        # Validate session
        session_info = self.auth_service.validate_session(login_result.session_token)
        
        assert session_info is not None
        assert session_info.user.username == "testuser"
        assert session_info.session_token == login_result.session_token
        assert session_info.time_remaining_seconds > 0
    
    def test_validate_invalid_session(self):
        """Test validation của invalid session token."""
        session_info = self.auth_service.validate_session("invalid_token")
        assert session_info is None
    
    def test_logout(self):
        """Test logout functionality."""
        # Login to get session token
        credentials = UserCredentials(
            username_or_email="testuser",
            password="password123"
        )
        
        login_result = self.auth_service.login(credentials)
        assert login_result.success is True
        
        # Logout
        logout_success = self.auth_service.logout(login_result.session_token)
        assert logout_success is True
        
        # Verify session is invalidated
        session_info = self.auth_service.validate_session(login_result.session_token)
        assert session_info is None
    
    def test_refresh_session(self):
        """Test session refresh."""
        # Login to get session token
        credentials = UserCredentials(
            username_or_email="testuser",
            password="password123"
        )
        
        login_result = self.auth_service.login(credentials)
        assert login_result.success is True
        
        # Refresh session
        refresh_result = self.auth_service.refresh_session(login_result.session_token)
        
        assert refresh_result is not None
        assert refresh_result.success is True
        assert refresh_result.session_token == login_result.session_token
        # New expiry should be later than original
        original_expiry = datetime.fromisoformat(login_result.expires_at)
        new_expiry = datetime.fromisoformat(refresh_result.expires_at)
        assert new_expiry > original_expiry
    
    def test_cleanup_expired_sessions(self):
        """Test cleanup của expired sessions."""
        # This would require manipulating database timestamps
        # For now, just test that the method runs without error
        cleaned_count = self.auth_service.cleanup_expired_sessions()
        assert cleaned_count >= 0
    
    def test_get_auth_stats(self):
        """Test getting authentication statistics."""
        # Login to create an active session
        credentials = UserCredentials(
            username_or_email="testuser",
            password="password123"
        )
        
        self.auth_service.login(credentials)
        
        # Get stats
        stats = self.auth_service.get_auth_stats()
        
        assert 'active_sessions' in stats
        assert 'total_sessions_today' in stats
        assert 'unique_users_today' in stats
        assert 'sessions_by_user' in stats


class TestAuthenticatedSessionManager:
    """Test AuthenticatedSessionManager functionality."""
    
    def setup_method(self):
        """Setup test database and session manager."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db_manager = init_auth_database(self.temp_db.name)
        self.user_manager = UserManager(self.db_manager)
        self.session_manager = AuthenticatedSessionManager(self.db_manager)
        
        # Create test user
        request = CreateUserRequest(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        self.test_user = self.user_manager.create_user(request)
    
    def teardown_method(self):
        """Cleanup test database."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_create_session(self):
        """Test creating session."""
        session_id = self.session_manager.create_session(
            user_id=self.test_user.id,
            session_type=SessionType.REPOSITORY_ANALYSIS,
            title="Test Session",
            description="Test session description"
        )
        
        assert session_id is not None
        assert len(session_id) > 0
    
    def test_get_session(self):
        """Test getting session."""
        # Create session
        session_id = self.session_manager.create_session(
            user_id=self.test_user.id,
            session_type=SessionType.REPOSITORY_ANALYSIS,
            title="Test Session",
            description="Test session description"
        )
        
        # Get session
        session = self.session_manager.get_session(session_id, self.test_user.id)
        
        assert session is not None
        assert session.session_id == session_id
        assert session.user_id == self.test_user.id
        assert session.session_type == SessionType.REPOSITORY_ANALYSIS
        assert session.title == "Test Session"
        assert session.description == "Test session description"
    
    def test_update_session_status(self):
        """Test updating session status."""
        # Create session
        session_id = self.session_manager.create_session(
            user_id=self.test_user.id,
            session_type=SessionType.REPOSITORY_ANALYSIS,
            title="Test Session"
        )
        
        # Update status
        success = self.session_manager.update_session_status(
            session_id, 
            self.test_user.id, 
            SessionStatus.COMPLETED
        )
        
        assert success is True
        
        # Verify update
        session = self.session_manager.get_session(session_id, self.test_user.id)
        assert session.status == SessionStatus.COMPLETED
    
    def test_add_chat_message(self):
        """Test adding chat message."""
        # Create session
        session_id = self.session_manager.create_session(
            user_id=self.test_user.id,
            session_type=SessionType.CODE_QNA,
            title="Test Chat Session"
        )
        
        # Add chat message
        success = self.session_manager.add_chat_message(
            session_id,
            self.test_user.id,
            "user",
            "Hello, this is a test message"
        )
        
        assert success is True
        
        # Verify message is saved
        session = self.session_manager.get_session(session_id, self.test_user.id)
        assert len(session.chat_messages) == 1
        assert session.chat_messages[0].role == "user"
        assert session.chat_messages[0].content == "Hello, this is a test message"
    
    def test_get_user_sessions(self):
        """Test getting user sessions."""
        # Create multiple sessions
        session_ids = []
        for i in range(3):
            session_id = self.session_manager.create_session(
                user_id=self.test_user.id,
                session_type=SessionType.REPOSITORY_ANALYSIS,
                title=f"Test Session {i+1}"
            )
            session_ids.append(session_id)
        
        # Get user sessions
        sessions = self.session_manager.get_user_sessions(self.test_user.id)
        
        assert len(sessions) == 3
        assert all(session.user_id == self.test_user.id for session in sessions)
    
    def test_delete_session(self):
        """Test deleting session."""
        # Create session
        session_id = self.session_manager.create_session(
            user_id=self.test_user.id,
            session_type=SessionType.REPOSITORY_ANALYSIS,
            title="Test Session"
        )
        
        # Delete session
        success = self.session_manager.delete_session(session_id, self.test_user.id)
        assert success is True
        
        # Verify session is deleted
        session = self.session_manager.get_session(session_id, self.test_user.id)
        assert session is None
    
    def test_get_user_session_stats(self):
        """Test getting user session statistics."""
        # Create sessions
        self.session_manager.create_session(
            user_id=self.test_user.id,
            session_type=SessionType.REPOSITORY_ANALYSIS,
            title="Repo Session"
        )
        
        self.session_manager.create_session(
            user_id=self.test_user.id,
            session_type=SessionType.CODE_QNA,
            title="Chat Session"
        )
        
        # Get stats
        stats = self.session_manager.get_user_session_stats(self.test_user.id)
        
        assert stats['total_sessions'] == 2
        assert 'by_type' in stats
        assert 'by_status' in stats
        assert 'recent_activity' in stats


if __name__ == "__main__":
    pytest.main([__file__]) 