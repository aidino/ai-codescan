# 🔐 Hướng Dẫn Test Authentication System

## 📋 Tổng Quan

AI CodeScan Authentication System cung cấp tính năng đăng nhập/đăng ký để quản lý sessions và data của từng user một cách riêng biệt.

## 🚀 Cài Đặt và Khởi Chạy

### 1. Setup Database

```bash
# Initialize database với sample users
python scripts/setup_auth_database.py init

# Hoặc reset database nếu đã có
python scripts/reset_auth_database.py reset
```

### 2. Khởi chạy Web UI

```bash
# Chạy authenticated web UI
python src/main.py auth-web

# Web UI sẽ chạy tại: http://localhost:8502
```

## 👥 Sample Users

Sau khi setup, bạn sẽ có các users sau:

| Username   | Password      | Role  | Email                    |
|------------|---------------|-------|--------------------------|
| admin      | admin123456   | ADMIN | admin@aicodescan.local   |
| test_user  | testpassword  | USER  | test@aicodescan.local    |
| demo       | demopassword  | USER  | demo@aicodescan.local    |

## 🧪 Test Scenarios

### Scenario 1: Login và Logout

1. **Truy cập Web UI**
   - Mở http://localhost:8502
   - Bạn sẽ thấy trang login

2. **Login thành công**
   - Username: `admin`
   - Password: `admin123456`
   - Click "🔐 Đăng nhập"
   - ✅ Được redirect đến dashboard

3. **Kiểm tra UI sau login**
   - Header: Có tên user và button "🚪 Đăng xuất" (màu xanh)
   - Sidebar: Có thông tin user và button "🚪 Logout" 
   - Dashboard: Hiển thị thống kê sessions của user

4. **Logout**
   - **Option 1**: Click "🚪 Đăng xuất" ở header (button chính)
   - **Option 2**: Click "🚪 Logout" ở sidebar
   - ✅ Thấy animation balloons và message "✅ Đăng xuất thành công!"
   - ✅ Được redirect về trang login

### Scenario 2: Register User Mới

1. **Từ trang login**
   - Click tab "📝 Đăng ký"

2. **Điền thông tin registration**
   - Username: `newuser`
   - Email: `newuser@test.com`
   - Password: `newpassword123`
   - Confirm Password: `newpassword123`
   - Click "📝 Tạo tài khoản"

3. **Verify registration**
   - ✅ Thấy message "✅ Tạo tài khoản thành công!"
   - ✅ Tự động login vào account mới

### Scenario 3: Multi-User Sessions

1. **Login với user 1**
   - Login với `admin`
   - Tạo 1 repository analysis session
   - Note session ID

2. **Login với user 2**
   - Logout admin
   - Login với `test_user`
   - Kiểm tra dashboard: Không thấy sessions của admin
   - Tạo session riêng cho test_user

3. **Verify User Isolation**
   - ✅ Mỗi user chỉ thấy sessions của mình
   - ✅ Data hoàn toàn isolated

### Scenario 4: Session Management

1. **Login và tạo sessions**
   - Login với `demo`
   - Click "🆕 Scan mới" → Tạo repository analysis
   - Click "💬 Chat mới" → Tạo chat session

2. **Kiểm tra history**
   - Trong sidebar: Thấy các sessions vừa tạo
   - Click vào session → View history mode

3. **Dashboard metrics**
   - Dashboard hiển thị:
     - Tổng sessions
     - Sessions hoàn thành
     - Repository scans
     - Chat sessions

### Scenario 5: Error Handling

1. **Login sai credentials**
   - Username: `admin`
   - Password: `wrongpassword`
   - ✅ Thấy error: "Invalid username/email or password"

2. **Register với duplicate username**
   - Thử tạo account với username `admin`
   - ✅ Thấy error về duplicate username

3. **Session expiration**
   - Sessions expire sau 24 giờ
   - Sau expire, user bị redirect về login

## 🔍 UI Elements để Kiểm Tra

### Header (Sau Login)
```
🤖 AI CodeScan    |    Xin chào, admin 👋    |    🚪 Đăng xuất
                  |    Role: admin           |    (button xanh)
```

### Sidebar (Sau Login)
```
👤 admin
Role: admin
🚪 Logout                    ← Button logout thứ 2

🧭 Điều hướng
📊 Dashboard
🆕 Scan mới  
💬 Chat mới

📚 Lịch sử Sessions
📊 Scans
💬 Chats

⚙️ Tài khoản
Tổng sessions: X
```

### Login Page
```
🔐 Đăng nhập    |    📝 Đăng ký
(Tab interface)
```

## 🛠️ Database Management

### Reset Database
```bash
# Full reset với backup
python scripts/reset_auth_database.py reset

# Reset without backup
python scripts/reset_auth_database.py reset --no-backup

# Reset without sample users
python scripts/reset_auth_database.py reset --no-users

# Clear data only (keep structure)
python scripts/reset_auth_database.py clear
```

### Backup Database
```bash
# Create backup
python scripts/reset_auth_database.py backup data/ai_codescan.db
```

### List Users
```bash
# Show all users
python scripts/setup_auth_database.py list-users
```

### Create Users
```bash
# Interactive user creation
python scripts/setup_auth_database.py create-user
```

## 🐛 Troubleshooting

### Issue: Không thấy logout button
**Solution**: 
- Button "🚪 Đăng xuất" ở header (màu xanh, full width)
- Button "🚪 Logout" ở sidebar
- Nếu không thấy, refresh page hoặc clear browser cache

### Issue: Login không hoạt động
**Solution**:
```bash
# Check database
python scripts/setup_auth_database.py list-users

# Reset database
python scripts/reset_auth_database.py reset
```

### Issue: Sessions không persistent
**Solution**:
- Check database file: `data/ai_codescan.db`
- Check logs trong `logs/` folder
- Restart web UI

### Issue: Port conflict
**Solution**:
```bash
# Use different port
python src/main.py auth-web --port 8503
```

## 📊 Expected Behavior

### ✅ Successful Test Results

1. **Login Flow**: Smooth transition từ login → dashboard
2. **Logout Flow**: Clear session, balloons animation, redirect to login
3. **User Isolation**: Mỗi user chỉ thấy data của mình
4. **Session Persistence**: Sessions saved across browser restarts
5. **UI Responsiveness**: Fast loading, clear navigation
6. **Error Handling**: Clear error messages, no crashes

### ❌ Red Flags

1. **Data Bleeding**: User A thấy sessions của User B
2. **Login Loops**: Endless redirect giữa login và dashboard
3. **Session Loss**: Sessions disappear sau refresh
4. **No Logout Button**: Không tìm thấy cách logout
5. **Database Errors**: SQLite errors trong logs

## 📝 Test Checklist

- [ ] Database initialization successful
- [ ] Admin user login works
- [ ] Test user login works  
- [ ] New user registration works
- [ ] Logout button visible và functional
- [ ] Session creation works
- [ ] Session history shows correct data
- [ ] User isolation verified
- [ ] Dashboard metrics accurate
- [ ] Error messages helpful
- [ ] No data bleeding between users
- [ ] Sessions persist across restarts

## 🔧 Development Tools

### Check Database Schema
```bash
sqlite3 data/ai_codescan.db ".schema"
```

### View Database Content
```bash
sqlite3 data/ai_codescan.db "SELECT * FROM users;"
sqlite3 data/ai_codescan.db "SELECT * FROM auth_sessions;"
```

### Monitor Logs
```bash
tail -f logs/ai_codescan.log
```

---

**Lưu ý**: Nếu gặp vấn đề gì, hãy check logs trong folder `logs/` và database integrity. Reset database thường giải quyết được hầu hết các vấn đề trong development environment. 