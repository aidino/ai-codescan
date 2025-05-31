"""
LLM Service Request/Response Protocol (LSRP) for AI CodeScan.

This module defines the comprehensive protocol for communication with LLM services,
including structured request/response models, task types, and metadata handling.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json
import uuid
import logging

try:
    from pydantic import BaseModel, Field, validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    # Fallback to dataclasses if Pydantic not available
    BaseModel = object
    Field = None
    PYDANTIC_AVAILABLE = False
    
logger = logging.getLogger(__name__)


class LLMTaskType(Enum):
    """Types of tasks that can be requested from LLM."""
    
    # Code explanation tasks
    CODE_EXPLANATION = "code_explanation"
    FUNCTION_EXPLANATION = "function_explanation" 
    CLASS_EXPLANATION = "class_explanation"
    ARCHITECTURE_EXPLANATION = "architecture_explanation"
    
    # Pull Request analysis tasks
    PR_SUMMARY = "pr_summary"
    PR_IMPACT_ANALYSIS = "pr_impact_analysis"
    PR_RISK_ASSESSMENT = "pr_risk_assessment"
    PR_REVIEW_SUGGESTIONS = "pr_review_suggestions"
    
    # Q&A tasks
    CODE_QA = "code_qa"
    ARCHITECTURE_QA = "architecture_qa"
    BEST_PRACTICES_QA = "best_practices_qa"
    TROUBLESHOOTING_QA = "troubleshooting_qa"
    
    # Report generation tasks
    EXECUTIVE_SUMMARY = "executive_summary"
    TECHNICAL_SUMMARY = "technical_summary"
    ISSUE_PRIORITIZATION = "issue_prioritization"
    RECOMMENDATIONS = "recommendations"
    
    # Analysis tasks
    CIRCULAR_DEPENDENCY_ANALYSIS = "circular_dependency_analysis"
    UNUSED_CODE_ANALYSIS = "unused_code_analysis"
    COMPLEXITY_ANALYSIS = "complexity_analysis"
    SECURITY_ANALYSIS = "security_analysis"


class LLMProvider(Enum):
    """Supported LLM providers."""
    
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    HUGGINGFACE = "huggingface"
    MOCK = "mock"


class RequestPriority(Enum):
    """Priority levels for LLM requests."""
    
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ResponseStatus(Enum):
    """Status of LLM response."""
    
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"


if PYDANTIC_AVAILABLE:
    class LLMServiceRequest(BaseModel):
        """
        Structured request for LLM services using Pydantic.
        
        This model defines the complete structure for LLM requests including
        task type, context, parameters, and metadata.
        """
        
        # Request identification
        request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
        timestamp: datetime = Field(default_factory=datetime.now)
        
        # Task definition
        task_type: LLMTaskType = Field(..., description="Type of task to perform")
        task_description: Optional[str] = Field(None, description="Human-readable task description")
        
        # Context and content
        primary_content: str = Field(..., description="Main content/context for the task")
        secondary_content: Optional[str] = Field(None, description="Additional context if needed")
        code_snippets: Optional[List[Dict[str, str]]] = Field(default_factory=list)
        ckg_data: Optional[Dict[str, Any]] = Field(None, description="Code Knowledge Graph data")
        
        # User interaction
        user_question: Optional[str] = Field(None, description="User's specific question")
        conversation_history: Optional[List[Dict[str, str]]] = Field(default_factory=list)
        
        # LLM parameters
        provider: LLMProvider = Field(default=LLMProvider.OPENAI)
        model_name: Optional[str] = Field(None, description="Specific model to use")
        max_tokens: Optional[int] = Field(4000, ge=1, le=32000)
        temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
        top_p: Optional[float] = Field(0.9, ge=0.0, le=1.0)
        presence_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0)
        frequency_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0)
        
        # Request configuration
        priority: RequestPriority = Field(default=RequestPriority.NORMAL)
        timeout_seconds: Optional[int] = Field(30, ge=1, le=300)
        retry_count: int = Field(default=3, ge=0, le=10)
        
        # Output formatting
        output_format: str = Field(default="text", description="Desired output format")
        output_language: str = Field(default="vi", description="Response language")
        include_reasoning: bool = Field(default=False, description="Include step-by-step reasoning")
        
        # Metadata
        project_context: Optional[Dict[str, Any]] = Field(default_factory=dict)
        session_id: Optional[str] = Field(None, description="Session identifier")
        user_id: Optional[str] = Field(None, description="User identifier")
        custom_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
        
        @validator('task_type', pre=True)
        def validate_task_type(cls, v):
            if isinstance(v, str):
                return LLMTaskType(v)
            return v
        
        @validator('provider', pre=True)
        def validate_provider(cls, v):
            if isinstance(v, str):
                return LLMProvider(v)
            return v
        
        @validator('primary_content')
        def validate_primary_content(cls, v):
            if not v or not v.strip():
                raise ValueError("Primary content cannot be empty")
            return v
        
        class Config:
            use_enum_values = True
            json_encoders = {
                datetime: lambda v: v.isoformat(),
                LLMTaskType: lambda v: v.value,
                LLMProvider: lambda v: v.value,
                RequestPriority: lambda v: v.value
            }


    class LLMServiceResponse(BaseModel):
        """
        Structured response from LLM services using Pydantic.
        
        This model defines the complete structure for LLM responses including
        content, metadata, usage statistics, and error information.
        """
        
        # Response identification
        response_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
        request_id: str = Field(..., description="ID of the original request")
        timestamp: datetime = Field(default_factory=datetime.now)
        
        # Response status
        status: ResponseStatus = Field(..., description="Status of the response")
        success: bool = Field(..., description="Whether the request was successful")
        
        # Content
        content: str = Field(..., description="Main response content")
        formatted_content: Optional[str] = Field(None, description="Formatted version of content")
        summary: Optional[str] = Field(None, description="Brief summary of the response")
        
        # Analysis metadata
        confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence in response")
        reasoning_steps: Optional[List[str]] = Field(default_factory=list)
        sources_used: Optional[List[str]] = Field(default_factory=list)
        
        # LLM provider information
        provider: LLMProvider = Field(..., description="Provider used for this response")
        model_used: Optional[str] = Field(None, description="Actual model used")
        
        # Usage statistics
        tokens_used: Optional[int] = Field(None, ge=0)
        tokens_prompt: Optional[int] = Field(None, ge=0)
        tokens_completion: Optional[int] = Field(None, ge=0)
        estimated_cost: Optional[float] = Field(None, ge=0.0)
        processing_time_seconds: Optional[float] = Field(None, ge=0.0)
        
        # Error information
        error_message: Optional[str] = Field(None, description="Error message if request failed")
        error_code: Optional[str] = Field(None, description="Error code for programmatic handling")
        error_details: Optional[Dict[str, Any]] = Field(default_factory=dict)
        
        # Quality metrics
        response_quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
        relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
        completeness_score: Optional[float] = Field(None, ge=0.0, le=1.0)
        
        # Additional metadata
        follow_up_suggestions: Optional[List[str]] = Field(default_factory=list)
        related_topics: Optional[List[str]] = Field(default_factory=list)
        custom_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
        
        @validator('status', pre=True)
        def validate_status(cls, v):
            if isinstance(v, str):
                return ResponseStatus(v)
            return v
        
        @validator('provider', pre=True) 
        def validate_provider(cls, v):
            if isinstance(v, str):
                return LLMProvider(v)
            return v
        
        @validator('success', pre=True, always=True)
        def validate_success_status_consistency(cls, v, values):
            status = values.get('status')
            if status == ResponseStatus.SUCCESS:
                return True
            elif status in [ResponseStatus.FAILED, ResponseStatus.TIMEOUT, ResponseStatus.ERROR]:
                return False
            return v
        
        class Config:
            use_enum_values = True
            json_encoders = {
                datetime: lambda v: v.isoformat(),
                ResponseStatus: lambda v: v.value,
                LLMProvider: lambda v: v.value
            }

else:
    # Fallback dataclass implementations when Pydantic is not available
    @dataclass
    class LLMServiceRequest:
        """Fallback LLMServiceRequest using dataclasses."""
        
        # Request identification
        request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
        timestamp: datetime = field(default_factory=datetime.now)
        
        # Task definition
        task_type: LLMTaskType = None
        task_description: Optional[str] = None
        
        # Context and content
        primary_content: str = ""
        secondary_content: Optional[str] = None
        code_snippets: List[Dict[str, str]] = field(default_factory=list)
        ckg_data: Optional[Dict[str, Any]] = None
        
        # User interaction
        user_question: Optional[str] = None
        conversation_history: List[Dict[str, str]] = field(default_factory=list)
        
        # LLM parameters
        provider: LLMProvider = LLMProvider.OPENAI
        model_name: Optional[str] = None
        max_tokens: Optional[int] = 4000
        temperature: Optional[float] = 0.7
        top_p: Optional[float] = 0.9
        presence_penalty: Optional[float] = 0.0
        frequency_penalty: Optional[float] = 0.0
        
        # Request configuration
        priority: RequestPriority = RequestPriority.NORMAL
        timeout_seconds: Optional[int] = 30
        retry_count: int = 3
        
        # Output formatting
        output_format: str = "text"
        output_language: str = "vi"
        include_reasoning: bool = False
        
        # Metadata
        project_context: Dict[str, Any] = field(default_factory=dict)
        session_id: Optional[str] = None
        user_id: Optional[str] = None
        custom_metadata: Dict[str, Any] = field(default_factory=dict)
    
    
    @dataclass
    class LLMServiceResponse:
        """Fallback LLMServiceResponse using dataclasses."""
        
        # Response identification
        response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
        request_id: str = ""
        timestamp: datetime = field(default_factory=datetime.now)
        
        # Response status
        status: ResponseStatus = ResponseStatus.SUCCESS
        success: bool = True
        
        # Content
        content: str = ""
        formatted_content: Optional[str] = None
        summary: Optional[str] = None
        
        # Analysis metadata
        confidence_score: Optional[float] = None
        reasoning_steps: List[str] = field(default_factory=list)
        sources_used: List[str] = field(default_factory=list)
        
        # LLM provider information
        provider: LLMProvider = LLMProvider.OPENAI
        model_used: Optional[str] = None
        
        # Usage statistics
        tokens_used: Optional[int] = None
        tokens_prompt: Optional[int] = None
        tokens_completion: Optional[int] = None
        estimated_cost: Optional[float] = None
        processing_time_seconds: Optional[float] = None
        
        # Error information
        error_message: Optional[str] = None
        error_code: Optional[str] = None
        error_details: Dict[str, Any] = field(default_factory=dict)
        
        # Quality metrics
        response_quality_score: Optional[float] = None
        relevance_score: Optional[float] = None
        completeness_score: Optional[float] = None
        
        # Additional metadata
        follow_up_suggestions: List[str] = field(default_factory=list)
        related_topics: List[str] = field(default_factory=list)
        custom_metadata: Dict[str, Any] = field(default_factory=dict)


class LLMRequestBuilder:
    """
    Builder class for constructing LLM service requests.
    
    This class provides a fluent interface for building complex LLM requests
    with proper validation and default values.
    """
    
    def __init__(self):
        """Initialize the builder with default values."""
        self._request_data = {}
        self.reset()
    
    def reset(self) -> 'LLMRequestBuilder':
        """Reset the builder to initial state."""
        self._request_data = {
            'task_type': LLMTaskType.CODE_EXPLANATION,
            'primary_content': '',
            'provider': LLMProvider.OPENAI,
            'max_tokens': 4000,
            'temperature': 0.7,
            'priority': RequestPriority.NORMAL,
            'output_language': 'vi',
            'retry_count': 3,
            'code_snippets': [],
            'conversation_history': [],
            'project_context': {},
            'custom_metadata': {}
        }
        return self
    
    def task_type(self, task_type: Union[LLMTaskType, str]) -> 'LLMRequestBuilder':
        """Set the task type."""
        if isinstance(task_type, str):
            task_type = LLMTaskType(task_type)
        self._request_data['task_type'] = task_type
        return self
    
    def content(self, primary: str, secondary: Optional[str] = None) -> 'LLMRequestBuilder':
        """Set the primary and optional secondary content."""
        self._request_data['primary_content'] = primary
        if secondary:
            self._request_data['secondary_content'] = secondary
        return self
    
    def code_snippets(self, snippets: List[Dict[str, str]]) -> 'LLMRequestBuilder':
        """Add code snippets to the request."""
        self._request_data['code_snippets'] = snippets
        return self
    
    def ckg_data(self, data: Dict[str, Any]) -> 'LLMRequestBuilder':
        """Add CKG data to the request."""
        self._request_data['ckg_data'] = data
        return self
    
    def user_question(self, question: str) -> 'LLMRequestBuilder':
        """Set the user's question."""
        self._request_data['user_question'] = question
        return self
    
    def conversation_history(self, history: List[Dict[str, str]]) -> 'LLMRequestBuilder':
        """Set the conversation history."""
        self._request_data['conversation_history'] = history
        return self
    
    def provider(self, provider: Union[LLMProvider, str]) -> 'LLMRequestBuilder':
        """Set the LLM provider."""
        if isinstance(provider, str):
            provider = LLMProvider(provider)
        self._request_data['provider'] = provider
        return self
    
    def model(self, model_name: str) -> 'LLMRequestBuilder':
        """Set the specific model name."""
        self._request_data['model_name'] = model_name
        return self
    
    def parameters(self, 
                  max_tokens: Optional[int] = None,
                  temperature: Optional[float] = None,
                  top_p: Optional[float] = None) -> 'LLMRequestBuilder':
        """Set LLM generation parameters."""
        if max_tokens is not None:
            self._request_data['max_tokens'] = max_tokens
        if temperature is not None:
            self._request_data['temperature'] = temperature
        if top_p is not None:
            self._request_data['top_p'] = top_p
        return self
    
    def priority(self, priority: Union[RequestPriority, str]) -> 'LLMRequestBuilder':
        """Set the request priority."""
        if isinstance(priority, str):
            priority = RequestPriority(priority)
        self._request_data['priority'] = priority
        return self
    
    def timeout(self, seconds: int) -> 'LLMRequestBuilder':
        """Set the timeout in seconds."""
        self._request_data['timeout_seconds'] = seconds
        return self
    
    def session(self, session_id: str, user_id: Optional[str] = None) -> 'LLMRequestBuilder':
        """Set session information."""
        self._request_data['session_id'] = session_id
        if user_id:
            self._request_data['user_id'] = user_id
        return self
    
    def output_format(self, format_type: str, language: str = "vi") -> 'LLMRequestBuilder':
        """Set output formatting options."""
        self._request_data['output_format'] = format_type
        self._request_data['output_language'] = language
        return self
    
    def metadata(self, **kwargs) -> 'LLMRequestBuilder':
        """Add custom metadata."""
        self._request_data['custom_metadata'].update(kwargs)
        return self
    
    def project_context(self, **kwargs) -> 'LLMRequestBuilder':
        """Add project context information."""
        self._request_data['project_context'].update(kwargs)
        return self
    
    def build(self) -> LLMServiceRequest:
        """Build and return the LLM service request."""
        if not self._request_data.get('primary_content'):
            raise ValueError("Primary content is required")
        
        return LLMServiceRequest(**self._request_data)


class LLMResponseValidator:
    """
    Validator for LLM service responses.
    
    This class provides validation and quality assessment for LLM responses.
    """
    
    @staticmethod
    def validate_response(response: LLMServiceResponse) -> Dict[str, Any]:
        """
        Validate an LLM response and return validation results.
        
        Args:
            response: LLM response to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'is_valid': True,
            'issues': [],
            'quality_score': 0.0,
            'recommendations': []
        }
        
        # Check basic requirements
        if not response.content or not response.content.strip():
            validation_results['is_valid'] = False
            validation_results['issues'].append("Response content is empty")
        
        if response.status != ResponseStatus.SUCCESS and response.success:
            validation_results['issues'].append("Inconsistent status and success flag")
        
        # Check content quality
        content_length = len(response.content) if response.content else 0
        if content_length < 10:
            validation_results['issues'].append("Response content is too short")
        elif content_length > 50000:
            validation_results['issues'].append("Response content is unusually long")
        
        # Calculate quality score
        quality_factors = []
        
        if response.confidence_score is not None:
            quality_factors.append(response.confidence_score)
        
        if response.relevance_score is not None:
            quality_factors.append(response.relevance_score)
        
        if response.completeness_score is not None:
            quality_factors.append(response.completeness_score)
        
        if quality_factors:
            validation_results['quality_score'] = sum(quality_factors) / len(quality_factors)
        else:
            # Estimate quality based on content characteristics
            if content_length > 100 and response.success:
                validation_results['quality_score'] = 0.7
            else:
                validation_results['quality_score'] = 0.3
        
        # Generate recommendations
        if validation_results['quality_score'] < 0.5:
            validation_results['recommendations'].append("Consider regenerating response with different parameters")
        
        if not response.sources_used:
            validation_results['recommendations'].append("Response lacks source attribution")
        
        if not response.follow_up_suggestions:
            validation_results['recommendations'].append("Consider adding follow-up suggestions for better user experience")
        
        return validation_results
    
    @staticmethod
    def calculate_response_metrics(response: LLMServiceResponse) -> Dict[str, float]:
        """
        Calculate various metrics for an LLM response.
        
        Args:
            response: LLM response to analyze
            
        Returns:
            Dictionary with calculated metrics
        """
        metrics = {}
        
        if response.content:
            content = response.content.strip()
            
            # Content metrics
            metrics['content_length'] = len(content)
            metrics['word_count'] = len(content.split())
            metrics['sentence_count'] = content.count('.') + content.count('!') + content.count('?')
            
            # Structure metrics
            metrics['has_code_blocks'] = float('```' in content)
            metrics['has_bullet_points'] = float('•' in content or '- ' in content)
            metrics['has_numbered_lists'] = float(any(f'{i}.' in content for i in range(1, 10)))
        
        # Performance metrics
        if response.processing_time_seconds:
            metrics['processing_time'] = response.processing_time_seconds
        
        if response.tokens_used:
            metrics['tokens_used'] = float(response.tokens_used)
            
            if response.processing_time_seconds:
                metrics['tokens_per_second'] = response.tokens_used / response.processing_time_seconds
        
        # Cost metrics
        if response.estimated_cost:
            metrics['estimated_cost'] = response.estimated_cost
            
            if response.tokens_used:
                metrics['cost_per_token'] = response.estimated_cost / response.tokens_used
        
        return metrics


# Utility functions for protocol operations
def create_code_explanation_request(
    code_content: str,
    file_path: str,
    language: str,
    **kwargs
) -> LLMServiceRequest:
    """Create a request for code explanation."""
    builder = LLMRequestBuilder()
    return (builder
            .task_type(LLMTaskType.CODE_EXPLANATION)
            .content(f"Explain this {language} code from {file_path}:\n\n```{language}\n{code_content}\n```")
            .code_snippets([{
                'content': code_content,
                'file_path': file_path,
                'language': language
            }])
            .project_context(language=language, file_path=file_path)
            .metadata(**kwargs)
            .build())


def create_pr_analysis_request(
    diff_content: str,
    pr_metadata: Dict[str, Any],
    **kwargs
) -> LLMServiceRequest:
    """Create a request for PR analysis."""
    builder = LLMRequestBuilder()
    return (builder
            .task_type(LLMTaskType.PR_SUMMARY)
            .content(f"Analyze this pull request:\n\n```diff\n{diff_content}\n```")
            .project_context(**pr_metadata)
            .metadata(**kwargs)
            .build())


def create_qa_request(
    question: str,
    context: str,
    ckg_data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> LLMServiceRequest:
    """Create a request for Q&A."""
    builder = LLMRequestBuilder()
    request = (builder
               .task_type(LLMTaskType.CODE_QA)
               .user_question(question)
               .content(context)
               .metadata(**kwargs))
    
    if ckg_data:
        request.ckg_data(ckg_data)
    
    return request.build()


def serialize_request(request: LLMServiceRequest) -> str:
    """Serialize an LLM request to JSON string."""
    if PYDANTIC_AVAILABLE:
        return request.json()
    else:
        # Manual serialization for dataclass
        data = {}
        for field_name in request.__annotations__:
            value = getattr(request, field_name)
            if isinstance(value, Enum):
                data[field_name] = value.value
            elif isinstance(value, datetime):
                data[field_name] = value.isoformat()
            else:
                data[field_name] = value
        return json.dumps(data, default=str)


def deserialize_request(json_str: str) -> LLMServiceRequest:
    """Deserialize an LLM request from JSON string."""
    data = json.loads(json_str)
    
    # Convert enum values back to enums
    if 'task_type' in data:
        data['task_type'] = LLMTaskType(data['task_type'])
    if 'provider' in data:
        data['provider'] = LLMProvider(data['provider'])
    if 'priority' in data:
        data['priority'] = RequestPriority(data['priority'])
    if 'timestamp' in data:
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
    
    return LLMServiceRequest(**data)


def serialize_response(response: LLMServiceResponse) -> str:
    """Serialize an LLM response to JSON string."""
    if PYDANTIC_AVAILABLE:
        return response.json()
    else:
        # Manual serialization for dataclass
        data = {}
        for field_name in response.__annotations__:
            value = getattr(response, field_name)
            if isinstance(value, Enum):
                data[field_name] = value.value
            elif isinstance(value, datetime):
                data[field_name] = value.isoformat()
            else:
                data[field_name] = value
        return json.dumps(data, default=str)


def deserialize_response(json_str: str) -> LLMServiceResponse:
    """Deserialize an LLM response from JSON string."""
    data = json.loads(json_str)
    
    # Convert enum values back to enums
    if 'status' in data:
        data['status'] = ResponseStatus(data['status'])
    if 'provider' in data:
        data['provider'] = LLMProvider(data['provider'])
    if 'timestamp' in data:
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
    
    return LLMServiceResponse(**data) 