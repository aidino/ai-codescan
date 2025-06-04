# 🤖 AI CodeScan

AI-powered code review assistant với kiến trúc multi-agent

## ✨ Tính năng chính

- 🔍 **Phân tích Code tự động**: Phân tích Python repository với static analysis tools
- 🌐 **Giao diện Web hiện đại**: Interactive Streamlit interface với enhanced components
- 🤖 **Kiến trúc Multi-Agent**: LangGraph-based agent orchestration
- 📊 **Knowledge Graph**: Neo4j-powered code relationship mapping
- 🧠 **Tích hợp LLM**: AI-powered insights và explanations
- 🐳 **Container hóa**: Docker-first development và deployment

## 🚀 Cài đặt nhanh

### Yêu cầu hệ thống

- Python 3.12+
- Docker & Docker Compose
- OpenAI API Key

### Cài đặt với Docker (Khuyến nghị)

```bash
# 1. Clone repository
git clone <repository-url>
cd ai-codescan

# 2. Setup environment
cp .env.example .env
# Chỉnh sửa .env và thêm OPENAI_API_KEY của bạn

# 3. Khởi động services
chmod +x scripts/setup.sh
./scripts/setup.sh

# Hoặc chạy thủ công:
docker-compose up --build -d
```

**Truy cập ứng dụng**:
- 🔐 Web UI: http://localhost:8501 (admin/admin123456)
- 📊 Neo4j Browser: http://localhost:7474 (neo4j/ai_codescan_password)

### Cài đặt cho Development

```bash
# 1. Setup environment
cp .env.example .env
# Chỉnh sửa .env và thêm OPENAI_API_KEY

# 2. Cài đặt dependencies
pip install -r requirements.txt

# 3. Chạy web interface
python src/main.py web
```

## ⚙️ Cấu hình Environment

### Biến môi trường bắt buộc

```bash
# .env file
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

### Biến môi trường tùy chọn

| Variable | Mô tả | Mặc định |
|----------|-------|----------|
| `AI_CODESCAN_ENV` | Environment mode | development |
| `NEO4J_PASSWORD` | Neo4j password | ai_codescan_password |
| `MAX_REPOSITORY_SIZE_MB` | Giới hạn kích thước repo | 500 |
| `CLONE_TIMEOUT_SECONDS` | Timeout clone Git | 300 |

## 💻 Hướng dẫn sử dụng

### 1. Web Interface (Khuyến nghị)

1. **Truy cập**: http://localhost:8501
2. **Đăng nhập**: username=`admin`, password=`admin123456`
3. **Chọn loại phân tích**:
   - **Repository Review**: Phân tích toàn bộ codebase
   - **PR Review**: Phân tích Pull Request
   - **Code Q&A**: Hỏi đáp về code
4. **Nhập URL**: GitHub, GitLab, BitBucket repository
5. **Xem kết quả**: Interactive charts và báo cáo chi tiết

### 2. Command Line Interface

```bash
# Phân tích repository
python src/main.py analyze --url https://github.com/user/repo

# Review Pull Request
python src/main.py review-pr --url https://github.com/user/repo --pr-id 123

# Khởi động web interface
python src/main.py web

# Kiểm tra version
python src/main.py version
```

## 🏗️ Kiến trúc hệ thống

### Multi-Agent Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Interaction &  │    │   Orchestrator   │    │ Data Acquisition│
│     Tasking     │◄──►│      Agent       │◄──►│     Team        │
│   (Web UI)      │    │   (LangGraph)    │    │  (Git Ops)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
        ┌──────────────┐ ┌─────────────┐ ┌──────────────┐
        │ CKG Operations│ │Code Analysis│ │ LLM Services │
        │   (Neo4j)    │ │ (Linting)   │ │  (OpenAI)    │
        └──────────────┘ └─────────────┘ └──────────────┘
                                │
                        ┌───────▼────────┐
                        │ Synthesis &    │
                        │   Reporting    │
                        └────────────────┘
```

### Các Agent Team

1. **🎯 Orchestrator**: Điều phối workflow trung tâm
2. **💻 Interaction & Tasking**: Web UI và tương tác người dùng
3. **📥 Data Acquisition**: Clone repository và chuẩn bị dữ liệu
4. **🕸️ CKG Operations**: Xây dựng Code Knowledge Graph
5. **🔍 Code Analysis**: Static analysis và architectural insights
6. **🧠 LLM Services**: AI-powered analysis và explanations
7. **📊 Synthesis & Reporting**: Tổng hợp và trình bày kết quả

## 🛠️ Công nghệ sử dụng

- **Frontend**: Streamlit, Enhanced Components (streamlit-aggrid, streamlit-ace, streamlit-option-menu)
- **Backend**: Python 3.12, FastAPI, Pydantic
- **Database**: Neo4j Community, Redis
- **AI/ML**: OpenAI API, LangChain, LangGraph
- **DevOps**: Docker, Docker Compose
- **Code Analysis**: Flake8, Pylint, MyPy, Black
- **Version Control**: Git, GitPython, PyGithub

## 🎯 Ngôn ngữ hỗ trợ

- ✅ **Python**: Flake8, Pylint, MyPy, Black (Hoàn thành)
- 🚧 **Java**: Checkstyle, PMD (Đang phát triển)
- 🚧 **Dart**: Dart Analyzer (Đang phát triển)
- 🚧 **Kotlin**: Detekt, Ktlint (Đang phát triển)

## 🧪 Testing

```bash
# Chạy all tests
python src/main.py test

# Test connection
python scripts/test_neo4j.py

# Test specific modules
pytest tests/unit/ tests/integration/

# Code formatting
black src/ tests/
isort src/ tests/

# Type checking
mypy src/
```

## 📚 Tài liệu

Xem thêm tài liệu chi tiết trong thư mục `docs/`:
- `PLANNING.md`: Kiến trúc hệ thống và planning
- `DESIGN.md`: Thiết kế chi tiết toàn diện
- `Task_4_4_Implementation_Guide.md`: Hướng dẫn Enhanced Components

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📞 Support

Nếu gặp vấn đề, hãy tạo issue trong GitHub repository.
