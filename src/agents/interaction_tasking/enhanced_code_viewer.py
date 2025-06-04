#!/usr/bin/env python3

"""
AI CodeScan - Enhanced Code Viewer Component

Enhanced code viewing and editing using streamlit-ace for syntax highlighting,
code search, and interactive code exploration.
"""

import streamlit as st
from streamlit_ace import st_ace
from typing import Optional, Dict, Any, List, Tuple
from loguru import logger
import re
from pathlib import Path


class EnhancedCodeViewerAgent:
    """
    Agent responsible for providing enhanced code viewing capabilities.
    
    Uses streamlit-ace to display code with syntax highlighting,
    search functionality, and interactive editing.
    """
    
    def __init__(self):
        """Initialize Enhanced Code Viewer Agent."""
        self.language_mappings = {
            '.py': 'python',
            '.java': 'java',
            '.kt': 'kotlin',
            '.dart': 'dart',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.sql': 'sql',
            '.sh': 'sh',
            '.dockerfile': 'dockerfile'
        }
        
        self.themes = [
            "monokai", "github", "tomorrow", "kuroir", "twilight",
            "xcode", "textmate", "solarized_dark", "solarized_light",
            "terminal", "chaos", "chrome", "clouds", "crimson_editor"
        ]
        
        self.font_sizes = [8, 10, 12, 14, 16, 18, 20, 22, 24]
    
    def get_language_from_filename(self, filename: str) -> str:
        """
        Determine programming language from filename.
        
        Args:
            filename: Name of the file
            
        Returns:
            Language identifier for ace editor
        """
        try:
            extension = Path(filename).suffix.lower()
            return self.language_mappings.get(extension, 'text')
        except Exception as e:
            logger.warning(f"Error determining language for {filename}: {e}")
            return 'text'
    
    def display_code_viewer(
        self,
        code_content: str,
        filename: str = "code.txt",
        title: str = "📄 Code Viewer",
        editable: bool = False,
        show_line_numbers: bool = True,
        highlight_lines: Optional[List[int]] = None,
        annotations: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[str]:
        """
        Display code with syntax highlighting and interactive features.
        
        Args:
            code_content: The code content to display
            filename: Name of the file (for language detection)
            title: Title for the code viewer
            editable: Whether the code should be editable
            show_line_numbers: Whether to show line numbers
            highlight_lines: List of line numbers to highlight
            annotations: List of annotations (errors, warnings, etc.)
            
        Returns:
            Modified code content if editable, None otherwise
        """
        try:
            st.subheader(title)
            
            # Language detection
            language = self.get_language_from_filename(filename)
            
            # Code viewer settings
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.text(f"📁 {filename} ({language})")
            
            with col2:
                selected_theme = st.selectbox(
                    "Theme:",
                    options=self.themes,
                    index=self.themes.index("monokai"),
                    key=f"theme_{filename}"
                )
            
            with col3:
                font_size = st.selectbox(
                    "Font Size:",
                    options=self.font_sizes,
                    index=self.font_sizes.index(14),
                    key=f"fontsize_{filename}"
                )
            
            with col4:
                wrap_enabled = st.checkbox(
                    "Wrap lines",
                    value=False,
                    key=f"wrap_{filename}"
                )
            
            # Search functionality
            if not editable:
                search_term = st.text_input(
                    "🔍 Search in code:",
                    key=f"search_{filename}",
                    help="Use regex patterns for advanced search"
                )
                
                if search_term:
                    # Highlight search results
                    try:
                        pattern = re.compile(search_term, re.IGNORECASE)
                        matches = list(pattern.finditer(code_content))
                        if matches:
                            st.success(f"Found {len(matches)} matches")
                        else:
                            st.info("No matches found")
                    except re.error:
                        st.warning("Invalid regex pattern")
            
            # Prepare annotations for ace editor
            ace_annotations = []
            if annotations:
                for annotation in annotations:
                    ace_annotations.append({
                        'row': annotation.get('line', 1) - 1,  # ace uses 0-based indexing
                        'column': annotation.get('column', 0),
                        'text': annotation.get('message', ''),
                        'type': annotation.get('type', 'info')  # info, warning, error
                    })
            
            # Prepare markers for highlighting lines
            markers = []
            if highlight_lines:
                for line_num in highlight_lines:
                    markers.append({
                        'startRow': line_num - 1,  # ace uses 0-based indexing
                        'startCol': 0,
                        'endRow': line_num - 1,
                        'endCol': 1000,
                        'className': 'highlight-marker',
                        'type': 'background'
                    })
            
            # Display code editor
            editor_content = st_ace(
                value=code_content,
                language=language,
                theme=selected_theme,
                key=f"ace_{filename}",
                height=600,
                font_size=font_size,
                tab_size=4,
                show_gutter=show_line_numbers,
                show_print_margin=True,
                wrap=wrap_enabled,
                annotations=ace_annotations,
                markers=markers,
                auto_update=False,
                readonly=not editable
            )
            
            # Code statistics
            lines = code_content.split('\n')
            with st.expander("📊 Code Statistics", expanded=False):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Lines", len(lines))
                with col2:
                    st.metric("Characters", len(code_content))
                with col3:
                    non_empty_lines = len([line for line in lines if line.strip()])
                    st.metric("Non-empty lines", non_empty_lines)
                with col4:
                    comment_lines = len([line for line in lines if line.strip().startswith(('#', '//', '/*', '*', '<!--'))])
                    st.metric("Comment lines", comment_lines)
            
            # Return modified content if editable
            if editable and editor_content != code_content:
                return editor_content
            
            return None
            
        except Exception as e:
            logger.error(f"Error displaying code viewer: {e}")
            st.error(f"Error displaying code viewer: {e}")
            return None
    
    def display_code_diff(
        self,
        original_code: str,
        modified_code: str,
        filename: str = "code.txt",
        title: str = "🔄 Code Diff Viewer"
    ) -> None:
        """
        Display side-by-side code diff.
        
        Args:
            original_code: Original code content
            modified_code: Modified code content
            filename: Name of the file
            title: Title for the diff viewer
        """
        try:
            st.subheader(title)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🔴 Original**")
                self.display_code_viewer(
                    original_code,
                    f"original_{filename}",
                    title="",
                    editable=False
                )
            
            with col2:
                st.markdown("**🟢 Modified**")
                self.display_code_viewer(
                    modified_code,
                    f"modified_{filename}",
                    title="",
                    editable=False
                )
            
            # Calculate diff statistics
            original_lines = original_code.split('\n')
            modified_lines = modified_code.split('\n')
            
            with st.expander("📊 Diff Statistics", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Original lines", len(original_lines))
                with col2:
                    st.metric("Modified lines", len(modified_lines))
                with col3:
                    diff = len(modified_lines) - len(original_lines)
                    st.metric("Line difference", diff, delta=diff)
            
        except Exception as e:
            logger.error(f"Error displaying code diff: {e}")
            st.error(f"Error displaying code diff: {e}")
    
    def display_code_with_findings(
        self,
        code_content: str,
        findings: List[Dict[str, Any]],
        filename: str = "code.txt",
        title: str = "🔍 Code with Findings"
    ) -> None:
        """
        Display code with findings annotations.
        
        Args:
            code_content: The code content
            findings: List of findings with line numbers
            filename: Name of the file
            title: Title for the viewer
        """
        try:
            st.subheader(title)
            
            # Convert findings to annotations
            annotations = []
            highlight_lines = []
            
            for finding in findings:
                line_num = finding.get('line', 1)
                severity = finding.get('severity', 'info').lower()
                message = finding.get('message', 'No message')
                
                # Map severity to annotation type
                annotation_type = 'error' if severity == 'high' else 'warning' if severity == 'medium' else 'info'
                
                annotations.append({
                    'line': line_num,
                    'column': 0,
                    'message': f"{severity.upper()}: {message}",
                    'type': annotation_type
                })
                
                highlight_lines.append(line_num)
            
            # Display findings summary
            if findings:
                st.markdown("**📋 Findings Summary:**")
                severity_counts = {}
                for finding in findings:
                    severity = finding.get('severity', 'info').upper()
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                cols = st.columns(len(severity_counts))
                for i, (severity, count) in enumerate(severity_counts.items()):
                    icon = "🔴" if severity == "HIGH" else "🟡" if severity == "MEDIUM" else "🟢"
                    cols[i].metric(f"{icon} {severity}", count)
            
            # Display code with annotations
            self.display_code_viewer(
                code_content=code_content,
                filename=filename,
                title="",
                editable=False,
                highlight_lines=highlight_lines,
                annotations=annotations
            )
            
            # Findings details
            if findings:
                with st.expander("📝 Findings Details", expanded=False):
                    for i, finding in enumerate(findings, 1):
                        line_num = finding.get('line', 'Unknown')
                        severity = finding.get('severity', 'info').upper()
                        category = finding.get('category', 'General')
                        message = finding.get('message', 'No message')
                        rule = finding.get('rule', 'Unknown')
                        
                        severity_color = "#dc3545" if severity == "HIGH" else "#fd7e14" if severity == "MEDIUM" else "#28a745"
                        
                        st.markdown(f"""
                        **Finding #{i}**
                        - **Line:** {line_num}
                        - **Severity:** <span style="color: {severity_color}; font-weight: bold;">{severity}</span>
                        - **Category:** {category}
                        - **Rule:** {rule}
                        - **Message:** {message}
                        """, unsafe_allow_html=True)
                        st.markdown("---")
            
        except Exception as e:
            logger.error(f"Error displaying code with findings: {e}")
            st.error(f"Error displaying code with findings: {e}")
    
    def display_file_tree_browser(
        self,
        file_tree: Dict[str, Any],
        title: str = "📁 File Tree Browser",
        on_file_select: Optional[callable] = None
    ) -> Optional[str]:
        """
        Display an interactive file tree browser.
        
        Args:
            file_tree: Nested dictionary representing file tree
            title: Title for the browser
            on_file_select: Callback function when file is selected
            
        Returns:
            Selected file path or None
        """
        try:
            st.subheader(title)
            
            def render_tree_node(node: Dict[str, Any], path: str = "", level: int = 0):
                """Recursively render tree nodes."""
                indent = "  " * level
                
                if node.get('type') == 'file':
                    file_icon = self._get_file_icon(node.get('name', ''))
                    if st.button(f"{indent}{file_icon} {node.get('name', '')}", 
                               key=f"file_{path}_{node.get('name', '')}"):
                        return f"{path}/{node.get('name', '')}" if path else node.get('name', '')
                else:
                    # Directory
                    folder_icon = "📁" if node.get('expanded', False) else "📂"
                    if st.button(f"{indent}{folder_icon} {node.get('name', '')}/", 
                               key=f"dir_{path}_{node.get('name', '')}"):
                        node['expanded'] = not node.get('expanded', False)
                    
                    if node.get('expanded', False):
                        for child_name, child_node in node.get('children', {}).items():
                            result = render_tree_node(
                                child_node, 
                                f"{path}/{child_name}" if path else child_name,
                                level + 1
                            )
                            if result:
                                return result
                return None
            
            # Render the tree
            selected_file = render_tree_node(file_tree)
            
            if selected_file and on_file_select:
                on_file_select(selected_file)
            
            return selected_file
            
        except Exception as e:
            logger.error(f"Error displaying file tree browser: {e}")
            st.error(f"Error displaying file tree browser: {e}")
            return None
    
    def _get_file_icon(self, filename: str) -> str:
        """Get icon for file based on extension."""
        icons = {
            '.py': '🐍',
            '.java': '☕',
            '.kt': '🟣',
            '.dart': '🎯',
            '.js': '💛',
            '.ts': '🔷',
            '.html': '🌐',
            '.css': '🎨',
            '.json': '📄',
            '.xml': '📋',
            '.yaml': '📝',
            '.yml': '📝',
            '.md': '📖',
            '.txt': '📄',
            '.sql': '🗃️',
            '.dockerfile': '🐳'
        }
        
        ext = Path(filename).suffix.lower()
        return icons.get(ext, '📄')


def create_enhanced_code_viewer() -> EnhancedCodeViewerAgent:
    """Factory function to create EnhancedCodeViewerAgent instance."""
    return EnhancedCodeViewerAgent()


# Sample data for testing
def generate_sample_code() -> str:
    """Generate sample code for testing."""
    return '''#!/usr/bin/env python3

"""
Sample Python code for demonstration.
This code contains various elements for syntax highlighting.
"""

import os
import sys
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class User:
    """Represents a user in the system."""
    id: int
    name: str
    email: str
    active: bool = True
    
    def __post_init__(self):
        """Validate user data after initialization."""
        if not self.email or '@' not in self.email:
            raise ValueError("Invalid email address")
    
    def get_display_name(self) -> str:
        """Get formatted display name."""
        return f"{self.name} ({self.email})"


class UserService:
    """Service for managing users."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.users: Dict[int, User] = {}
        self._next_id = 1
    
    def create_user(self, name: str, email: str) -> User:
        """Create a new user."""
        try:
            user = User(
                id=self._next_id,
                name=name,
                email=email
            )
            self.users[user.id] = user
            self._next_id += 1
            return user
        except ValueError as e:
            print(f"Error creating user: {e}")
            raise
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.users.get(user_id)
    
    def list_active_users(self) -> List[User]:
        """Get all active users."""
        return [user for user in self.users.values() if user.active]


def main():
    """Main application entry point."""
    service = UserService("sqlite:///users.db")
    
    # Create some sample users
    users = [
        ("Alice Smith", "alice@example.com"),
        ("Bob Jones", "bob@example.com"),
        ("Charlie Brown", "charlie@example.com")
    ]
    
    for name, email in users:
        try:
            user = service.create_user(name, email)
            print(f"Created user: {user.get_display_name()}")
        except ValueError:
            print(f"Failed to create user: {name}")
    
    # List all active users
    active_users = service.list_active_users()
    print(f"\\nActive users ({len(active_users)}):")
    for user in active_users:
        print(f"  - {user.get_display_name()}")


if __name__ == "__main__":
    main()
'''


def generate_sample_findings() -> List[Dict[str, Any]]:
    """Generate sample findings for testing."""
    return [
        {
            "line": 35,
            "severity": "HIGH",
            "category": "Security",
            "message": "Hardcoded database URL detected",
            "rule": "S2068"
        },
        {
            "line": 52,
            "severity": "MEDIUM",
            "category": "Code Smell",
            "message": "Method has too many lines (25 > 20)",
            "rule": "MethodLength"
        },
        {
            "line": 67,
            "severity": "LOW",
            "category": "Style",
            "message": "Line too long (exceeds 120 characters)",
            "rule": "LineLength"
        }
    ] 