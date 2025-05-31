#!/usr/bin/env python3
"""
Tests cho Kotlin static analysis support trong StaticAnalysisIntegratorAgent.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import subprocess
import sys
import os
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.code_analysis.static_analysis_integrator import (
    StaticAnalysisIntegratorAgent, 
    AnalysisResult, 
    Finding, 
    SeverityLevel, 
    FindingType
)


class TestKotlinStaticAnalysis(unittest.TestCase):
    """Test Kotlin static analysis support."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent = StaticAnalysisIntegratorAgent()
        
        # Sample Kotlin project path
        self.kotlin_project_path = "/test/kotlin_project"
        
        # Sample Detekt XML output
        self.sample_detekt_xml = """<?xml version="1.0" encoding="UTF-8"?>
<checkstyle version="8.0">
    <file name="src/main/kotlin/com/example/TestClass.kt">
        <error line="5" column="1" severity="warning" message="Magic number found: 42" source="detekt.style.MagicNumber"/>
        <error line="10" column="5" severity="error" message="Function name should be in camelCase" source="detekt.naming.FunctionNaming"/>
        <error line="15" column="9" severity="info" message="Consider using forEach instead of for loop" source="detekt.style.LoopWithTooManyJumpStatements"/>
    </file>
    <file name="src/main/kotlin/com/example/AnotherClass.kt">
        <error line="8" column="1" severity="warning" message="Class is too large (100 lines)" source="detekt.complexity.LargeClass"/>
        <error line="20" column="12" severity="warning" message="Unused import" source="detekt.style.UnusedImports"/>
    </file>
</checkstyle>"""
        
        # Sample Detekt text output
        self.sample_detekt_text = """src/main/kotlin/TestClass.kt:5:1: MagicNumber: Magic number found: 42
src/main/kotlin/TestClass.kt:10:5: FunctionNaming: Function name should be in camelCase
src/main/kotlin/AnotherClass.kt:8: LargeClass - Class is too large (100 lines)
src/main/kotlin/AnotherClass.kt:20: UnusedImports - Unused import"""
    
    def test_init_with_detekt_config(self):
        """Test initialization với Detekt configuration."""
        self.assertIn("detekt", self.agent.supported_tools)
        self.assertIn("detekt", self.agent.tools_config)
        
        detekt_config = self.agent.tools_config["detekt"]
        self.assertTrue(detekt_config["enabled"])
        self.assertEqual(detekt_config["version"], "1.23.4")
        self.assertTrue(detekt_config["build_upon_default_config"])
    
    @patch('agents.code_analysis.static_analysis_integrator.os.walk')
    def test_count_kotlin_files(self, mock_walk):
        """Test _count_kotlin_files method."""
        # Mock os.walk để return fake file structure
        mock_walk.return_value = [
            ('/test', ['src'], ['README.md']),
            ('/test/src', ['main'], ['build.gradle.kts']),
            ('/test/src/main', ['kotlin'], []),
            ('/test/src/main/kotlin', ['com'], ['Main.kt', 'Utils.kt']),
            ('/test/src/main/kotlin/com', ['example'], ['TestClass.kt'])
        ]
        
        count = self.agent._count_kotlin_files("/test")
        self.assertEqual(count, 3)  # Main.kt, Utils.kt, TestClass.kt
    
    @patch('agents.code_analysis.static_analysis_integrator.os.path.exists')
    def test_get_detekt_jar_existing(self, mock_exists):
        """Test _get_detekt_jar với existing JAR."""
        mock_exists.return_value = True
        
        config = {"jar_path": "/path/to/detekt.jar"}
        jar_path = self.agent._get_detekt_jar(config)
        
        self.assertEqual(jar_path, "/path/to/detekt.jar")
    
    @patch('agents.code_analysis.static_analysis_integrator.os.path.exists')
    @patch.object(StaticAnalysisIntegratorAgent, '_download_jar')
    def test_get_detekt_jar_download(self, mock_download, mock_exists):
        """Test _get_detekt_jar với auto-download."""
        # First call (jar doesn't exist) returns False, second call returns True after download
        mock_exists.side_effect = [False, False, True]
        mock_download.return_value = "/home/user/.ai_codescan/jars/detekt-cli-1.23.4-all.jar"
        
        config = {"version": "1.23.4"}
        jar_path = self.agent._get_detekt_jar(config)
        
        self.assertIsNotNone(jar_path)
        mock_download.assert_called_once()
    
    def test_parse_detekt_xml_output(self):
        """Test parse_detekt_output với XML content."""
        findings = self.agent.parse_detekt_output(self.sample_detekt_xml, self.kotlin_project_path)
        
        self.assertEqual(len(findings), 5)
        
        # Test first finding
        first_finding = findings[0]
        self.assertEqual(first_finding.line_number, 5)
        self.assertEqual(first_finding.column_number, 1)
        self.assertEqual(first_finding.severity, SeverityLevel.MEDIUM)
        self.assertEqual(first_finding.finding_type, FindingType.REFACTOR)
        self.assertEqual(first_finding.rule_id, "MagicNumber")
        self.assertEqual(first_finding.message, "Magic number found: 42")
        self.assertEqual(first_finding.tool, "detekt")
        self.assertIsNotNone(first_finding.suggestion)
        
        # Test severity mapping
        error_finding = findings[1]  # FunctionNaming with severity="error"
        self.assertEqual(error_finding.severity, SeverityLevel.HIGH)
        
        info_finding = findings[2]  # LoopWithTooManyJumpStatements with severity="info"
        self.assertEqual(info_finding.severity, SeverityLevel.LOW)
    
    def test_parse_detekt_text_output(self):
        """Test parse_detekt_text_output."""
        findings = self.agent.parse_detekt_text_output(self.sample_detekt_text, self.kotlin_project_path)
        
        self.assertEqual(len(findings), 4)
        
        # Test pattern matching
        first_finding = findings[0]
        self.assertEqual(first_finding.line_number, 5)
        self.assertEqual(first_finding.column_number, 1)
        self.assertEqual(first_finding.rule_id, "MagicNumber")
        
        # Test alternative pattern (without column)
        large_class_finding = findings[2]
        self.assertEqual(large_class_finding.line_number, 8)
        self.assertEqual(large_class_finding.column_number, 1)  # Default
        self.assertEqual(large_class_finding.rule_id, "LargeClass")
    
    def test_classify_detekt_finding_by_source(self):
        """Test _classify_detekt_finding với source categorization."""
        # Security category
        severity, finding_type = self.agent._classify_detekt_finding(
            "warning", "UnsafeCall", "detekt.security.UnsafeCall"
        )
        self.assertEqual(finding_type, FindingType.SECURITY)
        
        # Performance category
        severity, finding_type = self.agent._classify_detekt_finding(
            "warning", "SlowIteration", "detekt.performance.SlowIteration"
        )
        self.assertEqual(finding_type, FindingType.PERFORMANCE)
        
        # Complexity category
        severity, finding_type = self.agent._classify_detekt_finding(
            "warning", "LargeClass", "detekt.complexity.LargeClass"
        )
        self.assertEqual(finding_type, FindingType.REFACTOR)
        
        # Style category
        severity, finding_type = self.agent._classify_detekt_finding(
            "warning", "MagicNumber", "detekt.style.MagicNumber"
        )
        self.assertEqual(finding_type, FindingType.STYLE)
    
    def test_classify_detekt_finding_by_rule_name(self):
        """Test _classify_detekt_finding với rule name patterns."""
        # Magic number -> REFACTOR
        severity, finding_type = self.agent._classify_detekt_finding(
            "warning", "MagicNumber", ""
        )
        self.assertEqual(finding_type, FindingType.REFACTOR)
        
        # Unused -> WARNING
        severity, finding_type = self.agent._classify_detekt_finding(
            "warning", "UnusedImports", ""
        )
        self.assertEqual(finding_type, FindingType.WARNING)
        
        # Naming -> CONVENTION
        severity, finding_type = self.agent._classify_detekt_finding(
            "warning", "FunctionNaming", ""
        )
        self.assertEqual(finding_type, FindingType.CONVENTION)
        
        # Complexity -> REFACTOR
        severity, finding_type = self.agent._classify_detekt_finding(
            "warning", "ComplexMethod", ""
        )
        self.assertEqual(finding_type, FindingType.REFACTOR)
    
    def test_get_detekt_suggestion(self):
        """Test _get_detekt_suggestion method."""
        suggestion = self.agent._get_detekt_suggestion("MagicNumber")
        self.assertIsNotNone(suggestion)
        self.assertIn("magic numbers", suggestion.lower())
        
        suggestion = self.agent._get_detekt_suggestion("LongMethod")
        self.assertIsNotNone(suggestion)
        self.assertIn("method", suggestion.lower())
        
        # Unknown rule
        suggestion = self.agent._get_detekt_suggestion("UnknownRule")
        self.assertIsNone(suggestion)
    
    @patch('agents.code_analysis.static_analysis_integrator.os.walk')
    @patch('agents.code_analysis.static_analysis_integrator.subprocess.run')
    @patch.object(StaticAnalysisIntegratorAgent, '_get_detekt_jar')
    @patch('agents.code_analysis.static_analysis_integrator.os.path.exists')
    @patch('agents.code_analysis.static_analysis_integrator.os.remove')
    @patch('builtins.open', new_callable=mock_open)
    def test_run_detekt_success_with_xml(self, mock_file_open, mock_remove, mock_exists, 
                                        mock_get_jar, mock_subprocess, mock_walk):
        """Test run_detekt với successful execution và XML report."""
        # Setup mocks
        mock_walk.return_value = [('/test', ['src'], ['Main.kt'])]
        mock_get_jar.return_value = "/path/to/detekt.jar"
        mock_exists.return_value = True  # XML report exists
        mock_file_open.return_value.read.return_value = self.sample_detekt_xml
        
        # Mock subprocess success
        mock_process = Mock()
        mock_process.stdout = "Detekt analysis completed"
        mock_process.stderr = ""
        mock_subprocess.return_value = mock_process
        
        result = self.agent.run_detekt(self.kotlin_project_path)
        
        self.assertTrue(result.success)
        self.assertEqual(result.tool, "detekt")
        self.assertEqual(result.total_files_analyzed, 1)
        self.assertEqual(result.total_findings, 5)
        self.assertEqual(len(result.findings), 5)
        
        # Verify command construction
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]  # First positional argument
        self.assertIn("java", call_args)
        self.assertIn("-jar", call_args)
        self.assertIn("/path/to/detekt.jar", call_args)
        self.assertIn("--input", call_args)
        self.assertIn(self.kotlin_project_path, call_args)
        
        # Verify XML report cleanup
        mock_remove.assert_called_once()
    
    @patch('agents.code_analysis.static_analysis_integrator.os.walk')
    @patch('agents.code_analysis.static_analysis_integrator.subprocess.run')
    @patch.object(StaticAnalysisIntegratorAgent, '_get_detekt_jar')
    @patch('agents.code_analysis.static_analysis_integrator.os.path.exists')
    def test_run_detekt_success_text_fallback(self, mock_exists, mock_get_jar, 
                                             mock_subprocess, mock_walk):
        """Test run_detekt với text output fallback."""
        # Setup mocks
        mock_walk.return_value = [('/test', ['src'], ['Main.kt'])]
        mock_get_jar.return_value = "/path/to/detekt.jar"
        mock_exists.return_value = False  # No XML report
        
        # Mock subprocess success với text output
        mock_process = Mock()
        mock_process.stdout = self.sample_detekt_text
        mock_process.stderr = ""
        mock_subprocess.return_value = mock_process
        
        result = self.agent.run_detekt(self.kotlin_project_path)
        
        self.assertTrue(result.success)
        self.assertEqual(result.total_findings, 4)
        self.assertEqual(len(result.findings), 4)
    
    @patch('agents.code_analysis.static_analysis_integrator.os.walk')
    def test_run_detekt_no_kotlin_files(self, mock_walk):
        """Test run_detekt với no Kotlin files."""
        mock_walk.return_value = [('/test', ['src'], ['README.md'])]
        
        result = self.agent.run_detekt(self.kotlin_project_path)
        
        self.assertFalse(result.success)
        self.assertEqual(result.total_files_analyzed, 0)
        self.assertIn("Không tìm thấy file .kt", result.error_message)
    
    @patch('agents.code_analysis.static_analysis_integrator.os.walk')
    @patch.object(StaticAnalysisIntegratorAgent, '_get_detekt_jar')
    def test_run_detekt_no_jar(self, mock_get_jar, mock_walk):
        """Test run_detekt khi không thể get JAR."""
        mock_walk.return_value = [('/test', ['src'], ['Main.kt'])]
        mock_get_jar.return_value = None
        
        result = self.agent.run_detekt(self.kotlin_project_path)
        
        self.assertFalse(result.success)
        self.assertIn("Không thể download", result.error_message)
    
    @patch('agents.code_analysis.static_analysis_integrator.os.walk')
    @patch('agents.code_analysis.static_analysis_integrator.subprocess.run')
    @patch.object(StaticAnalysisIntegratorAgent, '_get_detekt_jar')
    def test_run_detekt_timeout(self, mock_get_jar, mock_subprocess, mock_walk):
        """Test run_detekt với subprocess timeout."""
        mock_walk.return_value = [('/test', ['src'], ['Main.kt'])]
        mock_get_jar.return_value = "/path/to/detekt.jar"
        mock_subprocess.side_effect = subprocess.TimeoutExpired("java", 300)
        
        result = self.agent.run_detekt(self.kotlin_project_path)
        
        self.assertFalse(result.success)
        self.assertIn("timeout", result.error_message)
    
    @patch('agents.code_analysis.static_analysis_integrator.os.walk')
    @patch('agents.code_analysis.static_analysis_integrator.subprocess.run')
    @patch.object(StaticAnalysisIntegratorAgent, '_get_detekt_jar')
    def test_run_detekt_subprocess_error(self, mock_get_jar, mock_subprocess, mock_walk):
        """Test run_detekt với subprocess error."""
        mock_walk.return_value = [('/test', ['src'], ['Main.kt'])]
        mock_get_jar.return_value = "/path/to/detekt.jar"
        mock_subprocess.side_effect = Exception("Java command failed")
        
        result = self.agent.run_detekt(self.kotlin_project_path)
        
        self.assertFalse(result.success)
        self.assertIn("Java command failed", result.error_message)
    
    def test_detekt_config_options(self):
        """Test Detekt configuration options được build correctly."""
        # Create agent với custom config
        custom_config = {
            "detekt": {
                "enabled": True,
                "config_file": "/custom/detekt.yml",
                "baseline": "/custom/baseline.xml",
                "fail_fast": True,
                "auto_correct": True,
                "exclude_patterns": ["**/test/**", "**/build/**"]
            }
        }
        
        agent = StaticAnalysisIntegratorAgent(custom_config)
        config = agent.tools_config["detekt"]
        
        self.assertEqual(config["config_file"], "/custom/detekt.yml")
        self.assertEqual(config["baseline"], "/custom/baseline.xml")
        self.assertTrue(config["fail_fast"])
        self.assertTrue(config["auto_correct"])
        self.assertIn("**/test/**", config["exclude_patterns"])
    
    def test_integration_with_main_run_analysis(self):
        """Test integration với main run_analysis method."""
        with patch.object(self.agent, 'run_detekt') as mock_run_detekt:
            mock_result = AnalysisResult(
                tool="detekt",
                project_path=self.kotlin_project_path,
                total_files_analyzed=5,
                total_findings=10,
                findings=[],
                execution_time_seconds=2.5,
                success=True
            )
            mock_run_detekt.return_value = mock_result
            
            results = self.agent.run_analysis(self.kotlin_project_path, ["detekt"])
            
            self.assertIn("detekt", results)
            self.assertEqual(results["detekt"].total_findings, 10)
            mock_run_detekt.assert_called_once_with(self.kotlin_project_path)


if __name__ == '__main__':
    unittest.main() 