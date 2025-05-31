#!/usr/bin/env python3
"""
AI CodeScan - LLM Provider Abstraction Layer

Abstract base classes và implementations cho different LLM providers.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import time
from loguru import logger

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class LLMModel(Enum):
    """Supported LLM models."""
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_4O = "gpt-4o"


@dataclass
class LLMMessage:
    """Message trong conversation."""
    role: str  # "system", "user", "assistant"
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMRequest:
    """Request tới LLM provider."""
    messages: List[LLMMessage]
    model: LLMModel
    max_tokens: int = 1000
    temperature: float = 0.7
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Response từ LLM provider."""
    content: str
    model: LLMModel
    usage_stats: Dict[str, int]
    cost_estimate: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract base class cho LLM providers."""
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        pass
    
    @abstractmethod
    def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response từ LLM."""
        pass
    
    @abstractmethod
    def estimate_cost(self, model: LLMModel, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost cho request."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation."""
    
    # Pricing per 1K tokens (updated 2024)
    PRICING = {
        LLMModel.GPT_3_5_TURBO: {"input": 0.0015, "output": 0.002},
        LLMModel.GPT_4: {"input": 0.03, "output": 0.06},
        LLMModel.GPT_4_TURBO: {"input": 0.01, "output": 0.03},
        LLMModel.GPT_4O: {"input": 0.005, "output": 0.015}
    }
    
    def __init__(self, api_key: str):
        """Initialize OpenAI provider."""
        self.api_key = api_key
        if OpenAI:
            self.client = OpenAI(api_key=api_key)
        else:
            logger.warning("OpenAI library not installed")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if OpenAI is available."""
        if not self.client:
            return False
        return self._test_connection()
    
    def _test_connection(self) -> bool:
        """Test connection tới OpenAI."""
        try:
            # Simple test request
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            logger.debug(f"OpenAI connection test failed: {e}")
            return False
    
    def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response từ OpenAI."""
        try:
            formatted_messages = self._format_messages_for_openai(request.messages)
            
            response = self.client.chat.completions.create(
                model=request.model.value,
                messages=formatted_messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            content = response.choices[0].message.content
            usage_stats = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            cost = self.estimate_cost(
                request.model,
                usage_stats["prompt_tokens"],
                usage_stats["completion_tokens"]
            )
            
            return LLMResponse(
                content=content,
                model=request.model,
                usage_stats=usage_stats,
                cost_estimate=cost,
                metadata={"provider": "openai", "response_time": time.time()}
            )
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise
    
    def estimate_cost(self, model: LLMModel, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost cho OpenAI request."""
        if model not in self.PRICING:
            return 0.0
            
        pricing = self.PRICING[model]
        input_cost = (prompt_tokens / 1000) * pricing["input"]
        output_cost = (completion_tokens / 1000) * pricing["output"]
        
        return input_cost + output_cost
    
    def _format_messages_for_openai(self, messages: List[LLMMessage]) -> List[Dict]:
        """Format messages cho OpenAI API."""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]


class MockProvider(LLMProvider):
    """Mock provider cho testing."""
    
    def __init__(self):
        """Initialize mock provider."""
        self.call_count = 0
        
    def is_available(self) -> bool:
        """Mock provider always available."""
        return True
    
    def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate mock response."""
        self.call_count += 1
        
        # Generate different responses based on content
        user_message = ""
        for msg in request.messages:
            if msg.role == "user":
                user_message = msg.content.lower()
                break
        
        if "explain" in user_message:
            content = "This code appears to have the following issues that need attention..."
        elif "suggest" in user_message:
            content = "Here are some suggestions to improve this code..."
        elif "summary" in user_message:
            content = "Project Summary: This codebase contains..."
        else:
            content = f"Mock response #{self.call_count}: I understand your request."
        
        # Mock usage stats
        usage_stats = {
            "prompt_tokens": len(user_message.split()) * 2,
            "completion_tokens": len(content.split()),
            "total_tokens": len(user_message.split()) * 2 + len(content.split())
        }
        
        return LLMResponse(
            content=content,
            model=request.model,
            usage_stats=usage_stats,
            cost_estimate=0.0,  # Mock provider is free
            metadata={"provider": "mock", "call_count": self.call_count}
        )
    
    def estimate_cost(self, model: LLMModel, prompt_tokens: int, completion_tokens: int) -> float:
        """Mock provider is always free."""
        return 0.0


# Factory functions
def create_openai_provider(api_key: str) -> OpenAIProvider:
    """Create OpenAI provider."""
    return OpenAIProvider(api_key)


def create_mock_provider() -> MockProvider:
    """Create mock provider."""
    return MockProvider() 