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
    page_title="AI CodeScan - Authenticated",
    page_icon="🔍",
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

# Import existing components
from agents.interaction_tasking.user_intent_parser import UserIntentParserAgent
from agents.interaction_tasking.dialog_manager import DialogManagerAgent
from agents.interaction_tasking.task_initiation import TaskInitiationAgent
from agents.interaction_tasking.presentation import PresentationAgent
from agents.interaction_tasking.history_manager import SessionType, SessionStatus


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
    """Render login/register page."""
    st.markdown("# 🔍 AI CodeScan")
    st.markdown("### AI-powered Code Review Assistant với Authentication")
    st.markdown("---")
    
    # Create tabs for login và register
    login_tab, register_tab = st.tabs(["🔑 Đăng nhập", "📝 Đăng ký"])
    
    with login_tab:
        render_login_form()
    
    with register_tab:
        render_register_form()


def render_login_form():
    """Render login form."""
    st.markdown("### 🔑 Đăng nhập")
    
    with st.form("login_form"):
        username_or_email = st.text_input(
            "Username hoặc Email",
            placeholder="Nhập username hoặc email"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Nhập password"
        )
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            submit = st.form_submit_button("🔑 Đăng nhập", type="primary", use_container_width=True)
        
        if submit:
            if not username_or_email or not password:
                st.error("⚠️ Vui lòng nhập đầy đủ thông tin!")
                return
            
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
                st.rerun()
            else:
                st.error(f"❌ Đăng nhập thất bại: {result.error_message}")


def render_register_form():
    """Render registration form."""
    st.markdown("### 📝 Đăng ký tài khoản mới")
    
    with st.form("register_form"):
        username = st.text_input(
            "Username",
            placeholder="Chọn username (3-50 ký tự)"
        )
        
        email = st.text_input(
            "Email",
            placeholder="Nhập địa chỉ email"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Nhập password (tối thiểu 8 ký tự)"
        )
        
        confirm_password = st.text_input(
            "Xác nhận Password",
            type="password",
            placeholder="Nhập lại password"
        )
        
        display_name = st.text_input(
            "Tên hiển thị (tuỳ chọn)",
            placeholder="Tên hiển thị trong hệ thống"
        )
        
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
            else:
                st.error("❌ Đăng ký thất bại. Username hoặc email có thể đã tồn tại.")


def render_authenticated_header():
    """Render header for authenticated users."""
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        st.markdown("# 🔍 AI CodeScan")
    
    with col2:
        st.markdown(f"### Xin chào, **{st.session_state.current_user.username}** 👋")
        st.caption(f"Role: {st.session_state.current_user.role.value}")
    
    with col3:
        # More prominent logout button
        st.markdown("")  # Add some spacing
        if st.button("🚪 Đăng xuất", type="primary", use_container_width=True):
            logout_user()


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
        # User profile section
        st.markdown(f"### 👤 {st.session_state.current_user.username}")
        st.markdown(f"**Role:** {st.session_state.current_user.role.value}")
        
        # Quick logout option in sidebar too
        if st.button("🚪 Logout", key="sidebar_logout", use_container_width=True, type="secondary"):
            logout_user()
        
        st.divider()
        
        # Navigation
        st.markdown("### 🧭 Điều hướng")
        
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.view_mode = "dashboard"
            st.rerun()
        
        if st.button("🆕 Scan mới", use_container_width=True):
            st.session_state.view_mode = "new_session"
            st.session_state.selected_history_session = None
            st.rerun()
        
        if st.button("💬 Chat mới", use_container_width=True):
            create_new_chat_session()
        
        st.divider()
        
        # User sessions history
        render_user_session_history()
        
        st.divider()
        
        # User info và settings
        render_user_info()


def render_user_session_history():
    """Render user's session history."""
    st.markdown("### 📚 Lịch sử Sessions")
    
    # Get user sessions
    sessions = st.session_state.session_manager.get_user_sessions(
        st.session_state.current_user.id,
        limit=10
    )
    
    if not sessions:
        st.info("Chưa có session nào")
        return
    
    # Group by type
    scan_sessions = [s for s in sessions if s.session_type == SessionType.REPOSITORY_ANALYSIS]
    chat_sessions = [s for s in sessions if s.session_type == SessionType.CODE_QNA]
    
    # Scan history
    if scan_sessions:
        st.markdown("#### 📊 Scans")
        for session in scan_sessions[:5]:
            status_icon = "✅" if session.status == SessionStatus.COMPLETED else "🔄"
            if st.button(
                f"{status_icon} {session.title}",
                key=f"scan_{session.session_id}",
                use_container_width=True
            ):
                view_session(session.session_id)
    
    # Chat history  
    if chat_sessions:
        st.markdown("#### 💬 Chats")
        for session in chat_sessions[:5]:
            status_icon = "✅" if session.status == SessionStatus.COMPLETED else "🔄"
            if st.button(
                f"{status_icon} {session.title}",
                key=f"chat_{session.session_id}",
                use_container_width=True
            ):
                view_session(session.session_id)


def render_user_info():
    """Render user information và settings."""
    st.markdown("### ⚙️ Tài khoản")
    
    # User stats
    stats = st.session_state.session_manager.get_user_session_stats(
        st.session_state.current_user.id
    )
    
    st.metric("Tổng sessions", stats['total_sessions'])
    
    if stats['by_status']:
        completed = stats['by_status'].get('completed', 0)
        in_progress = stats['by_status'].get('in_progress', 0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Hoàn thành", completed)
        with col2:
            st.metric("Đang xử lý", in_progress)


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
    st.markdown("## 📊 Dashboard")
    
    # User overview
    col1, col2, col3, col4 = st.columns(4)
    
    stats = st.session_state.session_manager.get_user_session_stats(
        st.session_state.current_user.id
    )
    
    with col1:
        st.metric("Tổng Sessions", stats['total_sessions'])
    
    with col2:
        completed = stats['by_status'].get('completed', 0)
        st.metric("Hoàn thành", completed)
    
    with col3:
        scans = stats['by_type'].get('repository_analysis', 0)
        st.metric("Repository Scans", scans)
    
    with col4:
        chats = stats['by_type'].get('code_qna', 0) 
        st.metric("Chat Sessions", chats)
    
    st.divider()
    
    # Recent activity
    st.markdown("### 📈 Hoạt động gần đây")
    
    if stats['recent_activity']:
        for activity in stats['recent_activity']:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    type_icon = "📊" if activity['type'] == 'repository_analysis' else "💬"
                    st.markdown(f"{type_icon} **{activity['title']}**")
                
                with col2:
                    status_icon = "✅" if activity['status'] == 'completed' else "🔄"
                    st.markdown(f"{status_icon} {activity['status']}")
                
                with col3:
                    updated = activity['updated_at'][:10] if activity['updated_at'] else "Unknown"
                    st.markdown(f"📅 {updated}")
    else:
        st.info("Chưa có hoạt động nào")
    
    # Quick actions
    st.markdown("### 🚀 Thao tác nhanh")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Scan Repository mới", use_container_width=True):
            st.session_state.view_mode = "new_session"
            st.rerun()
    
    with col2:
        if st.button("💬 Bắt đầu Chat", use_container_width=True):
            create_new_chat_session()
    
    with col3:
        if st.button("📚 Xem tất cả Sessions", use_container_width=True):
            st.session_state.view_mode = "all_sessions"
            st.rerun()


def render_new_session_interface():
    """Render interface for creating new session."""
    from agents.interaction_tasking.web_ui import render_new_session_interface as render_original
    
    # Create temporary options dict
    options = {}
    
    # Call original interface but with user context
    st.markdown("## 🔍 AI CodeScan - Phân tích Code Thông minh")
    
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
    
    st.session_state.analysis_in_progress = True
    
    with st.spinner("🔄 Đang phân tích repository..."):
        # Simulate analysis
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        steps = [
            "Cloning repository...",
            "Analyzing code structure...",
            "Running static analysis...",
            "Building knowledge graph...",
            "Generating insights...",
            "Preparing results..."
        ]
        
        for i, step in enumerate(steps):
            status_text.text(f"📋 {step}")
            progress_bar.progress((i + 1) / len(steps))
            time.sleep(1)  # Simulate work
        
        # Simulate results
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


def main():
    """Main authenticated Streamlit application."""
    # Initialize authentication system
    initialize_auth_system()
    
    # Initialize session state
    initialize_session_state()
    
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