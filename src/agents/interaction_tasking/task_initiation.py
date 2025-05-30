"""
Task Initiation Agent

Creates structured task definitions from user intent for the orchestrator.
"""

import uuid
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from loguru import logger


@dataclass
class TaskDefinition:
    """
    Structured task definition for the orchestrator.
    
    Attributes:
        task_id: Unique identifier for the task
        task_type: Type of task (repository_analysis, pr_review, qna)
        priority: Task priority (1-10, higher is more urgent)
        repository_info: Repository information if applicable
        pr_info: Pull Request information if applicable
        analysis_config: Configuration for analysis
        metadata: Additional task metadata
        created_at: Task creation timestamp
        estimated_duration: Estimated task duration in seconds
    """
    task_id: str
    task_type: str
    priority: int
    repository_info: Optional[Dict[str, Any]]
    pr_info: Optional[Dict[str, Any]]
    analysis_config: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: float
    estimated_duration: Optional[int] = None


class TaskInitiationAgent:
    """
    Agent responsible for creating structured task definitions from user intent.
    
    This agent takes parsed user intent and converts it into detailed task
    definitions that can be processed by the orchestrator.
    """
    
    def __init__(self):
        """Initialize the TaskInitiationAgent."""
        self.task_templates = self._load_task_templates()
        self.default_configs = self._load_default_configs()
    
    def create_task_definition(self, user_intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a structured task definition from user intent.
        
        Args:
            user_intent: Parsed user intent from UserIntentParserAgent
            
        Returns:
            Dict representation of TaskDefinition
            
        Raises:
            ValueError: If user intent is invalid or unsupported
        """
        logger.info(f"Creating task definition for intent: {user_intent.get('intent_type')}")
        
        # Validate user intent
        if not self._validate_user_intent(user_intent):
            raise ValueError("Invalid user intent structure")
        
        intent_type = user_intent['intent_type']
        task_id = str(uuid.uuid4())
        
        # Create task definition based on intent type
        if intent_type == 'repository_analysis':
            task_def = self._create_repository_analysis_task(task_id, user_intent)
        elif intent_type == 'pr_analysis':
            task_def = self._create_pr_analysis_task(task_id, user_intent)
        elif intent_type == 'qna':
            task_def = self._create_qna_task(task_id, user_intent)
        else:
            raise ValueError(f"Unsupported intent type: {intent_type}")
        
        logger.info(f"Created task definition: {task_id}")
        return asdict(task_def)
    
    def _create_repository_analysis_task(
        self, 
        task_id: str, 
        user_intent: Dict[str, Any]
    ) -> TaskDefinition:
        """
        Create task definition for repository analysis.
        
        Args:
            task_id: Unique task identifier
            user_intent: User intent data
            
        Returns:
            TaskDefinition for repository analysis
        """
        repository = user_intent['repository']
        analysis_scope = user_intent.get('analysis_scope', {})
        options = user_intent.get('options', {})
        
        # Determine priority based on analysis scope
        priority = self._calculate_priority(analysis_scope)
        
        # Build analysis configuration
        analysis_config = {
            'language': analysis_scope.get('force_language'),
            'include_tests': analysis_scope.get('include_tests', True),
            'detailed_analysis': analysis_scope.get('detailed_analysis', False),
            'analysis_types': analysis_scope.get('analysis_types', ['linting']),
            'output_format': 'structured',
            'max_files': 1000,  # Reasonable limit
            'timeout_seconds': 300  # 5 minutes max
        }
        
        # Repository information
        repository_info = {
            'url': repository['url'],
            'platform': repository['platform'],
            'owner': repository['owner'],
            'name': repository['name'],
            'branch': repository.get('branch', 'main'),
            'access_token': repository.get('access_token'),
            'clone_depth': 1  # Shallow clone for performance
        }
        
        # Calculate estimated duration
        estimated_duration = self._estimate_analysis_duration(analysis_config)
        
        # Build metadata
        metadata = {
            'user_session': user_intent.get('session_id'),
            'original_intent': user_intent,
            'ui_options': options,
            'estimated_files': 50,  # Default estimate
            'created_via': 'web_ui'
        }
        
        return TaskDefinition(
            task_id=task_id,
            task_type='repository_analysis',
            priority=priority,
            repository_info=repository_info,
            pr_info=None,
            analysis_config=analysis_config,
            metadata=metadata,
            created_at=time.time(),
            estimated_duration=estimated_duration
        )
    
    def _create_pr_analysis_task(
        self, 
        task_id: str, 
        user_intent: Dict[str, Any]
    ) -> TaskDefinition:
        """
        Create task definition for PR analysis.
        
        Args:
            task_id: Unique task identifier
            user_intent: User intent data
            
        Returns:
            TaskDefinition for PR analysis
        """
        repository = user_intent['repository']
        pull_request = user_intent['pull_request']
        options = user_intent.get('options', {})
        
        # PR analysis typically has higher priority
        priority = 7
        
        # Analysis config for PR review
        analysis_config = {
            'focus': 'pr_diff',
            'include_context': True,
            'diff_analysis': True,
            'impact_analysis': True,
            'security_check': True,
            'output_format': 'pr_review',
            'timeout_seconds': 180  # 3 minutes for PR review
        }
        
        # Repository info
        repository_info = {
            'url': repository['url'],
            'platform': repository['platform'],
            'owner': repository['owner'],
            'name': repository['name'],
            'access_token': repository.get('access_token')
        }
        
        # PR info
        pr_info = {
            'id': pull_request['id'],
            'platform': pull_request['platform']
        }
        
        metadata = {
            'user_session': user_intent.get('session_id'),
            'original_intent': user_intent,
            'ui_options': options,
            'created_via': 'web_ui'
        }
        
        return TaskDefinition(
            task_id=task_id,
            task_type='pr_analysis',
            priority=priority,
            repository_info=repository_info,
            pr_info=pr_info,
            analysis_config=analysis_config,
            metadata=metadata,
            created_at=time.time(),
            estimated_duration=120  # 2 minutes estimate
        )
    
    def _create_qna_task(
        self, 
        task_id: str, 
        user_intent: Dict[str, Any]
    ) -> TaskDefinition:
        """
        Create task definition for Q&A.
        
        Args:
            task_id: Unique task identifier
            user_intent: User intent data
            
        Returns:
            TaskDefinition for Q&A
        """
        question = user_intent['question']
        context = user_intent.get('context', {})
        
        # Q&A can have variable priority based on question complexity
        priority = self._calculate_qna_priority(question)
        
        # Analysis config for Q&A
        analysis_config = {
            'question_type': question['type'],
            'context_search': True,
            'llm_enhanced': True,
            'max_context_size': 10000,  # Max characters of context
            'output_format': 'conversational',
            'timeout_seconds': 60  # 1 minute for Q&A
        }
        
        metadata = {
            'user_session': user_intent.get('session_id'),
            'original_intent': user_intent,
            'question_text': question['text'],
            'question_type': question['type'],
            'context': context,
            'created_via': 'web_ui'
        }
        
        return TaskDefinition(
            task_id=task_id,
            task_type='qna',
            priority=priority,
            repository_info=context.get('repository'),
            pr_info=None,
            analysis_config=analysis_config,
            metadata=metadata,
            created_at=time.time(),
            estimated_duration=30  # 30 seconds estimate
        )
    
    def _calculate_priority(self, analysis_scope: Dict[str, Any]) -> int:
        """
        Calculate task priority based on analysis scope.
        
        Args:
            analysis_scope: Analysis scope configuration
            
        Returns:
            Priority value (1-10)
        """
        base_priority = 5
        
        # Increase priority for detailed analysis
        if analysis_scope.get('detailed_analysis'):
            base_priority += 2
        
        # Increase priority for multiple analysis types
        analysis_types = analysis_scope.get('analysis_types', [])
        if len(analysis_types) > 2:
            base_priority += 1
        
        return min(base_priority, 10)
    
    def _calculate_qna_priority(self, question: Dict[str, Any]) -> int:
        """
        Calculate priority for Q&A tasks.
        
        Args:
            question: Question information
            
        Returns:
            Priority value (1-10)
        """
        question_type = question.get('type', 'general')
        
        priority_map = {
            'architecture': 8,
            'explanation': 6,
            'location': 4,
            'reasoning': 7,
            'general': 5
        }
        
        return priority_map.get(question_type, 5)
    
    def _estimate_analysis_duration(self, analysis_config: Dict[str, Any]) -> int:
        """
        Estimate analysis duration based on configuration.
        
        Args:
            analysis_config: Analysis configuration
            
        Returns:
            Estimated duration in seconds
        """
        base_duration = 60  # 1 minute base
        
        # Add time for each analysis type
        analysis_types = analysis_config.get('analysis_types', ['linting'])
        type_durations = {
            'linting': 30,
            'architecture': 60,
            'ckg_analysis': 90,
            'security': 45
        }
        
        total_duration = base_duration
        for analysis_type in analysis_types:
            total_duration += type_durations.get(analysis_type, 30)
        
        # Multiply for detailed analysis
        if analysis_config.get('detailed_analysis'):
            total_duration = int(total_duration * 1.5)
        
        return min(total_duration, 600)  # Max 10 minutes
    
    def _validate_user_intent(self, user_intent: Dict[str, Any]) -> bool:
        """
        Validate user intent structure.
        
        Args:
            user_intent: User intent to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['intent_type', 'timestamp']
        return all(field in user_intent for field in required_fields)
    
    def _load_task_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Load task templates for different intent types.
        
        Returns:
            Dictionary of task templates
        """
        return {
            'repository_analysis': {
                'default_timeout': 300,
                'max_files': 1000,
                'analysis_types': ['linting', 'architecture']
            },
            'pr_analysis': {
                'default_timeout': 180,
                'focus_types': ['diff', 'impact', 'security']
            },
            'qna': {
                'default_timeout': 60,
                'max_context': 10000
            }
        }
    
    def _load_default_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Load default configurations for different analysis types.
        
        Returns:
            Dictionary of default configurations
        """
        return {
            'linting': {
                'tools': ['flake8', 'pylint'],
                'severity_threshold': 'warning'
            },
            'architecture': {
                'check_circular_deps': True,
                'check_unused_code': True,
                'complexity_threshold': 10
            },
            'security': {
                'check_vulnerabilities': True,
                'check_secrets': True
            }
        } 