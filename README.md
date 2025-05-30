# AI CodeScan 🔍🤖

AI-powered code review assistant with multi-agent architecture for comprehensive code analysis across multiple programming languages.

## 🌟 Features

- **Multi-Agent Architecture**: Orchestrated agents for different analysis tasks
- **Multi-Language Support**: Python, Java, Dart, Kotlin (planned)
- **Graph-Based Code Knowledge**: Neo4j-powered code knowledge graph (CKG)
- **AI-Powered Analysis**: LLM integration for intelligent code insights
- **Web Interface**: Modern Streamlit-based UI
- **Docker-Ready**: Containerized deployment with Docker Compose
- **Extensible**: Plugin architecture for custom analysis tools

## 🚀 Quick Start

### Prerequisites

- Python 3.12+ 
- Docker & Docker Compose
- Poetry (recommended) or pip

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ai-codescan
./scripts/setup.sh
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your OpenAI API key
nano .env
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# Or start only Neo4j and Redis
docker-compose up neo4j redis -d
```

### 4. Run Application

```bash
# Web Interface (recommended)
poetry run python src/main.py web

# CLI Interface
poetry run python src/main.py analyze --url https://github.com/user/repo
```

### 5. Access Interfaces

- **AI CodeScan Web UI**: http://localhost:8501
- **Neo4j Browser**: http://localhost:7474 (neo4j/ai_codescan_password)
- **Redis**: localhost:6379

## 🏗️ Architecture

### Agent Teams

1. **Orchestrator Agent**: Central coordination and workflow management
2. **Interaction & Tasking Team**: Web UI and user interaction
3. **Data Acquisition Team**: Repository cloning and preparation
4. **CKG Operations Team**: Code knowledge graph construction
5. **Code Analysis Team**: Static analysis and architectural insights
6. **LLM Services Team**: AI-powered analysis and explanations
7. **Synthesis & Reporting Team**: Result aggregation and presentation

### Technology Stack

- **Backend**: Python 3.12, Poetry, Pydantic
- **Web UI**: Streamlit
- **Database**: Neo4j (graph), Redis (cache)
- **LLM**: OpenAI GPT-4
- **Git Operations**: GitPython, PyGithub
- **Code Analysis**: Flake8, Pylint, Black, MyPy
- **Containerization**: Docker, Docker Compose

## 📋 Development Status

### ✅ Completed (v0.1.0)

- [x] Task 0.1: Comprehensive design documentation
- [x] Task 0.2: Core development environment setup
  - Python 3.12.9 with Poetry
  - Docker containerization
  - Neo4j and Redis integration
  - CLI framework with Click
  - Project structure and dependencies

### 🚧 In Progress

- [ ] Task 0.3: Agent framework research and selection
- [ ] Task 0.4: Project structure refinement  
- [ ] Task 0.5-0.7: Docker and Neo4j optimization

### 📋 Roadmap

- **Phase 1**: Basic Python analysis with Streamlit UI
- **Phase 2**: Multi-language support and architectural analysis
- **Phase 3**: LLM integration and PR analysis
- **Phase 4**: Advanced diagramming and UX improvements
- **Phase 5**: Research and continuous improvements

## 🛠️ Development

### Environment Setup

```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Run tests
poetry run pytest

# Code formatting
poetry run black src/
poetry run isort src/

# Type checking
poetry run mypy src/
```

### Testing

```bash
# Run all tests
poetry run python src/main.py test

# Test Neo4j connection
poetry run python scripts/test_neo4j.py

# Test specific component
poetry run pytest tests/unit/test_orchestrator.py
```

### Docker Development

```bash
# Build and run
docker-compose up --build

# Run only specific services
docker-compose up neo4j redis -d

# View logs
docker-compose logs -f ai-codescan

# Clean up
docker-compose down -v
```

## 📖 Usage Examples

### CLI Usage

```bash
# Analyze a repository
poetry run python src/main.py analyze --url https://github.com/user/repo

# Review a Pull Request
poetry run python src/main.py review-pr --url https://github.com/user/repo --pr-id 123

# Launch web interface
poetry run python src/main.py web

# Show version
poetry run python src/main.py version
```

### Web Interface

1. Navigate to http://localhost:8501
2. Enter repository URL
3. Select analysis options
4. View comprehensive results

## 🔧 Configuration

Key configuration options in `config.py`:

```python
# OpenAI Configuration
OPENAI_API_KEY = "your-api-key"
OPENAI_MODEL = "gpt-4"

# Neo4j Configuration  
NEO4J_URI = "bolt://localhost:7687"
NEO4J_PASSWORD = "ai_codescan_password"

# Analysis Settings
MAX_REPOSITORY_SIZE_MB = 500
ANALYSIS_TIMEOUT_SECONDS = 1800
```

## 📁 Project Structure

```
ai-codescan/
├── src/                    # Source code
│   ├── core/              # Core orchestration
│   ├── agents/            # Agent implementations
│   └── main.py           # CLI entry point
├── tests/                 # Test suites
├── docker/               # Docker configurations
├── scripts/              # Utility scripts
├── docs/                 # Documentation
├── temp_repos/           # Temporary repository storage
└── logs/                 # Application logs
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run quality checks
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check [docs/DESIGN.md](docs/DESIGN.md) for architecture details
- **Issues**: Track progress in [TASK.md](TASK.md)
- **Problems**: See [ISSUES.md](ISSUES.md) for known issues and solutions

## 🎯 Vision

AI CodeScan aims to revolutionize code review processes by combining:
- Advanced static analysis
- AI-powered insights  
- Architectural understanding
- Interactive visualizations
- Multi-language support

Our goal is to make code review more efficient, comprehensive, and accessible to development teams of all sizes. 
