#!/usr/bin/env python3
"""
Test suite cho ASTtoCKGBuilderAgent Dart support.

Kiểm tra việc xây dựng Code Knowledge Graph từ Dart AST.
"""

import unittest
from unittest.mock import Mock, patch
import os
import sys

# Add src to path để import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.ckg_operations.ast_to_ckg_builder import ASTtoCKGBuilderAgent, CKGBuildResult
from agents.ckg_operations.code_parser_coordinator import ParsedFile, ParseResult
from agents.ckg_operations.ckg_schema import NodeType, RelationshipType
from agents.ckg_operations.dart_parser import DartParseInfo
from agents.data_acquisition import LanguageInfo, ProjectLanguageProfile


class TestDartASTtoCKGBuilder(unittest.TestCase):
    """Test class cho ASTtoCKGBuilderAgent Dart support."""

    def setUp(self):
        """Set up test fixtures."""
        self.builder = ASTtoCKGBuilderAgent()
        self.test_file_path = "/test/project/lib/main.dart"
        
        # Mock DartParseInfo với sample data
        self.dart_parse_info = DartParseInfo(
            file_path=self.test_file_path,
            library_name="my_app",
            imports=["dart:core", "package:flutter/material.dart"],
            exports=["TestClass"],
            classes=["MyWidget"],
            mixins=["Validator"],
            extensions=["StringExtension"],
            functions=["main"],
            enums=["Status"],
            typedefs=["Callback"]
        )
        
        # Mock ParsedFile
        self.parsed_file = ParsedFile(
            file_path=self.test_file_path,
            relative_path="lib/main.dart",
            language="Dart",
            ast_tree=self.dart_parse_info,
            parse_success=True,
            nodes_count=15,
            lines_count=100
        )

    def test_dart_file_processing(self):
        """Test xử lý Dart file."""
        queries = self.builder._process_file(self.parsed_file)
        
        # Should return list of queries
        self.assertIsInstance(queries, list)
        self.assertGreater(len(queries), 0)
        
        # Verify file node creation
        file_nodes = [node for node in self.builder.created_nodes.values() 
                     if node.type == NodeType.FILE]
        self.assertEqual(len(file_nodes), 1)

    def test_dart_ast_processing(self):
        """Test processing Dart AST."""
        file_node = self.builder._create_file_node(self.parsed_file)
        queries = self.builder._process_dart_file(self.parsed_file, file_node)
        
        # Verify queries generated
        self.assertIsInstance(queries, list)
        self.assertGreater(len(queries), 0)
        
        # Verify Dart-specific nodes created
        node_types = [node.type for node in self.builder.created_nodes.values()]
        
        # Should have Dart-specific nodes
        self.assertIn(NodeType.DART_LIBRARY, node_types)
        self.assertIn(NodeType.DART_IMPORT, node_types)
        self.assertIn(NodeType.DART_CLASS, node_types)
        self.assertIn(NodeType.DART_FUNCTION, node_types)

    def test_dart_library_node_creation(self):
        """Test tạo Dart library node."""
        library_node = self.builder._create_dart_library_node("my_app", self.parsed_file)
        
        self.assertEqual(library_node.name, "my_app")
        self.assertEqual(library_node.type, NodeType.DART_LIBRARY)
        self.assertIn('id', library_node.properties)
        self.assertIn('full_name', library_node.properties)

    def test_dart_class_node_creation(self):
        """Test tạo Dart class node."""
        library_node = self.builder._create_dart_library_node("my_app", self.parsed_file)
        class_node = self.builder._create_dart_class_node("MyWidget", self.parsed_file, library_node)
        
        self.assertEqual(class_node.name, "MyWidget")
        self.assertEqual(class_node.type, NodeType.DART_CLASS)
        self.assertIn('package_name', class_node.properties)
        self.assertEqual(class_node.properties['package_name'], "my_app")
        self.assertEqual(class_node.properties['full_name'], "my_app.MyWidget")

    def test_dart_relationship_creation(self):
        """Test tạo relationships."""
        file_node = self.builder._create_file_node(self.parsed_file)
        queries = self.builder._process_dart_file(self.parsed_file, file_node)
        
        # Verify relationships created
        self.assertGreater(len(self.builder.created_relationships), 0)
        
        # Check for Dart-specific relationships
        rel_types = [rel.type for rel in self.builder.created_relationships]
        self.assertIn(RelationshipType.CONTAINS, rel_types)
        self.assertIn(RelationshipType.IMPORTS, rel_types)

    def test_build_ckg_from_dart_parse_result(self):
        """Test xây dựng CKG từ Dart ParseResult."""
        # Create mock language profile first
        dart_lang_info = LanguageInfo(
            name="Dart",
            percentage=100.0,
            file_count=1,
            total_lines=10
        )
        language_profile = ProjectLanguageProfile(
            primary_language="Dart",
            languages=[dart_lang_info],
            frameworks=[],
            build_tools=[],
            package_managers=[],
            project_type="mobile",
            confidence_score=0.9
        )
        
        parse_result = ParseResult(
            project_path="/test/project",
            language_profile=language_profile,
            parsed_files=[self.parsed_file],
            total_files=1,
            successful_files=1,
            failed_files=0,
            parse_errors=[],
            parsing_stats={"Dart": {"files": 1, "success": 1}}
        )
        
        result = self.builder.build_ckg_from_parse_result(parse_result)
        
        self.assertIsInstance(result, CKGBuildResult)
        self.assertTrue(result.build_success)
        self.assertGreater(result.total_nodes_created, 0)
        self.assertGreater(result.total_relationships_created, 0)

    def test_dart_minimal_file(self):
        """Test xử lý Dart file với minimal data."""
        minimal_parse_info = DartParseInfo(
            file_path=self.test_file_path,
            library_name=None,
            imports=[],
            exports=[],
            classes=[],
            mixins=[],
            extensions=[],
            functions=[],
            enums=[],
            typedefs=[]
        )
        
        minimal_parsed_file = ParsedFile(
            file_path=self.test_file_path,
            relative_path="lib/minimal.dart",
            language="Dart",
            ast_tree=minimal_parse_info,
            parse_success=True,
            nodes_count=1,
            lines_count=5
        )
        
        queries = self.builder._process_file(minimal_parsed_file)
        
        # Should still create file node
        self.assertGreater(len(queries), 0)
        file_nodes = [node for node in self.builder.created_nodes.values() 
                     if node.type == NodeType.FILE]
        self.assertEqual(len(file_nodes), 1)

    def test_dart_error_handling(self):
        """Test error handling trong Dart processing."""
        # Test với invalid AST type
        invalid_parsed_file = ParsedFile(
            file_path=self.test_file_path,
            relative_path="lib/main.dart", 
            language="Dart",
            ast_tree="invalid_ast",  # Not DartParseInfo
            parse_success=True,
            nodes_count=1,
            lines_count=10
        )
        
        file_node = self.builder._create_file_node(invalid_parsed_file)
        queries = self.builder._process_dart_file(invalid_parsed_file, file_node)
        
        # Should handle gracefully
        self.assertEqual(len(queries), 0)


if __name__ == '__main__':
    unittest.main() 