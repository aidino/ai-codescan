# AI CodeScan - Simplified Docker build with pip
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Upgrade pip to latest version
RUN pip install --upgrade pip

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Verify critical dependencies are installed
RUN python -c "import click; print('✅ click installed successfully')"
RUN python -c "import streamlit; print('✅ streamlit installed successfully')"
RUN python -c "import neo4j; print('✅ neo4j driver installed successfully')"
RUN python -c "import git; print('✅ gitpython installed successfully')"

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Change ownership to app user
RUN chown -R app:app /app

# Switch to non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Expose Streamlit port
EXPOSE 8501

# Set environment variables
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

# Run Streamlit application
CMD ["python", "-m", "streamlit", "run", "src/agents/interaction_tasking/web_ui.py", "--server.port=8501", "--server.address=0.0.0.0"] 