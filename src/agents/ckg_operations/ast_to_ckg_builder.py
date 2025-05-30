#!/usr/bin/env python3
"""
AI CodeScan - AST to CKG Builder Agent

Agent xây dựng Code Knowledge Graph từ Abstract Syntax Trees.
Chuyển đổi thông tin từ AST thành nodes và relationships trong Neo4j.
"""

import ast
import os
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from loguru import logger

from .ckg_schema import (
    NodeType, RelationshipType, NodeProperties, RelationshipProperties, CKGSchema
)
from .code_parser_coordinator import ParseResult, ParsedFile


@dataclass
class CKGBuildResult:
    """Kết quả xây dựng CKG."""
    project_path: str
    total_nodes_created: int
    total_relationships_created: int
    cypher_queries_executed: int
    build_success: bool
    error_messages: List[str]
    build_stats: Dict[str, Any]


class ASTtoCKGBuilderAgent:
    """
    Agent xây dựng Code Knowledge Graph từ AST.
    
    Trách nhiệm:
    - Duyệt qua các ASTs từ CodeParserCoordinatorAgent
    - Trích xuất entities và relationships theo CKG schema
    - Tạo Cypher queries để lưu vào Neo4j
    - Quản lý việc thực thi queries và báo cáo trạng thái
    """
    
    def __init__(self, neo4j_connection=None):
        """
        Khởi tạo ASTtoCKGBuilderAgent.
        
        Args:
            neo4j_connection: Connection đến Neo4j database
        """
        self.neo4j_connection = neo4j_connection
        self.schema = CKGSchema()
        self.node_id_counter = 0
        self.created_nodes = {}  # Mapping từ node_id đến NodeProperties
        self.created_relationships = []  # Danh sách RelationshipProperties
        
    def build_ckg_from_parse_result(self, parse_result: ParseResult) -> CKGBuildResult:
        """
        Xây dựng CKG từ ParseResult.
        
        Args:
            parse_result: Kết quả parse từ CodeParserCoordinatorAgent
            
        Returns:
            CKGBuildResult: Kết quả xây dựng CKG
        """
        logger.info(f"Bắt đầu xây dựng CKG cho project: {parse_result.project_path}")
        
        # Reset counters
        self.node_id_counter = 0
        self.created_nodes = {}
        self.created_relationships = []
        
        cypher_queries = []
        error_messages = []
        
        try:
            # Process từng file đã parse thành công
            for parsed_file in parse_result.parsed_files:
                if parsed_file.parse_success and parsed_file.ast_tree:
                    file_queries = self._process_file(parsed_file)
                    cypher_queries.extend(file_queries)
            
            # Thực thi queries nếu có Neo4j connection
            queries_executed = 0
            if self.neo4j_connection:
                queries_executed = self._execute_cypher_queries(cypher_queries)
            else:
                logger.warning("Không có Neo4j connection - chỉ tạo queries")
                queries_executed = len(cypher_queries)
            
            # Tính stats
            build_stats = self._calculate_build_stats(parse_result)
            
            return CKGBuildResult(
                project_path=parse_result.project_path,
                total_nodes_created=len(self.created_nodes),
                total_relationships_created=len(self.created_relationships),
                cypher_queries_executed=queries_executed,
                build_success=True,
                error_messages=error_messages,
                build_stats=build_stats
            )
            
        except Exception as e:
            logger.error(f"Lỗi xây dựng CKG: {str(e)}")
            error_messages.append(str(e))
            
            return CKGBuildResult(
                project_path=parse_result.project_path,
                total_nodes_created=len(self.created_nodes),
                total_relationships_created=len(self.created_relationships),
                cypher_queries_executed=0,
                build_success=False,
                error_messages=error_messages,
                build_stats={}
            )
    
    def build_ckg_from_ast(self, ast_node: ast.AST, file_path: str) -> List[str]:
        """
        Xây dựng CKG từ một AST node (interface cũ).
        
        Args:
            ast_node: AST node cần xử lý
            file_path: Đường dẫn file
            
        Returns:
            List[str]: Danh sách Cypher queries
        """
        # Tạo mock ParsedFile
        parsed_file = ParsedFile(
            file_path=file_path,
            relative_path=os.path.basename(file_path),
            language='Python',
            ast_tree=ast_node,
            parse_success=True,
            nodes_count=len(list(ast.walk(ast_node))),
            lines_count=0
        )
        
        return self._process_file(parsed_file)
    
    def save_to_neo4j(self, cypher_queries: List[str]) -> int:
        """
        Thực thi Cypher queries lên Neo4j.
        
        Args:
            cypher_queries: Danh sách queries cần thực thi
            
        Returns:
            int: Số queries đã thực thi thành công
            
        Raises:
            RuntimeError: Nếu không có Neo4j connection
        """
        if not self.neo4j_connection:
            raise RuntimeError("Không có Neo4j connection")
        
        return self._execute_cypher_queries(cypher_queries)
    
    def _process_file(self, parsed_file: ParsedFile) -> List[str]:
        """
        Xử lý một file đã parse thành nodes và relationships.
        
        Args:
            parsed_file: File đã parse
            
        Returns:
            List[str]: Danh sách Cypher queries
        """
        queries = []
        
        try:
            # Tạo File node
            file_node = self._create_file_node(parsed_file)
            queries.append(self.schema.get_cypher_create_node(file_node))
            
            # Tạo Module node
            module_node = self._create_module_node(parsed_file)
            queries.append(self.schema.get_cypher_create_node(module_node))
            
            # Tạo relationship CONTAINS giữa File và Module
            contains_rel = RelationshipProperties(
                type=RelationshipType.CONTAINS,
                source_node_id=file_node.properties['id'],
                target_node_id=module_node.properties['id']
            )
            queries.append(self.schema.get_cypher_create_relationship(contains_rel))
            
            # Xử lý AST tree
            ast_queries = self._process_ast_tree(parsed_file.ast_tree, parsed_file, module_node)
            queries.extend(ast_queries)
            
        except Exception as e:
            logger.error(f"Lỗi xử lý file {parsed_file.relative_path}: {str(e)}")
        
        return queries
    
    def _create_file_node(self, parsed_file: ParsedFile) -> NodeProperties:
        """Tạo File node."""
        node_id = self._generate_node_id(NodeType.FILE, parsed_file.file_path, 1, parsed_file.relative_path)
        
        properties = {
            'id': node_id,
            'language': parsed_file.language,
            'lines_count': parsed_file.lines_count,
            'nodes_count': parsed_file.nodes_count,
            'relative_path': parsed_file.relative_path
        }
        
        file_node = NodeProperties(
            name=parsed_file.relative_path,
            type=NodeType.FILE,
            file_path=parsed_file.file_path,
            line_number=1,
            properties=properties
        )
        
        self.created_nodes[node_id] = file_node
        return file_node
    
    def _create_module_node(self, parsed_file: ParsedFile) -> NodeProperties:
        """Tạo Module node."""
        module_name = os.path.splitext(parsed_file.relative_path)[0].replace(os.sep, '.')
        node_id = self._generate_node_id(NodeType.MODULE, parsed_file.file_path, 1, module_name)
        
        # Đếm các elements trong module
        imports_count = 0
        classes_count = 0
        functions_count = 0
        
        for node in ast.walk(parsed_file.ast_tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports_count += 1
            elif isinstance(node, ast.ClassDef):
                classes_count += 1
            elif isinstance(node, ast.FunctionDef):
                functions_count += 1
        
        properties = {
            'id': node_id,
            'imports_count': imports_count,
            'classes_count': classes_count,
            'functions_count': functions_count
        }
        
        module_node = NodeProperties(
            name=module_name,
            type=NodeType.MODULE,
            file_path=parsed_file.file_path,
            line_number=1,
            properties=properties
        )
        
        self.created_nodes[node_id] = module_node
        return module_node
    
    def _process_ast_tree(self, tree: ast.AST, parsed_file: ParsedFile, module_node: NodeProperties) -> List[str]:
        """
        Xử lý AST tree và tạo nodes/relationships.
        
        Args:
            tree: AST tree
            parsed_file: File đã parse
            module_node: Module node chứa các elements
            
        Returns:
            List[str]: Danh sách Cypher queries
        """
        queries = []
        
        # Duyệt qua tất cả nodes trong AST
        for node in ast.walk(tree):
            try:
                if isinstance(node, ast.Import):
                    queries.extend(self._process_import(node, parsed_file, module_node))
                elif isinstance(node, ast.ImportFrom):
                    queries.extend(self._process_import_from(node, parsed_file, module_node))
                elif isinstance(node, ast.ClassDef):
                    queries.extend(self._process_class(node, parsed_file, module_node))
                elif isinstance(node, ast.FunctionDef):
                    queries.extend(self._process_function(node, parsed_file, module_node))
                elif isinstance(node, ast.AsyncFunctionDef):
                    queries.extend(self._process_async_function(node, parsed_file, module_node))
            
            except Exception as e:
                logger.warning(f"Lỗi xử lý AST node {type(node).__name__}: {str(e)}")
        
        return queries
    
    def _process_import(self, node: ast.Import, parsed_file: ParsedFile, module_node: NodeProperties) -> List[str]:
        """Xử lý ast.Import."""
        queries = []
        
        for alias in node.names:
            import_node = self._create_import_node(
                alias.name, 
                alias.asname, 
                node.lineno, 
                parsed_file,
                is_from_import=False
            )
            queries.append(self.schema.get_cypher_create_node(import_node))
            
            # Tạo relationship IMPORTS
            imports_rel = RelationshipProperties(
                type=RelationshipType.IMPORTS,
                source_node_id=module_node.properties['id'],
                target_node_id=import_node.properties['id']
            )
            queries.append(self.schema.get_cypher_create_relationship(imports_rel))
        
        return queries
    
    def _process_import_from(self, node: ast.ImportFrom, parsed_file: ParsedFile, module_node: NodeProperties) -> List[str]:
        """Xử lý ast.ImportFrom."""
        queries = []
        
        module_name = node.module or ''
        
        for alias in node.names:
            import_node = self._create_import_node(
                f"{module_name}.{alias.name}" if module_name else alias.name,
                alias.asname,
                node.lineno,
                parsed_file,
                is_from_import=True,
                module_name=module_name
            )
            queries.append(self.schema.get_cypher_create_node(import_node))
            
            # Tạo relationship IMPORTS
            imports_rel = RelationshipProperties(
                type=RelationshipType.IMPORTS,
                source_node_id=module_node.properties['id'],
                target_node_id=import_node.properties['id']
            )
            queries.append(self.schema.get_cypher_create_relationship(imports_rel))
        
        return queries
    
    def _process_class(self, node: ast.ClassDef, parsed_file: ParsedFile, module_node: NodeProperties) -> List[str]:
        """Xử lý ast.ClassDef."""
        queries = []
        
        # Tạo Class node
        class_node = self._create_class_node(node, parsed_file)
        queries.append(self.schema.get_cypher_create_node(class_node))
        
        # Tạo relationship DEFINES_CLASS
        defines_rel = RelationshipProperties(
            type=RelationshipType.DEFINES_CLASS,
            source_node_id=module_node.properties['id'],
            target_node_id=class_node.properties['id']
        )
        queries.append(self.schema.get_cypher_create_relationship(defines_rel))
        
        # Xử lý methods trong class
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_queries = self._process_method(item, parsed_file, class_node)
                queries.extend(method_queries)
            elif isinstance(item, ast.AsyncFunctionDef):
                method_queries = self._process_async_method(item, parsed_file, class_node)
                queries.extend(method_queries)
        
        return queries
    
    def _process_function(self, node: ast.FunctionDef, parsed_file: ParsedFile, module_node: NodeProperties) -> List[str]:
        """Xử lý ast.FunctionDef (function ở module level)."""
        queries = []
        
        # Tạo Function node
        function_node = self._create_function_node(node, parsed_file)
        queries.append(self.schema.get_cypher_create_node(function_node))
        
        # Tạo relationship DEFINES_FUNCTION
        defines_rel = RelationshipProperties(
            type=RelationshipType.DEFINES_FUNCTION,
            source_node_id=module_node.properties['id'],
            target_node_id=function_node.properties['id']
        )
        queries.append(self.schema.get_cypher_create_relationship(defines_rel))
        
        # Xử lý parameters
        param_queries = self._process_function_parameters(node, parsed_file, function_node)
        queries.extend(param_queries)
        
        return queries
    
    def _process_async_function(self, node: ast.AsyncFunctionDef, parsed_file: ParsedFile, module_node: NodeProperties) -> List[str]:
        """Xử lý ast.AsyncFunctionDef."""
        # Tương tự _process_function nhưng đánh dấu is_async=True
        queries = []
        
        function_node = self._create_function_node(node, parsed_file, is_async=True)
        queries.append(self.schema.get_cypher_create_node(function_node))
        
        defines_rel = RelationshipProperties(
            type=RelationshipType.DEFINES_FUNCTION,
            source_node_id=module_node.properties['id'],
            target_node_id=function_node.properties['id']
        )
        queries.append(self.schema.get_cypher_create_relationship(defines_rel))
        
        param_queries = self._process_function_parameters(node, parsed_file, function_node)
        queries.extend(param_queries)
        
        return queries
    
    def _process_method(self, node: ast.FunctionDef, parsed_file: ParsedFile, class_node: NodeProperties) -> List[str]:
        """Xử lý method trong class."""
        queries = []
        
        # Tạo Method node
        method_node = self._create_method_node(node, parsed_file)
        queries.append(self.schema.get_cypher_create_node(method_node))
        
        # Tạo relationship DEFINES_METHOD
        defines_rel = RelationshipProperties(
            type=RelationshipType.DEFINES_METHOD,
            source_node_id=class_node.properties['id'],
            target_node_id=method_node.properties['id']
        )
        queries.append(self.schema.get_cypher_create_relationship(defines_rel))
        
        # Xử lý parameters
        param_queries = self._process_function_parameters(node, parsed_file, method_node)
        queries.extend(param_queries)
        
        return queries
    
    def _process_async_method(self, node: ast.AsyncFunctionDef, parsed_file: ParsedFile, class_node: NodeProperties) -> List[str]:
        """Xử lý async method trong class."""
        queries = []
        
        method_node = self._create_method_node(node, parsed_file, is_async=True)
        queries.append(self.schema.get_cypher_create_node(method_node))
        
        defines_rel = RelationshipProperties(
            type=RelationshipType.DEFINES_METHOD,
            source_node_id=class_node.properties['id'],
            target_node_id=method_node.properties['id']
        )
        queries.append(self.schema.get_cypher_create_relationship(defines_rel))
        
        param_queries = self._process_function_parameters(node, parsed_file, method_node)
        queries.extend(param_queries)
        
        return queries
    
    def _create_import_node(self, name: str, alias: Optional[str], line_number: int, 
                          parsed_file: ParsedFile, is_from_import: bool = False, 
                          module_name: str = '') -> NodeProperties:
        """Tạo Import node."""
        node_id = self._generate_node_id(NodeType.IMPORT, parsed_file.file_path, line_number, name)
        
        properties = {
            'id': node_id,
            'imported_name': name,
            'alias': alias,
            'is_from_import': is_from_import,
            'module_name': module_name
        }
        
        display_name = alias if alias else name
        
        import_node = NodeProperties(
            name=display_name,
            type=NodeType.IMPORT,
            file_path=parsed_file.file_path,
            line_number=line_number,
            properties=properties
        )
        
        self.created_nodes[node_id] = import_node
        return import_node
    
    def _create_class_node(self, node: ast.ClassDef, parsed_file: ParsedFile) -> NodeProperties:
        """Tạo Class node."""
        node_id = self._generate_node_id(NodeType.CLASS, parsed_file.file_path, node.lineno, node.name)
        
        # Đếm methods và attributes
        methods_count = len([n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))])
        
        # Lấy base classes
        base_classes = [self._get_name_from_node(base) for base in node.bases]
        
        properties = {
            'id': node_id,
            'methods_count': methods_count,
            'base_classes': base_classes,
            'docstring': ast.get_docstring(node)
        }
        
        class_node = NodeProperties(
            name=node.name,
            type=NodeType.CLASS,
            file_path=parsed_file.file_path,
            line_number=node.lineno,
            end_line_number=getattr(node, 'end_lineno', None),
            properties=properties
        )
        
        self.created_nodes[node_id] = class_node
        return class_node
    
    def _create_function_node(self, node: ast.FunctionDef, parsed_file: ParsedFile, is_async: bool = False) -> NodeProperties:
        """Tạo Function node."""
        node_id = self._generate_node_id(NodeType.FUNCTION, parsed_file.file_path, node.lineno, node.name)
        
        properties = {
            'id': node_id,
            'parameters_count': len(node.args.args),
            'is_async': is_async,
            'docstring': ast.get_docstring(node)
        }
        
        function_node = NodeProperties(
            name=node.name,
            type=NodeType.FUNCTION,
            file_path=parsed_file.file_path,
            line_number=node.lineno,
            end_line_number=getattr(node, 'end_lineno', None),
            properties=properties
        )
        
        self.created_nodes[node_id] = function_node
        return function_node
    
    def _create_method_node(self, node: ast.FunctionDef, parsed_file: ParsedFile, is_async: bool = False) -> NodeProperties:
        """Tạo Method node."""
        node_id = self._generate_node_id(NodeType.METHOD, parsed_file.file_path, node.lineno, node.name)
        
        # Xác định method type
        is_static = any(isinstance(d, ast.Name) and d.id == 'staticmethod' for d in node.decorator_list)
        is_class_method = any(isinstance(d, ast.Name) and d.id == 'classmethod' for d in node.decorator_list)
        is_property = any(isinstance(d, ast.Name) and d.id == 'property' for d in node.decorator_list)
        
        properties = {
            'id': node_id,
            'parameters_count': len(node.args.args),
            'is_async': is_async,
            'is_static': is_static,
            'is_class_method': is_class_method,
            'is_property': is_property,
            'docstring': ast.get_docstring(node)
        }
        
        method_node = NodeProperties(
            name=node.name,
            type=NodeType.METHOD,
            file_path=parsed_file.file_path,
            line_number=node.lineno,
            end_line_number=getattr(node, 'end_lineno', None),
            properties=properties
        )
        
        self.created_nodes[node_id] = method_node
        return method_node
    
    def _process_function_parameters(self, node: ast.FunctionDef, parsed_file: ParsedFile, 
                                   parent_node: NodeProperties) -> List[str]:
        """Xử lý parameters của function/method."""
        queries = []
        
        for arg in node.args.args:
            param_node = self._create_parameter_node(arg, parsed_file, node.lineno)
            queries.append(self.schema.get_cypher_create_node(param_node))
            
            # Tạo relationship HAS_PARAMETER
            has_param_rel = RelationshipProperties(
                type=RelationshipType.HAS_PARAMETER,
                source_node_id=parent_node.properties['id'],
                target_node_id=param_node.properties['id']
            )
            queries.append(self.schema.get_cypher_create_relationship(has_param_rel))
        
        return queries
    
    def _create_parameter_node(self, arg: ast.arg, parsed_file: ParsedFile, line_number: int) -> NodeProperties:
        """Tạo Parameter node."""
        node_id = self._generate_node_id(NodeType.PARAMETER, parsed_file.file_path, line_number, arg.arg)
        
        properties = {
            'id': node_id,
            'param_type': getattr(arg, 'annotation', None) and self._get_name_from_node(arg.annotation) or None
        }
        
        param_node = NodeProperties(
            name=arg.arg,
            type=NodeType.PARAMETER,
            file_path=parsed_file.file_path,
            line_number=line_number,
            properties=properties
        )
        
        self.created_nodes[node_id] = param_node
        return param_node
    
    def _get_name_from_node(self, node: ast.AST) -> str:
        """Lấy tên từ AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name_from_node(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        else:
            return str(type(node).__name__)
    
    def _generate_node_id(self, node_type: NodeType, file_path: str, line_number: int, name: str) -> str:
        """Tạo unique ID cho node."""
        clean_file_path = file_path.replace('/', '_').replace('\\', '_').replace('.', '_')
        clean_name = name.replace('.', '_').replace(' ', '_')
        return f"{node_type.value}_{clean_file_path}_{line_number}_{clean_name}_{self.node_id_counter}"
    
    def _execute_cypher_queries(self, queries: List[str]) -> int:
        """
        Thực thi Cypher queries lên Neo4j.
        
        Args:
            queries: Danh sách queries
            
        Returns:
            int: Số queries thành công
        """
        if not self.neo4j_connection:
            return 0
        
        executed_count = 0
        
        try:
            with self.neo4j_connection.session() as session:
                for query in queries:
                    try:
                        session.run(query)
                        executed_count += 1
                    except Exception as e:
                        logger.warning(f"Lỗi thực thi query: {str(e)[:100]}")
                        
        except Exception as e:
            logger.error(f"Lỗi kết nối Neo4j: {str(e)}")
        
        return executed_count
    
    def _calculate_build_stats(self, parse_result: ParseResult) -> Dict[str, Any]:
        """Tính toán thống kê xây dựng CKG."""
        stats = {
            'total_files_processed': parse_result.successful_files,
            'nodes_by_type': {},
            'relationships_by_type': {},
            'average_nodes_per_file': 0,
            'largest_file_nodes': 0,
            'ckg_density': 0
        }
        
        # Đếm nodes theo type
        for node in self.created_nodes.values():
            node_type = node.type.value
            stats['nodes_by_type'][node_type] = stats['nodes_by_type'].get(node_type, 0) + 1
        
        # Đếm relationships theo type
        for rel in self.created_relationships:
            rel_type = rel.type.value
            stats['relationships_by_type'][rel_type] = stats['relationships_by_type'].get(rel_type, 0) + 1
        
        # Tính toán metrics
        if parse_result.successful_files > 0:
            stats['average_nodes_per_file'] = len(self.created_nodes) / parse_result.successful_files
        
        total_nodes = len(self.created_nodes)
        total_relationships = len(self.created_relationships)
        if total_nodes > 1:
            max_possible_edges = total_nodes * (total_nodes - 1)
            stats['ckg_density'] = total_relationships / max_possible_edges if max_possible_edges > 0 else 0
        
        return stats 