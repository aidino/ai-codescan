#!/usr/bin/env python3
"""
AI CodeScan - CKG Schema Definition

Định nghĩa schema cơ bản cho Code Knowledge Graph (CKG) bao gồm
các loại nodes, relationships và properties cho Python.
"""

from enum import Enum
from typing import Dict, List, Any
from dataclasses import dataclass


class NodeType(Enum):
    """Định nghĩa các loại nodes trong CKG."""
    FILE = "File"
    MODULE = "Module"
    CLASS = "Class"
    FUNCTION = "Function"
    METHOD = "Method"
    VARIABLE = "Variable"
    PARAMETER = "Parameter"
    IMPORT = "Import"
    DECORATOR = "Decorator"


class RelationshipType(Enum):
    """Định nghĩa các loại relationships trong CKG."""
    IMPORTS = "IMPORTS"
    CALLS = "CALLS"
    DEFINES_CLASS = "DEFINES_CLASS"
    DEFINES_FUNCTION = "DEFINES_FUNCTION"
    DEFINES_METHOD = "DEFINES_METHOD"
    DEFINES_VARIABLE = "DEFINES_VARIABLE"
    HAS_PARAMETER = "HAS_PARAMETER"
    INHERITS_FROM = "INHERITS_FROM"
    DECORATED_BY = "DECORATED_BY"
    CONTAINS = "CONTAINS"
    BELONGS_TO = "BELONGS_TO"
    ASSIGNS_TO = "ASSIGNS_TO"
    ACCESSES = "ACCESSES"


@dataclass
class NodeProperties:
    """Thuộc tính cơ bản cho tất cả các nodes."""
    name: str
    type: NodeType
    file_path: str
    line_number: int
    end_line_number: int = None
    column_offset: int = None
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


@dataclass
class RelationshipProperties:
    """Thuộc tính cho relationships."""
    type: RelationshipType
    source_node_id: str
    target_node_id: str
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


class CKGSchema:
    """
    CKG Schema Definition cho Python.
    
    Định nghĩa cấu trúc và quy tắc cho việc xây dựng Code Knowledge Graph.
    """
    
    # Properties cho từng loại node
    NODE_PROPERTIES = {
        NodeType.FILE: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['size_bytes', 'encoding', 'is_test_file', 'language']
        },
        NodeType.MODULE: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['docstring', 'imports_count', 'classes_count', 'functions_count']
        },
        NodeType.CLASS: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['docstring', 'is_abstract', 'base_classes', 'methods_count', 'attributes_count']
        },
        NodeType.FUNCTION: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['docstring', 'return_type', 'parameters_count', 'complexity', 'is_async', 'is_generator']
        },
        NodeType.METHOD: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['docstring', 'return_type', 'parameters_count', 'complexity', 'is_async', 'is_static', 'is_class_method', 'is_property']
        },
        NodeType.VARIABLE: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['value_type', 'is_global', 'is_constant', 'assigned_value']
        },
        NodeType.PARAMETER: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['param_type', 'default_value', 'is_keyword_only', 'is_positional_only']
        },
        NodeType.IMPORT: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['module_name', 'imported_name', 'alias', 'is_from_import']
        },
        NodeType.DECORATOR: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['arguments', 'is_builtin']
        }
    }
    
    # Relationships hợp lệ giữa các loại nodes
    VALID_RELATIONSHIPS = {
        RelationshipType.IMPORTS: [(NodeType.MODULE, NodeType.MODULE), (NodeType.FILE, NodeType.MODULE)],
        RelationshipType.CALLS: [(NodeType.FUNCTION, NodeType.FUNCTION), (NodeType.METHOD, NodeType.FUNCTION), (NodeType.METHOD, NodeType.METHOD)],
        RelationshipType.DEFINES_CLASS: [(NodeType.MODULE, NodeType.CLASS), (NodeType.FILE, NodeType.CLASS)],
        RelationshipType.DEFINES_FUNCTION: [(NodeType.MODULE, NodeType.FUNCTION), (NodeType.FILE, NodeType.FUNCTION)],
        RelationshipType.DEFINES_METHOD: [(NodeType.CLASS, NodeType.METHOD)],
        RelationshipType.DEFINES_VARIABLE: [(NodeType.MODULE, NodeType.VARIABLE), (NodeType.CLASS, NodeType.VARIABLE), (NodeType.FUNCTION, NodeType.VARIABLE)],
        RelationshipType.HAS_PARAMETER: [(NodeType.FUNCTION, NodeType.PARAMETER), (NodeType.METHOD, NodeType.PARAMETER)],
        RelationshipType.INHERITS_FROM: [(NodeType.CLASS, NodeType.CLASS)],
        RelationshipType.DECORATED_BY: [(NodeType.FUNCTION, NodeType.DECORATOR), (NodeType.METHOD, NodeType.DECORATOR), (NodeType.CLASS, NodeType.DECORATOR)],
        RelationshipType.CONTAINS: [(NodeType.FILE, NodeType.MODULE), (NodeType.MODULE, NodeType.CLASS), (NodeType.MODULE, NodeType.FUNCTION)],
        RelationshipType.BELONGS_TO: [(NodeType.CLASS, NodeType.MODULE), (NodeType.FUNCTION, NodeType.MODULE), (NodeType.METHOD, NodeType.CLASS)],
        RelationshipType.ASSIGNS_TO: [(NodeType.FUNCTION, NodeType.VARIABLE), (NodeType.METHOD, NodeType.VARIABLE)],
        RelationshipType.ACCESSES: [(NodeType.FUNCTION, NodeType.VARIABLE), (NodeType.METHOD, NodeType.VARIABLE)]
    }
    
    @classmethod
    def validate_node(cls, node: NodeProperties) -> bool:
        """
        Validate node properties theo schema.
        
        Args:
            node: Node cần validate
            
        Returns:
            bool: True nếu node hợp lệ
        """
        if node.type not in cls.NODE_PROPERTIES:
            return False
        
        required_props = cls.NODE_PROPERTIES[node.type]['required']
        
        # Kiểm tra required properties
        for prop in required_props:
            if not hasattr(node, prop) or getattr(node, prop) is None:
                return False
        
        return True
    
    @classmethod
    def validate_relationship(cls, relationship: RelationshipProperties, 
                            source_node_type: NodeType, target_node_type: NodeType) -> bool:
        """
        Validate relationship theo schema.
        
        Args:
            relationship: Relationship cần validate
            source_node_type: Loại node nguồn
            target_node_type: Loại node đích
            
        Returns:
            bool: True nếu relationship hợp lệ
        """
        if relationship.type not in cls.VALID_RELATIONSHIPS:
            return False
        
        valid_pairs = cls.VALID_RELATIONSHIPS[relationship.type]
        return (source_node_type, target_node_type) in valid_pairs
    
    @classmethod
    def get_cypher_create_node(cls, node: NodeProperties) -> str:
        """
        Tạo Cypher query để tạo node.
        
        Args:
            node: Node cần tạo
            
        Returns:
            str: Cypher query
        """
        properties = {
            'name': node.name,
            'type': node.type.value,
            'file_path': node.file_path,
            'line_number': node.line_number
        }
        
        if node.end_line_number:
            properties['end_line_number'] = node.end_line_number
        
        if node.column_offset:
            properties['column_offset'] = node.column_offset
        
        if node.properties:
            properties.update(node.properties)
        
        # Tạo properties string cho Cypher
        props_str = ', '.join([f'{k}: {repr(v)}' for k, v in properties.items()])
        
        # Generate unique ID
        node_id = f"{node.type.value}_{node.file_path}_{node.line_number}_{node.name}".replace('/', '_').replace('.', '_')
        
        return f"CREATE (n:{node.type.value} {{{props_str}}}) SET n.id = '{node_id}' RETURN n"
    
    @classmethod
    def get_cypher_create_relationship(cls, relationship: RelationshipProperties) -> str:
        """
        Tạo Cypher query để tạo relationship.
        
        Args:
            relationship: Relationship cần tạo
            
        Returns:
            str: Cypher query
        """
        properties_str = ""
        if relationship.properties:
            props = ', '.join([f'{k}: {repr(v)}' for k, v in relationship.properties.items()])
            properties_str = f" {{{props}}}"
        
        return f"""
        MATCH (source {{id: '{relationship.source_node_id}'}})
        MATCH (target {{id: '{relationship.target_node_id}'}})
        CREATE (source)-[r:{relationship.type.value}{properties_str}]->(target)
        RETURN r
        """
    
    @classmethod
    def get_cypher_find_node(cls, node_type: NodeType, **filters) -> str:
        """
        Tạo Cypher query để tìm nodes.
        
        Args:
            node_type: Loại node cần tìm
            **filters: Các bộ lọc
            
        Returns:
            str: Cypher query
        """
        where_conditions = []
        for key, value in filters.items():
            where_conditions.append(f"n.{key} = {repr(value)}")
        
        where_clause = ""
        if where_conditions:
            where_clause = f" WHERE {' AND '.join(where_conditions)}"
        
        return f"MATCH (n:{node_type.value}){where_clause} RETURN n"
    
    @classmethod
    def get_cypher_find_relationships(cls, relationship_type: RelationshipType, **filters) -> str:
        """
        Tạo Cypher query để tìm relationships.
        
        Args:
            relationship_type: Loại relationship cần tìm
            **filters: Các bộ lọc
            
        Returns:
            str: Cypher query
        """
        where_conditions = []
        for key, value in filters.items():
            where_conditions.append(f"r.{key} = {repr(value)}")
        
        where_clause = ""
        if where_conditions:
            where_clause = f" WHERE {' AND '.join(where_conditions)}"
        
        return f"MATCH (source)-[r:{relationship_type.value}]->(target){where_clause} RETURN source, r, target" 