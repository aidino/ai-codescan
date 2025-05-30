#!/bin/bash

# AI CodeScan Project Setup Script
# This script sets up the development environment for AI CodeScan

set -e  # Exit on any error

echo "🚀 Setting up AI CodeScan Development Environment"
echo "================================================"

# Check Python version
echo "🐍 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION found"

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed. Please install pip."
    exit 1
fi

# Check Docker and Docker Compose
echo "🐳 Checking Docker setup..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker."
    exit 1
fi

if ! command -v docker compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose."
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p logs temp_repos

# Install Python dependencies using pip
echo "📦 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Dependencies installed successfully"
else
    echo "❌ requirements.txt not found"
    exit 1
fi

# Start Docker services
echo "🐳 Starting Docker services..."
docker compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Test Neo4j connection
echo "🧪 Testing Neo4j connection..."
python scripts/test_neo4j.py

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "🎯 Next steps:"
echo "1. Run: docker compose ps                    (check service status)"
echo "2. Run: python src/main.py web              (to start development server)"
echo "3. Open: http://localhost:8501               (to access web interface)"
echo ""
echo "📖 Other useful commands:"
echo "- python src/main.py --help"
echo "- docker compose logs ai-codescan           (view application logs)"
echo "- docker compose logs neo4j                 (view Neo4j logs)" 