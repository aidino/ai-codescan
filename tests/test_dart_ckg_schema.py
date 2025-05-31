"""
Tests for Dart CKG schema extensions.
"""

import unittest
from src.agents.ckg_operations.ckg_schema import CKGSchema, NodeType, RelationshipType, NodeProperties, RelationshipProperties


class TestDartCKGSchema(unittest.TestCase):
    """Test Dart-specific CKG schema functionality."""

    def test_dart_node_types(self):
        """Test that all Dart node types are defined."""
        dart_node_types = [
            NodeType.DART_CLASS,
            NodeType.DART_MIXIN,
            NodeType.DART_EXTENSION,
            NodeType.DART_FUNCTION,
            NodeType.DART_METHOD,
            NodeType.DART_GETTER,
            NodeType.DART_SETTER,
            NodeType.DART_CONSTRUCTOR,
            NodeType.DART_FIELD,
            NodeType.DART_VARIABLE,
            NodeType.DART_PARAMETER,
            NodeType.DART_IMPORT,
            NodeType.DART_EXPORT,
            NodeType.DART_PART,
            NodeType.DART_LIBRARY,
            NodeType.DART_ENUM,
            NodeType.DART_ENUM_VALUE,
            NodeType.DART_TYPEDEF,
        ]
        
        for node_type in dart_node_types:
            self.assertIsInstance(node_type, NodeType)
            self.assertTrue(node_type.value.startswith('Dart'))

    def test_dart_relationship_types(self):
        """Test that all Dart relationship types are defined."""
        dart_relationship_types = [
            RelationshipType.DEFINES_DART_CLASS,
            RelationshipType.DEFINES_DART_MIXIN,
            RelationshipType.DEFINES_DART_EXTENSION,
            RelationshipType.DEFINES_DART_FUNCTION,
            RelationshipType.DEFINES_DART_METHOD,
            RelationshipType.DEFINES_DART_GETTER,
            RelationshipType.DEFINES_DART_SETTER,
            RelationshipType.DEFINES_DART_CONSTRUCTOR,
            RelationshipType.DEFINES_DART_FIELD,
            RelationshipType.DEFINES_DART_VARIABLE,
            RelationshipType.DEFINES_DART_ENUM,
            RelationshipType.DEFINES_DART_TYPEDEF,
            RelationshipType.DART_EXTENDS,
            RelationshipType.DART_IMPLEMENTS,
            RelationshipType.DART_MIXES_IN,
            RelationshipType.DART_EXTENDS_TYPE,
            RelationshipType.DART_OVERRIDES,
            RelationshipType.DART_USES_TYPE,
            RelationshipType.DART_EXPORTS,
            RelationshipType.DART_PARTS,
        ]
        
        for rel_type in dart_relationship_types:
            self.assertIsInstance(rel_type, RelationshipType)

    def test_dart_node_properties(self):
        """Test that Dart node properties are properly defined."""
        # Test DART_CLASS properties
        class_props = CKGSchema.NODE_PROPERTIES[NodeType.DART_CLASS]
        self.assertIn('name', class_props['required'])
        self.assertIn('type', class_props['required'])
        self.assertIn('file_path', class_props['required'])
        self.assertIn('line_number', class_props['required'])
        self.assertIn('package_name', class_props['optional'])
        self.assertIn('extends_class', class_props['optional'])
        
        # Test DART_MIXIN properties
        mixin_props = CKGSchema.NODE_PROPERTIES[NodeType.DART_MIXIN]
        self.assertIn('name', mixin_props['required'])
        self.assertIn('extends_interfaces', mixin_props['optional'])
        
        # Test DART_EXTENSION properties
        extension_props = CKGSchema.NODE_PROPERTIES[NodeType.DART_EXTENSION]
        self.assertIn('name', extension_props['required'])
        self.assertIn('extends_class', extension_props['optional'])
        
        # Test DART_FUNCTION properties
        function_props = CKGSchema.NODE_PROPERTIES[NodeType.DART_FUNCTION]
        self.assertIn('name', function_props['required'])
        self.assertIn('return_type', function_props['optional'])
        self.assertIn('is_async', function_props['optional'])

    def test_dart_valid_relationships(self):
        """Test that Dart relationships are properly defined."""
        valid_rels = CKGSchema.VALID_RELATIONSHIPS
        
        # Test DART_EXTENDS relationship
        self.assertIn(RelationshipType.DART_EXTENDS, valid_rels)
        dart_extends = valid_rels[RelationshipType.DART_EXTENDS]
        self.assertIn((NodeType.DART_CLASS, NodeType.DART_CLASS), dart_extends)
        self.assertIn((NodeType.DART_MIXIN, NodeType.DART_CLASS), dart_extends)
        
        # Test DART_IMPLEMENTS relationship
        self.assertIn(RelationshipType.DART_IMPLEMENTS, valid_rels)
        dart_implements = valid_rels[RelationshipType.DART_IMPLEMENTS]
        self.assertIn((NodeType.DART_CLASS, NodeType.DART_MIXIN), dart_implements)
        
        # Test DART_MIXES_IN relationship
        self.assertIn(RelationshipType.DART_MIXES_IN, valid_rels)
        dart_mixes_in = valid_rels[RelationshipType.DART_MIXES_IN]
        self.assertIn((NodeType.DART_CLASS, NodeType.DART_MIXIN), dart_mixes_in)
        
        # Test DEFINES_DART_CLASS relationship
        self.assertIn(RelationshipType.DEFINES_DART_CLASS, valid_rels)
        defines_dart_class = valid_rels[RelationshipType.DEFINES_DART_CLASS]
        self.assertIn((NodeType.FILE, NodeType.DART_CLASS), defines_dart_class)

    def test_dart_node_validation(self):
        """Test validation of Dart nodes."""
        # Valid Dart class node
        dart_class_node = NodeProperties(
            name="MyWidget",
            type=NodeType.DART_CLASS,
            file_path="lib/widgets/my_widget.dart",
            line_number=10,
            end_line_number=50,
            properties={
                'package_name': 'my_app',
                'extends_class': 'StatelessWidget',
                'implements_interfaces': ['Comparable']
            }
        )
        
        self.assertTrue(CKGSchema.validate_node(dart_class_node))
        
        # Valid Dart mixin node
        dart_mixin_node = NodeProperties(
            name="MyMixin",
            type=NodeType.DART_MIXIN,
            file_path="lib/mixins/my_mixin.dart",
            line_number=5,
            properties={
                'extends_interfaces': ['Object'],
                'methods_count': 3
            }
        )
        
        self.assertTrue(CKGSchema.validate_node(dart_mixin_node))

    def test_dart_relationship_validation(self):
        """Test validation of Dart relationships."""
        # Valid DART_EXTENDS relationship
        dart_extends_rel = RelationshipProperties(
            type=RelationshipType.DART_EXTENDS,
            source_node_id="class_1",
            target_node_id="class_2",
            properties={}
        )
        
        self.assertTrue(CKGSchema.validate_relationship(
            dart_extends_rel, 
            NodeType.DART_CLASS, 
            NodeType.DART_CLASS
        ))
        
        # Valid DART_MIXES_IN relationship
        dart_mixes_in_rel = RelationshipProperties(
            type=RelationshipType.DART_MIXES_IN,
            source_node_id="class_1",
            target_node_id="mixin_1",
            properties={}
        )
        
        self.assertTrue(CKGSchema.validate_relationship(
            dart_mixes_in_rel,
            NodeType.DART_CLASS,
            NodeType.DART_MIXIN
        ))
        
        # Invalid relationship (wrong node types)
        invalid_rel = RelationshipProperties(
            type=RelationshipType.DART_EXTENDS,
            source_node_id="class_1",
            target_node_id="function_1",
            properties={}
        )
        
        self.assertFalse(CKGSchema.validate_relationship(
            invalid_rel,
            NodeType.DART_CLASS,
            NodeType.DART_FUNCTION
        ))

    def test_dart_cypher_queries(self):
        """Test Cypher query generation for Dart nodes and relationships."""
        # Test node creation query
        dart_class_node = NodeProperties(
            name="MyWidget",
            type=NodeType.DART_CLASS,
            file_path="lib/widgets/my_widget.dart",
            line_number=10,
            properties={
                'package_name': 'my_app',
                'extends_class': 'StatelessWidget'
            }
        )
        
        create_query = CKGSchema.get_cypher_create_node(dart_class_node)
        self.assertIn("CREATE", create_query)
        self.assertIn("DartClass", create_query)
        self.assertIn("MyWidget", create_query)
        
        # Test relationship creation query
        dart_extends_rel = RelationshipProperties(
            type=RelationshipType.DART_EXTENDS,
            source_node_id="class_1",
            target_node_id="class_2",
            properties={}
        )
        
        rel_query = CKGSchema.get_cypher_create_relationship(dart_extends_rel)
        self.assertIn("MATCH", rel_query)
        self.assertIn("DART_EXTENDS", rel_query)
        self.assertIn("class_1", rel_query)
        self.assertIn("class_2", rel_query)


if __name__ == '__main__':
    unittest.main() 