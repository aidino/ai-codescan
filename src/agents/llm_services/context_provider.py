#!/usr/bin/env python3
"""
Context Provider Module for LLM Services.

Handles gathering và formatting context data cho LLM requests.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ContextType(Enum):
    """Types of context for LLM requests."""
    CODE_ANALYSIS = "code_analysis"
    CODE_REVIEW = "code_review"
    QA_INTERACTION = "qa_interaction"
    BUG_ANALYSIS = "bug_analysis"
    ARCHITECTURE_ANALYSIS = "architecture_analysis"
    PR_ANALYSIS = "pr_analysis"


@dataclass
class ContextData:
    """Container for LLM context data."""
    code_snippet: str = ""
    file_path: str = ""
    language: str = ""
    ckg_data: Dict[str, Any] = None
    related_components: List[str] = None
    project_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.ckg_data is None:
            self.ckg_data = {}
        if self.related_components is None:
            self.related_components = []
        if self.project_info is None:
            self.project_info = {}


@dataclass
class ContextPreparationRequest:
    """Request for preparing context data for LLM."""
    context_type: str  # 'code_analysis', 'qa', 'review', etc.
    primary_code: str = ""
    file_path: str = ""
    language: str = ""
    additional_context: Dict[str, Any] = None
    include_ckg_data: bool = True
    include_related_code: bool = False
    max_context_length: int = 2000
    
    def __post_init__(self):
        if self.additional_context is None:
            self.additional_context = {}


@dataclass
class ContextPreparationResult:
    """Result of context preparation."""
    context_data: ContextData
    formatted_context: str
    context_length: int
    truncated: bool = False
    preparation_time: float = 0.0


# Alias for backward compatibility
PreparedContext = ContextPreparationResult


class ContextProviderModule:
    """Module for gathering và formatting context data cho LLM requests."""
    
    def __init__(self):
        """Initialize Context Provider Module."""
        self.max_context_length = 4000  # Max context characters
        logger.info("ContextProviderModule initialized")
    
    def gather_code_context(self, 
                           code_snippet: str,
                           file_path: str = "",
                           language: str = "",
                           include_surrounding: bool = False) -> ContextData:
        """
        Gather context for code analysis.
        
        Args:
            code_snippet: Main code to analyze
            file_path: Path to the file
            language: Programming language
            include_surrounding: Whether to include surrounding code context
            
        Returns:
            ContextData with gathered context
        """
        context = ContextData(
            code_snippet=code_snippet,
            file_path=file_path,
            language=language or self._detect_language(file_path)
        )
        
        # Add additional context if requested
        if include_surrounding:
            context.code_snippet = self._add_surrounding_context(code_snippet, file_path)
        
        return context
    
    def gather_ckg_context(self, 
                          component_name: str,
                          ckg_data: Dict[str, Any]) -> ContextData:
        """
        Gather CKG-related context.
        
        Args:
            component_name: Name of component to focus on
            ckg_data: CKG data from query
            
        Returns:
            ContextData with CKG context
        """
        context = ContextData(ckg_data=ckg_data)
        
        # Extract related components
        context.related_components = self._extract_related_components(
            component_name, ckg_data
        )
        
        return context
    
    def gather_qa_context(self,
                         question: str,
                         code_context: str = "",
                         ckg_results: List[Dict[str, Any]] = None) -> ContextData:
        """
        Gather context data for Q&A scenarios.
        
        Args:
            question: User question
            code_context: Relevant code context
            ckg_results: Results from CKG queries
            
        Returns:
            ContextData with Q&A context
        """
        context = ContextData(
            code_snippet=code_context,
            language=self._detect_language(""),
            ckg_data=self._format_ckg_results(ckg_results or []),
            related_components=self._extract_components_from_results(ckg_results or [])
        )
        
        return context
    
    def prepare_context(self, request: ContextPreparationRequest) -> ContextPreparationResult:
        """
        Prepare context based on ContextPreparationRequest.
        
        Args:
            request: Context preparation request
            
        Returns:
            ContextPreparationResult with prepared context
        """
        import time
        start_time = time.time()
        
        try:
            # Gather basic context
            context = ContextData(
                code_snippet=request.primary_code,
                file_path=request.file_path,
                language=request.language or self._detect_language(request.file_path),
                project_info=request.additional_context.copy()
            )
            
            # Add CKG data if requested
            if request.include_ckg_data and request.additional_context.get('ckg_results'):
                context.ckg_data = self._format_ckg_results(
                    request.additional_context['ckg_results']
                )
                context.related_components = self._extract_components_from_results(
                    request.additional_context['ckg_results']
                )
            
            # Format context for LLM
            formatted_context = self.format_context_for_llm(context)
            
            # Check if truncation needed
            truncated = len(formatted_context) > request.max_context_length
            if truncated:
                formatted_context = formatted_context[:request.max_context_length] + "..."
            
            preparation_time = time.time() - start_time
            
            return ContextPreparationResult(
                context_data=context,
                formatted_context=formatted_context,
                context_length=len(formatted_context),
                truncated=truncated,
                preparation_time=preparation_time
            )
            
        except Exception as e:
            logger.error(f"Error preparing context: {e}")
            # Return empty context on error
            return ContextPreparationResult(
                context_data=ContextData(),
                formatted_context="",
                context_length=0,
                truncated=False,
                preparation_time=time.time() - start_time
            )
    
    def format_context_for_llm(self, context: ContextData) -> str:
        """
        Format context data for LLM consumption.
        
        Args:
            context: ContextData to format
            
        Returns:
            Formatted context string
        """
        formatted_parts = []
        
        # Add code context
        if context.code_snippet:
            if context.language:
                formatted_parts.append(f"**Language:** {context.language}")
            if context.file_path:
                formatted_parts.append(f"**File:** {context.file_path}")
            
            formatted_parts.append("**Code:**")
            formatted_parts.append(f"```{context.language}")
            formatted_parts.append(context.code_snippet)
            formatted_parts.append("```")
        
        # Add CKG context
        if context.ckg_data:
            formatted_parts.append("\n**CKG Information:**")
            ckg_summary = self._format_ckg_summary(context.ckg_data)
            formatted_parts.append(ckg_summary)
        
        # Add related components
        if context.related_components:
            formatted_parts.append("\n**Related Components:**")
            for component in context.related_components[:5]:  # Limit to 5
                formatted_parts.append(f"- {component}")
        
        # Add project info
        if context.project_info:
            formatted_parts.append("\n**Project Info:**")
            for key, value in context.project_info.items():
                formatted_parts.append(f"- {key}: {value}")
        
        formatted_context = "\n".join(formatted_parts)
        
        # Truncate if too long
        if len(formatted_context) > self.max_context_length:
            formatted_context = formatted_context[:self.max_context_length] + "\n... (truncated)"
        
        return formatted_context
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file path."""
        if not file_path:
            return "unknown"
        
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.dart': 'dart',
            '.kt': 'kotlin',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift'
        }
        
        for ext, lang in extension_map.items():
            if file_path.endswith(ext):
                return lang
        
        return "unknown"
    
    def _add_surrounding_context(self, code_snippet: str, file_path: str) -> str:
        """Add surrounding code context (placeholder - would need file access)."""
        # In real implementation, this would read the file and include surrounding code
        return code_snippet
    
    def _extract_related_components(self, 
                                  component_name: str, 
                                  ckg_data: Dict[str, Any]) -> List[str]:
        """Extract related components from CKG data."""
        related = []
        
        # Look for relationships in CKG data
        relationships = ckg_data.get('relationships', [])
        for rel in relationships:
            if rel.get('source') == component_name:
                related.append(rel.get('target', ''))
            elif rel.get('target') == component_name:
                related.append(rel.get('source', ''))
        
        return list(set(filter(None, related)))
    
    def _format_ckg_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format CKG query results."""
        if not results:
            return {}
        
        formatted = {
            'total_results': len(results),
            'components': [],
            'relationships': []
        }
        
        for result in results[:10]:  # Limit results
            if 'name' in result:
                formatted['components'].append({
                    'name': result['name'],
                    'type': result.get('type', 'unknown'),
                    'description': result.get('description', '')
                })
        
        return formatted
    
    def _extract_components_from_results(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract component names from query results."""
        components = []
        for result in results:
            if 'name' in result:
                components.append(result['name'])
        return components
    
    def _format_ckg_summary(self, ckg_data: Dict[str, Any]) -> str:
        """Format CKG data into readable summary."""
        summary_parts = []
        
        if 'total_results' in ckg_data:
            summary_parts.append(f"Found {ckg_data['total_results']} relevant components")
        
        components = ckg_data.get('components', [])
        if components:
            summary_parts.append("Key components:")
            for comp in components[:3]:  # Show top 3
                summary_parts.append(f"- {comp['name']} ({comp['type']})")
        
        relationships = ckg_data.get('relationships', [])
        if relationships:
            summary_parts.append(f"Found {len(relationships)} relationships")
        
        return "\n".join(summary_parts) if summary_parts else "No CKG data available" 