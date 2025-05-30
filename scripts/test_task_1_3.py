#!/usr/bin/env python3
"""
Test script for Task 1.3: TEAM Data Acquisition Implementation.

Tests GitOperationsAgent, LanguageIdentifierAgent, and DataPreparationAgent
with a real repository to ensure everything works end-to-end.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.data_acquisition import (
    GitOperationsAgent,
    LanguageIdentifierAgent, 
    DataPreparationAgent,
    RepositoryInfo,
    ProjectLanguageProfile,
    ProjectDataContext
)
from loguru import logger

# Global variables to maintain temp directory across tests
temp_dir = None
repo_info = None

def test_git_operations():
    """Test GitOperationsAgent with a real repository."""
    global temp_dir, repo_info
    logger.info("=== Testing GitOperationsAgent ===")
    
    # Use a small, well-known Python repository
    test_repo_url = "https://github.com/psf/requests.git"
    
    # Create persistent temp directory
    temp_dir = tempfile.mkdtemp()
    git_agent = GitOperationsAgent(temp_dir=temp_dir)
    
    try:
        # Test repository cloning
        logger.info(f"Cloning repository: {test_repo_url}")
        repo_info = git_agent.clone_repository(
            repo_url=test_repo_url,
            depth=1  # Shallow clone for faster testing
        )
        
        logger.success(f"Repository cloned successfully:")
        logger.info(f"  - URL: {repo_info.url}")
        logger.info(f"  - Local path: {repo_info.local_path}")
        logger.info(f"  - Default branch: {repo_info.default_branch}")
        logger.info(f"  - Commit hash: {repo_info.commit_hash}")
        logger.info(f"  - Author: {repo_info.author}")
        logger.info(f"  - Languages detected: {repo_info.languages}")
        logger.info(f"  - Size: {repo_info.size_mb} MB")
        logger.info(f"  - File count: {repo_info.file_count}")
        
        # Verify the repository was actually cloned
        assert os.path.exists(repo_info.local_path), "Repository path should exist"
        assert os.path.exists(os.path.join(repo_info.local_path, ".git")), "Should have .git directory"
        
        # Test get_repository_info
        logger.info("Testing get_repository_info...")
        repo_info_2 = git_agent.get_repository_info(repo_info.local_path)
        assert repo_info_2.local_path == repo_info.local_path
        
        logger.success("GitOperationsAgent tests passed!")
        return repo_info
        
    except Exception as e:
        logger.error(f"GitOperationsAgent test failed: {e}")
        # Clean up on failure
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise

def test_language_identifier():
    """Test LanguageIdentifierAgent."""
    logger.info("=== Testing LanguageIdentifierAgent ===")
    
    try:
        lang_agent = LanguageIdentifierAgent()
        
        # Test language identification
        logger.info(f"Analyzing languages in: {repo_info.local_path}")
        language_profile = lang_agent.identify_language(repo_info.local_path)
        
        logger.success(f"Language analysis completed:")
        logger.info(f"  - Primary language: {language_profile.primary_language}")
        logger.info(f"  - Languages found: {len(language_profile.languages)}")
        
        for lang in language_profile.languages:
            logger.info(f"    * {lang.name}: {lang.percentage}% ({lang.file_count} files, {lang.total_lines} lines)")
        
        logger.info(f"  - Frameworks: {language_profile.frameworks}")
        logger.info(f"  - Build tools: {language_profile.build_tools}")
        logger.info(f"  - Package managers: {language_profile.package_managers}")
        logger.info(f"  - Project type: {language_profile.project_type}")
        logger.info(f"  - Confidence score: {language_profile.confidence_score}")
        
        assert language_profile.primary_language != "Unknown", "Should detect primary language"
        assert len(language_profile.languages) > 0, "Should detect at least one language"
        assert language_profile.confidence_score > 0, "Should have positive confidence"
        
        logger.success("LanguageIdentifierAgent tests passed!")
        return language_profile
        
    except Exception as e:
        logger.error(f"LanguageIdentifierAgent test failed: {e}")
        raise

def test_data_preparation(language_profile: ProjectLanguageProfile):
    """Test DataPreparationAgent."""
    logger.info("=== Testing DataPreparationAgent ===")
    
    try:
        data_agent = DataPreparationAgent(
            include_test_files=True,
            max_file_size_mb=0.5  # Smaller limit for testing
        )
        
        # Test project context preparation
        logger.info(f"Preparing project context for: {repo_info.local_path}")
        project_context = data_agent.prepare_project_context(
            repo_info=repo_info,
            language_profile=language_profile,
            additional_config={'scope': 'test_run'}
        )
        
        logger.success(f"Project context prepared:")
        logger.info(f"  - Project name: {project_context.project_metadata.name}")
        logger.info(f"  - Version: {project_context.project_metadata.version}")
        logger.info(f"  - Description: {project_context.project_metadata.description}")
        logger.info(f"  - Author: {project_context.project_metadata.author}")
        logger.info(f"  - License: {project_context.project_metadata.license}")
        
        logger.info(f"  - Total directories: {project_context.directory_structure.total_directories}")
        logger.info(f"  - Total files: {project_context.directory_structure.total_files}")
        logger.info(f"  - Max depth: {project_context.directory_structure.max_depth}")
        logger.info(f"  - Files analyzed: {len(project_context.files)}")
        
        # Show some file examples
        logger.info("  - Sample files:")
        for i, file_info in enumerate(project_context.files[:5]):  # First 5 files
            logger.info(f"    {i+1}. {file_info.relative_path} ({file_info.language}, {file_info.lines} lines)")
        
        # Show preparation config
        logger.info(f"  - Preparation config: {project_context.preparation_config}")
        
        # Test serialization
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            project_context.save_to_file(f.name)
            logger.info(f"  - Context saved to: {f.name}")
            
            # Verify file exists and has content
            assert os.path.exists(f.name), "Context file should be created"
            assert os.path.getsize(f.name) > 0, "Context file should have content"
            
            # Clean up
            os.unlink(f.name)
        
        assert project_context.project_metadata.name, "Should have project name"
        assert len(project_context.files) > 0, "Should analyze some files"
        assert project_context.directory_structure.total_files > 0, "Should count files"
        
        logger.success("DataPreparationAgent tests passed!")
        return project_context
        
    except Exception as e:
        logger.error(f"DataPreparationAgent test failed: {e}")
        raise

def test_integration():
    """Test full integration of all Data Acquisition agents."""
    logger.info("=== Testing Full Data Acquisition Integration ===")
    
    try:
        # Step 1: Clone repository
        repo_info_local = test_git_operations()
        
        # Step 2: Identify languages
        language_profile = test_language_identifier()
        
        # Step 3: Prepare project context
        project_context = test_data_preparation(language_profile)
        
        # Verify integration
        assert project_context.repository_info.url == repo_info_local.url
        assert project_context.language_profile.primary_language == language_profile.primary_language
        
        logger.success("🎉 All Data Acquisition Team tests passed!")
        logger.info(f"Successfully processed repository with:")
        logger.info(f"  - {len(project_context.files)} files analyzed")
        logger.info(f"  - {len(language_profile.languages)} languages detected")
        logger.info(f"  - Primary language: {language_profile.primary_language}")
        logger.info(f"  - Project type: {language_profile.project_type}")
        
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        return False
    finally:
        # Clean up temp directory
        if temp_dir and os.path.exists(temp_dir):
            logger.info(f"Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)

def main():
    """Main test function."""
    logger.info("Starting Task 1.3 Data Acquisition Team Tests...")
    
    try:
        success = test_integration()
        
        if success:
            logger.success("✅ Task 1.3 implementation is working correctly!")
            logger.info("All Data Acquisition agents are ready for integration with the orchestrator.")
            return 0
        else:
            logger.error("❌ Task 1.3 tests failed!")
            return 1
            
    except KeyboardInterrupt:
        logger.warning("Tests interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 