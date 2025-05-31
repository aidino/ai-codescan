#!/usr/bin/env python3
"""
AI CodeScan - Data Acquisition Module

Module chịu trách nhiệm thu thập dữ liệu từ repository.
"""

from .git_operations import (
    GitOperationsAgent,
    RepositoryInfo,
    PullRequestInfo
)

from .language_identifier import (
    LanguageIdentifierAgent,
    LanguageInfo,
    FrameworkInfo,
    DependencyInfo
)

from .data_preparation import (
    DataPreparationAgent,
    ProjectDataContext,
    FileAnalysisResult,
    StructureNode
)

__all__ = [
    # Git Operations
    'GitOperationsAgent',
    'RepositoryInfo',
    'PullRequestInfo',
    
    # Language Identification  
    'LanguageIdentifierAgent',
    'LanguageInfo',
    'FrameworkInfo',
    'DependencyInfo',
    
    # Data Preparation
    'DataPreparationAgent',
    'ProjectDataContext',
    'FileAnalysisResult',
    'StructureNode'
]
