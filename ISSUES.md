# **AI CodeScan - Issues và Solutions Tracking**

Ngày tạo: 30 tháng 5, 2025  
Tên dự án: AI CodeScan  
Phiên bản: 1.0

## **Mục đích của File này**

File này theo dõi các vấn đề đã gặp phải trong quá trình phát triển và các giải pháp đã được áp dụng để giải quyết chúng. Điều này giúp đảm bảo tính nhất quán trong việc xử lý vấn đề và tránh lặp lại những sai lầm đã biết.

---

## **Issue #001: Task 0.1 - DESIGN.md Incomplete Structure**

**ISSUE:**
Tài liệu DESIGN.md ban đầu có cấu trúc chưa hoàn chỉnh:
- Mục lục có bookmark reference bị lỗi (#bookmark=id.ypdlsqmn5jhd)
- Thiếu chi tiết về protocols và APIs nội bộ
- Thiếu phần error handling và security considerations
- Thiếu chiến lược deployment và testing

**RESOLVE:**
1. Sửa lỗi mục lục và loại bỏ bookmark reference không hợp lệ
2. Bổ sung Phần V: Protocols và APIs Nội bộ Chi tiết với:
   - Task Definition Protocol (TDP)
   - Agent State Communication Protocol (ASCP) 
   - LLMServiceRequest/Response Protocol (LSRP)
   - ProjectDataContext Schema (PDCS)
   - CKG Query API Specification
3. Bổ sung Phần VI: Error Handling và Security Considerations
4. Bổ sung Phần VII: Deployment và Scaling Strategy
5. Bổ sung Phần VIII: Testing Strategy và Quality Assurance

**Status:** ✅ RESOLVED - Task 0.1 hoàn thành

---

## **Potential Issues và Preventive Measures**

### **Issue Category: Docker & Containerization**

**POTENTIAL ISSUE:**
Khó khăn trong việc tích hợp các parser ngôn ngữ khác nhau (Java, Kotlin, Dart) với Python main application.

**PREVENTIVE MEASURES:**
- Thiết kế microservices architecture cho từng parser
- Sử dụng Docker containers riêng biệt cho mỗi ngôn ngữ
- Định nghĩa REST API chuẩn cho communication giữa parser services
- Implement health checks và graceful degradation

### **Issue Category: Performance & Scalability**

**POTENTIAL ISSUE:**  
Hiệu năng CKG có thể chậm với các repository lớn (> 100k LOC).

**PREVENTIVE MEASURES:**
- Implement incremental CKG updates
- Sử dụng indexing strategies cho Neo4j
- Implement caching layer với Redis
- Monitor performance metrics và set up alerts

### **Issue Category: Security**

**POTENTIAL ISSUE:**
PAT security và data privacy concerns.

**PREVENTIVE MEASURES:**
- Implement encryption cho PAT storage
- Set up automatic PAT cleanup
- Add audit logging cho sensitive operations
- Implement rate limiting và input validation

### **Issue Category: External Dependencies**

**POTENTIAL ISSUE:**
LLM API rate limits và service availability.

**PREVENTIVE MEASURES:**
- Implement exponential backoff retry strategy
- Add circuit breaker pattern
- Support multiple LLM providers
- Implement graceful degradation khi LLM không available

### **Docker Build Issues**

#### **Issue 1: Poetry Dependencies Installation Failed in Docker**

**ISSUE:**
Poetry không thể install dependencies trong Docker container, đặc biệt là module `click` và các dependencies khác. Lỗi `ModuleNotFoundError: No module named 'click'` xảy ra khi chạy application.

**Symptoms:**
- Docker build thành công nhưng Python modules không được install
- Container restart liên tục do dependency missing
- Health checks fail do modules không tồn tại
- `poetry install` command chạy nhưng không install packages vào system Python

**ROOT CAUSE:**
- Poetry version compatibility issues với Python 3.12
- Virtual environment configuration conflicts trong Docker
- Poetry cache và lock file synchronization problems

**SOLUTION:**
Chuyển đổi từ Poetry sang pip với requirements.txt:

1. **Tạo requirements.txt** từ pyproject.toml dependencies:
```bash
# Tạo file requirements.txt với tất cả dependencies
# Core packages: streamlit, neo4j, gitpython, openai, langchain, etc.
```

2. **Simplify Dockerfile** loại bỏ Poetry:
```dockerfile
# Thay thế Poetry setup
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Verify installation
RUN python -c "import click; print('✅ click installed successfully')"
RUN python -c "import streamlit; print('✅ streamlit installed successfully')"
```

3. **Update docker-compose.yml** nếu cần thiết để phù hợp với new Dockerfile

**VERIFICATION:**
- All containers start healthy: ✅
- Streamlit accessible at localhost:8501: ✅  
- Dependencies properly installed: ✅
- No module import errors: ✅

**PREVENTION:**
- Use pip với requirements.txt cho Docker environments
- Keep Poetry cho local development nếu muốn
- Always verify critical imports trong Dockerfile
- Use explicit package versions trong requirements.txt

---

## **Future Issue Tracking Template**

```