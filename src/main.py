#!/usr/bin/env python3
"""
AI CodeScan - Main Entry Point

This module serves as the main entry point for the AI CodeScan application.
It provides both CLI and programmatic interfaces to the core functionality.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

import click
from loguru import logger

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = "DEBUG" if verbose else "INFO"
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level
    )


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.version_option(version='0.1.0', prog_name='AI CodeScan')
def cli(verbose: bool) -> None:
    """AI CodeScan - AI-powered code review assistant."""
    setup_logging(verbose)
    logger.info("AI CodeScan v0.1.0 started")


@cli.command()
@click.option('--url', required=True, help='Repository URL to analyze')
@click.option('--language', help='Force specific language detection')
@click.option('--output', '-o', help='Output file for results')
def analyze(url: str, language: Optional[str], output: Optional[str]) -> None:
    """Analyze a repository for code quality and architecture issues."""
    logger.info(f"Starting analysis of repository: {url}")
    
    # TODO: Implement repository analysis
    # This will be implemented in Task 1.8
    click.echo(f"Repository analysis not yet implemented for: {url}")
    click.echo("This feature will be available after completing the agent architecture.")


@cli.command()
@click.option('--url', required=True, help='Repository URL')
@click.option('--pr-id', required=True, help='Pull Request ID')
@click.option('--platform', default='github', help='Git platform (github, gitlab, bitbucket)')
def review_pr(url: str, pr_id: str, platform: str) -> None:
    """Review a specific Pull Request."""
    logger.info(f"Starting PR review: {url}/pull/{pr_id}")
    
    # TODO: Implement PR review
    # This will be implemented in Task 3.3
    click.echo(f"PR review not yet implemented for: {url}/pull/{pr_id}")
    click.echo("This feature will be available in v1.0 after LLM integration.")


@cli.command()
def web() -> None:
    """Launch the web interface using Streamlit."""
    logger.info("Starting web interface...")
    
    try:
        import streamlit.web.cli as st_cli
        import sys
        import os
        
        # Path to the Streamlit app
        app_path = os.path.join(
            os.path.dirname(__file__), 
            'agents', 
            'interaction_tasking', 
            'web_ui.py'
        )
        
        if not os.path.exists(app_path):
            click.echo(f"❌ Streamlit app not found at: {app_path}")
            sys.exit(1)
        
        # Set up Streamlit arguments
        streamlit_args = [
            'streamlit',
            'run',
            app_path,
            '--server.port=8501',
            '--server.address=0.0.0.0',
            '--browser.gatherUsageStats=false',
            '--logger.level=warning'
        ]
        
        # Replace sys.argv for Streamlit
        original_argv = sys.argv.copy()
        sys.argv = streamlit_args
        
        try:
            # Run Streamlit
            st_cli.main()
        finally:
            # Restore original argv
            sys.argv = original_argv
            
    except ImportError:
        click.echo("❌ Streamlit not installed. Please run: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start web interface: {e}")
        click.echo(f"❌ Failed to start web interface: {e}")
        sys.exit(1)


@cli.command()
def version() -> None:
    """Show version information."""
    click.echo("AI CodeScan v0.1.0")
    click.echo("Multi-agent AI code review assistant")
    click.echo("Python version:", sys.version)


@cli.command()
def test() -> None:
    """Run the test suite."""
    logger.info("Running test suite...")
    
    try:
        import pytest
        # Run pytest programmatically
        exit_code = pytest.main(['-v', 'tests/'])
        sys.exit(exit_code)
    except ImportError:
        click.echo("pytest not installed. Please run: pip install -r requirements.txt")
        sys.exit(1)


@cli.command("auth-web")
def auth_web() -> None:
    """Launch the authenticated web interface using Streamlit."""
    logger.info("Starting authenticated web interface...")
    
    try:
        import streamlit.web.cli as st_cli
        import sys
        import os
        
        # Path to the authenticated Streamlit app
        app_path = os.path.join(
            os.path.dirname(__file__), 
            'agents', 
            'interaction_tasking', 
            'auth_web_ui.py'
        )
        
        if not os.path.exists(app_path):
            click.echo(f"❌ Authenticated Streamlit app not found at: {app_path}")
            sys.exit(1)
        
        # Set up Streamlit arguments
        streamlit_args = [
            'streamlit',
            'run',
            app_path,
            '--server.port=8502',  # Different port để avoid conflict
            '--server.address=0.0.0.0',
            '--browser.gatherUsageStats=false',
            '--logger.level=warning'
        ]
        
        # Replace sys.argv for Streamlit
        original_argv = sys.argv.copy()
        sys.argv = streamlit_args
        
        try:
            click.echo("🔍 Starting AI CodeScan Authenticated Web UI...")
            click.echo("📍 URL: http://localhost:8502")
            click.echo("👤 Default admin: username='admin', password='admin123456'")
            click.echo("⚠️  Please change default password after first login!")
            
            # Run Streamlit
            st_cli.main()
        finally:
            # Restore original argv
            sys.argv = original_argv
            
    except ImportError:
        click.echo("❌ Streamlit not installed. Please run: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start authenticated web interface: {e}")
        click.echo(f"❌ Failed to start authenticated web interface: {e}")
        sys.exit(1)


@cli.command("setup-auth")
@click.option('--db-path', default='data/ai_codescan.db', 
              help='Path to SQLite database file')
def setup_auth(db_path: str) -> None:
    """Setup authentication database với initial users."""
    logger.info("Setting up authentication database...")
    
    try:
        # Import auth setup
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scripts.setup_auth_database import setup_auth_database
        
        click.echo("🔐 Setting up authentication database...")
        success = setup_auth_database(db_path)
        
        if success:
            click.echo("✅ Authentication database setup completed!")
            click.echo(f"📁 Database location: {db_path}")
            click.echo("👤 Default admin: username='admin', password='admin123456'")
            click.echo("👤 Test user: username='test_user', password='testpassword'")
            click.echo("⚠️  Please change default passwords immediately!")
        else:
            click.echo("❌ Authentication database setup failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Auth setup failed: {e}")
        click.echo(f"❌ Authentication setup failed: {e}")
        sys.exit(1)


@cli.command()
@click.option('--host', default='localhost', help='Neo4j host')
@click.option('--port', default=7687, help='Neo4j port')
@click.option('--username', default='neo4j', help='Neo4j username')
@click.option('--password', prompt=True, hide_input=True, help='Neo4j password')
def setup_neo4j(host: str, port: int, username: str, password: str) -> None:
    """Setup Neo4j database schemas and constraints."""
    logger.info("Setting up Neo4j database...")
    
    try:
        from scripts.setup_neo4j_ckg import setup_neo4j_database
        
        click.echo("🗄️ Setting up Neo4j database...")
        success = setup_neo4j_database(
            uri=f"bolt://{host}:{port}",
            user=username,
            password=password
        )
        
        if success:
            click.echo("✅ Neo4j database setup completed!")
        else:
            click.echo("❌ Neo4j database setup failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Neo4j setup failed: {e}")
        click.echo(f"❌ Neo4j setup failed: {e}")
        sys.exit(1)


@cli.command()
@click.option('--port', default=8501, help='Port to run health check on')
def health(port: int) -> None:
    """Check health of running services."""
    import requests
    import time
    
    try:
        # Check Streamlit health
        response = requests.get(f"http://localhost:{port}/_stcore/health", timeout=5)
        if response.status_code == 200:
            click.echo(f"✅ Streamlit service healthy on port {port}")
        else:
            click.echo(f"⚠️ Streamlit service returned status {response.status_code}")
    except requests.exceptions.RequestException:
        click.echo(f"❌ Streamlit service not responding on port {port}")
    
    # Add more health checks as needed
    click.echo(f"🕐 Health check completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    cli() 