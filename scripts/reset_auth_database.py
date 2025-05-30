#!/usr/bin/env python3
"""
AI CodeScan - Reset Authentication Database

Script để reset và rebuild authentication database.
"""

import sys
import os
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.auth import (
    init_auth_database, 
    UserManager, 
    CreateUserRequest, 
    UserRole,
    DatabaseManager,
    DatabaseConfig
)
from loguru import logger


def backup_database(db_path: str) -> str:
    """
    Create backup of existing database.
    
    Args:
        db_path: Path to database file
        
    Returns:
        str: Path to backup file
    """
    db_file = Path(db_path)
    
    if not db_file.exists():
        return ""
    
    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_file.parent / f"{db_file.stem}_backup_{timestamp}{db_file.suffix}"
    
    try:
        shutil.copy2(db_path, backup_path)
        logger.info(f"Database backed up to: {backup_path}")
        return str(backup_path)
    except Exception as e:
        logger.error(f"Failed to backup database: {str(e)}")
        return ""


def delete_database(db_path: str) -> bool:
    """
    Delete existing database file.
    
    Args:
        db_path: Path to database file
        
    Returns:
        bool: True if deleted successfully
    """
    db_file = Path(db_path)
    
    if not db_file.exists():
        logger.info("Database file doesn't exist, nothing to delete")
        return True
    
    try:
        db_file.unlink()
        logger.info(f"Database deleted: {db_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete database: {str(e)}")
        return False


def reset_database(db_path: str = "data/ai_codescan.db", 
                   backup: bool = True,
                   create_sample_users: bool = True) -> bool:
    """
    Reset authentication database.
    
    Args:
        db_path: Path to SQLite database file
        backup: Whether to backup existing database
        create_sample_users: Whether to create sample users
        
    Returns:
        bool: True if reset successful
    """
    logger.info("Starting database reset...")
    
    try:
        # Backup existing database if requested
        backup_path = ""
        if backup:
            backup_path = backup_database(db_path)
        
        # Delete existing database
        if not delete_database(db_path):
            return False
        
        # Initialize new database
        db_manager = init_auth_database(db_path)
        logger.info(f"New database initialized: {db_path}")
        
        if create_sample_users:
            user_manager = UserManager(db_manager)
            
            # Create admin user
            admin_request = CreateUserRequest(
                username="admin",
                email="admin@aicodescan.local",
                password="admin123456",
                role=UserRole.ADMIN,
                profile_data={
                    "display_name": "AI CodeScan Administrator",
                    "created_by": "reset_script"
                }
            )
            
            admin_user = user_manager.create_user(admin_request)
            
            if admin_user:
                logger.info(f"Admin user created: {admin_user.username}")
            else:
                logger.error("Failed to create admin user")
                return False
            
            # Create test user
            test_request = CreateUserRequest(
                username="test_user",
                email="test@aicodescan.local",
                password="testpassword",
                role=UserRole.USER,
                profile_data={
                    "display_name": "Test User",
                    "created_by": "reset_script"
                }
            )
            
            test_user = user_manager.create_user(test_request)
            
            if test_user:
                logger.info(f"Test user created: {test_user.username}")
            else:
                logger.warning("Failed to create test user")
            
            # Create demo user
            demo_request = CreateUserRequest(
                username="demo",
                email="demo@aicodescan.local", 
                password="demopassword",
                role=UserRole.USER,
                profile_data={
                    "display_name": "Demo User",
                    "created_by": "reset_script"
                }
            )
            
            demo_user = user_manager.create_user(demo_request)
            
            if demo_user:
                logger.info(f"Demo user created: {demo_user.username}")
            
            # Display user statistics
            stats = user_manager.get_user_stats()
            logger.info(f"Database reset complete:")
            logger.info(f"  - Total users: {stats['total_users']}")
            logger.info(f"  - Active users: {stats['active_users']}")
            logger.info(f"  - By role: {stats['by_role']}")
        
        if backup_path:
            logger.info(f"💾 Old database backed up to: {backup_path}")
        
        logger.success("✅ Database reset completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database reset failed: {str(e)}")
        return False


def clear_all_data(db_path: str = "data/ai_codescan.db") -> bool:
    """
    Clear all data from database but keep structure.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        bool: True if cleared successfully
    """
    try:
        config = DatabaseConfig(db_path=db_path)
        db_manager = DatabaseManager(config)
        
        logger.info("Clearing all data from database...")
        
        # Delete data in order (respecting foreign key constraints)
        tables_to_clear = [
            "chat_messages",
            "scan_results", 
            "user_sessions",
            "auth_sessions",
            "users"
        ]
        
        for table in tables_to_clear:
            query = f"DELETE FROM {table}"
            affected_rows = db_manager.execute_update(query)
            logger.info(f"Cleared {affected_rows} rows from {table}")
        
        logger.success("✅ All data cleared successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to clear data: {str(e)}")
        return False


def main():
    """Main function với command-line interface."""
    if len(sys.argv) < 2:
        print("AI CodeScan - Database Reset Tool")
        print("=================================")
        print("\nUsage:")
        print("  python reset_auth_database.py reset [options]     - Full database reset")
        print("  python reset_auth_database.py clear               - Clear data only")
        print("  python reset_auth_database.py backup <db_path>    - Backup database")
        print("\nReset Options:")
        print("  --db-path <path>     Database file path (default: data/ai_codescan.db)")
        print("  --no-backup          Don't create backup")
        print("  --no-users           Don't create sample users")
        print("\nExamples:")
        print("  python reset_auth_database.py reset")
        print("  python reset_auth_database.py reset --db-path data/mydb.db")
        print("  python reset_auth_database.py reset --no-backup --no-users")
        print("  python reset_auth_database.py clear")
        print("  python reset_auth_database.py backup data/ai_codescan.db")
        return
    
    command = sys.argv[1].lower()
    
    if command == "reset":
        # Parse options
        db_path = "data/ai_codescan.db"
        backup = True
        create_users = True
        
        i = 2
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg == "--db-path" and i + 1 < len(sys.argv):
                db_path = sys.argv[i + 1]
                i += 2
            elif arg == "--no-backup":
                backup = False
                i += 1
            elif arg == "--no-users":
                create_users = False
                i += 1
            else:
                print(f"Unknown option: {arg}")
                sys.exit(1)
        
        # Confirm reset
        print(f"🗄️  Database: {db_path}")
        print(f"💾 Backup: {'Yes' if backup else 'No'}")
        print(f"👥 Create sample users: {'Yes' if create_users else 'No'}")
        
        confirm = input("\n⚠️  Are you sure you want to reset the database? (yes/no): ").lower()
        if confirm not in ['yes', 'y']:
            print("Reset cancelled")
            sys.exit(0)
        
        success = reset_database(db_path, backup, create_users)
        sys.exit(0 if success else 1)
    
    elif command == "clear":
        db_path = sys.argv[2] if len(sys.argv) > 2 else "data/ai_codescan.db"
        
        print(f"🗄️  Database: {db_path}")
        confirm = input("\n⚠️  Are you sure you want to clear all data? (yes/no): ").lower()
        if confirm not in ['yes', 'y']:
            print("Clear cancelled")
            sys.exit(0)
        
        success = clear_all_data(db_path)
        sys.exit(0 if success else 1)
    
    elif command == "backup":
        if len(sys.argv) < 3:
            print("Please specify database path")
            sys.exit(1)
        
        db_path = sys.argv[2]
        backup_path = backup_database(db_path)
        
        if backup_path:
            print(f"✅ Backup created: {backup_path}")
            sys.exit(0)
        else:
            print("❌ Backup failed")
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    from datetime import datetime
    main() 