#!/usr/bin/env python3
"""
AI CodeScan - Authentication Database Setup

Script để initialize authentication database và create admin user.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.auth import (
    init_auth_database, 
    UserManager, 
    CreateUserRequest, 
    UserRole
)
from loguru import logger


def setup_auth_database(db_path: str = "data/ai_codescan.db"):
    """
    Setup authentication database với initial admin user.
    
    Args:
        db_path: Path to SQLite database file
    """
    logger.info("Starting authentication database setup...")
    
    try:
        # Initialize database
        db_manager = init_auth_database(db_path)
        logger.info(f"Database initialized: {db_path}")
        
        # Create user manager
        user_manager = UserManager(db_manager)
        
        # Check if admin user already exists
        admin_user = user_manager.get_user_by_username("admin")
        
        if admin_user:
            logger.info("Admin user already exists")
        else:
            # Create default admin user
            admin_request = CreateUserRequest(
                username="admin",
                email="admin@aicodescan.local",
                password="admin123456",  # Should be changed immediately
                role=UserRole.ADMIN,
                profile_data={
                    "display_name": "AI CodeScan Administrator",
                    "created_by": "setup_script"
                }
            )
            
            admin_user = user_manager.create_user(admin_request)
            
            if admin_user:
                logger.info(f"Admin user created: {admin_user.username}")
                logger.warning("⚠️  Default admin password is 'admin123456' - CHANGE IT IMMEDIATELY!")
            else:
                logger.error("Failed to create admin user")
                return False
        
        # Create example user for testing
        test_user = user_manager.get_user_by_username("test_user")
        
        if not test_user:
            test_request = CreateUserRequest(
                username="test_user",
                email="test@aicodescan.local",
                password="testpassword",
                role=UserRole.USER,
                profile_data={
                    "display_name": "Test User",
                    "created_by": "setup_script"
                }
            )
            
            test_user = user_manager.create_user(test_request)
            
            if test_user:
                logger.info(f"Test user created: {test_user.username}")
            else:
                logger.warning("Failed to create test user")
        
        # Display user statistics
        stats = user_manager.get_user_stats()
        logger.info(f"Database setup complete:")
        logger.info(f"  - Total users: {stats['total_users']}")
        logger.info(f"  - Active users: {stats['active_users']}")
        logger.info(f"  - By role: {stats['by_role']}")
        
        logger.success("✅ Authentication database setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        return False


def create_user_interactive():
    """Interactive user creation."""
    print("\n🔐 Create New User")
    print("==================")
    
    try:
        # Get user input
        username = input("Username: ").strip()
        email = input("Email: ").strip()
        password = input("Password: ").strip()
        
        print("\nRoles:")
        print("1. User (regular user)")
        print("2. Admin (administrator)")
        
        role_choice = input("Select role (1-2): ").strip()
        
        if role_choice == "1":
            role = UserRole.USER
        elif role_choice == "2":
            role = UserRole.ADMIN
        else:
            print("Invalid role selection")
            return False
        
        display_name = input("Display name (optional): ").strip()
        
        # Initialize database
        db_manager = init_auth_database()
        user_manager = UserManager(db_manager)
        
        # Prepare profile data
        profile_data = {}
        if display_name:
            profile_data["display_name"] = display_name
        profile_data["created_by"] = "interactive_script"
        
        # Create user
        request = CreateUserRequest(
            username=username,
            email=email,
            password=password,
            role=role,
            profile_data=profile_data
        )
        
        user = user_manager.create_user(request)
        
        if user:
            print(f"\n✅ User created successfully:")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   Role: {user.role.value}")
            print(f"   ID: {user.id}")
            return True
        else:
            print("\n❌ Failed to create user")
            return False
            
    except KeyboardInterrupt:
        print("\n\nOperation cancelled")
        return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def list_users():
    """List all users in database."""
    try:
        # Initialize database
        db_manager = init_auth_database()
        user_manager = UserManager(db_manager)
        
        # Get users
        users = user_manager.list_users(limit=100)
        
        if not users:
            print("No users found")
            return
        
        print("\n👥 Users in Database")
        print("====================")
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Role':<10} {'Active':<8} {'Created':<20}")
        print("-" * 100)
        
        for user in users:
            created_date = user.created_at[:10] if user.created_at else "Unknown"
            print(f"{user.id:<5} {user.username:<20} {user.email:<30} {user.role.value:<10} {'Yes' if user.is_active else 'No':<8} {created_date:<20}")
        
        # Show stats
        stats = user_manager.get_user_stats()
        print(f"\nTotal: {stats['total_users']} | Active: {stats['active_users']}")
        
    except Exception as e:
        print(f"Error listing users: {str(e)}")


def main():
    """Main function với command-line interface."""
    if len(sys.argv) < 2:
        print("AI CodeScan - Authentication Database Setup")
        print("===========================================")
        print("\nUsage:")
        print("  python setup_auth_database.py init [db_path]     - Initialize database")
        print("  python setup_auth_database.py create-user        - Create user interactively")
        print("  python setup_auth_database.py list-users         - List all users")
        print("\nExamples:")
        print("  python setup_auth_database.py init")
        print("  python setup_auth_database.py init data/mydb.db")
        print("  python setup_auth_database.py create-user")
        print("  python setup_auth_database.py list-users")
        return
    
    command = sys.argv[1].lower()
    
    if command == "init":
        db_path = sys.argv[2] if len(sys.argv) > 2 else "data/ai_codescan.db"
        success = setup_auth_database(db_path)
        sys.exit(0 if success else 1)
    
    elif command == "create-user":
        success = create_user_interactive()
        sys.exit(0 if success else 1)
    
    elif command == "list-users":
        list_users()
        sys.exit(0)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main() 