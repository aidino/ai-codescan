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
        """
        Lấy thống kê cache.
        
        Returns:
            Dict[str, Any]: Thống kê cache
        """
        return {
            'cache_size': len(self.query_cache),
            'cached_queries': list(self.query_cache.keys())
        }

    # === Dart-specific Query Methods ===
    
    def get_dart_classes_in_file(self, file_path: str) -> CKGQueryResult:
        """
        Lấy tất cả Dart classes trong một file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: Danh sách Dart classes
        """
        query = """
        MATCH (f:File {file_path: $file_path})-[:DEFINES_DART_CLASS]->(cls:DartClass)
        RETURN cls.name as name, cls.line_number as line_number,
               cls.package_name as package, cls.is_abstract as is_abstract,
               cls.extends_class as extends_class, cls.implements_interfaces as implements_interfaces
        ORDER BY cls.line_number
        """
        
        return self.execute_query(query, {"file_path": file_path})
    
    def get_dart_mixins_in_file(self, file_path: str) -> CKGQueryResult:
        """
        Lấy tất cả Dart mixins trong một file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: Danh sách Dart mixins
        """
        query = """
        MATCH (f:File {file_path: $file_path})-[:DEFINES_DART_MIXIN]->(mixin:DartMixin)
        RETURN mixin.name as name, mixin.line_number as line_number,
               mixin.package_name as package, mixin.extends_interfaces as extends_interfaces
        ORDER BY mixin.line_number
        """
        
        return self.execute_query(query, {"file_path": file_path})
    
    def get_dart_extensions_in_file(self, file_path: str) -> CKGQueryResult:
        """
        Lấy tất cả Dart extensions trong một file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: Danh sách Dart extensions
        """
        query = """
        MATCH (f:File {file_path: $file_path})-[:DEFINES_DART_EXTENSION]->(ext:DartExtension)
        RETURN ext.name as name, ext.line_number as line_number,
               ext.extends_class as extends_class, ext.implements_interfaces as implements_interfaces
        ORDER BY ext.line_number
        """
        
        return self.execute_query(query, {"file_path": file_path})
    
    def get_dart_functions_in_file(self, file_path: str) -> CKGQueryResult:
        """
        Lấy tất cả Dart functions trong một file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: Danh sách Dart functions
        """
        query = """
        MATCH (f:File {file_path: $file_path})-[:DEFINES_DART_FUNCTION]->(func:DartFunction)
        RETURN func.name as name, func.line_number as line_number,
               func.return_type as return_type, func.parameters_count as params_count,
               func.is_async as is_async, func.is_generator as is_generator
        ORDER BY func.line_number
        """
        
        return self.execute_query(query, {"file_path": file_path})
    
    def get_dart_enums_in_file(self, file_path: str) -> CKGQueryResult:
        """
        Lấy tất cả Dart enums trong một file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: Danh sách Dart enums
        """
        query = """
        MATCH (f:File {file_path: $file_path})-[:DEFINES_DART_ENUM]->(enum:DartEnum)
        RETURN enum.name as name, enum.line_number as line_number,
               enum.package_name as package, enum.constants_count as constants_count
        ORDER BY enum.line_number
        """
        
        return self.execute_query(query, {"file_path": file_path})
    
    def get_dart_imports_in_file(self, file_path: str) -> CKGQueryResult:
        """
        Lấy tất cả Dart imports trong một file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: Danh sách Dart imports
        """
        query = """
        MATCH (f:File {file_path: $file_path})-[:IMPORTS]->(imp:DartImport)
        RETURN imp.name as name, imp.line_number as line_number,
               imp.imported_name as imported_name, imp.is_package_import as is_package_import,
               imp.is_relative_import as is_relative_import
        ORDER BY imp.line_number
        """
        
        return self.execute_query(query, {"file_path": file_path})
    
    def get_dart_exports_in_file(self, file_path: str) -> CKGQueryResult:
        """
        Lấy tất cả Dart exports trong một file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: Danh sách Dart exports
        """
        query = """
        MATCH (f:File {file_path: $file_path})-[:DART_EXPORTS]->(exp:DartExport)
        RETURN exp.name as name, exp.line_number as line_number,
               exp.full_name as full_name
        ORDER BY exp.line_number
        """
        
        return self.execute_query(query, {"file_path": file_path})
    
    def get_dart_library_info(self, file_path: str) -> CKGQueryResult:
        """
        Lấy thông tin Dart library trong một file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: Thông tin Dart library
        """
        query = """
        MATCH (f:File {file_path: $file_path})-[:CONTAINS]->(lib:DartLibrary)
        RETURN lib.name as name, lib.line_number as line_number,
               lib.full_name as full_name
        """
        
        return self.execute_query(query, {"file_path": file_path})
    
    def find_dart_class_hierarchy(self, class_name: str) -> CKGQueryResult:
        """
        Tìm hierarchy của Dart class (extends, implements, mixins).
        
        Args:
            class_name: Tên class
            
        Returns:
            CKGQueryResult: Class hierarchy information
        """
        query = """
        MATCH (cls:DartClass {name: $class_name})
        OPTIONAL MATCH (cls)-[:DART_EXTENDS]->(parent:DartClass)
        OPTIONAL MATCH (cls)-[:DART_IMPLEMENTS]->(interface:DartInterface)
        OPTIONAL MATCH (cls)-[:DART_MIXES_IN]->(mixin:DartMixin)
        RETURN cls.name as class_name,
               collect(DISTINCT parent.name) as extends_classes,
               collect(DISTINCT interface.name) as implements_interfaces,
               collect(DISTINCT mixin.name) as mixes_in_mixins
        """
        
        return self.execute_query(query, {"class_name": class_name})
    
    def get_dart_project_statistics(self) -> CKGQueryResult:
        """
        Lấy thống kê tổng quan về Dart project.
        
        Returns:
            CKGQueryResult: Thống kê Dart project
        """
        query = """
        RETURN 
            COUNT(DISTINCT n) FILTER (WHERE n:DartClass) as dart_classes_count,
            COUNT(DISTINCT n) FILTER (WHERE n:DartMixin) as dart_mixins_count,
            COUNT(DISTINCT n) FILTER (WHERE n:DartExtension) as dart_extensions_count,
            COUNT(DISTINCT n) FILTER (WHERE n:DartFunction) as dart_functions_count,
            COUNT(DISTINCT n) FILTER (WHERE n:DartEnum) as dart_enums_count,
            COUNT(DISTINCT n) FILTER (WHERE n:DartImport) as dart_imports_count,
            COUNT(DISTINCT n) FILTER (WHERE n:DartExport) as dart_exports_count,
            COUNT(DISTINCT n) FILTER (WHERE n:DartLibrary) as dart_libraries_count
        """
        
        return self.execute_query(query)
    
    def search_dart_elements_by_name(self, name_pattern: str, element_types: Optional[List[str]] = None) -> CKGQueryResult:
        """
        Tìm kiếm Dart elements theo tên.
        
        Args:
            name_pattern: Pattern tìm kiếm (regex)
            element_types: Loại elements cần tìm (DartClass, DartMixin, DartFunction, etc.)
            
        Returns:
            CKGQueryResult: Kết quả tìm kiếm
        """
        # Default Dart element types
        if element_types is None:
            element_types = ['DartClass', 'DartMixin', 'DartExtension', 'DartFunction', 'DartEnum']
        
        # Build dynamic query based on element types
        type_conditions = []
        for element_type in element_types:
            type_conditions.append(f"n:{element_type}")
        
        type_filter = " OR ".join(type_conditions)
        
        query = f"""
        MATCH (n)
        WHERE ({type_filter}) AND n.name =~ $pattern
        RETURN n.name as name, labels(n)[0] as type, n.file_path as file_path,
               n.line_number as line_number
        ORDER BY n.name
        LIMIT 50
        """
        
        return self.execute_query(query, {"pattern": f".*{name_pattern}.*"})
    
    def find_dart_unused_exports(self, file_path: Optional[str] = None) -> CKGQueryResult:
        """
        Tìm Dart exports không được sử dụng.
        
        Args:
            file_path: File path để tìm kiếm (optional)
            
        Returns:
            CKGQueryResult: Danh sách exports không được sử dụng
        """
        if file_path:
            query = """
            MATCH (f:File {file_path: $file_path})-[:DART_EXPORTS]->(exp:DartExport)
            WHERE NOT EXISTS {
                MATCH (other_file:File)-[:IMPORTS]->(imp:DartImport)
                WHERE imp.imported_name CONTAINS exp.name
            }
            RETURN exp.name as export_name, exp.file_path as file_path,
                   exp.line_number as line_number
            ORDER BY exp.name
            """
            return self.execute_query(query, {"file_path": file_path})
        else:
            query = """
            MATCH (exp:DartExport)
            WHERE NOT EXISTS {
                MATCH (other_file:File)-[:IMPORTS]->(imp:DartImport)
                WHERE imp.imported_name CONTAINS exp.name
            }
            RETURN exp.name as export_name, exp.file_path as file_path,
                   exp.line_number as line_number
            ORDER BY exp.file_path, exp.name
            """
            return self.execute_query(query)
    
    def find_dart_circular_imports(self) -> CKGQueryResult:
        """
        Tìm circular imports trong Dart code.
        
        Returns:
            CKGQueryResult: Danh sách circular import paths
        """
        query = """
        MATCH path = (f1:File)-[:CONTAINS]->(:DartLibrary)-[:DEFINES_DART_IMPORT]->(:DartImport)-[:DART_IMPORTS]->(f2:File)
        WHERE f1 <> f2 AND exists((f2)-[:CONTAINS]->(:DartLibrary)-[:DEFINES_DART_IMPORT]->(:DartImport)-[:DART_IMPORTS]->(f1))
        RETURN f1.file_path as file1, f2.file_path as file2, length(path) as path_length
        ORDER BY path_length DESC
        """
        
        return self.execute_query(query)

    # === Kotlin Query Methods ===
    
    def get_kotlin_classes_in_file(self, file_path: str) -> CKGQueryResult:
        """
        Lấy tất cả Kotlin classes trong một file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: Danh sách Kotlin classes
        """
        query = """
        MATCH (f:File {file_path: $file_path})
        MATCH (f)-[:DEFINES_KOTLIN_CLASS]->(c:KotlinClass)
        RETURN c.name as name, c.line_number as line_number,
               c.modifiers as modifiers, c.is_abstract as is_abstract,
               c.is_final as is_final, c.extends_class as extends_class,
               c.implements_interfaces as implements_interfaces,
               c.methods_count as methods_count, c.fields_count as fields_count
        ORDER BY c.line_number
        """
        
        return self.execute_query(query, {"file_path": file_path})

    def get_kotlin_interfaces_in_file(self, file_path: str) -> CKGQueryResult:
        """
        Lấy tất cả Kotlin interfaces trong một file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: Danh sách Kotlin interfaces
        """
        query = """
        MATCH (f:File {file_path: $file_path})
        MATCH (f)-[:DEFINES_KOTLIN_INTERFACE]->(i:KotlinInterface)
        RETURN i.name as name, i.line_number as line_number,
               i.modifiers as modifiers, i.extends_interfaces as extends_interfaces,
               i.methods_count as methods_count, i.fields_count as fields_count
        ORDER BY i.line_number
        """
        
        return self.execute_query(query, {"file_path": file_path})

    def get_kotlin_data_classes_in_file(self, file_path: str) -> CKGQueryResult:
        """
        Lấy tất cả Kotlin data classes trong một file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: Danh sách Kotlin data classes
        """
        query = """
        MATCH (f:File {file_path: $file_path})
        MATCH (f)-[:DEFINES_KOTLIN_DATA_CLASS]->(dc:KotlinDataClass)
        RETURN dc.name as name, dc.line_number as line_number,
               dc.modifiers as modifiers, dc.extends_class as extends_class,
               dc.implements_interfaces as implements_interfaces,
               dc.fields_count as fields_count
        ORDER BY dc.line_number
        """
        
        return self.execute_query(query, {"file_path": file_path})

    def get_kotlin_objects_in_file(self, file_path: str) -> CKGQueryResult:
        """
        Lấy tất cả Kotlin objects trong một file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: Danh sách Kotlin objects
        """
        query = """
        MATCH (f:File {file_path: $file_path})
        MATCH (f)-[:DEFINES_KOTLIN_OBJECT]->(o:KotlinObject)
        RETURN o.name as name, o.line_number as line_number,
               o.modifiers as modifiers, o.extends_class as extends_class,
               o.implements_interfaces as implements_interfaces,
               o.methods_count as methods_count, o.fields_count as fields_count
        ORDER BY o.line_number
        """
        
        return self.execute_query(query, {"file_path": file_path})

    def get_kotlin_functions_in_file(self, file_path: str) -> CKGQueryResult:
        """
        Lấy tất cả Kotlin functions trong một file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: Danh sách Kotlin functions
        """
        query = """
        MATCH (f:File {file_path: $file_path})
        MATCH (f)-[:DEFINES_KOTLIN_FUNCTION]->(func:KotlinFunction)
        RETURN func.name as name, func.line_number as line_number,
               func.return_type as return_type, func.parameters_count as parameters_count,
               func.complexity as complexity, func.is_async as is_async
        ORDER BY func.line_number
        """
        
        return self.execute_query(query, {"file_path": file_path})

    def get_kotlin_extension_functions_in_file(self, file_path: str) -> CKGQueryResult:
        """
        Lấy tất cả Kotlin extension functions trong một file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: Danh sách Kotlin extension functions
        """
        query = """
        MATCH (f:File {file_path: $file_path})
        MATCH (f)-[:DEFINES_KOTLIN_EXTENSION_FUNCTION]->(ef:KotlinExtensionFunction)
        RETURN ef.name as name, ef.line_number as line_number,
               ef.return_type as return_type, ef.parameters_count as parameters_count,
               ef.complexity as complexity
        ORDER BY ef.line_number
        """
        
        return self.execute_query(query, {"file_path": file_path})

    def get_kotlin_enums_in_file(self, file_path: str) -> CKGQueryResult:
        """
        Lấy tất cả Kotlin enums trong một file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: Danh sách Kotlin enums
        """
        query = """
        MATCH (f:File {file_path: $file_path})
        MATCH (f)-[:DEFINES_KOTLIN_ENUM]->(e:KotlinEnum)
        RETURN e.name as name, e.line_number as line_number,
               e.modifiers as modifiers, e.implements_interfaces as implements_interfaces,
               e.constants_count as constants_count, e.methods_count as methods_count
        ORDER BY e.line_number
        """
        
        return self.execute_query(query, {"file_path": file_path})

    def get_kotlin_imports_in_file(self, file_path: str) -> CKGQueryResult:
        """
        Lấy tất cả Kotlin imports trong một file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: Danh sách Kotlin imports
        """
        query = """
        MATCH (f:File {file_path: $file_path})
        MATCH (f)-[:CONTAINS]->(p:KotlinPackage)-[:DEFINES_KOTLIN_IMPORT]->(i:KotlinImport)
        RETURN i.name as import_name, i.line_number as line_number,
               i.module_name as module_name, i.imported_name as imported_name,
               i.alias as alias, i.is_from_import as is_from_import
        ORDER BY i.line_number
        """
        
        return self.execute_query(query, {"file_path": file_path})

    def get_kotlin_package_info(self, file_path: str) -> CKGQueryResult:
        """
        Lấy thông tin Kotlin package trong một file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: Thông tin Kotlin package
        """
        query = """
        MATCH (f:File {file_path: $file_path})
        MATCH (f)-[:CONTAINS]->(p:KotlinPackage)
        RETURN p.name as package_name, p.line_number as line_number,
               p.full_name as full_name, p.classes_count as classes_count,
               p.interfaces_count as interfaces_count
        """
        
        return self.execute_query(query, {"file_path": file_path})

    def find_kotlin_class_hierarchy(self, class_name: str) -> CKGQueryResult:
        """
        Tìm hierarchy của một Kotlin class.
        
        Args:
            class_name: Tên class cần tìm hierarchy
            
        Returns:
            CKGQueryResult: Class hierarchy với extends và implements relationships
        """
        query = """
        MATCH (c:KotlinClass {name: $class_name})
        OPTIONAL MATCH (c)-[:KOTLIN_EXTENDS]->(parent:KotlinClass)
        OPTIONAL MATCH (c)-[:KOTLIN_IMPLEMENTS]->(interface:KotlinInterface)
        OPTIONAL MATCH (child:KotlinClass)-[:KOTLIN_EXTENDS]->(c)
        RETURN c.name as class_name, c.file_path as file_path,
               parent.name as parent_class, interface.name as implemented_interface,
               collect(DISTINCT child.name) as child_classes
        """
        
        return self.execute_query(query, {"class_name": class_name})

    def get_kotlin_project_statistics(self) -> CKGQueryResult:
        """
        Lấy thống kê tổng quan về Kotlin code trong project.
        
        Returns:
            CKGQueryResult: Thống kê Kotlin project
        """
        query = """
        MATCH (f:File)
        OPTIONAL MATCH (f)-[:DEFINES_KOTLIN_CLASS]->(c:KotlinClass)
        OPTIONAL MATCH (f)-[:DEFINES_KOTLIN_INTERFACE]->(i:KotlinInterface)
        OPTIONAL MATCH (f)-[:DEFINES_KOTLIN_DATA_CLASS]->(dc:KotlinDataClass)
        OPTIONAL MATCH (f)-[:DEFINES_KOTLIN_OBJECT]->(o:KotlinObject)
        OPTIONAL MATCH (f)-[:DEFINES_KOTLIN_FUNCTION]->(func:KotlinFunction)
        OPTIONAL MATCH (f)-[:DEFINES_KOTLIN_EXTENSION_FUNCTION]->(ef:KotlinExtensionFunction)
        OPTIONAL MATCH (f)-[:DEFINES_KOTLIN_ENUM]->(e:KotlinEnum)
        RETURN 
            count(DISTINCT f) as total_kotlin_files,
            count(DISTINCT c) as total_classes,
            count(DISTINCT i) as total_interfaces,
            count(DISTINCT dc) as total_data_classes,
            count(DISTINCT o) as total_objects,
            count(DISTINCT func) as total_functions,
            count(DISTINCT ef) as total_extension_functions,
            count(DISTINCT e) as total_enums
        """
        
        return self.execute_query(query)

    def search_kotlin_elements_by_name(self, name_pattern: str, element_types: Optional[List[str]] = None) -> CKGQueryResult:
        """
        Tìm kiếm Kotlin elements theo tên.
        
        Args:
            name_pattern: Pattern để tìm kiếm (regex)
            element_types: Danh sách loại elements cần tìm (classes, interfaces, functions, etc.)
            
        Returns:
            CKGQueryResult: Danh sách elements matching pattern
        """
        # Default search all Kotlin element types
        if element_types is None:
            element_types = ['KotlinClass', 'KotlinInterface', 'KotlinDataClass', 'KotlinObject', 
                           'KotlinFunction', 'KotlinExtensionFunction', 'KotlinEnum']
        
        # Build WHERE clause cho element types
        type_clauses = []
        for element_type in element_types:
            type_clauses.append(f"n:{element_type}")
        
        where_clause = " OR ".join(type_clauses)
        
        query = f"""
        MATCH (n)
        WHERE ({where_clause}) AND n.name =~ $name_pattern
        RETURN n.name as name, labels(n) as types, n.file_path as file_path,
               n.line_number as line_number
        ORDER BY n.name
        """
        
        return self.execute_query(query, {"name_pattern": name_pattern})

    def find_kotlin_unused_objects(self, file_path: Optional[str] = None) -> CKGQueryResult:
        """
        Tìm Kotlin objects không được sử dụng.
        
        Args:
            file_path: File path để scope search (optional)
            
        Returns:
            CKGQueryResult: Danh sách unused Kotlin objects
        """
        if file_path:
            query = """
            MATCH (f:File {file_path: $file_path})-[:DEFINES_KOTLIN_OBJECT]->(o:KotlinObject)
            WHERE NOT exists((o)<-[:KOTLIN_USES_TYPE]-())
            RETURN o.name as object_name, o.file_path as file_path,
                   o.line_number as line_number, o.modifiers as modifiers
            ORDER BY o.name
            """
            parameters = {"file_path": file_path}
        else:
            query = """
            MATCH (o:KotlinObject)
            WHERE NOT exists((o)<-[:KOTLIN_USES_TYPE]-())
            RETURN o.name as object_name, o.file_path as file_path,
                   o.line_number as line_number, o.modifiers as modifiers
            ORDER BY o.name
            """
            parameters = {}
        
        return self.execute_query(query, parameters)

    def find_kotlin_circular_dependencies(self) -> CKGQueryResult:
        """
        Tìm circular dependencies trong Kotlin code.
        
        Returns:
            CKGQueryResult: Danh sách circular dependency paths
        """
        query = """
        MATCH path = (f1:File)-[:CONTAINS]->(:KotlinPackage)-[:DEFINES_KOTLIN_IMPORT]->(:KotlinImport)-[:KOTLIN_DEPENDS_ON]->(f2:File)
        WHERE f1 <> f2 AND exists((f2)-[:CONTAINS]->(:KotlinPackage)-[:DEFINES_KOTLIN_IMPORT]->(:KotlinImport)-[:KOTLIN_DEPENDS_ON]->(f1))
        RETURN f1.file_path as file1, f2.file_path as file2, length(path) as path_length
        ORDER BY path_length DESC
        """
        
        return self.execute_query(query) 