"""
LLM Analysis Support Agent for AI CodeScan.

This agent provides LLM-powered analysis capabilities including code explanation,
PR summary generation, and Q&A responses. It integrates with the LLM Services
team to deliver intelligent code analysis features.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

# Import LLM Services components
from ..llm_services.prompt_formatter import (
    PromptFormatterModule, 
    PromptTemplate, 
    PromptContext
)
from ..llm_services.context_provider import (
    ContextProviderModule,
    ContextPreparationRequest,
    ContextType,
    PreparedContext
)
from ..llm_services.llm_protocol import (
    LLMServiceRequest,
    LLMServiceResponse,
    LLMTaskType,
    LLMProvider,
    RequestPriority,
    LLMRequestBuilder,
    create_code_explanation_request,
    create_pr_analysis_request,
    create_qa_request
)

logger = logging.getLogger(__name__)


@dataclass
class CodeExplanationRequest:
    """Request for code explanation."""
    
    code_snippet: str
    file_path: str
    language: str
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    related_ckg_info: Optional[Dict[str, Any]] = None
    context_type: str = "general"
    

@dataclass
class PRSummaryRequest:
    """Request for PR summary generation."""
    
    diff_text: str
    pr_metadata: Dict[str, Any]
    changed_files: List[str]
    affected_components_info: Optional[Dict[str, Any]] = None
    ckg_context: Optional[Dict[str, Any]] = None
    

@dataclass
class QARequest:
    """Request for Q&A response."""
    
    user_question: str
    code_context: Optional[str] = None
    ckg_context: Optional[Dict[str, Any]] = None
    search_results: Optional[List[Dict[str, Any]]] = None
    project_metadata: Optional[Dict[str, Any]] = None


class LLMAnalysisSupportAgent:
    """
    Agent providing LLM-powered analysis support for code understanding.
    
    This agent coordinates with LLM Services team to provide intelligent
    analysis capabilities including code explanation, PR summaries, and Q&A.
    """
    
    def __init__(self, 
                 llm_gateway_agent = None,
                 default_provider: LLMProvider = LLMProvider.OPENAI,
                 default_max_tokens: int = 4000,
                 default_temperature: float = 0.7):
        """
        Initialize the LLM Analysis Support Agent.
        
        Args:
            llm_gateway_agent: LLMGatewayAgent instance for sending requests
            default_provider: Default LLM provider to use
            default_max_tokens: Default maximum tokens for requests
            default_temperature: Default temperature for LLM responses
        """
        self.llm_gateway_agent = llm_gateway_agent
        self.default_provider = default_provider
        self.default_max_tokens = default_max_tokens
        self.default_temperature = default_temperature
        
        # Initialize LLM Services components
        self.prompt_formatter = PromptFormatterModule()
        self.context_provider = ContextProviderModule(
            default_max_tokens=default_max_tokens
        )
        
        logger.info("LLMAnalysisSupportAgent initialized successfully")
    
    async def request_code_explanation(self, 
                                     request: CodeExplanationRequest,
                                     **kwargs) -> LLMServiceResponse:
        """
        Request code explanation from LLM.
        
        Args:
            request: Code explanation request containing code snippet and context
            **kwargs: Additional parameters for LLM request
            
        Returns:
            LLMServiceResponse containing the code explanation
        """
        try:
            logger.info(f"Processing code explanation request for {request.file_path}")
            
            # Prepare context using ContextProviderModule
            context_request = ContextPreparationRequest(
                context_type=ContextType.CODE_EXPLANATION,
                max_tokens=kwargs.get('max_tokens', self.default_max_tokens),
                code_snippets=[{
                    'content': request.code_snippet,
                    'file_path': request.file_path,
                    'language': request.language,
                    'function_name': request.function_name,
                    'class_name': request.class_name
                }],
                ckg_data=request.related_ckg_info,
                project_metadata={
                    'language': request.language,
                    'context_type': request.context_type
                }
            )
            
            prepared_context = self.context_provider.prepare_llm_context(context_request)
            
            # Format prompt using PromptFormatterModule
            prompt_context = PromptContext(
                code_snippet=request.code_snippet,
                file_path=request.file_path,
                language=request.language,
                function_name=request.function_name,
                class_name=request.class_name,
                ckg_data=request.related_ckg_info
            )
            
            # Choose appropriate template based on request
            if request.function_name:
                template = PromptTemplate.FUNCTION_EXPLANATION
            elif request.class_name:
                template = PromptTemplate.CLASS_EXPLANATION
            else:
                template = PromptTemplate.CODE_EXPLANATION
            
            formatted_prompt = self.prompt_formatter.format_prompt(
                template, 
                prompt_context,
                max_length=kwargs.get('max_prompt_length')
            )
            
            # Create LLMServiceRequest
            llm_request = (LLMRequestBuilder()
                .task_type(LLMTaskType.CODE_EXPLANATION)
                .content(formatted_prompt, prepared_context.formatted_context)
                .provider(kwargs.get('provider', self.default_provider))
                .parameters(
                    max_tokens=kwargs.get('max_tokens', self.default_max_tokens),
                    temperature=kwargs.get('temperature', self.default_temperature)
                )
                .priority(kwargs.get('priority', RequestPriority.NORMAL))
                .output_format("markdown", "vi")
                .metadata(
                    file_path=request.file_path,
                    language=request.language,
                    context_summary=prepared_context.context_summary
                )
                .build())
            
            # Send request via LLMGatewayAgent
            if self.llm_gateway_agent:
                response = await self.llm_gateway_agent.process_request(llm_request)
            else:
                # Mock response for testing
                logger.warning("No LLMGatewayAgent provided, returning mock response")
                response = self._create_mock_response(
                    llm_request, 
                    f"Mock code explanation for {request.file_path}"
                )
            
            logger.info(f"Code explanation completed for {request.file_path}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate code explanation: {e}")
            return self._create_error_response(
                f"code_explanation_{id(request)}", 
                f"Lỗi khi tạo giải thích code: {str(e)}"
            )
    
    async def request_pr_summary(self, 
                               request: PRSummaryRequest,
                               **kwargs) -> LLMServiceResponse:
        """
        Request PR summary from LLM.
        
        Args:
            request: PR summary request containing diff and metadata
            **kwargs: Additional parameters for LLM request
            
        Returns:
            LLMServiceResponse containing the PR summary
        """
        try:
            logger.info(f"Processing PR summary request for PR: {request.pr_metadata.get('id', 'unknown')}")
            
            # Prepare context using ContextProviderModule
            context_request = ContextPreparationRequest(
                context_type=ContextType.PR_ANALYSIS,
                max_tokens=kwargs.get('max_tokens', self.default_max_tokens),
                diff_content=request.diff_text,
                ckg_data=request.affected_components_info,
                project_metadata={
                    'pr_metadata': request.pr_metadata,
                    'changed_files': request.changed_files
                },
                custom_context={
                    'ckg_context': request.ckg_context
                }
            )
            
            prepared_context = self.context_provider.prepare_llm_context(context_request)
            
            # Format prompt using PromptFormatterModule  
            prompt_context = PromptContext(
                diff_text=request.diff_text,
                changed_files=request.changed_files,
                pr_metadata=request.pr_metadata,
                ckg_data=request.affected_components_info,
                custom_data=request.ckg_context
            )
            
            formatted_prompt = self.prompt_formatter.format_prompt(
                PromptTemplate.PR_SUMMARY,
                prompt_context,
                max_length=kwargs.get('max_prompt_length')
            )
            
            # Create LLMServiceRequest
            llm_request = (LLMRequestBuilder()
                .task_type(LLMTaskType.PR_SUMMARY)
                .content(formatted_prompt, prepared_context.formatted_context)
                .provider(kwargs.get('provider', self.default_provider))
                .parameters(
                    max_tokens=kwargs.get('max_tokens', self.default_max_tokens),
                    temperature=kwargs.get('temperature', self.default_temperature)
                )
                .priority(kwargs.get('priority', RequestPriority.HIGH))
                .output_format("markdown", "vi")
                .metadata(
                    pr_id=request.pr_metadata.get('id'),
                    changed_files_count=len(request.changed_files),
                    context_summary=prepared_context.context_summary
                )
                .build())
            
            # Send request via LLMGatewayAgent
            if self.llm_gateway_agent:
                response = await self.llm_gateway_agent.process_request(llm_request)
            else:
                # Mock response for testing
                logger.warning("No LLMGatewayAgent provided, returning mock response")
                response = self._create_mock_response(
                    llm_request,
                    f"Mock PR summary for PR {request.pr_metadata.get('id', 'unknown')}"
                )
            
            logger.info(f"PR summary completed for PR: {request.pr_metadata.get('id', 'unknown')}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate PR summary: {e}")
            return self._create_error_response(
                f"pr_summary_{id(request)}",
                f"Lỗi khi tạo tóm tắt PR: {str(e)}"
            )
    
    async def request_qna_answer(self, 
                               request: QARequest,
                               **kwargs) -> LLMServiceResponse:
        """
        Request Q&A answer from LLM.
        
        Args:
            request: Q&A request containing user question and context
            **kwargs: Additional parameters for LLM request
            
        Returns:
            LLMServiceResponse containing the answer
        """
        try:
            logger.info(f"Processing Q&A request: {request.user_question[:50]}...")
            
            # Prepare context using ContextProviderModule
            context_request = ContextPreparationRequest(
                context_type=ContextType.QA_RESPONSE,
                max_tokens=kwargs.get('max_tokens', self.default_max_tokens),
                code_snippets=[{'content': request.code_context}] if request.code_context else None,
                ckg_data=request.ckg_context,
                search_results=request.search_results,
                project_metadata=request.project_metadata,
                custom_context={
                    'user_question': request.user_question
                }
            )
            
            prepared_context = self.context_provider.prepare_llm_context(context_request)
            
            # Format prompt using PromptFormatterModule
            prompt_context = PromptContext(
                user_question=request.user_question,
                code_snippet=request.code_context,
                ckg_data=request.ckg_context,
                search_results=request.search_results,
                custom_data=request.project_metadata
            )
            
            formatted_prompt = self.prompt_formatter.format_prompt(
                PromptTemplate.CODE_QA_GENERAL,
                prompt_context,
                max_length=kwargs.get('max_prompt_length')
            )
            
            # Create LLMServiceRequest
            llm_request = (LLMRequestBuilder()
                .task_type(LLMTaskType.CODE_QA)
                .content(formatted_prompt, prepared_context.formatted_context)
                .user_question(request.user_question)
                .provider(kwargs.get('provider', self.default_provider))
                .parameters(
                    max_tokens=kwargs.get('max_tokens', self.default_max_tokens),
                    temperature=kwargs.get('temperature', self.default_temperature)
                )
                .priority(kwargs.get('priority', RequestPriority.NORMAL))
                .output_format("markdown", "vi")
                .metadata(
                    question_type="code_qa",
                    has_code_context=bool(request.code_context),
                    has_ckg_context=bool(request.ckg_context),
                    context_summary=prepared_context.context_summary
                )
                .build())
            
            # Send request via LLMGatewayAgent
            if self.llm_gateway_agent:
                response = await self.llm_gateway_agent.process_request(llm_request)
            else:
                # Mock response for testing
                logger.warning("No LLMGatewayAgent provided, returning mock response")
                response = self._create_mock_response(
                    llm_request,
                    f"Mock answer for question: {request.user_question[:30]}..."
                )
            
            logger.info(f"Q&A response completed for question: {request.user_question[:50]}...")
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate Q&A answer: {e}")
            return self._create_error_response(
                f"qa_answer_{id(request)}",
                f"Lỗi khi tạo câu trả lời: {str(e)}"
            )
    
    # Convenience methods for common use cases
    async def explain_function(self, 
                             code_snippet: str,
                             function_name: str,
                             file_path: str,
                             language: str,
                             ckg_info: Optional[Dict[str, Any]] = None,
                             **kwargs) -> LLMServiceResponse:
        """Convenience method for function explanation."""
        request = CodeExplanationRequest(
            code_snippet=code_snippet,
            file_path=file_path,
            language=language,
            function_name=function_name,
            related_ckg_info=ckg_info,
            context_type="function"
        )
        return await self.request_code_explanation(request, **kwargs)
    
    async def explain_class(self,
                          code_snippet: str,
                          class_name: str,
                          file_path: str,
                          language: str,
                          ckg_info: Optional[Dict[str, Any]] = None,
                          **kwargs) -> LLMServiceResponse:
        """Convenience method for class explanation."""
        request = CodeExplanationRequest(
            code_snippet=code_snippet,
            file_path=file_path,
            language=language,
            class_name=class_name,
            related_ckg_info=ckg_info,
            context_type="class"
        )
        return await self.request_code_explanation(request, **kwargs)
    
    async def analyze_pull_request(self,
                                 diff_text: str,
                                 pr_metadata: Dict[str, Any],
                                 changed_files: List[str],
                                 affected_components: Optional[Dict[str, Any]] = None,
                                 **kwargs) -> LLMServiceResponse:
        """Convenience method for PR analysis."""
        request = PRSummaryRequest(
            diff_text=diff_text,
            pr_metadata=pr_metadata,
            changed_files=changed_files,
            affected_components_info=affected_components
        )
        return await self.request_pr_summary(request, **kwargs)
    
    async def answer_code_question(self,
                                 question: str,
                                 code_context: Optional[str] = None,
                                 ckg_context: Optional[Dict[str, Any]] = None,
                                 **kwargs) -> LLMServiceResponse:
        """Convenience method for code Q&A."""
        request = QARequest(
            user_question=question,
            code_context=code_context,
            ckg_context=ckg_context
        )
        return await self.request_qna_answer(request, **kwargs)
    
    # Helper methods
    def _create_mock_response(self, 
                            request: LLMServiceRequest, 
                            mock_content: str) -> LLMServiceResponse:
        """Create a mock response for testing purposes."""
        from ..llm_services.llm_protocol import ResponseStatus
        
        return LLMServiceResponse(
            request_id=request.request_id,
            status=ResponseStatus.SUCCESS,
            success=True,
            content=mock_content,
            provider=request.provider,
            tokens_used=len(mock_content) // 4,  # Rough estimate
            processing_time_seconds=0.1,
            confidence_score=0.8,
            custom_metadata={'mock': True}
        )
    
    def _create_error_response(self, 
                             request_id: str, 
                             error_message: str) -> LLMServiceResponse:
        """Create an error response."""
        from ..llm_services.llm_protocol import ResponseStatus
        
        return LLMServiceResponse(
            request_id=request_id,
            status=ResponseStatus.ERROR,
            success=False,
            content="",
            error_message=error_message,
            provider=self.default_provider,
            tokens_used=0,
            processing_time_seconds=0.0
        )
    
    # Configuration methods
    def set_llm_gateway(self, llm_gateway_agent):
        """Set the LLMGatewayAgent for processing requests."""
        self.llm_gateway_agent = llm_gateway_agent
        logger.info("LLMGatewayAgent configured successfully")
    
    def update_default_settings(self,
                               provider: Optional[LLMProvider] = None,
                               max_tokens: Optional[int] = None,
                               temperature: Optional[float] = None):
        """Update default settings."""
        if provider:
            self.default_provider = provider
        if max_tokens:
            self.default_max_tokens = max_tokens
        if temperature:
            self.default_temperature = temperature
        
        logger.info(f"Updated default settings: provider={self.default_provider}, "
                   f"max_tokens={self.default_max_tokens}, temperature={self.default_temperature}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status information."""
        return {
            'agent_type': 'LLMAnalysisSupportAgent',
            'default_provider': self.default_provider.value,
            'default_max_tokens': self.default_max_tokens,
            'default_temperature': self.default_temperature,
            'llm_gateway_available': self.llm_gateway_agent is not None,
            'prompt_formatter_available': self.prompt_formatter is not None,
            'context_provider_available': self.context_provider is not None
        }


# Factory function for easy instantiation
def create_llm_analysis_support_agent(
    llm_gateway_agent = None,
    provider: LLMProvider = LLMProvider.OPENAI,
    max_tokens: int = 4000,
    temperature: float = 0.7
) -> LLMAnalysisSupportAgent:
    """
    Factory function to create LLMAnalysisSupportAgent with default settings.
    
    Args:
        llm_gateway_agent: LLMGatewayAgent instance
        provider: Default LLM provider
        max_tokens: Default maximum tokens
        temperature: Default temperature
        
    Returns:
        Configured LLMAnalysisSupportAgent instance
    """
    return LLMAnalysisSupportAgent(
        llm_gateway_agent=llm_gateway_agent,
        default_provider=provider,
        default_max_tokens=max_tokens,
        default_temperature=temperature
    ) 