#!/usr/bin/env python3
"""
Unit tests for Code Analysis components.

Tests for:
- Static Analysis Integrator (flake8, pylint, mypy integration)
- Contextual Query Agent (CKG-enhanced analysis)
"""

import tempfile
import shutil
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import subprocess

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.code_analysis.static_analysis_integrator import (
    StaticAnalysisIntegratorAgent, Finding, AnalysisResult,
    SeverityLevel, FindingType
)
from agents.code_analysis.contextual_query import (
    ContextualQueryAgent, ContextualFinding, ImpactScore
)


class TestStaticAnalysisIntegratorAgent:
    """Test StaticAnalysisIntegratorAgent functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.agent = StaticAnalysisIntegratorAgent()
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
        assert hasattr(self.agent, 'run_flake8')
        assert hasattr(self.agent, 'run_pylint')
        assert hasattr(self.agent, 'run_mypy')
        
    def test_finding_creation(self):
        """Test Finding dataclass creation."""
        finding = Finding(
            tool="flake8",
            file_path="test.py",
            line_number=10,
            column_number=5,
            message="Line too long",
            rule_id="E501",
            severity=SeverityLevel.LOW,
            finding_type=FindingType.STYLE
        )
        
        assert finding.tool == "flake8"
        assert finding.file_path == "test.py"
        assert finding.line_number == 10
        assert finding.severity == SeverityLevel.LOW
        assert finding.finding_type == FindingType.STYLE
        
    def test_analysis_result_creation(self):
        """Test AnalysisResult dataclass creation."""
        findings = [
            Finding("flake8", "test.py", 1, 1, "Test finding", "E501",
                   SeverityLevel.LOW, FindingType.STYLE)
        ]
        
        result = AnalysisResult(
            tool="flake8",
            success=True,
            findings=findings,
            execution_time=1.5,
            files_analyzed=5,
            error_message=None
        )
        
        assert result.tool == "flake8"
        assert result.success
        assert len(result.findings) == 1
        assert result.execution_time == 1.5
        assert result.files_analyzed == 5
        
    @patch('subprocess.run')
    def test_run_flake8_success(self, mock_subprocess):
        """Test successful flake8 execution."""
        # Mock flake8 output
        mock_output = "test.py:1:1: E501 line too long (82 > 79 characters)\ntest.py:5:10: F401 'os' imported but unused"
        mock_subprocess.return_value = Mock(
            returncode=1,  # flake8 returns 1 when issues found
            stdout=mock_output,
            stderr=""
        )
        
        # Create test file
        test_content = "import os\nprint('This is a very long line that exceeds the maximum line length limit')"
        self.create_test_python_file(test_content)
        
        result = self.agent.run_flake8(self.temp_dir)
        
        assert isinstance(result, AnalysisResult)
        assert result.tool == "flake8"
        assert result.success
        assert len(result.findings) == 2
        assert result.findings[0].rule_id == "E501"
        assert result.findings[1].rule_id == "F401"
        
    @patch('subprocess.run')
    def test_run_flake8_no_issues(self, mock_subprocess):
        """Test flake8 execution với no issues."""
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )
        
        # Create clean test file
        test_content = "print('Hello, World!')"
        self.create_test_python_file(test_content)
        
        result = self.agent.run_flake8(self.temp_dir)
        
        assert result.success
        assert len(result.findings) == 0
        
    @patch('subprocess.run')
    def test_run_flake8_execution_error(self, mock_subprocess):
        """Test flake8 execution error handling."""
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            returncode=2, cmd=['flake8'], stderr="flake8: command not found"
        )
        
        result = self.agent.run_flake8(self.temp_dir)
        
        assert not result.success
        assert result.error_message is not None
        assert "flake8: command not found" in result.error_message
        
    @patch('subprocess.run')
    def test_run_pylint_success(self, mock_subprocess):
        """Test successful pylint execution."""
        # Mock pylint JSON output
        mock_output = '''[
            {
                "type": "convention",
                "module": "test",
                "obj": "",
                "line": 1,
                "column": 0,
                "path": "test.py",
                "symbol": "missing-module-docstring",
                "message": "Missing module docstring",
                "message-id": "C0114"
            }
        ]'''
        mock_subprocess.return_value = Mock(
            returncode=1,
            stdout=mock_output,
            stderr=""
        )
        
        # Create test file
        test_content = "def hello(): pass"
        self.create_test_python_file(test_content)
        
        result = self.agent.run_pylint(self.temp_dir)
        
        assert isinstance(result, AnalysisResult)
        assert result.tool == "pylint"
        assert result.success
        assert len(result.findings) == 1
        assert result.findings[0].rule_id == "C0114"
        assert result.findings[0].severity == SeverityLevel.LOW
        
    @patch('subprocess.run')
    def test_run_mypy_success(self, mock_subprocess):
        """Test successful mypy execution."""
        # Mock mypy output
        mock_output = "test.py:5: error: Function is missing a return type annotation"
        mock_subprocess.return_value = Mock(
            returncode=1,
            stdout=mock_output,
            stderr=""
        )
        
        # Create test file
        test_content = "def hello(): return 'world'"
        self.create_test_python_file(test_content)
        
        result = self.agent.run_mypy(self.temp_dir)
        
        assert isinstance(result, AnalysisResult)
        assert result.tool == "mypy"
        assert result.success
        assert len(result.findings) == 1
        assert result.findings[0].finding_type == FindingType.ERROR
        
    def test_parse_flake8_output(self):
        """Test flake8 output parsing."""
        output = """test.py:1:1: E501 line too long (82 > 79 characters)
test.py:5:10: F401 'os' imported but unused
test.py:10:1: W293 blank line contains whitespace"""
        
        findings = self.agent._parse_flake8_output(output)
        
        assert len(findings) == 3
        assert findings[0].rule_id == "E501"
        assert findings[0].line_number == 1
        assert findings[0].column_number == 1
        assert findings[1].rule_id == "F401"
        assert findings[2].rule_id == "W293"
        
    def test_parse_pylint_output(self):
        """Test pylint JSON output parsing."""
        output = '''[
            {
                "type": "error",
                "module": "test",
                "obj": "hello",
                "line": 5,
                "column": 10,
                "path": "test.py",
                "symbol": "undefined-variable",
                "message": "Undefined variable 'x'",
                "message-id": "E1101"
            }
        ]'''
        
        findings = self.agent._parse_pylint_output(output)
        
        assert len(findings) == 1
        assert findings[0].rule_id == "E1101"
        assert findings[0].line_number == 5
        assert findings[0].column_number == 10
        assert findings[0].severity == SeverityLevel.HIGH
        
    def test_parse_mypy_output(self):
        """Test mypy output parsing."""
        output = """test.py:5: error: Function is missing a return type annotation
test.py:10: warning: Unused variable 'x'
test.py:15: note: Consider using Type[Class] instead"""
        
        findings = self.agent._parse_mypy_output(output)
        
        assert len(findings) == 2  # Notes are filtered out
        assert findings[0].finding_type == FindingType.ERROR
        assert findings[1].finding_type == FindingType.WARNING
        
    def test_classify_severity(self):
        """Test severity classification."""
        # Test flake8 severity classification
        assert self.agent._classify_severity("flake8", "E501") == SeverityLevel.LOW
        assert self.agent._classify_severity("flake8", "F401") == SeverityLevel.MEDIUM
        assert self.agent._classify_severity("flake8", "E999") == SeverityLevel.HIGH
        
        # Test pylint severity classification
        assert self.agent._classify_severity("pylint", "C0114") == SeverityLevel.LOW
        assert self.agent._classify_severity("pylint", "W0613") == SeverityLevel.MEDIUM
        assert self.agent._classify_severity("pylint", "E1101") == SeverityLevel.HIGH
        
    def test_classify_finding_type(self):
        """Test finding type classification."""
        # Test flake8 finding type classification
        assert self.agent._classify_finding_type("flake8", "E501") == FindingType.STYLE
        assert self.agent._classify_finding_type("flake8", "F401") == FindingType.ERROR
        assert self.agent._classify_finding_type("flake8", "W293") == FindingType.WARNING
        
        # Test pylint finding type classification
        assert self.agent._classify_finding_type("pylint", "C0114") == FindingType.CONVENTION
        assert self.agent._classify_finding_type("pylint", "R0903") == FindingType.REFACTOR
        
    def test_aggregate_results(self):
        """Test aggregating results từ multiple tools."""
        # Create sample results
        flake8_result = AnalysisResult(
            tool="flake8",
            success=True,
            findings=[
                Finding("flake8", "test.py", 1, 1, "Line too long", "E501",
                       SeverityLevel.LOW, FindingType.STYLE)
            ],
            execution_time=1.0,
            files_analyzed=1
        )
        
        pylint_result = AnalysisResult(
            tool="pylint",
            success=True,
            findings=[
                Finding("pylint", "test.py", 5, 0, "Missing docstring", "C0114",
                       SeverityLevel.LOW, FindingType.CONVENTION)
            ],
            execution_time=2.0,
            files_analyzed=1
        )
        
        results = [flake8_result, pylint_result]
        aggregated = self.agent.aggregate_results(results)
        
        assert aggregated.success
        assert len(aggregated.findings) == 2
        assert aggregated.execution_time == 3.0
        assert aggregated.files_analyzed == 1  # Unique files


class TestContextualQueryAgent:
    """Test ContextualQueryAgent CKG-enhanced analysis functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.agent = ContextualQueryAgent()
        
    def test_init(self):
        """Test agent initialization."""
        assert self.agent is not None
        assert hasattr(self.agent, 'analyze_findings_with_context')
        
    def test_contextual_finding_creation(self):
        """Test ContextualFinding dataclass creation."""
        original_finding = Finding(
            tool="flake8",
            file_path="test.py",
            line_number=10,
            column_number=5,
            message="Line too long",
            rule_id="E501",
            severity=SeverityLevel.LOW,
            finding_type=FindingType.STYLE
        )
        
        contextual_finding = ContextualFinding(
            original_finding=original_finding,
            file_context={"functions": ["main"], "classes": []},
            code_element_context={"element_type": "function", "element_name": "main"},
            impact_score=ImpactScore(priority=2, complexity=1, usage=3),
            related_findings=[],
            recommendations=["Consider breaking long lines"]
        )
        
        assert contextual_finding.original_finding == original_finding
        assert contextual_finding.impact_score.priority == 2
        assert len(contextual_finding.recommendations) == 1
        
    def test_impact_score_calculation(self):
        """Test impact score calculation."""
        impact = ImpactScore(priority=3, complexity=2, usage=4)
        
        assert impact.total_score == 9  # 3 + 2 + 4
        assert impact.weighted_score == 23  # 3*3 + 2*2 + 4*4 (assuming default weights)
        
    @patch('agents.code_analysis.contextual_query.CKGQueryInterfaceAgent')
    def test_analyze_findings_with_context(self, mock_ckg_query):
        """Test analyzing findings với CKG context."""
        # Mock CKG query interface
        mock_query_interface = Mock()
        mock_ckg_query.return_value = mock_query_interface
        
        # Mock query results
        mock_query_interface.get_functions_in_file.return_value = Mock(
            success=True,
            data=[{"name": "main"}, {"name": "helper"}]
        )
        mock_query_interface.get_classes_in_file.return_value = Mock(
            success=True,
            data=[{"name": "TestClass"}]
        )
        
        # Create sample findings
        findings = [
            Finding("flake8", "test.py", 10, 5, "Line too long", "E501",
                   SeverityLevel.LOW, FindingType.STYLE),
            Finding("pylint", "test.py", 15, 0, "Missing docstring", "C0114",
                   SeverityLevel.LOW, FindingType.CONVENTION)
        ]
        
        # Test analysis
        contextual_findings = self.agent.analyze_findings_with_context(findings)
        
        assert len(contextual_findings) == 2
        assert all(isinstance(cf, ContextualFinding) for cf in contextual_findings)
        assert all(cf.file_context is not None for cf in contextual_findings)
        
    @patch('agents.code_analysis.contextual_query.CKGQueryInterfaceAgent')
    def test_get_file_context(self, mock_ckg_query):
        """Test getting file context từ CKG."""
        # Mock CKG query interface
        mock_query_interface = Mock()
        mock_ckg_query.return_value = mock_query_interface
        
        # Mock query results
        mock_query_interface.get_functions_in_file.return_value = Mock(
            success=True,
            data=[{"name": "function1"}, {"name": "function2"}]
        )
        mock_query_interface.get_classes_in_file.return_value = Mock(
            success=True,
            data=[{"name": "Class1"}]
        )
        
        context = self.agent._get_file_context("test.py")
        
        assert "functions" in context
        assert "classes" in context
        assert len(context["functions"]) == 2
        assert len(context["classes"]) == 1
        
    def test_calculate_priority_score(self):
        """Test priority score calculation."""
        # Test high severity finding
        high_severity_finding = Finding(
            "pylint", "test.py", 10, 0, "Undefined variable", "E1101",
            SeverityLevel.HIGH, FindingType.ERROR
        )
        
        priority = self.agent._calculate_priority_score(high_severity_finding)
        assert priority >= 3  # High severity should get high priority
        
        # Test low severity finding
        low_severity_finding = Finding(
            "flake8", "test.py", 10, 0, "Line too long", "E501",
            SeverityLevel.LOW, FindingType.STYLE
        )
        
        priority = self.agent._calculate_priority_score(low_severity_finding)
        assert priority <= 2  # Low severity should get low priority
        
    @patch('agents.code_analysis.contextual_query.CKGQueryInterfaceAgent')
    def test_calculate_complexity_score(self, mock_ckg_query):
        """Test complexity score calculation."""
        # Mock CKG query interface
        mock_query_interface = Mock()
        mock_ckg_query.return_value = mock_query_interface
        
        # Mock complex function
        mock_query_interface.find_function_callers.return_value = Mock(
            success=True,
            data=[{"caller": "func1"}, {"caller": "func2"}, {"caller": "func3"}]
        )
        
        finding = Finding(
            "flake8", "test.py", 10, 0, "Line too long", "E501",
            SeverityLevel.LOW, FindingType.STYLE
        )
        
        complexity = self.agent._calculate_complexity_score(
            finding, {"element_type": "function", "element_name": "complex_func"}
        )
        
        assert complexity > 1  # Should indicate higher complexity
        
    def test_generate_recommendations(self):
        """Test recommendation generation."""
        finding = Finding(
            "flake8", "test.py", 10, 0, "Line too long (82 > 79 characters)", "E501",
            SeverityLevel.LOW, FindingType.STYLE
        )
        
        recommendations = self.agent._generate_recommendations(finding)
        
        assert len(recommendations) > 0
        assert any("line" in rec.lower() for rec in recommendations)
        
    def test_find_related_findings(self):
        """Test finding related findings."""
        findings = [
            Finding("flake8", "test.py", 10, 0, "Line too long", "E501",
                   SeverityLevel.LOW, FindingType.STYLE),
            Finding("flake8", "test.py", 12, 0, "Line too long", "E501",
                   SeverityLevel.LOW, FindingType.STYLE),
            Finding("pylint", "other.py", 5, 0, "Missing docstring", "C0114",
                   SeverityLevel.LOW, FindingType.CONVENTION)
        ]
        
        current_finding = findings[0]
        related = self.agent._find_related_findings(current_finding, findings)
        
        # Should find the second E501 finding as related
        assert len(related) == 1
        assert related[0].rule_id == "E501"
        assert related[0].line_number == 12


class TestCodeAnalysisIntegration:
    """Integration tests cho Code Analysis workflow."""
    
    def setup_method(self):
        """Setup integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Cleanup integration test fixtures."""
        shutil.rmtree(self.temp_dir)
        
    def create_test_project(self):
        """Create test Python project với code issues."""
        # File với various issues
        problematic_content = '''import os
import sys

def very_long_function_name_that_exceeds_normal_length_limits():
    x = 1
    y = 2
    return x + y

class ClassWithoutDocstring:
    def method_without_docstring(self):
        unused_variable = "test"
        print("This is a very long line that exceeds the maximum line length limit of 79 characters")
'''
        
        Path(self.temp_dir, "problematic.py").write_text(problematic_content)
        
        # Clean file
        clean_content = '''"""Module with good code quality."""

def hello_world() -> str:
    """Return greeting message."""
    return "Hello, World!"
'''
        
        Path(self.temp_dir, "clean.py").write_text(clean_content)
        
    @patch('subprocess.run')
    @patch('agents.code_analysis.contextual_query.CKGQueryInterfaceAgent')
    def test_complete_analysis_workflow(self, mock_ckg_query, mock_subprocess):
        """Test complete code analysis workflow."""
        # Setup mocks
        mock_subprocess.return_value = Mock(
            returncode=1,
            stdout="problematic.py:1:1: F401 'os' imported but unused",
            stderr=""
        )
        
        mock_query_interface = Mock()
        mock_ckg_query.return_value = mock_query_interface
        mock_query_interface.get_functions_in_file.return_value = Mock(
            success=True, data=[{"name": "very_long_function_name_that_exceeds_normal_length_limits"}]
        )
        mock_query_interface.get_classes_in_file.return_value = Mock(
            success=True, data=[{"name": "ClassWithoutDocstring"}]
        )
        
        # Create test project
        self.create_test_project()
        
        # Run analysis
        static_analyzer = StaticAnalysisIntegratorAgent()
        contextual_analyzer = ContextualQueryAgent()
        
        # Step 1: Static analysis
        flake8_result = static_analyzer.run_flake8(self.temp_dir)
        
        assert flake8_result.success
        assert len(flake8_result.findings) == 1
        
        # Step 2: Contextual analysis
        contextual_findings = contextual_analyzer.analyze_findings_with_context(
            flake8_result.findings
        )
        
        assert len(contextual_findings) == 1
        assert isinstance(contextual_findings[0], ContextualFinding)
        assert contextual_findings[0].file_context is not None
        assert contextual_findings[0].impact_score is not None


if __name__ == "__main__":
    pytest.main([__file__]) 