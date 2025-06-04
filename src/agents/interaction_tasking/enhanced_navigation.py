#!/usr/bin/env python3
"""
AI CodeScan - Enhanced Navigation Component

Enhanced Streamlit navigation using streamlit-option-menu for improved UX.
Provides professional sidebar navigation với icons và enhanced functionality.
"""

import streamlit as st
try:
    from streamlit_option_menu import option_menu
    OPTION_MENU_AVAILABLE = True
except ImportError:
    OPTION_MENU_AVAILABLE = False
    print("⚠️ streamlit_option_menu not available, using basic navigation")
from typing import Optional, Dict, Any, Tuple
from loguru import logger


class EnhancedNavigationAgent:
    """
    Agent responsible for providing enhanced navigation capabilities.
    
    Uses streamlit-option-menu để create professional navigation menus
    với icons, styling, và enhanced user experience.
    """
    
    def __init__(self):
        """Initialize Enhanced Navigation Agent."""
        self.menu_config = {
            "main_menu": {
                "options": [
                    "🏠 Dashboard",
                    "🔍 Repository Analysis", 
                    "🔄 Pull Request Review",
                    "💬 Q&A Assistant",
                    "📊 Code Diagrams",
                    "📝 User Feedback",
                    "📈 Session History"
                ],
                "icons": [
                    "house", 
                    "search", 
                    "arrow-repeat", 
                    "chat-text", 
                    "diagram-3", 
                    "pencil-square", 
                    "clock-history"
                ],
                "menu_icon": "list",
                "default_index": 0
            }
        }
        
        logger.info("Enhanced Navigation Agent initialized")
    
    def render_sidebar_navigation(self) -> str:
        """
        Render enhanced sidebar navigation menu.
        
        Returns:
            str: Selected menu option
        """
        with st.sidebar:
            # Add branding header
            st.markdown("""
                <div style="text-align: center; padding: 1rem 0;">
                    <h1 style="color: #1f77b4; margin: 0;">🤖 AI CodeScan</h1>
                    <p style="color: #666; margin: 0; font-size: 0.9rem;">Intelligent Code Analysis Platform</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Enhanced navigation menu or fallback
            if OPTION_MENU_AVAILABLE:
                selected = option_menu(
                    menu_title="Navigation",
                    options=self.menu_config["main_menu"]["options"],
                    icons=self.menu_config["main_menu"]["icons"],
                    menu_icon=self.menu_config["main_menu"]["menu_icon"],
                    default_index=self.menu_config["main_menu"]["default_index"],
                    orientation="vertical",
                    styles={
                        "container": {"padding": "0!important", "background-color": "#fafafa"},
                        "icon": {"color": "#1f77b4", "font-size": "18px"}, 
                        "nav-link": {
                            "font-size": "16px", 
                            "text-align": "left", 
                            "margin":"0px", 
                            "--hover-color": "#eee"
                        },
                        "nav-link-selected": {"background-color": "#1f77b4"},
                    }
                )
            else:
                # Fallback to basic Streamlit radio buttons
                st.write("**Navigation**")
                selected = st.radio(
                    "Chọn tính năng:",
                    self.menu_config["main_menu"]["options"],
                    index=self.menu_config["main_menu"]["default_index"],
                    key="navigation_menu"
                )
            
            return selected
    
    def render_top_navigation(self, user_name: Optional[str] = None) -> str:
        """
        Render enhanced top navigation bar.
        
        Args:
            user_name: Current user name for display
            
        Returns:
            str: Selected menu option
        """
        # Top navigation with user info
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            selected = option_menu(
                menu_title=None,
                options=["Home", "Analysis", "Reports", "Settings"],
                icons=["house", "graph-up", "file-earmark-text", "gear"],
                menu_icon="cast",
                default_index=0,
                orientation="horizontal",
                styles={
                    "container": {"padding": "0!important", "background-color": "transparent"},
                    "icon": {"color": "#1f77b4", "font-size": "16px"}, 
                    "nav-link": {
                        "font-size": "14px", 
                        "text-align": "center", 
                        "margin":"0px",
                        "padding": "8px 12px",
                        "--hover-color": "#eee"
                    },
                    "nav-link-selected": {"background-color": "#1f77b4", "color": "white"},
                }
            )
        
        with col3:
            if user_name:
                st.markdown(f"**👤 {user_name}**")
        
        return selected
    
    def render_breadcrumbs(self, path: list) -> None:
        """
        Render breadcrumb navigation.
        
        Args:
            path: List of breadcrumb items
        """
        if not path:
            return
        
        breadcrumb_html = " > ".join([f"<span style='color: #1f77b4;'>{item}</span>" for item in path])
        st.markdown(f"📍 {breadcrumb_html}", unsafe_allow_html=True)
    
    def render_settings_menu(self) -> str:
        """
        Render settings navigation menu.
        
        Returns:
            str: Selected settings option
        """
        settings_options = [
            "🔧 General Settings",
            "🔑 API Configuration", 
            "🎨 UI Preferences",
            "🔒 Security Settings",
            "📊 Analytics Preferences"
        ]
        
        settings_icons = [
            "gear",
            "key",
            "palette",
            "shield-lock",
            "graph-up"
        ]
        
        selected = option_menu(
            menu_title="Settings",
            options=settings_options,
            icons=settings_icons,
            menu_icon="gear",
            default_index=0,
            orientation="vertical",
            styles={
                "container": {"padding": "5px", "background-color": "#f8f9fa"},
                "icon": {"color": "#495057", "font-size": "16px"}, 
                "nav-link": {
                    "font-size": "14px", 
                    "text-align": "left", 
                    "margin":"2px", 
                    "padding": "8px 12px",
                    "--hover-color": "#e9ecef"
                },
                "nav-link-selected": {"background-color": "#495057", "color": "white"},
            }
        )
        
        return selected
    
    def get_view_mode_from_selection(self, selected_menu: str) -> str:
        """
        Convert menu selection to view mode.
        
        Args:
            selected_menu: Selected menu option
            
        Returns:
            str: Corresponding view mode
        """
        mapping = {
            "🏠 Dashboard": "dashboard",
            "🔍 Repository Analysis": "new_session", 
            "🔄 Pull Request Review": "pr_review",
            "💬 Q&A Assistant": "qna_assistant",
            "📊 Code Diagrams": "code_diagrams",
            "📝 User Feedback": "user_feedback",
            "📈 Session History": "history_view"
        }
        
        return mapping.get(selected_menu, "dashboard")
    
    def render_analysis_options_menu(self) -> Dict[str, Any]:
        """
        Render analysis options menu cho repository analysis.
        
        Returns:
            Dict[str, Any]: Selected analysis options
        """
        st.subheader("🔧 Analysis Options")
        
        # Analysis type selection
        analysis_type = option_menu(
            menu_title="Analysis Type",
            options=["🔍 Standard Analysis", "🚀 Deep Analysis", "⚡ Quick Scan"],
            icons=["search", "cpu", "lightning"],
            default_index=0,
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important"},
                "nav-link": {"font-size": "14px", "text-align": "center"},
                "nav-link-selected": {"background-color": "#28a745"},
            }
        )
        
        # Language selection
        languages = st.multiselect(
            "🌐 Programming Languages",
            ["Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "PHP"],
            default=["Python", "Java", "JavaScript"]
        )
        
        # Advanced options
        with st.expander("🔧 Advanced Options"):
            include_tests = st.checkbox("Include test files", value=True)
            include_docs = st.checkbox("Include documentation", value=False)
            performance_analysis = st.checkbox("Performance analysis", value=False)
            security_scan = st.checkbox("Security vulnerability scan", value=True)
        
        return {
            "analysis_type": analysis_type,
            "languages": languages,
            "include_tests": include_tests,
            "include_docs": include_docs,
            "performance_analysis": performance_analysis,
            "security_scan": security_scan
        }
    
    def render_quick_actions(self) -> Optional[str]:
        """
        Render quick action buttons.
        
        Returns:
            Optional[str]: Selected quick action
        """
        st.subheader("⚡ Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔍 Quick Scan", key="quick_scan"):
                return "quick_scan"
        
        with col2:
            if st.button("📊 Generate Report", key="generate_report"):
                return "generate_report"
        
        with col3:
            if st.button("💾 Export Data", key="export_data"):
                return "export_data"
        
        return None


def create_enhanced_navigation() -> EnhancedNavigationAgent:
    """
    Factory function to create Enhanced Navigation Agent.
    
    Returns:
        EnhancedNavigationAgent: Configured navigation agent
    """
    return EnhancedNavigationAgent()


# Usage example và testing
if __name__ == "__main__":
    st.set_page_config(
        page_title="Enhanced Navigation Test",
        page_icon="🧭",
        layout="wide"
    )
    
    nav_agent = create_enhanced_navigation()
    
    # Test sidebar navigation
    selected = nav_agent.render_sidebar_navigation()
    st.write(f"Selected: {selected}")
    
    # Test breadcrumbs
    nav_agent.render_breadcrumbs(["Home", "Analysis", "Repository"])
    
    # Test analysis options
    options = nav_agent.render_analysis_options_menu()
    st.write("Options:", options) 