#!/bin/bash

# AI CodeScan - Setup Script
# This script sets up the development environment for AI CodeScan

set -e  # Exit on any error

echo "🚀 AI CodeScan - Development Environment Setup"
echo "=============================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "⚠️  Poetry is not installed. Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "✅ Dependencies check passed"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ .env file created. Please edit it with your actual values."
    else
        echo "⚠️  .env.example not found. Creating basic .env file..."
        cat > .env << EOF
# AI CodeScan Environment Configuration
OPENAI_API_KEY=your_openai_api_key_here
AI_CODESCAN_ENV=development
NEO4J_PASSWORD=ai_codescan_password
EOF
        echo "✅ Basic .env file created. Please edit it with your actual values."
    fi
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p temp_repos logs

# Set permissions
chmod +x scripts/*.sh 2>/dev/null || true

# Install Python dependencies using Poetry
echo "📦 Installing Python dependencies..."
if poetry env info --path &> /dev/null; then
    echo "✅ Poetry environment already exists"
else
    echo "🔧 Creating Poetry environment..."
    poetry env use python3.12 || poetry env use python3.11 || poetry env use python3.10
fi

poetry install

echo "🐳 Building Docker images..."
docker-compose build

echo "✅ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your OpenAI API key"
echo "2. Run: docker-compose up -d  (to start services)"
echo "3. Run: poetry run python src/main.py web  (to start development server)"
echo "4. Visit: http://localhost:8501 (Streamlit UI)"
echo "5. Visit: http://localhost:7474 (Neo4j Browser)"
echo ""
echo "For development without Docker:"
echo "- poetry run python src/main.py --help"
echo ""
echo "Happy coding! 🎉" 