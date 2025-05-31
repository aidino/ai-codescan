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

# Import Java-specific types
try:
    from .java_parser import JavaNode, JavaParseInfo
except ImportError:
    # Fallback if java_parser is not available
    JavaNode = None
    JavaParseInfo = None

# Import Dart-specific types
try:
    from .dart_parser import DartNode, DartParseInfo
except ImportError:
    # Fallback if dart_parser is not available
    DartNode = None
    DartParseInfo = None


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
    AST to Code Knowledge Graph Builder Agent.

    Agent chuyển đổi Abstract Syntax Trees (AST) thành Code Knowledge Graph (CKG)
    bằng cách tạo các Cypher queries để build graph structure trong Neo4j database.

    Supports:
        - Python AST parsing và conversion
        - Java AST parsing và conversion (via JavaParser)
        - Node creation cho files, modules, classes, functions, methods
        - Relationship creation cho imports, calls, inheritance, containment
        - Property extraction từ AST nodes
        - Bulk operations cho performance optimization

    Args:
        neo4j_uri (str): Neo4j database connection URI.
        neo4j_user (str): Neo4j database username.
        neo4j_password (str): Neo4j database password.

    Attributes:
        schema (CKGSchema): Schema definition cho graph structure.
        driver: Neo4j database driver instance.
        created_nodes (Dict[str, NodeProperties]): Cache của created nodes.
        
    Example:
        >>> builder = ASTtoCKGBuilderAgent(
        ...     neo4j_uri="bolt://localhost:7687",
        ...     neo4j_user="neo4j",
        ...     neo4j_password="password"
        ... )
        >>> result = builder.build_ckg_from_parse_result(parse_result)
        >>> print(f"Created {result.total_nodes} nodes, {result.total_relationships} relationships")
        
    Note:
        Requires Neo4j database to be running và accessible.
        Uses CKGSchema để ensure consistent graph structure.
        Supports both Python và Java AST processing.
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
            
            # Xử lý theo ngôn ngữ
            if parsed_file.language == 'Python':
                queries.extend(self._process_python_file(parsed_file, file_node))
            elif parsed_file.language == 'Java':
                queries.extend(self._process_java_file(parsed_file, file_node))
            elif parsed_file.language == 'Dart':
                queries.extend(self._process_dart_file(parsed_file, file_node))
            elif parsed_file.language == 'Kotlin':
                queries.extend(self._process_kotlin_file(parsed_file, file_node))
            else:
                logger.warning(f"Unsupported language: {parsed_file.language}")
            
        except Exception as e:
            logger.error(f"Lỗi xử lý file {parsed_file.relative_path}: {str(e)}")
        
        return queries
    
    def _process_python_file(self, parsed_file: ParsedFile, file_node: NodeProperties) -> List[str]:
        """
        Xử lý Python file AST.
        
        Args:
            parsed_file: Parsed Python file
            file_node: File node đã tạo
            
        Returns:
            List[str]: Danh sách Cypher queries
        """
        queries = []
        
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
        self.created_relationships.append(contains_rel)
        
        # Xử lý AST tree
        if parsed_file.ast_tree:
            queries.extend(self._process_ast_tree(parsed_file.ast_tree, parsed_file, module_node))
        
        return queries
    
    def _process_java_file(self, parsed_file: ParsedFile, file_node: NodeProperties) -> List[str]:
        """
        Xử lý Java file AST.
        
        Args:
            parsed_file: Parsed Java file
            file_node: File node đã tạo
            
        Returns:
            List[str]: Danh sách Cypher queries
        """
        queries = []
        
        if not JavaNode:
            logger.warning("JavaNode not available - skipping Java file processing")
            return queries
            
        try:
            java_ast = parsed_file.ast_tree
            if not isinstance(java_ast, JavaNode):
                logger.warning(f"Expected JavaNode, got {type(java_ast)}")
                return queries
            
            # Process Java AST structure
            queries.extend(self._process_java_ast(java_ast, parsed_file, file_node))
            
        except Exception as e:
            logger.error(f"Error processing Java file {parsed_file.relative_path}: {e}")
        
        return queries
    
    def _process_java_ast(self, java_ast: 'JavaNode', parsed_file: ParsedFile, file_node: NodeProperties) -> List[str]:
        """
        Xử lý Java AST tree.
        
        Args:
            java_ast: Java AST root node
            parsed_file: Parsed file info
            file_node: File node đã tạo
            
        Returns:
            List[str]: Cypher queries
        """
        queries = []
        
        try:
            # Extract package information
            package_node = None
            if java_ast.metadata and java_ast.metadata.get('package_name'):
                package_node = self._create_java_package_node(
                    java_ast.metadata['package_name'], 
                    parsed_file
                )
                queries.append(self.schema.get_cypher_create_node(package_node))
                
                # Link file to package
                belongs_to_rel = RelationshipProperties(
                    type=RelationshipType.BELONGS_TO,
                    source_node_id=file_node.properties['id'],
                    target_node_id=package_node.properties['id']
                )
                queries.append(self.schema.get_cypher_create_relationship(belongs_to_rel))
                self.created_relationships.append(belongs_to_rel)
            
            # Process imports
            if java_ast.metadata and java_ast.metadata.get('imports'):
                for import_name in java_ast.metadata['imports']:
                    import_node = self._create_java_import_node(import_name, parsed_file)
                    queries.append(self.schema.get_cypher_create_node(import_node))
                    
                    # Link file to import
                    imports_rel = RelationshipProperties(
                        type=RelationshipType.IMPORTS,
                        source_node_id=file_node.properties['id'],
                        target_node_id=import_node.properties['id']
                    )
                    queries.append(self.schema.get_cypher_create_relationship(imports_rel))
                    self.created_relationships.append(imports_rel)
            
            # Process all child nodes recursively
            queries.extend(self._process_java_children(java_ast, parsed_file, file_node, package_node))
            
        except Exception as e:
            logger.error(f"Error processing Java AST: {e}")
        
        return queries
    
    def _process_java_children(self, parent_java_node: 'JavaNode', parsed_file: ParsedFile, 
                              file_node: NodeProperties, package_node: Optional[NodeProperties]) -> List[str]:
        """
        Xử lý các child nodes của Java AST.
        
        Args:
            parent_java_node: Parent Java node
            parsed_file: Parsed file info
            file_node: File node
            package_node: Package node (nếu có)
            
        Returns:
            List[str]: Cypher queries
        """
        queries = []
        
        for child in parent_java_node.children:
            try:
                if child.node_type == 'ClassOrInterfaceDeclaration':
                    if child.metadata and child.metadata.get('is_interface', False):
                        queries.extend(self._process_java_interface(child, parsed_file, file_node, package_node))
                    else:
                        queries.extend(self._process_java_class(child, parsed_file, file_node, package_node))
                        
                elif child.node_type == 'EnumDeclaration':
                    queries.extend(self._process_java_enum(child, parsed_file, file_node, package_node))
                    
                elif child.node_type == 'MethodDeclaration':
                    queries.extend(self._process_java_method(child, parsed_file, file_node))
                    
                elif child.node_type == 'FieldDeclaration':
                    queries.extend(self._process_java_field(child, parsed_file, file_node))
                
                # Recursively process children
                queries.extend(self._process_java_children(child, parsed_file, file_node, package_node))
                
            except Exception as e:
                logger.error(f"Error processing Java child node {child.node_type}: {e}")
        
        return queries
    
    def _process_java_class(self, java_class_node: 'JavaNode', parsed_file: ParsedFile,
                           file_node: NodeProperties, package_node: Optional[NodeProperties]) -> List[str]:
        """
        Xử lý Java class declaration.
        
        Args:
            java_class_node: Java class AST node
            parsed_file: Parsed file info
            file_node: File node
            package_node: Package node (nếu có)
            
        Returns:
            List[str]: Cypher queries
        """
        queries = []
        
        # Create Java class node
        class_node = self._create_java_class_node(java_class_node, parsed_file, package_node)
        queries.append(self.schema.get_cypher_create_node(class_node))
        
        # Link file defines class
        defines_rel = RelationshipProperties(
            type=RelationshipType.DEFINES_JAVA_CLASS,
            source_node_id=file_node.properties['id'],
            target_node_id=class_node.properties['id']
        )
        queries.append(self.schema.get_cypher_create_relationship(defines_rel))
        self.created_relationships.append(defines_rel)
        
        # Process class children (methods, fields, constructors)
        for child in java_class_node.children:
            if child.node_type == 'MethodDeclaration':
                queries.extend(self._process_java_method(child, parsed_file, class_node))
            elif child.node_type == 'FieldDeclaration':
                queries.extend(self._process_java_field(child, parsed_file, class_node))
            elif child.node_type == 'ConstructorDeclaration':
                queries.extend(self._process_java_constructor(child, parsed_file, class_node))
        
        return queries
    
    def _process_java_interface(self, java_interface_node: 'JavaNode', parsed_file: ParsedFile,
                               file_node: NodeProperties, package_node: Optional[NodeProperties]) -> List[str]:
        """
        Xử lý Java interface declaration.
        
        Args:
            java_interface_node: Java interface AST node
            parsed_file: Parsed file info
            file_node: File node
            package_node: Package node (nếu có)
            
        Returns:
            List[str]: Cypher queries
        """
        queries = []
        
        # Create Java interface node
        interface_node = self._create_java_interface_node(java_interface_node, parsed_file, package_node)
        queries.append(self.schema.get_cypher_create_node(interface_node))
        
        # Link file defines interface
        defines_rel = RelationshipProperties(
            type=RelationshipType.DEFINES_JAVA_INTERFACE,
            source_node_id=file_node.properties['id'],
            target_node_id=interface_node.properties['id']
        )
        queries.append(self.schema.get_cypher_create_relationship(defines_rel))
        self.created_relationships.append(defines_rel)
        
        # Process interface methods
        for child in java_interface_node.children:
            if child.node_type == 'MethodDeclaration':
                queries.extend(self._process_java_method(child, parsed_file, interface_node))
        
        return queries
    
    def _process_java_enum(self, java_enum_node: 'JavaNode', parsed_file: ParsedFile,
                          file_node: NodeProperties, package_node: Optional[NodeProperties]) -> List[str]:
        """
        Xử lý Java enum declaration.
        
        Args:
            java_enum_node: Java enum AST node
            parsed_file: Parsed file info
            file_node: File node
            package_node: Package node (nếu có)
            
        Returns:
            List[str]: Cypher queries
        """
        queries = []
        
        # Create Java enum node
        enum_node = self._create_java_enum_node(java_enum_node, parsed_file, package_node)
        queries.append(self.schema.get_cypher_create_node(enum_node))
        
        # Link file defines enum
        defines_rel = RelationshipProperties(
            type=RelationshipType.DEFINES_JAVA_CLASS,  # Enum is treated as special class
            source_node_id=file_node.properties['id'],
            target_node_id=enum_node.properties['id']
        )
        queries.append(self.schema.get_cypher_create_relationship(defines_rel))
        self.created_relationships.append(defines_rel)
        
        # Process enum constants
        for child in java_enum_node.children:
            if child.node_type == 'EnumConstantDeclaration':
                queries.extend(self._process_java_enum_constant(child, parsed_file, enum_node))
        
        return queries
    
    def _process_java_method(self, java_method_node: 'JavaNode', parsed_file: ParsedFile,
                            parent_node: NodeProperties) -> List[str]:
        """
        Xử lý Java method declaration.
        
        Args:
            java_method_node: Java method AST node
            parsed_file: Parsed file info
            parent_node: Parent node (class/interface)
            
        Returns:
            List[str]: Cypher queries
        """
        queries = []
        
        # Create Java method node
        method_node = self._create_java_method_node(java_method_node, parsed_file)
        queries.append(self.schema.get_cypher_create_node(method_node))
        
        # Link parent defines method
        defines_rel = RelationshipProperties(
            type=RelationshipType.DEFINES_JAVA_METHOD,
            source_node_id=parent_node.properties['id'],
            target_node_id=method_node.properties['id']
        )
        queries.append(self.schema.get_cypher_create_relationship(defines_rel))
        self.created_relationships.append(defines_rel)
        
        return queries
    
    def _process_java_field(self, java_field_node: 'JavaNode', parsed_file: ParsedFile,
                           parent_node: NodeProperties) -> List[str]:
        """
        Xử lý Java field declaration.
        
        Args:
            java_field_node: Java field AST node
            parsed_file: Parsed file info
            parent_node: Parent node (class)
            
        Returns:
            List[str]: Cypher queries
        """
        queries = []
        
        # Create Java field node
        field_node = self._create_java_field_node(java_field_node, parsed_file)
        queries.append(self.schema.get_cypher_create_node(field_node))
        
        # Link parent defines field
        defines_rel = RelationshipProperties(
            type=RelationshipType.DEFINES_JAVA_FIELD,
            source_node_id=parent_node.properties['id'],
            target_node_id=field_node.properties['id']
        )
        queries.append(self.schema.get_cypher_create_relationship(defines_rel))
        self.created_relationships.append(defines_rel)
        
        return queries
    
    def _process_java_constructor(self, java_constructor_node: 'JavaNode', parsed_file: ParsedFile,
                                 parent_node: NodeProperties) -> List[str]:
        """
        Xử lý Java constructor declaration.
        
        Args:
            java_constructor_node: Java constructor AST node
            parsed_file: Parsed file info
            parent_node: Parent node (class)
            
        Returns:
            List[str]: Cypher queries
        """
        queries = []
        
        # Create Java constructor node
        constructor_node = self._create_java_constructor_node(java_constructor_node, parsed_file)
        queries.append(self.schema.get_cypher_create_node(constructor_node))
        
        # Link parent defines constructor
        defines_rel = RelationshipProperties(
            type=RelationshipType.DEFINES_JAVA_CONSTRUCTOR,
            source_node_id=parent_node.properties['id'],
            target_node_id=constructor_node.properties['id']
        )
        queries.append(self.schema.get_cypher_create_relationship(defines_rel))
        self.created_relationships.append(defines_rel)
        
        return queries
    
    def _process_java_enum_constant(self, java_enum_const_node: 'JavaNode', parsed_file: ParsedFile,
                                   parent_node: NodeProperties) -> List[str]:
        """
        Xử lý Java enum constant declaration.
        
        Args:
            java_enum_const_node: Java enum constant AST node
            parsed_file: Parsed file info
            parent_node: Parent node (enum)
            
        Returns:
            List[str]: Cypher queries
        """
        queries = []
        
        # Create Java enum constant node
        enum_const_node = self._create_java_enum_constant_node(java_enum_const_node, parsed_file)
        queries.append(self.schema.get_cypher_create_node(enum_const_node))
        
        # Link parent contains enum constant
        contains_rel = RelationshipProperties(
            type=RelationshipType.CONTAINS,
            source_node_id=parent_node.properties['id'],
            target_node_id=enum_const_node.properties['id']
        )
        queries.append(self.schema.get_cypher_create_relationship(contains_rel))
        self.created_relationships.append(contains_rel)
        
        return queries

    # Java Node Creation Methods
    
    def _create_java_package_node(self, package_name: str, parsed_file: ParsedFile) -> NodeProperties:
        """Tạo Java Package node."""
        node_id = self._generate_node_id(NodeType.JAVA_PACKAGE, parsed_file.file_path, 1, package_name)
        
        properties = {
            'id': node_id,
            'full_name': package_name,
        }
        
        package_node = NodeProperties(
            name=package_name.split('.')[-1],  # Last part of package name
            type=NodeType.JAVA_PACKAGE,
            file_path=parsed_file.file_path,
            line_number=1,
            properties=properties
        )
        
        self.created_nodes[node_id] = package_node
        return package_node
    
    def _create_java_import_node(self, import_name: str, parsed_file: ParsedFile) -> NodeProperties:
        """Tạo Java Import node."""
        node_id = self._generate_node_id(NodeType.JAVA_IMPORT, parsed_file.file_path, 1, import_name)
        
        properties = {
            'id': node_id,
            'imported_name': import_name,
            'is_static_import': 'static' in import_name,
            'is_wildcard_import': import_name.endswith('*')
        }
        
        import_node = NodeProperties(
            name=import_name.split('.')[-1],  # Last part of import
            type=NodeType.JAVA_IMPORT,
            file_path=parsed_file.file_path,
            line_number=1,
            properties=properties
        )
        
        self.created_nodes[node_id] = import_node
        return import_node
    
    def _create_java_class_node(self, java_class_node: 'JavaNode', parsed_file: ParsedFile,
                               package_node: Optional[NodeProperties]) -> NodeProperties:
        """Tạo Java Class node."""
        class_name = java_class_node.name or "AnonymousClass"
        node_id = self._generate_node_id(NodeType.JAVA_CLASS, parsed_file.file_path, 
                                        java_class_node.start_line, class_name)
        
        # Extract class information
        package_name = package_node.name if package_node else ""
        full_name = f"{package_name}.{class_name}" if package_name else class_name
        
        # Count methods, fields, constructors
        methods_count = len([c for c in java_class_node.children if c.node_type == 'MethodDeclaration'])
        fields_count = len([c for c in java_class_node.children if c.node_type == 'FieldDeclaration'])
        constructors_count = len([c for c in java_class_node.children if c.node_type == 'ConstructorDeclaration'])
        
        properties = {
            'id': node_id,
            'package_name': package_name,
            'full_name': full_name,
            'modifiers': java_class_node.modifiers,
            'is_abstract': 'abstract' in java_class_node.modifiers,
            'is_final': 'final' in java_class_node.modifiers,
            'is_static': 'static' in java_class_node.modifiers,
            'methods_count': methods_count,
            'fields_count': fields_count,
            'constructors_count': constructors_count
        }
        
        class_node = NodeProperties(
            name=class_name,
            type=NodeType.JAVA_CLASS,
            file_path=parsed_file.file_path,
            line_number=java_class_node.start_line,
            end_line_number=java_class_node.end_line,
            properties=properties
        )
        
        self.created_nodes[node_id] = class_node
        return class_node
    
    def _create_java_interface_node(self, java_interface_node: 'JavaNode', parsed_file: ParsedFile,
                                   package_node: Optional[NodeProperties]) -> NodeProperties:
        """Tạo Java Interface node."""
        interface_name = java_interface_node.name or "AnonymousInterface"
        node_id = self._generate_node_id(NodeType.JAVA_INTERFACE, parsed_file.file_path,
                                        java_interface_node.start_line, interface_name)
        
        package_name = package_node.name if package_node else ""
        full_name = f"{package_name}.{interface_name}" if package_name else interface_name
        
        methods_count = len([c for c in java_interface_node.children if c.node_type == 'MethodDeclaration'])
        
        properties = {
            'id': node_id,
            'package_name': package_name,
            'full_name': full_name,
            'modifiers': java_interface_node.modifiers,
            'methods_count': methods_count
        }
        
        interface_node = NodeProperties(
            name=interface_name,
            type=NodeType.JAVA_INTERFACE,
            file_path=parsed_file.file_path,
            line_number=java_interface_node.start_line,
            end_line_number=java_interface_node.end_line,
            properties=properties
        )
        
        self.created_nodes[node_id] = interface_node
        return interface_node
    
    def _create_java_enum_node(self, java_enum_node: 'JavaNode', parsed_file: ParsedFile,
                              package_node: Optional[NodeProperties]) -> NodeProperties:
        """Tạo Java Enum node."""
        enum_name = java_enum_node.name or "AnonymousEnum"
        node_id = self._generate_node_id(NodeType.JAVA_ENUM, parsed_file.file_path,
                                        java_enum_node.start_line, enum_name)
        
        package_name = package_node.name if package_node else ""
        full_name = f"{package_name}.{enum_name}" if package_name else enum_name
        
        constants_count = len([c for c in java_enum_node.children if c.node_type == 'EnumConstantDeclaration'])
        methods_count = len([c for c in java_enum_node.children if c.node_type == 'MethodDeclaration'])
        
        properties = {
            'id': node_id,
            'package_name': package_name,
            'full_name': full_name,
            'modifiers': java_enum_node.modifiers,
            'constants_count': constants_count,
            'methods_count': methods_count
        }
        
        enum_node = NodeProperties(
            name=enum_name,
            type=NodeType.JAVA_ENUM,
            file_path=parsed_file.file_path,
            line_number=java_enum_node.start_line,
            end_line_number=java_enum_node.end_line,
            properties=properties
        )
        
        self.created_nodes[node_id] = enum_node
        return enum_node
    
    def _create_java_method_node(self, java_method_node: 'JavaNode', parsed_file: ParsedFile) -> NodeProperties:
        """Tạo Java Method node."""
        method_name = java_method_node.name or "anonymousMethod"
        node_id = self._generate_node_id(NodeType.JAVA_METHOD, parsed_file.file_path,
                                        java_method_node.start_line, method_name)
        
        # Extract method information
        return_type = java_method_node.metadata.get('return_type', 'void') if java_method_node.metadata else 'void'
        parameters = java_method_node.metadata.get('parameters', []) if java_method_node.metadata else []
        
        properties = {
            'id': node_id,
            'modifiers': java_method_node.modifiers,
            'return_type': return_type,
            'parameters': parameters,
            'is_abstract': 'abstract' in java_method_node.modifiers,
            'is_static': 'static' in java_method_node.modifiers,
            'is_final': 'final' in java_method_node.modifiers,
            'is_synchronized': 'synchronized' in java_method_node.modifiers,
            'is_native': 'native' in java_method_node.modifiers
        }
        
        method_node = NodeProperties(
            name=method_name,
            type=NodeType.JAVA_METHOD,
            file_path=parsed_file.file_path,
            line_number=java_method_node.start_line,
            end_line_number=java_method_node.end_line,
            properties=properties
        )
        
        self.created_nodes[node_id] = method_node
        return method_node
    
    def _create_java_field_node(self, java_field_node: 'JavaNode', parsed_file: ParsedFile) -> NodeProperties:
        """Tạo Java Field node."""
        field_name = java_field_node.name or "anonymousField"
        node_id = self._generate_node_id(NodeType.JAVA_FIELD, parsed_file.file_path,
                                        java_field_node.start_line, field_name)
        
        field_type = java_field_node.metadata.get('field_type', 'Object') if java_field_node.metadata else 'Object'
        
        properties = {
            'id': node_id,
            'field_type': field_type,
            'modifiers': java_field_node.modifiers,
            'is_static': 'static' in java_field_node.modifiers,
            'is_final': 'final' in java_field_node.modifiers,
            'is_volatile': 'volatile' in java_field_node.modifiers,
            'is_transient': 'transient' in java_field_node.modifiers
        }
        
        field_node = NodeProperties(
            name=field_name,
            type=NodeType.JAVA_FIELD,
            file_path=parsed_file.file_path,
            line_number=java_field_node.start_line,
            end_line_number=java_field_node.end_line,
            properties=properties
        )
        
        self.created_nodes[node_id] = field_node
        return field_node
    
    def _create_java_constructor_node(self, java_constructor_node: 'JavaNode', parsed_file: ParsedFile) -> NodeProperties:
        """Tạo Java Constructor node."""
        constructor_name = java_constructor_node.name or "Constructor"
        node_id = self._generate_node_id(NodeType.JAVA_CONSTRUCTOR, parsed_file.file_path,
                                        java_constructor_node.start_line, constructor_name)
        
        parameters = java_constructor_node.metadata.get('parameters', []) if java_constructor_node.metadata else []
        
        properties = {
            'id': node_id,
            'modifiers': java_constructor_node.modifiers,
            'parameters': parameters
        }
        
        constructor_node = NodeProperties(
            name=constructor_name,
            type=NodeType.JAVA_CONSTRUCTOR,
            file_path=parsed_file.file_path,
            line_number=java_constructor_node.start_line,
            end_line_number=java_constructor_node.end_line,
            properties=properties
        )
        
        self.created_nodes[node_id] = constructor_node
        return constructor_node
    
    def _create_java_enum_constant_node(self, java_enum_const_node: 'JavaNode', parsed_file: ParsedFile) -> NodeProperties:
        """Tạo Java Enum Constant node."""
        const_name = java_enum_const_node.name or "UNKNOWN_CONSTANT"
        node_id = self._generate_node_id(NodeType.JAVA_ENUM_CONSTANT, parsed_file.file_path,
                                        java_enum_const_node.start_line, const_name)
        
        arguments = java_enum_const_node.metadata.get('arguments', []) if java_enum_const_node.metadata else []
        ordinal = java_enum_const_node.metadata.get('ordinal', 0) if java_enum_const_node.metadata else 0
        
        properties = {
            'id': node_id,
            'arguments': arguments,
            'ordinal': ordinal
        }
        
        enum_const_node = NodeProperties(
            name=const_name,
            type=NodeType.JAVA_ENUM_CONSTANT,
            file_path=parsed_file.file_path,
            line_number=java_enum_const_node.start_line,
            end_line_number=java_enum_const_node.end_line,
            properties=properties
        )
        
        self.created_nodes[node_id] = enum_const_node
        return enum_const_node

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

    def _process_dart_file(self, parsed_file: ParsedFile, file_node: NodeProperties) -> List[str]:
        """
        Xử lý Dart file và convert thành CKG nodes.
        
        Args:
            parsed_file: ParsedFile object chứa Dart AST data
            file_node: File node đã được tạo
            
        Returns:
            List[str]: Danh sách Cypher queries
        """
        queries = []
        
        try:
            # Check if AST is DartParseInfo
            if isinstance(parsed_file.ast_tree, DartParseInfo):
                dart_ast = parsed_file.ast_tree
                queries.extend(self._process_dart_ast(dart_ast, parsed_file, file_node))
            else:
                logger.warning(f"Unknown Dart AST type: {type(parsed_file.ast_tree)}")
                
        except Exception as e:
            logger.error(f"Error processing Dart file {parsed_file.file_path}: {str(e)}")
            
        return queries
    
    def _process_dart_ast(self, dart_ast: 'DartParseInfo', parsed_file: ParsedFile, file_node: NodeProperties) -> List[str]:
        """
        Xử lý Dart AST và tạo CKG nodes.
        
        Args:
            dart_ast: DartParseInfo object chứa parsed data
            parsed_file: ParsedFile container
            file_node: File node properties
            
        Returns:
            List[str]: Cypher queries
        """
        queries = []
        
        try:
            # Tạo library node nếu có
            library_node = None
            if dart_ast.library_name:
                library_node = self._create_dart_library_node(dart_ast.library_name, parsed_file)
                queries.append(self.schema.get_cypher_create_node(library_node))
                
                # Tạo relationship từ file đến library
                lib_rel = RelationshipProperties(
                    type=RelationshipType.CONTAINS,
                    source_node_id=file_node.properties['id'],
                    target_node_id=library_node.properties['id']
                )
                self.created_relationships.append(lib_rel)
                queries.append(self.schema.get_cypher_create_relationship(lib_rel))
            
            # Process imports
            for import_name in dart_ast.imports:
                import_node = self._create_dart_import_node(import_name, parsed_file)
                queries.append(self.schema.get_cypher_create_node(import_node))
                
                # Relationship từ file đến import
                import_rel = RelationshipProperties(
                    type=RelationshipType.IMPORTS,
                    source_node_id=file_node.properties['id'],
                    target_node_id=import_node.properties['id']
                )
                self.created_relationships.append(import_rel)
                queries.append(self.schema.get_cypher_create_relationship(import_rel))
            
            # Process exports  
            for export_name in dart_ast.exports:
                export_node = self._create_dart_export_node(export_name, parsed_file)
                queries.append(self.schema.get_cypher_create_node(export_node))
                
                # Relationship từ file đến export
                export_rel = RelationshipProperties(
                    type=RelationshipType.DART_EXPORTS,
                    source_node_id=file_node.properties['id'],
                    target_node_id=export_node.properties['id']
                )
                self.created_relationships.append(export_rel)
                queries.append(self.schema.get_cypher_create_relationship(export_rel))
            
            # Process classes
            for class_name in dart_ast.classes:
                class_node = self._create_dart_class_node(class_name, parsed_file, library_node)
                queries.append(self.schema.get_cypher_create_node(class_node))
                
                # Relationship từ library hoặc file đến class
                parent_node = library_node if library_node else file_node
                class_rel = RelationshipProperties(
                    type=RelationshipType.DEFINES_DART_CLASS,
                    source_node_id=parent_node.properties['id'],
                    target_node_id=class_node.properties['id']
                )
                self.created_relationships.append(class_rel)
                queries.append(self.schema.get_cypher_create_relationship(class_rel))
            
            # Process mixins
            for mixin_name in dart_ast.mixins:
                mixin_node = self._create_dart_mixin_node(mixin_name, parsed_file, library_node)
                queries.append(self.schema.get_cypher_create_node(mixin_node))
                
                # Relationship từ library hoặc file đến mixin
                parent_node = library_node if library_node else file_node
                mixin_rel = RelationshipProperties(
                    type=RelationshipType.DEFINES_DART_MIXIN,
                    source_node_id=parent_node.properties['id'],
                    target_node_id=mixin_node.properties['id']
                )
                self.created_relationships.append(mixin_rel)
                queries.append(self.schema.get_cypher_create_relationship(mixin_rel))
            
            # Process extensions
            for extension_name in dart_ast.extensions:
                extension_node = self._create_dart_extension_node(extension_name, parsed_file, library_node)
                queries.append(self.schema.get_cypher_create_node(extension_node))
                
                # Relationship từ library hoặc file đến extension
                parent_node = library_node if library_node else file_node
                extension_rel = RelationshipProperties(
                    type=RelationshipType.DEFINES_DART_EXTENSION,
                    source_node_id=parent_node.properties['id'],
                    target_node_id=extension_node.properties['id']
                )
                self.created_relationships.append(extension_rel)
                queries.append(self.schema.get_cypher_create_relationship(extension_rel))
            
            # Process functions
            for function_name in dart_ast.functions:
                function_node = self._create_dart_function_node(function_name, parsed_file, library_node)
                queries.append(self.schema.get_cypher_create_node(function_node))
                
                # Relationship từ library hoặc file đến function
                parent_node = library_node if library_node else file_node
                function_rel = RelationshipProperties(
                    type=RelationshipType.DEFINES_DART_FUNCTION,
                    source_node_id=parent_node.properties['id'],
                    target_node_id=function_node.properties['id']
                )
                self.created_relationships.append(function_rel)
                queries.append(self.schema.get_cypher_create_relationship(function_rel))
            
            # Process enums
            for enum_name in dart_ast.enums:
                enum_node = self._create_dart_enum_node(enum_name, parsed_file, library_node)
                queries.append(self.schema.get_cypher_create_node(enum_node))
                
                # Relationship từ library hoặc file đến enum
                parent_node = library_node if library_node else file_node
                enum_rel = RelationshipProperties(
                    type=RelationshipType.DEFINES_DART_ENUM,
                    source_node_id=parent_node.properties['id'],
                    target_node_id=enum_node.properties['id']
                )
                self.created_relationships.append(enum_rel)
                queries.append(self.schema.get_cypher_create_relationship(enum_rel))
            
            # Process typedefs
            for typedef_name in dart_ast.typedefs:
                typedef_node = self._create_dart_typedef_node(typedef_name, parsed_file, library_node)
                queries.append(self.schema.get_cypher_create_node(typedef_node))
                
                # Relationship từ library hoặc file đến typedef
                parent_node = library_node if library_node else file_node
                typedef_rel = RelationshipProperties(
                    type=RelationshipType.DEFINES_DART_TYPEDEF,
                    source_node_id=parent_node.properties['id'],
                    target_node_id=typedef_node.properties['id']
                )
                self.created_relationships.append(typedef_rel)
                queries.append(self.schema.get_cypher_create_relationship(typedef_rel))
                
        except Exception as e:
            logger.error(f"Error processing Dart AST: {str(e)}")
            
        return queries

    # Dart node creation helpers
    
    def _create_dart_library_node(self, library_name: str, parsed_file: ParsedFile) -> NodeProperties:
        """Tạo Dart library node."""
        node_id = self._generate_node_id(NodeType.DART_LIBRARY, parsed_file.file_path, 1, library_name)
        
        node = NodeProperties(
            name=library_name,
            type=NodeType.DART_LIBRARY,
            file_path=parsed_file.file_path,
            line_number=1,
            properties={
                'id': node_id,
                'full_name': library_name
            }
        )
        
        self.created_nodes[node_id] = node
        return node
    
    def _create_dart_import_node(self, import_name: str, parsed_file: ParsedFile) -> NodeProperties:
        """Tạo Dart import node."""
        node_id = self._generate_node_id(NodeType.DART_IMPORT, parsed_file.file_path, 1, import_name)
        
        # Parse import URI 
        is_package_import = import_name.startswith('package:')
        is_relative_import = import_name.startswith('./') or import_name.startswith('../')
        
        node = NodeProperties(
            name=import_name,
            type=NodeType.DART_IMPORT,
            file_path=parsed_file.file_path,
            line_number=1,
            properties={
                'id': node_id,
                'imported_name': import_name,
                'is_package_import': is_package_import,
                'is_relative_import': is_relative_import
            }
        )
        
        self.created_nodes[node_id] = node
        return node
    
    def _create_dart_export_node(self, export_name: str, parsed_file: ParsedFile) -> NodeProperties:
        """Tạo Dart export node."""
        node_id = self._generate_node_id(NodeType.DART_EXPORT, parsed_file.file_path, 1, export_name)
        
        node = NodeProperties(
            name=export_name,
            type=NodeType.DART_EXPORT,
            file_path=parsed_file.file_path,
            line_number=1,
            properties={
                'id': node_id,
                'full_name': export_name
            }
        )
        
        self.created_nodes[node_id] = node
        return node
    
    def _create_dart_class_node(self, class_name: str, parsed_file: ParsedFile, library_node: Optional[NodeProperties]) -> NodeProperties:
        """Tạo Dart class node."""
        node_id = self._generate_node_id(NodeType.DART_CLASS, parsed_file.file_path, 1, class_name)
        
        library_name = library_node.name if library_node else None
        full_name = f"{library_name}.{class_name}" if library_name else class_name
        
        node = NodeProperties(
            name=class_name,
            type=NodeType.DART_CLASS,
            file_path=parsed_file.file_path,
            line_number=1,
            properties={
                'id': node_id,
                'package_name': library_name,
                'full_name': full_name,
                'is_abstract': False,
                'methods_count': 0,
                'fields_count': 0,
                'constructors_count': 0
            }
        )
        
        self.created_nodes[node_id] = node
        return node
    
    def _create_dart_mixin_node(self, mixin_name: str, parsed_file: ParsedFile, library_node: Optional[NodeProperties]) -> NodeProperties:
        """Tạo Dart mixin node."""
        node_id = self._generate_node_id(NodeType.DART_MIXIN, parsed_file.file_path, 1, mixin_name)
        
        library_name = library_node.name if library_node else None
        full_name = f"{library_name}.{mixin_name}" if library_name else mixin_name
        
        node = NodeProperties(
            name=mixin_name,
            type=NodeType.DART_MIXIN,
            file_path=parsed_file.file_path,
            line_number=1,
            properties={
                'id': node_id,
                'package_name': library_name,
                'full_name': full_name,
                'methods_count': 0
            }
        )
        
        self.created_nodes[node_id] = node
        return node
    
    def _create_dart_extension_node(self, extension_name: str, parsed_file: ParsedFile, library_node: Optional[NodeProperties]) -> NodeProperties:
        """Tạo Dart extension node."""
        node_id = self._generate_node_id(NodeType.DART_EXTENSION, parsed_file.file_path, 1, extension_name)
        
        library_name = library_node.name if library_node else None
        full_name = f"{library_name}.{extension_name}" if library_name else extension_name
        
        node = NodeProperties(
            name=extension_name,
            type=NodeType.DART_EXTENSION,
            file_path=parsed_file.file_path,
            line_number=1,
            properties={
                'id': node_id,
                'package_name': library_name,
                'full_name': full_name,
                'methods_count': 0
            }
        )
        
        self.created_nodes[node_id] = node
        return node
    
    def _create_dart_function_node(self, function_name: str, parsed_file: ParsedFile, library_node: Optional[NodeProperties]) -> NodeProperties:
        """Tạo Dart function node."""
        node_id = self._generate_node_id(NodeType.DART_FUNCTION, parsed_file.file_path, 1, function_name)
        
        library_name = library_node.name if library_node else None
        full_name = f"{library_name}.{function_name}" if library_name else function_name
        
        node = NodeProperties(
            name=function_name,
            type=NodeType.DART_FUNCTION,
            file_path=parsed_file.file_path,
            line_number=1,
            properties={
                'id': node_id,
                'package_name': library_name,
                'full_name': full_name,
                'is_async': False,
                'parameters_count': 0
            }
        )
        
        self.created_nodes[node_id] = node
        return node
    
    def _create_dart_enum_node(self, enum_name: str, parsed_file: ParsedFile, library_node: Optional[NodeProperties]) -> NodeProperties:
        """Tạo Dart enum node."""
        node_id = self._generate_node_id(NodeType.DART_ENUM, parsed_file.file_path, 1, enum_name)
        
        properties = {
            'id': node_id,
            'package_name': library_node.name if library_node else '',
            'full_name': f"{library_node.name}.{enum_name}" if library_node else enum_name,
            'modifiers': ['enum'],
            'implements_interfaces': [],
            'constants_count': 0,
            'methods_count': 0
        }
        
        return NodeProperties(
            name=enum_name,
            type=NodeType.DART_ENUM,
            file_path=parsed_file.file_path,
            line_number=1,
            properties=properties
        )
    
    def _create_dart_typedef_node(self, typedef_name: str, parsed_file: ParsedFile, library_node: Optional[NodeProperties]) -> NodeProperties:
        """Tạo Dart typedef node."""
        node_id = self._generate_node_id(NodeType.DART_TYPEDEF, parsed_file.file_path, 1, typedef_name)
        
        library_name = library_node.name if library_node else None
        full_name = f"{library_name}.{typedef_name}" if library_name else typedef_name
        
        node = NodeProperties(
            name=typedef_name,
            type=NodeType.DART_TYPEDEF,
            file_path=parsed_file.file_path,
            line_number=1,
            properties={
                'id': node_id,
                'package_name': library_name,
                'full_name': full_name
            }
        )
        
        self.created_nodes[node_id] = node
        return node

    # ===============================
    # Kotlin Processing Methods
    # ===============================
    
    def _process_kotlin_file(self, parsed_file: ParsedFile, file_node: NodeProperties) -> List[str]:
        """
        Xử lý Kotlin file AST.
        
        Args:
            parsed_file: Parsed Kotlin file
            file_node: File node đã tạo
            
        Returns:
            List[str]: Danh sách Cypher queries
        """
        queries = []
        
        try:
            # Import Kotlin classes safely
            try:
                from agents.ckg_operations.kotlin_parser import KotlinParseInfo
            except ImportError:
                logger.warning("KotlinParseInfo not available - skipping Kotlin file processing")
                return queries
            
            kotlin_ast = parsed_file.ast_tree
            if not isinstance(kotlin_ast, KotlinParseInfo):
                logger.warning(f"Expected KotlinParseInfo, got {type(kotlin_ast)}")
                return queries
            
            # Process Kotlin AST structure
            queries.extend(self._process_kotlin_ast(kotlin_ast, parsed_file, file_node))
            
        except Exception as e:
            logger.error(f"Error processing Kotlin file {parsed_file.relative_path}: {e}")
        
        return queries
    
    def _process_kotlin_ast(self, kotlin_ast: 'KotlinParseInfo', parsed_file: ParsedFile, file_node: NodeProperties) -> List[str]:
        """
        Xử lý Kotlin AST structure.
        
        Args:
            kotlin_ast: Kotlin AST parse info
            parsed_file: Parsed file info
            file_node: File node đã tạo
            
        Returns:
            List[str]: Cypher queries
        """
        queries = []
        
        try:
            # Extract package information
            package_node = None
            if kotlin_ast.package_name:
                package_node = self._create_kotlin_package_node(
                    kotlin_ast.package_name, 
                    parsed_file
                )
                queries.append(self.schema.get_cypher_create_node(package_node))
                
                # Link file to package
                belongs_to_rel = RelationshipProperties(
                    type=RelationshipType.BELONGS_TO,
                    source_node_id=file_node.properties['id'],
                    target_node_id=package_node.properties['id']
                )
                queries.append(self.schema.get_cypher_create_relationship(belongs_to_rel))
                self.created_relationships.append(belongs_to_rel)
            
            # Process imports
            if kotlin_ast.imports:
                for import_info in kotlin_ast.imports:
                    import_name = import_info.name if hasattr(import_info, 'name') else str(import_info)
                    import_node = self._create_kotlin_import_node(import_name, parsed_file)
                    queries.append(self.schema.get_cypher_create_node(import_node))
                    
                    # Link file to import
                    imports_rel = RelationshipProperties(
                        type=RelationshipType.IMPORTS,
                        source_node_id=file_node.properties['id'],
                        target_node_id=import_node.properties['id']
                    )
                    queries.append(self.schema.get_cypher_create_relationship(imports_rel))
                    self.created_relationships.append(imports_rel)
            
            # Process classes
            if kotlin_ast.classes:
                for class_info in kotlin_ast.classes:
                    class_name = class_info.name if hasattr(class_info, 'name') else str(class_info)
                    queries.extend(self._process_kotlin_class(class_name, parsed_file, file_node, package_node))
            
            # Process data classes
            if kotlin_ast.data_classes:
                for data_class_info in kotlin_ast.data_classes:
                    data_class_name = data_class_info.name if hasattr(data_class_info, 'name') else str(data_class_info)
                    queries.extend(self._process_kotlin_data_class(data_class_name, parsed_file, file_node, package_node))
            
            # Process interfaces
            if kotlin_ast.interfaces:
                for interface_info in kotlin_ast.interfaces:
                    interface_name = interface_info.name if hasattr(interface_info, 'name') else str(interface_info)
                    queries.extend(self._process_kotlin_interface(interface_name, parsed_file, file_node, package_node))
            
            # Process objects
            if kotlin_ast.objects:
                for object_info in kotlin_ast.objects:
                    object_name = object_info.name if hasattr(object_info, 'name') else str(object_info)
                    queries.extend(self._process_kotlin_object(object_name, parsed_file, file_node, package_node))
            
            # Process functions
            if kotlin_ast.functions:
                for function_info in kotlin_ast.functions:
                    function_name = function_info.name if hasattr(function_info, 'name') else str(function_info)
                    queries.extend(self._process_kotlin_function(function_name, parsed_file, file_node, package_node))
            
            # Process enums
            if kotlin_ast.enums:
                for enum_info in kotlin_ast.enums:
                    enum_name = enum_info.name if hasattr(enum_info, 'name') else str(enum_info)
                    queries.extend(self._process_kotlin_enum(enum_name, parsed_file, file_node, package_node))
            
        except Exception as e:
            logger.error(f"Error processing Kotlin AST: {e}")
        
        return queries
    
    def _process_kotlin_class(self, class_name: str, parsed_file: ParsedFile,
                             file_node: NodeProperties, package_node: Optional[NodeProperties]) -> List[str]:
        """Process Kotlin class declaration."""
        queries = []
        
        # Create Kotlin class node
        class_node = self._create_kotlin_class_node(class_name, parsed_file, package_node)
        queries.append(self.schema.get_cypher_create_node(class_node))
        
        # Link file defines class
        defines_rel = RelationshipProperties(
            type=RelationshipType.DEFINES_KOTLIN_CLASS,
            source_node_id=file_node.properties['id'],
            target_node_id=class_node.properties['id']
        )
        queries.append(self.schema.get_cypher_create_relationship(defines_rel))
        self.created_relationships.append(defines_rel)
        
        return queries
    
    def _process_kotlin_data_class(self, data_class_name: str, parsed_file: ParsedFile,
                                  file_node: NodeProperties, package_node: Optional[NodeProperties]) -> List[str]:
        """Process Kotlin data class declaration."""
        queries = []
        
        # Create Kotlin data class node
        data_class_node = self._create_kotlin_data_class_node(data_class_name, parsed_file, package_node)
        queries.append(self.schema.get_cypher_create_node(data_class_node))
        
        # Link file defines data class
        defines_rel = RelationshipProperties(
            type=RelationshipType.DEFINES_KOTLIN_DATA_CLASS,
            source_node_id=file_node.properties['id'],
            target_node_id=data_class_node.properties['id']
        )
        queries.append(self.schema.get_cypher_create_relationship(defines_rel))
        self.created_relationships.append(defines_rel)
        
        return queries
    
    def _process_kotlin_interface(self, interface_name: str, parsed_file: ParsedFile,
                                 file_node: NodeProperties, package_node: Optional[NodeProperties]) -> List[str]:
        """Process Kotlin interface declaration."""
        queries = []
        
        # Create Kotlin interface node
        interface_node = self._create_kotlin_interface_node(interface_name, parsed_file, package_node)
        queries.append(self.schema.get_cypher_create_node(interface_node))
        
        # Link file defines interface
        defines_rel = RelationshipProperties(
            type=RelationshipType.DEFINES_KOTLIN_INTERFACE,
            source_node_id=file_node.properties['id'],
            target_node_id=interface_node.properties['id']
        )
        queries.append(self.schema.get_cypher_create_relationship(defines_rel))
        self.created_relationships.append(defines_rel)
        
        return queries
    
    def _process_kotlin_object(self, object_name: str, parsed_file: ParsedFile,
                              file_node: NodeProperties, package_node: Optional[NodeProperties]) -> List[str]:
        """Process Kotlin object declaration."""
        queries = []
        
        # Create Kotlin object node
        object_node = self._create_kotlin_object_node(object_name, parsed_file, package_node)
        queries.append(self.schema.get_cypher_create_node(object_node))
        
        # Link file defines object
        defines_rel = RelationshipProperties(
            type=RelationshipType.DEFINES_KOTLIN_OBJECT,
            source_node_id=file_node.properties['id'],
            target_node_id=object_node.properties['id']
        )
        queries.append(self.schema.get_cypher_create_relationship(defines_rel))
        self.created_relationships.append(defines_rel)
        
        return queries
    
    def _process_kotlin_function(self, function_name: str, parsed_file: ParsedFile,
                                file_node: NodeProperties, package_node: Optional[NodeProperties]) -> List[str]:
        """Process Kotlin function declaration."""
        queries = []
        
        # Create Kotlin function node
        function_node = self._create_kotlin_function_node(function_name, parsed_file, package_node)
        queries.append(self.schema.get_cypher_create_node(function_node))
        
        # Link file defines function
        defines_rel = RelationshipProperties(
            type=RelationshipType.DEFINES_KOTLIN_FUNCTION,
            source_node_id=file_node.properties['id'],
            target_node_id=function_node.properties['id']
        )
        queries.append(self.schema.get_cypher_create_relationship(defines_rel))
        self.created_relationships.append(defines_rel)
        
        return queries
    
    def _process_kotlin_enum(self, enum_name: str, parsed_file: ParsedFile,
                            file_node: NodeProperties, package_node: Optional[NodeProperties]) -> List[str]:
        """Process Kotlin enum declaration."""
        queries = []
        
        # Create Kotlin enum node
        enum_node = self._create_kotlin_enum_node(enum_name, parsed_file, package_node)
        queries.append(self.schema.get_cypher_create_node(enum_node))
        
        # Link file defines enum
        defines_rel = RelationshipProperties(
            type=RelationshipType.DEFINES_KOTLIN_ENUM,
            source_node_id=file_node.properties['id'],
            target_node_id=enum_node.properties['id']
        )
        queries.append(self.schema.get_cypher_create_relationship(defines_rel))
        self.created_relationships.append(defines_rel)
        
        return queries

    # Kotlin Node Creation Methods
    
    def _create_kotlin_package_node(self, package_name: str, parsed_file: ParsedFile) -> NodeProperties:
        """Create Kotlin package node."""
        node_id = self._generate_node_id(NodeType.KOTLIN_PACKAGE, parsed_file.file_path, 1, package_name)
        
        properties = {
            'id': node_id,
            'full_name': package_name,
            'classes_count': 0,
            'interfaces_count': 0
        }
        
        return NodeProperties(
            name=package_name,
            type=NodeType.KOTLIN_PACKAGE,
            file_path=parsed_file.file_path,
            line_number=1,
            properties=properties
        )
    
    def _create_kotlin_import_node(self, import_name: str, parsed_file: ParsedFile) -> NodeProperties:
        """Create Kotlin import node."""
        node_id = self._generate_node_id(NodeType.KOTLIN_IMPORT, parsed_file.file_path, 1, import_name)
        
        properties = {
            'id': node_id,
            'imported_name': import_name,
            'is_static_import': False,
            'is_wildcard_import': '*' in import_name
        }
        
        return NodeProperties(
            name=import_name,
            type=NodeType.KOTLIN_IMPORT,
            file_path=parsed_file.file_path,
            line_number=1,
            properties=properties
        )
    
    def _create_kotlin_class_node(self, class_name: str, parsed_file: ParsedFile,
                                 package_node: Optional[NodeProperties]) -> NodeProperties:
        """Create Kotlin class node."""
        node_id = self._generate_node_id(NodeType.KOTLIN_CLASS, parsed_file.file_path, 1, class_name)
        
        properties = {
            'id': node_id,
            'package_name': package_node.name if package_node else '',
            'full_name': f"{package_node.name}.{class_name}" if package_node else class_name,
            'modifiers': [],
            'is_abstract': False,
            'is_final': False,
            'is_static': False,
            'extends_class': '',
            'implements_interfaces': [],
            'methods_count': 0,
            'fields_count': 0,
            'constructors_count': 0
        }
        
        return NodeProperties(
            name=class_name,
            type=NodeType.KOTLIN_CLASS,
            file_path=parsed_file.file_path,
            line_number=1,
            properties=properties
        )
    
    def _create_kotlin_data_class_node(self, data_class_name: str, parsed_file: ParsedFile,
                                      package_node: Optional[NodeProperties]) -> NodeProperties:
        """Create Kotlin data class node."""
        node_id = self._generate_node_id(NodeType.KOTLIN_DATA_CLASS, parsed_file.file_path, 1, data_class_name)
        
        properties = {
            'id': node_id,
            'package_name': package_node.name if package_node else '',
            'full_name': f"{package_node.name}.{data_class_name}" if package_node else data_class_name,
            'modifiers': ['data'],
            'is_abstract': False,
            'is_final': True,  # Data classes are final by default
            'is_static': False,
            'extends_class': '',
            'implements_interfaces': [],
            'methods_count': 0,
            'fields_count': 0,
            'constructors_count': 1  # Data classes have primary constructor
        }
        
        return NodeProperties(
            name=data_class_name,
            type=NodeType.KOTLIN_DATA_CLASS,
            file_path=parsed_file.file_path,
            line_number=1,
            properties=properties
        )
    
    def _create_kotlin_interface_node(self, interface_name: str, parsed_file: ParsedFile,
                                     package_node: Optional[NodeProperties]) -> NodeProperties:
        """Create Kotlin interface node."""
        node_id = self._generate_node_id(NodeType.KOTLIN_INTERFACE, parsed_file.file_path, 1, interface_name)
        
        properties = {
            'id': node_id,
            'package_name': package_node.name if package_node else '',
            'full_name': f"{package_node.name}.{interface_name}" if package_node else interface_name,
            'modifiers': [],
            'extends_interfaces': [],
            'methods_count': 0,
            'fields_count': 0
        }
        
        return NodeProperties(
            name=interface_name,
            type=NodeType.KOTLIN_INTERFACE,
            file_path=parsed_file.file_path,
            line_number=1,
            properties=properties
        )
    
    def _create_kotlin_object_node(self, object_name: str, parsed_file: ParsedFile,
                                  package_node: Optional[NodeProperties]) -> NodeProperties:
        """Create Kotlin object node."""
        node_id = self._generate_node_id(NodeType.KOTLIN_OBJECT, parsed_file.file_path, 1, object_name)
        
        properties = {
            'id': node_id,
            'package_name': package_node.name if package_node else '',
            'full_name': f"{package_node.name}.{object_name}" if package_node else object_name,
            'modifiers': ['object'],
            'is_abstract': False,
            'is_final': True,  # Objects are final
            'is_static': True,   # Objects are singleton
            'extends_class': '',
            'implements_interfaces': [],
            'methods_count': 0,
            'fields_count': 0,
            'constructors_count': 0  # Objects don't have constructors
        }
        
        return NodeProperties(
            name=object_name,
            type=NodeType.KOTLIN_OBJECT,
            file_path=parsed_file.file_path,
            line_number=1,
            properties=properties
        )
    
    def _create_kotlin_function_node(self, function_name: str, parsed_file: ParsedFile,
                                    package_node: Optional[NodeProperties]) -> NodeProperties:
        """Create Kotlin function node."""
        node_id = self._generate_node_id(NodeType.KOTLIN_FUNCTION, parsed_file.file_path, 1, function_name)
        
        properties = {
            'id': node_id,
            'return_type': 'Unit',
            'parameters_count': 0,
            'complexity': 1,
            'is_async': False,
            'is_generator': False
        }
        
        return NodeProperties(
            name=function_name,
            type=NodeType.KOTLIN_FUNCTION,
            file_path=parsed_file.file_path,
            line_number=1,
            properties=properties
        )
    
    def _create_kotlin_enum_node(self, enum_name: str, parsed_file: ParsedFile,
                                package_node: Optional[NodeProperties]) -> NodeProperties:
        """Create Kotlin enum node."""
        node_id = self._generate_node_id(NodeType.KOTLIN_ENUM, parsed_file.file_path, 1, enum_name)
        
        properties = {
            'id': node_id,
            'package_name': package_node.name if package_node else '',
            'full_name': f"{package_node.name}.{enum_name}" if package_node else enum_name,
            'modifiers': ['enum'],
            'implements_interfaces': [],
            'constants_count': 0,
            'methods_count': 0
        }
        
        return NodeProperties(
            name=enum_name,
            type=NodeType.KOTLIN_ENUM,
            file_path=parsed_file.file_path,
            line_number=1,
            properties=properties
        ) 