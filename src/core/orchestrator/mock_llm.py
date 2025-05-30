#!/usr/bin/env python3
"""
AI CodeScan - Mock LLM Module

Mock LLM implementation cho testing mà không cần API key thực.
"""

from typing import Any, Dict, List, Optional, Union
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.callbacks.manager import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)

class MockChatOpenAI(BaseChatModel):
    """
    Mock implementation của ChatOpenAI cho testing.
    
    Trả về predefined responses thay vì call API thực.
    """
    
    model_name: str = "mock-gpt-4"
    temperature: float = 0.1
    max_tokens: int = 4000
    
    def __init__(self, **kwargs):
        """Khởi tạo MockChatOpenAI."""
        super().__init__(**kwargs)
        self.model_name = kwargs.get("model", "mock-gpt-4")
        self.temperature = kwargs.get("temperature", 0.1)
        self.max_tokens = kwargs.get("max_tokens", 4000)
    
    @property
    def _llm_type(self) -> str:
        """Return type của LLM."""
        return "mock_openai"
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Generate mock response.
        
        Args:
            messages: List of messages
            stop: Stop sequences
            run_manager: Callback manager
            **kwargs: Additional arguments
            
        Returns:
            ChatResult với mock response
        """
        # Mock response dựa trên context
        last_message = messages[-1] if messages else None
        
        if last_message and isinstance(last_message, HumanMessage):
            content = last_message.content.lower()
            
            # Generate appropriate mock response
            if "data acquisition" in content or "thu thập dữ liệu" in content:
                response = "Đã hoàn thành thu thập dữ liệu từ repository. Phát hiện 15 files Python với tổng size 2.3MB."
            elif "code analysis" in content or "phân tích code" in content:
                response = "Phân tích code hoàn thành. Overall quality score: 8.5/10. Phát hiện 2 potential issues và 3 improvement opportunities."
            elif "knowledge graph" in content or "ckg" in content:
                response = "Đã xây dựng Code Knowledge Graph với 45 entities và 78 relationships. Graph density: 0.73."
            elif "insights" in content or "recommendation" in content:
                response = "Dựa trên analysis, đề xuất 3 high-priority improvements: 1) Optimize database queries, 2) Increase test coverage, 3) Refactor legacy modules."
            elif "synthesis" in content or "báo cáo" in content:
                response = "Đã tổng hợp báo cáo hoàn chỉnh với executive summary, detailed findings và actionable recommendations."
            else:
                response = "Mock LLM response: Đã xử lý yêu cầu và sinh ra output phù hợp cho testing."
        else:
            response = "Mock LLM response: Hello from MockChatOpenAI"
        
        # Tạo AIMessage response
        message = AIMessage(content=response)
        generation = ChatGeneration(message=message)
        
        return ChatResult(generations=[generation])
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Async version của _generate."""
        return self._generate(messages, stop, None, **kwargs)
    
    def _identifying_params(self) -> Dict[str, Any]:
        """Identifying parameters."""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
    
    @property
    def _default_params(self) -> Dict[str, Any]:
        """Default parameters."""
        return {
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
    
    def invoke(self, input_data: Union[str, List[BaseMessage]], **kwargs) -> AIMessage:
        """
        Invoke method cho compatibility.
        
        Args:
            input_data: Input string hoặc messages
            **kwargs: Additional arguments
            
        Returns:
            AIMessage response
        """
        if isinstance(input_data, str):
            messages = [HumanMessage(content=input_data)]
        else:
            messages = input_data
        
        result = self._generate(messages, **kwargs)
        return result.generations[0].message
    
    def predict(self, text: str, **kwargs) -> str:
        """
        Predict method cho compatibility.
        
        Args:
            text: Input text
            **kwargs: Additional arguments
            
        Returns:
            Response string
        """
        response = self.invoke(text, **kwargs)
        return response.content 