"""
Git Operations Agent for Data Acquisition Team.

Handles Git repository operations including cloning, branch management,
and repository information extraction.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
from dataclasses import dataclass
from loguru import logger

import git
from git import Repo, GitCommandError


@dataclass
class RepositoryInfo:
    """Repository information extracted from Git operations."""
    url: str
    local_path: str
    default_branch: str
    commit_hash: str
    author: str
    commit_message: str
    languages: List[str]
    size_mb: float
    file_count: int


class GitOperationsAgent:
    """Agent responsible for Git repository operations."""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize Git Operations Agent.
        
        Args:
            temp_dir: Temporary directory for cloning repos. If None, uses system temp.
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.base_clone_dir = Path(self.temp_dir) / "ai_codescan_repos"
        self.base_clone_dir.mkdir(exist_ok=True)
        
    def clone_repository(
        self, 
        repo_url: str, 
        local_path: Optional[str] = None,
        depth: int = 1,
        branch: Optional[str] = None,
        pat: Optional[str] = None
    ) -> RepositoryInfo:
        """
        Clone a Git repository to local path.
        
        Args:
            repo_url: URL of the repository to clone
            local_path: Local path to clone to. If None, auto-generates path
            depth: Clone depth (default 1 for shallow clone)
            branch: Specific branch to clone
            pat: Personal Access Token for private repos
            
        Returns:
            RepositoryInfo object with repository details
            
        Raises:
            GitCommandError: If clone operation fails
            ValueError: If repository URL is invalid
        """
        logger.info(f"Cloning repository: {repo_url}")
        
        # Validate repository URL
        if not self._is_valid_git_url(repo_url):
            raise ValueError(f"Invalid Git repository URL: {repo_url}")
        
        # Generate local path if not provided
        if local_path is None:
            repo_name = self._extract_repo_name(repo_url)
            local_path = str(self.base_clone_dir / repo_name)
        
        # Clean existing directory if it exists
        if os.path.exists(local_path):
            logger.warning(f"Directory {local_path} exists, removing...")
            shutil.rmtree(local_path)
        
        try:
            # Prepare clone arguments
            clone_kwargs = {
                'depth': depth,
                'single_branch': True
            }
            
            # Add branch if specified
            if branch:
                clone_kwargs['branch'] = branch
            
            # Add authentication if PAT provided
            auth_url = repo_url
            if pat:
                auth_url = self._add_auth_to_url(repo_url, pat)
            
            # Clone repository
            logger.info(f"Cloning to: {local_path}")
            repo = Repo.clone_from(auth_url, local_path, **clone_kwargs)
            
            # Extract repository information
            repo_info = self._extract_repository_info(repo, repo_url, local_path)
            
            logger.success(f"Successfully cloned repository to {local_path}")
            return repo_info
            
        except GitCommandError as e:
            logger.error(f"Git clone failed: {e}")
            # Clean up failed clone attempt
            if os.path.exists(local_path):
                shutil.rmtree(local_path)
            raise
        except Exception as e:
            logger.error(f"Unexpected error during clone: {e}")
            if os.path.exists(local_path):
                shutil.rmtree(local_path)
            raise
    
    def get_repository_info(self, local_path: str) -> RepositoryInfo:
        """
        Get information about an existing local repository.
        
        Args:
            local_path: Path to local repository
            
        Returns:
            RepositoryInfo object
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Repository path does not exist: {local_path}")
        
        try:
            repo = Repo(local_path)
            # Get original URL from remote
            remote_url = repo.remotes.origin.url if repo.remotes else "unknown"
            return self._extract_repository_info(repo, remote_url, local_path)
        except Exception as e:
            logger.error(f"Failed to get repository info: {e}")
            raise
    
    def cleanup_repository(self, local_path: str) -> bool:
        """
        Clean up cloned repository.
        
        Args:
            local_path: Path to repository to clean up
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            if os.path.exists(local_path):
                shutil.rmtree(local_path)
                logger.info(f"Cleaned up repository: {local_path}")
                return True
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup repository {local_path}: {e}")
            return False
    
    def _is_valid_git_url(self, url: str) -> bool:
        """Validate if URL is a valid Git repository URL."""
        try:
            parsed = urlparse(url)
            # Check for common Git hosting patterns
            valid_patterns = [
                'github.com',
                'gitlab.com',
                'bitbucket.org',
                '.git'
            ]
            return any(pattern in url.lower() for pattern in valid_patterns)
        except:
            return False
    
    def _extract_repo_name(self, repo_url: str) -> str:
        """Extract repository name from URL."""
        parsed = urlparse(repo_url)
        path = parsed.path.strip('/')
        
        # Remove .git suffix if present
        if path.endswith('.git'):
            path = path[:-4]
        
        # Get last part of path (repo name)
        return path.split('/')[-1] if '/' in path else path
    
    def _add_auth_to_url(self, url: str, pat: str) -> str:
        """Add PAT authentication to repository URL."""
        parsed = urlparse(url)
        
        if parsed.hostname in ['github.com', 'gitlab.com']:
            # Use token authentication
            auth_url = f"https://{pat}@{parsed.hostname}{parsed.path}"
        else:
            # Generic git authentication
            auth_url = f"https://{pat}@{parsed.netloc}{parsed.path}"
        
        return auth_url
    
    def _extract_repository_info(
        self, 
        repo: Repo, 
        repo_url: str, 
        local_path: str
    ) -> RepositoryInfo:
        """Extract detailed information from repository object."""
        try:
            # Get latest commit info
            latest_commit = repo.head.commit
            
            # Calculate repository size
            repo_size = self._calculate_repo_size(local_path)
            
            # Count files
            file_count = self._count_files(local_path)
            
            # Basic language detection (will be enhanced by LanguageIdentifierAgent)
            languages = self._detect_basic_languages(local_path)
            
            return RepositoryInfo(
                url=repo_url,
                local_path=local_path,
                default_branch=repo.active_branch.name,
                commit_hash=latest_commit.hexsha[:8],
                author=str(latest_commit.author),
                commit_message=latest_commit.message.strip(),
                languages=languages,
                size_mb=repo_size,
                file_count=file_count
            )
        except Exception as e:
            logger.warning(f"Could not extract complete repo info: {e}")
            # Return minimal info if extraction fails
            return RepositoryInfo(
                url=repo_url,
                local_path=local_path,
                default_branch="unknown",
                commit_hash="unknown",
                author="unknown",
                commit_message="unknown",
                languages=["unknown"],
                size_mb=0.0,
                file_count=0
            )
    
    def _calculate_repo_size(self, path: str) -> float:
        """Calculate repository size in MB."""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
            return round(total_size / (1024 * 1024), 2)  # Convert to MB
        except:
            return 0.0
    
    def _count_files(self, path: str) -> int:
        """Count total number of files in repository."""
        try:
            count = 0
            for dirpath, dirnames, filenames in os.walk(path):
                # Skip .git directory
                if '.git' in dirpath:
                    continue
                count += len(filenames)
            return count
        except:
            return 0
    
    def _detect_basic_languages(self, path: str) -> List[str]:
        """Basic language detection based on file extensions."""
        languages = set()
        extension_map = {
            '.py': 'Python',
            '.java': 'Java',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.dart': 'Dart',
            '.kt': 'Kotlin',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP'
        }
        
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                if '.git' in dirpath:
                    continue
                for filename in filenames:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in extension_map:
                        languages.add(extension_map[ext])
            
            return list(languages) if languages else ['Unknown']
        except:
            return ['Unknown'] 