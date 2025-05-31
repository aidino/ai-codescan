"""
Context Provider Module for AI CodeScan.

This module handles context preparation and optimization for LLM requests,
including code snippets, CKG data, diffs, and other relevant information
with intelligent truncation and prioritization.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import logging
import re
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ContextType(Enum):
    """Types of context that can be prepared for LLM."""
    
    CODE_EXPLANATION = "code_explanation"
    PR_ANALYSIS = "pr_analysis"
    QA_RESPONSE = "qa_response"
    ARCHITECTURE_ANALYSIS = "architecture_analysis"
    GENERAL_ANALYSIS = "general_analysis"


class PriorityLevel(Enum):
    """Priority levels for context components."""
    
    CRITICAL = 1    # Must include
    HIGH = 2        # Include if space allows
    MEDIUM = 3      # Include if plenty of space
    LOW = 4         # Include only if minimal space used


@dataclass
class ContextComponent:
    """Individual component of context with priority and metadata."""
    
    name: str
    content: str
    priority: PriorityLevel
    content_type: str
    size_bytes: int
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Calculate size if not provided."""
        if self.size_bytes == 0:
            self.size_bytes = len(self.content.encode('utf-8'))


@dataclass
class ContextPreparationRequest:
    """Request for context preparation."""
    
    context_type: ContextType
    max_tokens: int
    code_snippets: Optional[List[Dict[str, str]]] = None
    ckg_data: Optional[Dict[str, Any]] = None
    diff_content: Optional[str] = None
    user_question: Optional[str] = None
    findings: Optional[List[Dict[str, Any]]] = None
    architectural_issues: Optional[List[Dict[str, Any]]] = None
    search_results: Optional[List[Dict[str, Any]]] = None
    project_metadata: Optional[Dict[str, Any]] = None
    custom_context: Optional[Dict[str, Any]] = None


@dataclass
class PreparedContext:
    """Prepared and optimized context for LLM."""
    
    formatted_context: str
    total_tokens_estimate: int
    included_components: List[str]
    excluded_components: List[str]
    truncation_applied: bool
    context_summary: str
    metadata: Dict[str, Any]


class ContextProviderModule:
    """
    Module for preparing and optimizing context for LLM requests.
    
    This module intelligently selects, prioritizes, and formats context
    information to maximize relevance while staying within token limits.
    """
    
    def __init__(self, 
                 default_max_tokens: int = 4000,
                 tokens_per_character: float = 0.25):
        """
        Initialize the ContextProviderModule.
        
        Args:
            default_max_tokens: Default maximum tokens if not specified
            tokens_per_character: Estimated tokens per character ratio
        """
        self.default_max_tokens = default_max_tokens
        self.tokens_per_character = tokens_per_character
        self.context_formatters = self._initialize_formatters()
    
    def _initialize_formatters(self) -> Dict[ContextType, callable]:
        """Initialize context formatters for different context types."""
        return {
            ContextType.CODE_EXPLANATION: self._format_code_explanation_context,
            ContextType.PR_ANALYSIS: self._format_pr_analysis_context,
            ContextType.QA_RESPONSE: self._format_qa_response_context,
            ContextType.ARCHITECTURE_ANALYSIS: self._format_architecture_context,
            ContextType.GENERAL_ANALYSIS: self._format_general_context
        }
    
    def prepare_llm_context(self, request: ContextPreparationRequest) -> PreparedContext:
        """
        Prepare optimized context for LLM request.
        
        Args:
            request: Context preparation request
            
        Returns:
            PreparedContext with optimized content
        """
        try:
            # Extract and prioritize context components
            components = self._extract_context_components(request)
            
            # Select components based on priority and size constraints
            selected_components = self._select_components_by_priority(
                components, request.max_tokens or self.default_max_tokens
            )
            
            # Format context using appropriate formatter
            formatter = self.context_formatters.get(
                request.context_type, 
                self._format_general_context
            )
            formatted_context = formatter(selected_components, request)
            
            # Calculate final metrics
            estimated_tokens = self._estimate_tokens(formatted_context)
            included_names = [comp.name for comp in selected_components]
            excluded_names = [comp.name for comp in components if comp.name not in included_names]
            
            truncation_applied = any(
                'truncated' in comp.metadata.get('notes', '') 
                for comp in selected_components
                if comp.metadata
            )
            
            # Generate context summary
            context_summary = self._generate_context_summary(
                selected_components, request.context_type
            )
            
            return PreparedContext(
                formatted_context=formatted_context,
                total_tokens_estimate=estimated_tokens,
                included_components=included_names,
                excluded_components=excluded_names,
                truncation_applied=truncation_applied,
                context_summary=context_summary,
                metadata={
                    'total_components': len(components),
                    'selected_components': len(selected_components),
                    'context_type': request.context_type.value,
                    'max_tokens_requested': request.max_tokens,
                    'optimization_applied': len(excluded_names) > 0 or truncation_applied
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to prepare LLM context: {e}")
            # Return minimal fallback context
            return PreparedContext(
                formatted_context="Context preparation failed. Limited context available.",
                total_tokens_estimate=20,
                included_components=[],
                excluded_components=[],
                truncation_applied=False,
                context_summary="Fallback context due to preparation error",
                metadata={'error': str(e)}
            )
    
    def _extract_context_components(self, request: ContextPreparationRequest) -> List[ContextComponent]:
        """Extract and prioritize individual context components."""
        components = []
        
        # Code snippets - always high priority
        if request.code_snippets:
            for i, snippet in enumerate(request.code_snippets):
                content = self._format_code_snippet(snippet)
                components.append(ContextComponent(
                    name=f"code_snippet_{i}",
                    content=content,
                    priority=PriorityLevel.HIGH,
                    content_type="code",
                    size_bytes=0,  # Will be calculated in __post_init__
                    metadata={'language': snippet.get('language', 'unknown')}
                ))
        
        # User question - critical priority
        if request.user_question:
            components.append(ContextComponent(
                name="user_question",
                content=f"User Question: {request.user_question}",
                priority=PriorityLevel.CRITICAL,
                content_type="question",
                size_bytes=0
            ))
        
        # Diff content - high priority for PR analysis
        if request.diff_content:
            priority = PriorityLevel.HIGH if request.context_type == ContextType.PR_ANALYSIS else PriorityLevel.MEDIUM
            truncated_diff = self._truncate_diff(request.diff_content, max_lines=100)
            components.append(ContextComponent(
                name="diff_content",
                content=f"Changes:\n```diff\n{truncated_diff}\n```",
                priority=priority,
                content_type="diff",
                size_bytes=0,
                metadata={'truncated': len(request.diff_content.split('\n')) > 100}
            ))
        
        # CKG data - medium to high priority depending on context
        if request.ckg_data:
            priority = PriorityLevel.HIGH if request.context_type in [
                ContextType.ARCHITECTURE_ANALYSIS, ContextType.QA_RESPONSE
            ] else PriorityLevel.MEDIUM
            
            formatted_ckg = self._format_ckg_data(request.ckg_data)
            components.append(ContextComponent(
                name="ckg_data",
                content=f"Code Knowledge Graph:\n{formatted_ckg}",
                priority=priority,
                content_type="ckg",
                size_bytes=0,
                metadata={'nodes_count': len(request.ckg_data.get('nodes', []))}
            ))
        
        # Findings - medium priority
        if request.findings:
            formatted_findings = self._format_findings(request.findings)
            components.append(ContextComponent(
                name="analysis_findings",
                content=f"Analysis Findings:\n{formatted_findings}",
                priority=PriorityLevel.MEDIUM,
                content_type="findings",
                size_bytes=0,
                metadata={'findings_count': len(request.findings)}
            ))
        
        # Architectural issues - high priority for architecture analysis
        if request.architectural_issues:
            priority = PriorityLevel.HIGH if request.context_type == ContextType.ARCHITECTURE_ANALYSIS else PriorityLevel.MEDIUM
            formatted_issues = self._format_architectural_issues(request.architectural_issues)
            components.append(ContextComponent(
                name="architectural_issues",
                content=f"Architectural Issues:\n{formatted_issues}",
                priority=priority,
                content_type="architecture",
                size_bytes=0,
                metadata={'issues_count': len(request.architectural_issues)}
            ))
        
        # Search results - low to medium priority
        if request.search_results:
            formatted_results = self._format_search_results(request.search_results)
            components.append(ContextComponent(
                name="search_results",
                content=f"Related Information:\n{formatted_results}",
                priority=PriorityLevel.MEDIUM,
                content_type="search",
                size_bytes=0,
                metadata={'results_count': len(request.search_results)}
            ))
        
        # Project metadata - low priority
        if request.project_metadata:
            formatted_metadata = self._format_project_metadata(request.project_metadata)
            components.append(ContextComponent(
                name="project_metadata",
                content=f"Project Information:\n{formatted_metadata}",
                priority=PriorityLevel.LOW,
                content_type="metadata",
                size_bytes=0
            ))
        
        return components
    
    def _select_components_by_priority(self, 
                                     components: List[ContextComponent], 
                                     max_tokens: int) -> List[ContextComponent]:
        """Select components based on priority and token constraints."""
        # Sort by priority (critical first)
        sorted_components = sorted(components, key=lambda x: x.priority.value)
        
        selected = []
        current_tokens = 0
        max_chars = int(max_tokens / self.tokens_per_character)
        
        for component in sorted_components:
            estimated_tokens = self._estimate_tokens(component.content)
            
            if current_tokens + estimated_tokens <= max_tokens:
                # Component fits completely
                selected.append(component)
                current_tokens += estimated_tokens
            elif component.priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH]:
                # Try to truncate high-priority components
                remaining_chars = max_chars - int(current_tokens / self.tokens_per_character)
                if remaining_chars > 100:  # Minimum useful size
                    truncated_content = self._intelligent_truncate(
                        component.content, remaining_chars
                    )
                    truncated_component = ContextComponent(
                        name=component.name,
                        content=truncated_content,
                        priority=component.priority,
                        content_type=component.content_type,
                        size_bytes=len(truncated_content.encode('utf-8')),
                        metadata={
                            **(component.metadata or {}),
                            'truncated': True,
                            'original_size': component.size_bytes
                        }
                    )
                    selected.append(truncated_component)
                    current_tokens = max_tokens  # Use all remaining space
                    break
        
        logger.debug(f"Selected {len(selected)}/{len(components)} components, {current_tokens} tokens")
        return selected
    
    def _format_code_explanation_context(self, 
                                       components: List[ContextComponent], 
                                       request: ContextPreparationRequest) -> str:
        """Format context for code explanation."""
        sections = []
        
        # Always start with code if available
        code_components = [c for c in components if c.content_type == "code"]
        for comp in code_components:
            sections.append(comp.content)
        
        # Add CKG context if available
        ckg_components = [c for c in components if c.content_type == "ckg"]
        for comp in ckg_components:
            sections.append(comp.content)
        
        # Add other relevant information
        other_components = [c for c in components 
                          if c.content_type not in ["code", "ckg"]]
        for comp in other_components:
            sections.append(comp.content)
        
        return "\n\n".join(sections)
    
    def _format_pr_analysis_context(self, 
                                  components: List[ContextComponent], 
                                  request: ContextPreparationRequest) -> str:
        """Format context for PR analysis."""
        sections = []
        
        # Start with diff content
        diff_components = [c for c in components if c.content_type == "diff"]
        for comp in diff_components:
            sections.append(comp.content)
        
        # Add CKG analysis of affected components
        ckg_components = [c for c in components if c.content_type == "ckg"]
        for comp in ckg_components:
            sections.append(comp.content)
        
        # Add architectural issues if relevant
        arch_components = [c for c in components if c.content_type == "architecture"]
        for comp in arch_components:
            sections.append(comp.content)
        
        # Add other context
        other_components = [c for c in components 
                          if c.content_type not in ["diff", "ckg", "architecture"]]
        for comp in other_components:
            sections.append(comp.content)
        
        return "\n\n".join(sections)
    
    def _format_qa_response_context(self, 
                                  components: List[ContextComponent], 
                                  request: ContextPreparationRequest) -> str:
        """Format context for Q&A response."""
        sections = []
        
        # Start with user question
        question_components = [c for c in components if c.content_type == "question"]
        for comp in question_components:
            sections.append(comp.content)
        
        # Add relevant code
        code_components = [c for c in components if c.content_type == "code"]
        for comp in code_components:
            sections.append(comp.content)
        
        # Add CKG data for structural understanding
        ckg_components = [c for c in components if c.content_type == "ckg"]
        for comp in ckg_components:
            sections.append(comp.content)
        
        # Add search results
        search_components = [c for c in components if c.content_type == "search"]
        for comp in search_components:
            sections.append(comp.content)
        
        # Add project context
        other_components = [c for c in components 
                          if c.content_type not in ["question", "code", "ckg", "search"]]
        for comp in other_components:
            sections.append(comp.content)
        
        return "\n\n".join(sections)
    
    def _format_architecture_context(self, 
                                   components: List[ContextComponent], 
                                   request: ContextPreparationRequest) -> str:
        """Format context for architecture analysis."""
        sections = []
        
        # Start with architectural issues
        arch_components = [c for c in components if c.content_type == "architecture"]
        for comp in arch_components:
            sections.append(comp.content)
        
        # Add CKG structural data
        ckg_components = [c for c in components if c.content_type == "ckg"]
        for comp in ckg_components:
            sections.append(comp.content)
        
        # Add findings
        findings_components = [c for c in components if c.content_type == "findings"]
        for comp in findings_components:
            sections.append(comp.content)
        
        # Add other context
        other_components = [c for c in components 
                          if c.content_type not in ["architecture", "ckg", "findings"]]
        for comp in other_components:
            sections.append(comp.content)
        
        return "\n\n".join(sections)
    
    def _format_general_context(self, 
                              components: List[ContextComponent], 
                              request: ContextPreparationRequest) -> str:
        """Format context for general analysis."""
        sections = []
        
        # Order by priority and add all components
        for comp in sorted(components, key=lambda x: x.priority.value):
            sections.append(comp.content)
        
        return "\n\n".join(sections)
    
    def _format_code_snippet(self, snippet: Dict[str, str]) -> str:
        """Format code snippet with metadata."""
        language = snippet.get('language', 'text')
        file_path = snippet.get('file_path', 'Unknown file')
        content = snippet.get('content', '')
        
        return f"File: {file_path}\nLanguage: {language}\n\n```{language}\n{content}\n```"
    
    def _format_ckg_data(self, ckg_data: Dict[str, Any]) -> str:
        """Format CKG data for context inclusion."""
        formatted_parts = []
        
        if 'summary' in ckg_data:
            formatted_parts.append(f"Summary: {ckg_data['summary']}")
        
        if 'nodes' in ckg_data:
            node_count = len(ckg_data['nodes'])
            formatted_parts.append(f"Components: {node_count} code elements")
            
            # Include sample of important nodes
            important_nodes = [n for n in ckg_data['nodes'][:5]]
            if important_nodes:
                node_list = "\n".join([f"- {n.get('name', 'Unknown')}: {n.get('type', 'Unknown')}" 
                                     for n in important_nodes])
                formatted_parts.append(f"Key Components:\n{node_list}")
        
        if 'relationships' in ckg_data:
            rel_count = len(ckg_data['relationships'])
            formatted_parts.append(f"Relationships: {rel_count} connections")
        
        return "\n".join(formatted_parts)
    
    def _format_findings(self, findings: List[Dict[str, Any]]) -> str:
        """Format analysis findings."""
        if not findings:
            return "No findings available."
        
        # Group by severity
        severity_groups = {}
        for finding in findings:
            severity = finding.get('severity', 'Unknown')
            if severity not in severity_groups:
                severity_groups[severity] = []
            severity_groups[severity].append(finding)
        
        formatted_parts = []
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            if severity in severity_groups:
                count = len(severity_groups[severity])
                formatted_parts.append(f"{severity}: {count} issues")
                
                # Include sample of issues
                for finding in severity_groups[severity][:3]:
                    file_path = finding.get('file', 'Unknown')
                    message = finding.get('message', 'No message')
                    formatted_parts.append(f"  - {file_path}: {message}")
        
        return "\n".join(formatted_parts)
    
    def _format_architectural_issues(self, issues: List[Dict[str, Any]]) -> str:
        """Format architectural issues."""
        if not issues:
            return "No architectural issues detected."
        
        formatted = []
        for issue in issues[:5]:  # Limit to top 5 issues
            issue_type = issue.get('type', 'Unknown')
            description = issue.get('description', 'No description')
            severity = issue.get('severity', 'Unknown')
            formatted.append(f"[{severity}] {issue_type}: {description}")
        
        return "\n".join(formatted)
    
    def _format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """Format search results."""
        if not results:
            return "No search results available."
        
        formatted = []
        for i, result in enumerate(results[:3], 1):  # Top 3 results
            title = result.get('title', 'Unknown')
            snippet = result.get('snippet', 'No snippet')[:200]  # Truncate snippets
            formatted.append(f"{i}. {title}\n   {snippet}...")
        
        return "\n".join(formatted)
    
    def _format_project_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format project metadata."""
        formatted = []
        important_fields = ['name', 'language', 'framework', 'type', 'size']
        
        for field in important_fields:
            if field in metadata:
                formatted.append(f"{field.title()}: {metadata[field]}")
        
        return "\n".join(formatted)
    
    def _truncate_diff(self, diff_content: str, max_lines: int = 100) -> str:
        """Intelligently truncate diff content."""
        lines = diff_content.split('\n')
        if len(lines) <= max_lines:
            return diff_content
        
        # Keep file headers and first chunk of changes
        truncated_lines = []
        in_file_header = False
        change_lines_count = 0
        
        for line in lines:
            if line.startswith('diff --git') or line.startswith('+++') or line.startswith('---'):
                truncated_lines.append(line)
                in_file_header = True
            elif line.startswith('@@'):
                truncated_lines.append(line)
                in_file_header = False
            elif not in_file_header and (line.startswith('+') or line.startswith('-') or line.startswith(' ')):
                if change_lines_count < max_lines - 20:  # Reserve space for headers
                    truncated_lines.append(line)
                    change_lines_count += 1
                else:
                    truncated_lines.append('... [Additional changes truncated] ...')
                    break
            else:
                truncated_lines.append(line)
        
        return '\n'.join(truncated_lines)
    
    def _intelligent_truncate(self, content: str, max_chars: int) -> str:
        """Intelligently truncate content preserving structure."""
        if len(content) <= max_chars:
            return content
        
        # Try to truncate at meaningful boundaries
        truncation_points = [
            '\n\n',  # Paragraph boundaries
            '\n',    # Line boundaries
            '. ',    # Sentence boundaries
            ', ',    # Clause boundaries
        ]
        
        for delimiter in truncation_points:
            if delimiter in content[:max_chars]:
                # Find last occurrence of delimiter within limit
                last_pos = content[:max_chars].rfind(delimiter)
                if last_pos > max_chars * 0.7:  # Don't truncate too aggressively
                    return content[:last_pos + len(delimiter)] + "[... truncated ...]"
        
        # Fallback to simple truncation
        return content[:max_chars-20] + "[... truncated ...]"
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        # Simple estimation based on character count
        # More sophisticated tokenizers could be used here
        return int(len(text) * self.tokens_per_character)
    
    def _generate_context_summary(self, 
                                components: List[ContextComponent], 
                                context_type: ContextType) -> str:
        """Generate summary of included context."""
        component_types = {}
        total_size = 0
        
        for comp in components:
            if comp.content_type not in component_types:
                component_types[comp.content_type] = 0
            component_types[comp.content_type] += 1
            total_size += comp.size_bytes
        
        summary_parts = [f"Context for {context_type.value}:"]
        for content_type, count in component_types.items():
            summary_parts.append(f"- {content_type}: {count} components")
        
        summary_parts.append(f"Total size: {total_size} bytes")
        
        return "\n".join(summary_parts)
    
    def optimize_context_for_model(self, 
                                 context: str, 
                                 model_name: str,
                                 max_tokens: Optional[int] = None) -> str:
        """
        Optimize context for specific LLM model.
        
        Args:
            context: Prepared context
            model_name: Target LLM model name
            max_tokens: Model-specific token limit
            
        Returns:
            Optimized context string
        """
        # Model-specific optimizations could be added here
        # For now, apply general optimizations
        
        if max_tokens:
            estimated_tokens = self._estimate_tokens(context)
            if estimated_tokens > max_tokens:
                max_chars = int(max_tokens / self.tokens_per_character)
                context = self._intelligent_truncate(context, max_chars)
        
        # Clean up formatting
        context = re.sub(r'\n{3,}', '\n\n', context)  # Remove excessive newlines
        context = context.strip()
        
        return context 