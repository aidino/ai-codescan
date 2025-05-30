# 🔐 AI CodeScan Authentication Testing

## 🚀 Quick Start (1 Phút)

```bash
# Cài đặt và khởi chạy tất cả trong 1 lệnh
python scripts/quick_start_auth.py full
```

## 📱 Test Credentials

| Username   | Password      | Role  |
|------------|---------------|-------|
| admin      | admin123456   | ADMIN |
| test_user  | testpassword  | USER  |
| demo       | demopassword  | USER  |

## 🌐 Web UI: http://localhost:8502

## 🚪 Logout Buttons

Sau khi login, bạn sẽ thấy **2 logout buttons**:

1. **Header**: "🚪 Đăng xuất" (button màu xanh, full width)
2. **Sidebar**: "🚪 Logout" (button xám)

## 🔧 Commands

```bash
# Reset database nếu có lỗi
python scripts/reset_auth_database.py reset

# Khởi chạy lại web UI
python src/main.py auth-web

# Xem users hiện tại
python scripts/setup_auth_database.py list-users
```

## ✅ Test Checklist

- [ ] Login works
- [ ] Logout buttons visible và functional  
- [ ] User sessions isolated
- [ ] Dashboard shows user stats
- [ ] Registration works
- [ ] Error messages clear

## 📚 Detailed Guide

Xem `docs/TESTING_AUTHENTICATION.md` để có hướng dẫn chi tiết.

---

**💡 Tip**: Nếu gặp vấn đề gì, chạy `python scripts/reset_auth_database.py reset` để reset hoàn toàn database. 