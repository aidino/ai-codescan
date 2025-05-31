#!/usr/bin/env python3
"""
Tests for ASTtoCKGBuilderAgent with Java support.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from typing import Dict, List, Any

from src.agents.ckg_operations.ast_to_ckg_builder import ASTtoCKGBuilderAgent, CKGBuildResult
from src.agents.ckg_operations.ckg_schema import NodeType, RelationshipType
from src.agents.ckg_operations.code_parser_coordinator import ParseResult, ParsedFile
from src.agents.ckg_operations.java_parser import JavaNode, JavaParseInfo
from src.agents.data_acquisition import LanguageInfo, ProjectLanguageProfile


class TestASTtoCKGBuilderAgentJavaSupport:
    """Test Java support in ASTtoCKGBuilderAgent."""
    
    def setup_method(self):
        """Setup test environment."""
        self.builder = ASTtoCKGBuilderAgent()
        
    def create_mock_java_node(self, node_type: str, name: str = None, 
                             children: List[JavaNode] = None, 
                             metadata: Dict[str, Any] = None) -> JavaNode:
        """Create a mock Java AST node."""
        return JavaNode(
            node_type=node_type,
            name=name,
            modifiers=[],
            start_line=1,
            end_line=10,
            children=children or [],
            metadata=metadata or {}
        )
    
    def create_mock_java_class(self, class_name: str = "TestClass") -> JavaNode:
        """Create a mock Java class node."""
        # Create method child
        method_node = self.create_mock_java_node(
            "MethodDeclaration", 
            "testMethod",
            metadata={"return_type": "void", "parameters": []}
        )
        
        # Create field child
        field_node = self.create_mock_java_node(
            "FieldDeclaration",
            "testField", 
            metadata={"field_type": "String"}
        )
        
        # Create constructor child
        constructor_node = self.create_mock_java_node(
            "ConstructorDeclaration",
            class_name,
            metadata={"parameters": []}
        )
        
        return self.create_mock_java_node(
            "ClassOrInterfaceDeclaration",
            class_name,
            children=[method_node, field_node, constructor_node],
            metadata={"is_interface": False}
        )
    
    def create_mock_java_interface(self, interface_name: str = "TestInterface") -> JavaNode:
        """Create a mock Java interface node."""
        method_node = self.create_mock_java_node(
            "MethodDeclaration",
            "interfaceMethod",
            metadata={"return_type": "void", "parameters": []}
        )
        
        return self.create_mock_java_node(
            "ClassOrInterfaceDeclaration",
            interface_name,
            children=[method_node],
            metadata={"is_interface": True}
        )
    
    def create_mock_java_enum(self, enum_name: str = "TestEnum") -> JavaNode:
        """Create a mock Java enum node."""
        enum_const_node = self.create_mock_java_node(
            "EnumConstantDeclaration",
            "CONSTANT_VALUE",
            metadata={"arguments": [], "ordinal": 0}
        )
        
        return self.create_mock_java_node(
            "EnumDeclaration",
            enum_name,
            children=[enum_const_node]
        )
    
    def create_mock_java_parsed_file(self, java_ast: JavaNode, 
                                    file_path: str = "/test/TestClass.java") -> ParsedFile:
        """Create a mock Java ParsedFile."""
        return ParsedFile(
            file_path=file_path,
            relative_path="TestClass.java",
            language="Java",
            ast_tree=java_ast,
            parse_success=True,
            nodes_count=10,
            lines_count=50
        )
    
    def test_java_class_processing(self):
        """Test processing of Java class nodes."""
        # Create mock Java AST with package and imports
        java_class = self.create_mock_java_class("TestClass")
        root_node = self.create_mock_java_node(
            "CompilationUnit",
            children=[java_class],
            metadata={
                "package_name": "com.test",
                "imports": ["java.util.List", "java.io.File"]
            }
        )
        
        parsed_file = self.create_mock_java_parsed_file(root_node)
        
        # Process the file
        queries = self.builder._process_file(parsed_file)
        
        # Verify queries were generated
        assert len(queries) > 0
        
        # Verify nodes were created
        assert len(self.builder.created_nodes) > 0
        
        # Verify Java-specific node types exist
        node_types = [node.type for node in self.builder.created_nodes.values()]
        assert NodeType.FILE in node_types
        assert NodeType.JAVA_PACKAGE in node_types
        assert NodeType.JAVA_IMPORT in node_types
        assert NodeType.JAVA_CLASS in node_types
        assert NodeType.JAVA_METHOD in node_types
        assert NodeType.JAVA_FIELD in node_types
        assert NodeType.JAVA_CONSTRUCTOR in node_types
        
        # Verify relationships were created
        assert len(self.builder.created_relationships) > 0
        
        rel_types = [rel.type for rel in self.builder.created_relationships]
        assert RelationshipType.BELONGS_TO in rel_types  # File to Package
        assert RelationshipType.IMPORTS in rel_types     # File to Imports
        assert RelationshipType.DEFINES_JAVA_CLASS in rel_types
        assert RelationshipType.DEFINES_JAVA_METHOD in rel_types
        assert RelationshipType.DEFINES_JAVA_FIELD in rel_types
        assert RelationshipType.DEFINES_JAVA_CONSTRUCTOR in rel_types
    
    def test_java_interface_processing(self):
        """Test processing of Java interface nodes."""
        java_interface = self.create_mock_java_interface("TestInterface")
        root_node = self.create_mock_java_node(
            "CompilationUnit",
            children=[java_interface],
            metadata={"package_name": "com.test"}
        )
        
        parsed_file = self.create_mock_java_parsed_file(root_node)
        
        # Process the file
        queries = self.builder._process_file(parsed_file)
        
        # Verify interface node was created
        node_types = [node.type for node in self.builder.created_nodes.values()]
        assert NodeType.JAVA_INTERFACE in node_types
        
        # Verify interface relationship was created
        rel_types = [rel.type for rel in self.builder.created_relationships]
        assert RelationshipType.DEFINES_JAVA_INTERFACE in rel_types
    
    def test_java_enum_processing(self):
        """Test processing of Java enum nodes."""
        java_enum = self.create_mock_java_enum("TestEnum")
        root_node = self.create_mock_java_node(
            "CompilationUnit",
            children=[java_enum]
        )
        
        parsed_file = self.create_mock_java_parsed_file(root_node)
        
        # Process the file
        queries = self.builder._process_file(parsed_file)
        
        # Verify enum nodes were created
        node_types = [node.type for node in self.builder.created_nodes.values()]
        assert NodeType.JAVA_ENUM in node_types
        assert NodeType.JAVA_ENUM_CONSTANT in node_types
        
        # Verify enum relationships
        rel_types = [rel.type for rel in self.builder.created_relationships]
        assert RelationshipType.DEFINES_JAVA_CLASS in rel_types  # Enum treated as class
        assert RelationshipType.CONTAINS in rel_types  # Enum contains constants
    
    def test_java_package_node_creation(self):
        """Test Java package node creation."""
        parsed_file = self.create_mock_java_parsed_file(
            self.create_mock_java_node("CompilationUnit")
        )
        
        package_node = self.builder._create_java_package_node("com.test.example", parsed_file)
        
        assert package_node.name == "example"  # Last part of package
        assert package_node.type == NodeType.JAVA_PACKAGE
        assert package_node.properties['full_name'] == "com.test.example"
        assert package_node.properties['id'] is not None
    
    def test_java_import_node_creation(self):
        """Test Java import node creation."""
        parsed_file = self.create_mock_java_parsed_file(
            self.create_mock_java_node("CompilationUnit")
        )
        
        # Test regular import
        import_node = self.builder._create_java_import_node("java.util.List", parsed_file)
        
        assert import_node.name == "List"
        assert import_node.type == NodeType.JAVA_IMPORT
        assert import_node.properties['imported_name'] == "java.util.List"
        assert not import_node.properties['is_static_import']
        assert not import_node.properties['is_wildcard_import']
        
        # Test wildcard import
        wildcard_import = self.builder._create_java_import_node("java.util.*", parsed_file)
        assert wildcard_import.properties['is_wildcard_import']
        
        # Test static import
        static_import = self.builder._create_java_import_node("static java.lang.Math.PI", parsed_file)
        assert static_import.properties['is_static_import']
    
    def test_java_class_node_creation(self):
        """Test Java class node creation."""
        parsed_file = self.create_mock_java_parsed_file(
            self.create_mock_java_node("CompilationUnit")
        )
        package_node = self.builder._create_java_package_node("com.test", parsed_file)
        
        java_class_node = JavaNode(
            node_type="ClassOrInterfaceDeclaration",
            name="TestClass",
            modifiers=["public", "final"],
            start_line=5,
            end_line=25,
            children=[
                JavaNode(node_type="MethodDeclaration", name="method1"),
                JavaNode(node_type="FieldDeclaration", name="field1"),
                JavaNode(node_type="ConstructorDeclaration", name="TestClass")
            ]
        )
        
        class_node = self.builder._create_java_class_node(java_class_node, parsed_file, package_node)
        
        assert class_node.name == "TestClass"
        assert class_node.type == NodeType.JAVA_CLASS
        assert class_node.line_number == 5
        assert class_node.end_line_number == 25
        assert class_node.properties['package_name'] == "test"
        assert class_node.properties['full_name'] == "test.TestClass"
        assert class_node.properties['modifiers'] == ["public", "final"]
        assert class_node.properties['is_final']
        assert not class_node.properties['is_abstract']
        assert class_node.properties['methods_count'] == 1
        assert class_node.properties['fields_count'] == 1
        assert class_node.properties['constructors_count'] == 1
    
    def test_java_method_node_creation(self):
        """Test Java method node creation."""
        parsed_file = self.create_mock_java_parsed_file(
            self.create_mock_java_node("CompilationUnit")
        )
        
        java_method_node = JavaNode(
            node_type="MethodDeclaration",
            name="testMethod",
            modifiers=["public", "static"],
            start_line=10,
            end_line=15,
            metadata={
                "return_type": "String",
                "parameters": ["String arg1", "int arg2"]
            }
        )
        
        method_node = self.builder._create_java_method_node(java_method_node, parsed_file)
        
        assert method_node.name == "testMethod"
        assert method_node.type == NodeType.JAVA_METHOD
        assert method_node.properties['return_type'] == "String"
        assert method_node.properties['parameters'] == ["String arg1", "int arg2"]
        assert method_node.properties['is_static']
        assert not method_node.properties['is_abstract']
    
    def test_java_field_node_creation(self):
        """Test Java field node creation."""
        parsed_file = self.create_mock_java_parsed_file(
            self.create_mock_java_node("CompilationUnit")
        )
        
        java_field_node = JavaNode(
            node_type="FieldDeclaration",
            name="testField",
            modifiers=["private", "static", "final"],
            start_line=8,
            end_line=8,
            metadata={"field_type": "String"}
        )
        
        field_node = self.builder._create_java_field_node(java_field_node, parsed_file)
        
        assert field_node.name == "testField"
        assert field_node.type == NodeType.JAVA_FIELD
        assert field_node.properties['field_type'] == "String"
        assert field_node.properties['is_static']
        assert field_node.properties['is_final']
        assert not field_node.properties['is_volatile']
    
    def test_java_constructor_node_creation(self):
        """Test Java constructor node creation."""
        parsed_file = self.create_mock_java_parsed_file(
            self.create_mock_java_node("CompilationUnit")
        )
        
        java_constructor_node = JavaNode(
            node_type="ConstructorDeclaration",
            name="TestClass",
            modifiers=["public"],
            start_line=12,
            end_line=15,
            metadata={"parameters": ["String name", "int age"]}
        )
        
        constructor_node = self.builder._create_java_constructor_node(java_constructor_node, parsed_file)
        
        assert constructor_node.name == "TestClass"
        assert constructor_node.type == NodeType.JAVA_CONSTRUCTOR
        assert constructor_node.properties['parameters'] == ["String name", "int age"]
        assert constructor_node.properties['modifiers'] == ["public"]
    
    def test_java_enum_constant_node_creation(self):
        """Test Java enum constant node creation."""
        parsed_file = self.create_mock_java_parsed_file(
            self.create_mock_java_node("CompilationUnit")
        )
        
        java_enum_const_node = JavaNode(
            node_type="EnumConstantDeclaration",
            name="CONSTANT_VALUE",
            start_line=5,
            end_line=5,
            metadata={"arguments": ["arg1", "arg2"], "ordinal": 0}
        )
        
        enum_const_node = self.builder._create_java_enum_constant_node(java_enum_const_node, parsed_file)
        
        assert enum_const_node.name == "CONSTANT_VALUE"
        assert enum_const_node.type == NodeType.JAVA_ENUM_CONSTANT
        assert enum_const_node.properties['arguments'] == ["arg1", "arg2"]
        assert enum_const_node.properties['ordinal'] == 0
    
    def test_build_ckg_from_parse_result_java(self):
        """Test building CKG from Java ParseResult."""
        # Create a complete Java AST structure
        java_class = self.create_mock_java_class("TestClass")
        java_interface = self.create_mock_java_interface("TestInterface")
        java_enum = self.create_mock_java_enum("TestEnum")
        
        root_node = self.create_mock_java_node(
            "CompilationUnit",
            children=[java_class, java_interface, java_enum],
            metadata={
                "package_name": "com.test.example",
                "imports": ["java.util.List", "java.io.File"]
            }
        )
        
        parsed_file = self.create_mock_java_parsed_file(root_node, "/test/TestFile.java")
        
        # Create mock language profile
        java_lang_info = LanguageInfo(
            name="Java",
            percentage=100.0,
            file_count=1,
            total_lines=50
        )
        
        mock_language_profile = ProjectLanguageProfile(
            primary_language="Java",
            languages=[java_lang_info],
            frameworks=[],
            build_tools=[],
            package_managers=[],
            project_type="library",
            confidence_score=0.9
        )
        
        parse_result = ParseResult(
            project_path="/test",
            language_profile=mock_language_profile,
            total_files=1,
            successful_files=1,
            failed_files=0,
            parsed_files=[parsed_file],
            parse_errors=[],
            parsing_stats={"primary_language": "Java"}
        )
        
        # Build CKG
        result = self.builder.build_ckg_from_parse_result(parse_result)
        
        # Verify result
        assert result.build_success
        assert result.cypher_queries_executed >= 0
        assert result.total_nodes_created > 0
        assert result.total_relationships_created > 0
    
    def test_java_processing_with_no_java_node_import(self):
        """Test Java processing when JavaNode is not available."""
        # Mock JavaNode as None to simulate import failure
        with patch('src.agents.ckg_operations.ast_to_ckg_builder.JavaNode', None):
            builder = ASTtoCKGBuilderAgent()
            
            parsed_file = ParsedFile(
                file_path="/test/TestClass.java",
                relative_path="TestClass.java",
                language="Java",
                ast_tree=Mock(),  # Mock AST
                parse_success=True,
                nodes_count=10,
                lines_count=50
            )
            
            queries = builder._process_file(parsed_file)
            
            # Should only create File node, no Java-specific processing
            assert len(queries) == 1  # Only File node creation
            assert len(builder.created_nodes) == 1
            
            file_node = list(builder.created_nodes.values())[0]
            assert file_node.type == NodeType.FILE
    
    def test_java_processing_with_invalid_ast_type(self):
        """Test Java processing with invalid AST type."""
        parsed_file = ParsedFile(
            file_path="/test/TestClass.java",
            relative_path="TestClass.java", 
            language="Java",
            ast_tree="invalid_ast_type",  # String instead of JavaNode
            parse_success=True,
            nodes_count=10,
            lines_count=50
        )
        
        queries = self.builder._process_file(parsed_file)
        
        # Should only create File node due to invalid AST type
        assert len(queries) == 1  # Only File node creation
        assert len(self.builder.created_nodes) == 1
    
    def test_mixed_language_processing(self):
        """Test processing ParseResult with both Python and Java files."""
        # Create Python ParsedFile
        python_ast = Mock()  # Mock Python AST
        python_file = ParsedFile(
            file_path="/test/test.py",
            relative_path="test.py",
            language="Python",
            ast_tree=python_ast,
            parse_success=True,
            nodes_count=5,
            lines_count=25
        )
        
        # Create Java ParsedFile  
        java_class = self.create_mock_java_class("TestClass")
        java_file = self.create_mock_java_parsed_file(java_class, "/test/TestClass.java")
        
        # Create mock language profile for mixed languages
        python_lang_info = LanguageInfo(
            name="Python",
            percentage=60.0,
            file_count=1,
            total_lines=25
        )
        
        java_lang_info = LanguageInfo(
            name="Java", 
            percentage=40.0,
            file_count=1,
            total_lines=50
        )
        
        mock_language_profile = ProjectLanguageProfile(
            primary_language="Python",
            languages=[python_lang_info, java_lang_info],
            frameworks=[],
            build_tools=[],
            package_managers=[],
            project_type="library",
            confidence_score=0.8
        )
        
        parse_result = ParseResult(
            project_path="/test",
            language_profile=mock_language_profile,
            total_files=2,
            successful_files=2,
            failed_files=0,
            parsed_files=[python_file, java_file],
            parse_errors=[],
            parsing_stats={"primary_language": "Python"}
        )
        
        # Build CKG
        result = self.builder.build_ckg_from_parse_result(parse_result)
        
        # Verify mixed language processing
        assert result.build_success
        assert result.cypher_queries_executed >= 0
        assert result.total_nodes_created >= 2  # At least File nodes for both languages


if __name__ == "__main__":
    pytest.main([__file__]) 