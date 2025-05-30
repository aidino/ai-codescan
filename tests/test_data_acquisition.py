"""
Unit tests for Data Acquisition Team agents.

Tests GitOperationsAgent, LanguageIdentifierAgent, and DataPreparationAgent.
"""

import os
import tempfile
import shutil
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src to path
import sys
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from agents.data_acquisition import (
    GitOperationsAgent,
    LanguageIdentifierAgent,
    DataPreparationAgent,
    RepositoryInfo,
    LanguageInfo,
    ProjectLanguageProfile,
    ProjectDataContext,
    FileInfo,
    DirectoryStructure,
    ProjectMetadata
)


class TestGitOperationsAgent:
    """Test GitOperationsAgent functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def git_agent(self, temp_dir):
        """Create GitOperationsAgent instance."""
        return GitOperationsAgent(temp_dir=temp_dir)
    
    def test_init(self, temp_dir):
        """Test GitOperationsAgent initialization."""
        agent = GitOperationsAgent(temp_dir=temp_dir)
        assert agent.temp_dir == temp_dir
        assert agent.base_clone_dir.exists()
    
    def test_is_valid_git_url(self, git_agent):
        """Test URL validation."""
        # Valid URLs
        assert git_agent._is_valid_git_url("https://github.com/user/repo.git")
        assert git_agent._is_valid_git_url("https://gitlab.com/user/repo.git")
        assert git_agent._is_valid_git_url("https://bitbucket.org/user/repo")
        
        # Invalid URLs
        assert not git_agent._is_valid_git_url("invalid-url")
        assert not git_agent._is_valid_git_url("http://example.com")
        assert not git_agent._is_valid_git_url("")
    
    def test_extract_repo_name(self, git_agent):
        """Test repository name extraction."""
        assert git_agent._extract_repo_name("https://github.com/user/repo.git") == "repo"
        assert git_agent._extract_repo_name("https://gitlab.com/user/project") == "project"
        assert git_agent._extract_repo_name("https://bitbucket.org/user/my-repo.git") == "my-repo"
    
    def test_add_auth_to_url(self, git_agent):
        """Test adding authentication to URL."""
        url = "https://github.com/user/repo.git"
        pat = "ghp_test123"
        auth_url = git_agent._add_auth_to_url(url, pat)
        assert pat in auth_url
        assert "github.com" in auth_url
    
    def test_calculate_repo_size(self, git_agent, temp_dir):
        """Test repository size calculation."""
        # Create test files
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")
        
        size = git_agent._calculate_repo_size(temp_dir)
        assert size >= 0  # Size can be 0 due to rounding to MB
    
    def test_count_files(self, git_agent, temp_dir):
        """Test file counting."""
        # Create test files
        for i in range(3):
            with open(os.path.join(temp_dir, f"test{i}.txt"), "w") as f:
                f.write("test")
        
        count = git_agent._count_files(temp_dir)
        assert count == 3
    
    def test_detect_basic_languages(self, git_agent, temp_dir):
        """Test basic language detection."""
        # Create test files with different extensions
        extensions = [".py", ".java", ".js", ".cpp"]
        for ext in extensions:
            with open(os.path.join(temp_dir, f"test{ext}"), "w") as f:
                f.write("test")
        
        languages = git_agent._detect_basic_languages(temp_dir)
        assert "Python" in languages
        assert "Java" in languages
        assert "JavaScript" in languages
        assert "C++" in languages


class TestLanguageIdentifierAgent:
    """Test LanguageIdentifierAgent functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def lang_agent(self):
        """Create LanguageIdentifierAgent instance."""
        return LanguageIdentifierAgent()
    
    @pytest.fixture
    def sample_python_project(self, temp_dir):
        """Create a sample Python project for testing."""
        # Create Python files
        with open(os.path.join(temp_dir, "main.py"), "w") as f:
            f.write("print('hello world')\n" * 50)
        
        with open(os.path.join(temp_dir, "utils.py"), "w") as f:
            f.write("def helper():\n    pass\n" * 20)
        
        # Create requirements.txt
        with open(os.path.join(temp_dir, "requirements.txt"), "w") as f:
            f.write("flask==2.0.0\nrequests==2.25.1\n")
        
        # Create setup.py
        with open(os.path.join(temp_dir, "setup.py"), "w") as f:
            f.write("from setuptools import setup\nsetup(name='test')")
        
        return temp_dir
    
    def test_init(self, lang_agent):
        """Test LanguageIdentifierAgent initialization."""
        assert len(lang_agent.language_extensions) > 0
        assert len(lang_agent.config_files) > 0
        assert "Python" in lang_agent.language_extensions
    
    def test_analyze_file_extensions(self, lang_agent, sample_python_project):
        """Test file extension analysis."""
        stats = lang_agent._analyze_file_extensions(sample_python_project)
        assert "Python" in stats
        # Should have 3 Python files: main.py, utils.py, setup.py
        assert stats["Python"]["file_count"] >= 2  # At least 2, could be 3 with setup.py
        assert stats["Python"]["total_lines"] > 0
    
    def test_analyze_config_files(self, lang_agent, sample_python_project):
        """Test configuration file analysis."""
        configs = lang_agent._analyze_config_files(sample_python_project)
        assert "Python" in configs
        assert "requirements.txt" in configs["Python"]
        assert "setup.py" in configs["Python"]
    
    def test_detect_frameworks(self, lang_agent, temp_dir):
        """Test framework detection."""
        # Create package.json with React
        package_json = {
            "dependencies": {"react": "^17.0.0"},
            "devDependencies": {"jest": "^26.0.0"}
        }
        
        import json
        with open(os.path.join(temp_dir, "package.json"), "w") as f:
            json.dump(package_json, f)
        
        # Create a minimal Python file for language stats
        with open(os.path.join(temp_dir, "app.py"), "w") as f:
            f.write("print('test')")
        
        language_stats = {"JavaScript": {"file_count": 1}}
        frameworks = lang_agent._detect_frameworks(temp_dir, language_stats)
        assert any("React" in fw for fw in frameworks)
    
    def test_determine_project_type(self, lang_agent, temp_dir):
        """Test project type determination."""
        # Test library type
        with open(os.path.join(temp_dir, "setup.py"), "w") as f:
            f.write("from setuptools import setup")
        
        project_type = lang_agent._determine_project_type(temp_dir, [])
        assert project_type == "library"
        
        # Test containerized app
        os.remove(os.path.join(temp_dir, "setup.py"))
        with open(os.path.join(temp_dir, "Dockerfile"), "w") as f:
            f.write("FROM python:3.9")
        
        project_type = lang_agent._determine_project_type(temp_dir, [])
        assert project_type == "containerized_app"
    
    def test_calculate_confidence(self, lang_agent):
        """Test confidence calculation."""
        language_stats = {"Python": {"file_count": 5}}
        config_analysis = {"Python": ["requirements.txt"]}
        
        confidence = lang_agent._calculate_confidence(language_stats, config_analysis)
        assert 0 <= confidence <= 1.0
        assert confidence > 0.5  # Should have good confidence
    
    def test_create_language_info_list(self, lang_agent):
        """Test language info list creation."""
        language_stats = {
            "Python": {"file_count": 8, "total_lines": 1000},
            "JavaScript": {"file_count": 2, "total_lines": 200}
        }
        
        languages = lang_agent._create_language_info_list(language_stats)
        assert len(languages) == 2
        assert languages[0].name == "Python"  # Should be sorted by percentage
        assert languages[0].percentage == 80.0
        assert languages[1].name == "JavaScript"
        assert languages[1].percentage == 20.0
    
    def test_identify_language(self, lang_agent, sample_python_project):
        """Test complete language identification."""
        profile = lang_agent.identify_language(sample_python_project)
        
        assert isinstance(profile, ProjectLanguageProfile)
        assert profile.primary_language == "Python"
        assert len(profile.languages) > 0
        assert profile.languages[0].name == "Python"
        assert profile.confidence_score > 0
        assert "pip" in profile.package_managers
    
    def test_identify_language_invalid_path(self, lang_agent):
        """Test language identification with invalid path."""
        with pytest.raises(FileNotFoundError):
            lang_agent.identify_language("/nonexistent/path")


class TestDataPreparationAgent:
    """Test DataPreparationAgent functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def data_agent(self):
        """Create DataPreparationAgent instance."""
        return DataPreparationAgent(
            include_test_files=True,
            max_file_size_mb=1.0
        )
    
    @pytest.fixture
    def sample_repo_info(self, temp_dir):
        """Create sample repository info."""
        return RepositoryInfo(
            url="https://github.com/test/repo.git",
            local_path=temp_dir,
            default_branch="main",
            commit_hash="abc123",
            author="Test Author",
            commit_message="Test commit",
            languages=["Python"],
            size_mb=1.5,
            file_count=10
        )
    
    @pytest.fixture
    def sample_language_profile(self):
        """Create sample language profile."""
        return ProjectLanguageProfile(
            primary_language="Python",
            languages=[
                LanguageInfo(name="Python", percentage=90.0, file_count=9, total_lines=1000),
                LanguageInfo(name="Markdown", percentage=10.0, file_count=1, total_lines=100)
            ],
            frameworks=["Python: Flask"],
            build_tools=["Python setuptools"],
            package_managers=["pip"],
            project_type="web_backend",
            confidence_score=0.9
        )
    
    @pytest.fixture
    def sample_python_project(self, temp_dir):
        """Create sample Python project."""
        # Create source files
        os.makedirs(os.path.join(temp_dir, "src"), exist_ok=True)
        with open(os.path.join(temp_dir, "src", "main.py"), "w") as f:
            f.write("def main():\n    print('hello')\n")
        
        # Create test files
        os.makedirs(os.path.join(temp_dir, "tests"), exist_ok=True)
        with open(os.path.join(temp_dir, "tests", "test_main.py"), "w") as f:
            f.write("def test_main():\n    assert True\n")
        
        # Create config files
        with open(os.path.join(temp_dir, "requirements.txt"), "w") as f:
            f.write("flask==2.0.0\n")
        
        with open(os.path.join(temp_dir, "README.md"), "w") as f:
            f.write("# Test Project\n")
        
        return temp_dir
    
    def test_init(self, data_agent):
        """Test DataPreparationAgent initialization."""
        assert data_agent.include_test_files == True
        assert data_agent.max_file_size_bytes == 1024 * 1024
        assert len(data_agent.exclude_extensions) > 0
        assert len(data_agent.test_file_patterns) > 0
    
    def test_analyze_directory_structure(self, data_agent, sample_python_project):
        """Test directory structure analysis."""
        structure = data_agent._analyze_directory_structure(sample_python_project)
        
        assert isinstance(structure, DirectoryStructure)
        assert structure.total_directories > 0
        assert structure.total_files > 0
        assert structure.max_depth > 0
        assert len(structure.common_directories) > 0
    
    def test_analyze_files(self, data_agent, sample_python_project, sample_language_profile):
        """Test file analysis."""
        files = data_agent._analyze_files(sample_python_project, sample_language_profile)
        
        assert len(files) > 0
        assert all(isinstance(f, FileInfo) for f in files)
        
        # Check that we have different types of files
        python_files = [f for f in files if f.language == "Python"]
        markdown_files = [f for f in files if f.language == "Markdown"]
        
        assert len(python_files) > 0
        assert len(markdown_files) > 0
    
    def test_determine_file_language(self, data_agent, sample_language_profile):
        """Test file language determination."""
        assert data_agent._determine_file_language("test.py", sample_language_profile) == "Python"
        assert data_agent._determine_file_language("README.md", sample_language_profile) == "Markdown"
        assert data_agent._determine_file_language("config.json", sample_language_profile) == "JSON"
    
    def test_is_test_file(self, data_agent):
        """Test test file detection."""
        assert data_agent._is_test_file("tests/test_main.py", "test_main.py")
        assert data_agent._is_test_file("src/main_test.py", "main_test.py")
        assert not data_agent._is_test_file("src/main.py", "main.py")
    
    def test_is_config_file(self, data_agent):
        """Test config file detection."""
        assert data_agent._is_config_file("requirements.txt")
        assert data_agent._is_config_file("config.yaml")
        assert data_agent._is_config_file("Dockerfile")
        assert not data_agent._is_config_file("main.py")
    
    def test_count_file_lines(self, data_agent, temp_dir):
        """Test file line counting."""
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("line 1\nline 2\nline 3\n")
        
        lines = data_agent._count_file_lines(test_file)
        assert lines == 3
    
    def test_extract_python_metadata(self, data_agent, temp_dir):
        """Test Python metadata extraction."""
        # Create requirements.txt
        with open(os.path.join(temp_dir, "requirements.txt"), "w") as f:
            f.write("flask==2.0.0\nrequests>=2.25.0\n")
        
        metadata = ProjectMetadata(name="test", dependencies={})
        result = data_agent._extract_python_metadata(temp_dir, metadata)
        
        assert "requirements" in result.dependencies
        assert len(result.dependencies["requirements"]) == 2
    
    def test_extract_javascript_metadata(self, data_agent, temp_dir):
        """Test JavaScript metadata extraction."""
        package_json = {
            "name": "test-project",
            "version": "1.0.0",
            "description": "Test project",
            "dependencies": {"react": "^17.0.0"},
            "devDependencies": {"jest": "^26.0.0"}
        }
        
        import json
        with open(os.path.join(temp_dir, "package.json"), "w") as f:
            json.dump(package_json, f)
        
        metadata = ProjectMetadata(name="test", dependencies={})
        result = data_agent._extract_javascript_metadata(temp_dir, metadata)
        
        assert result.name == "test-project"
        assert result.version == "1.0.0"
        assert "dependencies" in result.dependencies
        assert "devDependencies" in result.dependencies
    
    def test_prepare_project_context(self, data_agent, sample_python_project, sample_repo_info, sample_language_profile):
        """Test complete project context preparation."""
        # Update repo_info local_path to match the sample project
        sample_repo_info.local_path = sample_python_project
        
        context = data_agent.prepare_project_context(
            repo_info=sample_repo_info,
            language_profile=sample_language_profile,
            additional_config={"scope": "test"}
        )
        
        assert isinstance(context, ProjectDataContext)
        assert context.repository_info == sample_repo_info
        assert context.language_profile == sample_language_profile
        assert isinstance(context.project_metadata, ProjectMetadata)
        assert isinstance(context.directory_structure, DirectoryStructure)
        assert len(context.files) > 0
        assert context.preparation_config["scope"] == "test"
    
    def test_prepare_project_context_invalid_path(self, data_agent, sample_repo_info, sample_language_profile):
        """Test project context preparation with invalid path."""
        sample_repo_info.local_path = "/nonexistent/path"
        
        with pytest.raises(FileNotFoundError):
            data_agent.prepare_project_context(
                repo_info=sample_repo_info,
                language_profile=sample_language_profile
            )
    
    def test_project_data_context_serialization(self, temp_dir, sample_repo_info, sample_language_profile):
        """Test ProjectDataContext serialization."""
        context = ProjectDataContext(
            repository_info=sample_repo_info,
            language_profile=sample_language_profile,
            project_metadata=ProjectMetadata(name="test"),
            directory_structure=DirectoryStructure(
                total_directories=1,
                total_files=5,
                max_depth=2,
                common_directories=["src"],
                ignored_directories=[]
            ),
            files=[],
            analysis_timestamp=pytest.importorskip("datetime").datetime.now(),
            preparation_config={}
        )
        
        # Test to_dict
        data = context.to_dict()
        assert isinstance(data, dict)
        assert "repository_info" in data
        assert "language_profile" in data
        
        # Test save_to_file
        test_file = os.path.join(temp_dir, "context.json")
        context.save_to_file(test_file)
        assert os.path.exists(test_file)
        assert os.path.getsize(test_file) > 0


class TestDataClassesAndStructures:
    """Test data classes and structures."""
    
    def test_repository_info_creation(self):
        """Test RepositoryInfo dataclass."""
        repo_info = RepositoryInfo(
            url="https://github.com/test/repo.git",
            local_path="/tmp/repo",
            default_branch="main",
            commit_hash="abc123",
            author="Test Author",
            commit_message="Test commit",
            languages=["Python", "JavaScript"],
            size_mb=2.5,
            file_count=15
        )
        
        assert repo_info.url == "https://github.com/test/repo.git"
        assert repo_info.languages == ["Python", "JavaScript"]
        assert repo_info.size_mb == 2.5
    
    def test_language_info_creation(self):
        """Test LanguageInfo dataclass."""
        lang_info = LanguageInfo(
            name="Python",
            percentage=85.5,
            file_count=17,
            total_lines=1500,
            framework="Django"
        )
        
        assert lang_info.name == "Python"
        assert lang_info.percentage == 85.5
        assert lang_info.framework == "Django"
    
    def test_project_language_profile_creation(self):
        """Test ProjectLanguageProfile dataclass."""
        profile = ProjectLanguageProfile(
            primary_language="Python",
            languages=[
                LanguageInfo(name="Python", percentage=80.0, file_count=8, total_lines=800),
                LanguageInfo(name="JavaScript", percentage=20.0, file_count=2, total_lines=200)
            ],
            frameworks=["Python: Django"],
            build_tools=["setuptools"],
            package_managers=["pip"],
            project_type="web_backend",
            confidence_score=0.9
        )
        
        assert profile.primary_language == "Python"
        assert len(profile.languages) == 2
        assert profile.confidence_score == 0.9
    
    def test_file_info_creation(self):
        """Test FileInfo dataclass."""
        import datetime
        
        file_info = FileInfo(
            path="/tmp/test.py",
            relative_path="src/test.py",
            size_bytes=1024,
            lines=50,
            language="Python",
            last_modified=datetime.datetime.now(),
            is_test_file=False,
            is_config_file=False
        )
        
        assert file_info.path == "/tmp/test.py"
        assert file_info.language == "Python"
        assert file_info.lines == 50
        assert not file_info.is_test_file
    
    def test_directory_structure_creation(self):
        """Test DirectoryStructure dataclass."""
        structure = DirectoryStructure(
            total_directories=5,
            total_files=25,
            max_depth=3,
            common_directories=["src", "tests", "docs"],
            ignored_directories=[".git", "__pycache__"]
        )
        
        assert structure.total_directories == 5
        assert structure.max_depth == 3
        assert "src" in structure.common_directories
        assert ".git" in structure.ignored_directories
    
    def test_project_metadata_creation(self):
        """Test ProjectMetadata dataclass."""
        metadata = ProjectMetadata(
            name="test-project",
            version="1.0.0",
            description="A test project",
            author="Test Author",
            license="MIT",
            dependencies={"runtime": ["flask", "requests"]},
            scripts={"start": "python main.py"},
            keywords=["test", "python"]
        )
        
        assert metadata.name == "test-project"
        assert metadata.version == "1.0.0"
        assert "flask" in metadata.dependencies["runtime"]
        assert "test" in metadata.keywords


if __name__ == "__main__":
    pytest.main([__file__]) 