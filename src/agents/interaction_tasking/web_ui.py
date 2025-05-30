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

# Configure page FIRST (must be first Streamlit command)
st.set_page_config(
    page_title="AI CodeScan",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

from loguru import logger

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.interaction_tasking.user_intent_parser import UserIntentParserAgent
from agents.interaction_tasking.dialog_manager import DialogManagerAgent
from agents.interaction_tasking.task_initiation import TaskInitiationAgent
from agents.interaction_tasking.presentation import PresentationAgent
from agents.interaction_tasking.history_manager import (
    HistoryManager, SessionType, SessionStatus, ScanResult, ChatMessage
)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = None
    
    if "history_manager" not in st.session_state:
        st.session_state.history_manager = HistoryManager()
    
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None
    
    if "analysis_in_progress" not in st.session_state:
        st.session_state.analysis_in_progress = False
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    if "selected_history_session" not in st.session_state:
        st.session_state.selected_history_session = None
    
    if "view_mode" not in st.session_state:
        st.session_state.view_mode = "new_session"  # "new_session" or "history_view"


def render_header():
    """Render the main header and navigation."""
    st.title("🔍 AI CodeScan")
    st.markdown("### AI-powered Code Review Assistant")
    st.markdown("---")


def render_sidebar():
    """Render sidebar with history management and controls."""
    with st.sidebar:
        st.markdown("### 🔍 AI CodeScan")
        
        # New Session Buttons
        st.markdown("#### ➕ Tạo mới")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🆕 Scan mới", use_container_width=True):
                create_new_session()
        
        with col2:
            if st.button("💬 Chat mới", use_container_width=True):
                create_new_chat_session()
        
        st.divider()
        
        # History Section
        st.markdown("#### 📚 Lịch sử")
        
        # History filter tabs
        history_tab1, history_tab2 = st.tabs(["📊 Scans", "💬 Chats"])
        
        with history_tab1:
            render_scan_history()
        
        with history_tab2:
            render_chat_history()
        
        st.divider()
        
        # Session Info
        render_session_info()


def create_new_session():
    """Create new analysis session."""
    st.session_state.view_mode = "new_session"
    st.session_state.selected_history_session = None
    st.session_state.analysis_results = None
    st.session_state.analysis_in_progress = False
    st.session_state.current_session_id = None
    st.rerun()


def create_new_chat_session():
    """Create new chat session."""
    session_id = st.session_state.history_manager.create_session(
        session_type=SessionType.CODE_QNA,
        title=f"Chat Session - {time.strftime('%Y-%m-%d %H:%M')}",
        description="Interactive Q&A session"
    )
    
    st.session_state.current_session_id = session_id
    st.session_state.view_mode = "new_session"
    st.session_state.selected_history_session = None
    st.session_state.chat_messages = []
    st.success(f"🆕 Đã tạo chat session mới!")
    st.rerun()


def render_scan_history():
    """Render scan history in sidebar."""
    scan_sessions = st.session_state.history_manager.get_recent_sessions(
        limit=10, 
        session_type=SessionType.REPOSITORY_ANALYSIS
    )
    
    if not scan_sessions:
        st.write("*Chưa có scan nào*")
        return
    
    for session in scan_sessions:
        # Format display
        status_icon = {
            "completed": "✅",
            "in_progress": "⏳", 
            "error": "❌",
            "cancelled": "🚫"
        }.get(session.status.value, "⏳")
        
        title = session.title[:30] + "..." if len(session.title) > 30 else session.title
        display_text = f"{status_icon} {title}"
        
        if st.button(display_text, key=f"scan_{session.session_id}", use_container_width=True):
            view_history_session(session.session_id)


def render_chat_history():
    """Render chat history in sidebar."""
    chat_sessions = st.session_state.history_manager.get_recent_sessions(
        limit=10,
        session_type=SessionType.CODE_QNA
    )
    
    if not chat_sessions:
        st.write("*Chưa có chat nào*")
        return
    
    for session in chat_sessions:
        status_icon = {
            "completed": "✅",
            "in_progress": "⏳",
            "error": "❌", 
            "cancelled": "🚫"
        }.get(session.status.value, "⏳")
        
        title = session.title[:30] + "..." if len(session.title) > 30 else session.title
        display_text = f"{status_icon} {title}"
        
        if st.button(display_text, key=f"chat_{session.session_id}", use_container_width=True):
            view_history_session(session.session_id)


def view_history_session(session_id: str):
    """View historical session (read-only)."""
    st.session_state.view_mode = "history_view"
    st.session_state.selected_history_session = session_id
    st.rerun()


def render_session_info():
    """Render current session information."""
    st.markdown("#### ℹ️ Session Info")
    
    if st.session_state.view_mode == "history_view":
        st.write("📖 **Chế độ**: Xem lịch sử")
        st.write("🔒 **Read-only mode**")
    else:
        st.write("✏️ **Chế độ**: Session mới")
        if st.session_state.current_session_id:
            st.write(f"🆔 **ID**: {st.session_state.current_session_id[:8]}...")
    
    # Session stats
    stats = st.session_state.history_manager.get_session_stats()
    st.write(f"📊 **Tổng sessions**: {stats['total_sessions']}")
    
    if stats['by_type']:
        st.write("**Theo loại**:")
        for session_type, count in stats['by_type'].items():
            type_name = {
                'repository_analysis': 'Repo Scan',
                'pr_review': 'PR Review', 
                'code_qna': 'Q&A Chat'
            }.get(session_type, session_type)
            st.write(f"• {type_name}: {count}")


def render_history_view():
    """Render historical session view (read-only)."""
    session_id = st.session_state.selected_history_session
    if not session_id:
        st.error("Không tìm thấy session!")
        return
    
    session = st.session_state.history_manager.get_session(session_id)
    if not session:
        st.error("Session không tồn tại!")
        return
    
    # Header
    st.markdown("## 📖 Xem Lịch sử Session")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"**{session.title}**")
    with col2:
        status_color = {
            "completed": "green",
            "in_progress": "orange",
            "error": "red",
            "cancelled": "gray"
        }.get(session.status.value, "blue")
        st.markdown(f":{status_color}[{session.status.value.title()}]")
    with col3:
        st.write(f"📅 {session.created_at[:10]}")
    
    st.write(f"**Mô tả**: {session.description}")
    st.write(f"**Loại**: {session.session_type.value}")
    
    # Warning about read-only mode
    st.warning("🔒 **Chế độ chỉ xem**: Đây là lịch sử session. Bạn không thể tiếp tục trò chuyện để tránh vấn đề context đã thay đổi.")
    
    # Display content based on session type
    if session.session_type == SessionType.REPOSITORY_ANALYSIS and session.scan_result:
        render_historical_scan_result(session.scan_result)
    elif session.session_type == SessionType.CODE_QNA and session.chat_messages:
        render_historical_chat_messages(session.chat_messages)
    else:
        st.info("Session này chưa có dữ liệu hoặc đang trong quá trình xử lý.")


def render_historical_scan_result(scan_result: ScanResult):
    """Render historical scan result (read-only)."""
    st.markdown("### 📊 Kết quả Scan")
    
    # Basic info
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Repository**: {scan_result.repository_name}")
        st.write(f"**URL**: {scan_result.repository_url}")
    with col2:
        st.write(f"**Loại phân tích**: {scan_result.analysis_type}")
        st.write(f"**Số findings**: {scan_result.findings_count}")
    
    # Summary
    st.markdown("#### 📝 Tóm tắt")
    st.write(scan_result.summary)
    
    # Severity breakdown
    if scan_result.severity_breakdown:
        st.markdown("#### ⚠️ Phân loại mức độ nghiêm trọng")
        for severity, count in scan_result.severity_breakdown.items():
            st.write(f"• **{severity}**: {count}")
    
    # Detailed results
    if scan_result.detailed_results:
        st.markdown("#### 🔍 Chi tiết kết quả")
        st.json(scan_result.detailed_results)


def render_historical_chat_messages(chat_messages: list):
    """Render historical chat messages (read-only)."""
    st.markdown("### 💬 Lịch sử Trò chuyện")
    
    for message in chat_messages:
        if isinstance(message, dict):
            role = message.get('role', 'unknown')
            content = message.get('content', '')
            timestamp = message.get('timestamp', '')
        else:
            role = message.role
            content = message.content
            timestamp = message.timestamp
        
        # Format timestamp
        time_str = timestamp[:19] if len(timestamp) > 19 else timestamp
        
        if role == "user":
            st.markdown(f"**🙋 User** _{time_str}_")
            st.write(content)
        elif role == "assistant":
            st.markdown(f"**🤖 Assistant** _{time_str}_")
            st.write(content)
        
        st.divider()


def render_main_interface(options: Dict[str, Any]):
    """Render the main interface content."""
    if st.session_state.view_mode == "history_view":
        render_history_view()
    else:
        render_new_session_interface(options)


def render_new_session_interface(options: Dict[str, Any]):
    """Render interface for new session."""
    st.markdown("## 🔍 AI CodeScan - Phân tích Code Thông minh")
    
    # Analysis Type Selection with modern styling
    st.markdown("### 📋 Chọn loại phân tích")
    
    analysis_type = st.selectbox(
        "Loại phân tích",
        ["Repository Review", "Pull Request Review", "Code Q&A"],
        help="Chọn loại phân tích bạn muốn thực hiện"
    )
    
    # Advanced Options in expandable section
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
    
    # Update options with advanced settings
    options.update({
        'analysis_type': analysis_type,
        'force_language': None if force_language == "Auto-detect" else force_language.lower(),
        'include_tests': include_tests,
        'detailed_analysis': detailed_analysis
    })
    
    # Render appropriate interface based on analysis type
    if analysis_type == "Repository Review":
        render_repository_interface(options)
    elif analysis_type == "Pull Request Review":
        render_pr_interface(options)
    elif analysis_type == "Code Q&A":
        render_qna_interface(options)


def render_repository_interface(options: Dict[str, Any]):
    """Render repository analysis interface."""
    st.markdown("### 📦 Repository Analysis")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        repo_url = st.text_input(
            "🔗 Repository URL",
            placeholder="https://github.com/username/repository",
            help="Nhập URL của repository bạn muốn phân tích"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
        analyze_button = st.button("🔍 Phân tích Repository", type="primary", use_container_width=True)
    
    # PAT input for private repositories
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
            process_repository_analysis(repo_url, pat, options)
    
    # Display results if available
    if st.session_state.analysis_results:
        render_analysis_results()


def render_pr_interface(options: Dict[str, Any]):
    """Render Pull Request review interface."""
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
            process_pr_analysis(repo_url, pr_id, platform, pat, options)
    
    # Display results
    if st.session_state.analysis_results:
        render_analysis_results()


def render_qna_interface(options: Dict[str, Any]):
    """Render Q&A interface with chat functionality."""
    st.markdown("### ❓ Code Q&A")
    
    # Repository context input
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
                process_context_loading(context_repo, options)
    
    # Chat interface
    st.markdown("#### 💬 Chat Interface")
    
    # Display chat history
    if st.session_state.chat_messages:
        for message in st.session_state.chat_messages:
            if message['role'] == 'user':
                st.markdown(f"**🙋 You:** {message['content']}")
            else:
                st.markdown(f"**🤖 AI:** {message['content']}")
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
                process_qna_question(user_question, context_repo, options)
            else:
                st.error("Vui lòng nhập câu hỏi!")


def process_repository_analysis(repo_url: str, pat: Optional[str], options: Dict[str, Any]):
    """Process repository analysis with history tracking."""
    # Create session if not exists
    if not st.session_state.current_session_id:
        repo_name = repo_url.split('/')[-1] if '/' in repo_url else repo_url
        session_id = st.session_state.history_manager.create_session(
            session_type=SessionType.REPOSITORY_ANALYSIS,
            title=f"Repository Scan: {repo_name}",
            description=f"Analysis of {repo_url}",
            metadata={"repo_url": repo_url, "options": options}
        )
        st.session_state.current_session_id = session_id
    
    st.session_state.analysis_in_progress = True
    
    with st.spinner("🔄 Đang phân tích repository..."):
        # Simulate analysis process
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Mock analysis steps
            steps = [
                ("📥 Cloning repository...", 20),
                ("🔍 Analyzing code structure...", 40),
                ("🧪 Running static analysis...", 60),
                ("📊 Generating insights...", 80),
                ("✅ Finalizing results...", 100)
            ]
            
            for step_text, progress in steps:
                status_text.text(step_text)
                progress_bar.progress(progress)
                time.sleep(1)  # Simulate processing time
            
            # Generate mock results
            results = create_mock_analysis_results(repo_url, options)
            st.session_state.analysis_results = results
            
            # Save to history
            repo_name = repo_url.split('/')[-1] if '/' in repo_url else repo_url
            scan_result = ScanResult(
                repository_url=repo_url,
                repository_name=repo_name,
                analysis_type="Repository Analysis",
                findings_count=results.get('total_issues', 0),
                severity_breakdown=results.get('severity_counts', {}),
                summary=f"Completed analysis of {repo_name}",
                detailed_results=results,
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S')
            )
            
            st.session_state.history_manager.save_scan_result(
                st.session_state.current_session_id, 
                scan_result
            )
            
            st.success("✅ Phân tích hoàn thành!")
            
        except Exception as e:
            st.session_state.history_manager.update_session_status(
                st.session_state.current_session_id,
                SessionStatus.ERROR
            )
            st.error(f"❌ Lỗi khi phân tích: {str(e)}")
        
        finally:
            st.session_state.analysis_in_progress = False


def process_qna_question(question: str, context_repo: Optional[str], options: Dict[str, Any]):
    """Process Q&A question with chat history."""
    # Add user message to chat
    st.session_state.chat_messages.append({
        'role': 'user',
        'content': question,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    })
    
    # Save to history manager if we have an active session
    if st.session_state.current_session_id:
        st.session_state.history_manager.add_chat_message(
            st.session_state.current_session_id,
            "user",
            question
        )
    
    # Mock AI response
    with st.spinner("🤖 AI đang suy nghĩ..."):
        time.sleep(2)  # Simulate processing
        
        # Generate mock response
        mock_response = f"""
        Câu hỏi của bạn về "{question[:50]}..." rất thú vị!
        
        Dựa trên context repository {context_repo if context_repo else "general knowledge"}, 
        tôi có thể giải thích như sau:
        
        1. **Phân tích**: Đây là một câu hỏi về code analysis
        2. **Gợi ý**: Hãy xem xét các best practices trong ngôn ngữ bạn đang sử dụng
        3. **Kết luận**: Để có câu trả lời chính xác hơn, tôi cần thêm context về codebase cụ thể
        
        Bạn có muốn hỏi thêm gì không?
        """
        
        # Add AI response to chat
        st.session_state.chat_messages.append({
            'role': 'assistant',
            'content': mock_response,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Save to history manager
        if st.session_state.current_session_id:
            st.session_state.history_manager.add_chat_message(
                st.session_state.current_session_id,
                "assistant",
                mock_response
            )
    
    st.rerun()


def render_analysis_results():
    """Render analysis results with modern UI."""
    if not st.session_state.analysis_results:
        return
    
    results = st.session_state.analysis_results
    
    st.markdown("## 📊 Kết quả Phân tích")
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Tổng Issues",
            results.get('total_issues', 0),
            delta=None
        )
    
    with col2:
        st.metric(
            "Files được scan",
            results.get('files_analyzed', 0),
            delta=None
        )
    
    with col3:
        st.metric(
            "Dòng code",
            results.get('lines_of_code', 0),
            delta=None
        )
    
    with col4:
        st.metric(
            "Điểm chất lượng",
            f"{results.get('quality_score', 85)}/100",
            delta=results.get('quality_delta', 0)
        )
    
    # Severity breakdown chart
    st.markdown("### ⚠️ Phân bố mức độ nghiêm trọng")
    severity_data = results.get('severity_counts', {})
    
    if severity_data:
        import plotly.express as px
        import pandas as pd
        
        df = pd.DataFrame(list(severity_data.items()), columns=['Severity', 'Count'])
        fig = px.pie(df, values='Count', names='Severity', 
                     title="Distribution of Issues by Severity")
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed results in tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Tóm tắt", "🐛 Linting", "🏗️ Kiến trúc", "📊 Biểu đồ", "🔍 Raw Data"])
    
    with tab1:
        st.markdown("#### 📋 Tóm tắt chung")
        st.write(results.get('summary', 'Phân tích repository hoàn tất.'))
        
        if results.get('recommendations'):
            st.markdown("#### 💡 Khuyến nghị")
            for rec in results['recommendations']:
                st.write(f"• {rec}")
    
    with tab2:
        st.markdown("#### 🔍 Chi tiết Linting Issues")
        linting_issues = results.get('linting_issues', [])
        
        if linting_issues:
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                severity_filter = st.multiselect(
                    "Lọc theo mức độ:",
                    options=list(severity_data.keys()),
                    default=list(severity_data.keys())
                )
            with col2:
                file_filter = st.text_input("Lọc theo file:", placeholder="*.py")
            
            # Display filtered issues
            filtered_issues = [
                issue for issue in linting_issues
                if issue['severity'] in severity_filter
                and (not file_filter or file_filter in issue['file'])
            ]
            
            for issue in filtered_issues[:50]:  # Limit display
                severity_color = {
                    'error': '🔴',
                    'warning': '🟡', 
                    'info': '🔵'
                }.get(issue['severity'], '⚪')
                
                st.markdown(f"""
                **{severity_color} {issue['severity'].title()}** - `{issue['file']}:{issue['line']}`
                
                {issue['message']}
                
                ---
                """)
        else:
            st.info("Không tìm thấy linting issues!")
    
    with tab3:
        st.markdown("#### 🏗️ Phân tích Kiến trúc")
        
        arch_issues = results.get('architectural_issues', [])
        if arch_issues:
            for issue in arch_issues:
                st.warning(f"**{issue['type']}**: {issue['description']}")
        else:
            st.success("Không phát hiện vấn đề kiến trúc!")
        
        # Code complexity
        complexity = results.get('complexity', {})
        if complexity:
            st.markdown("##### 📈 Độ phức tạp Code")
            for metric, value in complexity.items():
                st.write(f"**{metric}**: {value}")
    
    with tab4:
        st.markdown("#### 📊 Biểu đồ và Thống kê")
        
        # Language distribution
        lang_data = results.get('language_distribution', {})
        if lang_data:
            st.markdown("##### 💻 Phân bố Ngôn ngữ")
            df_lang = pd.DataFrame(list(lang_data.items()), columns=['Language', 'Lines'])
            fig_lang = px.bar(df_lang, x='Language', y='Lines', 
                             title="Lines of Code by Language")
            st.plotly_chart(fig_lang, use_container_width=True)
        
        # File size distribution
        file_sizes = results.get('file_sizes', [])
        if file_sizes:
            st.markdown("##### 📁 Phân bố Kích thước File")
            df_sizes = pd.DataFrame(file_sizes, columns=['File', 'Size'])
            fig_sizes = px.histogram(df_sizes, x='Size', nbins=20,
                                   title="Distribution of File Sizes")
            st.plotly_chart(fig_sizes, use_container_width=True)
    
    with tab5:
        st.markdown("#### 🔍 Raw Data (JSON)")
        st.json(results)
    
    # Export options
    st.markdown("### 💾 Export Results")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export JSON", use_container_width=True):
            st.download_button(
                label="Download JSON",
                data=str(results),
                file_name=f"analysis_results_{time.strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📊 Export CSV", use_container_width=True):
            # Convert issues to CSV format
            csv_data = "File,Line,Severity,Message\n"
            for issue in results.get('linting_issues', []):
                csv_data += f"{issue['file']},{issue['line']},{issue['severity']},{issue['message']}\n"
            
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"linting_issues_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col3:
        if st.button("🔄 Analyze Again", use_container_width=True):
            st.session_state.analysis_results = None
            st.rerun()


def create_mock_analysis_results(repo_url: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """Create mock analysis results for demonstration."""
    import random
    
    repo_name = repo_url.split('/')[-1] if '/' in repo_url else "unknown-repo"
    
    # Generate realistic mock data
    total_issues = random.randint(15, 85)
    severity_counts = {
        'error': random.randint(1, max(1, total_issues // 4)),
        'warning': random.randint(5, max(5, total_issues // 2)),
        'info': max(1, total_issues - (total_issues // 4) - (total_issues // 2))
    }
    
    # Ensure total matches
    actual_total = sum(severity_counts.values())
    severity_counts['info'] = severity_counts['info'] + (total_issues - actual_total)
    
    mock_issues = []
    file_names = ['main.py', 'utils.py', 'models.py', 'views.py', 'config.py']
    
    for severity, count in severity_counts.items():
        for i in range(count):
            mock_issues.append({
                'file': random.choice(file_names),
                'line': random.randint(1, 500),
                'severity': severity,
                'message': f"Mock {severity} issue #{i+1} in {repo_name}",
                'rule': f"{severity.upper()}{random.randint(100, 999)}"
            })
    
    return {
        'repository': repo_name,
        'repository_url': repo_url,
        'analysis_type': options.get('analysis_type', 'Repository Review'),
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_issues': total_issues,
        'files_analyzed': random.randint(10, 50),
        'lines_of_code': random.randint(1000, 10000),
        'quality_score': random.randint(70, 95),
        'quality_delta': random.randint(-5, 10),
        'severity_counts': severity_counts,
        'linting_issues': mock_issues,
        'architectural_issues': [
            {
                'type': 'Circular Dependency',
                'description': 'Detected circular dependency between modules A and B'
            },
            {
                'type': 'Unused Public Method',
                'description': 'Public method "unused_function" appears to be unused'
            }
        ] if random.random() > 0.5 else [],
        'complexity': {
            'Cyclomatic Complexity': f"{random.uniform(2.5, 8.5):.1f}",
            'Maintainability Index': f"{random.uniform(60, 90):.1f}",
            'Technical Debt Ratio': f"{random.uniform(5, 25):.1f}%"
        },
        'language_distribution': {
            'Python': random.randint(2000, 8000),
            'JavaScript': random.randint(500, 2000),
            'CSS': random.randint(100, 800),
            'HTML': random.randint(50, 500)
        },
        'file_sizes': [[f"file{i}.py", random.randint(50, 500)] for i in range(20)],
        'summary': f"""
        Phân tích repository {repo_name} hoàn tất. 
        
        Tổng quan:
        - Tổng số issues: {total_issues}
        - Files được phân tích: {random.randint(10, 50)}
        - Chất lượng code: {"Tốt" if total_issues < 30 else "Trung bình" if total_issues < 60 else "Cần cải thiện"}
        
        Kết quả cho thấy codebase có mức độ chất lượng {"cao" if total_issues < 30 else "trung bình"} 
        với một số vấn đề cần được xem xét.
        """,
        'recommendations': [
            "Xem xét refactor các function có độ phức tạp cao",
            "Thêm type hints cho các function thiếu",
            "Cập nhật docstrings cho các public methods",
            "Tối ưu hóa import statements",
            "Xem xét sử dụng linting tools trong CI/CD pipeline"
        ]
    }


def process_pr_analysis(repo_url: str, pr_id: str, platform: str, pat: Optional[str], options: Dict[str, Any]):
    """Process PR analysis (mock implementation)."""
    with st.spinner(f"🔄 Đang phân tích PR #{pr_id}..."):
        time.sleep(2)  # Simulate processing
        
        # Mock PR analysis results
        mock_results = {
            'pr_id': pr_id,
            'platform': platform,
            'summary': f"PR #{pr_id} adds new features with {random.randint(3, 15)} changed files",
            'changes_summary': {
                'files_changed': random.randint(3, 15),
                'lines_added': random.randint(50, 500),
                'lines_deleted': random.randint(10, 100),
                'commits': random.randint(1, 8)
            },
            'impact_analysis': [
                "Thêm feature mới không ảnh hưởng đến existing functionality",
                "Cần kiểm tra backward compatibility",
                "Performance impact minimal"
            ]
        }
        
        st.session_state.analysis_results = mock_results
        st.success(f"✅ Phân tích PR #{pr_id} hoàn thành!")


def process_context_loading(repo_url: str, options: Dict[str, Any]):
    """Load repository context for Q&A (mock implementation)."""
    with st.spinner("📥 Đang load repository context..."):
        time.sleep(1)  # Simulate loading
        st.success(f"✅ Đã load context từ {repo_url}")


def main():
    """Main Streamlit application."""
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Main content area
    render_main_interface({})


if __name__ == "__main__":
    main() 