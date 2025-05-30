"""
Unit tests for TEAM Interaction & Tasking components.

Tests the web UI agents and their functionality.
"""

import pytest
import time
from unittest.mock import Mock, patch
from typing import Dict, Any

# Add src to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agents.interaction_tasking.user_intent_parser import UserIntentParserAgent
from agents.interaction_tasking.dialog_manager import DialogManagerAgent, DialogState
from agents.interaction_tasking.task_initiation import TaskInitiationAgent, TaskDefinition
from agents.interaction_tasking.presentation import PresentationAgent


class TestUserIntentParserAgent:
    """Test suite for UserIntentParserAgent."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = UserIntentParserAgent()
    
    def test_parse_github_repository_request(self):
        """Test parsing GitHub repository request."""
        repo_url = "https://github.com/octocat/Hello-World"
        options = {
            'analysis_type': 'Repository Review',
            'force_language': None,
            'include_tests': True,
            'detailed_analysis': False
        }
        
        result = self.parser.parse_repository_request(repo_url, None, options)
        
        assert result['intent_type'] == 'repository_analysis'
        assert result['repository']['platform'] == 'github'
        assert result['repository']['owner'] == 'octocat'
        assert result['repository']['name'] == 'Hello-World'
        assert result['repository']['url'] == repo_url
        assert result['analysis_scope']['include_tests'] is True
        assert 'timestamp' in result
    
    def test_parse_gitlab_repository_with_token(self):
        """Test parsing GitLab repository with personal access token."""
        repo_url = "https://gitlab.com/user/project"
        pat = "glpat-test-token"
        options = {'detailed_analysis': True}
        
        result = self.parser.parse_repository_request(repo_url, pat, options)
        
        assert result['repository']['platform'] == 'gitlab'
        assert result['repository']['access_token'] == pat
        assert result['analysis_scope']['detailed_analysis'] is True
    
    def test_parse_repository_with_branch(self):
        """Test parsing repository URL with specific branch."""
        repo_url = "https://github.com/user/repo/tree/feature-branch"
        
        result = self.parser.parse_repository_request(repo_url)
        
        assert result['repository']['branch'] == 'feature-branch'
    
    def test_parse_invalid_repository_url(self):
        """Test parsing invalid repository URL."""
        with pytest.raises(ValueError, match="Failed to parse repository URL"):
            self.parser.parse_repository_request("not-a-valid-url")
    
    def test_parse_unsupported_platform(self):
        """Test parsing unsupported git platform."""
        with pytest.raises(ValueError, match="Unsupported platform"):
            self.parser.parse_repository_request("https://unknown-git-platform.com/user/repo")
    
    def test_parse_pr_request(self):
        """Test parsing Pull Request review request."""
        repo_url = "https://github.com/user/repo"
        pr_id = "123"
        
        result = self.parser.parse_pr_request(repo_url, pr_id)
        
        assert result['intent_type'] == 'pr_analysis'
        assert result['pull_request']['id'] == pr_id
        assert result['repository']['platform'] == 'github'
    
    def test_parse_qna_request(self):
        """Test parsing Q&A request."""
        question = "What are the main architectural patterns in this codebase?"
        context = {'repository': {'url': 'https://github.com/user/repo'}}
        
        result = self.parser.parse_qna_request(question, context)
        
        assert result['intent_type'] == 'qna'
        assert result['question']['text'] == question
        assert result['question']['type'] == 'architecture'
        assert result['context'] == context
    
    def test_validate_intent_repository(self):
        """Test validating repository analysis intent."""
        valid_intent = {
            'intent_type': 'repository_analysis',
            'repository': {
                'url': 'https://github.com/user/repo',
                'platform': 'github',
                'owner': 'user',
                'name': 'repo'
            },
            'timestamp': time.time()
        }
        
        assert self.parser.validate_intent(valid_intent) is True
    
    def test_validate_intent_missing_fields(self):
        """Test validating intent with missing required fields."""
        invalid_intent = {
            'intent_type': 'repository_analysis'
            # Missing timestamp and repository
        }
        
        assert self.parser.validate_intent(invalid_intent) is False


class TestDialogManagerAgent:
    """Test suite for DialogManagerAgent."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.dialog_manager = DialogManagerAgent()
    
    def test_start_session(self):
        """Test starting a new dialog session."""
        session_id = "test-session-123"
        
        self.dialog_manager.start_session(session_id)
        
        assert self.dialog_manager.current_session_id == session_id
        assert self.dialog_manager.current_state == DialogState.WAITING_INPUT
        assert len(self.dialog_manager.state_history) > 0
    
    def test_update_state(self):
        """Test updating dialog state."""
        self.dialog_manager.start_session("test-session")
        
        self.dialog_manager.update_state("processing")
        
        assert self.dialog_manager.current_state == DialogState.PROCESSING
        assert len(self.dialog_manager.state_history) == 2  # Start + update
    
    def test_state_transitions(self):
        """Test various state transitions."""
        self.dialog_manager.start_session("test-session")
        
        # Test normal flow
        assert self.dialog_manager.can_accept_input() is True
        assert self.dialog_manager.is_processing() is False
        
        self.dialog_manager.update_state("processing")
        assert self.dialog_manager.can_accept_input() is False
        assert self.dialog_manager.is_processing() is True
        
        self.dialog_manager.update_state("completed")
        assert self.dialog_manager.can_accept_input() is True
        assert self.dialog_manager.is_processing() is False
    
    def test_error_state_handling(self):
        """Test error state management."""
        self.dialog_manager.start_session("test-session")
        
        error_msg = "Test error occurred"
        error_details = {"code": 500, "details": "Internal server error"}
        
        self.dialog_manager.set_error_state(error_msg, error_details)
        
        assert self.dialog_manager.current_state == DialogState.ERROR
        assert self.dialog_manager.can_accept_input() is True
        
        # Test clearing error
        self.dialog_manager.clear_error()
        assert self.dialog_manager.current_state == DialogState.WAITING_INPUT
    
    def test_record_user_interaction(self):
        """Test recording user interactions."""
        self.dialog_manager.start_session("test-session")
        
        interaction_data = {"url": "https://github.com/user/repo", "button": "analyze"}
        self.dialog_manager.record_user_interaction("repository_input", interaction_data)
        
        interactions = self.dialog_manager.get_interaction_history()
        assert len(interactions) == 1
        assert interactions[0]['type'] == "repository_input"
        assert interactions[0]['data'] == interaction_data
    
    def test_get_suggested_actions(self):
        """Test getting suggested actions based on state."""
        self.dialog_manager.start_session("test-session")
        
        # Test waiting input suggestions
        suggestions = self.dialog_manager.get_suggested_actions()
        assert len(suggestions) > 0
        assert any(s['action'] == 'repository_analysis' for s in suggestions)
        
        # Test completed state suggestions
        self.dialog_manager.update_state("completed")
        completed_suggestions = self.dialog_manager.get_suggested_actions()
        assert any(s['action'] == 'new_analysis' for s in completed_suggestions)
    
    def test_session_summary(self):
        """Test getting session summary."""
        session_id = "test-session-456"
        self.dialog_manager.start_session(session_id)
        
        # Add some interactions
        self.dialog_manager.record_user_interaction("test", {"data": "value"})
        self.dialog_manager.update_state("processing")
        
        summary = self.dialog_manager.get_session_summary()
        
        assert summary['session_id'] == session_id
        assert summary['total_interactions'] == 1
        assert summary['current_state'] == 'processing'
        assert 'duration_seconds' in summary


class TestTaskInitiationAgent:
    """Test suite for TaskInitiationAgent."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.task_agent = TaskInitiationAgent()
    
    def test_create_repository_analysis_task(self):
        """Test creating repository analysis task definition."""
        user_intent = {
            'intent_type': 'repository_analysis',
            'repository': {
                'url': 'https://github.com/user/repo',
                'platform': 'github',
                'owner': 'user',
                'name': 'repo',
                'branch': 'main'
            },
            'analysis_scope': {
                'include_tests': True,
                'detailed_analysis': False,
                'force_language': None,
                'analysis_types': ['linting', 'architecture']
            },
            'options': {},
            'timestamp': time.time()
        }
        
        task_def = self.task_agent.create_task_definition(user_intent)
        
        assert task_def['task_type'] == 'repository_analysis'
        assert task_def['repository_info']['platform'] == 'github'
        assert task_def['analysis_config']['include_tests'] is True
        assert 'task_id' in task_def
        assert 'estimated_duration' in task_def
    
    def test_create_pr_analysis_task(self):
        """Test creating PR analysis task definition."""
        user_intent = {
            'intent_type': 'pr_analysis',
            'repository': {
                'url': 'https://github.com/user/repo',
                'platform': 'github',
                'owner': 'user',
                'name': 'repo'
            },
            'pull_request': {
                'id': '123',
                'platform': 'github'
            },
            'options': {},
            'timestamp': time.time()
        }
        
        task_def = self.task_agent.create_task_definition(user_intent)
        
        assert task_def['task_type'] == 'pr_analysis'
        assert task_def['pr_info']['id'] == '123'
        assert task_def['priority'] == 7  # PR analysis has higher priority
        assert task_def['analysis_config']['focus'] == 'pr_diff'
    
    def test_create_qna_task(self):
        """Test creating Q&A task definition."""
        user_intent = {
            'intent_type': 'qna',
            'question': {
                'text': 'How does this architecture work?',
                'type': 'architecture'
            },
            'context': {},
            'timestamp': time.time()
        }
        
        task_def = self.task_agent.create_task_definition(user_intent)
        
        assert task_def['task_type'] == 'qna'
        assert task_def['priority'] == 8  # Architecture questions have high priority
        assert task_def['analysis_config']['question_type'] == 'architecture'
    
    def test_priority_calculation(self):
        """Test task priority calculation."""
        # Test basic analysis scope
        basic_scope = {'detailed_analysis': False, 'analysis_types': ['linting']}
        priority1 = self.task_agent._calculate_priority(basic_scope)
        
        # Test detailed analysis with multiple types
        detailed_scope = {
            'detailed_analysis': True, 
            'analysis_types': ['linting', 'architecture', 'security']
        }
        priority2 = self.task_agent._calculate_priority(detailed_scope)
        
        assert priority2 > priority1  # Detailed analysis should have higher priority
    
    def test_duration_estimation(self):
        """Test analysis duration estimation."""
        config1 = {'analysis_types': ['linting'], 'detailed_analysis': False}
        duration1 = self.task_agent._estimate_analysis_duration(config1)
        
        config2 = {
            'analysis_types': ['linting', 'architecture', 'ckg_analysis'], 
            'detailed_analysis': True
        }
        duration2 = self.task_agent._estimate_analysis_duration(config2)
        
        assert duration2 > duration1  # More complex analysis should take longer
        assert duration2 <= 600  # Should not exceed max duration
    
    def test_invalid_user_intent(self):
        """Test handling invalid user intent."""
        invalid_intent = {'invalid': 'data'}
        
        with pytest.raises(ValueError, match="Invalid user intent structure"):
            self.task_agent.create_task_definition(invalid_intent)
    
    def test_unsupported_intent_type(self):
        """Test handling unsupported intent type."""
        unsupported_intent = {
            'intent_type': 'unsupported_type',
            'timestamp': time.time()
        }
        
        with pytest.raises(ValueError, match="Unsupported intent type"):
            self.task_agent.create_task_definition(unsupported_intent)


class TestPresentationAgent:
    """Test suite for PresentationAgent."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.presentation = PresentationAgent()
    
    @patch('streamlit.header')
    @patch('streamlit.warning')
    def test_display_empty_results(self, mock_warning, mock_header):
        """Test displaying empty results."""
        self.presentation.display_analysis_results({})
        
        mock_warning.assert_called_once_with("⚠️ No analysis results to display")
    
    def test_severity_colors_and_icons(self):
        """Test severity color and icon mappings."""
        assert 'critical' in self.presentation.severity_colors
        assert 'critical' in self.presentation.severity_icons
        assert self.presentation.severity_colors['critical'] == '#FF4B4B'
        assert self.presentation.severity_icons['critical'] == '🔴'
    
    def test_export_results_json_format(self):
        """Test JSON export functionality."""
        results = {
            'repository': {'url': 'https://github.com/user/repo'},
            'linter_results': {'total_issues': 5}
        }
        
        # Mock the JSON export - in real implementation this would create downloadable content
        import json
        json_data = json.dumps(results, indent=2, default=str)
        
        assert 'repository' in json_data
        assert 'linter_results' in json_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 