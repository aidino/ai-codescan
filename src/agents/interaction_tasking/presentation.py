"""
Presentation Agent

Handles formatting and displaying analysis results in the Streamlit web UI.
"""

from typing import Dict, Any, List, Optional
import streamlit as st
import pandas as pd
from loguru import logger

# Optional imports với fallback
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    logger.warning("Plotly not available. Charts will be disabled.")
    PLOTLY_AVAILABLE = False
    px = None
    go = None


class PresentationAgent:
    """
    Agent responsible for presenting analysis results in the web UI.
    
    This agent formats and displays various types of analysis results
    in an organized and visually appealing manner using Streamlit.
    """
    
    def __init__(self):
        """Initialize the PresentationAgent."""
        self.severity_colors = {
            'critical': '#FF4B4B',
            'major': '#FF8C00',
            'minor': '#FFA500',
            'info': '#0066CC',
            'warning': '#FFD700'
        }
        
        self.severity_icons = {
            'critical': '🔴',
            'major': '🟠',
            'minor': '🟡',
            'info': '🔵',
            'warning': '⚠️'
        }
    
    def display_analysis_results(self, results: Dict[str, Any]) -> None:
        """
        Display comprehensive analysis results.
        
        Args:
            results: Analysis results from the system
        """
        logger.info("Displaying analysis results in web UI")
        
        if not results:
            st.warning("⚠️ No analysis results to display")
            return
        
        # Main results header
        st.header("📊 Analysis Results")
        
        # Repository summary
        if 'repository' in results:
            self._display_repository_summary(results['repository'])
        
        # Create tabs for different result sections
        tabs = st.tabs([
            "📋 Summary", 
            "🔍 Linting Results", 
            "🏗️ Architecture Analysis",
            "📈 Metrics & Charts",
            "📄 Raw Data"
        ])
        
        with tabs[0]:
            self._display_summary(results)
        
        with tabs[1]:
            if 'linter_results' in results:
                self._display_linting_results(results['linter_results'])
            else:
                st.info("No linting results available")
        
        with tabs[2]:
            if 'architecture_analysis' in results:
                self._display_architecture_analysis(results['architecture_analysis'])
            else:
                st.info("No architecture analysis available")
        
        with tabs[3]:
            self._display_metrics_and_charts(results)
        
        with tabs[4]:
            self._display_raw_data(results)
        
        # Action buttons
        self._display_action_buttons(results)
    
    def _display_repository_summary(self, repo_info: Dict[str, Any]) -> None:
        """Display repository summary information."""
        st.subheader("🗂️ Repository Information")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Language", repo_info.get('language', 'Unknown'))
        
        with col2:
            st.metric("Files Analyzed", repo_info.get('files_analyzed', 0))
        
        with col3:
            st.metric("Lines of Code", f"{repo_info.get('lines_of_code', 0):,}")
        
        with col4:
            url = repo_info.get('url', '')
            if url:
                st.markdown(f"[🔗 Repository]({url})")
        
        st.markdown("---")
    
    def _display_summary(self, results: Dict[str, Any]) -> None:
        """Display high-level summary of analysis results."""
        st.subheader("📋 Analysis Summary")
        
        # Overall status
        if 'summary' in results:
            st.info(results['summary'])
        
        # Key metrics
        col1, col2, col3 = st.columns(3)
        
        # Linting metrics
        if 'linter_results' in results:
            linter = results['linter_results']
            total_issues = linter.get('total_issues', 0)
            
            with col1:
                st.metric(
                    "Total Issues",
                    total_issues,
                    delta=None,
                    help="Total number of linting issues found"
                )
        
        # Architecture metrics  
        if 'architecture_analysis' in results:
            arch = results['architecture_analysis']
            
            with col2:
                st.metric(
                    "Circular Dependencies",
                    arch.get('circular_dependencies', 0),
                    delta=None,
                    help="Number of circular dependencies detected"
                )
            
            with col3:
                complexity = arch.get('complexity_score', 0)
                st.metric(
                    "Complexity Score",
                    f"{complexity:.1f}/10",
                    delta=None,
                    help="Overall code complexity score"
                )
        
        # Recommendations
        self._display_recommendations(results)
    
    def _display_linting_results(self, linter_results: Dict[str, Any]) -> None:
        """Display detailed linting results."""
        st.subheader("🔍 Linting Results")
        
        issues = linter_results.get('issues', [])
        
        if not issues:
            st.success("✅ No linting issues found!")
            return
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Critical", linter_results.get('critical', 0))
        with col2:
            st.metric("Major", linter_results.get('major', 0))
        with col3:
            st.metric("Minor", linter_results.get('minor', 0))
        with col4:
            st.metric("Total", linter_results.get('total_issues', 0))
        
        # Issues breakdown
        st.subheader("Issues Breakdown")
        
        # Filter controls
        col1, col2 = st.columns(2)
        
        with col1:
            severity_filter = st.multiselect(
                "Filter by Severity",
                ['critical', 'major', 'minor', 'info'],
                default=['critical', 'major', 'minor', 'info']
            )
        
        with col2:
            files = list(set(issue['file'] for issue in issues))
            file_filter = st.selectbox(
                "Filter by File",
                ['All Files'] + files
            )
        
        # Filter issues
        filtered_issues = issues
        if severity_filter:
            filtered_issues = [
                issue for issue in filtered_issues 
                if issue.get('severity') in severity_filter
            ]
        
        if file_filter != 'All Files':
            filtered_issues = [
                issue for issue in filtered_issues
                if issue.get('file') == file_filter
            ]
        
        # Display filtered issues
        for issue in filtered_issues:
            self._display_issue_card(issue)
    
    def _display_issue_card(self, issue: Dict[str, Any]) -> None:
        """Display a single linting issue in a card format."""
        severity = issue.get('severity', 'info')
        icon = self.severity_icons.get(severity, '📝')
        
        with st.container():
            col1, col2 = st.columns([1, 20])
            
            with col1:
                st.markdown(f"## {icon}")
            
            with col2:
                st.markdown(f"**{issue.get('file', 'Unknown file')}:{issue.get('line', '?')}**")
                st.markdown(f"`{issue.get('rule', 'Unknown rule')}` - {issue.get('message', 'No message')}")
                
                if severity == 'critical':
                    st.error(f"Critical: {issue.get('message', '')}")
                elif severity == 'major':
                    st.warning(f"Major: {issue.get('message', '')}")
                else:
                    st.info(f"{severity.title()}: {issue.get('message', '')}")
        
        st.markdown("---")
    
    def _display_architecture_analysis(self, arch_results: Dict[str, Any]) -> None:
        """Display architecture analysis results."""
        st.subheader("🏗️ Architecture Analysis")
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            circular_deps = arch_results.get('circular_dependencies', 0)
            if circular_deps == 0:
                st.success(f"✅ Circular Dependencies: {circular_deps}")
            else:
                st.error(f"❌ Circular Dependencies: {circular_deps}")
        
        with col2:
            unused_elements = arch_results.get('unused_public_elements', 0)
            if unused_elements == 0:
                st.success(f"✅ Unused Public Elements: {unused_elements}")
            else:
                st.warning(f"⚠️ Unused Public Elements: {unused_elements}")
        
        with col3:
            complexity = arch_results.get('complexity_score', 0)
            if complexity <= 5:
                st.success(f"✅ Complexity Score: {complexity:.1f}/10")
            elif complexity <= 7:
                st.warning(f"⚠️ Complexity Score: {complexity:.1f}/10")
            else:
                st.error(f"❌ Complexity Score: {complexity:.1f}/10")
        
        # Detailed findings
        if circular_deps > 0:
            st.subheader("🔄 Circular Dependencies")
            st.warning("Circular dependencies detected. This can lead to maintenance issues and tight coupling.")
            # TODO: Display specific circular dependency chains when available
        
        if unused_elements > 0:
            st.subheader("🗑️ Unused Public Elements")
            st.info("Consider removing or making these elements private if they're not part of the public API.")
            # TODO: Display specific unused elements when available
    
    def _display_metrics_and_charts(self, results: Dict[str, Any]) -> None:
        """Display metrics and visualizations."""
        st.subheader("📈 Metrics & Visualizations")
        
        if not PLOTLY_AVAILABLE:
            st.warning("📊 Charts are not available. Please install plotly: `pip install plotly`")
            return
        
        # Linting results chart
        if 'linter_results' in results:
            self._create_linting_chart(results['linter_results'])
        
        # Architecture metrics
        if 'architecture_analysis' in results:
            self._create_architecture_chart(results['architecture_analysis'])
    
    def _create_linting_chart(self, linter_results: Dict[str, Any]) -> None:
        """Create charts for linting results."""
        if not PLOTLY_AVAILABLE:
            st.info("Charts require plotly. Showing text summary instead.")
            
            # Text-based summary as fallback
            severities = ['critical', 'major', 'minor', 'info']
            counts = [linter_results.get(sev, 0) for sev in severities]
            
            st.write("**Issues by Severity:**")
            for sev, count in zip(severities, counts):
                if count > 0:
                    st.write(f"- {sev.title()}: {count}")
            return
            
        st.subheader("🔍 Linting Issues Distribution")
        
        # Severity distribution pie chart
        severities = ['critical', 'major', 'minor', 'info']
        counts = [linter_results.get(sev, 0) for sev in severities]
        
        if sum(counts) > 0:
            fig = px.pie(
                values=counts,
                names=severities,
                title="Issues by Severity",
                color_discrete_map={
                    'critical': '#FF4B4B',
                    'major': '#FF8C00', 
                    'minor': '#FFA500',
                    'info': '#0066CC'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No linting issues to visualize")
    
    def _create_architecture_chart(self, arch_results: Dict[str, Any]) -> None:
        """Create charts for architecture analysis."""
        if not PLOTLY_AVAILABLE:
            st.info("Charts require plotly. Showing text summary instead.")
            
            # Text-based summary as fallback
            metrics = {
                'Circular Dependencies': arch_results.get('circular_dependencies', 0),
                'Unused Public Elements': arch_results.get('unused_public_elements', 0),
                'Complexity Score': arch_results.get('complexity_score', 0)
            }
            
            st.write("**Architecture Metrics:**")
            for metric, value in metrics.items():
                st.write(f"- {metric}: {value}")
            return
            
        st.subheader("🏗️ Architecture Metrics")
        
        # Simple metrics bar chart
        metrics = {
            'Circular Dependencies': arch_results.get('circular_dependencies', 0),
            'Unused Public Elements': arch_results.get('unused_public_elements', 0),
            'Complexity Score': arch_results.get('complexity_score', 0)
        }
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(metrics.keys()),
                y=list(metrics.values()),
                marker_color=['red' if v > 0 else 'green' for v in metrics.values()]
            )
        ])
        
        fig.update_layout(
            title="Architecture Health Metrics",
            yaxis_title="Count/Score"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _display_recommendations(self, results: Dict[str, Any]) -> None:
        """Display actionable recommendations based on results."""
        st.subheader("💡 Recommendations")
        
        recommendations = []
        
        # Generate recommendations based on results
        if 'linter_results' in results:
            linter = results['linter_results']
            critical = linter.get('critical', 0)
            major = linter.get('major', 0)
            
            if critical > 0:
                recommendations.append(
                    f"🔴 **High Priority**: Fix {critical} critical linting issues immediately"
                )
            
            if major > 0:
                recommendations.append(
                    f"🟠 **Medium Priority**: Address {major} major linting issues"
                )
        
        if 'architecture_analysis' in results:
            arch = results['architecture_analysis']
            circular_deps = arch.get('circular_dependencies', 0)
            complexity = arch.get('complexity_score', 0)
            
            if circular_deps > 0:
                recommendations.append(
                    "🔄 **Architecture**: Refactor circular dependencies to improve maintainability"
                )
            
            if complexity > 7:
                recommendations.append(
                    "🧩 **Complexity**: Consider breaking down complex modules for better readability"
                )
        
        # Display recommendations
        if recommendations:
            for rec in recommendations:
                st.markdown(f"- {rec}")
        else:
            st.success("✅ No immediate recommendations - your code looks good!")
    
    def _display_raw_data(self, results: Dict[str, Any]) -> None:
        """Display raw data in expandable sections."""
        st.subheader("📄 Raw Analysis Data")
        
        with st.expander("🔍 Linting Results"):
            if 'linter_results' in results:
                st.json(results['linter_results'])
            else:
                st.info("No linting data available")
        
        with st.expander("🏗️ Architecture Analysis"):
            if 'architecture_analysis' in results:
                st.json(results['architecture_analysis'])
            else:
                st.info("No architecture data available")
        
        with st.expander("🗂️ Repository Information"):
            if 'repository' in results:
                st.json(results['repository'])
            else:
                st.info("No repository data available")
    
    def _display_action_buttons(self, results: Dict[str, Any]) -> None:
        """Display action buttons for results."""
        st.markdown("---")
        st.subheader("🔧 Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📊 Export Results"):
                self._export_results(results)
        
        with col2:
            if st.button("🔄 Analyze Again"):
                # Clear results to trigger new analysis
                if 'analysis_results' in st.session_state:
                    st.session_state.analysis_results = None
                st.rerun()
        
        with col3:
            if st.button("📋 Copy Summary"):
                summary = results.get('summary', 'No summary available')
                st.code(summary, language='text')
        
        with col4:
            if st.button("🚀 New Analysis"):
                # Reset session for new analysis
                for key in ['analysis_results', 'current_task_id', 'dialog_state']:
                    if key in st.session_state:
                        st.session_state[key] = None
                st.session_state.dialog_state = "waiting_input"
                st.rerun()
    
    def _export_results(self, results: Dict[str, Any]) -> None:
        """Export results in various formats."""
        # Create downloadable content
        import json
        
        # JSON export
        json_data = json.dumps(results, indent=2, default=str)
        st.download_button(
            label="📁 Download JSON",
            data=json_data,
            file_name="ai_codescan_results.json",
            mime="application/json"
        )
        
        # CSV export for issues
        if 'linter_results' in results and 'issues' in results['linter_results']:
            issues = results['linter_results']['issues']
            if issues:
                df = pd.DataFrame(issues)
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="📊 Download Issues CSV",
                    data=csv_data,
                    file_name="ai_codescan_issues.csv",
                    mime="text/csv"
                ) 