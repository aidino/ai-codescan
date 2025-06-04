# 🤖 Hướng dẫn sử dụng AI Repository Chat

## 📋 Tổng quan

**AI Repository Chat** là tính năng mới của AI CodeScan cho phép bạn tương tác với hệ thống phân tích code thông qua giao diện chat thân thiện. Thay vì điền form, bạn chỉ cần trò chuyện với AI assistant để phân tích repository.

---

## 🚀 Bắt đầu sử dụng

### 1. **Truy cập tính năng**
1. Đăng nhập vào AI CodeScan
2. Từ menu chính, chọn **"AI Repository Chat"**
3. Giao diện chatbox sẽ xuất hiện với lời chào từ AI

### 2. **Cung cấp Repository URL**
AI sẽ hỏi bạn muốn phân tích repository nào. Cung cấp URL repository:

```
✅ Các định dạng URL được hỗ trợ:
• https://github.com/username/repository
• https://gitlab.com/username/project  
• https://bitbucket.org/team/repository
• git@github.com:username/repo.git
```

**Ví dụ:**
```
👤 User: https://github.com/django/django
🤖 AI: ✅ Repository hợp lệ và có thể truy cập!
```

---

## 🔐 Xử lý Repository Private

### **Khi nào cần Personal Access Token (PAT)?**
Nếu repository của bạn là private, AI sẽ yêu cầu PAT để truy cập:

```
🤖 AI: 🔒 Repository này có vẻ là private hoặc cần authentication.

🔑 Để truy cập, tôi cần Personal Access Token (PAT):

**Hướng dẫn tạo PAT:**
- GitHub: Settings → Developer settings → Personal access tokens
- GitLab: User Settings → Access Tokens  
- BitBucket: Account settings → App passwords
```

### **Cách cung cấp PAT an toàn:**
1. Tạo PAT từ platform tương ứng
2. Copy PAT và paste vào chat
3. PAT chỉ được lưu trong session hiện tại
4. Tự động xóa sau khi phân tích xong

**⚠️ Lưu ý bảo mật:**
- PAT không được lưu trữ vĩnh viễn
- Chỉ sử dụng trong session hiện tại
- Tự động cleanup sau khi hoàn thành

---

## 📊 Quy trình phân tích

### **1. Xác nhận phân tích**
Sau khi AI xác thực repository, bạn sẽ được hỏi xác nhận:

```
🤖 AI: 🔍 Bạn có muốn tôi bắt đầu phân tích không?
👤 User: có / yes / ok / được / đồng ý
```

### **2. Theo dõi tiến trình**
AI sẽ hiển thị real-time progress:

```
🔄 Bắt đầu phân tích repository...

Đang thực hiện:
1. 📥 Clone repository
2. 🔍 Nhận diện ngôn ngữ lập trình  
3. 🧪 Phân tích static code
4. 🏗️ Phân tích kiến trúc
5. 📊 Tính toán metrics
```

### **3. Xem kết quả**
Kết quả được hiển thị dưới dạng báo cáo chi tiết:

```
✅ Phân tích hoàn tất!

## 📊 Tổng quan Repository
- Repository: django
- Ngôn ngữ: Python (95.2%), JavaScript (3.1%), HTML (1.7%)
- Files phân tích: 1,247
- Lines of code: 284,569
- Quality Score: 87/100

## 🐛 Issues Found
- Tổng issues: 156
- Critical: 3
- Error: 12
- Warning: 141
```

---

## 💬 Tương tác với kết quả

Sau khi có kết quả, bạn có thể hỏi AI về bất kỳ vấn đề nào:

### **🔧 Hỏi về cách sửa lỗi:**
```
👤 User: Cách sửa lỗi security vulnerability?
🤖 AI: 🔧 Gợi ý sửa lỗi:

1. Security vulnerabilities:
   - Update dependencies: pip install --upgrade package-name
   - Check with: safety check hoặc pip-audit
```

### **📖 Giải thích lỗi chi tiết:**
```
👤 User: Giải thích tại sao có lỗi complexity cao?
🤖 AI: 📖 Giải thích các vấn đề:

🧠 Code Complexity Issues:
- Functions có quá nhiều decision points
- Khó test và maintain
- Tăng bug rate
```

### **🚀 Đề xuất cải thiện:**
```
👤 User: Cách cải thiện code
🤖 AI: 🚀 Đề xuất cải thiện cho Repository:

Quality Score hiện tại: 87/100

📋 Priority cao:
- 🚨 Sửa ngay 3 critical issues
- ⚠️ Focus vào việc sửa error issues trước
```

### **📊 Export kết quả:**
```
👤 User: Export kết quả
🤖 AI: 📊 Kết quả đã sẵn sàng export!

Available formats:
- 📄 JSON Report - Chi tiết đầy đủ
- 📋 Summary Report - Tóm tắt chính
- 🔍 Issues Only - Danh sách lỗi
```

---

## 🎯 Các câu lệnh hữu ích

### **Phân tích repository:**
- `https://github.com/user/repo`
- `Phân tích repository này: [URL]`
- `Scan this project: [URL]`

### **Xác nhận/từ chối:**
- **Đồng ý:** `có`, `yes`, `ok`, `được`, `đồng ý`, `bắt đầu`
- **Từ chối:** `không`, `no`, `hủy`, `dừng`

### **Hỏi về kết quả:**
- `Cách sửa lỗi [tên lỗi]?`
- `Giải thích lỗi [type]`
- `Đề xuất cải thiện`
- `Export kết quả`
- `Tại sao có lỗi này?`
- `How to fix [issue]?`

---

## 🛠️ Tính năng nâng cao

### **📈 Theo dõi trạng thái**
Sidebar hiển thị thông tin real-time:
- **Conversation Status:** Trạng thái hiện tại
- **Repository Info:** Thông tin repository đang phân tích
- **Export Results:** Download báo cáo (khi có)

### **🎛️ Controls**
- **🔄 New Chat:** Bắt đầu cuộc hội thoại mới
- **📋 Clear:** Xóa lịch sử chat hiện tại
- **💡 Quick Help:** Hướng dẫn nhanh

### **📊 Export Options**
Khi phân tích hoàn tất, bạn có thể export kết quả:
- **JSON Report:** Dữ liệu đầy đủ cho developers
- **Summary Report:** Báo cáo tóm tắt cho managers
- **Issues Only:** Danh sách lỗi để fix

---

## ❓ Troubleshooting

### **🔧 Các vấn đề thường gặp:**

#### **❌ "Không tìm thấy URL repository hợp lệ"**
**Nguyên nhân:** URL không đúng format hoặc thiếu protocol
**Giải pháp:**
- Đảm bảo URL có `https://` hoặc `git@`
- Kiểm tra spelling của URL
- Sử dụng full URL, không rút gọn

#### **🔒 "Repository có vẻ là private"**
**Nguyên nhân:** Repository cần authentication
**Giải pháp:**
- Tạo Personal Access Token từ platform
- Đảm bảo PAT có quyền đọc repository
- Check PAT chưa expired

#### **⏳ "Phân tích mất quá nhiều thời gian"**
**Nguyên nhân:** Repository quá lớn hoặc mạng chậm
**Giải pháp:**
- Chờ thêm thời gian (repositories lớn cần 5-10 phút)
- Kiểm tra kết nối mạng
- Thử repository nhỏ hơn để test

#### **🚫 "PAT không hợp lệ"**
**Nguyên nhân:** PAT sai hoặc không có quyền
**Giải pháp:**
- Tạo PAT mới với quyền `repo:read`
- Copy paste cẩn thận (không thêm space)
- Đảm bảo PAT chưa expired

---

## 💡 Tips & Best Practices

### **🎯 Để có trải nghiệm tốt nhất:**

1. **Sử dụng repository vừa phải:** Repository với < 100k LOC sẽ phân tích nhanh hơn

2. **Chuẩn bị PAT trước:** Nếu có repository private, tạo PAT trước khi bắt đầu

3. **Đặt câu hỏi cụ thể:** Thay vì "fix lỗi", hỏi "cách sửa security vulnerability"

4. **Sử dụng export:** Download kết quả để tham khảo offline

5. **Thử different repositories:** Test với các loại project khác nhau

### **🔍 Repository types được recommend:**
- **Small projects:** < 50 files, good for testing
- **Medium projects:** 50-500 files, normal analysis
- **Large projects:** > 500 files, có thể mất thời gian

---

## 🚀 Roadmap & Future Features

### **🔮 Tính năng đang phát triển:**
- **Voice Input:** Tương tác bằng giọng nói
- **Multi-repo Analysis:** Phân tích nhiều repositories cùng lúc
- **Team Collaboration:** Chia sẻ kết quả với team
- **Custom Analysis Rules:** Tự định nghĩa rules phân tích

### **💡 Đề xuất cải tiến:**
Nếu bạn có ý tưởng cải tiến, sử dụng **User Feedback** để gửi suggestions!

---

## 📞 Hỗ trợ

### **🆘 Cần trợ giúp?**
- **Quick Help:** Click vào 💡 trong sidebar
- **User Feedback:** Gửi feedback qua tính năng trong app
- **Documentation:** Check PLANNING.md cho technical details

### **🐛 Báo lỗi:**
1. Ghi lại steps to reproduce
2. Screenshot error message
3. Submit qua User Feedback với type "Bug Report"

---

*📅 **Last Updated:** December 15, 2024*  
*🔄 **Version:** AI CodeScan v1.1* 