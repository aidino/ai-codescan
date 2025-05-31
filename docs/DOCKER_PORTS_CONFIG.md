# AI CodeScan - Authenticated Interface Configuration

## 🔍 Overview

AI CodeScan hiện chỉ cung cấp một web interface duy nhất với user authentication system để đảm bảo bảo mật và quản lý user sessions hiệu quả.

### 🔐 Authenticated Web Interface (Port 8501)
- **URL**: http://localhost:8501
- **File**: `src/agents/interaction_tasking/auth_web_ui.py`
- **Features**:
  - Complete user authentication system
  - User registration và login
  - Persistent user sessions với history tracking
  - User-specific analysis results và chat history
  - Role-based access control (Admin, User, Guest)
  - Session management với security features
  - Professional UI với modern design
  - Advanced analysis capabilities

## 🐳 Docker Configuration

### Single Interface Mode (Default)
```bash
# Start authenticated interface
docker-compose up ai-codescan
# hoặc
python src/main.py web
```

**Environment Variables:**
- `AI_CODESCAN_AUTH_MODE=auth` (default and only mode)
- `STREAMLIT_SERVER_PORT=8501` 
- `STREAMLIT_SERVER_ADDRESS=0.0.0.0`

**Container Configuration:**
- **Port Mapping**: 8501:8501
- **Health Check**: http://localhost:8501/_stcore/health
- **Default Admin**: username=`admin`, password=`admin123456`

## 🚀 Quick Start

### 1. Using Docker (Recommended)
```bash
# Start all services including authentication
docker-compose up -d

# Wait for initialization (about 30 seconds)
# Access web interface
open http://localhost:8501
```

### 2. Using Python CLI
```bash
# Start authenticated web interface
python src/main.py web

# Access interface
open http://localhost:8501
```

### 3. Login Information
**Default Admin Account:**
- **Username**: `admin`
- **Password**: `admin123456`
- **Email**: `admin@aicodescan.local`

**Demo Accounts:**
- **Test User**: username=`test_user`, password=`testpassword`
- **Demo User**: username=`demo`, password=`demopassword`

## 🔒 Security Features

### Authentication System:
- **Password Hashing**: PBKDF2-HMAC-SHA256 với random salt
- **Session Management**: Secure session tokens với expiration
- **User Isolation**: Complete separation của user data
- **Input Validation**: Comprehensive validation để prevent attacks
- **SQL Injection Protection**: Parameterized queries throughout

### User Management:
- **Registration**: Secure user registration với validation
- **Role-Based Access**: Admin, User, Guest roles với appropriate permissions
- **Session Tracking**: Complete session history và activity tracking
- **Profile Management**: User profiles với optional metadata

## 📊 Features Comparison

### Before (Anonymous + Authenticated):
- ❌ Two separate interfaces confusing users
- ❌ Port conflicts (8501 vs 8502)
- ❌ Inconsistent user experience
- ❌ Anonymous interface lacked persistence

### After (Authenticated Only):
- ✅ Single, unified interface
- ✅ Standard port 8501 cho consistency
- ✅ Complete authentication system
- ✅ Persistent user sessions và history
- ✅ Professional UI với role-based features
- ✅ Better security và user management

## 🔧 Configuration Options

### Docker Environment Variables:
```bash
# Core settings
AI_CODESCAN_ENV=development
AI_CODESCAN_AUTH_MODE=auth

# Database settings
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=ai_codescan_password

# Web interface settings
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### CLI Options:
```bash
# Main web command (authenticated interface)
python src/main.py web

# Authentication setup
python src/main.py setup-auth

# Health check
python src/main.py health --port 8501
```

## 🛠️ Troubleshooting

### Common Issues:

1. **Port Already in Use**:
   ```bash
   # Kill existing process
   lsof -ti:8501 | xargs kill -9
   # Or change port in docker-compose.yml
   ```

2. **Authentication Database Not Found**:
   ```bash
   # Initialize authentication system
   python src/main.py setup-auth
   ```

3. **Import Errors**:
   ```bash
   # Ensure all dependencies installed
   pip install -r requirements.txt
   ```

4. **Login Issues**:
   - Use default admin credentials: admin/admin123456
   - Check logs: `logs/app.log`
   - Reset database: `python scripts/reset_auth_database.py reset`

## 📈 Performance & Monitoring

### Health Checks:
- **Interface Health**: http://localhost:8501/_stcore/health
- **Database Health**: Built-in SQLite health checks
- **Session Monitoring**: Real-time session tracking

### Metrics:
- User session statistics
- Analysis completion rates  
- System resource usage
- Database performance

## 🔄 Migration from Anonymous Interface

Nếu bạn đã sử dụng anonymous interface trước đây:

1. **Data Migration**: Anonymous session data không được migrate (theo design)
2. **New Registration**: Users cần tạo accounts mới
3. **Updated Workflows**: Sử dụng authenticated workflows cho all features
4. **Port Change**: Interface bây giờ chạy trên port 8501 (thay vì 8502)

---

**Kết luận**: AI CodeScan bây giờ sử dụng exclusively authenticated interface cho better security, user experience, và feature consistency. Tất cả users cần authentication để access hệ thống, đảm bảo proper session management và data isolation. 