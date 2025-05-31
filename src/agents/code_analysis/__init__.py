#!/usr/bin/env python3
"""
AI CodeScan - Code Analysis Module

Module thực hiện static analysis và contextual analysis trên code.
"""

from .static_analysis_integrator import (
    StaticAnalysisIntegratorAgent,
    Finding,
    AnalysisResult,
    SeverityLevel,
    FindingType
)

from .contextual_query import (
    ContextualQueryAgent,
    ContextualFinding,
    ContextualAnalysisResult
)

from .architectural_analyzer import (
    ArchitecturalAnalyzerAgent,
    ArchitecturalIssue,
    ArchitecturalAnalysisResult,
    CircularDependency,
    UnusedElement,
    IssueType
)

from .llm_analysis_support import (
    LLMAnalysisSupportAgent,
    CodeExplanationRequest,
    PRSummaryRequest,
    QARequest,
    create_llm_analysis_support_agent
)

from .pr_analyzer import (
    PRAnalyzerAgent,
    PRImpactAnalysis,
    PRAnalysisResult
)

__all__ = [
    # Static Analysis
    'StaticAnalysisIntegratorAgent',
    'Finding',
    'AnalysisResult',
    'SeverityLevel',
    'FindingType',
    
    # Contextual Query
    'ContextualQueryAgent',
    'ContextualFinding',
    'ContextualAnalysisResult',
    
    # Architectural Analysis
    'ArchitecturalAnalyzerAgent',
    'ArchitecturalIssue',
    'ArchitecturalAnalysisResult',
    'CircularDependency',
    'UnusedElement',
    'IssueType',
    
    # LLM Analysis Support
    'LLMAnalysisSupportAgent',
    'CodeExplanationRequest',
    'PRSummaryRequest',
    'QARequest',
    'create_llm_analysis_support_agent',
    
    # PR Analysis
    'PRAnalyzerAgent',
    'PRImpactAnalysis',
    'PRAnalysisResult'
]
