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

# Import debug logging
try:
    from src.core.logging import debug_trace, get_debug_logger
except ImportError:
    # Fallback for testing environment
    def debug_trace(message):
        pass
    def get_debug_logger():
        from loguru import logger
        return logger


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
        
        # Setup debug logger reference
        self._debug_logger = get_debug_logger()
        
        # Log agent initialization
        self._debug_logger.log_step("GitOperationsAgent initialized", {
            "temp_dir": str(self.temp_dir),
            "base_clone_dir": str(self.base_clone_dir)
        })
        
    @debug_trace(stage="DATA_ACQUISITION")
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
        self._debug_logger.log_step("Starting repository clone", {
            "repo_url": repo_url,
            "depth": depth,
            "branch": branch,
            "has_pat": bool(pat)
        })
        
        # Validate repository URL
        if not self._is_valid_git_url(repo_url):
            error_msg = f"Invalid Git repository URL: {repo_url}"
            self._debug_logger.log_error(ValueError(error_msg), {"repo_url": repo_url})
            raise ValueError(error_msg)
        
        # Generate local path if not provided
        if local_path is None:
            repo_name = self._extract_repo_name(repo_url)
            local_path = str(self.base_clone_dir / repo_name)
            self._debug_logger.log_step("Generated local path", {
                "repo_name": repo_name,
                "local_path": local_path
            })
        
        # Clean existing directory if it exists
        if os.path.exists(local_path):
            self._debug_logger.log_step("Cleaning existing directory", {"path": local_path})
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
                self._debug_logger.log_step("Using specific branch", {"branch": branch})
            
            # Add authentication if PAT provided
            auth_url = repo_url
            if pat:
                auth_url = self._add_auth_to_url(repo_url, pat)
                self._debug_logger.log_step("Added authentication to URL", {"has_auth": True})
            
            # Performance tracking
            import time
            clone_start_time = time.time()
            
            # Clone repository
            self._debug_logger.log_step("Executing git clone", {
                "target_path": local_path,
                "clone_args": {k: v for k, v in clone_kwargs.items() if k != 'branch'}
            })
            
            repo = Repo.clone_from(auth_url, local_path, **clone_kwargs)
            
            clone_duration = time.time() - clone_start_time
            self._debug_logger.log_performance_metric("git_clone_duration", clone_duration, "seconds")
            
            # Extract repository information
            repo_info = self._extract_repository_info(repo, repo_url, local_path)
            
            self._debug_logger.log_step("Repository clone completed successfully", {
                "local_path": local_path,
                "duration": f"{clone_duration:.2f}s",
                "repo_info": {
                    "commit_hash": repo_info.commit_hash,
                    "size_mb": repo_info.size_mb,
                    "file_count": repo_info.file_count,
                    "languages": repo_info.languages
                }
            })
            
            return repo_info
            
        except GitCommandError as e:
            self._debug_logger.log_error(e, {
                "repo_url": repo_url,
                "local_path": local_path,
                "clone_kwargs": clone_kwargs
            })
            
            # Clean up failed clone attempt
            if os.path.exists(local_path):
                shutil.rmtree(local_path)
                self._debug_logger.log_step("Cleaned up failed clone", {"path": local_path})
            raise
        except Exception as e:
            self._debug_logger.log_error(e, {
                "repo_url": repo_url,
                "local_path": local_path,
                "operation": "clone_repository"
            })
            
            if os.path.exists(local_path):
                shutil.rmtree(local_path)
            raise
    
    @debug_trace(stage="DATA_ACQUISITION")
    def get_repository_info(self, local_path: str) -> RepositoryInfo:
        """
        Get information about an existing local repository.
        
        Args:
            local_path: Path to local repository
            
        Returns:
            RepositoryInfo object
        """
        self._debug_logger.log_step("Getting repository info", {"local_path": local_path})
        
        if not os.path.exists(local_path):
            error_msg = f"Repository path does not exist: {local_path}"
            self._debug_logger.log_error(FileNotFoundError(error_msg), {"path": local_path})
            raise FileNotFoundError(error_msg)
        
        try:
            repo = Repo(local_path)
            # Get original URL from remote
            remote_url = repo.remotes.origin.url if repo.remotes else "unknown"
            
            repo_info = self._extract_repository_info(repo, remote_url, local_path)
            
            self._debug_logger.log_step("Repository info extracted", {
                "remote_url": remote_url,
                "info": {
                    "commit_hash": repo_info.commit_hash,
                    "size_mb": repo_info.size_mb,
                    "file_count": repo_info.file_count
                }
            })
            
            return repo_info
        except Exception as e:
            self._debug_logger.log_error(e, {"local_path": local_path, "operation": "get_repository_info"})
            raise
    
    @debug_trace(stage="DATA_ACQUISITION")
    def cleanup_repository(self, local_path: str) -> bool:
        """
        Clean up cloned repository.
        
        Args:
            local_path: Path to repository to clean up
            
        Returns:
            True if cleanup successful, False otherwise
        """
        self._debug_logger.log_step("Starting repository cleanup", {"path": local_path})
        
        try:
            if os.path.exists(local_path):
                # Get size before cleanup for metrics
                import shutil
                size_before = sum(f.stat().st_size for f in Path(local_path).rglob('*') if f.is_file())
                
                shutil.rmtree(local_path)
                
                self._debug_logger.log_step("Repository cleanup completed", {
                    "path": local_path,
                    "size_cleaned_mb": size_before / (1024 * 1024)
                })
                
                self._debug_logger.log_performance_metric("cleanup_size_mb", size_before / (1024 * 1024), "MB")
                return True
            else:
                self._debug_logger.log_step("Repository path does not exist, cleanup skipped", {"path": local_path})
                return True
        except Exception as e:
            self._debug_logger.log_error(e, {"local_path": local_path, "operation": "cleanup_repository"})
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
            is_valid = any(pattern in url.lower() for pattern in valid_patterns)
            
            self._debug_logger.log_step("URL validation", {
                "url": url,
                "is_valid": is_valid,
                "matched_patterns": [p for p in valid_patterns if p in url.lower()]
            })
            
            return is_valid
        except Exception as e:
            self._debug_logger.log_error(e, {"url": url, "operation": "url_validation"})
            return False
    
    def _extract_repo_name(self, repo_url: str) -> str:
        """Extract repository name from URL."""
        parsed = urlparse(repo_url)
        path = parsed.path.strip('/')
        
        # Remove .git suffix if present
        if path.endswith('.git'):
            path = path[:-4]
        
        # Get last part of path (repo name)
        repo_name = path.split('/')[-1] if '/' in path else path
        
        self._debug_logger.log_step("Extracted repository name", {
            "repo_url": repo_url,
            "repo_name": repo_name,
            "parsed_path": path
        })
        
        return repo_name
    
    def _add_auth_to_url(self, url: str, pat: str) -> str:
        """Add PAT authentication to repository URL."""
        parsed = urlparse(url)
        
        # For GitHub, GitLab, etc., use token in URL
        if 'github.com' in url:
            auth_url = url.replace('https://', f'https://{pat}@')
        elif 'gitlab.com' in url:
            auth_url = url.replace('https://', f'https://oauth2:{pat}@')
        else:
            auth_url = url.replace('https://', f'https://{pat}@')
        
        self._debug_logger.log_step("Added authentication to URL", {
            "original_domain": parsed.netloc,
            "auth_added": True
        })
        
        return auth_url
    
    def _extract_repository_info(
        self, 
        repo: Repo, 
        repo_url: str, 
        local_path: str
    ) -> RepositoryInfo:
        """Extract comprehensive repository information."""
        self._debug_logger.log_step("Extracting repository information", {
            "repo_url": repo_url,
            "local_path": local_path
        })
        
        try:
            # Get basic repo info
            default_branch = repo.head.reference.name if repo.head.is_valid() else "main"
            commit = repo.head.commit
            commit_hash = commit.hexsha
            author = str(commit.author)
            commit_message = commit.message.strip()
            
            # Calculate repository metrics
            size_mb = self._calculate_repo_size(local_path)
            file_count = self._count_files(local_path)
            languages = self._detect_basic_languages(local_path)
            
            repo_info = RepositoryInfo(
                url=repo_url,
                local_path=local_path,
                default_branch=default_branch,
                commit_hash=commit_hash,
                author=author,
                commit_message=commit_message,
                languages=languages,
                size_mb=size_mb,
                file_count=file_count
            )
            
            self._debug_logger.log_data("repository_info", {
                "url": repo_url,
                "branch": default_branch,
                "commit_hash": commit_hash[:8],  # Short hash for logging
                "author": author,
                "size_mb": size_mb,
                "file_count": file_count,
                "languages": languages
            })
            
            # Log performance metrics
            self._debug_logger.log_performance_metric("repo_size_mb", size_mb, "MB")
            self._debug_logger.log_performance_metric("repo_file_count", file_count, "files")
            
            return repo_info
            
        except Exception as e:
            self._debug_logger.log_error(e, {
                "repo_url": repo_url,
                "local_path": local_path,
                "operation": "extract_repository_info"
            })
            raise
    
    def _calculate_repo_size(self, path: str) -> float:
        """Calculate repository size in MB."""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
            
            size_mb = total_size / (1024 * 1024)
            
            self._debug_logger.log_step("Calculated repository size", {
                "path": path,
                "total_bytes": total_size,
                "size_mb": round(size_mb, 2)
            })
            
            return size_mb
        except Exception as e:
            self._debug_logger.log_error(e, {"path": path, "operation": "calculate_repo_size"})
            return 0.0
    
    def _count_files(self, path: str) -> int:
        """Count total files in repository."""
        try:
            file_count = 0
            for root, dirs, files in os.walk(path):
                file_count += len(files)
            
            self._debug_logger.log_step("Counted repository files", {
                "path": path,
                "file_count": file_count
            })
            
            return file_count
        except Exception as e:
            self._debug_logger.log_error(e, {"path": path, "operation": "count_files"})
            return 0
    
    def _detect_basic_languages(self, path: str) -> List[str]:
        """Detect programming languages in repository."""
        try:
            language_extensions = {
                '.py': 'Python',
                '.js': 'JavaScript', 
                '.ts': 'TypeScript',
                '.java': 'Java',
                '.kt': 'Kotlin',
                '.dart': 'Dart',
                '.cpp': 'C++',
                '.c': 'C',
                '.cs': 'C#',
                '.php': 'PHP',
                '.rb': 'Ruby',
                '.go': 'Go',
                '.rs': 'Rust',
                '.swift': 'Swift'
            }
            
            detected_languages = set()
            
            for root, dirs, files in os.walk(path):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in language_extensions:
                        detected_languages.add(language_extensions[ext])
            
            languages = list(detected_languages)
            
            self._debug_logger.log_step("Detected programming languages", {
                "path": path,
                "languages": languages,
                "total_languages": len(languages)
            })
            
            return languages
        except Exception as e:
            self._debug_logger.log_error(e, {"path": path, "operation": "detect_basic_languages"})
            return [] 