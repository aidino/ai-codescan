# 🤖 AI CodeScan

AI-powered code review assistant với multi-agent architecture

## ✨ Features

- 🔍 **Automated Code Analysis**: Python repository analysis với static tools
- 🌐 **Modern Web UI**: Interactive Streamlit interface
- 🤖 **Multi-Agent Architecture**: LangGraph-based agent orchestration
- 📊 **Knowledge Graph**: Neo4j-powered code relationship mapping
- 🧠 **LLM Integration**: AI-powered insights và explanations
- 🐳 **Containerized**: Docker-first development và deployment

## ⚙️ Environment Configuration

### Step 1: Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env file với your settings
nano .env  # or vim, code, etc.
```

### Step 2: Required Configuration

**🔑 OpenAI API Key (Required)**
```bash
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

**🔒 Security Keys (Auto-generated)**
```bash
# These are already generated in .env, change in production:
SECRET_KEY=<random-secure-key>
PAT_ENCRYPTION_KEY=<random-secure-key>
```

### Step 3: Database Configuration (Auto-configured)

Docker Compose sẽ tự động setup:
- **Neo4j**: `bolt://localhost:7687` (neo4j/ai_codescan_password)
- **Redis**: `localhost:6379` (no password)

### Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key cho LLM features | - | ✅ |
| `AI_CODESCAN_ENV` | Environment mode | development | ❌ |
| `NEO4J_PASSWORD` | Neo4j database password | ai_codescan_password | ❌ |
| `MAX_REPOSITORY_SIZE_MB` | Max repo size limit | 500 | ❌ |
| `CLONE_TIMEOUT_SECONDS` | Git clone timeout | 300 | ❌ |

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- OpenAI API Key

### Docker (Recommended)

```bash
# 1. Clone repository
git clone <repository-url>
cd ai-codescan

# 2. Setup environment (see Environment Configuration section above)
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Start services
chmod +x scripts/setup.sh
./scripts/setup.sh

# Or manually:
docker-compose up --build -d
```

**Access Applications**:
- 🔐 Authenticated Web UI: http://localhost:8501 (admin/admin123456)
- 📊 Neo4j Browser: http://localhost:7474 (neo4j/ai_codescan_password)

### Local Development

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run authenticated web interface
python src/main.py web
```

## 📋 Requirements

- Python 3.12+
- Docker & Docker Compose
- Git

## 🏗️ Architecture

### Multi-Agent System

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

### Agent Teams

1. **🎯 Orchestrator**: Central workflow coordination
2. **💻 Interaction & Tasking**: Web UI và user interaction  
3. **📥 Data Acquisition**: Repository cloning và preparation
4. **🕸️ CKG Operations**: Code knowledge graph construction
5. **🔍 Code Analysis**: Static analysis và architectural insights
6. **🧠 LLM Services**: AI-powered analysis và explanations
7. **📊 Synthesis & Reporting**: Result aggregation và presentation

## 🛠️ Tech Stack

- **Frontend**: Streamlit, HTML/CSS, JavaScript
- **Backend**: Python 3.12, pip, Pydantic
- **Database**: Neo4j Community, Redis
- **AI/ML**: OpenAI API, LangChain, LangGraph
- **DevOps**: Docker, Docker Compose
- **Code Analysis**: Flake8, Pylint, MyPy, Black
- **Version Control**: Git, GitPython, PyGithub

## 💻 Development

### Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Activate virtual environment (optional)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Run tests
pytest

# Code formatting
black src/
isort src/

# Type checking
mypy src/
```

### Testing

```bash
# Run all tests
python src/main.py test

# Test Neo4j connection
python scripts/test_neo4j.py

# Test specific modules
pytest tests/unit/test_orchestrator.py
```

### Docker Development

```bash
# Build and run
docker-compose up --build

# View logs
docker-compose logs -f ai-codescan

# Execute commands in container
docker-compose exec ai-codescan bash

# Clean up
docker-compose down -v
```

## 📖 Usage

### Command Line Interface

```bash
# Repository analysis
python src/main.py analyze --url https://github.com/user/repo

# PR review  
python src/main.py review-pr --url https://github.com/user/repo --pr-id 123

# Web interface
python src/main.py web

# Version info
python src/main.py version
```

### Web Interface

1. 🔐 Navigate to http://localhost:8501 và login với default admin account
2. 👤 **Default Login**: username=`admin`, password=`admin123456`
3. 📝 Choose analysis type:
   - **Repository Review**: Full codebase analysis
   - **PR Review**: Pull request analysis  
   - **Code Q&A**: Interactive code questions
4. 🔗 Enter repository URL (GitHub, GitLab, BitBucket)
5. ⚙️ Configure analysis options
6. 📊 Review results with interactive charts và exports
7. 📚 Access your session history và user dashboard

## 🎯 Supported Languages

- ✅ **Python**: Flake8, Pylint, MyPy, Black
- 🚧 **Java**: Checkstyle, PMD (planned)
- 🚧 **Dart**: Dart Analyzer (planned)  
- 🚧 **Kotlin**: Detekt, Ktlint (planned)

## 🗃️ Database Schema

- **Neo4j**: Code Knowledge Graph (CKG)
  - Nodes: Files, Classes, Functions, Variables
  - Relationships: IMPORTS, CALLS, DEFINES, INHERITS
- **Redis**: Session management, caching

## 📈 Development Status

### ✅ Completed

- ✅ **Task 0.1-0.7**: Project foundation và Docker setup
- ✅ **Task 1.1**: LangGraph orchestrator implementation
- ✅ **Task 1.2**: Complete Streamlit Web UI với 4 agents
- ✅ **Docker Infrastructure**: Fixed dependency issues, all containers healthy

### 🚧 In Progress

- 🔄 **Task 1.3**: Data Acquisition team implementation

### 📋 Roadmap

- **Phase 1**: Basic Python analysis with Web UI ✅
- **Phase 2**: Multi-language support và architectural analysis
- **Phase 3**: LLM integration và PR analysis
- **Phase 4**: Advanced diagramming và UX improvements
- **Phase 5**: Research và continuous improvements

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Follow coding standards (Black, isort, mypy)
4. Write tests cho new features
5. Submit pull request

## 📄 License

[Your chosen license]

## 🆘 Support

- 📚 Documentation: [Link to docs]
- 🐛 Issues: [GitHub Issues]
- 💬 Discussions: [GitHub Discussions]

---

**Made with ❤️ for better code quality**
