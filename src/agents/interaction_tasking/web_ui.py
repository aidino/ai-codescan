"""
AI CodeScan - Streamlit Web UI

Main Streamlit application providing web interface for AI CodeScan.
This is the primary user interface for repository analysis and code review.
"""

import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any
import uuid

import streamlit as st
from loguru import logger

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .user_intent_parser import UserIntentParserAgent
from .dialog_manager import DialogManagerAgent
from .task_initiation import TaskInitiationAgent
from .presentation import PresentationAgent

# Configure page
st.set_page_config(
    page_title="AI CodeScan",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    
    if 'dialog_state' not in st.session_state:
        st.session_state.dialog_state = "waiting_input"
    
    if 'task_history' not in st.session_state:
        st.session_state.task_history = []
    
    if 'current_task_id' not in st.session_state:
        st.session_state.current_task_id = None


def render_header():
    """Render the main header and navigation."""
    st.title("🔍 AI CodeScan")
    st.markdown("### AI-powered Code Review Assistant")
    st.markdown("---")


def render_sidebar():
    """Render the sidebar with options and information."""
    with st.sidebar:
        st.header("🛠️ Options")
        
        # Analysis Type Selection
        analysis_type = st.selectbox(
            "Analysis Type",
            ["Repository Review", "Pull Request Review", "Code Q&A"],
            help="Select the type of analysis you want to perform"
        )
        
        # Advanced Options
        with st.expander("⚙️ Advanced Options"):
            force_language = st.selectbox(
                "Force Language Detection",
                ["Auto-detect", "Python", "Java", "Dart", "Kotlin"],
                help="Override automatic language detection"
            )
            
            include_tests = st.checkbox(
                "Include Test Files",
                value=True,
                help="Include test files in analysis"
            )
            
            detailed_analysis = st.checkbox(
                "Detailed Analysis",
                value=False,
                help="Enable more detailed but slower analysis"
            )
        
        # Information Section
        st.markdown("---")
        st.header("ℹ️ Information")
        
        if st.session_state.current_task_id:
            st.info(f"Current Task: {st.session_state.current_task_id[:8]}")
        
        st.info(f"Session: {st.session_state.session_id[:8]}")
        
        # Status
        status_color = {
            "waiting_input": "🟡",
            "processing": "🔄", 
            "completed": "✅",
            "error": "❌"
        }
        st.markdown(f"Status: {status_color.get(st.session_state.dialog_state, '❓')} {st.session_state.dialog_state.replace('_', ' ').title()}")
        
        return {
            'analysis_type': analysis_type,
            'force_language': None if force_language == "Auto-detect" else force_language.lower(),
            'include_tests': include_tests,
            'detailed_analysis': detailed_analysis
        }


def render_main_interface(options: Dict[str, Any]):
    """Render the main interface based on analysis type."""
    analysis_type = options['analysis_type']
    
    if analysis_type == "Repository Review":
        render_repository_interface(options)
    elif analysis_type == "Pull Request Review":
        render_pr_interface(options)
    elif analysis_type == "Code Q&A":
        render_qna_interface(options)


def render_repository_interface(options: Dict[str, Any]):
    """Render repository analysis interface."""
    st.header("📁 Repository Analysis")
    
    # Input Section
    col1, col2 = st.columns([3, 1])
    
    with col1:
        repo_url = st.text_input(
            "GitHub Repository URL:",
            placeholder="https://github.com/username/repository",
            help="Enter the URL of the GitHub repository you want to analyze"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
        analyze_button = st.button(
            "🔍 Analyze Repository",
            type="primary",
            disabled=not repo_url or st.session_state.dialog_state == "processing"
        )
    
    # Optional PAT input (initially hidden)
    show_pat = st.checkbox(
        "Private Repository (requires Personal Access Token)",
        help="Check this if you're analyzing a private repository"
    )
    
    personal_access_token = None
    if show_pat:
        personal_access_token = st.text_input(
            "Personal Access Token:",
            type="password",
            help="GitHub Personal Access Token for private repository access"
        )
    
    # Process analysis request
    if analyze_button and repo_url:
        process_repository_analysis(repo_url, personal_access_token, options)
    
    # Display results
    render_analysis_results()


def render_pr_interface(options: Dict[str, Any]):
    """Render Pull Request analysis interface."""
    st.header("📋 Pull Request Review")
    st.info("Pull Request review functionality will be available in v1.0 (Task 3.3)")
    
    # Placeholder inputs for future implementation
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Repository URL:", disabled=True, placeholder="Coming soon...")
    
    with col2:
        st.text_input("PR Number:", disabled=True, placeholder="Coming soon...")
    
    st.button("Review PR", disabled=True, help="Feature coming in v1.0")


def render_qna_interface(options: Dict[str, Any]):
    """Render Code Q&A interface."""
    st.header("❓ Code Q&A")
    st.info("Interactive Q&A functionality will be available in v1.0 (Task 3.4)")
    
    # Placeholder for future implementation
    st.text_area(
        "Ask a question about your code:",
        disabled=True,
        placeholder="What are the main architectural patterns in this codebase?"
    )
    
    st.button("Ask Question", disabled=True, help="Feature coming in v1.0")


def process_repository_analysis(repo_url: str, pat: Optional[str], options: Dict[str, Any]):
    """Process repository analysis request."""
    # Initialize agents
    user_intent_parser = UserIntentParserAgent()
    dialog_manager = DialogManagerAgent()
    task_initiation = TaskInitiationAgent()
    
    try:
        # Update dialog state
        st.session_state.dialog_state = "processing"
        dialog_manager.update_state("processing")
        
        # Show progress
        progress_placeholder = st.empty()
        with progress_placeholder.container():
            st.info("🔄 Processing your request...")
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        # Parse user intent
        status_text.text("Parsing request...")
        progress_bar.progress(20)
        
        user_intent = user_intent_parser.parse_repository_request(
            repo_url=repo_url,
            pat=pat,
            options=options
        )
        
        # Create task definition
        status_text.text("Creating analysis task...")
        progress_bar.progress(40)
        
        task_definition = task_initiation.create_task_definition(user_intent)
        st.session_state.current_task_id = task_definition.get('task_id')
        
        # TODO: This will be connected to the orchestrator in Task 1.8
        status_text.text("Analyzing repository...")
        progress_bar.progress(60)
        time.sleep(1)  # Simulate processing time
        
        status_text.text("Generating report...")
        progress_bar.progress(80)
        time.sleep(1)  # Simulate processing time
        
        # For now, create mock results
        mock_results = create_mock_analysis_results(repo_url, options)
        st.session_state.analysis_results = mock_results
        
        progress_bar.progress(100)
        status_text.text("Analysis completed!")
        
        # Update dialog state
        st.session_state.dialog_state = "completed"
        dialog_manager.update_state("completed")
        
        # Clear progress indicator after a short delay
        time.sleep(1)
        progress_placeholder.empty()
        
        # Add to task history
        st.session_state.task_history.append({
            'task_id': st.session_state.current_task_id,
            'repo_url': repo_url,
            'timestamp': time.time(),
            'status': 'completed'
        })
        
        st.success("✅ Repository analysis completed!")
        st.rerun()
        
    except Exception as e:
        logger.error(f"Error during repository analysis: {e}")
        st.session_state.dialog_state = "error"
        st.error(f"❌ Analysis failed: {str(e)}")


def create_mock_analysis_results(repo_url: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """Create mock analysis results for demonstration purposes."""
    return {
        'repository': {
            'url': repo_url,
            'language': options.get('force_language', 'Python'),
            'files_analyzed': 25,
            'lines_of_code': 1250
        },
        'linter_results': {
            'total_issues': 8,
            'critical': 1,
            'major': 3,
            'minor': 4,
            'issues': [
                {
                    'file': 'src/main.py',
                    'line': 45,
                    'severity': 'critical',
                    'message': 'Unused import: sys',
                    'rule': 'F401'
                },
                {
                    'file': 'src/utils.py', 
                    'line': 12,
                    'severity': 'major',
                    'message': 'Line too long (92 > 88 characters)',
                    'rule': 'E501'
                },
                {
                    'file': 'src/config.py',
                    'line': 8,
                    'severity': 'major',
                    'message': 'Missing docstring in public module',
                    'rule': 'D100'
                }
            ]
        },
        'architecture_analysis': {
            'circular_dependencies': 0,
            'unused_public_elements': 2,
            'complexity_score': 7.5
        },
        'summary': "Repository analysis completed. Found 8 linting issues that should be addressed. No circular dependencies detected. Architecture complexity is within acceptable range."
    }


def render_analysis_results():
    """Render analysis results if available."""
    if st.session_state.analysis_results:
        presentation = PresentationAgent()
        presentation.display_analysis_results(st.session_state.analysis_results)


def render_footer():
    """Render the footer."""
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**AI CodeScan v1.0**")
    
    with col2:
        st.markdown("Multi-agent AI Code Review")
    
    with col3:
        if st.button("🔄 Reset Session"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


def run_streamlit_app():
    """Main Streamlit application entry point."""
    # Initialize session state
    initialize_session_state()
    
    # Render UI components
    render_header()
    options = render_sidebar()
    render_main_interface(options)
    render_footer()


if __name__ == "__main__":
    run_streamlit_app() 