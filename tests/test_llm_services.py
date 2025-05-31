#!/usr/bin/env python3
"""
Unit tests for LLM Services components.

Tests for:
- LLM Provider Abstraction (OpenAI, Mock providers)
- LLM Gateway Agent (multi-provider support, fallbacks)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.llm_services.llm_provider_abstraction import (
    LLMProvider, LLMRequest, LLMResponse, LLMMessage,
    LLMModel, OpenAIProvider, MockProvider,
    create_openai_provider, create_mock_provider
)
from agents.llm_services.llm_gateway import (
    LLMGatewayAgent, LLMServiceRequest, LLMServiceResponse
)


class TestLLMProviderAbstraction:
    """Test LLM Provider abstraction layer."""
    
    def test_llm_message_creation(self):
        """Test LLMMessage dataclass creation."""
        message = LLMMessage(
            role="user",
            content="Hello, how are you?",
            metadata={"timestamp": "2024-01-01"}
        )
        
        assert message.role == "user"
        assert message.content == "Hello, how are you?"
        assert message.metadata["timestamp"] == "2024-01-01"
        
    def test_llm_request_creation(self):
        """Test LLMRequest dataclass creation."""
        messages = [
            LLMMessage("system", "You are a helpful assistant"),
            LLMMessage("user", "Hello")
        ]
        
        request = LLMRequest(
            messages=messages,
            model=LLMModel.GPT_4,
            max_tokens=100,
            temperature=0.7,
            metadata={"task_type": "chat"}
        )
        
        assert len(request.messages) == 2
        assert request.model == LLMModel.GPT_4
        assert request.max_tokens == 100
        assert request.temperature == 0.7
        
    def test_llm_response_creation(self):
        """Test LLMResponse dataclass creation."""
        response = LLMResponse(
            content="Hello! I'm doing well, thank you.",
            model=LLMModel.GPT_4,
            usage_stats={
                "prompt_tokens": 10,
                "completion_tokens": 15,
                "total_tokens": 25
            },
            cost_estimate=0.001,
            metadata={"provider": "openai"}
        )
        
        assert response.content == "Hello! I'm doing well, thank you."
        assert response.model == LLMModel.GPT_4
        assert response.usage_stats["total_tokens"] == 25
        assert response.cost_estimate == 0.001
        
    def test_llm_model_enum(self):
        """Test LLMModel enum values."""
        assert LLMModel.GPT_3_5_TURBO.value == "gpt-3.5-turbo"
        assert LLMModel.GPT_4.value == "gpt-4"
        assert LLMModel.GPT_4_TURBO.value == "gpt-4-turbo-preview"
        assert LLMModel.GPT_4O.value == "gpt-4o"


class TestOpenAIProvider:
    """Test OpenAI provider implementation."""
    
    def setup_method(self):
        """Setup test fixtures."""
        with patch('agents.llm_services.llm_provider_abstraction.OpenAI'):
            self.provider = OpenAIProvider(api_key="test-key")
            
    def test_init(self):
        """Test OpenAI provider initialization."""
        assert self.provider is not None
        assert self.provider.api_key == "test-key"
        
    @patch('agents.llm_services.llm_provider_abstraction.OpenAI')
    def test_init_with_client(self, mock_openai):
        """Test initialization với OpenAI client."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        provider = OpenAIProvider(api_key="test-key")
        
        assert provider.client == mock_client
        mock_openai.assert_called_once_with(api_key="test-key")
        
    def test_is_available(self):
        """Test availability check."""
        # Mock successful API call
        with patch.object(self.provider, '_test_connection', return_value=True):
            assert self.provider.is_available()
            
        # Mock failed API call
        with patch.object(self.provider, '_test_connection', return_value=False):
            assert not self.provider.is_available()
            
    @patch('agents.llm_services.llm_provider_abstraction.OpenAI')
    def test_generate_response_success(self, mock_openai):
        """Test successful response generation."""
        # Mock OpenAI client và response
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_usage = Mock()
        
        # Setup mock chain
        mock_message.content = "Hello! How can I help you?"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-4"
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 15
        mock_usage.total_tokens = 25
        mock_response.usage = mock_usage
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Create provider và request
        provider = OpenAIProvider(api_key="test-key")
        request = LLMRequest(
            messages=[LLMMessage("user", "Hello")],
            model=LLMModel.GPT_4,
            max_tokens=100,
            temperature=0.7
        )
        
        # Test response generation
        response = provider.generate_response(request)
        
        assert isinstance(response, LLMResponse)
        assert response.content == "Hello! How can I help you?"
        assert response.model == LLMModel.GPT_4
        assert response.usage_stats["total_tokens"] == 25
        assert response.cost_estimate > 0
        
    def test_estimate_cost(self):
        """Test cost estimation."""
        # Test GPT-4 cost estimation
        cost = self.provider.estimate_cost(LLMModel.GPT_4, 100, 50)
        assert cost > 0
        
        # Test GPT-3.5 cost estimation
        cost_35 = self.provider.estimate_cost(LLMModel.GPT_3_5_TURBO, 100, 50)
        assert cost_35 > 0
        assert cost_35 < cost  # GPT-3.5 should be cheaper
        
    def test_format_messages_for_openai(self):
        """Test message formatting cho OpenAI API."""
        messages = [
            LLMMessage("system", "You are helpful"),
            LLMMessage("user", "Hello"),
            LLMMessage("assistant", "Hi there!")
        ]
        
        formatted = self.provider._format_messages_for_openai(messages)
        
        assert len(formatted) == 3
        assert formatted[0]["role"] == "system"
        assert formatted[0]["content"] == "You are helpful"
        assert formatted[1]["role"] == "user"
        assert formatted[2]["role"] == "assistant"


class TestMockProvider:
    """Test Mock provider implementation."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.provider = MockProvider()
        
    def test_init(self):
        """Test Mock provider initialization."""
        assert self.provider is not None
        assert self.provider.is_available()
        
    def test_generate_response(self):
        """Test mock response generation."""
        request = LLMRequest(
            messages=[LLMMessage("user", "Hello")],
            model=LLMModel.GPT_4,
            max_tokens=100,
            temperature=0.7
        )
        
        response = self.provider.generate_response(request)
        
        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert len(response.content) > 0
        assert response.model == LLMModel.GPT_4
        assert response.cost_estimate == 0.0  # Mock provider is free
        
    def test_estimate_cost(self):
        """Test mock cost estimation."""
        cost = self.provider.estimate_cost(LLMModel.GPT_4, 100, 50)
        assert cost == 0.0  # Mock provider has no cost
        
    def test_different_mock_responses(self):
        """Test that mock provider generates different responses."""
        request = LLMRequest(
            messages=[LLMMessage("user", "Hello")],
            model=LLMModel.GPT_4
        )
        
        # Generate multiple responses
        responses = [self.provider.generate_response(request) for _ in range(5)]
        
        # Should generate different responses (at least some variety)
        contents = [r.content for r in responses]
        assert len(set(contents)) > 1  # At least some variety


class TestLLMGatewayAgent:
    """Test LLM Gateway Agent functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        # Create mock providers
        self.mock_openai = Mock(spec=OpenAIProvider)
        self.mock_fallback = Mock(spec=MockProvider)
        
        self.mock_openai.is_available.return_value = True
        self.mock_fallback.is_available.return_value = True
        
        # Create gateway với mock providers
        self.gateway = LLMGatewayAgent()
        self.gateway.providers = {
            "openai": self.mock_openai,
            "mock": self.mock_fallback
        }
        self.gateway.provider_order = ["openai", "mock"]
        
    def test_init(self):
        """Test gateway initialization."""
        gateway = LLMGatewayAgent()
        assert gateway is not None
        assert hasattr(gateway, 'send_test_prompt')
        assert hasattr(gateway, 'explain_code_finding')
        
    def test_send_test_prompt_success(self):
        """Test successful test prompt."""
        # Mock successful response
        mock_response = LLMResponse(
            content="Test response",
            model=LLMModel.GPT_4,
            usage_stats={"total_tokens": 20},
            cost_estimate=0.001
        )
        self.mock_openai.generate_response.return_value = mock_response
        
        response = self.gateway.send_test_prompt("Test prompt")
        
        assert isinstance(response, LLMServiceResponse)
        assert response.success
        assert response.content == "Test response"
        assert response.provider_used == "openai"
        
    def test_send_test_prompt_with_fallback(self):
        """Test test prompt với provider fallback."""
        # Mock primary provider failure
        self.mock_openai.generate_response.side_effect = Exception("API Error")
        
        # Mock fallback success
        mock_response = LLMResponse(
            content="Fallback response",
            model=LLMModel.GPT_4,
            usage_stats={"total_tokens": 20},
            cost_estimate=0.0
        )
        self.mock_fallback.generate_response.return_value = mock_response
        
        response = self.gateway.send_test_prompt("Test prompt")
        
        assert response.success
        assert response.content == "Fallback response"
        assert response.provider_used == "mock"
        
    def test_explain_code_finding(self):
        """Test code finding explanation."""
        # Mock response
        mock_response = LLMResponse(
            content="This finding indicates a style issue...",
            model=LLMModel.GPT_4,
            usage_stats={"total_tokens": 50},
            cost_estimate=0.002
        )
        self.mock_openai.generate_response.return_value = mock_response
        
        finding_data = {
            "rule_id": "E501",
            "message": "Line too long",
            "file_path": "test.py",
            "line_number": 10
        }
        
        response = self.gateway.explain_code_finding(finding_data)
        
        assert response.success
        assert "style issue" in response.content
        assert response.metadata["task_type"] == "code_explanation"
        
    def test_suggest_code_improvements(self):
        """Test code improvement suggestions."""
        # Mock response
        mock_response = LLMResponse(
            content="Consider refactoring this function...",
            model=LLMModel.GPT_4,
            usage_stats={"total_tokens": 75},
            cost_estimate=0.003
        )
        self.mock_openai.generate_response.return_value = mock_response
        
        code_context = {
            "file_path": "test.py",
            "function_name": "complex_function",
            "code_snippet": "def complex_function():\n    # complex code here\n    pass"
        }
        
        response = self.gateway.suggest_code_improvements(code_context)
        
        assert response.success
        assert "refactoring" in response.content
        assert response.metadata["task_type"] == "improvement_suggestion"
        
    def test_generate_project_summary(self):
        """Test project summary generation."""
        # Mock response
        mock_response = LLMResponse(
            content="This project appears to be a web application...",
            model=LLMModel.GPT_4,
            usage_stats={"total_tokens": 100},
            cost_estimate=0.004
        )
        self.mock_openai.generate_response.return_value = mock_response
        
        project_data = {
            "name": "test-project",
            "total_files": 25,
            "primary_language": "Python",
            "frameworks": ["Flask"],
            "total_issues": 15
        }
        
        response = self.gateway.generate_project_summary(project_data)
        
        assert response.success
        assert "web application" in response.content
        assert response.metadata["task_type"] == "project_summary"
        
    def test_get_usage_statistics(self):
        """Test usage statistics tracking."""
        # Simulate some usage
        self.gateway.total_requests = 5
        self.gateway.total_cost = 0.05
        self.gateway.successful_requests = 4
        
        stats = self.gateway.get_usage_statistics()
        
        assert stats["total_requests"] == 5
        assert stats["successful_requests"] == 4
        assert stats["total_cost"] == 0.05
        assert stats["success_rate"] == 0.8
        assert "average_cost_per_request" in stats
        
    def test_get_available_providers(self):
        """Test getting available providers."""
        available = self.gateway.get_available_providers()
        
        assert "openai" in available
        assert "mock" in available
        assert len(available) == 2
        
    def test_no_available_providers(self):
        """Test handling when no providers are available."""
        # Mock all providers as unavailable
        self.mock_openai.is_available.return_value = False
        self.mock_fallback.is_available.return_value = False
        
        response = self.gateway.send_test_prompt("Test")
        
        assert not response.success
        assert "No available providers" in response.error_message


class TestLLMFactoryFunctions:
    """Test LLM provider factory functions."""
    
    @patch('agents.llm_services.llm_provider_abstraction.OpenAI')
    def test_create_openai_provider(self, mock_openai):
        """Test OpenAI provider factory function."""
        provider = create_openai_provider("test-api-key")
        
        assert isinstance(provider, OpenAIProvider)
        assert provider.api_key == "test-api-key"
        
    def test_create_mock_provider(self):
        """Test Mock provider factory function."""
        provider = create_mock_provider()
        
        assert isinstance(provider, MockProvider)
        assert provider.is_available()


class TestLLMIntegration:
    """Integration tests cho LLM Services workflow."""
    
    @patch('agents.llm_services.llm_provider_abstraction.OpenAI')
    def test_complete_llm_workflow(self, mock_openai):
        """Test complete LLM workflow từ request đến response."""
        # Setup mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_usage = Mock()
        
        mock_message.content = "This is a detailed explanation of the code issue..."
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-4"
        mock_usage.prompt_tokens = 50
        mock_usage.completion_tokens = 100
        mock_usage.total_tokens = 150
        mock_response.usage = mock_usage
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Create real providers và gateway
        openai_provider = OpenAIProvider(api_key="test-key")
        mock_provider = MockProvider()
        
        gateway = LLMGatewayAgent()
        gateway.providers = {
            "openai": openai_provider,
            "mock": mock_provider
        }
        gateway.provider_order = ["openai", "mock"]
        
        # Test complete workflow
        finding_data = {
            "rule_id": "E501",
            "message": "line too long (85 > 79 characters)",
            "file_path": "src/main.py",
            "line_number": 42,
            "context": "This line contains a very long string literal"
        }
        
        response = gateway.explain_code_finding(finding_data)
        
        # Verify response
        assert response.success
        assert response.content == "This is a detailed explanation of the code issue..."
        assert response.provider_used == "openai"
        assert response.cost_estimate > 0
        assert response.metadata["task_type"] == "code_explanation"
        
        # Verify usage statistics were updated
        stats = gateway.get_usage_statistics()
        assert stats["total_requests"] >= 1
        assert stats["successful_requests"] >= 1
        assert stats["total_cost"] > 0


if __name__ == "__main__":
    pytest.main([__file__]) 