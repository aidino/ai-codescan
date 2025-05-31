#!/usr/bin/env python3
"""
Unit tests for CKG Operations components.

Tests for:
- CKG Schema definitions
- Code Parser Coordinator (AST parsing)
- AST to CKG Builder (graph construction)
- CKG Query Interface (Neo4j operations)
"""

import ast
import tempfile
import shutil
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.ckg_operations.ckg_schema import (
    NodeType, RelationshipType, CKGNode, CKGRelationship,
    CKGSchema, create_file_node, create_function_node,
    create_class_node, create_import_relationship
)
from agents.ckg_operations.code_parser_coordinator import (
    CodeParserCoordinatorAgent, ParseResult
)
from agents.ckg_operations.ast_to_ckg_builder import (
    ASTtoCKGBuilderAgent, BuildResult
)
from agents.ckg_operations.ckg_query_interface import (
    CKGQueryInterfaceAgent, QueryResult
)


class TestCKGSchema:
    """Test CKG Schema definitions và utility functions."""
    
    def test_node_types_enum(self):
        """Test NodeType enum values."""
        assert NodeType.FILE.value == "File"
        assert NodeType.FUNCTION.value == "Function"
        assert NodeType.CLASS.value == "Class"
        assert NodeType.MODULE.value == "Module"
        
    def test_relationship_types_enum(self):
        """Test RelationshipType enum values."""
        assert RelationshipType.IMPORTS.value == "IMPORTS"
        assert RelationshipType.CALLS.value == "CALLS"
        assert RelationshipType.DEFINES_FUNCTION.value == "DEFINES_FUNCTION"
        assert RelationshipType.DEFINES_CLASS.value == "DEFINES_CLASS"
        
    def test_ckg_node_creation(self):
        """Test CKGNode creation với properties."""
        node = CKGNode(
            id="test_node",
            type=NodeType.FUNCTION,
            properties={"name": "test_function", "line_number": 10}
        )
        assert node.id == "test_node"
        assert node.type == NodeType.FUNCTION
        assert node.properties["name"] == "test_function"
        assert node.properties["line_number"] == 10
        
    def test_ckg_relationship_creation(self):
        """Test CKGRelationship creation."""
        rel = CKGRelationship(
            type=RelationshipType.CALLS,
            source_id="func1",
            target_id="func2",
            properties={"line_number": 15}
        )
        assert rel.type == RelationshipType.CALLS
        assert rel.source_id == "func1"
        assert rel.target_id == "func2"
        assert rel.properties["line_number"] == 15
        
    def test_create_file_node(self):
        """Test file node creation utility."""
        node = create_file_node("test.py", "/path/to/test.py", 100, "python")
        assert node.type == NodeType.FILE
        assert node.properties["name"] == "test.py"
        assert node.properties["path"] == "/path/to/test.py"
        assert node.properties["line_count"] == 100
        assert node.properties["language"] == "python"
        
    def test_create_function_node(self):
        """Test function node creation utility."""
        node = create_function_node("test_func", "test.py", 10, 20, ["arg1", "arg2"])
        assert node.type == NodeType.FUNCTION
        assert node.properties["name"] == "test_func"
        assert node.properties["file_path"] == "test.py"
        assert node.properties["start_line"] == 10
        assert node.properties["end_line"] == 20
        assert node.properties["parameters"] == ["arg1", "arg2"]
        
    def test_create_class_node(self):
        """Test class node creation utility."""
        node = create_class_node("TestClass", "test.py", 5, 25, ["BaseClass"])
        assert node.type == NodeType.CLASS
        assert node.properties["name"] == "TestClass"
        assert node.properties["file_path"] == "test.py"
        assert node.properties["start_line"] == 5
        assert node.properties["end_line"] == 25
        assert node.properties["base_classes"] == ["BaseClass"]
        
    def test_create_import_relationship(self):
        """Test import relationship creation utility."""
        rel = create_import_relationship("file1.py", "module2", "import module2", 1)
        assert rel.type == RelationshipType.IMPORTS
        assert rel.source_id == "file1.py"
        assert rel.target_id == "module2"
        assert rel.properties["import_statement"] == "import module2"
        assert rel.properties["line_number"] == 1


class TestCodeParserCoordinatorAgent:
    """Test CodeParserCoordinatorAgent AST parsing functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.agent = CodeParserCoordinatorAgent()
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Cleanup test fixtures."""
        shutil.rmtree(self.temp_dir)
        
    def create_test_python_file(self, content: str, filename: str = "test.py") -> Path:
        """Create temporary Python file với content."""
        file_path = Path(self.temp_dir) / filename
        file_path.write_text(content)
        return file_path
        
    def test_init(self):
        """Test agent initialization."""
        assert self.agent is not None
        assert hasattr(self.agent, 'parse_python_project')
        
    def test_parse_simple_python_file(self):
        """Test parsing simple Python file."""
        content = """
def hello_world():
    print("Hello, World!")
    
class TestClass:
    def method(self):
        pass
"""
        file_path = self.create_test_python_file(content)
        
        result = self.agent.parse_python_project(str(file_path.parent))
        
        assert isinstance(result, ParseResult)
        assert result.success
        assert len(result.parsed_files) == 1
        assert file_path.name in result.parsed_files
        assert result.total_files == 1
        assert result.total_lines > 0
        
    def test_parse_python_file_with_imports(self):
        """Test parsing Python file với imports."""
        content = """
import os
from pathlib import Path
import sys as system

def main():
    pass
"""
        file_path = self.create_test_python_file(content)
        
        result = self.agent.parse_python_project(str(file_path.parent))
        
        assert result.success
        assert len(result.parsed_files) == 1
        # Check that imports were detected in AST
        ast_data = result.parsed_files[file_path.name]
        assert ast_data is not None
        
    def test_parse_invalid_python_file(self):
        """Test parsing invalid Python syntax."""
        content = """
def invalid_syntax(
    print("Missing closing parenthesis")
"""
        file_path = self.create_test_python_file(content)
        
        result = self.agent.parse_python_project(str(file_path.parent))
        
        # Should handle parsing errors gracefully
        assert isinstance(result, ParseResult)
        assert len(result.parsing_errors) > 0
        
    def test_parse_empty_directory(self):
        """Test parsing empty directory."""
        result = self.agent.parse_python_project(self.temp_dir)
        
        assert result.success
        assert len(result.parsed_files) == 0
        assert result.total_files == 0
        
    def test_parse_multiple_python_files(self):
        """Test parsing multiple Python files."""
        content1 = "def func1(): pass"
        content2 = "class Class2: pass"
        
        self.create_test_python_file(content1, "file1.py")
        self.create_test_python_file(content2, "file2.py")
        
        result = self.agent.parse_python_project(self.temp_dir)
        
        assert result.success
        assert len(result.parsed_files) == 2
        assert result.total_files == 2
        assert "file1.py" in result.parsed_files
        assert "file2.py" in result.parsed_files


class TestASTtoCKGBuilderAgent:
    """Test ASTtoCKGBuilderAgent graph building functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.agent = ASTtoCKGBuilderAgent()
        
    @patch('agents.ckg_operations.ast_to_ckg_builder.neo4j.GraphDatabase')
    def test_init_with_mock_neo4j(self, mock_neo4j):
        """Test agent initialization với mocked Neo4j."""
        mock_driver = Mock()
        mock_neo4j.driver.return_value = mock_driver
        
        agent = ASTtoCKGBuilderAgent()
        assert agent is not None
        
    def test_extract_functions_from_ast(self):
        """Test extracting functions từ AST node."""
        code = """
def hello():
    pass
    
def world(arg1, arg2):
    return arg1 + arg2
"""
        tree = ast.parse(code)
        
        functions = self.agent._extract_functions_from_ast(tree, "test.py")
        
        assert len(functions) == 2
        assert functions[0].properties["name"] == "hello"
        assert functions[1].properties["name"] == "world"
        assert functions[1].properties["parameters"] == ["arg1", "arg2"]
        
    def test_extract_classes_from_ast(self):
        """Test extracting classes từ AST node."""
        code = """
class BaseClass:
    pass
    
class DerivedClass(BaseClass):
    def method(self):
        pass
"""
        tree = ast.parse(code)
        
        classes = self.agent._extract_classes_from_ast(tree, "test.py")
        
        assert len(classes) == 2
        assert classes[0].properties["name"] == "BaseClass"
        assert classes[1].properties["name"] == "DerivedClass"
        assert "BaseClass" in classes[1].properties["base_classes"]
        
    def test_extract_imports_from_ast(self):
        """Test extracting imports từ AST node."""
        code = """
import os
from pathlib import Path
import sys as system
"""
        tree = ast.parse(code)
        
        imports = self.agent._extract_imports_from_ast(tree, "test.py")
        
        assert len(imports) >= 3  # May include more detailed import relationships
        
    def test_generate_cypher_queries(self):
        """Test Cypher query generation."""
        # Create sample nodes and relationships
        nodes = [
            create_file_node("test.py", "/path/test.py", 10, "python"),
            create_function_node("test_func", "test.py", 1, 5, ["arg1"])
        ]
        relationships = [
            create_import_relationship("test.py", "os", "import os", 1)
        ]
        
        queries = self.agent._generate_cypher_queries(nodes, relationships)
        
        assert len(queries) > 0
        assert any("CREATE" in query or "MERGE" in query for query in queries)
        
    @patch('agents.ckg_operations.ast_to_ckg_builder.neo4j.GraphDatabase')
    def test_build_ckg_from_parse_result(self, mock_neo4j):
        """Test building CKG từ parse result."""
        # Mock Neo4j driver và session
        mock_driver = Mock()
        mock_session = Mock()
        mock_neo4j.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Create mock parse result
        parse_result = ParseResult(
            success=True,
            parsed_files={"test.py": ast.parse("def test(): pass")},
            total_files=1,
            total_lines=2,
            parsing_errors=[]
        )
        
        result = self.agent.build_ckg_from_parse_result(parse_result)
        
        assert isinstance(result, BuildResult)
        # Should attempt to create nodes và relationships
        assert mock_session.run.called


class TestCKGQueryInterfaceAgent:
    """Test CKGQueryInterfaceAgent Neo4j query functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        # Create agent với mock connection
        with patch('agents.ckg_operations.ckg_query_interface.neo4j.GraphDatabase'):
            self.agent = CKGQueryInterfaceAgent()
            
    @patch('agents.ckg_operations.ckg_query_interface.neo4j.GraphDatabase')
    def test_init_connection(self, mock_neo4j):
        """Test Neo4j connection initialization."""
        mock_driver = Mock()
        mock_neo4j.driver.return_value = mock_driver
        
        agent = CKGQueryInterfaceAgent()
        assert agent is not None
        
    def test_get_functions_in_file(self):
        """Test querying functions trong file."""
        # Mock session và results
        mock_session = Mock()
        mock_result = Mock()
        mock_record = Mock()
        mock_record.__getitem__.return_value = "test_function"
        mock_result.__iter__.return_value = [mock_record]
        mock_session.run.return_value = mock_result
        
        with patch.object(self.agent, '_get_session', return_value=mock_session):
            result = self.agent.get_functions_in_file("test.py")
            
        assert isinstance(result, QueryResult)
        mock_session.run.assert_called_once()
        
    def test_get_classes_in_file(self):
        """Test querying classes trong file."""
        mock_session = Mock()
        mock_result = Mock()
        mock_record = Mock()
        mock_record.__getitem__.return_value = "TestClass"
        mock_result.__iter__.return_value = [mock_record]
        mock_session.run.return_value = mock_result
        
        with patch.object(self.agent, '_get_session', return_value=mock_session):
            result = self.agent.get_classes_in_file("test.py")
            
        assert isinstance(result, QueryResult)
        mock_session.run.assert_called_once()
        
    def test_find_function_callers(self):
        """Test finding function callers."""
        mock_session = Mock()
        mock_result = Mock()
        mock_result.__iter__.return_value = []
        mock_session.run.return_value = mock_result
        
        with patch.object(self.agent, '_get_session', return_value=mock_session):
            result = self.agent.find_function_callers("test_function")
            
        assert isinstance(result, QueryResult)
        mock_session.run.assert_called_once()
        
    def test_find_circular_dependencies(self):
        """Test circular dependency detection."""
        mock_session = Mock()
        mock_result = Mock()
        mock_result.__iter__.return_value = []
        mock_session.run.return_value = mock_result
        
        with patch.object(self.agent, '_get_session', return_value=mock_session):
            result = self.agent.find_circular_dependencies()
            
        assert isinstance(result, QueryResult)
        mock_session.run.assert_called_once()
        
    def test_get_project_statistics(self):
        """Test project statistics query."""
        mock_session = Mock()
        mock_result = Mock()
        mock_record = Mock()
        mock_record.data.return_value = {"total_files": 5, "total_functions": 20}
        mock_result.__iter__.return_value = [mock_record]
        mock_session.run.return_value = mock_result
        
        with patch.object(self.agent, '_get_session', return_value=mock_session):
            result = self.agent.get_project_statistics()
            
        assert isinstance(result, QueryResult)
        mock_session.run.assert_called_once()
        
    def test_search_by_name(self):
        """Test searching code elements by name."""
        mock_session = Mock()
        mock_result = Mock()
        mock_result.__iter__.return_value = []
        mock_session.run.return_value = mock_result
        
        with patch.object(self.agent, '_get_session', return_value=mock_session):
            result = self.agent.search_by_name("test.*")
            
        assert isinstance(result, QueryResult)
        mock_session.run.assert_called_once()
        
    def test_query_result_creation(self):
        """Test QueryResult dataclass creation."""
        result = QueryResult(
            success=True,
            data=[{"name": "test"}],
            query="MATCH (n) RETURN n",
            execution_time=0.1,
            error_message=None
        )
        
        assert result.success
        assert len(result.data) == 1
        assert result.query == "MATCH (n) RETURN n"
        assert result.execution_time == 0.1
        assert result.error_message is None


class TestCKGIntegration:
    """Integration tests cho CKG Operations workflow."""
    
    def setup_method(self):
        """Setup integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Cleanup integration test fixtures."""
        shutil.rmtree(self.temp_dir)
        
    def create_test_project(self):
        """Create test Python project với multiple files."""
        # Main module
        main_content = """
import helper
from utils import utility_function

def main():
    helper.process_data()
    result = utility_function("test")
    return result

if __name__ == "__main__":
    main()
"""
        
        # Helper module
        helper_content = """
def process_data():
    return "processed"
    
class DataProcessor:
    def __init__(self):
        self.data = []
        
    def add_item(self, item):
        self.data.append(item)
"""
        
        # Utils module
        utils_content = """
def utility_function(value):
    return f"Utility: {value}"
    
def helper_function():
    pass
"""
        
        Path(self.temp_dir, "main.py").write_text(main_content)
        Path(self.temp_dir, "helper.py").write_text(helper_content)
        Path(self.temp_dir, "utils.py").write_text(utils_content)
        
    @patch('agents.ckg_operations.ast_to_ckg_builder.neo4j.GraphDatabase')
    @patch('agents.ckg_operations.ckg_query_interface.neo4j.GraphDatabase')
    def test_complete_ckg_workflow(self, mock_query_neo4j, mock_builder_neo4j):
        """Test complete CKG workflow từ parsing đến querying."""
        # Setup mocks
        mock_driver = Mock()
        mock_session = Mock()
        mock_query_neo4j.driver.return_value = mock_driver
        mock_builder_neo4j.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Create test project
        self.create_test_project()
        
        # Step 1: Parse project
        parser = CodeParserCoordinatorAgent()
        parse_result = parser.parse_python_project(self.temp_dir)
        
        assert parse_result.success
        assert len(parse_result.parsed_files) == 3
        
        # Step 2: Build CKG
        builder = ASTtoCKGBuilderAgent()
        build_result = builder.build_ckg_from_parse_result(parse_result)
        
        assert isinstance(build_result, BuildResult)
        
        # Step 3: Query CKG
        query_interface = CKGQueryInterfaceAgent()
        
        # Mock query results
        mock_result = Mock()
        mock_result.__iter__.return_value = []
        mock_session.run.return_value = mock_result
        
        with patch.object(query_interface, '_get_session', return_value=mock_session):
            functions_result = query_interface.get_functions_in_file("main.py")
            stats_result = query_interface.get_project_statistics()
            
        assert isinstance(functions_result, QueryResult)
        assert isinstance(stats_result, QueryResult)
        
        # Verify that Neo4j operations were called
        assert mock_session.run.called


if __name__ == "__main__":
    pytest.main([__file__]) 