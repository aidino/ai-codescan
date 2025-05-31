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
        
        # Navigation section với modern buttons
        st.markdown("""
            <h3 style="color: #495057; font-size: 1rem; margin-bottom: 1rem;">🧭 Điều hướng</h3>
        """, unsafe_allow_html=True)
        
        nav_buttons = [
            ("📊 Dashboard", "dashboard", "primary" if st.session_state.view_mode == "dashboard" else "secondary"),
            ("🆕 Scan mới", "new_session", "primary" if st.session_state.view_mode == "new_session" else "secondary"),
            ("💬 Chat mới", "new_chat", "secondary")
        ]
        
        for label, mode, button_type in nav_buttons:
            if st.button(label, use_container_width=True, type=button_type, key=f"nav_{mode}"):
                if mode == "new_chat":
                    create_new_chat_session()
                else:
                    st.session_state.view_mode = mode
                    if mode == "new_session":
                        st.session_state.selected_history_session = None
                    st.rerun()
        
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
                
                # Create session button với hover effect
                button_style = """
                    background: white;
                    border: 1px solid #e1e5e9;
                    border-radius: 10px;
                    padding: 0.75rem;
                    margin-bottom: 0.5rem;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    text-align: left;
                    width: 100%;
                """
                
                if st.button(
                    f"{type_icon} {title}\n{status_icon} {session.status.value}",
                    key=f"session_{session.session_id}_{i}",
                    use_container_width=True,
                    help=f"Created: {session.created_at[:10] if session.created_at else 'Unknown'}"
                ):
                    view_session(session.session_id)
        else:
            st.markdown("""
                <div style="
                    text-align: center;
                    padding: 2rem 1rem;
                    background: #f8f9fa;
                    border-radius: 10px;
                    color: #6c757d;
                    border: 2px dashed #dee2e6;
                ">
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
        ["Repository Review", "Pull Request Review", "Code Q&A"],
        help="Chọn loại phân tích bạn muốn thực hiện"
    )
    
    # Advanced Options
    with st.expander("⚙️ Tùy chọn nâng cao"):
        col1, col2 = st.columns(2)
        
        with col1:
            force_language = st.selectbox(
                "Ngôn ngữ cụ thể",
                ["Auto-detect", "Python", "Java", "Dart", "Kotlin"],
                help="Ghi đè tự động phát hiện ngôn ngữ"
            )
            
            include_tests = st.checkbox(
                "Bao gồm file test",
                value=True,
                help="Bao gồm các file test trong phân tích"
            )
        
        with col2:
            detailed_analysis = st.checkbox(
                "Phân tích chi tiết",
                value=False,
                help="Bật phân tích chi tiết hơn nhưng chậm hơn"
            )
    
    # Update options
    options.update({
        'analysis_type': analysis_type,
        'force_language': None if force_language == "Auto-detect" else force_language.lower(),
        'include_tests': include_tests,
        'detailed_analysis': detailed_analysis
    })
    
    # Render appropriate interface based on analysis type
    if analysis_type == "Repository Review":
        render_authenticated_repository_interface(options)
    elif analysis_type == "Pull Request Review":
        render_authenticated_pr_interface(options)
    elif analysis_type == "Code Q&A":
        render_authenticated_qna_interface(options)


def render_authenticated_repository_interface(options: Dict[str, Any]):
    """Render repository analysis với user authentication."""
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
    
    # PAT input
    show_pat = st.checkbox("🔐 Repository riêng tư (cần Personal Access Token)")
    pat = None
    if show_pat:
        pat = st.text_input(
            "Personal Access Token",
            type="password",
            help="Nhập PAT để truy cập repository riêng tư"
        )
    
    if analyze_button and repo_url:
        if show_pat and not pat:
            st.error("Vui lòng nhập Personal Access Token cho repository riêng tư!")
        else:
            process_authenticated_repository_analysis(repo_url, pat, options)


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


def render_authenticated_qna_interface(options: Dict[str, Any]):
    """Render Q&A interface với user authentication."""
    st.markdown("### ❓ Code Q&A")
    
    # Context repository
    st.markdown("#### 📦 Context Repository (tuỳ chọn)")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        context_repo = st.text_input(
            "Repository URL để làm context",
            placeholder="https://github.com/username/repository",
            help="Repository để cung cấp context cho câu hỏi"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📥 Load Context"):
            if context_repo:
                process_authenticated_context_loading(context_repo, options)
    
    # Chat interface
    st.markdown("#### 💬 Chat Interface")
    
    # Load existing chat messages from current session
    if st.session_state.current_session_id:
        session = st.session_state.session_manager.get_session(
            st.session_state.current_session_id,
            st.session_state.current_user.id
        )
        
        if session and session.chat_messages:
            for message in session.chat_messages:
                if message.role == 'user':
                    st.markdown(f"**🙋 You:** {message.content}")
                else:
                    st.markdown(f"**🤖 AI:** {message.content}")
            st.divider()
    
    # Chat input
    user_question = st.text_area(
        "Đặt câu hỏi về code:",
        placeholder="Ví dụ: Giải thích function này hoạt động như thế nào?",
        height=100
    )
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("💬 Gửi câu hỏi", type="primary", use_container_width=True):
            if user_question.strip():
                process_authenticated_qna_question(user_question, context_repo, options)
            else:
                st.error("Vui lòng nhập câu hỏi!")


def process_authenticated_repository_analysis(repo_url: str, pat: Optional[str], options: Dict[str, Any]):
    """Process repository analysis với user session tracking."""
    # Import debug logging
    from core.logging import log_repository_analysis_start, get_debug_logger
    
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
        from core.logging import log_repository_analysis_end
        log_repository_analysis_end()
        
        status_text.text("✅ Analysis completed!")
        st.success("🎉 Repository analysis completed successfully!")
        
        # Display results
        render_analysis_results()


def process_authenticated_pr_analysis(repo_url: str, pr_id: str, platform: str, pat: Optional[str], options: Dict[str, Any]):
    """Process PR analysis với user session tracking."""
    st.info("🔄 PR analysis functionality sẽ được implement trong phase 2")


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
    """Render analysis results."""
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
    
    # Severity breakdown
    st.markdown("### ⚠️ Phân bố mức độ nghiêm trọng")
    
    severity_data = results.get('severity_counts', {})
    if severity_data:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🔴 Critical", severity_data.get('critical', 0))
        with col2:
            st.metric("🟠 Major", severity_data.get('major', 0))
        with col3:
            st.metric("🟡 Minor", severity_data.get('minor', 0))
        with col4:
            st.metric("🔵 Info", severity_data.get('info', 0))
    
    # Summary
    st.markdown("### 📝 Tóm tắt")
    st.markdown(results.get('summary', 'No summary available'))


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