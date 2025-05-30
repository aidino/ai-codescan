#!/usr/bin/env python3
"""
AI CodeScan - CKG Query Interface Agent

Agent cung cấp giao diện truy vấn Code Knowledge Graph.
Cung cấp API chuẩn hóa để truy vấn thông tin từ CKG mà không cần biết chi tiết Neo4j.
"""

import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from loguru import logger
import json

try:
    from neo4j import GraphDatabase
except ImportError:
    logger.warning("Neo4j driver not installed. Some features will be limited.")
    GraphDatabase = None

from .ckg_schema import NodeType, RelationshipType, CKGSchema


@dataclass
class CKGQueryResult:
    """Kết quả truy vấn CKG."""
    query: str
    results: List[Dict[str, Any]]
    total_count: int
    execution_time_ms: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class ConnectionConfig:
    """Cấu hình kết nối Neo4j."""
    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = "ai_codescan_password"
    database: str = "ai-codescan"


class CKGQueryInterfaceAgent:
    """
    Agent cung cấp giao diện truy vấn CKG.
    
    Trách nhiệm:
    - Cung cấp API truy vấn CKG chuẩn hóa
    - Quản lý kết nối Neo4j
    - Tối ưu hóa performance với caching
    - Đảm bảo security và validation
    """
    
    def __init__(self, connection_config: Optional[ConnectionConfig] = None):
        """
        Khởi tạo CKGQueryInterfaceAgent.
        
        Args:
            connection_config: Cấu hình kết nối Neo4j
        """
        self.config = connection_config or ConnectionConfig()
        self.driver = None
        self.schema = CKGSchema()
        self.query_cache = {}  # Simple cache cho frequent queries
        
        # Kết nối Neo4j
        self._connect()
    
    def get_connection(self):
        """
        Lấy connection đến Neo4j.
        
        Returns:
            Neo4j driver hoặc None nếu không kết nối được
        """
        if self.driver is None:
            self._connect()
        return self.driver
    
    def _connect(self):
        """Thiết lập kết nối Neo4j."""
        if GraphDatabase is None:
            logger.warning("Neo4j driver not available")
            return
        
        try:
            self.driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.username, self.config.password)
            )
            
            # Test connection
            with self.driver.session(database=self.config.database) as session:
                session.run("RETURN 1")
            
            logger.info(f"Kết nối Neo4j thành công: {self.config.uri}")
            
        except Exception as e:
            logger.error(f"Lỗi kết nối Neo4j: {str(e)}")
            self.driver = None
    
    def close(self):
        """Đóng kết nối Neo4j."""
        if self.driver:
            self.driver.close()
            self.driver = None
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> CKGQueryResult:
        """
        Thực thi Cypher query.
        
        Args:
            query: Cypher query
            parameters: Parameters cho query
            
        Returns:
            CKGQueryResult: Kết quả truy vấn
        """
        if not self.driver:
            return CKGQueryResult(
                query=query,
                results=[],
                total_count=0,
                execution_time_ms=0,
                success=False,
                error_message="Không có kết nối Neo4j"
            )
        
        import time
        start_time = time.time()
        
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query, parameters or {})
                records = []
                
                for record in result:
                    record_dict = {}
                    for key in record.keys():
                        value = record[key]
                        # Convert Neo4j objects to dict
                        if hasattr(value, '__dict__'):
                            record_dict[key] = dict(value)
                        else:
                            record_dict[key] = value
                    records.append(record_dict)
                
                execution_time = (time.time() - start_time) * 1000
                
                return CKGQueryResult(
                    query=query,
                    results=records,
                    total_count=len(records),
                    execution_time_ms=execution_time,
                    success=True
                )
                
        except Exception as e:
            logger.error(f"Lỗi thực thi query: {str(e)}")
            execution_time = (time.time() - start_time) * 1000
            
            return CKGQueryResult(
                query=query,
                results=[],
                total_count=0,
                execution_time_ms=execution_time,
                success=False,
                error_message=str(e)
            )
    
    # === API Methods cho các truy vấn phổ biến ===
    
    def get_functions_in_file(self, file_path: str) -> CKGQueryResult:
        """
        Lấy tất cả functions trong một file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: Danh sách functions
        """
        query = """
        MATCH (f:File {file_path: $file_path})-[:CONTAINS]->(m:Module)
        MATCH (m)-[:DEFINES_FUNCTION]->(func:Function)
        RETURN func.name as name, func.line_number as line_number,
               func.parameters_count as params_count, func.docstring as docstring
        ORDER BY func.line_number
        """
        
        return self.execute_query(query, {"file_path": file_path})
    
    def get_classes_in_file(self, file_path: str) -> CKGQueryResult:
        """
        Lấy tất cả classes trong một file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: Danh sách classes
        """
        query = """
        MATCH (f:File {file_path: $file_path})-[:CONTAINS]->(m:Module)
        MATCH (m)-[:DEFINES_CLASS]->(cls:Class)
        RETURN cls.name as name, cls.line_number as line_number,
               cls.methods_count as methods_count, cls.base_classes as base_classes,
               cls.docstring as docstring
        ORDER BY cls.line_number
        """
        
        return self.execute_query(query, {"file_path": file_path})
    
    def get_methods_in_class(self, class_name: str, file_path: Optional[str] = None) -> CKGQueryResult:
        """
        Lấy tất cả methods trong một class.
        
        Args:
            class_name: Tên class
            file_path: Đường dẫn file (optional)
            
        Returns:
            CKGQueryResult: Danh sách methods
        """
        if file_path:
            query = """
            MATCH (f:File {file_path: $file_path})-[:CONTAINS]->(m:Module)
            MATCH (m)-[:DEFINES_CLASS]->(cls:Class {name: $class_name})
            MATCH (cls)-[:DEFINES_METHOD]->(method:Method)
            RETURN method.name as name, method.line_number as line_number,
                   method.parameters_count as params_count, method.is_static as is_static,
                   method.is_class_method as is_class_method, method.docstring as docstring
            ORDER BY method.line_number
            """
            params = {"class_name": class_name, "file_path": file_path}
        else:
            query = """
            MATCH (cls:Class {name: $class_name})-[:DEFINES_METHOD]->(method:Method)
            RETURN method.name as name, method.line_number as line_number,
                   method.parameters_count as params_count, method.is_static as is_static,
                   method.is_class_method as is_class_method, method.docstring as docstring,
                   method.file_path as file_path
            ORDER BY method.line_number
            """
            params = {"class_name": class_name}
        
        return self.execute_query(query, params)
    
    def get_imports_in_file(self, file_path: str) -> CKGQueryResult:
        """
        Lấy tất cả imports trong một file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: Danh sách imports
        """
        query = """
        MATCH (f:File {file_path: $file_path})-[:CONTAINS]->(m:Module)
        MATCH (m)-[:IMPORTS]->(imp:Import)
        RETURN imp.name as name, imp.imported_name as imported_name,
               imp.alias as alias, imp.is_from_import as is_from_import,
               imp.module_name as module_name, imp.line_number as line_number
        ORDER BY imp.line_number
        """
        
        return self.execute_query(query, {"file_path": file_path})
    
    def find_function_callers(self, function_name: str) -> CKGQueryResult:
        """
        Tìm những functions gọi đến function đã cho.
        
        Args:
            function_name: Tên function
            
        Returns:
            CKGQueryResult: Danh sách callers
        """
        query = """
        MATCH (caller)-[:CALLS]->(target:Function {name: $function_name})
        RETURN caller.name as caller_name, caller.type as caller_type,
               caller.file_path as caller_file, caller.line_number as caller_line,
               target.name as target_name, target.file_path as target_file
        """
        
        return self.execute_query(query, {"function_name": function_name})
    
    def find_function_callees(self, function_name: str, file_path: Optional[str] = None) -> CKGQueryResult:
        """
        Tìm những functions được gọi bởi function đã cho.
        
        Args:
            function_name: Tên function
            file_path: Đường dẫn file (optional)
            
        Returns:
            CKGQueryResult: Danh sách callees
        """
        if file_path:
            query = """
            MATCH (caller:Function {name: $function_name, file_path: $file_path})
            MATCH (caller)-[:CALLS]->(target)
            RETURN target.name as target_name, target.type as target_type,
                   target.file_path as target_file, target.line_number as target_line,
                   caller.name as caller_name, caller.file_path as caller_file
            """
            params = {"function_name": function_name, "file_path": file_path}
        else:
            query = """
            MATCH (caller:Function {name: $function_name})-[:CALLS]->(target)
            RETURN target.name as target_name, target.type as target_type,
                   target.file_path as target_file, target.line_number as target_line,
                   caller.name as caller_name, caller.file_path as caller_file
            """
            params = {"function_name": function_name}
        
        return self.execute_query(query, params)
    
    def get_class_hierarchy(self, class_name: str) -> CKGQueryResult:
        """
        Lấy hierarchy của một class (base classes và derived classes).
        
        Args:
            class_name: Tên class
            
        Returns:
            CKGQueryResult: Class hierarchy
        """
        query = """
        MATCH (cls:Class {name: $class_name})
        OPTIONAL MATCH (cls)-[:INHERITS_FROM]->(base:Class)
        OPTIONAL MATCH (derived:Class)-[:INHERITS_FROM]->(cls)
        RETURN cls.name as class_name, cls.file_path as class_file,
               COLLECT(DISTINCT base.name) as base_classes,
               COLLECT(DISTINCT derived.name) as derived_classes
        """
        
        return self.execute_query(query, {"class_name": class_name})
    
    def find_circular_dependencies(self) -> CKGQueryResult:
        """
        Tìm circular dependencies giữa các modules.
        
        Returns:
            CKGQueryResult: Circular dependencies
        """
        query = """
        MATCH path = (m1:Module)-[:IMPORTS*2..10]->(m1)
        WHERE ALL(rel in relationships(path) WHERE type(rel) = 'IMPORTS')
        RETURN [node in nodes(path) | node.name] as cycle_path,
               length(path) as cycle_length
        ORDER BY cycle_length
        """
        
        return self.execute_query(query)
    
    def get_unused_public_functions(self, file_path: Optional[str] = None) -> CKGQueryResult:
        """
        Tìm public functions không được sử dụng.
        
        Args:
            file_path: Đường dẫn file (optional)
            
        Returns:
            CKGQueryResult: Unused functions
        """
        if file_path:
            query = """
            MATCH (f:File {file_path: $file_path})-[:CONTAINS]->(m:Module)
            MATCH (m)-[:DEFINES_FUNCTION]->(func:Function)
            WHERE NOT func.name STARTS WITH '_'
            AND NOT EXISTS((other)-[:CALLS]->(func))
            RETURN func.name as name, func.file_path as file_path,
                   func.line_number as line_number, func.docstring as docstring
            ORDER BY func.name
            """
            params = {"file_path": file_path}
        else:
            query = """
            MATCH (func:Function)
            WHERE NOT func.name STARTS WITH '_'
            AND NOT EXISTS((other)-[:CALLS]->(func))
            RETURN func.name as name, func.file_path as file_path,
                   func.line_number as line_number, func.docstring as docstring
            ORDER BY func.file_path, func.name
            """
            params = {}
        
        return self.execute_query(query, params)
    
    def get_project_statistics(self) -> CKGQueryResult:
        """
        Lấy thống kê tổng quan về project.
        
        Returns:
            CKGQueryResult: Project statistics
        """
        query = """
        MATCH (f:File) WITH COUNT(f) as files_count
        MATCH (m:Module) WITH files_count, COUNT(m) as modules_count
        MATCH (c:Class) WITH files_count, modules_count, COUNT(c) as classes_count
        MATCH (func:Function) WITH files_count, modules_count, classes_count, COUNT(func) as functions_count
        MATCH (method:Method) WITH files_count, modules_count, classes_count, functions_count, COUNT(method) as methods_count
        MATCH (imp:Import) WITH files_count, modules_count, classes_count, functions_count, methods_count, COUNT(imp) as imports_count
        MATCH ()-[r]->() WITH files_count, modules_count, classes_count, functions_count, methods_count, imports_count, COUNT(r) as relationships_count
        RETURN files_count, modules_count, classes_count, functions_count, 
               methods_count, imports_count, relationships_count
        """
        
        return self.execute_query(query)
    
    def search_by_name(self, name_pattern: str, node_types: Optional[List[str]] = None) -> CKGQueryResult:
        """
        Tìm kiếm nodes theo tên.
        
        Args:
            name_pattern: Pattern tìm kiếm (hỗ trợ regex)
            node_types: Danh sách loại nodes cần tìm
            
        Returns:
            CKGQueryResult: Kết quả tìm kiếm
        """
        if node_types:
            type_filter = " OR ".join([f"'{t}' IN labels(n)" for t in node_types])
            query = f"""
            MATCH (n)
            WHERE n.name =~ $pattern AND ({type_filter})
            RETURN n.name as name, labels(n) as types, n.file_path as file_path,
                   n.line_number as line_number, n.docstring as docstring
            ORDER BY n.name
            """
        else:
            query = """
            MATCH (n)
            WHERE n.name =~ $pattern
            RETURN n.name as name, labels(n) as types, n.file_path as file_path,
                   n.line_number as line_number, n.docstring as docstring
            ORDER BY n.name
            """
        
        # Convert pattern to regex
        regex_pattern = f"(?i).*{name_pattern}.*"
        
        return self.execute_query(query, {"pattern": regex_pattern})
    
    def get_file_dependencies(self, file_path: str) -> CKGQueryResult:
        """
        Lấy dependencies của một file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: File dependencies
        """
        query = """
        MATCH (f:File {file_path: $file_path})-[:CONTAINS]->(m:Module)
        MATCH (m)-[:IMPORTS]->(imp:Import)
        RETURN DISTINCT imp.module_name as dependency,
               COUNT(imp) as import_count,
               COLLECT(imp.imported_name) as imported_items
        ORDER BY dependency
        """
        
        return self.execute_query(query, {"file_path": file_path})
    
    def get_complex_functions(self, min_parameters: int = 5) -> CKGQueryResult:
        """
        Tìm functions phức tạp (nhiều parameters).
        
        Args:
            min_parameters: Số parameters tối thiểu
            
        Returns:
            CKGQueryResult: Complex functions
        """
        query = """
        MATCH (func:Function)
        WHERE func.parameters_count >= $min_params
        RETURN func.name as name, func.file_path as file_path,
               func.line_number as line_number, func.parameters_count as params_count,
               func.docstring as docstring
        ORDER BY func.parameters_count DESC, func.name
        """
        
        return self.execute_query(query, {"min_params": min_parameters})
    
    # === Cache Management ===
    
    def clear_cache(self):
        """Xóa query cache."""
        self.query_cache.clear()
        logger.info("Query cache đã được xóa")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Lấy thống kê cache."""
        return {
            "cache_size": len(self.query_cache),
            "cached_queries": list(self.query_cache.keys())
        } 