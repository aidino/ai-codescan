"""
Unit tests for PAT Handler Agent.

Tests secure PAT storage, retrieval, và validation functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.agents.interaction_tasking.pat_handler import PATHandlerAgent, PATInfo


class TestPATHandlerAgent:
    """Test cases for PATHandlerAgent."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.agent = PATHandlerAgent()
    
    def test_initialization(self):
        """Test agent initialization."""
        assert self.agent.session_key is not None
        assert self.agent.cipher is not None
        assert len(self.agent.stored_pats) == 0
    
    def test_store_pat_success(self):
        """Test successful PAT storage."""
        platform = "GitHub"
        username = "testuser"
        token = "ghp_test123456789012345678901234567890"
        session_id = "test_session"
        
        token_hash = self.agent.store_pat(platform, username, token, session_id)
        
        assert token_hash is not None
        assert len(token_hash) == 64  # SHA256 hash length
        assert token_hash in self.agent.stored_pats
        
        stored_pat = self.agent.stored_pats[token_hash]
        assert stored_pat.platform == "github"
        assert stored_pat.username == username
        assert stored_pat.token_hash == token_hash
        assert stored_pat.created_at is not None
    
    def test_store_empty_token_raises_error(self):
        """Test storing empty token raises ValueError."""
        with pytest.raises(ValueError, match="Token cannot be empty"):
            self.agent.store_pat("GitHub", "user", "", "session")
        
        with pytest.raises(ValueError, match="Token cannot be empty"):
            self.agent.store_pat("GitHub", "user", "   ", "session")
    
    def test_retrieve_pat_success(self):
        """Test successful PAT retrieval."""
        platform = "GitHub"
        username = "testuser"
        token = "ghp_test123456789012345678901234567890"
        session_id = "test_session"
        
        # Store PAT first
        token_hash = self.agent.store_pat(platform, username, token, session_id)
        
        # Retrieve PAT
        retrieved_token = self.agent.retrieve_pat(token_hash)
        
        assert retrieved_token == token
        
        # Check last_used was updated
        stored_pat = self.agent.stored_pats[token_hash]
        assert stored_pat.last_used is not None
    
    def test_retrieve_nonexistent_pat_returns_none(self):
        """Test retrieving non-existent PAT returns None."""
        fake_hash = "nonexistent_hash"
        result = self.agent.retrieve_pat(fake_hash)
        assert result is None
    
    def test_validate_pat_format_github(self):
        """Test GitHub PAT format validation."""
        # Valid GitHub PATs
        valid_tokens = [
            "ghp_" + "x" * 36,
            "gho_" + "x" * 36, 
            "ghu_" + "x" * 36,
            "ghs_" + "x" * 36,
            "ghr_" + "x" * 36
        ]
        
        for token in valid_tokens:
            assert self.agent.validate_pat_format("GitHub", token)
        
        # Invalid GitHub PATs
        invalid_tokens = [
            "invalid_token",
            "ghp_short",
            "wrong_prefix_" + "x" * 30
        ]
        
        for token in invalid_tokens:
            assert not self.agent.validate_pat_format("GitHub", token)
    
    def test_validate_pat_format_gitlab(self):
        """Test GitLab PAT format validation."""
        # Valid GitLab PAT
        valid_token = "glpat-" + "x" * 20
        assert self.agent.validate_pat_format("GitLab", valid_token)
        
        # Invalid GitLab PATs
        invalid_tokens = [
            "invalid_token",
            "glpat-short",
            "wrong_prefix_" + "x" * 20
        ]
        
        for token in invalid_tokens:
            assert not self.agent.validate_pat_format("GitLab", token)
    
    def test_validate_pat_format_bitbucket(self):
        """Test BitBucket PAT format validation."""
        # Valid BitBucket PAT (generic validation)
        valid_token = "x" * 32
        assert self.agent.validate_pat_format("BitBucket", valid_token)
        
        # Invalid BitBucket PAT
        invalid_token = "short"
        assert not self.agent.validate_pat_format("BitBucket", invalid_token)
    
    def test_validate_pat_format_unknown_platform(self):
        """Test PAT validation for unknown platform."""
        # Should use generic validation (min 20 chars, alphanumeric)
        valid_token = "a" * 20
        assert self.agent.validate_pat_format("UnknownPlatform", valid_token)
        
        invalid_token = "short"
        assert not self.agent.validate_pat_format("UnknownPlatform", invalid_token)
    
    def test_get_platform_pat_url(self):
        """Test getting PAT creation URLs for different platforms."""
        github_url = self.agent.get_platform_pat_url("GitHub")
        assert "github.com/settings/tokens" in github_url
        
        gitlab_url = self.agent.get_platform_pat_url("GitLab")
        assert "gitlab.com" in gitlab_url
        
        bitbucket_url = self.agent.get_platform_pat_url("BitBucket")
        assert "bitbucket.org" in bitbucket_url
        
        # Unknown platform should return generic URL
        unknown_url = self.agent.get_platform_pat_url("Unknown")
        assert "git-scm.com" in unknown_url
    
    def test_clear_session_pats(self):
        """Test clearing all PATs from session."""
        # Store multiple PATs
        tokens = [
            ("GitHub", "user1", "ghp_" + "x" * 36, "session1"),
            ("GitLab", "user2", "glpat-" + "x" * 20, "session1")
        ]
        
        for platform, username, token, session_id in tokens:
            self.agent.store_pat(platform, username, token, session_id)
        
        assert len(self.agent.stored_pats) == 2
        
        # Clear all PATs
        self.agent.clear_session_pats()
        assert len(self.agent.stored_pats) == 0
    
    def test_get_stored_pat_info(self):
        """Test getting PAT information without exposing tokens."""
        platform = "GitHub"
        username = "testuser"
        token = "ghp_test123456789012345678901234567890"
        session_id = "test_session"
        
        # Store PAT
        token_hash = self.agent.store_pat(platform, username, token, session_id)
        
        # Get PAT info
        pat_info = self.agent.get_stored_pat_info()
        
        assert len(pat_info) == 1
        info = pat_info[0]
        
        assert info['platform'] == "github"
        assert info['username'] == username
        assert info['token_hash'].endswith("...")
        assert len(info['token_hash']) == 11  # 8 chars + "..."
        assert info['created_at'] is not None
        assert 'last_used' in info
    
    def test_multiple_pats_storage(self):
        """Test storing multiple PATs from different platforms."""
        pats = [
            ("GitHub", "user1", "ghp_" + "x" * 36, "session1"),
            ("GitLab", "user2", "glpat-" + "x" * 20, "session1"),
            ("BitBucket", "user3", "x" * 32, "session1")
        ]
        
        stored_hashes = []
        for platform, username, token, session_id in pats:
            token_hash = self.agent.store_pat(platform, username, token, session_id)
            stored_hashes.append(token_hash)
        
        assert len(self.agent.stored_pats) == 3
        assert len(set(stored_hashes)) == 3  # All hashes should be unique
        
        # Verify all can be retrieved
        for i, (platform, username, token, session_id) in enumerate(pats):
            retrieved = self.agent.retrieve_pat(stored_hashes[i])
            assert retrieved == token
    
    def test_encryption_decryption_integrity(self):
        """Test that encryption/decryption maintains data integrity."""
        test_tokens = [
            "ghp_short_token_12345678901234567890",
            "glpat-very_long_token_with_special_chars!@#$%",
            "simple_token_123",
            "token_with_unicode_ñáéíóú"
        ]
        
        for token in test_tokens:
            token_hash = self.agent.store_pat("GitHub", "user", token, "session")
            retrieved = self.agent.retrieve_pat(token_hash)
            assert retrieved == token
    
    @patch('src.agents.interaction_tasking.pat_handler.logger')
    def test_logging_on_operations(self, mock_logger):
        """Test that operations are properly logged."""
        platform = "GitHub"
        username = "testuser"
        token = "ghp_test123456789012345678901234567890"
        session_id = "test_session"
        
        # Store PAT
        token_hash = self.agent.store_pat(platform, username, token, session_id)
        
        # Verify logging calls
        mock_logger.info.assert_called()
        
        # Retrieve PAT
        self.agent.retrieve_pat(token_hash)
        
        # Should have additional log calls
        assert mock_logger.info.call_count >= 2


class TestPATInfo:
    """Test cases for PATInfo dataclass."""
    
    def test_pat_info_creation(self):
        """Test PATInfo dataclass creation."""
        pat_info = PATInfo(
            platform="github",
            username="testuser",
            token_hash="abc123",
            encrypted_token=b"encrypted_data",
            created_at="2024-01-01T00:00:00",
            last_used=None
        )
        
        assert pat_info.platform == "github"
        assert pat_info.username == "testuser"
        assert pat_info.token_hash == "abc123"
        assert pat_info.encrypted_token == b"encrypted_data"
        assert pat_info.created_at == "2024-01-01T00:00:00"
        assert pat_info.last_used is None
    
    def test_pat_info_with_last_used(self):
        """Test PATInfo with last_used timestamp."""
        pat_info = PATInfo(
            platform="gitlab",
            username="user2",
            token_hash="def456",
            encrypted_token=b"data",
            created_at="2024-01-01T00:00:00",
            last_used="2024-01-01T12:00:00"
        )
        
        assert pat_info.last_used == "2024-01-01T12:00:00" 