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

# Create startup script
RUN echo '#!/bin/bash\n\
echo "🔐 Starting AI CodeScan Authenticated Web Interface..."\n\
echo "📍 URL: http://localhost:8501"\n\
echo "👤 Default admin: username=admin, password=admin123456"\n\
echo "⚠️  Please change default password after first login!"\n\
\n\
# Initialize authentication database\n\
python scripts/setup_auth_database.py init || true\n\
\n\
# Start authenticated web interface on port 8501\n\
python -m streamlit run src/agents/interaction_tasking/auth_web_ui.py --server.port=8501 --server.address=0.0.0.0\n' > /app/start.sh && chmod +x /app/start.sh

# Change ownership to app user
RUN chown -R app:app /app

# Switch to non-root user
USER app

# Health check for authenticated interface only
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Expose only authenticated interface port
EXPOSE 8501

# Set environment variables
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

# Run startup script
CMD ["/app/start.sh"] 