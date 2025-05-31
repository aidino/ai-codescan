#!/usr/bin/env python3
"""
AI CodeScan - Authentication Demo Script

Demonstrates và test tính năng đăng nhập, đăng xuất, đăng ký.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loguru import logger
from src.core.auth import (
    init_auth_database,
    UserManager,
    AuthService,
    CreateUserRequest,
    UserCredentials,
    UserRole
)

def test_authentication_system():
    """Test comprehensive authentication functionality."""
    print("🔐 AI CodeScan Authentication System Demo")
    print("=" * 50)
    
    # Initialize system
    print("\n1. 🗄️ Initializing database...")
    db_manager = init_auth_database("data/ai_codescan.db")
    user_manager = UserManager(db_manager)
    auth_service = AuthService(db_manager)
    
    # Test user creation (registration)
    print("\n2. 📝 Testing User Registration...")
    
    new_user_request = CreateUserRequest(
        username="demo_user",
        email="demo@test.com",
        password="demopassword123",
        role=UserRole.USER,
        profile_data={"display_name": "Demo User", "department": "Testing"}
    )
    
    # Check if user already exists
    existing_user = user_manager.get_user_by_username("demo_user")
    if existing_user:
        print(f"   ℹ️  User 'demo_user' already exists, skipping creation")
    else:
        new_user = user_manager.create_user(new_user_request)
        if new_user:
            print(f"   ✅ Successfully registered user: {new_user.username}")
        else:
            print(f"   ❌ Failed to register user")
    
    # Test user authentication (login)
    print("\n3. 🔑 Testing User Login...")
    
    login_credentials = UserCredentials(
        username_or_email="demo_user",
        password="demopassword123"
    )
    
    auth_result = auth_service.login(login_credentials)
    
    if auth_result.success:
        print(f"   ✅ Login successful!")
        print(f"   👤 User: {auth_result.user.username}")
        print(f"   🔗 Session token: {auth_result.session_token[:16]}...")
        print(f"   ⏰ Expires at: {auth_result.expires_at}")
        
        session_token = auth_result.session_token
        
        # Test session validation
        print("\n4. 🔍 Testing Session Validation...")
        session_info = auth_service.validate_session(session_token)
        
        if session_info:
            print(f"   ✅ Session is valid")
            print(f"   👤 Current user: {session_info.user.username}")
            print(f"   ⏳ Time remaining: {session_info.time_remaining_seconds} seconds")
        else:
            print(f"   ❌ Session validation failed")
        
        # Test logout
        print("\n5. 🚪 Testing User Logout...")
        logout_success = auth_service.logout(session_token)
        
        if logout_success:
            print(f"   ✅ Logout successful")
        else:
            print(f"   ❌ Logout failed")
        
        # Verify session is invalidated
        print("\n6. 🔍 Verifying Session Invalidation...")
        invalid_session = auth_service.validate_session(session_token)
        
        if not invalid_session:
            print(f"   ✅ Session properly invalidated after logout")
        else:
            print(f"   ❌ Session still valid after logout (ERROR)")
            
    else:
        print(f"   ❌ Login failed: {auth_result.error_message}")
    
    # Test invalid login
    print("\n7. ❌ Testing Invalid Login...")
    
    invalid_credentials = UserCredentials(
        username_or_email="demo_user",
        password="wrongpassword"
    )
    
    invalid_auth_result = auth_service.login(invalid_credentials)
    
    if not invalid_auth_result.success:
        print(f"   ✅ Invalid login properly rejected: {invalid_auth_result.error_message}")
    else:
        print(f"   ❌ Invalid login incorrectly accepted (SECURITY ISSUE)")
    
    # Display user statistics
    print("\n8. 📊 User Statistics...")
    stats = user_manager.get_user_stats()
    print(f"   Total users: {stats['total_users']}")
    print(f"   Active users: {stats['active_users']}")
    print(f"   Users by role: {stats['by_role']}")
    print(f"   Recent registrations (7 days): {stats['recent_registrations']}")
    print(f"   Recent logins (7 days): {stats['recent_logins']}")
    
    # Display auth statistics
    print("\n9. 📈 Authentication Statistics...")
    auth_stats = auth_service.get_auth_stats()
    print(f"   Active sessions: {auth_stats['active_sessions']}")
    print(f"   Sessions today: {auth_stats['total_sessions_today']}")
    print(f"   Unique users today: {auth_stats['unique_users_today']}")
    print(f"   Sessions by user: {auth_stats['sessions_by_user']}")
    
    print("\n" + "=" * 50)
    print("🎉 Authentication Demo Completed!")


def test_web_ui_credentials():
    """Display web UI test credentials."""
    print("\n🌐 Web UI Test Credentials")
    print("=" * 30)
    print("URL: http://localhost:8502")
    print("\nDefault Test Accounts:")
    print("┌─────────────┬─────────────────┬─────────┐")
    print("│ Username    │ Password        │ Role    │")
    print("├─────────────┼─────────────────┼─────────┤")
    print("│ admin       │ admin123456     │ ADMIN   │")
    print("│ test_user   │ testpassword    │ USER    │")
    print("│ demo        │ demopassword    │ USER    │")
    print("│ demo_user   │ demopassword123 │ USER    │")
    print("└─────────────┴─────────────────┴─────────┘")
    print("\nTest Scenarios:")
    print("1. Login với valid credentials")
    print("2. Login với invalid credentials")
    print("3. Register new account")
    print("4. Logout (2 buttons: header và sidebar)")
    print("5. Session history và user isolation")


if __name__ == "__main__":
    test_authentication_system()
    test_web_ui_credentials() 