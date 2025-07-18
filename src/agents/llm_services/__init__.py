#!/usr/bin/env python3
"""
AI CodeScan - LLM Services Module

Module cung cấp LLM services và abstraction layer.
"""

from .llm_provider_abstraction import (
    LLMProvider,
    OpenAIProvider,
    MockProvider,
    LLMRequest,
    LLMResponse,
    LLMMessage,
    LLMModel,
    create_system_message,
    create_user_message,
    create_assistant_message,
    create_provider
)

from .llm_gateway import (
    LLMGatewayAgent,
    LLMTaskResult
)

from .prompt_formatter import (
    PromptFormatterModule,
    PromptTemplate,
    PromptType,
    PromptContext
)

from .context_provider import (
    ContextProviderModule,
    ContextData,
    ContextPreparationRequest,
    ContextPreparationResult,
    ContextType,
    PreparedContext
)

# NOTE: LLMAnalysisSupportAgent is in code_analysis module
# Import reference để có thể access được
try:
    from ..code_analysis.llm_analysis_support import (
        LLMAnalysisSupportAgent,
        CodeExplanationRequest,
        PRSummaryRequest,
        QARequest,
        create_llm_analysis_support_agent
    )
    _LLM_ANALYSIS_AVAILABLE = True
except ImportError:
    _LLM_ANALYSIS_AVAILABLE = False

__all__ = [
    # Provider Abstraction
    'LLMProvider',
    'OpenAIProvider', 
    'MockProvider',
    'LLMRequest',
    'LLMResponse',
    'LLMMessage',
    'LLMModel',
    'create_system_message',
    'create_user_message',
    'create_assistant_message',
    'create_provider',
    
    # Gateway
    'LLMGatewayAgent',
    'LLMTaskResult',
    
    # Prompt & Context
    'PromptFormatterModule',
    'PromptTemplate',
    'PromptType',
    'PromptContext',
    'ContextProviderModule',
    'ContextData',
    'ContextPreparationRequest',
    'ContextPreparationResult',
    'ContextType',
    'PreparedContext'
]

# Conditionally add LLM Analysis Support exports
if _LLM_ANALYSIS_AVAILABLE:
    __all__.extend([
        'LLMAnalysisSupportAgent',
        'CodeExplanationRequest', 
        'PRSummaryRequest',
        'QARequest',
        'create_llm_analysis_support_agent'
    ])
