#!/usr/bin/env python3
"""
Test suite cho CKG Schema Kotlin support.

Kiểm tra các Kotlin node types và relationship types được định nghĩa đúng
trong CKG Schema.
"""

import unittest
import os
import sys

# Add src to path để import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.ckg_operations.ckg_schema import CKGSchema, NodeType, RelationshipType, NodeProperties, RelationshipProperties


class TestKotlinCKGSchema(unittest.TestCase):
    """Test class cho CKG Schema Kotlin support."""

    def test_kotlin_node_types_exist(self):
        """Test tất cả Kotlin node types được định nghĩa."""
        kotlin_node_types = [
            NodeType.KOTLIN_CLASS,
            NodeType.KOTLIN_INTERFACE,
            NodeType.KOTLIN_DATA_CLASS,
            NodeType.KOTLIN_SEALED_CLASS,
            NodeType.KOTLIN_OBJECT,
            NodeType.KOTLIN_COMPANION_OBJECT,
            NodeType.KOTLIN_FUNCTION,
            NodeType.KOTLIN_METHOD,
            NodeType.KOTLIN_EXTENSION_FUNCTION,
            NodeType.KOTLIN_CONSTRUCTOR,
            NodeType.KOTLIN_PROPERTY,
            NodeType.KOTLIN_FIELD,
            NodeType.KOTLIN_PARAMETER,
            NodeType.KOTLIN_IMPORT,
            NodeType.KOTLIN_PACKAGE,
            NodeType.KOTLIN_ANNOTATION,
            NodeType.KOTLIN_ENUM,
            NodeType.KOTLIN_ENUM_ENTRY,
            NodeType.KOTLIN_TYPEALIAS
        ]
        
        for node_type in kotlin_node_types:
            with self.subTest(node_type=node_type):
                self.assertIsInstance(node_type, NodeType)
                self.assertIn(node_type, CKGSchema.NODE_PROPERTIES)

    def test_kotlin_relationship_types_exist(self):
        """Test tất cả Kotlin relationship types được định nghĩa."""
        kotlin_relationship_types = [
            RelationshipType.DEFINES_KOTLIN_CLASS,
            RelationshipType.DEFINES_KOTLIN_INTERFACE,
            RelationshipType.DEFINES_KOTLIN_DATA_CLASS,
            RelationshipType.DEFINES_KOTLIN_SEALED_CLASS,
            RelationshipType.DEFINES_KOTLIN_OBJECT,
            RelationshipType.DEFINES_KOTLIN_COMPANION_OBJECT,
            RelationshipType.DEFINES_KOTLIN_FUNCTION,
            RelationshipType.DEFINES_KOTLIN_METHOD,
            RelationshipType.DEFINES_KOTLIN_EXTENSION_FUNCTION,
            RelationshipType.DEFINES_KOTLIN_CONSTRUCTOR,
            RelationshipType.DEFINES_KOTLIN_PROPERTY,
            RelationshipType.DEFINES_KOTLIN_FIELD,
            RelationshipType.DEFINES_KOTLIN_ENUM,
            RelationshipType.DEFINES_KOTLIN_TYPEALIAS,
            RelationshipType.KOTLIN_EXTENDS,
            RelationshipType.KOTLIN_IMPLEMENTS,
            RelationshipType.KOTLIN_OVERRIDES,
            RelationshipType.KOTLIN_USES_TYPE,
            RelationshipType.KOTLIN_ANNOTATED_BY,
            RelationshipType.KOTLIN_COMPILES_TO,
            RelationshipType.KOTLIN_DEPENDS_ON
        ]
        
        for relationship_type in kotlin_relationship_types:
            with self.subTest(relationship_type=relationship_type):
                self.assertIsInstance(relationship_type, RelationshipType)
                self.assertIn(relationship_type, CKGSchema.VALID_RELATIONSHIPS)

    def test_kotlin_node_properties(self):
        """Test properties của Kotlin nodes."""
        # Test Kotlin class properties
        kotlin_class_props = CKGSchema.NODE_PROPERTIES[NodeType.KOTLIN_CLASS]
        self.assertIn('name', kotlin_class_props['required'])
        self.assertIn('type', kotlin_class_props['required'])
        self.assertIn('file_path', kotlin_class_props['required'])
        self.assertIn('line_number', kotlin_class_props['required'])
        self.assertIn('package_name', kotlin_class_props['optional'])
        self.assertIn('full_name', kotlin_class_props['optional'])
        self.assertIn('modifiers', kotlin_class_props['optional'])
        
        # Test Kotlin function properties
        kotlin_func_props = CKGSchema.NODE_PROPERTIES[NodeType.KOTLIN_FUNCTION]
        self.assertIn('return_type', kotlin_func_props['optional'])
        self.assertIn('parameters_count', kotlin_func_props['optional'])
        self.assertIn('complexity', kotlin_func_props['optional'])

    def test_kotlin_valid_relationships(self):
        """Test valid relationships cho Kotlin nodes."""
        # Test DEFINES_KOTLIN_CLASS relationship
        valid_defines_class = CKGSchema.VALID_RELATIONSHIPS[RelationshipType.DEFINES_KOTLIN_CLASS]
        self.assertIn((NodeType.FILE, NodeType.KOTLIN_CLASS), valid_defines_class)
        
        # Test KOTLIN_EXTENDS relationship
        valid_extends = CKGSchema.VALID_RELATIONSHIPS[RelationshipType.KOTLIN_EXTENDS]
        self.assertIn((NodeType.KOTLIN_CLASS, NodeType.KOTLIN_CLASS), valid_extends)
        
        # Test KOTLIN_IMPLEMENTS relationship
        valid_implements = CKGSchema.VALID_RELATIONSHIPS[RelationshipType.KOTLIN_IMPLEMENTS]
        self.assertIn((NodeType.KOTLIN_CLASS, NodeType.KOTLIN_INTERFACE), valid_implements)

    def test_kotlin_node_validation(self):
        """Test validation của Kotlin nodes."""
        # Create valid Kotlin class node
        kotlin_class_node = NodeProperties(
            name="MainActivity",
            type=NodeType.KOTLIN_CLASS,
            file_path="/path/to/MainActivity.kt",
            line_number=1,
            properties={'package_name': 'com.example'}
        )
        
        self.assertTrue(CKGSchema.validate_node(kotlin_class_node))
        
        # Create invalid node (missing required field)
        invalid_node = NodeProperties(
            name="InvalidClass",
            type=NodeType.KOTLIN_CLASS,
            file_path="",  # Missing file_path
            line_number=1
        )
        
        self.assertFalse(CKGSchema.validate_node(invalid_node))

    def test_kotlin_relationship_validation(self):
        """Test validation của Kotlin relationships."""
        # Valid relationship: File DEFINES_KOTLIN_CLASS KotlinClass
        valid_relationship = RelationshipProperties(
            type=RelationshipType.DEFINES_KOTLIN_CLASS,
            source_node_id="file_1",
            target_node_id="kotlin_class_1"
        )
        
        self.assertTrue(CKGSchema.validate_relationship(
            valid_relationship, 
            NodeType.FILE, 
            NodeType.KOTLIN_CLASS
        ))
        
        # Invalid relationship: KotlinClass DEFINES_KOTLIN_CLASS File (wrong direction)
        invalid_relationship = RelationshipProperties(
            type=RelationshipType.DEFINES_KOTLIN_CLASS,
            source_node_id="kotlin_class_1",
            target_node_id="file_1"
        )
        
        self.assertFalse(CKGSchema.validate_relationship(
            invalid_relationship,
            NodeType.KOTLIN_CLASS,
            NodeType.FILE
        ))

    def test_kotlin_cypher_generation(self):
        """Test Cypher query generation cho Kotlin nodes."""
        kotlin_class_node = NodeProperties(
            name="MainActivity",
            type=NodeType.KOTLIN_CLASS,
            file_path="/path/to/MainActivity.kt",
            line_number=10,
            properties={'package_name': 'com.example.myapp'}
        )
        
        cypher_query = CKGSchema.get_cypher_create_node(kotlin_class_node)
        
        self.assertIn("CREATE", cypher_query)
        self.assertIn("KotlinClass", cypher_query)
        self.assertIn("MainActivity", cypher_query)
        self.assertIn("com.example.myapp", cypher_query)
        
    def test_kotlin_relationship_cypher_generation(self):
        """Test Cypher query generation cho Kotlin relationships."""
        relationship = RelationshipProperties(
            type=RelationshipType.KOTLIN_EXTENDS,
            source_node_id="child_class",
            target_node_id="parent_class"
        )
        
        cypher_query = CKGSchema.get_cypher_create_relationship(relationship)
        
        self.assertIn("MERGE", cypher_query)
        self.assertIn("KOTLIN_EXTENDS", cypher_query)
        self.assertIn("child_class", cypher_query)
        self.assertIn("parent_class", cypher_query)

    def test_kotlin_specific_node_types(self):
        """Test các Kotlin-specific node types."""
        # Test data class
        self.assertIn(NodeType.KOTLIN_DATA_CLASS, CKGSchema.NODE_PROPERTIES)
        
        # Test sealed class
        self.assertIn(NodeType.KOTLIN_SEALED_CLASS, CKGSchema.NODE_PROPERTIES)
        
        # Test object and companion object
        self.assertIn(NodeType.KOTLIN_OBJECT, CKGSchema.NODE_PROPERTIES)
        self.assertIn(NodeType.KOTLIN_COMPANION_OBJECT, CKGSchema.NODE_PROPERTIES)
        
        # Test extension function
        self.assertIn(NodeType.KOTLIN_EXTENSION_FUNCTION, CKGSchema.NODE_PROPERTIES)
        
        # Test typealias
        self.assertIn(NodeType.KOTLIN_TYPEALIAS, CKGSchema.NODE_PROPERTIES)


if __name__ == '__main__':
    unittest.main() 