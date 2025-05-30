#!/usr/bin/env python3
"""
AI CodeScan - Neo4j CKG Setup Script

Script cấu hình Neo4j database cho Code Knowledge Graph.
Tạo constraints, indexes và thiết lập cấu hình cần thiết.
"""

import sys
import os
from pathlib import Path
from loguru import logger

# Add src to path để import modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from neo4j import GraphDatabase
except ImportError:
    logger.error("Neo4j driver not installed. Please install with: pip install neo4j")
    sys.exit(1)

from agents.ckg_operations import CKGQueryInterfaceAgent, ConnectionConfig


class Neo4jCKGSetup:
    """Setup Neo4j database cho CKG."""
    
    def __init__(self, connection_config: ConnectionConfig):
        """
        Khởi tạo setup.
        
        Args:
            connection_config: Cấu hình kết nối Neo4j
        """
        self.config = connection_config
        self.driver = None
    
    def connect(self):
        """Kết nối đến Neo4j."""
        try:
            self.driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.username, self.config.password)
            )
            
            # Test connection
            with self.driver.session(database=self.config.database) as session:
                session.run("RETURN 1")
            
            logger.info(f"Kết nối Neo4j thành công: {self.config.uri}")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi kết nối Neo4j: {str(e)}")
            return False
    
    def close(self):
        """Đóng kết nối."""
        if self.driver:
            self.driver.close()
    
    def setup_database(self):
        """Thiết lập database với constraints và indexes."""
        if not self.driver:
            logger.error("Không có kết nối Neo4j")
            return False
        
        try:
            with self.driver.session(database=self.config.database) as session:
                # Drop existing constraints and indexes (if any)
                logger.info("Xóa constraints và indexes cũ...")
                self._drop_existing_constraints_indexes(session)
                
                # Create constraints
                logger.info("Tạo constraints...")
                self._create_constraints(session)
                
                # Create indexes
                logger.info("Tạo indexes...")
                self._create_indexes(session)
                
                # Create any initial data if needed
                logger.info("Tạo dữ liệu khởi tạo...")
                self._create_initial_data(session)
                
                logger.info("Thiết lập database hoàn tất!")
                return True
                
        except Exception as e:
            logger.error(f"Lỗi thiết lập database: {str(e)}")
            return False
    
    def _drop_existing_constraints_indexes(self, session):
        """Xóa constraints và indexes hiện có."""
        
        # Drop constraints
        constraints_to_drop = [
            "DROP CONSTRAINT file_id_unique IF EXISTS",
            "DROP CONSTRAINT module_id_unique IF EXISTS", 
            "DROP CONSTRAINT class_id_unique IF EXISTS",
            "DROP CONSTRAINT function_id_unique IF EXISTS",
            "DROP CONSTRAINT method_id_unique IF EXISTS",
            "DROP CONSTRAINT parameter_id_unique IF EXISTS",
            "DROP CONSTRAINT import_id_unique IF EXISTS",
            "DROP CONSTRAINT decorator_id_unique IF EXISTS",
            "DROP CONSTRAINT variable_id_unique IF EXISTS"
        ]
        
        for constraint in constraints_to_drop:
            try:
                session.run(constraint)
            except Exception:
                pass  # Constraint might not exist
        
        # Drop indexes
        indexes_to_drop = [
            "DROP INDEX file_path_index IF EXISTS",
            "DROP INDEX file_name_index IF EXISTS",
            "DROP INDEX class_name_index IF EXISTS", 
            "DROP INDEX function_name_index IF EXISTS",
            "DROP INDEX method_name_index IF EXISTS",
            "DROP INDEX import_name_index IF EXISTS",
            "DROP INDEX line_number_index IF EXISTS"
        ]
        
        for index in indexes_to_drop:
            try:
                session.run(index)
            except Exception:
                pass  # Index might not exist
    
    def _create_constraints(self, session):
        """Tạo uniqueness constraints."""
        
        constraints = [
            # Node ID uniqueness constraints
            "CREATE CONSTRAINT file_id_unique FOR (f:File) REQUIRE f.id IS UNIQUE",
            "CREATE CONSTRAINT module_id_unique FOR (m:Module) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT class_id_unique FOR (c:Class) REQUIRE c.id IS UNIQUE", 
            "CREATE CONSTRAINT function_id_unique FOR (f:Function) REQUIRE f.id IS UNIQUE",
            "CREATE CONSTRAINT method_id_unique FOR (m:Method) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT parameter_id_unique FOR (p:Parameter) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT import_id_unique FOR (i:Import) REQUIRE i.id IS UNIQUE",
            "CREATE CONSTRAINT decorator_id_unique FOR (d:Decorator) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT variable_id_unique FOR (v:Variable) REQUIRE v.id IS UNIQUE"
        ]
        
        for constraint in constraints:
            try:
                session.run(constraint)
                logger.debug(f"Created constraint: {constraint}")
            except Exception as e:
                logger.warning(f"Failed to create constraint: {str(e)}")
    
    def _create_indexes(self, session):
        """Tạo performance indexes."""
        
        indexes = [
            # File path indexes for fast lookup
            "CREATE INDEX file_path_index FOR (f:File) ON (f.file_path)",
            "CREATE INDEX file_name_index FOR (f:File) ON (f.name)",
            
            # Name indexes for searching
            "CREATE INDEX class_name_index FOR (c:Class) ON (c.name)",
            "CREATE INDEX function_name_index FOR (f:Function) ON (f.name)", 
            "CREATE INDEX method_name_index FOR (m:Method) ON (m.name)",
            "CREATE INDEX import_name_index FOR (i:Import) ON (i.name)",
            
            # Line number index for navigation
            "CREATE INDEX line_number_index FOR (n) ON (n.line_number)",
            
            # Composite indexes for common queries
            "CREATE INDEX file_type_index FOR (n) ON (n.file_path, n.type)",
            "CREATE INDEX name_type_index FOR (n) ON (n.name, n.type)"
        ]
        
        for index in indexes:
            try:
                session.run(index)
                logger.debug(f"Created index: {index}")
            except Exception as e:
                logger.warning(f"Failed to create index: {str(e)}")
    
    def _create_initial_data(self, session):
        """Tạo dữ liệu khởi tạo nếu cần."""
        
        # Create metadata node for CKG info
        metadata_query = """
        MERGE (meta:CKGMetadata {id: 'main'})
        SET meta.version = '1.0',
            meta.created_at = datetime(),
            meta.schema_version = '1.0',
            meta.last_updated = datetime()
        RETURN meta
        """
        
        try:
            result = session.run(metadata_query)
            logger.debug("Created CKG metadata node")
        except Exception as e:
            logger.warning(f"Failed to create metadata: {str(e)}")
    
    def verify_setup(self):
        """Kiểm tra thiết lập database."""
        if not self.driver:
            logger.error("Không có kết nối Neo4j")
            return False
        
        try:
            with self.driver.session(database=self.config.database) as session:
                # Check constraints
                logger.info("Kiểm tra constraints...")
                constraints_result = session.run("SHOW CONSTRAINTS")
                constraints_count = len(list(constraints_result))
                logger.info(f"Tìm thấy {constraints_count} constraints")
                
                # Check indexes
                logger.info("Kiểm tra indexes...")
                indexes_result = session.run("SHOW INDEXES")
                indexes_count = len(list(indexes_result))
                logger.info(f"Tìm thấy {indexes_count} indexes")
                
                # Check metadata
                logger.info("Kiểm tra metadata...")
                metadata_result = session.run("MATCH (meta:CKGMetadata) RETURN meta")
                metadata_exists = len(list(metadata_result)) > 0
                logger.info(f"Metadata node exists: {metadata_exists}")
                
                logger.info("✅ Database setup verification completed!")
                return True
                
        except Exception as e:
            logger.error(f"Lỗi kiểm tra setup: {str(e)}")
            return False
    
    def clear_database(self):
        """Xóa tất cả dữ liệu trong database (cẩn thận!)."""
        if not self.driver:
            logger.error("Không có kết nối Neo4j")
            return False
        
        logger.warning("⚠️  CẢNH BÁO: Sẽ xóa TẤT CẢ dữ liệu trong database!")
        
        try:
            with self.driver.session(database=self.config.database) as session:
                # Delete all nodes and relationships
                session.run("MATCH (n) DETACH DELETE n")
                logger.info("Đã xóa tất cả nodes và relationships")
                
                return True
                
        except Exception as e:
            logger.error(f"Lỗi xóa database: {str(e)}")
            return False


def main():
    """Main function."""
    logger.info("🚀 Bắt đầu thiết lập Neo4j CKG...")
    
    # Cấu hình kết nối từ environment variables hoặc default
    config = ConnectionConfig(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        username=os.getenv("NEO4J_USERNAME", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "ai_codescan_password"),
        database=os.getenv("NEO4J_DATABASE", "ai-codescan")
    )
    
    setup = Neo4jCKGSetup(config)
    
    try:
        # Kết nối
        if not setup.connect():
            logger.error("❌ Không thể kết nối Neo4j")
            return False
        
        # Parse command line arguments
        import argparse
        parser = argparse.ArgumentParser(description="Setup Neo4j CKG Database")
        parser.add_argument("--clear", action="store_true", help="Clear all data before setup")
        parser.add_argument("--verify-only", action="store_true", help="Only verify existing setup")
        args = parser.parse_args()
        
        if args.verify_only:
            # Chỉ kiểm tra
            logger.info("🔍 Chỉ kiểm tra setup hiện tại...")
            success = setup.verify_setup()
        else:
            # Clear database nếu được yêu cầu
            if args.clear:
                logger.info("🗑️  Xóa database...")
                setup.clear_database()
            
            # Thiết lập database
            logger.info("🔧 Thiết lập database...")
            success = setup.setup_database()
            
            if success:
                # Kiểm tra setup
                logger.info("🔍 Kiểm tra setup...")
                success = setup.verify_setup()
        
        if success:
            logger.info("✅ Thiết lập Neo4j CKG hoàn tất!")
            return True
        else:
            logger.error("❌ Thiết lập thất bại!")
            return False
            
    finally:
        setup.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 