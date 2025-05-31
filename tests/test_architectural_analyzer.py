#!/usr/bin/env python3
"""
Unit tests cho ArchitecturalAnalyzerAgent.

Test cases cover:
- Circular dependency detection
- Unused public element detection  
- Graph algorithms
- Error handling
- Result formatting
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.code_analysis.architectural_analyzer import (
    ArchitecturalAnalyzerAgent,
    ArchitecturalIssue,
    ArchitecturalAnalysisResult,
    CircularDependency,
    UnusedElement,
    IssueType,
    SeverityLevel
)
from src.agents.ckg_operations.ckg_query_interface import CKGQueryResult


class TestArchitecturalAnalyzerAgent(unittest.TestCase):
    """Test cases cho ArchitecturalAnalyzerAgent."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_ckg_agent = Mock()
        self.analyzer = ArchitecturalAnalyzerAgent(ckg_query_agent=self.mock_ckg_agent)

    def test_init_with_ckg_agent(self):
        """Test khởi tạo với CKGQueryInterfaceAgent được cung cấp."""
        mock_agent = Mock()
        analyzer = ArchitecturalAnalyzerAgent(ckg_query_agent=mock_agent)
        
        self.assertEqual(analyzer.ckg_query_agent, mock_agent)
        self.assertIsNotNone(analyzer.logger)
        self.assertEqual(len(analyzer.static_analysis_limitations), 5)

    def test_init_without_ckg_agent(self):
        """Test khởi tạo mà không cung cấp CKGQueryInterfaceAgent."""
        with patch('src.agents.code_analysis.architectural_analyzer.CKGQueryInterfaceAgent') as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            
            analyzer = ArchitecturalAnalyzerAgent()
            
            mock_class.assert_called_once()
            self.assertEqual(analyzer.ckg_query_agent, mock_instance)

    def test_analyze_architecture_success(self):
        """Test phân tích kiến trúc thành công."""
        # Mock data cho dependencies
        dependency_data = [
            {"source_file": "a.py", "target_file": "b.py"},
            {"source_file": "b.py", "target_file": "c.py"},
            {"source_file": "c.py", "target_file": "a.py"}  # Circular
        ]
        
        # Mock data cho unused functions
        unused_function_data = [
            {"name": "unused_func", "file_path": "utils.py", "line_number": 10}
        ]
        
        # Mock CKG query results
        self.mock_ckg_agent.execute_query.return_value = CKGQueryResult(
            query="test", results=dependency_data, total_count=3, 
            execution_time_ms=50.0, success=True
        )
        
        self.mock_ckg_agent.get_unused_public_functions.return_value = CKGQueryResult(
            query="test", results=unused_function_data, total_count=1,
            execution_time_ms=30.0, success=True
        )
        
        # Run analysis
        result = self.analyzer.analyze_architecture("/test/project")
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.project_path, "/test/project")
        self.assertGreater(result.total_issues, 0)
        self.assertGreater(len(result.circular_dependencies), 0)
        self.assertGreater(len(result.unused_elements), 0)
        self.assertIsInstance(result.execution_time_seconds, float)

    def test_analyze_architecture_complete_failure(self):
        """Test complete failure trong analyze_architecture method."""
        # Mock để method chính bị lỗi ngay từ đầu
        with patch.object(self.analyzer, '_analyze_circular_dependencies', side_effect=Exception("Critical error")):
            result = self.analyzer.analyze_architecture("/test/project")
        
            # Trong trường hợp này, exception được catch bởi main try-catch
            self.assertFalse(result.success)
            self.assertIsNotNone(result.error_message)
            self.assertEqual(result.total_issues, 0)
            self.assertEqual(len(result.circular_dependencies), 0)
            self.assertEqual(len(result.unused_elements), 0)

    def test_analyze_architecture_error(self):
        """Test xử lý lỗi trong phân tích kiến trúc với graceful degradation."""
        # Mock lỗi trong CKG query - set cho tất cả methods
        self.mock_ckg_agent.execute_query.side_effect = Exception("Database error")
        self.mock_ckg_agent.get_unused_public_functions.side_effect = Exception("Database error")
        
        result = self.analyzer.analyze_architecture("/test/project")
        
        # Với graceful degradation, analysis vẫn success nhưng không có results
        self.assertTrue(result.success)  # Graceful degradation
        self.assertEqual(result.total_issues, 0)  # Không có issues do errors
        self.assertEqual(len(result.circular_dependencies), 0)
        self.assertEqual(len(result.unused_elements), 0)
        self.assertIsInstance(result.execution_time_seconds, float)

    def test_build_dependency_graph(self):
        """Test xây dựng dependency graph."""
        dependency_data = [
            {"source_file": "a.py", "target_file": "b.py"},
            {"source_file": "b.py", "target_file": "c.py"},
            {"source_file": "a.py", "target_file": "c.py"}
        ]
        
        graph = self.analyzer._build_dependency_graph(dependency_data)
        
        expected_graph = {
            "a.py": {"b.py", "c.py"},
            "b.py": {"c.py"},
            "c.py": set()
        }
        
        self.assertEqual(graph, expected_graph)

    def test_build_dependency_graph_empty(self):
        """Test xây dựng dependency graph từ data rỗng."""
        graph = self.analyzer._build_dependency_graph([])
        self.assertEqual(graph, {})

    def test_find_cycles_in_graph_with_cycle(self):
        """Test tìm cycles trong graph có cycle."""
        graph = {
            "A": {"B"},
            "B": {"C"},
            "C": {"A"}  # Cycle: A -> B -> C -> A
        }
        
        cycles = self.analyzer._find_cycles_in_graph(graph)
        
        self.assertEqual(len(cycles), 1)
        cycle = cycles[0]
        self.assertIn("A", cycle)
        self.assertIn("B", cycle)
        self.assertIn("C", cycle)

    def test_find_cycles_in_graph_without_cycle(self):
        """Test tìm cycles trong graph không có cycle."""
        graph = {
            "A": {"B"},
            "B": {"C"},
            "C": set()
        }
        
        cycles = self.analyzer._find_cycles_in_graph(graph)
        self.assertEqual(len(cycles), 0)

    def test_find_cycles_in_graph_empty(self):
        """Test tìm cycles trong graph rỗng."""
        cycles = self.analyzer._find_cycles_in_graph({})
        self.assertEqual(len(cycles), 0)

    def test_find_cycles_in_graph_multiple_cycles(self):
        """Test tìm multiple cycles trong graph."""
        graph = {
            "A": {"B"},
            "B": {"A"},  # Cycle 1: A -> B -> A
            "C": {"D"},
            "D": {"E"},
            "E": {"C"}   # Cycle 2: C -> D -> E -> C
        }
        
        cycles = self.analyzer._find_cycles_in_graph(graph)
        self.assertGreaterEqual(len(cycles), 2)

    def test_find_unused_public_functions_success(self):
        """Test tìm unused public functions thành công."""
        mock_data = [
            {"name": "func1", "file_path": "module.py", "line_number": 10},
            {"name": "func2", "file_path": "utils.py", "line_number": 20}
        ]
        
        self.mock_ckg_agent.get_unused_public_functions.return_value = CKGQueryResult(
            query="test", results=mock_data, total_count=2,
            execution_time_ms=30.0, success=True
        )
        
        unused_functions = self.analyzer._find_unused_public_functions()
        
        self.assertEqual(len(unused_functions), 2)
        self.assertEqual(unused_functions[0].element_name, "func1")
        self.assertEqual(unused_functions[0].element_type, "function")
        self.assertEqual(unused_functions[1].element_name, "func2")

    def test_find_unused_public_functions_error(self):
        """Test xử lý lỗi khi tìm unused public functions."""
        self.mock_ckg_agent.get_unused_public_functions.return_value = CKGQueryResult(
            query="test", results=[], total_count=0,
            execution_time_ms=10.0, success=False, error_message="Query failed"
        )
        
        unused_functions = self.analyzer._find_unused_public_functions()
        self.assertEqual(len(unused_functions), 0)

    def test_find_unused_public_classes_success(self):
        """Test tìm unused public classes thành công."""
        mock_data = [
            {"name": "Class1", "file_path": "models.py", "line_number": 15},
            {"name": "Class2", "file_path": "utils.py", "line_number": 25}
        ]
        
        self.mock_ckg_agent.execute_query.return_value = CKGQueryResult(
            query="test", results=mock_data, total_count=2,
            execution_time_ms=40.0, success=True
        )
        
        unused_classes = self.analyzer._find_unused_public_classes()
        
        self.assertEqual(len(unused_classes), 2)
        self.assertEqual(unused_classes[0].element_name, "Class1")
        self.assertEqual(unused_classes[0].element_type, "class")
        self.assertEqual(unused_classes[1].element_name, "Class2")

    def test_create_circular_dependency_issue(self):
        """Test tạo ArchitecturalIssue từ CircularDependency."""
        cycle = CircularDependency(
            cycle=["a.py", "b.py", "c.py"],
            cycle_type="file",
            description="Test cycle"
        )
        
        issue = self.analyzer._create_circular_dependency_issue(cycle)
        
        self.assertEqual(issue.issue_type, IssueType.CIRCULAR_DEPENDENCY)
        self.assertEqual(issue.severity, SeverityLevel.MEDIUM)  # <= 3 files
        self.assertIn("Circular Dependency", issue.title)
        self.assertEqual(issue.affected_elements, cycle.cycle)
        self.assertIsNotNone(issue.suggestion)

    def test_create_circular_dependency_issue_large_cycle(self):
        """Test tạo issue cho large circular dependency."""
        cycle = CircularDependency(
            cycle=["a.py", "b.py", "c.py", "d.py", "e.py"],  # > 3 files
            cycle_type="file",
            description="Large cycle"
        )
        
        issue = self.analyzer._create_circular_dependency_issue(cycle)
        self.assertEqual(issue.severity, SeverityLevel.HIGH)  # > 3 files

    def test_create_unused_element_issue(self):
        """Test tạo ArchitecturalIssue từ UnusedElement."""
        element = UnusedElement(
            element_name="unused_func",
            element_type="function",
            file_path="utils.py",
            line_number=42,
            reason="Not called externally"
        )
        
        issue = self.analyzer._create_unused_element_issue(element)
        
        self.assertEqual(issue.issue_type, IssueType.UNUSED_PUBLIC_ELEMENT)
        self.assertEqual(issue.severity, SeverityLevel.LOW)
        self.assertIn("unused_func", issue.title)
        self.assertIsNotNone(issue.suggestion)
        self.assertIsNotNone(issue.static_analysis_limitation)
        self.assertIsNotNone(issue.metadata)

    def test_get_summary_stats(self):
        """Test tạo summary statistics."""
        # Tạo mock result
        issues = [
            ArchitecturalIssue(
                issue_type=IssueType.CIRCULAR_DEPENDENCY,
                severity=SeverityLevel.HIGH,
                title="Test issue 1",
                description="Test",
                affected_elements=[]
            ),
            ArchitecturalIssue(
                issue_type=IssueType.UNUSED_PUBLIC_ELEMENT,
                severity=SeverityLevel.LOW,
                title="Test issue 2",
                description="Test",
                affected_elements=[]
            )
        ]
        
        result = ArchitecturalAnalysisResult(
            project_path="/test",
            total_issues=2,
            issues=issues,
            circular_dependencies=[],
            unused_elements=[],
            analysis_scope="test",
            limitations=[],
            execution_time_seconds=0.1,
            success=True
        )
        
        stats = self.analyzer.get_summary_stats(result)
        
        # Assertions
        self.assertEqual(stats["total_issues"], 2)
        self.assertEqual(stats["execution_time"], 0.1)
        self.assertTrue(stats["success"])
        self.assertIn("severity_distribution", stats)
        self.assertIn("issue_type_distribution", stats)
        self.assertEqual(stats["severity_distribution"]["high"], 1)
        self.assertEqual(stats["severity_distribution"]["low"], 1)

    def test_analyze_circular_dependencies_success(self):
        """Test phân tích circular dependencies thành công."""
        dependency_data = [
            {"source_file": "a.py", "target_file": "b.py"},
            {"source_file": "b.py", "target_file": "a.py"}  # Simple cycle
        ]
        
        self.mock_ckg_agent.execute_query.return_value = CKGQueryResult(
            query="test", results=dependency_data, total_count=2,
            execution_time_ms=30.0, success=True
        )
        
        circular_deps = self.analyzer._analyze_circular_dependencies()
        
        self.assertGreater(len(circular_deps), 0)
        self.assertEqual(circular_deps[0].cycle_type, "file")

    def test_analyze_circular_dependencies_no_cycles(self):
        """Test phân tích khi không có circular dependencies."""
        dependency_data = [
            {"source_file": "a.py", "target_file": "b.py"},
            {"source_file": "b.py", "target_file": "c.py"}  # No cycle
        ]
        
        self.mock_ckg_agent.execute_query.return_value = CKGQueryResult(
            query="test", results=dependency_data, total_count=2,
            execution_time_ms=20.0, success=True
        )
        
        circular_deps = self.analyzer._analyze_circular_dependencies()
        self.assertEqual(len(circular_deps), 0)

    def test_analyze_circular_dependencies_error(self):
        """Test xử lý lỗi trong phân tích circular dependencies."""
        self.mock_ckg_agent.execute_query.return_value = CKGQueryResult(
            query="test", results=[], total_count=0,
            execution_time_ms=10.0, success=False, error_message="Query failed"
        )
        
        circular_deps = self.analyzer._analyze_circular_dependencies()
        self.assertEqual(len(circular_deps), 0)

    def test_analyze_unused_public_elements_success(self):
        """Test phân tích unused public elements thành công."""
        # Mock unused functions
        self.mock_ckg_agent.get_unused_public_functions.return_value = CKGQueryResult(
            query="test", results=[{"name": "func", "file_path": "test.py", "line_number": 10}],
            total_count=1, execution_time_ms=20.0, success=True
        )
        
        # Mock unused classes query
        self.mock_ckg_agent.execute_query.return_value = CKGQueryResult(
            query="test", results=[{"name": "Class", "file_path": "test.py", "line_number": 5}],
            total_count=1, execution_time_ms=15.0, success=True
        )
        
        unused_elements = self.analyzer._analyze_unused_public_elements()
        
        self.assertGreater(len(unused_elements), 0)
        # Should contain both functions and classes
        element_types = {elem.element_type for elem in unused_elements}
        self.assertIn("function", element_types)
        self.assertIn("class", element_types)


if __name__ == '__main__':
    unittest.main() 