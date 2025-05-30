#!/usr/bin/env python3
"""Test script to verify dependencies are installed correctly in container."""

import sys

def test_imports():
    """Test importing all required dependencies."""
    deps = [
        'click',
        'streamlit', 
        'gitpython',
        'neo4j',
        'openai',
        'pydantic',
        'loguru',
        'langgraph',
        'langchain'
    ]
    
    failed = []
    for dep in deps:
        try:
            __import__(dep)
            print(f"✅ {dep} - OK")
        except ImportError as e:
            print(f"❌ {dep} - FAILED: {e}")
            failed.append(dep)
    
    if failed:
        print(f"\nFailed imports: {failed}")
        sys.exit(1)
    else:
        print("\n🎉 All dependencies imported successfully!")

if __name__ == "__main__":
    test_imports() 