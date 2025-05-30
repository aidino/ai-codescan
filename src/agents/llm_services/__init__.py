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
    'LLMTaskResult'
]
