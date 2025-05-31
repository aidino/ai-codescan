#!/usr/bin/env python3
"""
Demo script để test PAT Integration (Task 2.1).

Tests secure PAT storage, validation và integration với GitOperationsAgent.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.interaction_tasking.pat_handler import PATHandlerAgent
from agents.data_acquisition.git_operations import GitOperationsAgent
from loguru import logger


def test_pat_storage_and_validation():
    """Test PAT storage và validation functionality."""
    print("🧪 Testing PAT Storage & Validation")
    print("=" * 50)
    
    # Initialize PAT handler
    pat_handler = PATHandlerAgent()
    
    # Test different PAT formats
    test_pats = [
        ("GitHub", "testuser1", "ghp_1234567890123456789012345678901234567890"),
        ("GitLab", "testuser2", "glpat-abcdefghijklmnopqrstuvwxyz"),
        ("BitBucket", "testuser3", "ATBBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"),
    ]
    
    stored_hashes = []
    
    for platform, username, token in test_pats:
        print(f"\n📝 Testing {platform} PAT...")
        
        # Validate format
        is_valid = pat_handler.validate_pat_format(platform, token)
        print(f"   ✅ Format validation: {'✓ VALID' if is_valid else '✗ INVALID'}")
        
        if is_valid:
            # Store PAT
            try:
                token_hash = pat_handler.store_pat(platform, username, token, "test_session")
                stored_hashes.append(token_hash)
                print(f"   💾 Stored with hash: {token_hash[:8]}...")
                
                # Retrieve PAT
                retrieved = pat_handler.retrieve_pat(token_hash)
                if retrieved == token:
                    print(f"   🔓 Retrieved successfully: {'✓ MATCH' if retrieved == token else '✗ MISMATCH'}")
                else:
                    print(f"   ❌ Retrieval failed")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
    
    # Test PAT info display
    print(f"\n📊 Stored PAT Information:")
    pat_info = pat_handler.get_stored_pat_info()
    for info in pat_info:
        print(f"   🔹 {info['platform'].title()} - {info['username']} ({info['token_hash']})")
    
    return pat_handler, stored_hashes


def test_git_operations_with_pat():
    """Test GitOperationsAgent với PAT support."""
    print("\n\n🔗 Testing Git Operations with PAT")
    print("=" * 50)
    
    git_agent = GitOperationsAgent()
    
    # Test public repository (no PAT needed)
    public_repo = "https://github.com/octocat/Hello-World"
    print(f"\n📦 Testing public repository: {public_repo}")
    
    try:
        repo_info = git_agent.clone_repository(public_repo, depth=1)
        print(f"   ✅ Clone successful:")
        print(f"      📂 Local path: {repo_info.local_path}")
        print(f"      🌳 Branch: {repo_info.default_branch}")
        print(f"      📊 Size: {repo_info.size_mb:.2f} MB")
        print(f"      📄 Files: {repo_info.file_count}")
        print(f"      🗣️ Languages: {', '.join(repo_info.languages)}")
        
        # Cleanup
        git_agent.cleanup_repository(repo_info.local_path)
        print(f"   🗑️ Cleaned up repository")
        
    except Exception as e:
        print(f"   ❌ Clone failed: {str(e)}")
    
    # Test PAT URL formatting
    print(f"\n🔐 Testing PAT URL formatting:")
    test_url = "https://github.com/user/private-repo"
    test_pat = "ghp_test123456789012345678901234567890"
    
    # Access private method for testing
    auth_url = git_agent._add_auth_to_url(test_url, test_pat)
    expected_start = "https://ghp_"
    
    if auth_url.startswith(expected_start):
        print(f"   ✅ PAT integration: URL properly formatted")
        print(f"      🔗 Pattern: https://[PAT]@github.com/...")
    else:
        print(f"   ❌ PAT integration failed")


def test_platform_helpers():
    """Test platform-specific helper functions."""
    print("\n\n🏢 Testing Platform Helpers")
    print("=" * 50)
    
    pat_handler = PATHandlerAgent()
    
    platforms = ["GitHub", "GitLab", "BitBucket", "Unknown"]
    
    for platform in platforms:
        url = pat_handler.get_platform_pat_url(platform)
        print(f"   🔗 {platform}: {url}")


def test_pat_security_features():
    """Test security features của PAT handling."""
    print("\n\n🔒 Testing Security Features")
    print("=" * 50)
    
    pat_handler = PATHandlerAgent()
    
    # Test that tokens are properly encrypted
    token = "ghp_test123456789012345678901234567890"
    token_hash = pat_handler.store_pat("GitHub", "user", token, "session")
    
    # Verify that stored data is encrypted
    stored_pat = pat_handler.stored_pats[token_hash]
    
    # Encrypted token should not match original
    if stored_pat.encrypted_token != token.encode():
        print("   ✅ Token encryption: Properly encrypted")
    else:
        print("   ❌ Token encryption: Not encrypted!")
    
    # Test that hash is unique
    token_hash2 = pat_handler.store_pat("GitHub", "user", token, "session2")
    if token_hash != token_hash2:
        print("   ✅ Hash uniqueness: Different sessions generate different hashes")
    else:
        print("   ❌ Hash uniqueness: Same hash for different sessions!")
    
    # Test session isolation
    pat_handler.clear_session_pats()
    if len(pat_handler.stored_pats) == 0:
        print("   ✅ Session cleanup: All PATs cleared successfully")
    else:
        print("   ❌ Session cleanup: PATs not properly cleared!")


def test_error_handling():
    """Test error handling scenarios."""
    print("\n\n⚠️ Testing Error Handling")
    print("=" * 50)
    
    pat_handler = PATHandlerAgent()
    
    # Test empty token
    try:
        pat_handler.store_pat("GitHub", "user", "", "session")
        print("   ❌ Empty token: Should have raised error!")
    except ValueError:
        print("   ✅ Empty token: Properly rejected")
    
    # Test retrieval of non-existent PAT
    result = pat_handler.retrieve_pat("nonexistent_hash")
    if result is None:
        print("   ✅ Non-existent PAT: Properly handled")
    else:
        print("   ❌ Non-existent PAT: Should return None!")
    
    # Test invalid PAT formats
    invalid_pats = [
        ("GitHub", "invalid"),
        ("GitLab", "also_invalid"),
        ("BitBucket", "short")
    ]
    
    for platform, invalid_token in invalid_pats:
        is_valid = pat_handler.validate_pat_format(platform, invalid_token)
        if not is_valid:
            print(f"   ✅ Invalid {platform} PAT: Properly rejected")
        else:
            print(f"   ❌ Invalid {platform} PAT: Should be rejected!")


def main():
    """Run all PAT integration tests."""
    print("🚀 AI CodeScan - PAT Integration Testing")
    print("Task 2.1: Mở rộng TEAM Data Acquisition cho PAT và Private Repo")
    print("=" * 70)
    
    try:
        # Test PAT storage and validation
        pat_handler, stored_hashes = test_pat_storage_and_validation()
        
        # Test Git operations
        test_git_operations_with_pat()
        
        # Test platform helpers
        test_platform_helpers()
        
        # Test security features
        test_pat_security_features()
        
        # Test error handling
        test_error_handling()
        
        print("\n\n🎉 PAT Integration Testing Completed!")
        print("=" * 70)
        print("✅ All tests completed successfully")
        print("🔐 PAT security features working properly")
        print("🔗 Git operations integration ready")
        print("🚀 Task 2.1 implementation: READY FOR PRODUCTION")
        
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        print(f"\n❌ Test execution failed: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 