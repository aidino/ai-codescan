#!/usr/bin/env python3
"""
Presentation Agent for Interaction & Tasking Team.

Handles formatting and presenting data for the Web UI.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PresentationFormat:
    """Format configuration for presenting data."""
    format_type: str  # 'text', 'json', 'table', 'chart'
    display_options: Dict[str, Any]
    priority: int = 1


class PresentationAgent:
    """Agent responsible for formatting và presenting analysis results."""
    
    def __init__(self):
        """Initialize Presentation Agent."""
        self.supported_formats = {
            'text': self._format_as_text,
            'json': self._format_as_json,
            'table': self._format_as_table,
            'markdown': self._format_as_markdown
        }
        logger.info("PresentationAgent initialized")
    
    def format_analysis_results(self, 
                               results: Dict[str, Any], 
                               format_type: str = 'markdown') -> str:
        """
        Format analysis results for presentation.
        
        Args:
            results: Analysis results to format
            format_type: Format type (text, json, table, markdown)
            
        Returns:
            Formatted string for display
        """
        if format_type not in self.supported_formats:
            format_type = 'text'
            
        formatter = self.supported_formats[format_type]
        return formatter(results)
    
    def format_findings(self, findings: List[Dict[str, Any]]) -> str:
        """Format code analysis findings."""
        if not findings:
            return "✅ No issues found!"
        
        output = "## 📋 Code Analysis Findings\n\n"
        
        for i, finding in enumerate(findings, 1):
            severity = finding.get('severity', 'info').upper()
            icon = {'ERROR': '❌', 'WARNING': '⚠️', 'INFO': 'ℹ️'}.get(severity, 'ℹ️')
            
            output += f"### {icon} Finding {i}: {finding.get('rule', 'Unknown')}\n"
            output += f"**Severity:** {severity}\n"
            output += f"**File:** `{finding.get('file', 'Unknown')}`\n"
            output += f"**Line:** {finding.get('line', '?')}\n"
            output += f"**Message:** {finding.get('message', 'No description')}\n\n"
            
            if finding.get('code_context'):
                output += "**Code:**\n"
                output += f"```python\n{finding['code_context']}\n```\n\n"
        
        return output
    
    def format_project_summary(self, summary: Dict[str, Any]) -> str:
        """Format project summary for display."""
        output = "# 📊 Project Analysis Summary\n\n"
        
        # Basic info
        if 'repository_url' in summary:
            output += f"**Repository:** {summary['repository_url']}\n"
        
        if 'language' in summary:
            output += f"**Primary Language:** {summary['language']}\n"
        
        if 'file_count' in summary:
            output += f"**Total Files:** {summary['file_count']}\n"
        
        # Statistics
        if 'statistics' in summary:
            stats = summary['statistics']
            output += "\n## 📈 Statistics\n\n"
            for key, value in stats.items():
                output += f"- **{key.replace('_', ' ').title()}:** {value}\n"
        
        # Analysis results
        if 'analysis_results' in summary:
            output += "\n" + self.format_findings(summary['analysis_results'])
        
        return output
    
    def _format_as_text(self, data: Dict[str, Any]) -> str:
        """Format data as plain text."""
        def _dict_to_text(d, level=0):
            output = ""
            indent = "  " * level
            for key, value in d.items():
                if isinstance(value, dict):
                    output += f"{indent}{key}:\n"
                    output += _dict_to_text(value, level + 1)
                elif isinstance(value, list):
                    output += f"{indent}{key}: {len(value)} items\n"
                else:
                    output += f"{indent}{key}: {value}\n"
            return output
        
        return _dict_to_text(data)
    
    def _format_as_json(self, data: Dict[str, Any]) -> str:
        """Format data as JSON string."""
        import json
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _format_as_table(self, data: Dict[str, Any]) -> str:
        """Format data as table."""
        if not data:
            return "No data to display"
        
        # Simple table format
        output = "| Key | Value |\n|-----|-------|\n"
        for key, value in data.items():
            value_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
            output += f"| {key} | {value_str} |\n"
        
        return output
    
    def _format_as_markdown(self, data: Dict[str, Any]) -> str:
        """Format data as markdown."""
        output = "## Analysis Results\n\n"
        
        for key, value in data.items():
            output += f"### {key.replace('_', ' ').title()}\n\n"
            
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    output += f"- **{subkey}:** {subvalue}\n"
            elif isinstance(value, list):
                for item in value[:5]:  # Limit to first 5 items
                    output += f"- {item}\n"
                if len(value) > 5:
                    output += f"- ... và {len(value) - 5} items khác\n"
            else:
                output += f"{value}\n"
            
            output += "\n"
        
        return output 