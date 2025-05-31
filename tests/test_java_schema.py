#!/usr/bin/env python3
"""
Test suite cho Java Schema Extensions trong CKG Schema.

Tests Java node types, relationships, và validation logic.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.ckg_operations.ckg_schema import (
    NodeType, RelationshipType, NodeProperties, RelationshipProperties, CKGSchema
)


class TestJavaNodeTypes:
    """Test Java node types trong CKG schema."""
    
    def test_java_node_types_exist(self):
        """Test tất cả Java node types được định nghĩa."""
        java_nodes = [
            NodeType.JAVA_CLASS,
            NodeType.JAVA_INTERFACE,
            NodeType.JAVA_METHOD,
            NodeType.JAVA_FIELD,
            NodeType.JAVA_CONSTRUCTOR,
            NodeType.JAVA_PACKAGE,
            NodeType.JAVA_IMPORT,
            NodeType.JAVA_ANNOTATION,
            NodeType.JAVA_ENUM,
            NodeType.JAVA_ENUM_CONSTANT
        ]
        
        for node_type in java_nodes:
            assert isinstance(node_type, NodeType)
            assert node_type.value.startswith("Java") or node_type.value == "JavaPackage"
    
    def test_java_node_properties_defined(self):
        """Test Java node properties được định nghĩa trong schema."""
        java_nodes = [
            NodeType.JAVA_CLASS,
            NodeType.JAVA_INTERFACE,
            NodeType.JAVA_METHOD,
            NodeType.JAVA_FIELD,
            NodeType.JAVA_CONSTRUCTOR,
            NodeType.JAVA_PACKAGE,
            NodeType.JAVA_IMPORT,
            NodeType.JAVA_ANNOTATION,
            NodeType.JAVA_ENUM,
            NodeType.JAVA_ENUM_CONSTANT
        ]
        
        for node_type in java_nodes:
            assert node_type in CKGSchema.NODE_PROPERTIES
            properties = CKGSchema.NODE_PROPERTIES[node_type]
            assert 'required' in properties
            assert 'optional' in properties
            assert 'name' in properties['required']
            assert 'type' in properties['required']
            assert 'file_path' in properties['required']
            assert 'line_number' in properties['required']


class TestJavaRelationshipTypes:
    """Test Java relationship types trong CKG schema."""
    
    def test_java_relationship_types_exist(self):
        """Test tất cả Java relationship types được định nghĩa."""
        java_relationships = [
            RelationshipType.DEFINES_JAVA_CLASS,
            RelationshipType.DEFINES_JAVA_INTERFACE,
            RelationshipType.DEFINES_JAVA_METHOD,
            RelationshipType.DEFINES_JAVA_FIELD,
            RelationshipType.DEFINES_JAVA_CONSTRUCTOR,
            RelationshipType.JAVA_EXTENDS,
            RelationshipType.JAVA_IMPLEMENTS,
            RelationshipType.JAVA_ANNOTATED_BY,
            RelationshipType.JAVA_THROWS,
            RelationshipType.JAVA_OVERRIDES,
            RelationshipType.JAVA_USES_TYPE
        ]
        
        for rel_type in java_relationships:
            assert isinstance(rel_type, RelationshipType)
            assert rel_type.value.startswith("JAVA_") or rel_type.value.startswith("DEFINES_JAVA_")
    
    def test_java_relationships_in_valid_relationships(self):
        """Test Java relationships được định nghĩa trong VALID_RELATIONSHIPS."""
        java_relationships = [
            RelationshipType.DEFINES_JAVA_CLASS,
            RelationshipType.DEFINES_JAVA_INTERFACE,
            RelationshipType.DEFINES_JAVA_METHOD,
            RelationshipType.DEFINES_JAVA_FIELD,
            RelationshipType.DEFINES_JAVA_CONSTRUCTOR,
            RelationshipType.JAVA_EXTENDS,
            RelationshipType.JAVA_IMPLEMENTS,
            RelationshipType.JAVA_ANNOTATED_BY,
            RelationshipType.JAVA_THROWS,
            RelationshipType.JAVA_OVERRIDES,
            RelationshipType.JAVA_USES_TYPE
        ]
        
        for rel_type in java_relationships:
            assert rel_type in CKGSchema.VALID_RELATIONSHIPS
            valid_pairs = CKGSchema.VALID_RELATIONSHIPS[rel_type]
            assert len(valid_pairs) > 0
            for source_type, target_type in valid_pairs:
                assert isinstance(source_type, NodeType)
                assert isinstance(target_type, NodeType)


class TestJavaNodeValidation:
    """Test validation cho Java nodes."""
    
    def test_valid_java_class_node(self):
        """Test validation của valid Java class node."""
        node = NodeProperties(
            name="TestClass",
            type=NodeType.JAVA_CLASS,
            file_path="/test/TestClass.java",
            line_number=10
        )
        
        assert CKGSchema.validate_node(node) == True
    
    def test_valid_java_interface_node(self):
        """Test validation của valid Java interface node."""
        node = NodeProperties(
            name="TestInterface",
            type=NodeType.JAVA_INTERFACE,
            file_path="/test/TestInterface.java",
            line_number=5
        )
        
        assert CKGSchema.validate_node(node) == True
    
    def test_valid_java_method_node(self):
        """Test validation của valid Java method node."""
        node = NodeProperties(
            name="testMethod",
            type=NodeType.JAVA_METHOD,
            file_path="/test/TestClass.java",
            line_number=15,
            properties={
                'modifiers': ['public'],
                'return_type': 'String',
                'parameters': ['String arg1', 'int arg2']
            }
        )
        
        assert CKGSchema.validate_node(node) == True
    
    def test_invalid_java_node_missing_required(self):
        """Test validation fails cho Java node thiếu required properties."""
        node = NodeProperties(
            name="TestClass",
            type=NodeType.JAVA_CLASS,
            file_path="/test/TestClass.java",
            line_number=None  # Missing required property
        )
        
        assert CKGSchema.validate_node(node) == False


class TestJavaRelationshipValidation:
    """Test validation cho Java relationships."""
    
    def test_valid_java_extends_relationship(self):
        """Test validation của valid Java extends relationship."""
        relationship = RelationshipProperties(
            type=RelationshipType.JAVA_EXTENDS,
            source_node_id="class1",
            target_node_id="class2"
        )
        
        assert CKGSchema.validate_relationship(
            relationship, 
            NodeType.JAVA_CLASS, 
            NodeType.JAVA_CLASS
        ) == True
    
    def test_valid_java_implements_relationship(self):
        """Test validation của valid Java implements relationship."""
        relationship = RelationshipProperties(
            type=RelationshipType.JAVA_IMPLEMENTS,
            source_node_id="class1",
            target_node_id="interface1"
        )
        
        assert CKGSchema.validate_relationship(
            relationship,
            NodeType.JAVA_CLASS,
            NodeType.JAVA_INTERFACE
        ) == True
    
    def test_valid_defines_java_method_relationship(self):
        """Test validation của valid defines Java method relationship."""
        relationship = RelationshipProperties(
            type=RelationshipType.DEFINES_JAVA_METHOD,
            source_node_id="class1",
            target_node_id="method1"
        )
        
        assert CKGSchema.validate_relationship(
            relationship,
            NodeType.JAVA_CLASS,
            NodeType.JAVA_METHOD
        ) == True
    
    def test_invalid_java_relationship_wrong_types(self):
        """Test validation fails cho Java relationship với wrong node types."""
        relationship = RelationshipProperties(
            type=RelationshipType.JAVA_EXTENDS,
            source_node_id="class1",
            target_node_id="method1"
        )
        
        # JAVA_EXTENDS should be class-to-class, not class-to-method
        assert CKGSchema.validate_relationship(
            relationship,
            NodeType.JAVA_CLASS,
            NodeType.JAVA_METHOD
        ) == False


class TestJavaCypherGeneration:
    """Test Cypher query generation cho Java nodes và relationships."""
    
    def test_java_class_cypher_generation(self):
        """Test Cypher generation cho Java class node."""
        node = NodeProperties(
            name="TestClass",
            type=NodeType.JAVA_CLASS,
            file_path="/test/TestClass.java",
            line_number=10,
            properties={
                'package_name': 'com.example',
                'modifiers': ['public'],
                'is_abstract': False
            }
        )
        
        cypher = CKGSchema.get_cypher_create_node(node)
        
        assert "CREATE (n:JavaClass" in cypher
        assert "name: 'TestClass'" in cypher
        assert "file_path: '/test/TestClass.java'" in cypher
        assert "line_number: 10" in cypher
        assert "package_name: 'com.example'" in cypher
        assert "RETURN n" in cypher
    
    def test_java_extends_cypher_generation(self):
        """Test Cypher generation cho Java extends relationship."""
        relationship = RelationshipProperties(
            type=RelationshipType.JAVA_EXTENDS,
            source_node_id="child_class",
            target_node_id="parent_class"
        )
        
        cypher = CKGSchema.get_cypher_create_relationship(relationship)
        
        assert "MATCH (source {id: 'child_class'})" in cypher
        assert "MATCH (target {id: 'parent_class'})" in cypher
        assert "CREATE (source)-[r:JAVA_EXTENDS]->(target)" in cypher
        assert "RETURN r" in cypher


class TestJavaSchemaIntegration:
    """Test integration của Java schema với existing Python schema."""
    
    def test_common_relationships_support_both_languages(self):
        """Test common relationships hỗ trợ cả Python và Java."""
        # Test IMPORTS relationship
        imports_pairs = CKGSchema.VALID_RELATIONSHIPS[RelationshipType.IMPORTS]
        
        # Should support both Python modules và Java packages
        python_import = (NodeType.MODULE, NodeType.MODULE)
        java_import = (NodeType.JAVA_PACKAGE, NodeType.JAVA_PACKAGE)
        
        assert python_import in imports_pairs
        assert java_import in imports_pairs
        
        # Test CALLS relationship
        calls_pairs = CKGSchema.VALID_RELATIONSHIPS[RelationshipType.CALLS]
        
        # Should support both Python methods và Java methods
        python_call = (NodeType.METHOD, NodeType.METHOD)
        java_call = (NodeType.JAVA_METHOD, NodeType.JAVA_METHOD)
        
        assert python_call in calls_pairs
        assert java_call in calls_pairs
    
    def test_language_specific_relationships_isolated(self):
        """Test language-specific relationships không conflict."""
        # Python-specific relationships
        python_inherits = CKGSchema.VALID_RELATIONSHIPS[RelationshipType.INHERITS_FROM]
        for source_type, target_type in python_inherits:
            assert not source_type.value.startswith("Java")
            assert not target_type.value.startswith("Java")
        
        # Java-specific relationships
        java_extends = CKGSchema.VALID_RELATIONSHIPS[RelationshipType.JAVA_EXTENDS]
        for source_type, target_type in java_extends:
            assert source_type.value.startswith("Java")
            assert target_type.value.startswith("Java")
    
    def test_all_java_nodes_have_properties(self):
        """Test tất cả Java nodes có properties definition."""
        java_node_types = [
            NodeType.JAVA_CLASS, NodeType.JAVA_INTERFACE, NodeType.JAVA_METHOD,
            NodeType.JAVA_FIELD, NodeType.JAVA_CONSTRUCTOR, NodeType.JAVA_PACKAGE,
            NodeType.JAVA_IMPORT, NodeType.JAVA_ANNOTATION, NodeType.JAVA_ENUM,
            NodeType.JAVA_ENUM_CONSTANT
        ]
        
        for node_type in java_node_types:
            assert node_type in CKGSchema.NODE_PROPERTIES
            properties = CKGSchema.NODE_PROPERTIES[node_type]
            assert len(properties['required']) >= 4  # name, type, file_path, line_number
            assert len(properties['optional']) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 