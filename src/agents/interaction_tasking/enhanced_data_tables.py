#!/usr/bin/env python3

"""
AI CodeScan - Enhanced Data Tables Component

Enhanced data display using streamlit-aggrid for interactive tables.
Provides advanced filtering, sorting, pagination, and export capabilities.
"""

import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode, JsCode
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
from loguru import logger
import json
from datetime import datetime


class EnhancedDataTablesAgent:
    """
    Agent responsible for providing enhanced data table capabilities.
    
    Uses streamlit-aggrid to create interactive, professional data tables
    for displaying analysis results, findings, and metrics.
    """
    
    def __init__(self):
        """Initialize Enhanced Data Tables Agent."""
        self.table_configs = {
            "findings_table": {
                "height": 400,
                "selection_mode": "multiple",
                "use_checkbox": True,
                "fit_columns_on_grid_load": True,
                "allow_unsafe_jscode": True,
                "enable_enterprise_modules": False,
                "theme": "streamlit"
            },
            "metrics_table": {
                "height": 300,
                "selection_mode": "single",
                "use_checkbox": False,
                "fit_columns_on_grid_load": True,
                "allow_unsafe_jscode": True,
                "enable_enterprise_modules": False,
                "theme": "alpine"
            },
            "files_table": {
                "height": 500,
                "selection_mode": "multiple",
                "use_checkbox": True,
                "fit_columns_on_grid_load": False,
                "allow_unsafe_jscode": True,
                "enable_enterprise_modules": False,
                "theme": "streamlit"
            }
        }
        
        # Custom JS code for formatting
        self.js_formatters = {
            "severity_renderer": JsCode("""
                function(params) {
                    if (params.value === 'HIGH') {
                        return '<span style="color: #dc3545; font-weight: bold;">🔴 HIGH</span>';
                    } else if (params.value === 'MEDIUM') {
                        return '<span style="color: #fd7e14; font-weight: bold;">🟡 MEDIUM</span>';
                    } else if (params.value === 'LOW') {
                        return '<span style="color: #28a745; font-weight: bold;">🟢 LOW</span>';
                    }
                    return params.value;
                }
            """),
            "file_type_renderer": JsCode("""
                function(params) {
                    const icons = {
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
                        '.yml': '📝'
                    };
                    const ext = params.value.toLowerCase();
                    for (const [extension, icon] of Object.entries(icons)) {
                        if (ext.endsWith(extension)) {
                            return icon + ' ' + params.value;
                        }
                    }
                    return '📄 ' + params.value;
                }
            """),
            "progress_renderer": JsCode("""
                function(params) {
                    const value = params.value;
                    const percentage = Math.round(value);
                    let color = '#28a745';
                    if (percentage < 50) color = '#dc3545';
                    else if (percentage < 80) color = '#fd7e14';
                    
                    return `
                        <div style="width: 100%; background-color: #e9ecef; border-radius: 3px;">
                            <div style="width: ${percentage}%; background-color: ${color}; 
                                        height: 20px; border-radius: 3px; text-align: center; 
                                        line-height: 20px; color: white; font-size: 12px;">
                                ${percentage}%
                            </div>
                        </div>
                    `;
                }
            """)
        }
    
    def create_findings_table(
        self, 
        findings_data: List[Dict[str, Any]], 
        title: str = "🔍 Analysis Findings",
        show_export: bool = True
    ) -> Optional[pd.DataFrame]:
        """
        Create an interactive findings table.
        
        Args:
            findings_data: List of finding dictionaries
            title: Table title
            show_export: Whether to show export buttons
            
        Returns:
            Selected rows DataFrame or None
        """
        try:
            if not findings_data:
                st.info("No findings to display.")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(findings_data)
            
            # Ensure required columns exist
            required_columns = ['severity', 'category', 'message', 'file', 'line']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = "N/A"
            
            st.subheader(title)
            
            # Export buttons
            if show_export:
                col1, col2, col3, col4 = st.columns([1, 1, 1, 5])
                with col1:
                    if st.button("📊 Export CSV", key="export_findings_csv"):
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"findings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                
                with col2:
                    if st.button("📋 Export JSON", key="export_findings_json"):
                        json_str = df.to_json(orient='records', indent=2)
                        st.download_button(
                            label="Download JSON",
                            data=json_str,
                            file_name=f"findings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
            
            # Configure grid options
            gb = GridOptionsBuilder.from_dataframe(df)
            
            # Column configurations
            gb.configure_column("severity", 
                              cellRenderer=self.js_formatters["severity_renderer"],
                              filter="agSetColumnFilter",
                              width=120)
            gb.configure_column("category", 
                              filter="agSetColumnFilter",
                              width=150)
            gb.configure_column("message", 
                              wrapText=True,
                              autoHeight=True,
                              width=400)
            gb.configure_column("file", 
                              cellRenderer=self.js_formatters["file_type_renderer"],
                              filter="agTextColumnFilter",
                              width=200)
            gb.configure_column("line", 
                              type=["numericColumn"],
                              width=80)
            
            # Grid options
            config = self.table_configs["findings_table"]
            gb.configure_selection(
                selection_mode=config["selection_mode"],
                use_checkbox=config["use_checkbox"]
            )
            gb.configure_grid_options(
                domLayout='normal',
                suppressRowClickSelection=False,
                rowMultiSelectWithClick=True,
                suppressColumnVirtualisation=True
            )
            
            gridOptions = gb.build()
            
            # Display grid
            grid_response = AgGrid(
                df,
                gridOptions=gridOptions,
                data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                height=config["height"],
                fit_columns_on_grid_load=config["fit_columns_on_grid_load"],
                allow_unsafe_jscode=config["allow_unsafe_jscode"],
                enable_enterprise_modules=config["enable_enterprise_modules"],
                theme=config["theme"]
            )
            
            # Show selected rows info
            selected_rows = grid_response['selected_rows']
            if selected_rows:
                st.success(f"✅ Selected {len(selected_rows)} finding(s)")
                return pd.DataFrame(selected_rows)
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating findings table: {e}")
            st.error(f"Error creating findings table: {e}")
            return None
    
    def create_metrics_table(
        self, 
        metrics_data: List[Dict[str, Any]], 
        title: str = "📊 Code Metrics"
    ) -> Optional[pd.DataFrame]:
        """
        Create an interactive metrics table.
        
        Args:
            metrics_data: List of metrics dictionaries
            title: Table title
            
        Returns:
            Selected row DataFrame or None
        """
        try:
            if not metrics_data:
                st.info("No metrics to display.")
                return None
            
            df = pd.DataFrame(metrics_data)
            
            st.subheader(title)
            
            # Configure grid options
            gb = GridOptionsBuilder.from_dataframe(df)
            
            # Column configurations with conditional formatting
            for col in df.columns:
                if col in ['coverage', 'complexity_score', 'maintainability']:
                    gb.configure_column(col, 
                                      cellRenderer=self.js_formatters["progress_renderer"],
                                      type=["numericColumn"],
                                      width=150)
                elif col == 'file':
                    gb.configure_column(col,
                                      cellRenderer=self.js_formatters["file_type_renderer"],
                                      filter="agTextColumnFilter",
                                      width=200)
                else:
                    gb.configure_column(col, filter="agTextColumnFilter")
            
            # Grid options
            config = self.table_configs["metrics_table"]
            gb.configure_selection(
                selection_mode=config["selection_mode"],
                use_checkbox=config["use_checkbox"]
            )
            
            gridOptions = gb.build()
            
            # Display grid
            grid_response = AgGrid(
                df,
                gridOptions=gridOptions,
                data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                height=config["height"],
                fit_columns_on_grid_load=config["fit_columns_on_grid_load"],
                allow_unsafe_jscode=config["allow_unsafe_jscode"],
                enable_enterprise_modules=config["enable_enterprise_modules"],
                theme=config["theme"]
            )
            
            # Show selected row info
            selected_rows = grid_response['selected_rows']
            if selected_rows:
                return pd.DataFrame(selected_rows)
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating metrics table: {e}")
            st.error(f"Error creating metrics table: {e}")
            return None
    
    def create_files_explorer_table(
        self, 
        files_data: List[Dict[str, Any]], 
        title: str = "📁 Files Explorer"
    ) -> Optional[pd.DataFrame]:
        """
        Create an interactive files explorer table.
        
        Args:
            files_data: List of file dictionaries
            title: Table title
            
        Returns:
            Selected rows DataFrame or None
        """
        try:
            if not files_data:
                st.info("No files to display.")
                return None
            
            df = pd.DataFrame(files_data)
            
            st.subheader(title)
            
            # Filter controls
            col1, col2, col3 = st.columns(3)
            with col1:
                file_types = st.multiselect(
                    "Filter by file type:",
                    options=df['type'].unique() if 'type' in df.columns else [],
                    key="file_type_filter"
                )
            with col2:
                languages = st.multiselect(
                    "Filter by language:",
                    options=df['language'].unique() if 'language' in df.columns else [],
                    key="language_filter"
                )
            with col3:
                size_range = st.slider(
                    "File size range (KB):",
                    min_value=0,
                    max_value=int(df['size_kb'].max()) if 'size_kb' in df.columns else 100,
                    value=(0, int(df['size_kb'].max()) if 'size_kb' in df.columns else 100),
                    key="size_range_filter"
                )
            
            # Apply filters
            filtered_df = df.copy()
            if file_types:
                filtered_df = filtered_df[filtered_df['type'].isin(file_types)]
            if languages:
                filtered_df = filtered_df[filtered_df['language'].isin(languages)]
            if 'size_kb' in filtered_df.columns:
                filtered_df = filtered_df[
                    (filtered_df['size_kb'] >= size_range[0]) & 
                    (filtered_df['size_kb'] <= size_range[1])
                ]
            
            # Configure grid options
            gb = GridOptionsBuilder.from_dataframe(filtered_df)
            
            # Column configurations
            if 'path' in filtered_df.columns:
                gb.configure_column("path", 
                                  cellRenderer=self.js_formatters["file_type_renderer"],
                                  filter="agTextColumnFilter",
                                  width=300)
            
            # Numeric columns
            numeric_columns = ['size_kb', 'lines', 'functions', 'classes']
            for col in numeric_columns:
                if col in filtered_df.columns:
                    gb.configure_column(col, type=["numericColumn"], width=100)
            
            # Grid options
            config = self.table_configs["files_table"]
            gb.configure_selection(
                selection_mode=config["selection_mode"],
                use_checkbox=config["use_checkbox"]
            )
            
            # Enable sorting and filtering
            gb.configure_default_column(
                filterable=True,
                sortable=True,
                resizable=True
            )
            
            gridOptions = gb.build()
            
            # Display grid
            grid_response = AgGrid(
                filtered_df,
                gridOptions=gridOptions,
                data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                height=config["height"],
                fit_columns_on_grid_load=config["fit_columns_on_grid_load"],
                allow_unsafe_jscode=config["allow_unsafe_jscode"],
                enable_enterprise_modules=config["enable_enterprise_modules"],
                theme=config["theme"]
            )
            
            # Show selection info
            selected_rows = grid_response['selected_rows']
            if selected_rows:
                st.success(f"✅ Selected {len(selected_rows)} file(s)")
                return pd.DataFrame(selected_rows)
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating files explorer table: {e}")
            st.error(f"Error creating files explorer table: {e}")
            return None
    
    def create_comparison_table(
        self, 
        before_data: List[Dict[str, Any]], 
        after_data: List[Dict[str, Any]], 
        title: str = "🔄 Before/After Comparison"
    ) -> None:
        """
        Create a side-by-side comparison table.
        
        Args:
            before_data: Data before changes
            after_data: Data after changes
            title: Table title
        """
        try:
            st.subheader(title)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Before:**")
                if before_data:
                    df_before = pd.DataFrame(before_data)
                    gb_before = GridOptionsBuilder.from_dataframe(df_before)
                    gb_before.configure_default_column(filterable=True, sortable=True)
                    
                    AgGrid(
                        df_before,
                        gridOptions=gb_before.build(),
                        height=300,
                        theme="alpine"
                    )
                else:
                    st.info("No before data")
            
            with col2:
                st.markdown("**After:**")
                if after_data:
                    df_after = pd.DataFrame(after_data)
                    gb_after = GridOptionsBuilder.from_dataframe(df_after)
                    gb_after.configure_default_column(filterable=True, sortable=True)
                    
                    AgGrid(
                        df_after,
                        gridOptions=gb_after.build(),
                        height=300,
                        theme="alpine"
                    )
                else:
                    st.info("No after data")
                    
        except Exception as e:
            logger.error(f"Error creating comparison table: {e}")
            st.error(f"Error creating comparison table: {e}")


def create_enhanced_data_tables() -> EnhancedDataTablesAgent:
    """Factory function to create EnhancedDataTablesAgent instance."""
    return EnhancedDataTablesAgent()


# Sample data generators for testing
def generate_sample_findings() -> List[Dict[str, Any]]:
    """Generate sample findings data for testing."""
    return [
        {
            "severity": "HIGH",
            "category": "Security",
            "message": "Potential SQL injection vulnerability detected",
            "file": "database.py",
            "line": 45,
            "rule": "S3649"
        },
        {
            "severity": "MEDIUM", 
            "category": "Code Smell",
            "message": "Function too complex (cyclomatic complexity: 15)",
            "file": "utils.java",
            "line": 123,
            "rule": "ComplexityCheck"
        },
        {
            "severity": "LOW",
            "category": "Style",
            "message": "Line too long (exceeds 120 characters)",
            "file": "main.kt",
            "line": 67,
            "rule": "LineLength"
        },
        {
            "severity": "HIGH",
            "category": "Bug",
            "message": "Null pointer dereference possible",
            "file": "service.dart",
            "line": 234,
            "rule": "NullCheck"
        }
    ]


def generate_sample_metrics() -> List[Dict[str, Any]]:
    """Generate sample metrics data for testing."""
    return [
        {
            "file": "main.py",
            "lines": 450,
            "functions": 23,
            "classes": 5,
            "coverage": 85.5,
            "complexity_score": 72.3,
            "maintainability": 78.9
        },
        {
            "file": "utils.java",
            "lines": 320,
            "functions": 18,
            "classes": 3,
            "coverage": 92.1,
            "complexity_score": 68.7,
            "maintainability": 83.2
        },
        {
            "file": "service.kt",
            "lines": 280,
            "functions": 15,
            "classes": 2,
            "coverage": 76.8,
            "complexity_score": 81.4,
            "maintainability": 71.5
        }
    ]


def generate_sample_files() -> List[Dict[str, Any]]:
    """Generate sample files data for testing."""
    return [
        {
            "path": "src/main.py",
            "type": "Source",
            "language": "Python",
            "size_kb": 12.5,
            "lines": 450,
            "functions": 23,
            "classes": 5
        },
        {
            "path": "src/utils.java",
            "type": "Source", 
            "language": "Java",
            "size_kb": 8.3,
            "lines": 320,
            "functions": 18,
            "classes": 3
        },
        {
            "path": "lib/service.kt",
            "type": "Source",
            "language": "Kotlin", 
            "size_kb": 6.7,
            "lines": 280,
            "functions": 15,
            "classes": 2
        },
        {
            "path": "config/settings.json",
            "type": "Config",
            "language": "JSON",
            "size_kb": 1.2,
            "lines": 35,
            "functions": 0,
            "classes": 0
        }
    ] 