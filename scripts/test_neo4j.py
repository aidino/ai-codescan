#!/usr/bin/env python3
"""
Test Neo4j Connection Script

This script tests the connection to Neo4j database.
Usage: poetry run python scripts/test_neo4j.py
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    from neo4j import GraphDatabase
    import logging
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    def test_neo4j_connection():
        """Test Neo4j connection."""
        
        # Configuration from environment or defaults
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "ai_codescan_password")
        
        logger.info(f"Testing connection to Neo4j at {uri}")
        
        try:
            # Create driver
            driver = GraphDatabase.driver(uri, auth=(user, password))
            
            # Test connection
            with driver.session() as session:
                # Simple query to test connection
                result = session.run("RETURN 'Connection successful' as message, datetime() as timestamp")
                record = result.single()
                
                if record:
                    logger.info(f"✅ {record['message']} at {record['timestamp']}")
                    
                    # Test database info
                    result = session.run("CALL db.info()")
                    db_info = result.single()
                    if db_info:
                        logger.info(f"Database: {db_info.get('name', 'N/A')}")
                    
                    return True
                else:
                    logger.error("❌ No response from Neo4j")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
        finally:
            if 'driver' in locals():
                driver.close()
    
    if __name__ == "__main__":
        print("🧪 Testing Neo4j Connection")
        print("==========================")
        
        success = test_neo4j_connection()
        
        if success:
            print("\n✅ Neo4j connection test passed!")
            sys.exit(0)
        else:
            print("\n❌ Neo4j connection test failed!")
            print("Make sure Neo4j is running and credentials are correct.")
            print("Run: docker-compose up neo4j -d")
            sys.exit(1)
            
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you have installed dependencies: poetry install")
    sys.exit(1) 