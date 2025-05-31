# AI CodeScan - Authentication System

## Overview

AI CodeScan authentication system provides secure user management và multi-user support cho code analysis platform. Hệ thống được thiết kế với security-first approach và production-ready capabilities.

## Features

### 🔐 Core Authentication
- **User Registration**: Secure user account creation với validation
- **User Login**: Username hoặc email-based authentication
- **Session Management**: Secure token-based sessions với automatic expiration
- **Password Security**: PBKDF2-HMAC-SHA256 hashing với random salt
- **Multi-device Support**: Multiple concurrent sessions per user

### 👥 User Management
- **User Roles**: ADMIN, USER, GUEST với appropriate permissions
- **User Profiles**: Customizable user profiles với metadata
- **Account Management**: Update profile, change password, deactivate account
- **User Statistics**: Activity tracking và usage analytics

### 🗄️ Database Design
- **SQLite Backend**: Lightweight, embedded database với ACID compliance
- **Optimized Schema**: Foreign key constraints và performance indexes
- **Data Isolation**: User-scoped data với proper security boundaries
- **Audit Trail**: Comprehensive logging của user activities

### 🌐 Web Interface
- **Login/Register Forms**: Modern UI với real-time validation
- **User Dashboard**: Personal activity overview và quick actions
- **Session History**: Browse và manage past analysis sessions
- **Responsive Design**: Mobile-friendly interface

## Architecture

```
src/core/auth/
├── __init__.py              # Module exports
├── database.py              # SQLite database manager
├── user_manager.py          # User CRUD operations
├── auth_service.py          # Authentication logic
└── session_manager.py       # Enhanced session management

src/agents/interaction_tasking/
├── auth_web_ui.py           # Authenticated Streamlit UI
└── web_ui.py               # Original anonymous UI

scripts/
└── setup_auth_database.py  # Database setup tool

tests/
└── test_auth_system.py     # Comprehensive unit tests
```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(32) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP NULL,
    profile_data TEXT NULL,
    preferences TEXT NULL
);
```

### Authentication Sessions
```sql
CREATE TABLE auth_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45) NULL,
    user_agent TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

### User Sessions
```sql
CREATE TABLE user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(36) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    session_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

## Quick Start

### 1. Initialize Database

```bash
# Setup authentication database với default users
python src/main.py setup-auth

# Or specify custom database path
python src/main.py setup-auth --db-path /path/to/database.db
```

### 2. Start Authenticated Web UI

```bash
# Launch authenticated web interface
python src/main.py auth-web

# Access at http://localhost:8502
```

### 3. Default Accounts

**Admin Account:**
- Username: `admin`
- Password: `admin123456`
- Role: ADMIN

**Test Account:**
- Username: `test_user`
- Password: `testpassword`
- Role: USER

> ⚠️ **Security Warning**: Change default passwords immediately in production!

## API Usage

### User Management

```python
from src.core.auth import UserManager, CreateUserRequest, UserRole

# Initialize user manager
user_manager = UserManager(db_manager)

# Create new user
request = CreateUserRequest(
    username="newuser",
    email="user@example.com",
    password="securepassword",
    role=UserRole.USER
)

user = user_manager.create_user(request)

# Authenticate user
credentials = UserCredentials(
    username_or_email="newuser",
    password="securepassword"
)

authenticated_user = user_manager.authenticate_user(credentials)
```

### Authentication Service

```python
from src.core.auth import AuthService

# Initialize auth service
auth_service = AuthService(db_manager)

# User login
result = auth_service.login(credentials)

if result.success:
    session_token = result.session_token
    user = result.user
    expires_at = result.expires_at

# Validate session
session_info = auth_service.validate_session(session_token)

# Logout
auth_service.logout(session_token)
```

### Session Management

```python
from src.core.auth import AuthenticatedSessionManager
from src.core.auth.session_manager import SessionType

# Initialize session manager
session_manager = AuthenticatedSessionManager(db_manager)

# Create user session
session_id = session_manager.create_session(
    user_id=user.id,
    session_type=SessionType.REPOSITORY_ANALYSIS,
    title="Repository Analysis",
    description="Analyzing project repository"
)

# Get user sessions
sessions = session_manager.get_user_sessions(user.id)

# Add chat message
session_manager.add_chat_message(
    session_id,
    user.id,
    "user",
    "How can I improve this code?"
)
```

## Security Features

### Password Security
- **Hashing Algorithm**: PBKDF2-HMAC-SHA256
- **Iterations**: 100,000 (industry standard)
- **Salt**: 32-byte cryptographically secure random salt per password
- **Minimum Length**: 8 characters (configurable)

### Session Security
- **Token Generation**: 32-byte cryptographically secure random tokens
- **Expiration**: 24-hour default với automatic cleanup
- **Refresh**: Automatic session extension on activity
- **Device Tracking**: IP address và user agent logging

### Input Validation
- **Username**: 3-50 characters, alphanumeric với underscores
- **Email**: RFC 5322 compliant email validation
- **Password**: Configurable strength requirements
- **SQL Injection**: Parameterized queries throughout

## Configuration

### Database Configuration

```python
from src.core.auth.database import DatabaseConfig

config = DatabaseConfig(
    db_path="data/ai_codescan.db",
    timeout=30.0,
    enable_foreign_keys=True
)
```

### Session Configuration

```python
# Session timeout (24 hours default)
SESSION_TIMEOUT_HOURS = 24

# Password hashing iterations
PBKDF2_ITERATIONS = 100000

# Token length (bytes)
TOKEN_LENGTH = 32
```

## CLI Tools

### Database Setup
```bash
# Initialize database với sample users
python scripts/setup_auth_database.py init

# Create user interactively
python scripts/setup_auth_database.py create-user

# List all users
python scripts/setup_auth_database.py list-users
```

### User Management
```bash
# Setup auth from main CLI
python src/main.py setup-auth

# Health check
python src/main.py health --port 8502
```

## Testing

### Run Tests
```bash
# Run all authentication tests
pytest tests/test_auth_system.py -v

# Run with coverage
pytest tests/test_auth_system.py --cov=src.core.auth
```

### Test Categories
- **DatabaseManager**: 4 tests covering database operations
- **UserManager**: 12 tests covering user lifecycle
- **AuthService**: 8 tests covering authentication flow
- **SessionManager**: 8 tests covering session management

## Performance

### Database Performance
- **Indexes**: Optimized indexes trên frequently queried columns
- **Connection Pooling**: Efficient database connection management
- **Query Optimization**: Minimal N+1 queries với proper joins

### Session Performance
- **Token Lookup**: O(1) session token validation
- **Cache Strategy**: In-memory caching cho frequent operations
- **Cleanup**: Automated expired session cleanup

## Security Considerations

### Production Deployment
1. **Change Default Passwords**: Update admin và test user passwords
2. **Database Security**: Restrict database file permissions
3. **HTTPS**: Use TLS encryption for web interface
4. **Environment Variables**: Store sensitive config in environment
5. **Regular Updates**: Monitor và update dependencies

### Monitoring
- **Authentication Logs**: Monitor failed login attempts
- **Session Activity**: Track unusual session patterns
- **Database Health**: Monitor database performance
- **User Activity**: Audit user actions và data access

## Troubleshooting

### Common Issues

**Database Connection Errors:**
```bash
# Check database file permissions
ls -la data/ai_codescan.db

# Reinitialize database
python src/main.py setup-auth --db-path data/ai_codescan.db
```