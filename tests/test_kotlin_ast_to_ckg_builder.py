#!/usr/bin/env python3
"""
Tests cho Kotlin support trong ASTtoCKGBuilderAgent.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.ckg_operations.ast_to_ckg_builder import ASTtoCKGBuilderAgent
from agents.ckg_operations.ckg_schema import NodeType, RelationshipType, NodeProperties
from agents.ckg_operations.code_parser_coordinator import ParsedFile, ParseResult
from agents.ckg_operations.kotlin_parser import KotlinParseInfo, KotlinNode


class TestKotlinASTtoCKGBuilder(unittest.TestCase):
    """Test Kotlin support trong ASTtoCKGBuilderAgent."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.builder = ASTtoCKGBuilderAgent()
        
        # Mock Neo4j connection
        self.builder.neo4j_connection = Mock()
        
        # Sample Kotlin ParsedFile
        self.sample_kotlin_file = ParsedFile(
            file_path="/test/src/main/kotlin/com/example/TestClass.kt",
            relative_path="src/main/kotlin/com/example/TestClass.kt",
            language="kotlin",
            ast_tree=KotlinParseInfo(
                package_name="com.example",
                imports=["java.util.List", "kotlin.collections.ArrayList"],
                classes=[
                    KotlinNode(
                        type="class",
                        name="TestClass",
                        start_line=5,
                        end_line=20,
                        modifiers=["public"],
                        properties={"extends": "BaseClass", "implements": ["TestInterface"]}
                    )
                ],
                interfaces=[
                    KotlinNode(
                        type="interface",
                        name="TestInterface",
                        start_line=22,
                        end_line=30,
                        modifiers=["public"]
                    )
                ],
                objects=[
                    KotlinNode(
                        type="object",
                        name="TestObject",
                        start_line=32,
                        end_line=40,
                        modifiers=["public"]
                    )
                ],
                functions=[
                    KotlinNode(
                        type="function",
                        name="testFunction",
                        start_line=42,
                        end_line=50,
                        modifiers=["public"],
                        properties={"return_type": "String", "parameters": ["param1: Int"]}
                    )
                ],
                data_classes=[
                    KotlinNode(
                        type="data_class",
                        name="TestDataClass",
                        start_line=52,
                        end_line=55,
                        modifiers=["public", "data"],
                        properties={"fields": ["name: String", "age: Int"]}
                    )
                ],
                enums=[
                    KotlinNode(
                        type="enum",
                        name="TestEnum",
                        start_line=57,
                        end_line=65,
                        modifiers=["public"],
                        properties={"constants": ["FIRST", "SECOND", "THIRD"]}
                    )
                ]
            ),
            parse_success=True,
            nodes_count=6,
            lines_count=65
        )
    
    def test_process_kotlin_file(self):
        """Test _process_kotlin_file method."""
        # Create file node
        file_node = NodeProperties(
            name="TestClass.kt",
            type=NodeType.FILE,
            file_path="/test/src/main/kotlin/com/example/TestClass.kt",
            line_number=1
        )
        
        # Mock CKG schema methods
        with patch.object(self.builder.schema, 'get_cypher_create_node') as mock_create_node, \
             patch.object(self.builder.schema, 'get_cypher_create_relationship') as mock_create_rel:
            
            mock_create_node.return_value = "CREATE (n:TestNode)"
            mock_create_rel.return_value = "CREATE (a)-[:TEST_REL]->(b)"
            
            queries = self.builder._process_kotlin_file(self.sample_kotlin_file, file_node)
            
            # Should generate queries for all Kotlin elements
            self.assertGreater(len(queries), 0)
            self.assertIsInstance(queries, list)
    
    def test_process_kotlin_ast(self):
        """Test _process_kotlin_ast method."""
        file_node = NodeProperties(
            name="TestClass.kt",
            type=NodeType.FILE,
            file_path="/test/src/main/kotlin/com/example/TestClass.kt",
            line_number=1
        )
        
        kotlin_ast = self.sample_kotlin_file.ast_tree
        
        with patch.object(self.builder.schema, 'get_cypher_create_node') as mock_create_node, \
             patch.object(self.builder.schema, 'get_cypher_create_relationship') as mock_create_rel:
            
            mock_create_node.return_value = "CREATE (n:TestNode)"
            mock_create_rel.return_value = "CREATE (a)-[:TEST_REL]->(b)"
            
            queries = self.builder._process_kotlin_ast(kotlin_ast, self.sample_kotlin_file, file_node)
            
            self.assertIsInstance(queries, list)
            self.assertGreater(len(queries), 0)
    
    def test_create_kotlin_package_node(self):
        """Test _create_kotlin_package_node method."""
        package_node = self.builder._create_kotlin_package_node(
            "com.example.test", 
            self.sample_kotlin_file
        )
        
        self.assertEqual(package_node.name, "com.example.test")
        self.assertEqual(package_node.type, NodeType.KOTLIN_PACKAGE)
        self.assertEqual(package_node.file_path, self.sample_kotlin_file.file_path)
    
    def test_create_kotlin_import_node(self):
        """Test _create_kotlin_import_node method."""
        import_node = self.builder._create_kotlin_import_node(
            "java.util.List",
            self.sample_kotlin_file
        )
        
        self.assertEqual(import_node.name, "java.util.List")
        self.assertEqual(import_node.type, NodeType.KOTLIN_IMPORT)
        self.assertEqual(import_node.file_path, self.sample_kotlin_file.file_path)
    
    def test_create_kotlin_class_node(self):
        """Test _create_kotlin_class_node method."""
        # Create package node
        package_node = self.builder._create_kotlin_package_node(
            "com.example", 
            self.sample_kotlin_file
        )
        
        class_node = self.builder._create_kotlin_class_node(
            "TestClass",
            self.sample_kotlin_file,
            package_node
        )
        
        self.assertEqual(class_node.name, "TestClass")
        self.assertEqual(class_node.type, NodeType.KOTLIN_CLASS)
        self.assertEqual(class_node.file_path, self.sample_kotlin_file.file_path)
        
        # Check properties
        self.assertIn("modifiers", class_node.properties)
        self.assertIn("is_final", class_node.properties)
    
    def test_create_kotlin_data_class_node(self):
        """Test _create_kotlin_data_class_node method."""
        package_node = self.builder._create_kotlin_package_node(
            "com.example", 
            self.sample_kotlin_file
        )
        
        data_class_node = self.builder._create_kotlin_data_class_node(
            "TestDataClass",
            self.sample_kotlin_file,
            package_node
        )
        
        self.assertEqual(data_class_node.name, "TestDataClass")
        self.assertEqual(data_class_node.type, NodeType.KOTLIN_DATA_CLASS)
        self.assertEqual(data_class_node.file_path, self.sample_kotlin_file.file_path)
        
        # Data classes are final by default
        self.assertTrue(data_class_node.properties.get("is_final", True))
    
    def test_create_kotlin_interface_node(self):
        """Test _create_kotlin_interface_node method."""
        package_node = self.builder._create_kotlin_package_node(
            "com.example", 
            self.sample_kotlin_file
        )
        
        interface_node = self.builder._create_kotlin_interface_node(
            "TestInterface",
            self.sample_kotlin_file,
            package_node
        )
        
        self.assertEqual(interface_node.name, "TestInterface")
        self.assertEqual(interface_node.type, NodeType.KOTLIN_INTERFACE)
        self.assertEqual(interface_node.file_path, self.sample_kotlin_file.file_path)
    
    def test_create_kotlin_object_node(self):
        """Test _create_kotlin_object_node method."""
        package_node = self.builder._create_kotlin_package_node(
            "com.example", 
            self.sample_kotlin_file
        )
        
        object_node = self.builder._create_kotlin_object_node(
            "TestObject",
            self.sample_kotlin_file,
            package_node
        )
        
        self.assertEqual(object_node.name, "TestObject")
        self.assertEqual(object_node.type, NodeType.KOTLIN_OBJECT)
        self.assertEqual(object_node.file_path, self.sample_kotlin_file.file_path)
        
        # Objects are final and singleton
        self.assertTrue(object_node.properties.get("is_final", True))
    
    def test_create_kotlin_function_node(self):
        """Test _create_kotlin_function_node method."""
        package_node = self.builder._create_kotlin_package_node(
            "com.example", 
            self.sample_kotlin_file
        )
        
        function_node = self.builder._create_kotlin_function_node(
            "testFunction",
            self.sample_kotlin_file,
            package_node
        )
        
        self.assertEqual(function_node.name, "testFunction")
        self.assertEqual(function_node.type, NodeType.KOTLIN_FUNCTION)
        self.assertEqual(function_node.file_path, self.sample_kotlin_file.file_path)
        
        # Check function properties
        self.assertIn("return_type", function_node.properties)
        self.assertIn("parameters_count", function_node.properties)
        self.assertIn("complexity", function_node.properties)
    
    def test_create_kotlin_enum_node(self):
        """Test _create_kotlin_enum_node method."""
        package_node = self.builder._create_kotlin_package_node(
            "com.example", 
            self.sample_kotlin_file
        )
        
        enum_node = self.builder._create_kotlin_enum_node(
            "TestEnum",
            self.sample_kotlin_file,
            package_node
        )
        
        self.assertEqual(enum_node.name, "TestEnum")
        self.assertEqual(enum_node.type, NodeType.KOTLIN_ENUM)
        self.assertEqual(enum_node.file_path, self.sample_kotlin_file.file_path)
        
        # Check enum properties
        self.assertIn("constants_count", enum_node.properties)
        self.assertIn("methods_count", enum_node.properties)
    
    def test_process_kotlin_class(self):
        """Test _process_kotlin_class method."""
        file_node = NodeProperties(
            name="TestClass.kt",
            type=NodeType.FILE,
            file_path="/test/src/main/kotlin/com/example/TestClass.kt",
            line_number=1
        )
        
        package_node = self.builder._create_kotlin_package_node(
            "com.example", 
            self.sample_kotlin_file
        )
        
        with patch.object(self.builder.schema, 'get_cypher_create_node') as mock_create_node, \
             patch.object(self.builder.schema, 'get_cypher_create_relationship') as mock_create_rel:
            
            mock_create_node.return_value = "CREATE (n:TestNode)"
            mock_create_rel.return_value = "CREATE (a)-[:TEST_REL]->(b)"
            
            queries = self.builder._process_kotlin_class(
                "TestClass",
                self.sample_kotlin_file,
                file_node,
                package_node
            )
            
            self.assertIsInstance(queries, list)
            self.assertGreater(len(queries), 0)
    
    def test_process_kotlin_data_class(self):
        """Test _process_kotlin_data_class method."""
        file_node = NodeProperties(
            name="TestClass.kt",
            type=NodeType.FILE,
            file_path="/test/src/main/kotlin/com/example/TestClass.kt",
            line_number=1
        )
        
        package_node = self.builder._create_kotlin_package_node(
            "com.example", 
            self.sample_kotlin_file
        )
        
        with patch.object(self.builder.schema, 'get_cypher_create_node') as mock_create_node, \
             patch.object(self.builder.schema, 'get_cypher_create_relationship') as mock_create_rel:
            
            mock_create_node.return_value = "CREATE (n:TestNode)"
            mock_create_rel.return_value = "CREATE (a)-[:TEST_REL]->(b)"
            
            queries = self.builder._process_kotlin_data_class(
                "TestDataClass",
                self.sample_kotlin_file,
                file_node,
                package_node
            )
            
            self.assertIsInstance(queries, list)
            self.assertGreater(len(queries), 0)
    
    def test_process_kotlin_interface(self):
        """Test _process_kotlin_interface method."""
        file_node = NodeProperties(
            name="TestClass.kt",
            type=NodeType.FILE,
            file_path="/test/src/main/kotlin/com/example/TestClass.kt",
            line_number=1
        )
        
        package_node = self.builder._create_kotlin_package_node(
            "com.example", 
            self.sample_kotlin_file
        )
        
        with patch.object(self.builder.schema, 'get_cypher_create_node') as mock_create_node, \
             patch.object(self.builder.schema, 'get_cypher_create_relationship') as mock_create_rel:
            
            mock_create_node.return_value = "CREATE (n:TestNode)"
            mock_create_rel.return_value = "CREATE (a)-[:TEST_REL]->(b)"
            
            queries = self.builder._process_kotlin_interface(
                "TestInterface",
                self.sample_kotlin_file,
                file_node,
                package_node
            )
            
            self.assertIsInstance(queries, list)
            self.assertGreater(len(queries), 0)
    
    def test_process_kotlin_object(self):
        """Test _process_kotlin_object method."""
        file_node = NodeProperties(
            name="TestClass.kt",
            type=NodeType.FILE,
            file_path="/test/src/main/kotlin/com/example/TestClass.kt",
            line_number=1
        )
        
        package_node = self.builder._create_kotlin_package_node(
            "com.example", 
            self.sample_kotlin_file
        )
        
        with patch.object(self.builder.schema, 'get_cypher_create_node') as mock_create_node, \
             patch.object(self.builder.schema, 'get_cypher_create_relationship') as mock_create_rel:
            
            mock_create_node.return_value = "CREATE (n:TestNode)"
            mock_create_rel.return_value = "CREATE (a)-[:TEST_REL]->(b)"
            
            queries = self.builder._process_kotlin_object(
                "TestObject",
                self.sample_kotlin_file,
                file_node,
                package_node
            )
            
            self.assertIsInstance(queries, list)
            self.assertGreater(len(queries), 0)
    
    def test_process_kotlin_function(self):
        """Test _process_kotlin_function method."""
        file_node = NodeProperties(
            name="TestClass.kt",
            type=NodeType.FILE,
            file_path="/test/src/main/kotlin/com/example/TestClass.kt",
            line_number=1
        )
        
        package_node = self.builder._create_kotlin_package_node(
            "com.example", 
            self.sample_kotlin_file
        )
        
        with patch.object(self.builder.schema, 'get_cypher_create_node') as mock_create_node, \
             patch.object(self.builder.schema, 'get_cypher_create_relationship') as mock_create_rel:
            
            mock_create_node.return_value = "CREATE (n:TestNode)"
            mock_create_rel.return_value = "CREATE (a)-[:TEST_REL]->(b)"
            
            queries = self.builder._process_kotlin_function(
                "testFunction",
                self.sample_kotlin_file,
                file_node,
                package_node
            )
            
            self.assertIsInstance(queries, list)
            self.assertGreater(len(queries), 0)
    
    def test_process_kotlin_enum(self):
        """Test _process_kotlin_enum method."""
        file_node = NodeProperties(
            name="TestClass.kt",
            type=NodeType.FILE,
            file_path="/test/src/main/kotlin/com/example/TestClass.kt",
            line_number=1
        )
        
        package_node = self.builder._create_kotlin_package_node(
            "com.example", 
            self.sample_kotlin_file
        )
        
        with patch.object(self.builder.schema, 'get_cypher_create_node') as mock_create_node, \
             patch.object(self.builder.schema, 'get_cypher_create_relationship') as mock_create_rel:
            
            mock_create_node.return_value = "CREATE (n:TestNode)"
            mock_create_rel.return_value = "CREATE (a)-[:TEST_REL]->(b)"
            
            queries = self.builder._process_kotlin_enum(
                "TestEnum",
                self.sample_kotlin_file,
                file_node,
                package_node
            )
            
            self.assertIsInstance(queries, list)
            self.assertGreater(len(queries), 0)


if __name__ == '__main__':
    unittest.main() 