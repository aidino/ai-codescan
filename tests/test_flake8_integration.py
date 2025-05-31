#!/usr/bin/env python3
"""
Integration test for complete Flake8 analysis workflow.

Test requirement từ Task 1.10: "Viết một integration test cơ bản cho luồng phân tích Flake8 
(có thể mock các lời gọi Git và Neo4j)."

This test covers the complete end-to-end workflow:
1. Git repository cloning (mocked)
2. Language identification
3. Data preparation
4. AST parsing và CKG building (mocked Neo4j)
5. Static analysis với flake8
6. Finding aggregation
7. Report generation
"""

import tempfile
import shutil
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import ast
import subprocess

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.data_acquisition.git_operations import GitOperationsAgent, RepositoryInfo
from agents.data_acquisition.language_identifier import LanguageIdentifierAgent
from agents.data_acquisition.data_preparation import DataPreparationAgent
from agents.ckg_operations.code_parser_coordinator import CodeParserCoordinatorAgent
from agents.ckg_operations.ast_to_ckg_builder import ASTtoCKGBuilderAgent
from agents.code_analysis.static_analysis_integrator import StaticAnalysisIntegratorAgent
from agents.synthesis_reporting.finding_aggregator import FindingAggregatorAgent, AggregationStrategy
from agents.synthesis_reporting.report_generator import ReportGeneratorAgent, ReportFormat
from core.logging import get_debug_logger


class TestFlake8IntegrationWorkflow:
    """Integration test cho complete Flake8 analysis workflow."""
    
    def setup_method(self):
        """Setup integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_repo_url = "https://github.com/test/sample-python-project.git"
        self.test_repo_name = "sample-python-project"
        
    def teardown_method(self):
        """Cleanup integration test fixtures."""
        shutil.rmtree(self.temp_dir)
        
    def create_test_python_project(self):
        """Create realistic test Python project với various code issues."""
        repo_dir = Path(self.temp_dir) / self.test_repo_name
        repo_dir.mkdir()
        
        # Main module with various flake8 issues
        main_content = '''#!/usr/bin/env python3
"""
Main application module.
This module contains the main entry point for the application.
"""

import os
import sys
import json
import requests  # unused import for F401

# Long line that exceeds 79 characters limit for E501 testing
def very_long_function_name_that_definitely_exceeds_normal_length_conventions():
    """Function with long name and line length issues."""
    x = 1
    y = 2
    z = 3
    
    # Another long line for testing
    result = f"This is a very long string that exceeds the maximum line length limit of 79 characters and should trigger E501"
    
    print(f"Processing values: {x}, {y}, {z}")
    return result


class DataProcessor:
    """Class for processing various data types."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.data = []
        unused_variable = "test"  # F841 - assigned but never used
        
    def process_data(self, data_list):
        """Process input data and return results."""
        if data_list == None:  # E711 - comparison to None should use 'is'
            return []
            
        results = []
        for item in data_list:
            if item:
                results.append(item.upper())
                
        return results
    
    def save_data(self, filename):
        """Save processed data to file."""
        with open(filename, 'w') as f:  # Missing encoding specification
            json.dump(self.data, f)


def main():
    """Main application entry point."""
    processor = DataProcessor()
    data = ["hello", "world", None, "test"]
    
    # Missing space around operator (E225)
    result=processor.process_data(data)
    
    print("Processing complete:", result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''
        
        # Helper module with additional issues
        helper_content = '''"""Helper utilities module."""

import math

def calculate_area(radius):
    # Missing docstring for this function (D100 if using pydocstyle)
    return math.pi * radius**2

def helper_function():
    pass  # Function has no content
    
# Trailing whitespace and blank line issues
def another_function():    
    x = 1
    return x

'''
        
        # Utils module with imports and complexity issues
        utils_content = '''"""Utility functions for the application."""

import os
import subprocess
from typing import List, Dict, Any
from pathlib import Path

# Multiple imports on same line (E401)
import json, csv

def read_config_file(filepath: str) -> Dict[str, Any]:
    """Read configuration from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Config file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        return json.load(f)

def execute_command(command: List[str]) -> str:
    """Execute shell command and return output."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return ""

# Function with high complexity
def complex_function(data, options={}):
    """Complex function với multiple paths and nesting."""
    if not data:
        return None
    
    if isinstance(data, str):
        if options.get('upper'):
            if len(data) > 10:
                if data.startswith('test'):
                    return data.upper().strip()
                else:
                    return data.upper()
            else:
                return data.lower()
        else:
            return data
    elif isinstance(data, list):
        results = []
        for item in data:
            if item:
                if isinstance(item, str):
                    results.append(item.strip())
                else:
                    results.append(str(item))
        return results
    else:
        return str(data)
'''
        
        # Requirements file
        requirements_content = '''requests>=2.25.0
Flask>=2.0.0
pytest>=6.0.0
flake8>=4.0.0
'''
        
        # Create files
        (repo_dir / "main.py").write_text(main_content)
        (repo_dir / "helper.py").write_text(helper_content)
        (repo_dir / "utils.py").write_text(utils_content)
        (repo_dir / "requirements.txt").write_text(requirements_content)
        
        # Create package structure
        package_dir = repo_dir / "mypackage"
        package_dir.mkdir()
        (package_dir / "__init__.py").write_text("# Package initialization\n")
        
        return str(repo_dir)
        
    @patch('agents.data_acquisition.git_operations.git.Repo')
    @patch('agents.ckg_operations.ast_to_ckg_builder.neo4j.GraphDatabase')
    @patch('subprocess.run')
    def test_complete_flake8_workflow(self, mock_subprocess, mock_neo4j, mock_git_repo):
        """Test complete end-to-end flake8 analysis workflow với mocked dependencies."""
        
        # ===============================
        # SETUP PHASE - Create test data
        # ===============================
        test_repo_path = self.create_test_python_project()
        debug_logger = get_debug_logger("integration_test")
        
        # ===============================
        # MOCK SETUP PHASE
        # ===============================
        
        # 1. Mock Git operations
        mock_repo = Mock()
        mock_repo.working_dir = test_repo_path
        mock_git_repo.clone_from.return_value = mock_repo
        
        # 2. Mock Neo4j driver và session
        mock_driver = Mock()
        mock_session = Mock()
        mock_neo4j.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # 3. Mock flake8 subprocess call với realistic output
        flake8_output = f"""main.py:9:1: F401 'requests' imported but unused
main.py:12:1: E501 line too long (119 > 79 characters)
main.py:17:5: F841 local variable 'result' is assigned to but never used
main.py:28:1: E501 line too long (132 > 79 characters)
main.py:42:9: F841 local variable 'unused_variable' is assigned to but never used
main.py:47:20: E711 comparison to None should be 'if cond is None:'
main.py:66:11: E225 missing whitespace around operator
helper.py:6:1: D100 Missing docstring in public function
helper.py:10:1: E302 expected 2 blank lines, found 1
helper.py:15:20: W291 trailing whitespace
utils.py:9:1: E401 multiple imports on one line
utils.py:35:1: C901 'complex_function' is too complex (12)"""
        
        mock_subprocess.return_value = Mock(
            returncode=1,  # flake8 returns 1 when issues found
            stdout=flake8_output,
            stderr=""
        )
        
        # ===============================
        # WORKFLOW EXECUTION PHASE
        # ===============================
        
        print("\n🚀 Starting Complete Flake8 Integration Workflow Test")
        
        # Stage 1: Repository Acquisition (Mocked Git)
        print("📥 Stage 1: Repository Acquisition")
        git_agent = GitOperationsAgent()
        git_agent._debug_logger = debug_logger
        
        repo_info = git_agent.clone_repository(
            self.test_repo_url,
            self.temp_dir
        )
        
        assert isinstance(repo_info, RepositoryInfo)
        assert repo_info.success
        assert repo_info.local_path == test_repo_path
        assert repo_info.repository_url == self.test_repo_url
        print(f"   ✅ Repository cloned to: {repo_info.local_path}")
        
        # Stage 2: Language Identification
        print("🔍 Stage 2: Language Identification")
        lang_agent = LanguageIdentifierAgent()
        lang_agent._debug_logger = debug_logger
        
        language_profile = lang_agent.identify_language(repo_info.local_path)
        
        assert language_profile.primary_language == "Python"
        assert len(language_profile.languages) > 0
        assert any(lang.name == "Python" for lang in language_profile.languages)
        print(f"   ✅ Primary language detected: {language_profile.primary_language}")
        print(f"   📊 Total languages found: {len(language_profile.languages)}")
        
        # Stage 3: Data Preparation
        print("📋 Stage 3: Data Preparation")
        data_agent = DataPreparationAgent()
        data_agent._debug_logger = debug_logger
        
        project_context = data_agent.prepare_project_context(
            repo_info,
            language_profile
        )
        
        assert project_context is not None
        python_files = [f for f in project_context.files if f.language == "Python"]
        assert len(python_files) >= 3  # main.py, helper.py, utils.py
        print(f"   ✅ Project context prepared: {len(python_files)} Python files found")
        
        # Stage 4: AST Parsing và CKG Building (Mocked Neo4j)
        print("🏗️  Stage 4: AST Parsing & CKG Building")
        
        # Parse Python files
        parser_agent = CodeParserCoordinatorAgent()
        parser_agent._debug_logger = debug_logger
        
        parse_result = parser_agent.parse_python_project(repo_info.local_path)
        
        assert parse_result.success
        assert len(parse_result.parsed_files) >= 3
        print(f"   ✅ AST parsing completed: {len(parse_result.parsed_files)} files parsed")
        
        # Build CKG (mocked)
        ckg_builder = ASTtoCKGBuilderAgent()
        ckg_builder._debug_logger = debug_logger
        
        build_result = ckg_builder.build_ckg_from_parse_result(parse_result)
        
        # Verify Neo4j operations were attempted
        assert mock_session.run.called
        print("   ✅ CKG building completed (mocked Neo4j operations)")
        
        # Stage 5: Static Analysis với Flake8
        print("🔧 Stage 5: Static Analysis with Flake8")
        static_analyzer = StaticAnalysisIntegratorAgent()
        static_analyzer._debug_logger = debug_logger
        
        flake8_result = static_analyzer.run_flake8(repo_info.local_path)
        
        assert flake8_result.success
        assert len(flake8_result.findings) > 0
        print(f"   ✅ Flake8 analysis completed: {len(flake8_result.findings)} issues found")
        
        # Verify specific findings are detected
        rule_ids = [f.rule_id for f in flake8_result.findings]
        assert "F401" in rule_ids  # Unused import
        assert "E501" in rule_ids  # Line too long
        assert "F841" in rule_ids  # Unused variable
        assert "E711" in rule_ids  # Comparison to None
        
        # Stage 6: Finding Aggregation
        print("📊 Stage 6: Finding Aggregation")
        aggregator = FindingAggregatorAgent()
        
        aggregation_result = aggregator.aggregate_findings(
            flake8_result.findings,
            strategy=AggregationStrategy.MERGE_DUPLICATES
        )
        
        assert aggregation_result.original_count > 0
        assert len(aggregation_result.aggregated_findings) > 0
        print(f"   ✅ Finding aggregation completed:")
        print(f"      📈 Original findings: {aggregation_result.original_count}")
        print(f"      🔄 Aggregated findings: {aggregation_result.aggregated_count}")
        print(f"      💫 Deduplication ratio: {aggregation_result.deduplication_ratio:.2f}")
        
        # Stage 7: Report Generation
        print("📄 Stage 7: Report Generation")
        report_generator = ReportGeneratorAgent()
        
        # Generate multiple report formats
        text_report = report_generator.generate_report(
            aggregation_result.aggregated_findings,
            format=ReportFormat.TEXT,
            project_name=self.test_repo_name
        )
        
        json_report = report_generator.generate_report(
            aggregation_result.aggregated_findings,
            format=ReportFormat.JSON,
            project_name=self.test_repo_name
        )
        
        html_report = report_generator.generate_report(
            aggregation_result.aggregated_findings,
            format=ReportFormat.HTML,
            project_name=self.test_repo_name
        )
        
        # Verify reports contain expected content
        assert self.test_repo_name in text_report
        assert "F401" in text_report
        assert "E501" in text_report
        
        import json as json_module
        json_data = json_module.loads(json_report)
        assert json_data["metadata"]["project_name"] == self.test_repo_name
        assert len(json_data["findings"]) > 0
        
        assert "<html>" in html_report
        assert self.test_repo_name in html_report
        
        print("   ✅ Report generation completed:")
        print(f"      📝 Text report: {len(text_report)} characters")
        print(f"      📊 JSON report: {len(json_data['findings'])} findings")
        print(f"      🌐 HTML report: {len(html_report)} characters")
        
        # Generate executive summary
        executive_summary = report_generator.generate_executive_summary(
            aggregation_result.aggregated_findings,
            project_name=self.test_repo_name
        )
        
        assert self.test_repo_name in executive_summary.overview
        assert len(executive_summary.key_findings) > 0
        assert executive_summary.metrics["total_findings"] > 0
        
        print("   ✅ Executive summary generated")
        
        # ===============================
        # VERIFICATION PHASE
        # ===============================
        
        print("🔍 Final Verification")
        
        # Verify all stages completed successfully
        assert repo_info.success, "Git operations should succeed"
        assert language_profile.primary_language == "Python", "Should detect Python"
        assert project_context is not None, "Data preparation should succeed"
        assert parse_result.success, "AST parsing should succeed"
        assert flake8_result.success, "Flake8 analysis should succeed"
        assert len(aggregation_result.aggregated_findings) > 0, "Should have aggregated findings"
        assert len(text_report) > 0, "Should generate non-empty reports"
        
        # Verify specific issue types were found
        severity_levels = [f.representative_finding.severity.value for f in aggregation_result.aggregated_findings]
        finding_types = [f.representative_finding.finding_type.value for f in aggregation_result.aggregated_findings]
        
        assert "LOW" in severity_levels or "MEDIUM" in severity_levels, "Should find issues of various severities"
        assert "STYLE" in finding_types or "ERROR" in finding_types, "Should find different types of issues"
        
        # Verify mock calls were made
        mock_git_repo.clone_from.assert_called_once()
        mock_subprocess.assert_called()
        mock_session.run.assert_called()
        
        print("✅ All verifications passed!")
        print(f"🎉 Complete Flake8 Integration Workflow Test SUCCESSFUL")
        print(f"📊 Total findings processed: {aggregation_result.original_count}")
        print(f"📈 Final aggregated findings: {aggregation_result.aggregated_count}")
        
        return {
            "repo_info": repo_info,
            "language_profile": language_profile,
            "project_context": project_context,
            "parse_result": parse_result,
            "flake8_result": flake8_result,
            "aggregation_result": aggregation_result,
            "reports": {
                "text": text_report,
                "json": json_report,
                "html": html_report
            },
            "executive_summary": executive_summary
        }
        
    @patch('subprocess.run')
    def test_flake8_error_handling(self, mock_subprocess):
        """Test error handling trong flake8 workflow."""
        
        # Test scenario: flake8 command not found
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            returncode=2, cmd=['flake8'], stderr="flake8: command not found"
        )
        
        test_repo_path = self.create_test_python_project()
        static_analyzer = StaticAnalysisIntegratorAgent()
        
        result = static_analyzer.run_flake8(test_repo_path)
        
        assert not result.success
        assert result.error_message is not None
        assert "flake8: command not found" in result.error_message
        assert len(result.findings) == 0
        
    def test_workflow_performance_metrics(self):
        """Test performance tracking trong integration workflow."""
        test_repo_path = self.create_test_python_project()
        
        # Test individual component performance
        import time
        
        # Language identification performance
        lang_agent = LanguageIdentifierAgent()
        start_time = time.time()
        language_profile = lang_agent.identify_language(test_repo_path)
        lang_time = time.time() - start_time
        
        assert lang_time < 5.0  # Should complete within 5 seconds
        assert language_profile.primary_language == "Python"
        
        # AST parsing performance
        parser_agent = CodeParserCoordinatorAgent()
        start_time = time.time()
        parse_result = parser_agent.parse_python_project(test_repo_path)
        parse_time = time.time() - start_time
        
        assert parse_time < 10.0  # Should complete within 10 seconds
        assert parse_result.success
        
        print(f"Performance metrics:")
        print(f"  Language identification: {lang_time:.2f}s")
        print(f"  AST parsing: {parse_time:.2f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 