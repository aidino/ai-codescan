"""
Unit tests for Java Parser Agent.

Tests Java AST parsing functionality using JavaParser library.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.agents.ckg_operations.java_parser import (
    JavaParserAgent, JavaNode, JavaParseInfo
)


class TestJavaParserAgent:
    """Test cases for JavaParserAgent."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Cleanup after each test method."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_java_file(self, content: str, filename: str = "Test.java") -> Path:
        """Create a test Java file with given content."""
        file_path = Path(self.temp_dir) / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    @patch('subprocess.run')
    def test_find_java_command_success(self, mock_run):
        """Test successful Java command detection."""
        mock_run.return_value = MagicMock(returncode=0)
        
        agent = JavaParserAgent.__new__(JavaParserAgent)  # Skip __init__
        java_cmd = agent._find_java_command()
        
        assert java_cmd in ['java', 'java.exe']
        mock_run.assert_called()
    
    @patch('subprocess.run')
    def test_find_java_command_failure(self, mock_run):
        """Test Java command detection failure."""
        mock_run.side_effect = FileNotFoundError()
        
        agent = JavaParserAgent.__new__(JavaParserAgent)  # Skip __init__
        
        with pytest.raises(RuntimeError, match="Java not found in system PATH"):
            agent._find_java_command()
    
    @patch('src.agents.ckg_operations.java_parser.JavaParserAgent._ensure_javaparser_available')
    @patch('src.agents.ckg_operations.java_parser.JavaParserAgent._find_java_command')
    def test_initialization_success(self, mock_find_java, mock_ensure_jar):
        """Test successful JavaParserAgent initialization."""
        mock_find_java.return_value = 'java'
        mock_ensure_jar.return_value = None
        
        agent = JavaParserAgent()
        
        assert agent.java_cmd == 'java'
        mock_find_java.assert_called_once()
        mock_ensure_jar.assert_called_once()
    
    def test_java_node_creation(self):
        """Test JavaNode dataclass creation."""
        node = JavaNode(
            node_type='ClassDeclaration',
            name='TestClass',
            modifiers=['public'],
            start_line=1,
            end_line=10
        )
        
        assert node.node_type == 'ClassDeclaration'
        assert node.name == 'TestClass'
        assert node.modifiers == ['public']
        assert node.start_line == 1
        assert node.end_line == 10
        assert len(node.children) == 0
        assert len(node.metadata) == 0
    
    def test_java_parse_info_creation(self):
        """Test JavaParseInfo dataclass creation."""
        info = JavaParseInfo(
            package_name='com.example',
            imports=['java.util.List', 'java.io.File'],
            classes=['TestClass'],
            interfaces=['TestInterface'],
            methods=['testMethod'],
            fields=['testField']
        )
        
        assert info.package_name == 'com.example'
        assert len(info.imports) == 2
        assert 'java.util.List' in info.imports
        assert len(info.classes) == 1
        assert len(info.interfaces) == 1
        assert len(info.methods) == 1
        assert len(info.fields) == 1
        assert len(info.dependencies) == 0  # Empty by default
    
    @patch('src.agents.ckg_operations.java_parser.JavaParserAgent._find_java_command')
    @patch('os.path.exists')
    def test_ensure_javaparser_existing_jar(self, mock_exists, mock_find_java):
        """Test JavaParser JAR detection when already exists."""
        mock_find_java.return_value = 'java'
        mock_exists.return_value = True
        
        agent = JavaParserAgent.__new__(JavaParserAgent)
        agent.javaparser_jar_path = '/path/to/existing.jar'
        
        agent._ensure_javaparser_available()
        
        assert agent.javaparser_jar_path == '/path/to/existing.jar'
    
    @patch('src.agents.ckg_operations.java_parser.JavaParserAgent._find_java_command')
    @patch('os.path.exists')
    @patch('requests.get')
    def test_ensure_javaparser_download_success(self, mock_get, mock_exists, mock_find_java):
        """Test successful JavaParser JAR download."""
        mock_find_java.return_value = 'java'
        mock_exists.return_value = False
        
        # Mock successful download
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.iter_content.return_value = [b'jar_content']
        mock_get.return_value = mock_response
        
        agent = JavaParserAgent.__new__(JavaParserAgent)
        agent.javaparser_jar_path = None
        
        with patch('builtins.open', create=True) as mock_open:
            agent._ensure_javaparser_available()
        
        mock_get.assert_called_once()
        assert agent.javaparser_jar_path is not None
        assert 'javaparser-core-3.26.4.jar' in agent.javaparser_jar_path
    
    @patch('src.agents.ckg_operations.java_parser.JavaParserAgent._find_java_command')
    @patch('os.path.exists')
    @patch('requests.get')
    def test_ensure_javaparser_download_failure(self, mock_get, mock_exists, mock_find_java):
        """Test JavaParser JAR download failure."""
        mock_find_java.return_value = 'java'
        mock_exists.return_value = False
        mock_get.side_effect = Exception("Download failed")
        
        agent = JavaParserAgent.__new__(JavaParserAgent)
        agent.javaparser_jar_path = None
        
        with pytest.raises(RuntimeError, match="JavaParser JAR not available"):
            agent._ensure_javaparser_available()
    
    def test_count_file_lines(self):
        """Test file line counting."""
        content = "line1\nline2\nline3\n"
        file_path = self.create_test_java_file(content)
        
        agent = JavaParserAgent.__new__(JavaParserAgent)
        line_count = agent._count_file_lines(str(file_path))
        
        assert line_count == 3  # Three actual lines
    
    def test_count_file_lines_error(self):
        """Test file line counting with non-existent file."""
        agent = JavaParserAgent.__new__(JavaParserAgent)
        line_count = agent._count_file_lines('/non/existent/file.java')
        
        assert line_count == 0
    
    def test_parse_ast_json_simple(self):
        """Test parsing simple AST JSON."""
        ast_json = {
            'node_type': 'CompilationUnit',
            'package': 'com.example',
            'imports': ['java.util.List'],
            'types': [
                {
                    'type': 'ClassOrInterfaceDeclaration',
                    'name': 'TestClass',
                    'isInterface': False,
                    'methods': ['testMethod'],
                    'fields': ['testField']
                }
            ]
        }
        
        agent = JavaParserAgent.__new__(JavaParserAgent)
        java_ast = agent._parse_ast_json(ast_json)
        
        assert java_ast.node_type == 'CompilationUnit'
        assert java_ast.name == 'root'
        assert len(java_ast.children) == 1
        
        class_node = java_ast.children[0]
        assert class_node.node_type == 'ClassOrInterfaceDeclaration'
        assert class_node.name == 'TestClass'
        assert len(class_node.children) == 2  # 1 method + 1 field
    
    def test_extract_java_info(self):
        """Test Java information extraction from AST."""
        java_ast = JavaNode(
            node_type='CompilationUnit',
            name='root',
            metadata={
                'package': 'com.example.test',
                'imports': ['java.util.List', 'java.io.File'],
                'types': [
                    {
                        'name': 'TestClass',
                        'isInterface': False,
                        'methods': ['method1', 'method2'],
                        'fields': ['field1']
                    },
                    {
                        'name': 'TestInterface',
                        'isInterface': True,
                        'methods': ['interfaceMethod'],
                        'fields': []
                    }
                ]
            }
        )
        
        agent = JavaParserAgent.__new__(JavaParserAgent)
        info = agent._extract_java_info(java_ast)
        
        assert info.package_name == 'com.example.test'
        assert len(info.imports) == 2
        assert 'java.util.List' in info.imports
        assert len(info.classes) == 1
        assert 'TestClass' in info.classes
        assert len(info.interfaces) == 1
        assert 'TestInterface' in info.interfaces
        assert len(info.methods) == 3  # 2 from class + 1 from interface
        assert len(info.fields) == 1
        assert len(info.dependencies) == 2  # java.util, java.io
        assert 'java.util' in info.dependencies
        assert 'java.io' in info.dependencies
    
    def test_count_java_nodes(self):
        """Test Java AST node counting."""
        # Create a tree: root -> class -> method + field
        method_node = JavaNode(node_type='MethodDeclaration', name='testMethod')
        field_node = JavaNode(node_type='FieldDeclaration', name='testField')
        class_node = JavaNode(
            node_type='ClassOrInterfaceDeclaration', 
            name='TestClass',
            children=[method_node, field_node]
        )
        root_node = JavaNode(
            node_type='CompilationUnit',
            name='root',
            children=[class_node]
        )
        
        agent = JavaParserAgent.__new__(JavaParserAgent)
        node_count = agent._count_java_nodes(root_node)
        
        assert node_count == 4  # root + class + method + field
    
    @patch('src.agents.ckg_operations.java_parser.JavaParserAgent._run_javaparser')
    def test_parse_java_file_success(self, mock_run_parser):
        """Test successful Java file parsing."""
        # Mock JavaParser output
        mock_run_parser.return_value = {
            'node_type': 'CompilationUnit',
            'package': 'com.example',
            'imports': ['java.util.List'],
            'types': [{
                'type': 'ClassOrInterfaceDeclaration',
                'name': 'TestClass',
                'methods': ['testMethod'],
                'fields': []
            }]
        }
        
        content = '''
package com.example;
import java.util.List;

public class TestClass {
    public void testMethod() {}
}
'''
        file_path = self.create_test_java_file(content)
        
        agent = JavaParserAgent.__new__(JavaParserAgent)
        parsed_file = agent._parse_java_file(str(file_path), 'TestClass.java')
        
        assert parsed_file.parse_success is True
        assert parsed_file.language == 'Java'
        assert parsed_file.relative_path == 'TestClass.java'
        assert parsed_file.nodes_count > 0
        assert parsed_file.lines_count > 0
        assert parsed_file.ast_tree is not None
        
        # Check parse_info
        parse_info = parsed_file.ast_tree['parse_info']
        assert parse_info['package_name'] == 'com.example'
        assert 'java.util.List' in parse_info['imports']
    
    @patch('src.agents.ckg_operations.java_parser.JavaParserAgent._run_javaparser')
    def test_parse_java_file_parser_error(self, mock_run_parser):
        """Test Java file parsing with parser error."""
        import subprocess
        mock_run_parser.side_effect = subprocess.CalledProcessError(
            1, 'java', stderr='Compilation error'
        )
        
        content = "invalid java syntax"
        file_path = self.create_test_java_file(content)
        
        agent = JavaParserAgent.__new__(JavaParserAgent)
        parsed_file = agent._parse_java_file(str(file_path), 'Invalid.java')
        
        assert parsed_file.parse_success is False
        assert parsed_file.language == 'Java'
        assert 'JavaParser error' in parsed_file.error_message
        assert parsed_file.ast_tree is None
    
    @patch('src.agents.ckg_operations.java_parser.JavaParserAgent._run_javaparser')
    def test_parse_java_file_timeout(self, mock_run_parser):
        """Test Java file parsing with timeout."""
        import subprocess
        mock_run_parser.side_effect = subprocess.TimeoutExpired('java', 30)
        
        content = "public class Test {}"
        file_path = self.create_test_java_file(content)
        
        agent = JavaParserAgent.__new__(JavaParserAgent)
        parsed_file = agent._parse_java_file(str(file_path), 'Test.java')
        
        assert parsed_file.parse_success is False
        assert 'timeout' in parsed_file.error_message.lower()
    
    def test_parse_java_files_multiple(self):
        """Test parsing multiple Java files."""
        # Create test files
        file1_content = "public class Test1 {}"
        file2_content = "public class Test2 {}"
        
        file1_path = self.create_test_java_file(file1_content, "Test1.java")
        file2_path = self.create_test_java_file(file2_content, "Test2.java")
        
        java_files = [
            (str(file1_path), "Test1.java"),
            (str(file2_path), "Test2.java")
        ]
        
        # Mock successful parsing for both files
        with patch.object(JavaParserAgent, '_parse_java_file') as mock_parse:
            mock_parse.side_effect = [
                MagicMock(parse_success=True, language='Java'),
                MagicMock(parse_success=True, language='Java')
            ]
            
            agent = JavaParserAgent.__new__(JavaParserAgent)
            parsed_files = agent.parse_java_files(java_files)
            
            assert len(parsed_files) == 2
            assert mock_parse.call_count == 2


class TestJavaNode:
    """Test cases for JavaNode dataclass."""
    
    def test_java_node_defaults(self):
        """Test JavaNode with default values."""
        node = JavaNode(node_type='TestNode')
        
        assert node.node_type == 'TestNode'
        assert node.name is None
        assert node.modifiers == []
        assert node.start_line == 0
        assert node.end_line == 0
        assert node.children == []
        assert node.metadata == {}
    
    def test_java_node_with_children(self):
        """Test JavaNode with children."""
        child1 = JavaNode(node_type='Child1')
        child2 = JavaNode(node_type='Child2')
        
        parent = JavaNode(
            node_type='Parent',
            children=[child1, child2]
        )
        
        assert len(parent.children) == 2
        assert parent.children[0].node_type == 'Child1'
        assert parent.children[1].node_type == 'Child2'


class TestJavaParseInfo:
    """Test cases for JavaParseInfo dataclass."""
    
    def test_java_parse_info_defaults(self):
        """Test JavaParseInfo with default values."""
        info = JavaParseInfo()
        
        assert info.package_name is None
        assert info.imports == []
        assert info.classes == []
        assert info.interfaces == []
        assert info.methods == []
        assert info.fields == []
        assert info.dependencies == []
    
    def test_java_parse_info_with_data(self):
        """Test JavaParseInfo with actual data."""
        info = JavaParseInfo(
            package_name='com.test',
            imports=['java.util.List'],
            classes=['TestClass'],
            interfaces=['TestInterface'],
            methods=['testMethod'],
            fields=['testField'],
            dependencies=['java.util']
        )
        
        assert info.package_name == 'com.test'
        assert len(info.imports) == 1
        assert len(info.classes) == 1
        assert len(info.interfaces) == 1
        assert len(info.methods) == 1
        assert len(info.fields) == 1
        assert len(info.dependencies) == 1 