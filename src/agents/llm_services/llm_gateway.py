#!/usr/bin/env python3
"""
AI CodeScan - LLM Gateway Agent

Gateway agent quản lý tương tác với LLM providers.
Cung cấp high-level interface cho các tác vụ LLM khác nhau.
"""

import os
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from loguru import logger

from .llm_provider_abstraction import (
    LLMProvider, 
    OpenAIProvider, 
    MockProvider,
    LLMRequest, 
    LLMResponse, 
    LLMMessage,
    LLMModel
)


@dataclass
class LLMServiceRequest:
    """Service request với metadata."""
    task_type: str
    messages: List[LLMMessage]
    model: LLMModel
    parameters: Dict[str, Any]


@dataclass
class LLMServiceResponse:
    """Service response với metadata."""
    task_type: str
    content: str
    success: bool
    llm_response: Optional[LLMResponse] = None
    error_message: Optional[str] = None


@dataclass
class LLMTaskResult:
    """Kết quả từ LLM task."""
    task_type: str
    input_data: Any
    output_data: Any
    llm_response: LLMResponse
    success: bool
    error_message: Optional[str] = None
    
    @property
    def response(self) -> str:
        """Backward compatibility property for response content."""
        return self.output_data if isinstance(self.output_data, str) else str(self.output_data)


class LLMGatewayAgent:
    """
    Gateway agent cho LLM services.
    
    Trách nhiệm:
    - Manage multiple LLM providers
    - Route requests đến appropriate provider
    - Handle retry logic và fallbacks
    - Provide high-level LLM task interfaces
    - Monitor usage và costs
    """
    
    def __init__(self, 
                 primary_provider: Optional[LLMProvider] = None,
                 fallback_providers: Optional[List[LLMProvider]] = None,
                 default_model: LLMModel = LLMModel.GPT_3_5_TURBO):
        """
        Khởi tạo LLM Gateway Agent.
        
        Args:
            primary_provider: Primary LLM provider
            fallback_providers: Fallback providers nếu primary fails
            default_model: Default model để sử dụng
        """
        self.primary_provider = primary_provider or self._create_default_provider()
        self.fallback_providers = fallback_providers or []
        self.default_model = default_model
        
        # Usage tracking
        self.usage_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_cost": 0.0,
            "total_tokens": 0
        }
        
        logger.info(f"LLM Gateway initialized với primary provider: {type(self.primary_provider).__name__}")
    
    def _create_default_provider(self) -> LLMProvider:
        """Tạo default provider based on available config."""
        # Try OpenAI first
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                openai_provider = OpenAIProvider(api_key=openai_key)
                if openai_provider.is_available():
                    logger.info("Using OpenAI as default provider")
                    return openai_provider
            except Exception as e:
                logger.debug(f"Cannot use OpenAI provider: {str(e)}")
        
        # Fallback to mock provider
        logger.info("Using Mock provider as fallback")
        return MockProvider()
    
    def send_request(self, request: LLMRequest) -> LLMResponse:
        """
        Send request đến LLM provider với retry logic.
        
        Args:
            request: LLM request
            
        Returns:
            LLMResponse: Response từ LLM
        """
        self.usage_stats["total_requests"] += 1
        
        # Try primary provider
        providers_to_try = [self.primary_provider] + self.fallback_providers
        
        for i, provider in enumerate(providers_to_try):
            try:
                logger.debug(f"Trying provider {type(provider).__name__} (attempt {i+1})")
                
                if not provider.is_available():
                    logger.warning(f"Provider {type(provider).__name__} not available")
                    continue
                
                response = provider.generate_response(request)
                
                # Update usage stats
                self.usage_stats["successful_requests"] += 1
                self.usage_stats["total_tokens"] += response.usage_stats.get("total_tokens", 0)
                self.usage_stats["total_cost"] += response.cost_estimate
                
                return response
                    
            except Exception as e:
                logger.error(f"Error with provider {type(provider).__name__}: {str(e)}")
        
        # All providers failed
        self.usage_stats["failed_requests"] += 1
        return LLMResponse(
            content="",
            model=request.model,
            usage_stats={},
            cost_estimate=0.0,
            metadata={"error": "All LLM providers failed"}
        )
    
    def send_test_prompt(self, prompt: str = "Hello! This is a test prompt.") -> LLMTaskResult:
        """
        Send test prompt đến LLM.
        
        Args:
            prompt: Test prompt to send
            
        Returns:
            LLMTaskResult: Result của test
        """
        try:
            messages = [
                LLMMessage(role="system", content="You are a helpful assistant. Respond briefly to test prompts."),
                LLMMessage(role="user", content=prompt)
            ]
            
            request = LLMRequest(
                messages=messages,
                model=self.default_model,
                max_tokens=100,
                temperature=0.7
            )
            
            response = self.send_request(request)
            
            return LLMTaskResult(
                task_type="test_prompt",
                input_data=prompt,
                output_data=response.content,
                llm_response=response,
                success=True,
                error_message=None
            )
            
        except Exception as e:
            logger.error(f"Error sending test prompt: {str(e)}")
            return LLMTaskResult(
                task_type="test_prompt",
                input_data=prompt,
                output_data="",
                llm_response=None,
                success=False,
                error_message=str(e)
            )
    
    def explain_code_finding(self, finding_description: str, code_context: str = "") -> LLMTaskResult:
        """
        Explain code finding với LLM.
        
        Args:
            finding_description: Mô tả finding cần explain
            code_context: Code context liên quan
            
        Returns:
            LLMTaskResult: Explanation từ LLM
        """
        try:
            system_prompt = """You are an expert code analyzer. Explain code findings clearly and provide actionable recommendations. 
            Focus on:
            1. What the issue is
            2. Why it matters  
            3. How to fix it
            4. Best practices to prevent similar issues
            
            Keep explanations concise but comprehensive."""
            
            user_prompt = f"""Please explain this code finding:
            
            Finding: {finding_description}
            
            Code Context: {code_context if code_context else 'No additional context provided'}
            
            Provide a clear explanation and recommendations."""
            
            messages = [
                create_system_message(system_prompt),
                create_user_message(user_prompt)
            ]
            
            request = LLMRequest(
                messages=messages,
                model=self.default_model,
                max_tokens=500,
                temperature=0.3  # Lower temperature for more consistent explanations
            )
            
            response = self.send_request(request)
            
            return LLMTaskResult(
                task_type="explain_finding",
                input_data={"finding": finding_description, "context": code_context},
                output_data=response.content,
                llm_response=response,
                success=response.success,
                error_message=response.error_message
            )
            
        except Exception as e:
            logger.error(f"Error explaining code finding: {str(e)}")
            return LLMTaskResult(
                task_type="explain_finding",
                input_data={"finding": finding_description, "context": code_context},
                output_data="",
                llm_response=LLMResponse(
                    content="",
                    model=self.default_model.value,
                    usage={},
                    finish_reason="error",
                    response_time_ms=0,
                    success=False,
                    error_message=str(e)
                ),
                success=False,
                error_message=str(e)
            )
    
    def suggest_code_improvements(self, code_snippet: str, analysis_results: Dict[str, Any]) -> LLMTaskResult:
        """
        Suggest improvements cho code snippet based on analysis results.
        
        Args:
            code_snippet: Code cần improve
            analysis_results: Results từ static analysis
            
        Returns:
            LLMTaskResult: Improvement suggestions
        """
        try:
            system_prompt = """You are an expert software engineer. Analyze code and provide specific improvement suggestions.
            Focus on:
            1. Code quality improvements
            2. Performance optimizations
            3. Maintainability enhancements
            4. Best practices adherence
            
            Provide concrete, actionable suggestions with example code when helpful."""
            
            # Format analysis results
            findings_summary = self._format_analysis_for_llm(analysis_results)
            
            user_prompt = f"""Please suggest improvements for this code:
            
            Code:
            ```python
            {code_snippet}
            ```
            
            Analysis Results:
            {findings_summary}
            
            Provide specific suggestions for improvement."""
            
            messages = [
                create_system_message(system_prompt),
                create_user_message(user_prompt)
            ]
            
            request = LLMRequest(
                messages=messages,
                model=self.default_model,
                max_tokens=800,
                temperature=0.3
            )
            
            response = self.send_request(request)
            
            return LLMTaskResult(
                task_type="suggest_improvements",
                input_data={"code": code_snippet, "analysis": analysis_results},
                output_data=response.content,
                llm_response=response,
                success=response.success,
                error_message=response.error_message
            )
            
        except Exception as e:
            logger.error(f"Error suggesting improvements: {str(e)}")
            return LLMTaskResult(
                task_type="suggest_improvements",
                input_data={"code": code_snippet, "analysis": analysis_results},
                output_data="",
                llm_response=LLMResponse(
                    content="",
                    model=self.default_model.value,
                    usage={},
                    finish_reason="error",
                    response_time_ms=0,
                    success=False,
                    error_message=str(e)
                ),
                success=False,
                error_message=str(e)
            )
    
    def _format_analysis_for_llm(self, analysis_results: Dict[str, Any]) -> str:
        """Format analysis results cho LLM consumption."""
        formatted = []
        
        if "summary" in analysis_results:
            summary = analysis_results["summary"]
            formatted.append(f"Total Findings: {summary.get('total_findings', 0)}")
            formatted.append(f"Files Analyzed: {summary.get('total_files_analyzed', 0)}")
        
        if "severity_breakdown" in analysis_results:
            severity = analysis_results["severity_breakdown"]
            formatted.append("Severity Breakdown:")
            for level, count in severity.items():
                if count > 0:
                    formatted.append(f"  - {level}: {count}")
        
        if "type_breakdown" in analysis_results:
            types = analysis_results["type_breakdown"]
            formatted.append("Issue Types:")
            for issue_type, count in types.items():
                if count > 0:
                    formatted.append(f"  - {issue_type}: {count}")
        
        return "\n".join(formatted) if formatted else "No analysis results available"
    
    def generate_project_summary(self, project_info: Dict[str, Any]) -> LLMTaskResult:
        """
        Generate project summary từ analysis results.
        
        Args:
            project_info: Project information và analysis results
            
        Returns:
            LLMTaskResult: Project summary
        """
        try:
            system_prompt = """You are a technical project analyst. Generate concise, informative summaries of software projects based on analysis data.
            Include:
            1. Project overview và characteristics
            2. Key findings và insights
            3. Code quality assessment
            4. Recommendations for improvement
            
            Keep the summary professional and actionable."""
            
            # Format project info
            project_description = self._format_project_info_for_llm(project_info)
            
            user_prompt = f"""Generate a comprehensive summary for this project:
            
            {project_description}
            
            Provide insights và recommendations based on the analysis data."""
            
            messages = [
                create_system_message(system_prompt),
                create_user_message(user_prompt)
            ]
            
            request = LLMRequest(
                messages=messages,
                model=self.default_model,
                max_tokens=1000,
                temperature=0.4
            )
            
            response = self.send_request(request)
            
            return LLMTaskResult(
                task_type="project_summary",
                input_data=project_info,
                output_data=response.content,
                llm_response=response,
                success=response.success,
                error_message=response.error_message
            )
            
        except Exception as e:
            logger.error(f"Error generating project summary: {str(e)}")
            return LLMTaskResult(
                task_type="project_summary",
                input_data=project_info,
                output_data="",
                llm_response=LLMResponse(
                    content="",
                    model=self.default_model.value,
                    usage={},
                    finish_reason="error",
                    response_time_ms=0,
                    success=False,
                    error_message=str(e)
                ),
                success=False,
                error_message=str(e)
            )
    
    def _format_project_info_for_llm(self, project_info: Dict[str, Any]) -> str:
        """Format project info cho LLM consumption."""
        formatted = []
        
        # Basic project info
        if "name" in project_info:
            formatted.append(f"Project: {project_info['name']}")
        
        if "language_profile" in project_info:
            profile = project_info["language_profile"]
            formatted.append(f"Primary Language: {profile.get('primary_language', 'Unknown')}")
            formatted.append(f"Project Type: {profile.get('project_type', 'Unknown')}")
        
        # Analysis results
        if "analysis_results" in project_info:
            results = project_info["analysis_results"]
            formatted.append("\nAnalysis Results:")
            formatted.append(self._format_analysis_for_llm(results))
        
        return "\n".join(formatted) if formatted else "Limited project information available"
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Lấy usage statistics.
        
        Returns:
            Dict với usage stats
        """
        return self.usage_stats.copy()
    
    def reset_usage_stats(self):
        """Reset usage statistics."""
        self.usage_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_cost": 0.0,
            "total_tokens": 0
        }
        logger.info("Usage statistics reset")
    
    def is_available(self) -> bool:
        """
        Kiểm tra gateway có available không.
        
        Returns:
            bool: True nếu có ít nhất 1 provider available
        """
        if self.primary_provider.is_available():
            return True
        
        for provider in self.fallback_providers:
            if provider.is_available():
                return True
        
        return False
    
    def get_available_models(self) -> List[LLMModel]:
        """
        Lấy danh sách models available.
        
        Returns:
            List[LLMModel]: Available models
        """
        available_models = set()
        
        if self.primary_provider.is_available():
            available_models.update(self.primary_provider.get_supported_models())
        
        for provider in self.fallback_providers:
            if provider.is_available():
                available_models.update(provider.get_supported_models())
        
        return list(available_models) 