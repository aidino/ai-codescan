#!/usr/bin/env python3
"""
AI CodeScan - Authenticated Streamlit Web UI

Enhanced Streamlit application với user authentication support.
Integrates với authentication system để provide user-specific sessions.
"""

import sys
import time
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

import streamlit as st

# Configure page FIRST (must be first Streamlit command)
st.set_page_config(
    page_title="🤖 AI CodeScan - Authenticated",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

from loguru import logger

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import authentication system
from core.auth import (
    init_auth_database,
    UserManager,
    AuthService,
    AuthenticatedSessionManager,
    CreateUserRequest,
    UserCredentials,
    UserRole
)
from core.auth.session_manager import SessionType, SessionStatus

# Import existing components
from agents.interaction_tasking.user_intent_parser import UserIntentParserAgent
from agents.interaction_tasking.dialog_manager import DialogManagerAgent
from agents.interaction_tasking.task_initiation import TaskInitiationAgent
from agents.interaction_tasking.presentation import PresentationAgent

# Import PATHandlerAgent
from agents.interaction_tasking.pat_handler import PATHandlerAgent

# Import diagram generator
from agents.synthesis_reporting.diagram_generator import DiagramGeneratorAgent, DiagramType, DiagramFormat

# Import feedback system
from agents.interaction_tasking.feedback_collector import (
    FeedbackCollectorAgent, 
    UserFeedback, 
    FeedbackType, 
    FeatureArea, 
    SatisfactionLevel,
    UIImprovementAgent,
    create_feedback_collector
)
from agents.interaction_tasking.ui_improvement_agent import (
    UIImprovementAgent,
    create_ui_improvement_agent
)

# Import enhanced navigation
from agents.interaction_tasking.enhanced_navigation import (
    EnhancedNavigationAgent,
    create_enhanced_navigation
)

# Fix relative imports - use absolute imports instead
from core.logging import log_repository_analysis_start, get_debug_logger
from core.logging import log_repository_analysis_end


def initialize_auth_system():
    """Initialize authentication system."""
    if "auth_initialized" not in st.session_state:
        try:
            # Initialize database và auth services
            st.session_state.db_manager = init_auth_database()
            st.session_state.user_manager = UserManager(st.session_state.db_manager)
            st.session_state.auth_service = AuthService(st.session_state.db_manager)
            st.session_state.session_manager = AuthenticatedSessionManager(st.session_state.db_manager)
            
            st.session_state.auth_initialized = True
            logger.info("Authentication system initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize auth system: {str(e)}")
            st.error(f"⚠️ Authentication system initialization failed: {str(e)}")
            st.stop()


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    # Authentication state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    
    if "session_token" not in st.session_state:
        st.session_state.session_token = None
    
    # PAT Handler initialization
    if "pat_handler" not in st.session_state:
        st.session_state.pat_handler = PATHandlerAgent()
    
    # Session management state
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = None
    
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None
    
    if "analysis_in_progress" not in st.session_state:
        st.session_state.analysis_in_progress = False
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    if "view_mode" not in st.session_state:
        st.session_state.view_mode = "dashboard"  # dashboard, new_session, history_view
    
    if "selected_history_session" not in st.session_state:
        st.session_state.selected_history_session = None
    
    # PAT management state
    if "stored_pat_hash" not in st.session_state:
        st.session_state.stored_pat_hash = None
    
    # Feedback system initialization
    if "feedback_collector" not in st.session_state:
        st.session_state.feedback_collector = create_feedback_collector()
    
    if "ui_improvement_agent" not in st.session_state:
        st.session_state.ui_improvement_agent = create_ui_improvement_agent(st.session_state.feedback_collector)
    
    # Enhanced navigation initialization
    if "enhanced_navigation" not in st.session_state:
        st.session_state.enhanced_navigation = create_enhanced_navigation()


def check_authentication():
    """Check if user is authenticated and session is valid."""
    if not st.session_state.authenticated or not st.session_state.session_token:
        return False
    
    # Validate session token
    session_info = st.session_state.auth_service.validate_session(st.session_state.session_token)
    
    if not session_info:
        # Session expired or invalid
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.session_state.session_token = None
        return False
    
    # Update current user info
    st.session_state.current_user = session_info.user
    return True


def render_login_page():
    """Render login/register page với improved UI."""
    # Enhanced CSS for better styling and responsive design
    st.markdown("""
        <style>
        .login-container {
            max-width: 500px;
            margin: 0 auto;
            padding: 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
            color: white;
            margin-top: 2rem;
            margin-bottom: 2rem;
        }
        .login-form {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            color: #333;
        }
        .login-title {
            text-align: center;
            color: white;
            margin-bottom: 0.5rem;
            font-size: 2.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .login-subtitle {
            text-align: center;
            color: rgba(255,255,255,0.9);
            margin-bottom: 2rem;
            font-size: 1.1rem;
        }
        
        /* Fix Streamlit tabs styling issues */
        .stTabs > div > div > div > div {
            padding: 1.5rem;
            background: white;
            border-radius: 15px;
            margin-top: 1rem;
            box-shadow: inset 0 2px 5px rgba(0,0,0,0.05);
        }
        
        /* Fix tab-highlight overlapping tab-border */
        .st-c2.st-c3.st-c4.st-c5.st-c6.st-c7.st-cy.st-c9.st-cq.st-e6.st-e7 {
            z-index: 1 !important;
            bottom: 1px !important;
        }
        
        /* Ensure tab borders are visible */
        [data-baseweb="tab-border"] {
            z-index: 2 !important;
        }
        
        /* Tab styling improvements */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: transparent;
            border-bottom: 2px solid #e1e5e9;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: auto;
            white-space: nowrap;
            padding: 12px 24px;
            border-radius: 8px 8px 0 0;
            background: #f8f9fa;
            border: 2px solid #e1e5e9;
            border-bottom: none;
            color: #495057;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background: #e9ecef;
            color: #343a40;
        }
        
        .stTabs [aria-selected="true"] {
            background: white !important;
            color: #667eea !important;
            border-color: #667eea !important;
            border-bottom: 2px solid white !important;
            margin-bottom: -2px !important;
            z-index: 3 !important;
        }
        
        /* Tab highlight fixes */
        [data-baseweb="tab-highlight"] {
            display: none !important;
        }
        
        /* Input field improvements */
        .stTextInput > div > div > input {
            border-radius: 10px;
            border: 2px solid #e1e5e9;
            padding: 0.75rem;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        .stTextInput > div > div > input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        /* Button styling */
        .stButton > button {
            border-radius: 10px;
            height: 3rem;
            font-size: 1.1rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        /* Form improvements */
        .stForm {
            border: none;
            background: transparent;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .login-container {
                margin: 1rem;
                padding: 1.5rem;
            }
            .login-title {
                font-size: 2rem;
            }
            .stTabs > div > div > div > div {
                padding: 1rem;
            }
        }
        
        /* Success/Error message styling */
        .stAlert {
            border-radius: 10px;
            border: none;
            margin: 1rem 0;
        }
        
        /* Demo accounts expander styling */
        .streamlit-expanderHeader {
            background: linear-gradient(90deg, #f8f9fa, #e9ecef);
            border-radius: 10px;
            margin-top: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Center the login form với responsive layout
    col1, col2, col3 = st.columns([0.5, 3, 0.5])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # Title and subtitle
        st.markdown('<h1 class="login-title">🤖 AI CodeScan</h1>', unsafe_allow_html=True)
        st.markdown('<p class="login-subtitle">AI-powered Code Review Assistant</p>', unsafe_allow_html=True)
        
        # Create tabs for login và register
        login_tab, register_tab = st.tabs(["🔑 Đăng nhập", "📝 Đăng ký"])
        
        with login_tab:
            render_login_form()
        
        with register_tab:
            render_register_form()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Demo accounts info (outside container for better spacing)
    st.markdown("---")
    with st.expander("🔑 Demo Accounts để Testing", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **👨‍💼 Admin Account**
            - **Username:** `admin`
            - **Password:** `admin123456`
            - **Role:** Administrator
            """)
        
        with col2:
            st.markdown("""
            **👤 Test User**
            - **Username:** `test_user`
            - **Password:** `testpassword`
            - **Role:** User
            """)
        
        with col3:
            st.markdown("""
            **🎮 Demo User**
            - **Username:** `demo`
            - **Password:** `demopassword`
            - **Role:** User
            """)
        
        st.info("💡 **Lưu ý:** Đây là accounts demo cho testing. Trong production, hãy thay đổi password mặc định!")


def render_login_form():
    """Render improved login form."""
    with st.container():
        st.markdown("### 🔑 Đăng nhập hệ thống")
        st.markdown("---")
        
        with st.form("login_form", clear_on_submit=False):
            # Input fields với better spacing
            username_or_email = st.text_input(
                "👤 Username hoặc Email",
                placeholder="Nhập username hoặc email",
                help="Bạn có thể sử dụng username hoặc email để đăng nhập"
            )
            
            password = st.text_input(
                "🔒 Password",
                type="password",
                placeholder="Nhập password",
                help="Nhập password của bạn"
            )
            
            # Submit button với full width
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("🔑 Đăng nhập", type="primary", use_container_width=True)
            
            if submit:
                if not username_or_email or not password:
                    st.error("⚠️ Vui lòng nhập đầy đủ thông tin!")
                    return
                
                # Add loading spinner
                with st.spinner("Đang xác thực..."):
                    # Authenticate user
                    credentials = UserCredentials(
                        username_or_email=username_or_email,
                        password=password
                    )
                    
                    result = st.session_state.auth_service.login(credentials)
                    
                    if result.success:
                        st.session_state.authenticated = True
                        st.session_state.current_user = result.user
                        st.session_state.session_token = result.session_token
                        
                        st.success(f"✅ Đăng nhập thành công! Chào mừng {result.user.username}")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ Đăng nhập thất bại: {result.error_message}")


def render_register_form():
    """Render improved registration form."""
    with st.container():
        st.markdown("### 📝 Tạo tài khoản mới")
        st.markdown("---")
        
        with st.form("register_form", clear_on_submit=False):
            # Input fields với better layout
            col1, col2 = st.columns(2)
            
            with col1:
                username = st.text_input(
                    "👤 Username",
                    placeholder="3-50 ký tự",
                    help="Username duy nhất cho tài khoản của bạn"
                )
            
            with col2:
                email = st.text_input(
                    "📧 Email",
                    placeholder="your@email.com",
                    help="Email hợp lệ để khôi phục tài khoản"
                )
            
            password = st.text_input(
                "🔒 Password",
                type="password",
                placeholder="Tối thiểu 8 ký tự",
                help="Password mạnh với ít nhất 8 ký tự"
            )
            
            confirm_password = st.text_input(
                "🔒 Xác nhận Password",
                type="password",
                placeholder="Nhập lại password",
                help="Nhập lại password để xác nhận"
            )
            
            display_name = st.text_input(
                "✨ Tên hiển thị (tuỳ chọn)",
                placeholder="Tên hiển thị trong hệ thống",
                help="Tên này sẽ hiển thị trong interface"
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("📝 Đăng ký", type="primary", use_container_width=True)
            
            if submit:
                # Validate input
                if not username or not email or not password:
                    st.error("⚠️ Vui lòng nhập đầy đủ thông tin bắt buộc!")
                    return
                
                if password != confirm_password:
                    st.error("⚠️ Password xác nhận không khớp!")
                    return
                
                if len(password) < 8:
                    st.error("⚠️ Password phải có ít nhất 8 ký tự!")
                    return
                
                if len(username) < 3 or len(username) > 50:
                    st.error("⚠️ Username phải có 3-50 ký tự!")
                    return
                
                # Add loading spinner
                with st.spinner("Đang tạo tài khoản..."):
                    # Create user
                    profile_data = {}
                    if display_name:
                        profile_data["display_name"] = display_name
                    profile_data["created_from"] = "web_ui"
                    
                    request = CreateUserRequest(
                        username=username,
                        email=email,
                        password=password,
                        role=UserRole.USER,
                        profile_data=profile_data
                    )
                    
                    user = st.session_state.user_manager.create_user(request)
                    
                    if user:
                        st.success(f"✅ Đăng ký thành công! Tài khoản {username} đã được tạo.")
                        st.info("💡 Bạn có thể đăng nhập bằng tab 'Đăng nhập'")
                        st.balloons()
                    else:
                        st.error("❌ Đăng ký thất bại. Username hoặc email có thể đã tồn tại.")


def render_authenticated_header():
    """Render header for authenticated users."""
    st.markdown("# 🤖 AI CodeScan")
    st.markdown("### AI-powered Code Review Assistant")
    st.divider()


def logout_user():
    """Logout current user."""
    if st.session_state.session_token:
        try:
            st.session_state.auth_service.logout(st.session_state.session_token)
            logger.info(f"User logged out: {st.session_state.current_user.username}")
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
    
    # Clear session state
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.session_token = None
    st.session_state.current_session_id = None
    st.session_state.analysis_results = None
    st.session_state.chat_messages = []
    st.session_state.view_mode = "dashboard"
    
    st.success("✅ Đăng xuất thành công!")
    st.balloons()  # Add celebratory animation
    time.sleep(1)  # Brief pause to show success message
    st.rerun()


def render_authenticated_sidebar():
    """Render sidebar for authenticated users."""
    with st.sidebar:
        # Modern user profile section với card design
        st.markdown("""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1.5rem;
                border-radius: 15px;
                color: white;
                margin-bottom: 1.5rem;
                text-align: center;
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            ">
                <h2 style="margin: 0; font-size: 1.2rem;">👤 {}</h2>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 0.9rem;">
                    {} • {}
                </p>
            </div>
        """.format(
            st.session_state.current_user.username,
            st.session_state.current_user.role.value,
            "Online"
        ), unsafe_allow_html=True)
        
        # Logout button với modern design
        if st.button("🚪 Đăng xuất", key="sidebar_logout", use_container_width=True, type="secondary"):
            logout_user()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # User Statistics Card
        stats = st.session_state.session_manager.get_user_session_stats(
            st.session_state.current_user.id
        )
        
        st.markdown("""
            <div style="
                background: white;
                padding: 1.5rem;
                border-radius: 15px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
                border: 1px solid #e1e5e9;
                margin-bottom: 1.5rem;
            ">
                <h3 style="margin: 0 0 1rem 0; color: #495057; font-size: 1rem;">📊 Thống kê</h3>
        """, unsafe_allow_html=True)
        
        # Metrics in grid layout
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tổng", stats['total_sessions'], label_visibility="visible")
            scans = stats['by_type'].get('repository_analysis', 0)
            st.metric("Scans", scans)
        
        with col2:
            completed = stats['by_status'].get('completed', 0)
            st.metric("Hoàn thành", completed)
            chats = stats['by_type'].get('code_qna', 0)
            st.metric("Chats", chats)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Enhanced Navigation section với streamlit-option-menu
        st.markdown("""
            <h3 style="color: #495057; font-size: 1rem; margin-bottom: 1rem;">🧭 Điều hướng</h3>
        """, unsafe_allow_html=True)
        
        # Use enhanced navigation agent
        nav_agent = st.session_state.enhanced_navigation
        
        # Get current view mode index for default selection
        view_mode_mapping = {
            "dashboard": 0,
            "new_session": 1, 
            "pr_review": 2,
            "qna_assistant": 3,
            "code_diagrams": 4,
            "user_feedback": 5,
            "history_view": 6
        }
        
        current_index = view_mode_mapping.get(st.session_state.view_mode, 0)
        
        # Render option menu navigation
        from streamlit_option_menu import option_menu
        
        selected_nav = option_menu(
            menu_title=None,
            options=[
                "🏠 Dashboard",
                "🔍 Repository Analysis", 
                "🔄 Pull Request Review",
                "💬 Q&A Assistant",
                "📊 Code Diagrams",
                "📝 User Feedback",
                "📈 Session History"
            ],
            icons=[
                "house", 
                "search", 
                "arrow-repeat", 
                "chat-text", 
                "diagram-3", 
                "pencil-square", 
                "clock-history"
            ],
            menu_icon="list",
            default_index=current_index,
            orientation="vertical",
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#667eea", "font-size": "16px"}, 
                "nav-link": {
                    "font-size": "14px", 
                    "text-align": "left", 
                    "margin":"2px", 
                    "padding": "8px 12px",
                    "border-radius": "8px",
                    "--hover-color": "#f0f2ff"
                },
                "nav-link-selected": {"background-color": "#667eea", "color": "white"},
            }
        )
        
        # Convert selection to view mode
        new_view_mode = nav_agent.get_view_mode_from_selection(selected_nav)
        
        # Update view mode if changed
        if new_view_mode != st.session_state.view_mode:
            st.session_state.view_mode = new_view_mode
            if new_view_mode == "new_session":
                st.session_state.selected_history_session = None
            st.rerun()
        
        # Quick chat action
        if st.button("💬 Chat mới", use_container_width=True, type="secondary"):
            create_new_chat_session()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Session History với improved design
        st.markdown("""
            <h3 style="color: #495057; font-size: 1rem; margin-bottom: 1rem;">📚 Lịch sử gần đây</h3>
        """, unsafe_allow_html=True)
        
        # Get user sessions
        sessions = st.session_state.session_manager.get_user_sessions(
            st.session_state.current_user.id,
            limit=8
        )
        
        if sessions:
            for i, session in enumerate(sessions):
                # Determine icon và color based on type và status
                if session.session_type == SessionType.REPOSITORY_ANALYSIS:
                    type_icon = "📊"
                    type_color = "#28a745"
                else:
                    type_icon = "💬"
                    type_color = "#007bff"
                
                status_icon = "✅" if session.status == SessionStatus.COMPLETED else "🔄"
                
                # Truncate title for better display
                title = session.title
                if len(title) > 25:
                    title = title[:22] + "..."
                
                # Create session item với modern card design
                with st.container():
                    st.markdown(f"""
                        <div style="
                            background: white;
                            border: 1px solid #e1e5e9;
                            border-radius: 12px;
                            padding: 1rem;
                            margin-bottom: 0.75rem;
                            box-shadow: 0 3px 10px rgba(0,0,0,0.05);
                            transition: all 0.3s ease;
                        " class="session-history-card">
                            <div style="
                                display: flex;
                                align-items: center;
                                justify-content: space-between;
                                margin-bottom: 0.5rem;
                            ">
                                <span style="font-size: 1.1rem;">{type_icon}</span>
                                <span style="font-size: 0.9rem; color: #6c757d;">
                                    {session.created_at[:10] if session.created_at else 'Unknown'}
                                </span>
                            </div>
                            <div style="
                                font-weight: 600;
                                color: #343a40;
                                margin-bottom: 0.25rem;
                                font-size: 0.9rem;
                                line-height: 1.3;
                            ">
                                {title}
                            </div>
                            <div style="
                                display: flex;
                                align-items: center;
                                font-size: 0.8rem;
                                color: #6c757d;
                            ">
                                <span style="margin-right: 0.5rem;">{status_icon}</span>
                                <span>{session.status.value.replace('_', ' ').title()}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Button bên trong container để handle click
                    if st.button(
                        "👁️ Xem chi tiết",
                        key=f"session_{session.session_id}_{i}",
                        use_container_width=True,
                        help=f"Xem session: {session.title}",
                        type="secondary"
                    ):
                        view_session(session.session_id)
        else:
            st.markdown("""
                <div class="history-empty-state">
                    <p style="margin: 0; font-size: 0.9rem;">
                        📝 Chưa có session nào<br>
                        Bắt đầu bằng cách tạo scan mới!
                    </p>
                </div>
            """, unsafe_allow_html=True)
        
        # Quick actions at bottom
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
            <h3 style="color: #495057; font-size: 1rem; margin-bottom: 1rem;">⚡ Thao tác nhanh</h3>
        """, unsafe_allow_html=True)
        
        if st.button("📈 Xem tất cả Sessions", use_container_width=True):
            st.session_state.view_mode = "all_sessions"
            st.rerun()
        
        # System info section
        st.markdown("<br><hr>", unsafe_allow_html=True)
        st.markdown("""
            <div style="
                text-align: center;
                padding: 1rem;
                background: #f8f9fa;
                border-radius: 10px;
                font-size: 0.8rem;
                color: #6c757d;
            ">
                <p style="margin: 0;">🤖 AI CodeScan v1.0</p>
                <p style="margin: 0;">Powered by LangGraph</p>
            </div>
        """, unsafe_allow_html=True)


def create_new_chat_session():
    """Create new chat session."""
    session_id = st.session_state.session_manager.create_session(
        user_id=st.session_state.current_user.id,
        session_type=SessionType.CODE_QNA,
        title=f"Chat Session - {time.strftime('%H:%M')}"
    )
    
    st.session_state.current_session_id = session_id
    st.session_state.view_mode = "new_session"
    st.session_state.chat_messages = []
    st.rerun()


def view_session(session_id: str):
    """View specific session."""
    st.session_state.view_mode = "history_view"
    st.session_state.selected_history_session = session_id
    st.rerun()


def render_dashboard():
    """Render user dashboard."""
    st.markdown("## 📈 Hoạt động gần đây")
    
    # Get user stats for recent activity
    stats = st.session_state.session_manager.get_user_session_stats(
        st.session_state.current_user.id
    )
    
    # Recent activity
    if stats['recent_activity']:
        for i, activity in enumerate(stats['recent_activity']):
            with st.container():
                # Create card-like container for each activity
                st.markdown(f"""
                    <div style="
                        background: white;
                        padding: 1.5rem;
                        border-radius: 15px;
                        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
                        border: 1px solid #e1e5e9;
                        margin-bottom: 1rem;
                    ">
                """, unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    type_icon = "📊" if activity['type'] == 'repository_analysis' else "💬"
                    st.markdown(f"### {type_icon} {activity['title']}")
                    st.caption(f"Type: {activity['type'].replace('_', ' ').title()}")
                
                with col2:
                    status_icon = "✅" if activity['status'] == 'completed' else "🔄"
                    st.markdown(f"**Status**")
                    st.markdown(f"{status_icon} {activity['status'].title()}")
                
                with col3:
                    updated = activity['updated_at'][:10] if activity['updated_at'] else "Unknown"
                    st.markdown(f"**Date**")
                    st.markdown(f"📅 {updated}")
                
                with col4:
                    st.markdown("")  # Spacing
                    if st.button("👁️ View", key=f"view_activity_{i}", use_container_width=True):
                        view_session(activity['session_id'])
                
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Empty state with nice design
        st.markdown("""
            <div style="
                text-align: center;
                padding: 3rem;
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border-radius: 20px;
                border: 2px dashed #dee2e6;
                margin: 2rem 0;
            ">
                <h3>🌟 Chưa có hoạt động nào</h3>
                <p style="color: #6c757d; margin-bottom: 2rem;">
                    Bắt đầu với việc scan repository đầu tiên của bạn!
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Quick start actions
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Bắt đầu Scan Repository", type="primary", use_container_width=True):
                st.session_state.view_mode = "new_session"
                st.rerun()


def render_new_session_interface():
    """Render interface for creating new session."""
    # Create temporary options dict
    options = {}
    
    # Call original interface but with user context
    st.markdown("## 🤖 AI CodeScan - Phân tích Code Thông minh")
    
    # Analysis Type Selection
    st.markdown("### 📋 Chọn loại phân tích")
    
    analysis_type = st.selectbox(
        "Loại phân tích",
        ["Repository Review", "Pull Request Review", "Code Q&A", "Code Diagrams", "User Feedback"],
        help="Chọn loại phân tích bạn muốn thực hiện"
    )
    
    # Advanced Options
    with st.expander("⚙️ Tùy chọn nâng cao"):
        col1, col2 = st.columns(2)
        
        with col1:
            force_language = st.selectbox(
                "Ngôn ngữ cụ thể",
                ["Auto-detect", "Python", "Java", "Dart", "Kotlin"],
                help="Ghi đè tự động phát hiện ngôn ngữ. Chọn Auto-detect để phân tích multi-language."
            )
            
            include_tests = st.checkbox(
                "Bao gồm file test",
                value=True,
                help="Bao gồm các file test trong phân tích"
            )
            
            architectural_analysis = st.checkbox(
                "Phân tích kiến trúc",
                value=True,
                help="Bật phân tích kiến trúc để phát hiện circular dependencies và unused elements"
            )
        
        with col2:
            detailed_analysis = st.checkbox(
                "Phân tích chi tiết",
                value=False,
                help="Bật phân tích chi tiết hơn nhưng chậm hơn"
            )
            
            enable_ckg_analysis = st.checkbox(
                "Phân tích CKG",
                value=True,
                help="Bật Code Knowledge Graph analysis để hiểu sâu hơn về mối quan hệ code"
            )
    
    # Update options
    options.update({
        'analysis_type': analysis_type,
        'force_language': None if force_language == "Auto-detect" else force_language.lower(),
        'include_tests': include_tests,
        'detailed_analysis': detailed_analysis,
        'architectural_analysis': architectural_analysis,
        'enable_ckg_analysis': enable_ckg_analysis
    })
    
    # Render appropriate interface based on analysis type
    if analysis_type == "Repository Review":
        render_authenticated_repository_interface(options)
    elif analysis_type == "Pull Request Review":
        render_authenticated_pr_interface(options)
    elif analysis_type == "Code Q&A":
        render_authenticated_qna_interface(options)
    elif analysis_type == "Code Diagrams":
        render_code_diagrams_interface(options)
    elif analysis_type == "User Feedback":
        render_user_feedback_interface(options)


def render_authenticated_repository_interface(options: Dict[str, Any]):
    """Render repository analysis với enhanced PAT management."""
    st.markdown("### 📦 Repository Analysis")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        repo_url = st.text_input(
            "🔗 Repository URL",
            placeholder="https://github.com/username/repository",
            help="Nhập URL của repository bạn muốn phân tích"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_button = st.button("🔍 Phân tích Repository", type="primary", use_container_width=True)
    
    # Enhanced PAT Management Section
    st.markdown("---")
    st.markdown("#### 🔐 Private Repository Access")
    
    # Show stored PATs info
    stored_pats = st.session_state.pat_handler.get_stored_pat_info()
    if stored_pats:
        st.info(f"✅ Có {len(stored_pats)} PAT được lưu trữ trong session này")
        
        with st.expander("📋 Xem PATs đã lưu", expanded=False):
            for i, pat_info in enumerate(stored_pats):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.text(f"🔹 {pat_info['platform'].title()}")
                with col2:
                    st.text(f"👤 {pat_info['username']}")
                with col3:
                    st.text(f"🆔 {pat_info['token_hash']}")
    
    # PAT input section
    show_pat = st.checkbox("🔑 Sử dụng Personal Access Token")
    pat = None
    pat_hash = None
    
    if show_pat:
        if stored_pats:
            use_stored = st.radio(
                "Chọn PAT:",
                ["Sử dụng PAT đã lưu", "Nhập PAT mới"],
                horizontal=True
            )
            
            if use_stored == "Sử dụng PAT đã lưu":
                if len(stored_pats) == 1:
                    selected_pat = stored_pats[0]
                    st.success(f"🔗 Sử dụng PAT: {selected_pat['platform'].title()} - {selected_pat['username']}")
                    pat_hash = st.session_state.pat_handler.stored_pats[next(iter(st.session_state.pat_handler.stored_pats.keys()))].token_hash
                else:
                    # Multiple PATs - let user choose
                    pat_options = [f"{pat['platform'].title()} - {pat['username']} ({pat['token_hash']})" for pat in stored_pats]
                    selected_option = st.selectbox("Chọn PAT:", pat_options)
                    if selected_option:
                        # Extract hash from selection
                        selected_hash = selected_option.split('(')[-1].rstrip(')')
                        pat_hash = next((hash for hash, info in st.session_state.pat_handler.stored_pats.items() 
                                       if info.token_hash.startswith(selected_hash.split('...')[0])), None)
            else:
                # New PAT input
                pat = render_pat_input_section()
        else:
            # No stored PATs - show input
            pat = render_pat_input_section()
    
    # Analysis execution
    if analyze_button and repo_url:
        # Determine PAT to use
        final_pat = None
        if show_pat:
            if pat_hash:
                # Use stored PAT
                final_pat = st.session_state.pat_handler.retrieve_pat(pat_hash)
                if not final_pat:
                    st.error("❌ Không thể truy xuất PAT đã lưu!")
                    return
            elif pat:
                # Use newly entered PAT
                final_pat = pat
        
        # Validate requirements
        if show_pat and not final_pat:
            st.error("⚠️ Vui lòng nhập hoặc chọn Personal Access Token cho repository riêng tư!")
        else:
            process_authenticated_repository_analysis(repo_url, final_pat, options)


def render_pat_input_section():
    """Render PAT input section với validation."""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Platform detection from URL
        platform = "GitHub"  # Default
        if "gitlab" in st.session_state.get('repo_url', '').lower():
            platform = "GitLab"
        elif "bitbucket" in st.session_state.get('repo_url', '').lower():
            platform = "BitBucket"
        
        platform = st.selectbox(
            "🏢 Platform:",
            ["GitHub", "GitLab", "BitBucket"],
            index=["GitHub", "GitLab", "BitBucket"].index(platform)
        )
    
    with col2:
        # Help link
        pat_url = st.session_state.pat_handler.get_platform_pat_url(platform)
        st.markdown(f"[📚 Tạo PAT]({pat_url})", unsafe_allow_html=True)
    
    # Username input
    username = st.text_input(
        "👤 Username:",
        placeholder="your-username",
        help="Username của bạn trên platform"
    )
    
    # PAT input với validation
    pat = st.text_input(
        "🔑 Personal Access Token:",
        type="password",
        placeholder="ghp_xxxxxxxxxxxxxxxxxxxx" if platform == "GitHub" else "your-token",
        help=f"Nhập PAT của {platform} để truy cập repository riêng tư"
    )
    
    # Real-time validation
    if pat:
        is_valid = st.session_state.pat_handler.validate_pat_format(platform, pat)
        if is_valid:
            st.success("✅ Format PAT hợp lệ")
            
            # Option to store PAT
            col1, col2 = st.columns([3, 1])
            with col1:
                store_pat = st.checkbox("💾 Lưu PAT trong session này", help="PAT sẽ được mã hóa và lưu tạm thời")
            
            with col2:
                if store_pat and username and st.button("💾 Lưu", key="store_pat_btn"):
                    try:
                        session_id = st.session_state.current_session_id or "temp_session"
                        token_hash = st.session_state.pat_handler.store_pat(
                            platform=platform,
                            username=username,
                            token=pat,
                            session_id=session_id
                        )
                        st.session_state.stored_pat_hash = token_hash
                        st.success("💾 PAT đã được lưu an toàn!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Lỗi khi lưu PAT: {str(e)}")
        else:
            st.error(f"❌ Format PAT không hợp lệ cho {platform}")
            # Show format hints
            if platform == "GitHub":
                st.info("💡 GitHub PAT thường bắt đầu với: ghp_, gho_, ghu_, ghs_, hoặc ghr_")
            elif platform == "GitLab":
                st.info("💡 GitLab PAT thường bắt đầu với: glpat-")
    
    return pat


def process_authenticated_repository_analysis(repo_url: str, pat: Optional[str], options: Dict[str, Any]):
    """Process repository analysis với user session tracking."""
    # Create session if not exists
    if not st.session_state.current_session_id:
        repo_name = repo_url.split('/')[-1] if '/' in repo_url else repo_url
        session_id = st.session_state.session_manager.create_session(
            user_id=st.session_state.current_user.id,
            session_type=SessionType.REPOSITORY_ANALYSIS,
            title=f"Repository Scan: {repo_name}",
            description=f"Analysis of {repo_url}",
            metadata={"repo_url": repo_url, "options": options}
        )
        st.session_state.current_session_id = session_id
    
    # Initialize debug logging cho session
    debug_logger = log_repository_analysis_start(
        repo_url, 
        session_id=f"ui_session_{st.session_state.current_session_id}"
    )
    
    # Log UI context
    debug_logger.log_step("Repository analysis started from Web UI", {
        "user_id": st.session_state.current_user.id,
        "username": st.session_state.current_user.username,
        "session_id": st.session_state.current_session_id,
        "repo_url": repo_url,
        "has_pat": bool(pat),
        "options": options
    })
    
    st.session_state.analysis_in_progress = True
    
    with st.spinner("🔄 Đang phân tích repository..."):
        # Simulate analysis with detailed logging
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        steps = [
            ("Cloning repository...", "DATA_ACQUISITION"),
            ("Analyzing code structure...", "LANGUAGE_IDENTIFICATION"),
            ("Running static analysis...", "CODE_ANALYSIS"),
            ("Building knowledge graph...", "CKG_OPERATIONS"),
            ("Generating insights...", "LLM_SERVICES"),
            ("Preparing results...", "SYNTHESIS_REPORTING")
        ]
        
        for i, (step_desc, stage) in enumerate(steps):
            # Set analysis stage
            debug_logger.set_analysis_stage(stage)
            
            status_text.text(f"📋 {step_desc}")
            progress_bar.progress((i + 1) / len(steps))
            
            # Log step progression
            debug_logger.log_step(step_desc, {
                "stage": stage,
                "progress_percent": ((i + 1) / len(steps)) * 100,
                "step_number": i + 1,
                "total_steps": len(steps)
            })
            
            # Simulate different processing times for different stages
            if stage == "DATA_ACQUISITION":
                # Simulate repository cloning
                debug_logger.log_step("Simulating git clone operation", {
                    "repo_url": repo_url,
                    "depth": 1,
                    "estimated_duration": "2-5 seconds"
                })
                import time
                time.sleep(2)  # Simulate longer clone time
                
                # Log mock clone results
                debug_logger.log_data("mock_clone_result", {
                    "status": "success",
                    "local_path": f"/tmp/ai_codescan_repos/{repo_url.split('/')[-1]}",
                    "size_mb": 1.5,
                    "file_count": 23
                })
                
            elif stage == "LANGUAGE_IDENTIFICATION":
                # Simulate language detection
                debug_logger.log_step("Simulating language identification", {
                    "detected_languages": ["Python", "JavaScript"],
                    "primary_language": "Python",
                    "confidence": 0.95
                })
                time.sleep(1)
                
            elif stage == "CODE_ANALYSIS":
                # Simulate static analysis
                debug_logger.log_step("Simulating static analysis tools", {
                    "tools": ["flake8", "pylint", "mypy"],
                    "files_analyzed": 15,
                    "issues_found": 42
                })
                time.sleep(1.5)
                
            elif stage == "CKG_OPERATIONS":
                # Simulate CKG building
                debug_logger.log_step("Simulating CKG construction", {
                    "nodes_created": 158,
                    "relationships_created": 234,
                    "node_types": ["File", "Function", "Class", "Import"]
                })
                time.sleep(1)
                
            elif stage == "LLM_SERVICES":
                # Simulate LLM processing
                debug_logger.log_step("Simulating LLM insights generation", {
                    "model": "gpt-4-turbo",
                    "tokens_processed": 1250,
                    "insights_generated": 8
                })
                time.sleep(1)
                
            elif stage == "SYNTHESIS_REPORTING":
                # Simulate report generation
                debug_logger.log_step("Simulating report synthesis", {
                    "report_sections": ["overview", "issues", "recommendations"],
                    "export_formats": ["json", "html", "pdf"]
                })
                time.sleep(0.5)
        
        # Simulate results generation
        repo_name = repo_url.split('/')[-1] if '/' in repo_url else repo_url
        fake_results = {
            'total_issues': 42,
            'files_analyzed': 15,
            'lines_of_code': 1523,
            'quality_score': 87,
            'severity_counts': {
                'critical': 2,
                'major': 8,
                'minor': 15,
                'info': 17
            },
            'repository': {
                'name': repo_name,
                'url': repo_url,
                'language': 'Python',
                'size': '150KB'
            },
            'summary': f"Repository {repo_name} has been analyzed successfully. Found 42 issues across 15 files."
        }
        
        # Log final results
        debug_logger.log_data("analysis_results", fake_results)
        
        st.session_state.analysis_results = fake_results
        st.session_state.analysis_in_progress = False
        
        # Save results to session
        from core.auth.session_manager import AuthenticatedScanResult
        scan_result = AuthenticatedScanResult(
            session_id=st.session_state.current_session_id,
            user_id=st.session_state.current_user.id,
            repository_url=repo_url,
            repository_name=repo_name,
            analysis_type="repository_analysis",
            findings_count=fake_results['total_issues'],
            severity_breakdown=fake_results['severity_counts'],
            summary=fake_results['summary'],
            detailed_results=fake_results,
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        
        st.session_state.session_manager.save_scan_result(
            st.session_state.current_session_id,
            st.session_state.current_user.id,
            scan_result
        )
        
        # Log session completion
        debug_logger.log_step("Analysis session completed", {
            "session_id": st.session_state.current_session_id,
            "total_issues": fake_results['total_issues'],
            "quality_score": fake_results['quality_score'],
            "files_analyzed": fake_results['files_analyzed']
        })
        
        # Finalize debug logging
        log_repository_analysis_end()
        
        status_text.text("✅ Analysis completed!")
        st.success("🎉 Repository analysis completed successfully!")
        
        # Display results
        render_analysis_results()


def render_authenticated_pr_interface(options: Dict[str, Any]):
    """Render PR analysis với user authentication."""
    st.markdown("### 🔄 Pull Request Review")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        repo_url = st.text_input(
            "🔗 Repository URL",
            placeholder="https://github.com/username/repository",
            help="Repository chứa Pull Request"
        )
    
    with col2:
        pr_id = st.text_input(
            "PR ID",
            placeholder="123",
            help="ID của Pull Request"
        )
    
    platform = st.selectbox(
        "Platform",
        ["GitHub", "GitLab", "BitBucket"],
        help="Chọn platform Git"
    )
    
    # PAT input
    show_pat = st.checkbox("🔐 Cần Personal Access Token", key="pr_pat_checkbox")
    pat = None
    if show_pat:
        pat = st.text_input(
            "Personal Access Token",
            type="password",
            help="PAT để truy cập repository",
            key="pr_pat_input"
        )
    
    if st.button("🔍 Phân tích PR", type="primary", use_container_width=True):
        if not repo_url or not pr_id:
            st.error("Vui lòng nhập đầy đủ Repository URL và PR ID!")
        elif show_pat and not pat:
            st.error("Vui lòng nhập Personal Access Token!")
        else:
            process_authenticated_pr_analysis(repo_url, pr_id, platform, pat, options)


def process_authenticated_pr_analysis(repo_url: str, pr_id: str, platform: str, pat: Optional[str], options: Dict[str, Any]):
    """Process PR analysis với user session tracking."""
    st.info("🔄 PR analysis functionality sẽ được implement trong phase 2")


def render_authenticated_qna_interface(options: Dict[str, Any]):
    """Render Q&A interface để người dùng đặt câu hỏi về code."""
    st.markdown("### ❓ Code Q&A")
    
    # Context source selection
    context_options = ["None", "Use Repository", "Previous Analysis"]
    context_source = st.selectbox(
        "📁 Nguồn ngữ cảnh:",
        context_options,
        help="Chọn nguồn thông tin để trả lời câu hỏi"
    )
    
    context_repo = None
    if context_source == "Use Repository":
        context_repo = st.text_input(
            "🔗 Repository URL:",
            placeholder="https://github.com/username/repository",
            help="URL repository để làm ngữ cảnh trả lời"
        )
        
        if context_repo:
            with st.spinner("📊 Đang load context từ repository..."):
                process_authenticated_context_loading(context_repo, options)
    
    # Question input
    question = st.text_area(
        "💬 Câu hỏi của bạn:",
        placeholder="Ví dụ: Class nào chịu trách nhiệm xử lý authentication? Hàm main() làm gì?",
        height=100,
        help="Đặt câu hỏi về cấu trúc code, chức năng, hoặc thiết kế"
    )
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        ask_button = st.button("🤖 Hỏi AI", type="primary", use_container_width=True)
    
    if ask_button and question:
        if context_source == "Use Repository" and not context_repo:
            st.error("⚠️ Vui lòng nhập URL repository cho ngữ cảnh!")
        else:
            process_authenticated_qna_question(question, context_repo, options)


def process_authenticated_context_loading(context_repo: str, options: Dict[str, Any]):
    """Process context loading với user session tracking."""
    st.info("🔄 Context loading functionality sẽ được implement trong phase 2")


def process_authenticated_qna_question(question: str, context_repo: Optional[str], options: Dict[str, Any]):
    """Process Q&A question với user session tracking."""
    # Create session if not exists
    if not st.session_state.current_session_id:
        session_id = st.session_state.session_manager.create_session(
            user_id=st.session_state.current_user.id,
            session_type=SessionType.CODE_QNA,
            title=f"Code Q&A - {time.strftime('%H:%M')}",
            description="Interactive code discussion"
        )
        st.session_state.current_session_id = session_id
    
    # Add user message to session
    st.session_state.session_manager.add_chat_message(
        st.session_state.current_session_id,
        st.session_state.current_user.id,
        "user",
        question
    )
    
    # Simulate AI response
    with st.spinner("🤖 AI đang suy nghĩ..."):
        time.sleep(2)  # Simulate processing
        
        ai_response = f"Cảm ơn bạn đã hỏi: '{question}'. Đây là phiên bản demo, AI response sẽ được implement trong phase 2 với LLM integration."
        
        # Add AI response to session
        st.session_state.session_manager.add_chat_message(
            st.session_state.current_session_id,
            st.session_state.current_user.id,
            "assistant",
            ai_response
        )
        
        st.success("✅ Câu hỏi đã được gửi!")
        st.rerun()


def render_analysis_results():
    """Render analysis results với support cho architectural findings và multi-language analysis."""
    if not st.session_state.analysis_results:
        return
    
    results = st.session_state.analysis_results
    
    st.markdown("## 📊 Kết quả Phân tích")
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Tổng Issues", results.get('total_issues', 0))
    
    with col2:
        st.metric("Files analyzed", results.get('files_analyzed', 0))
    
    with col3:
        st.metric("Lines of code", results.get('lines_of_code', 0))
    
    with col4:
        st.metric("Quality score", f"{results.get('quality_score', 85)}/100")
    
    # Architectural Issues
    architectural_issues = results.get('architectural_issues', {})
    if architectural_issues:
        st.markdown("### 🏗️ Architectural Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            circular_deps = architectural_issues.get('circular_dependencies', [])
            if circular_deps:
                st.markdown("#### 🔄 Circular Dependencies")
                for dep in circular_deps[:5]:  # Top 5
                    cycle_str = " → ".join(dep.get('cycle', []))
                    if cycle_str:
                        cycle_str += f" → {dep['cycle'][0]}"  # Complete the circle
                    st.markdown(f"- **{dep.get('cycle_type', 'file')} cycle**: {cycle_str}")
                    if dep.get('description'):
                        st.markdown(f"  *{dep['description']}*")
        
        with col2:
            unused_elements = architectural_issues.get('unused_elements', [])
            if unused_elements:
                st.markdown("#### 🗑️ Unused Public Elements")
                for element in unused_elements[:5]:  # Top 5
                    st.markdown(f"- **{element.get('element_type', 'element')}**: `{element.get('element_name', 'Unknown')}`")
                    st.markdown(f"  📄 {element.get('file_path', 'Unknown file')}")
                    if element.get('reason'):
                        st.markdown(f"  *{element['reason']}*")
        
        # Architectural limitations warning
        limitations = architectural_issues.get('limitations', [])
        if limitations:
            with st.expander("⚠️ Analysis Limitations"):
                for limitation in limitations:
                    st.markdown(f"- {limitation}")

    # Language Distribution Charts
    languages = results.get('languages', {})
    if languages and len(languages) > 1:
        st.markdown("### 📊 Ngôn ngữ Distribution")
        
        import plotly.express as px
        
        # Language files distribution
        lang_data = []
        for lang, data in languages.items():
            file_count = data.get('file_count', 0)
            if file_count > 0:
                lang_data.append({'Language': lang.title(), 'Files': file_count})
        
        if lang_data:
            import pandas as pd
            df = pd.DataFrame(lang_data)
            fig = px.pie(df, values='Files', names='Language', 
                        title="Files by Language",
                        color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)

    # Static Analysis Results by Language
    static_analysis = results.get('static_analysis_by_language', {})
    if static_analysis:
        st.markdown("### 🔍 Kết quả Static Analysis theo Ngôn ngữ")
        
        # Create tabs for each language
        languages = list(static_analysis.keys())
        if len(languages) == 1:
            # Single language - no tabs needed
            lang = languages[0]
            lang_results = static_analysis[lang]
            _render_language_analysis_results(lang, lang_results)
        else:
            # Multiple languages - use tabs
            tabs = st.tabs([f"📄 {lang.title()}" for lang in languages])
            
            for tab, lang in zip(tabs, languages):
                with tab:
                    lang_results = static_analysis[lang]
                    _render_language_analysis_results(lang, lang_results)
    
    # Summary
    st.markdown("### 📝 Tóm tắt")
    summary = results.get('summary', 'No summary available')
    if isinstance(summary, dict):
        # Detailed summary
        if summary.get('overall_quality'):
            st.markdown(f"**Chất lượng tổng thể:** {summary['overall_quality']}")
        if summary.get('key_issues'):
            st.markdown("**Vấn đề chính:**")
            for issue in summary['key_issues'][:5]:  # Top 5 issues
                st.markdown(f"- {issue}")
        if summary.get('recommendations'):
            st.markdown("**Khuyến nghị:**")
            for rec in summary['recommendations'][:3]:  # Top 3 recommendations
                st.markdown(f"- {rec}")
    else:
        st.markdown(summary)

def _render_language_analysis_results(language: str, results: Dict[str, Any]):
    """Render analysis results cho một ngôn ngữ cụ thể."""
    st.markdown(f"#### {language.title()} Analysis Results")
    
    # Tool-specific results
    tools_used = results.get('tools_used', [])
    if tools_used:
        st.markdown(f"**Tools sử dụng:** {', '.join(tools_used)}")
    
    # Findings count
    findings_count = results.get('findings_count', 0)
    st.metric(f"🔍 {language.title()} Issues", findings_count)
    
    # Top issues for this language
    top_issues = results.get('top_issues', [])
    if top_issues:
        st.markdown("**Top Issues:**")
        for issue in top_issues[:5]:
            severity_icon = {
                'critical': '🔴',
                'high': '🟠', 
                'medium': '🟡',
                'low': '🔵'
            }.get(issue.get('severity', 'medium').lower(), '🔵')
            
            st.markdown(f"{severity_icon} **{issue.get('rule_id', 'Unknown')}**: {issue.get('message', 'No message')}")
            if issue.get('file_path'):
                st.markdown(f"   📄 {issue['file_path']}{':' + str(issue['line_number']) if issue.get('line_number') else ''}")
    
    # Language-specific metrics
    if language.lower() == 'java':
        if results.get('checkstyle_issues'):
            st.metric("Checkstyle Issues", results['checkstyle_issues'])
        if results.get('pmd_issues'):
            st.metric("PMD Issues", results['pmd_issues'])
    elif language.lower() == 'kotlin':
        if results.get('detekt_issues'):
            st.metric("Detekt Issues", results['detekt_issues'])
    elif language.lower() == 'dart':
        if results.get('dart_analyzer_issues'):
            st.metric("Dart Analyzer Issues", results['dart_analyzer_issues'])
    elif language.lower() == 'python':
        if results.get('flake8_issues'):
            st.metric("Flake8 Issues", results['flake8_issues'])
        if results.get('pylint_issues'):
            st.metric("Pylint Issues", results['pylint_issues'])
        if results.get('mypy_issues'):
            st.metric("MyPy Issues", results['mypy_issues'])


def render_history_view():
    """Render view for historical session."""
    if not st.session_state.selected_history_session:
        st.error("No session selected")
        return
    
    session = st.session_state.session_manager.get_session(
        st.session_state.selected_history_session,
        st.session_state.current_user.id
    )
    
    if not session:
        st.error("Session not found")
        return
    
    st.markdown(f"## 📚 {session.title}")
    st.markdown(f"**Loại:** {session.session_type.value}")
    st.markdown(f"**Trạng thái:** {session.status.value}")
    st.markdown(f"**Tạo lúc:** {session.created_at}")
    
    if session.description:
        st.markdown(f"**Mô tả:** {session.description}")
    
    st.divider()
    
    # Show scan results if available
    if session.scan_result:
        st.markdown("### 📊 Kết quả Scan")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Findings", session.scan_result.findings_count)
        with col2:
            st.metric("Repository", session.scan_result.repository_name or "Unknown")
        with col3:
            st.metric("Analysis Type", session.scan_result.analysis_type)
        
        if session.scan_result.summary:
            st.markdown("**Tóm tắt:**")
            st.markdown(session.scan_result.summary)
    
    # Show chat messages if available
    if session.chat_messages:
        st.markdown("### 💬 Chat History")
        
        for message in session.chat_messages:
            if message.role == 'user':
                st.markdown(f"**🙋 You:** {message.content}")
            else:
                st.markdown(f"**🤖 AI:** {message.content}")


def load_custom_css():
    """Load custom CSS styles từ file."""
    try:
        css_file_path = Path(__file__).parent / "styles.css"
        if css_file_path.exists():
            with open(css_file_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
            return css_content
        else:
            logger.warning(f"CSS file not found: {css_file_path}")
            return ""
    except Exception as e:
        logger.error(f"Error loading CSS file: {str(e)}")
        return ""


def render_code_diagrams_interface(options: Dict[str, Any]):
    """Render interface để sinh sơ đồ code."""
    st.markdown("### 📊 Code Diagrams")
    
    # Repository URL for context
    col1, col2 = st.columns([3, 1])
    
    with col1:
        repo_url = st.text_input(
            "🔗 Repository URL",
            placeholder="https://github.com/username/repository",
            help="URL repository để analyze và sinh sơ đồ"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        load_repo = st.button("📥 Load Repository", type="secondary", use_container_width=True)
    
    # Diagram generation options
    st.markdown("---")
    st.markdown("#### ⚙️ Diagram Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Target element selection
        target_element = st.text_input(
            "🎯 Target Element",
            placeholder="ClassName hoặc module.path",
            help="Class name hoặc module path để tạo sơ đồ"
        )
        
        # Diagram type
        diagram_type = st.selectbox(
            "📋 Diagram Type",
            ["Class Diagram", "Interface Diagram", "Package Diagram", "Dependency Diagram", "Inheritance Diagram"],
            help="Loại sơ đồ muốn tạo"
        )
        
        # Output format
        output_format = st.selectbox(
            "🖼️ Output Format",
            ["PlantUML", "Mermaid"],
            help="Format output của sơ đồ"
        )
    
    with col2:
        # Diagram options
        st.markdown("**🔧 Options:**")
        
        include_relationships = st.checkbox(
            "Include Relationships",
            value=True,
            help="Bao gồm quan hệ giữa các classes"
        )
        
        include_methods = st.checkbox(
            "Include Methods",
            value=True,
            help="Hiển thị methods trong classes"
        )
        
        include_attributes = st.checkbox(
            "Include Attributes",
            value=True,
            help="Hiển thị attributes/fields"
        )
        
        filter_private = st.checkbox(
            "Filter Private Members",
            value=True,
            help="Ẩn private methods và attributes"
        )
        
        max_depth = st.slider(
            "Max Depth",
            min_value=1,
            max_value=5,
            value=2,
            help="Độ sâu tối đa cho related elements"
        )
    
    # Generate diagram button
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col2:
        generate_button = st.button("🎨 Generate Diagram", type="primary", use_container_width=True)
    
    # Process diagram generation
    if generate_button:
        if not repo_url:
            st.error("⚠️ Vui lòng nhập Repository URL!")
        elif not target_element:
            st.error("⚠️ Vui lòng nhập Target Element!")
        else:
            # Update options với diagram parameters
            diagram_options = {
                'repo_url': repo_url,
                'target_element': target_element,
                'diagram_type': diagram_type,
                'output_format': output_format,
                'include_relationships': include_relationships,
                'include_methods': include_methods,
                'include_attributes': include_attributes,
                'filter_private': filter_private,
                'max_depth': max_depth
            }
            options.update(diagram_options)
            
            process_diagram_generation(options)


def process_diagram_generation(options: Dict[str, Any]):
    """Process diagram generation request."""
    try:
        with st.spinner("🎨 Generating diagram..."):
            # Initialize diagram generator (mock for now)
            diagram_generator = DiagramGeneratorAgent(ckg_query_agent=None)
            
            # Map UI strings to enum values
            diagram_type_map = {
                "Class Diagram": DiagramType.CLASS_DIAGRAM,
                "Interface Diagram": DiagramType.INTERFACE_DIAGRAM,
                "Package Diagram": DiagramType.PACKAGE_DIAGRAM,
                "Dependency Diagram": DiagramType.DEPENDENCY_DIAGRAM,
                "Inheritance Diagram": DiagramType.INHERITANCE_DIAGRAM
            }
            
            output_format_map = {
                "PlantUML": DiagramFormat.PLANTUML,
                "Mermaid": DiagramFormat.MERMAID
            }
            
            # Generate diagram
            result = diagram_generator.generate_class_diagram_code(
                class_name_or_module_path=options['target_element'],
                diagram_type=options['output_format'].lower(),
                include_relationships=options['include_relationships'],
                include_methods=options['include_methods'],
                include_attributes=options['include_attributes'],
                filter_private=options['filter_private'],
                max_depth=options['max_depth']
            )
            
            if result.success:
                st.success("✅ Diagram generated successfully!")
                
                # Display results
                st.markdown("---")
                st.markdown("### 📊 Generated Diagram")
                
                # Info panel
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Target", result.target_element)
                with col2:
                    st.metric("Type", result.diagram_type.value.replace('_', ' ').title())
                with col3:
                    st.metric("Format", result.output_format.value.upper())
                with col4:
                    st.metric("Generation Time", f"{result.generation_time:.2f}s")
                
                # Diagram code display
                st.markdown("#### 📝 Diagram Code")
                
                # Display with syntax highlighting
                if result.output_format == DiagramFormat.PLANTUML:
                    st.code(result.diagram_code, language="plantuml")
                elif result.output_format == DiagramFormat.MERMAID:
                    st.code(result.diagram_code, language="mermaid")
                
                # Copy to clipboard button
                if st.button("📋 Copy to Clipboard"):
                    st.session_state['diagram_code'] = result.diagram_code
                    st.success("Code copied to session state!")
                
                # Render diagram if possible
                if result.output_format == DiagramFormat.MERMAID:
                    try:
                        st.markdown("#### 🎨 Rendered Diagram")
                        # Try to render Mermaid diagram using streamlit-agraph or similar
                        # For now, show as code with note
                        st.info("💡 **Tip**: Copy the Mermaid code above and paste it into [Mermaid Live Editor](https://mermaid.live/) để xem diagram được render.")
                        
                        # Display in expandable section for easy copying
                        with st.expander("📋 Mermaid Code for External Viewer"):
                            st.text_area(
                                "Mermaid Code:",
                                value=result.diagram_code,
                                height=200,
                                help="Copy code này và paste vào Mermaid viewer"
                            )
                    except Exception as e:
                        logger.warning(f"Could not render Mermaid diagram: {e}")
                
                elif result.output_format == DiagramFormat.PLANTUML:
                    st.markdown("#### 🎨 Diagram Preview")
                    st.info("💡 **Tip**: Copy the PlantUML code above và paste vào [PlantUML Server](http://www.plantuml.com/plantuml/uml/) để xem diagram được render.")
                    
                    # Display in expandable section for easy copying
                    with st.expander("📋 PlantUML Code for External Viewer"):
                        st.text_area(
                            "PlantUML Code:",
                            value=result.diagram_code,
                            height=200,
                            help="Copy code này và paste vào PlantUML viewer"
                        )
                
                # Additional info
                if result.elements_included:
                    st.markdown("#### 📋 Elements Included")
                    st.write(", ".join(result.elements_included))
                
                if result.relationships_included:
                    st.markdown("#### 🔗 Relationships Included")
                    st.write(", ".join(result.relationships_included))
                
                # Save to session
                if 'diagram_results' not in st.session_state:
                    st.session_state.diagram_results = []
                
                st.session_state.diagram_results.append({
                    'timestamp': time.time(),
                    'target_element': result.target_element,
                    'diagram_type': result.diagram_type.value,
                    'output_format': result.output_format.value,
                    'diagram_code': result.diagram_code,
                    'generation_time': result.generation_time
                })
                
            else:
                st.error(f"❌ Failed to generate diagram: {result.error_message}")
                
                if result.warnings:
                    st.warning("⚠️ Warnings:")
                    for warning in result.warnings:
                        st.write(f"• {warning}")
                        
    except Exception as e:
        logger.error(f"Diagram generation error: {e}")
        st.error(f"❌ Error generating diagram: {str(e)}")
        
        # Show debug info in expander
        with st.expander("🐛 Debug Information"):
            st.write("**Error Details:**")
            st.write(str(e))
            st.write("**Options:**")
            st.json(options)


def render_user_feedback_interface(options: Dict[str, Any]):
    """Render comprehensive user feedback interface."""
    st.markdown("### 📝 Phản hồi người dùng")
    
    # Tabs for feedback and analytics
    tab1, tab2, tab3 = st.tabs(["💬 Gửi phản hồi", "📊 Thống kê", "🔧 Cải tiến"])
    
    with tab1:
        render_feedback_form()
    
    with tab2:
        render_feedback_analytics()
    
    with tab3:
        render_improvement_roadmap()


def render_feedback_form():
    """Render feedback submission form."""
    st.markdown("#### 💬 Chia sẻ trải nghiệm của bạn")
    
    with st.form("feedback_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Rating
            rating = st.slider(
                "⭐ Đánh giá tổng thể (1-5 sao)",
                min_value=1,
                max_value=5,
                value=4,
                help="1 = Rất không hài lòng, 5 = Rất hài lòng"
            )
            
            # Satisfaction level
            satisfaction_options = {
                "Rất không hài lòng": SatisfactionLevel.VERY_DISSATISFIED,
                "Không hài lòng": SatisfactionLevel.DISSATISFIED,
                "Trung tính": SatisfactionLevel.NEUTRAL,
                "Hài lòng": SatisfactionLevel.SATISFIED,
                "Rất hài lòng": SatisfactionLevel.VERY_SATISFIED
            }
            satisfaction_text = st.selectbox(
                "😊 Mức độ hài lòng",
                list(satisfaction_options.keys()),
                index=3  # Default to "Hài lòng"
            )
            satisfaction_level = satisfaction_options[satisfaction_text]
            
            # Feedback type
            feedback_type_options = {
                "Phản hồi chung": FeedbackType.GENERAL,
                "Yêu cầu tính năng": FeedbackType.FEATURE_REQUEST,
                "Báo lỗi": FeedbackType.BUG_REPORT,
                "Cải tiến giao diện": FeedbackType.UI_IMPROVEMENT,
                "Vấn đề hiệu suất": FeedbackType.PERFORMANCE_ISSUE,
                "Tài liệu": FeedbackType.DOCUMENTATION
            }
            feedback_type_text = st.selectbox(
                "📋 Loại phản hồi",
                list(feedback_type_options.keys())
            )
            feedback_type = feedback_type_options[feedback_type_text]
        
        with col2:
            # Feature area
            feature_area_options = {
                "Phân tích Repository": FeatureArea.REPOSITORY_ANALYSIS,
                "Sơ đồ Code": FeatureArea.CODE_DIAGRAMS,
                "Review PR": FeatureArea.PR_REVIEW,
                "Hỏi đáp Code": FeatureArea.CODE_QNA,
                "Giao diện Web": FeatureArea.WEB_INTERFACE,
                "Xác thực": FeatureArea.AUTHENTICATION,
                "Báo cáo": FeatureArea.REPORTING,
                "Hỗ trợ đa ngôn ngữ": FeatureArea.MULTI_LANGUAGE_SUPPORT
            }
            feature_area_text = st.selectbox(
                "🎯 Khu vực tính năng",
                list(feature_area_options.keys())
            )
            feature_area = feature_area_options[feature_area_text]
            
            # Anonymous option
            anonymous = st.checkbox(
                "🕶️ Gửi phản hồi ẩn danh",
                value=False,
                help="Không lưu thông tin người dùng với phản hồi này"
            )
            
            # Contact email (optional)
            contact_email = st.text_input(
                "📧 Email liên hệ (tùy chọn)",
                placeholder="your.email@example.com",
                help="Để lại email nếu bạn muốn được phản hồi"
            )
        
        # Title and description
        title = st.text_input(
            "📝 Tiêu đề phản hồi",
            placeholder="Tóm tắt ngắn gọn về phản hồi của bạn",
            max_chars=100
        )
        
        description = st.text_area(
            "📄 Mô tả chi tiết",
            placeholder="Mô tả chi tiết về trải nghiệm, vấn đề gặp phải, hoặc đề xuất cải tiến...",
            height=120,
            max_chars=1000
        )
        
        suggestions = st.text_area(
            "💡 Đề xuất cải tiến",
            placeholder="Bạn có đề xuất gì để cải thiện trải nghiệm không?",
            height=80,
            max_chars=500
        )
        
        # Submit button
        submitted = st.form_submit_button(
            "🚀 Gửi phản hồi",
            type="primary",
            use_container_width=True
        )
        
        if submitted:
            if not title or not description:
                st.error("⚠️ Vui lòng điền tiêu đề và mô tả!")
            else:
                process_user_feedback_submission(
                    rating=rating,
                    satisfaction_level=satisfaction_level,
                    feedback_type=feedback_type,
                    feature_area=feature_area,
                    title=title,
                    description=description,
                    suggestions=suggestions,
                    contact_email=contact_email if contact_email else None,
                    anonymous=anonymous
                )


def render_feedback_analytics():
    """Render feedback analytics dashboard."""
    st.markdown("#### 📊 Thống kê phản hồi")
    
    try:
        analytics = st.session_state.feedback_collector.get_feedback_summary()
        
        if analytics.total_feedback_count == 0:
            st.info("📭 Chưa có phản hồi nào được thu thập.")
            return
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "📊 Tổng phản hồi",
                analytics.total_feedback_count,
                delta=analytics.recent_feedback_count,
                delta_color="normal"
            )
        
        with col2:
            st.metric(
                "⭐ Đánh giá TB",
                f"{analytics.average_rating:.1f}/5",
                delta=None
            )
        
        with col3:
            st.metric(
                "📈 Phản hồi gần đây",
                f"{analytics.recent_feedback_count} (7 ngày)",
                delta=None
            )
        
        with col4:
            st.metric(
                "📋 Tỷ lệ phản hồi",
                f"{analytics.response_rate:.1f}%",
                delta=None
            )
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 😊 Phân bố mức độ hài lòng")
            if analytics.satisfaction_distribution:
                satisfaction_data = {
                    k.replace('_', ' ').title(): v 
                    for k, v in analytics.satisfaction_distribution.items()
                    if v > 0
                }
                st.bar_chart(satisfaction_data)
            else:
                st.info("Không có dữ liệu mức độ hài lòng")
        
        with col2:
            st.markdown("##### 📋 Phân bố loại phản hồi")
            if analytics.feedback_type_distribution:
                feedback_data = {
                    k.replace('_', ' ').title(): v 
                    for k, v in analytics.feedback_type_distribution.items()
                    if v > 0
                }
                st.bar_chart(feedback_data)
            else:
                st.info("Không có dữ liệu loại phản hồi")
        
        # Feature area distribution
        st.markdown("##### 🎯 Phân bố theo khu vực tính năng")
        if analytics.feature_area_distribution:
            feature_data = {
                k.replace('_', ' ').title(): v 
                for k, v in analytics.feature_area_distribution.items()
                if v > 0
            }
            st.bar_chart(feature_data)
        else:
            st.info("Không có dữ liệu khu vực tính năng")
        
        # Recent feedback
        st.markdown("##### 📝 Phản hồi gần đây")
        recent_feedback = st.session_state.feedback_collector.get_recent_feedback(limit=5)
        
        if recent_feedback:
            for feedback in recent_feedback:
                with st.expander(f"⭐ {feedback.rating}/5 - {feedback.title}"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**Mô tả:** {feedback.description}")
                        if feedback.suggestions:
                            st.write(f"**Đề xuất:** {feedback.suggestions}")
                    with col2:
                        st.write(f"**Loại:** {feedback.feedback_type.value}")
                        st.write(f"**Khu vực:** {feedback.feature_area.value}")
                        st.write(f"**Thời gian:** {feedback.timestamp.strftime('%d/%m/%Y %H:%M')}")
        else:
            st.info("Không có phản hồi gần đây")
            
    except Exception as e:
        st.error(f"❌ Lỗi khi tải thống kê: {str(e)}")


def render_improvement_roadmap():
    """Render UI improvement roadmap."""
    st.markdown("#### 🔧 Lộ trình cải tiến")
    
    try:
        # Generate improvements from feedback
        if st.button("🔄 Phân tích phản hồi và tạo đề xuất cải tiến"):
            with st.spinner("Đang phân tích phản hồi..."):
                improvements = st.session_state.ui_improvement_agent.analyze_feedback_for_improvements()
                if improvements:
                    st.success(f"✅ Đã tạo {len(improvements)} đề xuất cải tiến!")
                else:
                    st.info("📭 Chưa có đủ phản hồi để tạo đề xuất cải tiến.")
        
        # Show improvement roadmap
        improvements = st.session_state.ui_improvement_agent.get_improvement_roadmap()
        
        if not improvements:
            st.info("📋 Chưa có đề xuất cải tiến nào. Hãy phân tích phản hồi để tạo đề xuất.")
            return
        
        # Filter by priority
        priority_filter = st.selectbox(
            "🎯 Lọc theo mức độ ưu tiên",
            ["Tất cả", "Critical", "High", "Medium", "Low"]
        )
        
        if priority_filter != "Tất cả":
            from agents.interaction_tasking.ui_improvement_agent import ImprovementPriority
            priority_map = {
                "Critical": ImprovementPriority.CRITICAL,
                "High": ImprovementPriority.HIGH,
                "Medium": ImprovementPriority.MEDIUM,
                "Low": ImprovementPriority.LOW
            }
            filtered_improvements = [
                imp for imp in improvements 
                if imp.priority == priority_map[priority_filter]
            ]
        else:
            filtered_improvements = improvements
        
        # Display improvements
        for improvement in filtered_improvements[:10]:  # Show top 10
            priority_color = {
                "CRITICAL": "🔴",
                "HIGH": "🟠", 
                "MEDIUM": "🟡",
                "LOW": "🟢"
            }.get(improvement.priority.name, "⚪")
            
            with st.expander(f"{priority_color} {improvement.title} ({improvement.priority.name})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Mô tả:** {improvement.description}")
                    st.write(f"**Ghi chú triển khai:** {improvement.implementation_notes}")
                    if improvement.related_feedback_ids:
                        st.write(f"**Liên quan đến phản hồi:** {len(improvement.related_feedback_ids)} phản hồi")
                
                with col2:
                    st.write(f"**Danh mục:** {improvement.category.value}")
                    st.write(f"**Khu vực:** {improvement.feature_area.value}")
                    st.write(f"**Ước tính công sức:** {improvement.estimated_effort}")
                    st.write(f"**Tác động dự kiến:** {improvement.expected_impact}")
                    st.write(f"**Trạng thái:** {improvement.status.value}")
                    
                    # Implementation button
                    if improvement.status.value == "planned":
                        if st.button(f"✅ Đánh dấu hoàn thành", key=f"impl_{improvement.improvement_id}"):
                            success = st.session_state.ui_improvement_agent.implement_improvement(
                                improvement.improvement_id,
                                "Marked as implemented via UI"
                            )
                            if success:
                                st.success("✅ Đã đánh dấu hoàn thành!")
                                st.rerun()
        
        # Improvement statistics
        st.markdown("##### 📈 Thống kê cải tiến")
        stats = st.session_state.ui_improvement_agent.get_improvement_stats()
        
        if stats:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📊 Tổng cải tiến", stats.get("total_improvements", 0))
            
            with col2:
                st.metric("✅ Tỷ lệ hoàn thành", f"{stats.get('implementation_rate', 0):.1f}%")
            
            with col3:
                critical_count = stats.get("by_priority", {}).get("CRITICAL", 0)
                st.metric("🔴 Cải tiến quan trọng", critical_count)
            
    except Exception as e:
        st.error(f"❌ Lỗi khi tải lộ trình cải tiến: {str(e)}")


def process_user_feedback_submission(
    rating: int,
    satisfaction_level: SatisfactionLevel,
    feedback_type: FeedbackType,
    feature_area: FeatureArea,
    title: str,
    description: str,
    suggestions: str,
    contact_email: Optional[str],
    anonymous: bool
):
    """Process user feedback submission."""
    try:
        # Create feedback object
        feedback = UserFeedback(
            feedback_id="",  # Will be generated
            user_id=None if anonymous else (st.session_state.current_user.user_id if st.session_state.current_user else None),
            session_id=st.session_state.current_session_id,
            feedback_type=feedback_type,
            feature_area=feature_area,
            satisfaction_level=satisfaction_level,
            rating=rating,
            title=title,
            description=description,
            suggestions=suggestions,
            contact_email=contact_email,
            anonymous=anonymous,
            timestamp=datetime.now()
        )
        
        # Submit feedback
        success = st.session_state.feedback_collector.collect_feedback(feedback)
        
        if success:
            st.success("🎉 Cảm ơn bạn đã gửi phản hồi! Chúng tôi sẽ sử dụng thông tin này để cải thiện dịch vụ.")
            st.balloons()
            
            # Show appreciation message based on rating
            if rating >= 4:
                st.info("😊 Rất vui khi bạn hài lòng với dịch vụ của chúng tôi!")
            elif rating == 3:
                st.info("🤔 Chúng tôi sẽ cố gắng cải thiện để mang lại trải nghiệm tốt hơn!")
            else:
                st.warning("😔 Chúng tôi xin lỗi vì trải nghiệm chưa tốt. Phản hồi của bạn rất quan trọng để chúng tôi cải thiện!")
        else:
            st.error("❌ Có lỗi xảy ra khi gửi phản hồi. Vui lòng thử lại!")
            
    except Exception as e:
        st.error(f"❌ Lỗi khi xử lý phản hồi: {str(e)}")
        logger.error(f"Error processing feedback: {e}")


def main():
    """Main authenticated Streamlit application."""
    # Initialize authentication system
    initialize_auth_system()
    
    # Initialize session state
    initialize_session_state()
    
    # Load and apply custom CSS styling
    custom_css = load_custom_css()
    if custom_css:
        st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)
    else:
        # Fallback CSS nếu file không load được
        st.markdown("""
            <style>
            /* Fallback CSS - Critical tab fixes only */
            [data-baseweb="tab-highlight"] {
                display: none !important;
            }
            
            .st-c2.st-c3.st-c4.st-c5.st-c6.st-c7.st-cy.st-c9.st-cq.st-e6.st-e7 {
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
                z-index: -1 !important;
            }
            
            [data-baseweb="tab-border"] {
                z-index: 2 !important;
            }
            </style>
        """, unsafe_allow_html=True)
    
    # Check authentication
    if not check_authentication():
        render_login_page()
        return
    
    # Render authenticated interface
    render_authenticated_header()
    render_authenticated_sidebar()
    
    # Main content based on view mode
    if st.session_state.view_mode == "dashboard":
        render_dashboard()
    elif st.session_state.view_mode == "new_session":
        render_new_session_interface()
    elif st.session_state.view_mode == "history_view":
        render_history_view()
    else:
        render_dashboard()


if __name__ == "__main__":
    main() 