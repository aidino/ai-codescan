#!/usr/bin/env python3
"""
AI CodeScan Environment Validation Script

Validates that all required environment variables are properly configured.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def check_env_file() -> bool:
    """Check if .env file exists."""
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found")
        print("   Run: cp .env.example .env")
        return False
    
    print("✅ .env file exists")
    return True

def validate_openai_config() -> bool:
    """Validate OpenAI configuration."""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key or api_key == 'your-openai-api-key-here':
        print("❌ OPENAI_API_KEY not configured")
        print("   Get your API key from: https://platform.openai.com/api-keys")
        print("   Set it in .env file: OPENAI_API_KEY=sk-your-key-here")
        return False
    
    if not api_key.startswith('sk-'):
        print("⚠️  OPENAI_API_KEY format might be incorrect (should start with 'sk-')")
        return False
    
    print("✅ OpenAI API key configured")
    return True

def validate_security_keys() -> bool:
    """Validate security keys."""
    secret_key = os.getenv('SECRET_KEY')
    pat_key = os.getenv('PAT_ENCRYPTION_KEY')
    
    issues = []
    
    if not secret_key or secret_key == 'your-secret-key-here-change-in-production':
        issues.append("SECRET_KEY not configured")
    
    if not pat_key or pat_key == 'your-pat-encryption-key-here-change-in-production':
        issues.append("PAT_ENCRYPTION_KEY not configured")
    
    if issues:
        print("⚠️  Security keys need updating:")
        for issue in issues:
            print(f"   - {issue}")
        print("   Generate new keys with: python -c \"import secrets; print(secrets.token_urlsafe(32))\"")
        return False
    
    print("✅ Security keys configured")
    return True

def validate_database_config() -> bool:
    """Validate database configuration."""
    neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_password = os.getenv('NEO4J_PASSWORD', 'ai_codescan_password')
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    
    print("✅ Database configuration:")
    print(f"   Neo4j: {neo4j_uri}")
    print(f"   Redis: {redis_host}:{os.getenv('REDIS_PORT', '6379')}")
    
    return True

def validate_performance_config() -> bool:
    """Validate performance configuration."""
    max_size = int(os.getenv('MAX_REPOSITORY_SIZE_MB', '500'))
    clone_timeout = int(os.getenv('CLONE_TIMEOUT_SECONDS', '300'))
    analysis_timeout = int(os.getenv('ANALYSIS_TIMEOUT_SECONDS', '1800'))
    
    print("✅ Performance limits configured:")
    print(f"   Max repository size: {max_size} MB")
    print(f"   Clone timeout: {clone_timeout} seconds")
    print(f"   Analysis timeout: {analysis_timeout} seconds")
    
    return True

def main():
    """Main validation function."""
    print("🤖 AI CodeScan Environment Validation")
    print("=" * 50)
    
    # Load .env file if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("ℹ️  python-dotenv not installed, reading from system environment")
    
    checks = [
        ("Environment File", check_env_file),
        ("OpenAI Configuration", validate_openai_config),
        ("Security Keys", validate_security_keys), 
        ("Database Configuration", validate_database_config),
        ("Performance Configuration", validate_performance_config)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"\n📋 {name}")
        if check_func():
            passed += 1
    
    print(f"\n{'=' * 50}")
    if passed == total:
        print("🎉 All checks passed! Environment is properly configured.")
        print("\n🚀 You can now run: docker-compose up --build")
        sys.exit(0)
    else:
        print(f"❌ {total - passed} issue(s) found. Please fix the above issues.")
        print("\n📖 See README.md Environment Configuration section for help.")
        sys.exit(1)

if __name__ == "__main__":
    main() 