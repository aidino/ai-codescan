"""
User Intent Parser Agent

Parses user intent from web UI inputs and converts them into structured requests
for the AI CodeScan system.
"""

import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from loguru import logger


class UserIntentParserAgent:
    """
    Agent responsible for parsing user intent from web UI interactions.
    
    This agent converts user inputs (repository URLs, analysis options, etc.)
    into structured data that can be processed by other agents in the system.
    """
    
    def __init__(self):
        """Initialize the UserIntentParserAgent."""
        self.supported_platforms = {
            'github.com': 'github',
            'gitlab.com': 'gitlab', 
            'bitbucket.org': 'bitbucket'
        }
    
    def parse_repository_request(
        self, 
        repo_url: str, 
        pat: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Parse a repository analysis request from web UI.
        
        Args:
            repo_url: Repository URL provided by user
            pat: Personal Access Token (if provided)
            options: Additional analysis options from UI
            
        Returns:
            Dict containing structured user intent
            
        Raises:
            ValueError: If repository URL is invalid or unsupported
        """
        logger.info(f"Parsing repository request for: {repo_url}")
        
        # Validate and parse repository URL
        repo_info = self._parse_repository_url(repo_url)
        
        # Determine analysis scope
        analysis_scope = self._determine_analysis_scope(options or {})
        
        # Create structured user intent
        user_intent = {
            'intent_type': 'repository_analysis',
            'repository': {
                'url': repo_url,
                'platform': repo_info['platform'],
                'owner': repo_info['owner'],
                'name': repo_info['name'],
                'branch': repo_info.get('branch', 'main'),
                'access_token': pat
            },
            'analysis_scope': analysis_scope,
            'options': options or {},
            'timestamp': self._get_timestamp()
        }
        
        logger.info(f"Parsed intent: {user_intent['intent_type']} for {repo_info['platform']}")
        return user_intent
    
    def parse_pr_request(
        self,
        repo_url: str,
        pr_id: str,
        pat: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Parse a Pull Request review request from web UI.
        
        Args:
            repo_url: Repository URL
            pr_id: Pull Request ID
            pat: Personal Access Token (if provided)
            options: Additional analysis options
            
        Returns:
            Dict containing structured user intent for PR review
        """
        logger.info(f"Parsing PR request for: {repo_url}/pull/{pr_id}")
        
        repo_info = self._parse_repository_url(repo_url)
        
        user_intent = {
            'intent_type': 'pr_analysis',
            'repository': {
                'url': repo_url,
                'platform': repo_info['platform'],
                'owner': repo_info['owner'],
                'name': repo_info['name'],
                'access_token': pat
            },
            'pull_request': {
                'id': pr_id,
                'platform': repo_info['platform']
            },
            'options': options or {},
            'timestamp': self._get_timestamp()
        }
        
        return user_intent
    
    def parse_qna_request(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Parse a Q&A request from web UI.
        
        Args:
            question: User's question about the code
            context: Additional context (repository, files, etc.)
            
        Returns:
            Dict containing structured user intent for Q&A
        """
        logger.info(f"Parsing Q&A request: {question[:50]}...")
        
        user_intent = {
            'intent_type': 'qna',
            'question': {
                'text': question,
                'type': self._classify_question_type(question)
            },
            'context': context or {},
            'timestamp': self._get_timestamp()
        }
        
        return user_intent
    
    def _parse_repository_url(self, repo_url: str) -> Dict[str, str]:
        """
        Parse and validate repository URL.
        
        Args:
            repo_url: Repository URL to parse
            
        Returns:
            Dict containing parsed repository information
            
        Raises:
            ValueError: If URL is invalid or unsupported
        """
        if not repo_url:
            raise ValueError("Repository URL cannot be empty")
        
        # Clean up URL
        repo_url = repo_url.strip()
        if not repo_url.startswith(('http://', 'https://')):
            repo_url = 'https://' + repo_url
        
        try:
            parsed = urlparse(repo_url)
            hostname = parsed.netloc
            
            # Check if platform is supported
            platform = None
            for supported_host, platform_name in self.supported_platforms.items():
                if supported_host in hostname:
                    platform = platform_name
                    break
            
            if not platform:
                raise ValueError(f"Unsupported platform: {hostname}")
            
            # Parse path to extract owner/repo
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) < 2:
                raise ValueError("Invalid repository URL format")
            
            owner = path_parts[0]
            repo_name = path_parts[1]
            
            # Remove .git suffix if present
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
            
            repo_info = {
                'platform': platform,
                'owner': owner,
                'name': repo_name,
                'full_name': f"{owner}/{repo_name}"
            }
            
            # Extract branch if specified in URL
            if len(path_parts) > 3 and path_parts[2] == 'tree':
                repo_info['branch'] = path_parts[3]
            
            return repo_info
            
        except Exception as e:
            raise ValueError(f"Failed to parse repository URL: {str(e)}")
    
    def _determine_analysis_scope(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine analysis scope based on user options.
        
        Args:
            options: User-selected options from UI
            
        Returns:
            Dict containing analysis scope configuration
        """
        return {
            'include_tests': options.get('include_tests', True),
            'detailed_analysis': options.get('detailed_analysis', False),
            'force_language': options.get('force_language'),
            'analysis_types': [
                'linting',
                'architecture',
                'ckg_analysis'
            ]
        }
    
    def _classify_question_type(self, question: str) -> str:
        """
        Classify the type of question being asked.
        
        Args:
            question: User's question text
            
        Returns:
            String representing question type
        """
        question_lower = question.lower()
        
        # Check for architecture/structure keywords first (more specific)
        if any(word in question_lower for word in ['structure', 'architecture', 'pattern', 'design']):
            return 'architecture'
        elif any(word in question_lower for word in ['where', 'find', 'locate']):
            return 'location'
        elif any(word in question_lower for word in ['why', 'reason']):
            return 'reasoning'
        elif any(word in question_lower for word in ['how', 'explain', 'what']):
            return 'explanation'
        else:
            return 'general'
    
    def _get_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()
    
    def validate_intent(self, user_intent: Dict[str, Any]) -> bool:
        """
        Validate parsed user intent.
        
        Args:
            user_intent: Parsed user intent dictionary
            
        Returns:
            True if intent is valid, False otherwise
        """
        required_fields = ['intent_type', 'timestamp']
        
        for field in required_fields:
            if field not in user_intent:
                logger.error(f"Missing required field: {field}")
                return False
        
        intent_type = user_intent['intent_type']
        
        if intent_type == 'repository_analysis':
            return self._validate_repository_intent(user_intent)
        elif intent_type == 'pr_analysis':
            return self._validate_pr_intent(user_intent)
        elif intent_type == 'qna':
            return self._validate_qna_intent(user_intent)
        else:
            logger.error(f"Unknown intent type: {intent_type}")
            return False
    
    def _validate_repository_intent(self, intent: Dict[str, Any]) -> bool:
        """Validate repository analysis intent."""
        if 'repository' not in intent:
            return False
        
        repo = intent['repository']
        required_repo_fields = ['url', 'platform', 'owner', 'name']
        
        return all(field in repo for field in required_repo_fields)
    
    def _validate_pr_intent(self, intent: Dict[str, Any]) -> bool:
        """Validate PR analysis intent."""
        return (
            'repository' in intent and 
            'pull_request' in intent and
            'id' in intent['pull_request']
        )
    
    def _validate_qna_intent(self, intent: Dict[str, Any]) -> bool:
        """Validate Q&A intent."""
        return (
            'question' in intent and
            'text' in intent['question'] and
            len(intent['question']['text'].strip()) > 0
        ) 