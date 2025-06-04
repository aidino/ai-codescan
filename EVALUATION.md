# 🧪 Kịch bản Manual Test cho AI CodeScan Web UI

Dựa trên phân tích codebase và tài liệu thiết kế, dưới đây là danh sách các kịch bản test manual để kiểm tra tất cả tính năng của web UI:

## 🔐 **Authentication & User Management**

### Test Case A1: Đăng nhập hệ thống
**Mục đích:** Kiểm tra chức năng đăng nhập cơ bản
**Bước thực hiện:**
1. Truy cập `http://localhost:8501`
2. Nhập username: `admin`, password: `admin123456`
3. Click "🔐 Đăng nhập"
4. **Kết quả mong đợi:** Chuyển đến dashboard chính, hiển thị thông tin user ở sidebar

### Test Case A2: Đăng ký tài khoản mới
**Mục đích:** Kiểm tra chức năng tạo tài khoản
**Bước thực hiện:**
1. Tại trang login, click "📝 Đăng ký tài khoản mới"
2. Nhập thông tin: username, email, password, confirm password
3. Chọn role (nếu có)
4. Click "🚀 Tạo tài khoản"
5. **Kết quả mong đợi:** Hiển thị thông báo thành công, tự động đăng nhập

### Test Case A3: Đăng xuất
**Mục đích:** Kiểm tra chức năng đăng xuất
**Bước thực hiện:**
1. Sau khi đăng nhập, click "🚪 Đăng xuất" ở sidebar hoặc header
2. **Kết quả mong đợi:** Quay lại trang login, xóa session state

## 🏠 **Dashboard & Navigation**

### Test Case B1: Dashboard chính
**Mục đích:** Kiểm tra hiển thị dashboard
**Bước thực hiện:**
1. Đăng nhập thành công
2. Quan sát dashboard chính
3. **Kết quả mong đợi:** 
   - Hiển thị thống kê user
   - Recent activities (nếu có)
   - Quick action buttons

### Test Case B2: Navigation sidebar
**Mục đích:** Kiểm tra điều hướng qua sidebar
**Bước thực hiện:**
1. Click từng mục trong sidebar:
   - 🏠 Dashboard
   - 🔍 Repository Analysis  
   - 🔄 Pull Request Review
   - 💬 Q&A Assistant
   - 📊 Code Diagrams
   - 📝 User Feedback
   - 📈 Session History
2. **Kết quả mong đợi:** Mỗi click chuyển đến view tương ứng

## 📊 **Repository Analysis**

###  Test Caset sC1: Repository analysis - Public repo
**Mục đích:** Kiểm tra phân tích repository công khai
**Bước thực hiện:**
1. Click "🔍 Repository Analysis" trong sidebar
2. Nhập URL: `https://github.com/python/cpython`
3. Trong Advanced Options:
   - Chọn force language: "Python"
   - Check "Phân tích kiến trúc"
   - Check "Phân tích CKG"
4. Click "🔍 Phân tích Repository"
5. **Kết quả mong đợi:** 
   - Hiển thị progress bar
   - Kết quả phân tích với tabs: Summary, Linting, Architecture, Charts
   - Có thể export kết quả

### Test Case C2: Repository analysis - với PAT
**Mục đích:** Kiểm tra phân tích repository private với PAT
**Bước thực hiện:**
1. Click "🔍 Repository Analysis"
2. Nhập URL repository private (nếu có)
3. Check "🔑 Sử dụng Personal Access Token"
4. Chọn platform (GitHub/GitLab/BitBucket)
5. Nhập PAT và username
6. Click "💾 Lưu" để lưu PAT
7. Click "🔍 Phân tích Repository"
8. **Kết quả mong đợi:** PAT được lưu trong session, phân tích thành công

### Test Case C3: PAT Management
**Mục đích:** Kiểm tra quản lý PAT trong session
**Bước thực hiện:**
1. Sau khi lưu PAT ở C2, thực hiện analysis khác
2. Check "🔑 Sử dụng Personal Access Token"
3. Chọn "Sử dụng PAT đã lưu"
4. **Kết quả mong đợi:** Hiển thị danh sách PAT đã lưu, có thể chọn và sử dụng

## 🔄 **Pull Request Review**

### Test Case D1: PR Review
**Mục đích:** Kiểm tra tính năng review Pull Request
**Bước thực hiện:**
1. Click "🔄 Pull Request Review"
2. Nhập repository URL và PR ID
3. Chọn platform
4. Click "🔍 Phân tích PR"
5. **Kết quả mong đợi:** Hiển thị tóm tắt PR, diff analysis, impact assessment

## 💬 **Q&A Assistant**

### Test Case E1: Code Q&A
**Mục đích:** Kiểm tra tính năng hỏi đáp về code
**Bước thực hiện:**
1. Click "💬 Q&A Assistant"
2. Nhập context repository (tùy chọn)
3. Nhập câu hỏi: "What is the purpose of this class?"
4. Click "💬 Gửi câu hỏi"
5. **Kết quả mong đợi:** Hiển thị phản hồi AI (mock response trong v1.0)

### Test Case E2: Chat History
**Mục đích:** Kiểm tra lưu trữ lịch sử chat
**Bước thực hiện:**
1. Tiếp tục từ E1, hỏi thêm vài câu
2. Quan sát chat history được lưu
3. **Kết quả mong đợi:** Tất cả tin nhắn được hiển thị theo thứ tự thời gian

## 📊 **Code Diagrams**

### Test Case F1: Class Diagram Generation
**Mục đích:** Kiểm tra tính năng sinh sơ đồ code
**Bước thực hiện:**
1. Click "📊 Code Diagrams"
2. Nhập repository URL
3. Click "📥 Load Repository"
4. Nhập target element (class name)
5. Chọn diagram type: "Class Diagram"
6. Chọn format: "PlantUML"
7. Click "🎨 Generate Diagram"
8. **Kết quả mong đợi:** Hiển thị mã PlantUML và preview sơ đồ

### Test Case F2: Multiple Diagram Formats
**Mục đích:** Kiểm tra các format sơ đồ khác nhau
**Bước thực hiện:**
1. Thực hiện F1 với format "Mermaid"
2. So sánh kết quả với PlantUML
3. **Kết quả mong đợi:** Cả hai format đều generate thành công

## 📝 **User Feedback**

### Test Case G1: Submit Feedback
**Mục đích:** Kiểm tra hệ thống feedback
**Bước thực hiện:**
1. Click "📝 User Feedback"
2. Tab "💬 Gửi phản hồi":
   - Rating: 4/5 stars
   - Satisfaction: "Satisfied"
   - Feedback type: "Feature Request"
   - Feature area: "Repository Analysis"
   - Nhập title và description
3. Click "🚀 Gửi phản hồi"
4. **Kết quả mong đợi:** Hiển thị thông báo thành công, balloons animation

### Test Case G2: Feedback Analytics
**Mục đích:** Kiểm tra thống kê feedback
**Bước thực hiện:**
1. Tab "📊 Thống kê"
2. Quan sát các metrics và charts
3. **Kết quả mong đợi:** Hiển thị thống kê rating, satisfaction levels, feedback trends

### Test Case G3: Improvement Roadmap
**Mục đích:** Kiểm tra roadmap cải tiến
**Bước thực hiện:**
1. Tab "🔧 Cải tiến"
2. Click "🤖 Phân tích phản hồi"
3. Quan sát improvement suggestions
4. **Kết quả mong đợi:** Hiển thị danh sách đề xuất cải tiến dựa trên feedback

## 📈 **Session History**

### Test Case H1: Session History View
**Mục đích:** Kiểm tra xem lịch sử sessions
**Bước thực hiện:**
1. Click "📈 Session History"
2. Quan sát danh sách sessions đã tạo
3. Click "👁️ Xem chi tiết" trên một session
4. **Kết quả mong đợi:** Chuyển sang history view, hiển thị đầy đủ thông tin session

### Test Case H2: Session Management
**Mục đố:** Kiểm tra quản lý sessions
**Bước thực hiện:**
1. Tại session history, thử filter theo type
2. Quan sát session statistics
3. **Kết quả mong đợi:** Filter hoạt động đúng, stats chính xác

## 🎨 **UI/UX & Performance**

### Test Case I1: Responsive Design
**Mục đích:** Kiểm tra giao diện responsive
**Bước thực hiện:**
1. Thay đổi kích thước cửa sổ browser
2. Kiểm tra trên mobile view
3. **Kết quả mong đợi:** UI adapt tốt với các screen size

### Test Case I2: Loading Performance
**Mục đích:** Kiểm tra hiệu suất loading
**Bước thực hiện:**
1. Đo thời gian load các trang
2. Kiểm tra progress indicators
3. **Kết quả mong đợi:** Load time hợp lý, có loading feedback

### Test Case I3: Error Handling
**Mục đích:** Kiểm tra xử lý lỗi
**Bước thực hiện:**
1. Nhập URL repository không hợp lệ
2. Nhập PAT sai format
3. Gửi form với thông tin thiếu
4. **Kết quả mong đợi:** Hiển thị error messages rõ ràng, không crash

## 🔧 **Advanced Features**

### Test Case J1: Multi-language Support
**Mục đích:** Kiểm tra hỗ trợ nhiều ngôn ngữ
**Bước thực hiện:**
1. Analyze repository có nhiều ngôn ngữ (Java + Python)
2. Kiểm tra force language override
3. **Kết quả mong đợi:** Detect đúng languages, results phù hợp

### Test Case J2: Session Persistence
**Mục đích:** Kiểm tra lưu trữ session state
**Bước thực hiện:**
1. Thực hiện một analysis
2. Refresh browser
3. Kiểm tra session state có được preserve
4. **Kết quả mong đợi:** Session state được maintain

### Test Case J3: Export Functionality
**Mục đích:** Kiểm tra export kết quả
**Bước thực hiện:**
1. Sau khi có analysis results
2. Click "📊 Export Results"
3. Thử export JSON và CSV
4. **Kết quả mong đợi:** Files được download với format đúng

## 🚀 **Integration Tests**

### Test Case K1: End-to-end Workflow
**Mục đích:** Kiểm tra luồng hoàn chỉnh
**Bước thực hiện:**
1. Đăng nhập → Repository Analysis → View Results → Export → Q&A → Feedback
2. **Kết quả mong đợi:** Tất cả steps hoạt động liền mạch

### Test Case K2: Multiple Sessions
**Mục đích:** Kiểm tra multiple concurrent sessions
**Bước thực hiện:**
1. Tạo repository analysis session
2. Tạo Q&A session
3. Chuyển đổi giữa các sessions
4. **Kết quả mong đợi:** Mỗi session maintain state riêng biệt

---

## 📋 **Checklist cho Manual Testing**

### Trước khi test:
- [ ] Chạy `docker-compose up -d` để start services
- [ ] Verify `http://localhost:8501` accessible  
- [ ] Run `python src/main.py setup-auth` để tạo database
- [ ] Verify Neo4j tại `http://localhost:7474`

### Trong quá trình test:
- [ ] Document screenshots cho các bugs
- [ ] Note performance issues
- [ ] Test trên multiple browsers (Chrome, Firefox)
- [ ] Kiểm tra browser console cho JavaScript errors
- [ ] Monitor Docker logs cho backend errors

### Sau khi test:
- [ ] Compile bug report với steps to reproduce
- [ ] Prioritize bugs theo severity
- [ ] Verify fixes với re-testing
- [ ] Update test cases dựa trên changes

---

## 🎯 **Test Repository Suggestions**

Để test hiệu quả, sử dụng các repository sau:

### Small/Simple Repos (để test nhanh):
- `https://github.com/python/hello-world` - Python đơn giản
- `https://github.com/spring-projects/spring-petclinic` - Java Spring
- `https://github.com/flutter/samples` - Flutter/Dart

### Medium Repos (để test performance):
- `https://github.com/django/django` - Python framework lớn
- `https://github.com/JetBrains/kotlin` - Kotlin language
- `https://github.com/flutter/flutter` - Flutter framework

### Multi-language Repos:
- `https://github.com/microsoft/vscode` - TypeScript + others
- `https://github.com/apache/spark` - Scala + Java + Python

---

## 📝 **Bug Report Template**

```
**Bug ID:** [Unique identifier]
**Test Case:** [Reference test case]
**Severity:** [Critical/High/Medium/Low]
**Browser:** [Chrome/Firefox/Safari/Edge]
**Environment:** [Docker/Local/Other]

**Steps to Reproduce:**
1. 
2. 
3. 

**Expected Result:**
[What should happen]

**Actual Result:**
[What actually happened]

**Screenshots/Logs:**
[Attach relevant media]

**Workaround:**
[If any temporary solution exists]
```

---

Những kịch bản test này sẽ giúp bạn kiểm tra toàn diện tất cả tính năng của AI CodeScan Web UI và phát hiện các issues để fix cùng Cursor AI. 