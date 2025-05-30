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
        click.echo("❌ Streamlit not installed. Please run: poetry install")
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
        click.echo("pytest not installed. Please run: poetry install")
        sys.exit(1)


if __name__ == '__main__':
    cli() 