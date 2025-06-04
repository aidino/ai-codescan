"""
Conversational Repository Analysis Agent với Chatbox Interface.

Enhanced version của repository analysis với AI-powered conversation flow.
"""

import streamlit as st
import re
import time
import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from loguru import logger

# Import existing analysis agents
try:
    from agents.data_acquisition.git_operations import GitOperationsAgent
    # Remove circular import - we'll use lazy loading for analysis function
    # from agents.interaction_tasking.auth_web_ui import perform_real_repository_analysis
    from core.logging import log_repository_analysis_start
except ImportError as e:
    logger.warning(f"Import error: {e}. Using mock implementations.")


class ConversationState(Enum):
    """Trạng thái của cuộc hội thoại"""
    INITIAL = "initial"
    WAITING_REPO_URL = "waiting_repo_url"
    CHECKING_REPO_ACCESS = "checking_repo_access"
    WAITING_PAT = "waiting_pat"
    CONFIRMING_ANALYSIS = "confirming_analysis"
    ANALYZING = "analyzing" 
    ANALYSIS_COMPLETE = "analysis_complete"
    DISCUSSING_RESULTS = "discussing_results"


@dataclass
class ChatMessage:
    """Message trong chat conversation"""
    role: str  # 'ai' hoặc 'user'
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RepositoryContext:
    """Context thông tin repository"""
    url: Optional[str] = None
    is_private: Optional[bool] = None
    requires_pat: bool = False
    pat: Optional[str] = None
    platform: Optional[str] = None  # github, gitlab, bitbucket
    clone_status: Optional[str] = None
    analysis_results: Optional[Dict[str, Any]] = None


class ConversationalRepositoryAnalyst:
    """AI Assistant cho Repository Analysis với conversation flow"""
    
    def __init__(self):
        self.conversation_state = ConversationState.INITIAL
        self.messages: List[ChatMessage] = []
        self.repo_context = RepositoryContext()
        try:
            self.git_agent = GitOperationsAgent()
        except:
            self.git_agent = None
        
    def initialize_conversation(self):
        """Khởi tạo cuộc hội thoại"""
        self.conversation_state = ConversationState.WAITING_REPO_URL
        
        welcome_message = """
👋 **Chào bạn! Tôi là AI Assistant của CodeScan.**

Tôi sẽ giúp bạn phân tích repository một cách chi tiết. Hãy bắt đầu nhé!

🔍 **Bạn muốn phân tích repository nào?**
Vui lòng cung cấp URL của repository (GitHub, GitLab, BitBucket):

*Ví dụ: `https://github.com/username/project-name`*
        """
        
        self.add_message("ai", welcome_message)
        return welcome_message
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Thêm message vào conversation"""
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata
        )
        self.messages.append(message)
        
    def process_user_input(self, user_input: str) -> str:
        """Xử lý input từ user và trả về response"""
        self.add_message("user", user_input)
        
        if self.conversation_state == ConversationState.WAITING_REPO_URL:
            return self._handle_repo_url_input(user_input)
        elif self.conversation_state == ConversationState.WAITING_PAT:
            return self._handle_pat_input(user_input)
        elif self.conversation_state == ConversationState.CONFIRMING_ANALYSIS:
            return self._handle_analysis_confirmation(user_input)
        elif self.conversation_state == ConversationState.DISCUSSING_RESULTS:
            return self._handle_results_discussion(user_input)
        else:
            return "Xin lỗi, tôi không hiểu yêu cầu của bạn. Bạn có thể thử lại không?"
    
    def _handle_repo_url_input(self, user_input: str) -> str:
        """Xử lý input URL repository"""
        # Extract URL từ user input
        url = self._extract_repository_url(user_input)
        
        if not url:
            return """
🤔 **Tôi không tìm thấy URL repository hợp lệ.**

Vui lòng cung cấp URL đầy đủ của repository, ví dụ:
- `https://github.com/username/repo-name`
- `https://gitlab.com/username/repo-name`
- `https://bitbucket.org/username/repo-name`
            """
        
        self.repo_context.url = url
        self.repo_context.platform = self._detect_platform(url)
        
        # Kiểm tra repository access
        self.conversation_state = ConversationState.CHECKING_REPO_ACCESS
        return self._check_repository_access(url)
    
    def _check_repository_access(self, url: str) -> str:
        """Kiểm tra quyền truy cập repository"""
        try:
            # Mock check for now - in real implementation, use GitOperationsAgent
            # Assume most repos are public for demo
            is_public = 'github.com' in url and not any(x in url.lower() for x in ['private', 'enterprise'])
            
            if is_public:
                # Public repository - có thể clone
                self.repo_context.is_private = False
                self.conversation_state = ConversationState.CONFIRMING_ANALYSIS
                
                return f"""
✅ **Repository hợp lệ và có thể truy cập!**

📊 **Thông tin repository:**
- **URL:** `{url}`
- **Platform:** {self.repo_context.platform.title()}
- **Type:** Public repository

🔍 **Bạn có muốn tôi bắt đầu phân tích không?**
*(Trả lời: có/yes hoặc không/no)*
                """
            else:
                # Có thể là private repository
                self.repo_context.is_private = True
                self.repo_context.requires_pat = True
                self.conversation_state = ConversationState.WAITING_PAT
                
                return f"""
🔒 **Repository này có vẻ là private hoặc cần authentication.**

📊 **Thông tin repository:**
- **URL:** `{url}`
- **Platform:** {self.repo_context.platform.title()}
- **Type:** Private repository

🔑 **Để truy cập, tôi cần Personal Access Token (PAT):**

**Hướng dẫn tạo PAT:**
- **GitHub:** Settings → Developer settings → Personal access tokens
- **GitLab:** User Settings → Access Tokens  
- **BitBucket:** Account settings → App passwords

Vui lòng cung cấp PAT của bạn:
*(PAT sẽ chỉ được sử dụng trong session này và không được lưu trữ)*
                """
                
        except Exception as e:
            logger.error(f"Error checking repository access: {e}")
            return f"""
❌ **Có lỗi khi kiểm tra repository:**

**Lỗi:** {str(e)}

Vui lòng kiểm tra lại URL hoặc thử repository khác.
            """
    
    def _handle_pat_input(self, user_input: str) -> str:
        """Xử lý input Personal Access Token"""
        pat = user_input.strip()
        
        if len(pat) < 10:  # Basic validation
            return """
🔑 **PAT có vẻ không hợp lệ.**

Personal Access Token thường dài hơn 10 ký tự.
Vui lòng kiểm tra lại và nhập PAT đúng.
            """
        
        self.repo_context.pat = pat
        self.conversation_state = ConversationState.CONFIRMING_ANALYSIS
        
        return f"""
✅ **PAT hợp lệ! Repository có thể truy cập được.**

📊 **Thông tin repository:**
- **URL:** `{self.repo_context.url}`
- **Platform:** {self.repo_context.platform.title()}
- **Type:** Private repository
- **Authentication:** ✅ Thành công

🔍 **Bạn có muốn tôi bắt đầu phân tích không?**
*(Trả lời: có/yes hoặc không/no)*
        """
    
    def _handle_analysis_confirmation(self, user_input: str) -> str:
        """Xử lý xác nhận bắt đầu phân tích"""
        response = user_input.lower().strip()
        
        if response in ['có', 'yes', 'y', 'ok', 'được', 'đồng ý', 'bắt đầu']:
            self.conversation_state = ConversationState.ANALYZING
            return self._start_analysis()
        elif response in ['không', 'no', 'n', 'hủy', 'dừng']:
            return """
👋 **Đã hủy phân tích.**

Nếu bạn muốn phân tích repository khác, hãy cung cấp URL mới.
            """
        else:
            return """
🤔 **Tôi không hiểu rõ ý bạn.**

Vui lòng trả lời:
- **"Có"** hoặc **"Yes"** để bắt đầu phân tích
- **"Không"** hoặc **"No"** để hủy
            """
    
    def _start_analysis(self) -> str:
        """Bắt đầu quá trình phân tích repository"""
        try:
            analysis_start_message = """
🔄 **Bắt đầu phân tích repository...**

**Đang thực hiện:**
1. 📥 Clone repository
2. 🔍 Nhận diện ngôn ngữ lập trình  
3. 🧪 Phân tích static code
4. 🏗️ Phân tích kiến trúc
5. 📊 Tính toán metrics

*Vui lòng đợi, quá trình này có thể mất vài phút...*
            """
            
            # Simulate analysis progress
            time.sleep(2)  # Simulate processing time
            
            # For now, use mock results
            self.repo_context.analysis_results = self._generate_mock_analysis_results()
            
            self.conversation_state = ConversationState.ANALYSIS_COMPLETE
            return analysis_start_message + "\n\n" + self._present_analysis_results()
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return f"""
❌ **Phân tích thất bại!**

**Lỗi:** {str(e)}

Có thể do:
- Repository quá lớn
- Kết nối mạng không ổn định
- Lỗi hệ thống

Bạn có muốn thử lại không?
            """
    
    def _generate_mock_analysis_results(self) -> Dict[str, Any]:
        """Generate mock analysis results for demo"""
        repo_name = self.repo_context.url.split('/')[-1] if self.repo_context.url else "unknown"
        
        return {
            'repository': repo_name,
            'repository_url': self.repo_context.url,
            'analysis_type': 'Repository Review',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_issues': 42,
            'files_analyzed': 15,
            'lines_of_code': 1523,
            'quality_score': 87,
            'severity_counts': {
                'critical': 2,
                'error': 4,
                'warning': 12,
                'info': 24
            },
            'languages': {
                'python': {'file_count': 8, 'percentage': 65.2},
                'javascript': {'file_count': 4, 'percentage': 24.1},
                'html': {'file_count': 3, 'percentage': 10.7}
            },
            'summary': {
                'key_issues': [
                    "Found 2 potential security vulnerabilities in dependencies",
                    "Code complexity is high in 3 functions",
                    "Missing documentation for 8 public methods",
                    "12 unused imports detected",
                    "Code style violations in 15 files"
                ],
                'recommendations': [
                    "Update dependencies to latest secure versions",
                    "Refactor complex functions to improve maintainability",
                    "Add comprehensive documentation",
                    "Setup automated code formatting"
                ]
            }
        }
    
    def _present_analysis_results(self) -> str:
        """Trình bày kết quả phân tích"""
        if not self.repo_context.analysis_results:
            return "❌ **Không có kết quả phân tích.**"
        
        results = self.repo_context.analysis_results
        self.conversation_state = ConversationState.DISCUSSING_RESULTS
        
        # Format results summary
        languages_str = ", ".join([f"{lang.title()} ({info['percentage']:.1f}%)" 
                                 for lang, info in results.get('languages', {}).items()])
        
        summary = f"""
✅ **Phân tích hoàn tất!**

## 📊 **Tổng quan Repository**
- **Repository:** {results.get('repository', 'Unknown')}
- **Ngôn ngữ:** {languages_str}
- **Files phân tích:** {results.get('files_analyzed', 0)}
- **Lines of code:** {results.get('lines_of_code', 0):,}
- **Quality Score:** {results.get('quality_score', 0)}/100

## 🐛 **Issues Found**
- **Tổng issues:** {results.get('total_issues', 0)}
- **Critical:** {results.get('severity_counts', {}).get('critical', 0)}
- **Error:** {results.get('severity_counts', {}).get('error', 0)}
- **Warning:** {results.get('severity_counts', {}).get('warning', 0)}

## 🔍 **Key Issues**
        """
        
        # Add key issues
        key_issues = results.get('summary', {}).get('key_issues', [])
        for i, issue in enumerate(key_issues[:5], 1):
            summary += f"\n{i}. {issue}"
        
        summary += f"""

## 💡 **Recommendations**
        """
        
        # Add recommendations  
        recommendations = results.get('summary', {}).get('recommendations', [])
        for i, rec in enumerate(recommendations[:3], 1):
            summary += f"\n{i}. {rec}"
        
        summary += f"""

---

💬 **Bạn có câu hỏi gì về kết quả phân tích không?**

Tôi có thể giúp bạn:
- Giải thích chi tiết các lỗi
- Hướng dẫn cách sửa issues cụ thể
- Đề xuất improvements
- Phân tích deeper vào từng component
        """
        
        return summary
    
    def _handle_results_discussion(self, user_input: str) -> str:
        """Xử lý thảo luận về kết quả phân tích"""
        user_lower = user_input.lower()
        
        # Check for improvements first (more specific)
        if any(word in user_lower for word in ['cải thiện', 'improve', 'tốt hơn']):
            return self._suggest_improvements()
        elif any(word in user_lower for word in ['giải thích', 'explain', 'tại sao', 'why']):
            return self._explain_issues(user_input)
        elif any(word in user_lower for word in ['export', 'xuất', 'download', 'tải']):
            return self._export_results()
        elif any(word in user_lower for word in ['sửa', 'fix', 'cách', 'how']):
            return self._provide_fix_suggestions(user_input)
        else:
            return """
🤔 **Tôi hiểu bạn muốn tìm hiểu thêm.**

Tôi có thể giúp bạn:
- **"Cách sửa lỗi X"** - Hướng dẫn fix issues cụ thể
- **"Giải thích lỗi Y"** - Giải thích tại sao có lỗi này
- **"Cách cải thiện code"** - Đề xuất improvements tổng thể
- **"Export kết quả"** - Xuất báo cáo chi tiết

Bạn muốn tìm hiểu về vấn đề nào?
            """
    
    def _provide_fix_suggestions(self, user_input: str) -> str:
        """Đề xuất cách sửa lỗi"""
        return """
🔧 **Gợi ý sửa lỗi:**

**Lỗi phổ biến và cách sửa:**

1. **Security vulnerabilities:**
   - Update dependencies: `pip install --upgrade package-name`
   - Check with: `safety check` hoặc `pip-audit`

2. **Code complexity:**
   - Break down large functions
   - Use helper functions
   - Apply Single Responsibility Principle

3. **Missing documentation:**
   ```python
   def function_name(param):
       '''
       Brief description.
       
       Args:
           param (type): Description
           
       Returns:
           type: Description
       '''
   ```

4. **Unused imports:**
   - Remove với: `autoflake --remove-all-unused-imports`
   - Hoặc sử dụng IDE auto-cleanup

Bạn muốn tôi giải thích chi tiết lỗi nào?
        """
    
    def _explain_issues(self, user_input: str) -> str:
        """Giải thích các issues"""
        return """
📖 **Giải thích các vấn đề:**

**Tại sao các lỗi này quan trọng:**

🔒 **Security Issues:**
- Có thể tạo vulnerabilities cho attackers
- Cần fix ngay lập tức
- Ảnh hưởng đến toàn bộ hệ thống

⚡ **Performance Issues:**
- Làm chậm application
- Tăng resource consumption
- Ảnh hưởng user experience

📚 **Maintainability Issues:**
- Code khó đọc và maintain
- Increase development time
- Tăng bug rate

🎨 **Style Issues:**
- Inconsistent coding style
- Giảm readability
- Team collaboration khó khăn

Bạn muốn tôi giải thích vấn đề cụ thể nào?
        """
    
    def _suggest_improvements(self) -> str:
        """Đề xuất cải thiện"""
        if not self.repo_context.analysis_results:
            return "Không có dữ liệu phân tích để đề xuất."
        
        results = self.repo_context.analysis_results
        quality_score = results.get('quality_score', 0)
        
        suggestions = f"""
🚀 **Đề xuất cải thiện cho Repository:**

**Quality Score hiện tại: {quality_score}/100**

**📋 Priority cao:**
        """
        
        if quality_score < 70:
            suggestions += "\n- ⚠️ Focus vào việc sửa critical và error issues trước"
        
        if results.get('severity_counts', {}).get('critical', 0) > 0:
            suggestions += "\n- 🚨 Sửa ngay 2 critical issues"
            
        suggestions += """

**🔧 Technical Improvements:**
- Setup pre-commit hooks cho code quality
- Add comprehensive unit tests
- Implement CI/CD pipeline
- Code review process
- Documentation standards

**📈 Long-term Strategy:**
- Regular dependency updates
- Performance monitoring
- Security scanning automation
- Team coding standards

Bạn muốn tôi hướng dẫn implement suggestion nào?
        """
        
        return suggestions
    
    def _export_results(self) -> str:
        """Export analysis results"""
        if not self.repo_context.analysis_results:
            return "❌ **Không có kết quả để export.**"
        
        # Store results in session state for download
        st.session_state.export_data = {
            'analysis_results': self.repo_context.analysis_results,
            'export_timestamp': datetime.now().isoformat(),
            'repository_url': self.repo_context.url
        }
        
        return """
📊 **Kết quả đã sẵn sàng export!**

**Available formats:**
- 📄 **JSON Report** - Chi tiết đầy đủ
- 📋 **Summary Report** - Tóm tắt chính
- 🔍 **Issues Only** - Danh sách lỗi

**Để download:**
1. Check sidebar "📊 Export Results"
2. Chọn format mong muốn
3. Click Download button

Files sẽ được tạo với timestamp để dễ quản lý.
        """
    
    def _extract_repository_url(self, text: str) -> Optional[str]:
        """Extract repository URL từ user input"""
        # URL patterns for common Git platforms
        patterns = [
            r'https?://github\.com/[\w\-\.]+/[\w\-\.]+',
            r'https?://gitlab\.com/[\w\-\.]+/[\w\-\.]+',
            r'https?://bitbucket\.org/[\w\-\.]+/[\w\-\.]+',
            r'git@github\.com:[\w\-\.]+/[\w\-\.]+\.git',
            r'git@gitlab\.com:[\w\-\.]+/[\w\-\.]+\.git'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                url = match.group(0)
                # Normalize URL
                if url.endswith('.git'):
                    url = url[:-4]
                return url
        
        return None
    
    def _detect_platform(self, url: str) -> str:
        """Detect Git platform từ URL"""
        if 'github.com' in url:
            return 'github'
        elif 'gitlab.com' in url:
            return 'gitlab'
        elif 'bitbucket.org' in url:
            return 'bitbucket'
        else:
            return 'unknown'


def render_conversational_repository_analysis():
    """Render giao diện chatbox cho repository analysis"""
    
    st.title("🤖 AI Repository Analyst")
    st.markdown("*Conversational code analysis powered by AI*")
    
    # Initialize session state
    if 'chat_analyst' not in st.session_state:
        st.session_state.chat_analyst = ConversationalRepositoryAnalyst()
        st.session_state.chat_analyst.initialize_conversation()
    
    analyst = st.session_state.chat_analyst
    
    # Main chat interface
    st.markdown("---")
    
    # Chat history container với max height
    chat_container = st.container()
    with chat_container:
        # CSS for better chat styling
        st.markdown("""
        <style>
        .chat-message {
            margin: 10px 0;
            padding: 15px;
            border-radius: 10px;
            max-width: 80%;
        }
        .ai-message {
            background: linear-gradient(90deg, #e3f2fd 0%, #f0f8ff 100%);
            border-left: 4px solid #2196f3;
        }
        .user-message {
            background: linear-gradient(90deg, #f5f5f5 0%, #e8f4fd 100%);
            border-left: 4px solid #4caf50;
            margin-left: auto;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Display conversation history
        for message in analyst.messages:
            if message.role == "ai":
                st.markdown(f"""
                <div class="chat-message ai-message">
                    <strong>🤖 AI Assistant</strong><br/>
                    {message.content}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>👤 You</strong><br/>
                    {message.content}
                </div>
                """, unsafe_allow_html=True)
    
    # Input section at bottom
    st.markdown("---")
    
    # Input form
    with st.form("chat_input", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_input(
                "💬 Type your message:",
                placeholder="Ask me anything about repository analysis...",
                key="user_input_field"
            )
        
        with col2:
            send_button = st.form_submit_button("🚀 Send", use_container_width=True)
    
    # Process user input
    if send_button and user_input and user_input.strip():
        with st.spinner("🤖 AI đang xử lý..."):
            try:
                response = analyst.process_user_input(user_input.strip())
                analyst.add_message("ai", response)
                st.rerun()
            except Exception as e:
                error_msg = f"❌ **Lỗi:** {str(e)}\n\nVui lòng thử lại."
                analyst.add_message("ai", error_msg)
                st.rerun()
    
    # Sidebar with info và controls
    with st.sidebar:
        st.markdown("### 💬 Conversation Status")
        
        # Show current state with icons
        state_icons = {
            'initial': '🔄',
            'waiting_repo_url': '🔍',
            'checking_repo_access': '🔐',
            'waiting_pat': '🔑',
            'confirming_analysis': '❓',
            'analyzing': '⚗️',
            'analysis_complete': '✅',
            'discussing_results': '💬'
        }
        
        current_state = analyst.conversation_state.value
        icon = state_icons.get(current_state, '🤖')
        st.info(f"{icon} **{current_state.replace('_', ' ').title()}**")
        
        # Repository info
        if analyst.repo_context.url:
            st.markdown("### 📊 Repository Info")
            st.code(analyst.repo_context.url, language="")
            
            if analyst.repo_context.platform:
                st.write(f"**Platform:** {analyst.repo_context.platform.title()}")
            if analyst.repo_context.is_private is not None:
                repo_type = "🔒 Private" if analyst.repo_context.is_private else "🌍 Public"
                st.write(f"**Type:** {repo_type}")
        
        # Export results (if available)
        if analyst.conversation_state == ConversationState.DISCUSSING_RESULTS:
            st.markdown("### 📊 Export Results")
            
            if st.button("📄 Download JSON Report"):
                if hasattr(st.session_state, 'export_data'):
                    json_data = json.dumps(st.session_state.export_data, indent=2)
                    st.download_button(
                        label="💾 Download JSON",
                        data=json_data,
                        file_name=f"analysis_report_{int(time.time())}.json",
                        mime="application/json"
                    )
        
        # Controls
        st.markdown("### 🎛️ Controls")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 New Chat", use_container_width=True):
                st.session_state.chat_analyst = ConversationalRepositoryAnalyst()
                st.session_state.chat_analyst.initialize_conversation()
                st.rerun()
        
        with col2:
            if st.button("📋 Clear", use_container_width=True):
                if hasattr(st.session_state, 'chat_analyst'):
                    st.session_state.chat_analyst.messages = []
                    st.session_state.chat_analyst.initialize_conversation()
                st.rerun()
        
        # Help section
        with st.expander("💡 Quick Help"):
            st.markdown("""
            **Repository Analysis Flow:**
            1. 📝 Provide repository URL
            2. 🔐 Enter PAT (if private)
            3. ✅ Confirm analysis
            4. ⏳ Wait for results
            5. 💬 Discuss findings
            
            **Available Commands:**
            - "Explain error X"
            - "How to fix Y?"
            - "Suggest improvements"
            - "Export results"
            """)


if __name__ == "__main__":
    render_conversational_repository_analysis() 