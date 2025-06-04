#!/usr/bin/env python3
"""
Simple Neo4j Connection Test
Quick test để check Neo4j connection trong setup process.
"""

import sys
import os
from pathlib import Path

# Add src to path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root / "src"))

def test_neo4j_connection():
    """Test basic Neo4j connection."""
    try:
        from neo4j import GraphDatabase
        
        # Default Neo4j credentials from docker-compose
        uri = "bolt://localhost:7687"
        username = "neo4j"
        password = "ai_codescan_password"
        
        print("🔌 Connecting to Neo4j...")
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        # Test connection with a simple query
        with driver.session() as session:
            result = session.run("RETURN 'AI CodeScan Connected' AS message")
            record = result.single()
            if record:
                print(f"✅ Neo4j Connection: {record['message']}")
                return True
            
    except Exception as e:
        print(f"❌ Neo4j Connection Failed: {str(e)}")
        print("💡 Make sure Docker containers are running: docker compose ps")
        return False
    
    finally:
        try:
            driver.close()
        except:
            pass
    
    return False

def test_redis_connection():
    """Test basic Redis connection."""
    try:
        import redis
        
        # Default Redis settings from docker-compose
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        print("🔌 Connecting to Redis...")
        r.ping()
        r.set('ai_codescan_test', 'connected')
        value = r.get('ai_codescan_test')
        
        if value == 'connected':
            print("✅ Redis Connection: OK")
            r.delete('ai_codescan_test')
            return True
            
    except Exception as e:
        print(f"❌ Redis Connection Failed: {str(e)}")
        return False
    
    return False

def main():
    """Main test function."""
    print("🧪 AI CodeScan - Quick System Test")
    print("==================================")
    
    # Test Neo4j
    neo4j_ok = test_neo4j_connection()
    
    # Test Redis  
    redis_ok = test_redis_connection()
    
    print("\n📊 Test Results:")
    print(f"   Neo4j: {'✅ OK' if neo4j_ok else '❌ FAILED'}")
    print(f"   Redis: {'✅ OK' if redis_ok else '❌ FAILED'}")
    
    if neo4j_ok and redis_ok:
        print("\n🎉 All systems ready!")
        return 0
    else:
        print("\n⚠️  Some services are not ready. Check Docker containers.")
        return 1

if __name__ == "__main__":
    exit(main()) 