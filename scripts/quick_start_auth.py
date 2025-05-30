#!/usr/bin/env python3
"""
AI CodeScan - Quick Start Authentication

Script để quickly setup và start authentication testing.
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.core.auth import init_auth_database, UserManager, CreateUserRequest, UserRole


def check_prerequisites():
    """Check if required dependencies are available."""
    try:
        import streamlit
        import sqlite3
        logger.info("✅ Prerequisites check passed")
        return True
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        logger.info("Run: pip install -r requirements.txt")
        return False


def setup_database():
    """Setup authentication database with sample users."""
    logger.info("🗄️  Setting up authentication database...")
    
    try:
        # Initialize database
        db_manager = init_auth_database("data/ai_codescan.db")
        user_manager = UserManager(db_manager)
        
        # Create sample users
        users_to_create = [
            {
                "username": "admin",
                "email": "admin@aicodescan.local",
                "password": "admin123456",
                "role": UserRole.ADMIN,
                "display_name": "AI CodeScan Administrator"
            },
            {
                "username": "test_user", 
                "email": "test@aicodescan.local",
                "password": "testpassword",
                "role": UserRole.USER,
                "display_name": "Test User"
            },
            {
                "username": "demo",
                "email": "demo@aicodescan.local", 
                "password": "demopassword",
                "role": UserRole.USER,
                "display_name": "Demo User"
            }
        ]
        
        for user_data in users_to_create:
            existing_user = user_manager.get_user_by_username(user_data["username"])
            
            if not existing_user:
                request = CreateUserRequest(
                    username=user_data["username"],
                    email=user_data["email"],
                    password=user_data["password"],
                    role=user_data["role"],
                    profile_data={
                        "display_name": user_data["display_name"],
                        "created_by": "quick_start_script"
                    }
                )
                
                user = user_manager.create_user(request)
                if user:
                    logger.info(f"✅ Created user: {user.username}")
                else:
                    logger.warning(f"❌ Failed to create user: {user_data['username']}")
            else:
                logger.info(f"👤 User already exists: {user_data['username']}")
        
        # Show user stats
        stats = user_manager.get_user_stats()
        logger.info(f"📊 Database ready - Total users: {stats['total_users']}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {str(e)}")
        return False


def start_web_ui():
    """Start the authentication web UI."""
    logger.info("🚀 Starting authentication web UI...")
    
    try:
        # Change to project root directory
        os.chdir(project_root)
        
        # Start the web UI
        cmd = [sys.executable, "src/main.py", "auth-web"]
        
        logger.info("📝 Running command: " + " ".join(cmd))
        logger.info("🌐 Web UI will be available at: http://localhost:8502")
        logger.info("🔑 Login credentials:")
        logger.info("    Username: admin     | Password: admin123456     | Role: ADMIN")
        logger.info("    Username: test_user | Password: testpassword    | Role: USER")
        logger.info("    Username: demo      | Password: demopassword    | Role: USER")
        logger.info("\n🚪 To stop: Press Ctrl+C")
        
        # Run the web UI
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        logger.info("🛑 Web UI stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start web UI: {str(e)}")


def print_help():
    """Print help information."""
    print("""
🔐 AI CodeScan - Quick Start Authentication
==========================================

This script helps you quickly setup và test the authentication system.

Commands:
  setup     - Setup database with sample users
  start     - Start authentication web UI
  full      - Setup database + start web UI (recommended)
  help      - Show this help

Examples:
  python scripts/quick_start_auth.py full      # Complete setup + start
  python scripts/quick_start_auth.py setup     # Database setup only
  python scripts/quick_start_auth.py start     # Start web UI only

Test Users (created by setup):
┌─────────────┬─────────────────┬─────────┬──────────────────────────┐
│ Username    │ Password        │ Role    │ Email                    │
├─────────────┼─────────────────┼─────────┼──────────────────────────┤
│ admin       │ admin123456     │ ADMIN   │ admin@aicodescan.local   │
│ test_user   │ testpassword    │ USER    │ test@aicodescan.local    │
│ demo        │ demopassword    │ USER    │ demo@aicodescan.local    │
└─────────────┴─────────────────┴─────────┴──────────────────────────┘

Web UI: http://localhost:8502

Logout Buttons:
- Header: "🚪 Đăng xuất" (primary blue button)
- Sidebar: "🚪 Logout" (secondary button)

Troubleshooting:
- Database issues: python scripts/reset_auth_database.py reset
- Port conflicts: python src/main.py auth-web --port 8503
- View logs: tail -f logs/ai_codescan.log
""")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "help":
        print_help()
        
    elif command == "setup":
        logger.info("🔧 Setting up authentication database...")
        if check_prerequisites():
            success = setup_database()
            if success:
                logger.success("✅ Database setup completed!")
                logger.info("💡 Next: python scripts/quick_start_auth.py start")
            else:
                logger.error("❌ Database setup failed!")
                sys.exit(1)
        else:
            sys.exit(1)
            
    elif command == "start":
        logger.info("🚀 Starting web UI...")
        if check_prerequisites():
            start_web_ui()
        else:
            sys.exit(1)
            
    elif command == "full":
        logger.info("🔧 Full setup: Database + Web UI...")
        if not check_prerequisites():
            sys.exit(1)
            
        # Setup database
        success = setup_database()
        if not success:
            logger.error("❌ Database setup failed!")
            sys.exit(1)
            
        logger.success("✅ Database setup completed!")
        
        # Start web UI
        logger.info("🚀 Starting web UI in 3 seconds...")
        time.sleep(3)
        start_web_ui()
        
    else:
        logger.error(f"❌ Unknown command: {command}")
        print_help()
        sys.exit(1)


if __name__ == "__main__":
    main() 