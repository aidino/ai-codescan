#!/usr/bin/env python3
"""
Tests cho Dart Static Analysis Integration functionality.
"""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.agents.code_analysis.static_analysis_integrator import (
    StaticAnalysisIntegratorAgent, 
    AnalysisResult, 
    Finding, 
    SeverityLevel, 
    FindingType
)


class TestDartStaticAnalysis(unittest.TestCase):
    """Test Dart static analysis integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent = StaticAnalysisIntegratorAgent()
        
        # Create temporary Dart project directory
        self.temp_dir = tempfile.mkdtemp()
        self.dart_project_path = os.path.join(self.temp_dir, "dart_project")
        os.makedirs(self.dart_project_path)
        
        # Create pubspec.yaml to make it a valid Dart project
        pubspec_content = """
name: test_dart_project
description: Test Dart project for static analysis
version: 1.0.0

environment:
  sdk: '>=2.17.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter

dev_dependencies:
  flutter_test:
    sdk: flutter
"""
        with open(os.path.join(self.dart_project_path, "pubspec.yaml"), "w") as f:
            f.write(pubspec_content)
        
        # Create lib directory with sample Dart file
        lib_dir = os.path.join(self.dart_project_path, "lib")
        os.makedirs(lib_dir)
        
        dart_file_content = """
class TestClass {
  String name;
  int age;
  
  TestClass(this.name, this.age);
  
  void printInfo() {
    print('Name: $name, Age: $age');
  }
}

void main() {
  var person = new TestClass('John', 25);
  person.printInfo();
}
"""
        with open(os.path.join(lib_dir, "main.dart"), "w") as f:
            f.write(dart_file_content)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_dart_analyze_in_supported_tools(self):
        """Test rằng dart_analyze có trong supported tools."""
        self.assertIn("dart_analyze", self.agent.supported_tools)
    
    def test_dart_analyze_config_exists(self):
        """Test rằng dart_analyze config tồn tại trong default config."""
        config = self.agent._get_default_config()
        self.assertIn("dart_analyze", config)
        
        dart_config = config["dart_analyze"]
        self.assertIn("enabled", dart_config)
        self.assertIn("fatal_infos", dart_config)
        self.assertIn("fatal_warnings", dart_config)
        self.assertIn("exclude_patterns", dart_config)
    
    def test_count_dart_files(self):
        """Test counting Dart files trong project."""
        count = self.agent._count_dart_files(self.dart_project_path)
        self.assertEqual(count, 1)  # Should find main.dart
    
    def test_dart_analyze_no_pubspec(self):
        """Test dart analyze với project không có pubspec.yaml."""
        # Create project without pubspec.yaml
        no_pubspec_dir = os.path.join(self.temp_dir, "no_pubspec")
        os.makedirs(no_pubspec_dir)
        
        result = self.agent.run_dart_analyze(no_pubspec_dir)
        
        self.assertFalse(result.success)
        self.assertIn("pubspec.yaml", result.error_message)
        self.assertEqual(result.tool, "dart_analyze")
        self.assertEqual(result.total_findings, 0)
    
    @patch('subprocess.run')
    def test_dart_analyze_success(self, mock_subprocess):
        """Test successful dart analyze execution."""
        # Mock successful dart analyze output
        mock_result = Mock()
        mock_result.stdout = "lib/main.dart:10:5 • Prefer const with constant constructors • prefer_const_constructors\n"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        result = self.agent.run_dart_analyze(self.dart_project_path)
        
        self.assertTrue(result.success)
        self.assertEqual(result.tool, "dart_analyze")
        self.assertEqual(result.total_findings, 1)
        self.assertEqual(len(result.findings), 1)
        
        # Check finding details
        finding = result.findings[0]
        self.assertIn("main.dart", finding.file_path)
        self.assertEqual(finding.line_number, 10)
        self.assertEqual(finding.column_number, 5)
        self.assertEqual(finding.rule_id, "prefer_const_constructors")
        self.assertEqual(finding.tool, "dart_analyze")
    
    @patch('subprocess.run')
    def test_dart_analyze_no_issues(self, mock_subprocess):
        """Test dart analyze với no issues."""
        # Mock dart analyze output with no issues
        mock_result = Mock()
        mock_result.stdout = "Analyzing project...\nNo issues found!\n"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        result = self.agent.run_dart_analyze(self.dart_project_path)
        
        self.assertTrue(result.success)
        self.assertEqual(result.total_findings, 0)
        self.assertEqual(len(result.findings), 0)
    
    @patch('subprocess.run')
    def test_dart_analyze_timeout(self, mock_subprocess):
        """Test dart analyze timeout."""
        # Mock timeout exception
        import subprocess
        mock_subprocess.side_effect = subprocess.TimeoutExpired("dart", 300)
        
        result = self.agent.run_dart_analyze(self.dart_project_path)
        
        self.assertFalse(result.success)
        self.assertIn("timeout", result.error_message)
        self.assertEqual(result.total_findings, 0)
    
    @patch('subprocess.run')
    def test_dart_analyze_not_installed(self, mock_subprocess):
        """Test dart analyze khi Dart SDK không được cài đặt."""
        # Mock FileNotFoundError
        mock_subprocess.side_effect = FileNotFoundError("dart command not found")
        
        result = self.agent.run_dart_analyze(self.dart_project_path)
        
        self.assertFalse(result.success)
        self.assertIn("Dart SDK", result.error_message)
        self.assertEqual(result.total_findings, 0)
    
    def test_parse_dart_analyze_output_standard_format(self):
        """Test parsing standard dart analyze output format."""
        output = """
lib/main.dart:10:5 • Prefer const with constant constructors • prefer_const_constructors
lib/utils.dart:15:10 • Avoid print calls in production code • avoid_print
lib/models.dart:20:1 • Use UpperCamelCase for types • camel_case_types
"""
        
        findings = self.agent.parse_dart_analyze_output(output, self.dart_project_path)
        
        self.assertEqual(len(findings), 3)
        
        # Check first finding
        finding1 = findings[0]
        self.assertIn("main.dart", finding1.file_path)
        self.assertEqual(finding1.line_number, 10)
        self.assertEqual(finding1.column_number, 5)
        self.assertEqual(finding1.rule_id, "prefer_const_constructors")
        self.assertEqual(finding1.severity, SeverityLevel.LOW)
        self.assertEqual(finding1.finding_type, FindingType.STYLE)
        
        # Check suggestion exists
        self.assertIsNotNone(finding1.suggestion)
    
    def test_parse_dart_analyze_output_alternative_format(self):
        """Test parsing alternative dart analyze output format."""
        output = """
lib/main.dart:10:5: error: Undefined name 'variable'
lib/utils.dart:15:10: warning: Unused import
lib/models.dart:20:1: info: Consider making this field final
"""
        
        findings = self.agent.parse_dart_analyze_output(output, self.dart_project_path)
        
        self.assertEqual(len(findings), 3)
        
        # Check severity mapping
        error_finding = findings[0]
        self.assertEqual(error_finding.severity, SeverityLevel.HIGH)
        self.assertEqual(error_finding.finding_type, FindingType.ERROR)
        
        warning_finding = findings[1]
        self.assertEqual(warning_finding.severity, SeverityLevel.MEDIUM)
        self.assertEqual(warning_finding.finding_type, FindingType.WARNING)
        
        info_finding = findings[2]
        self.assertEqual(info_finding.severity, SeverityLevel.LOW)
        self.assertEqual(info_finding.finding_type, FindingType.CONVENTION)
    
    def test_parse_dart_analyze_empty_output(self):
        """Test parsing empty dart analyze output."""
        output = ""
        
        findings = self.agent.parse_dart_analyze_output(output, self.dart_project_path)
        
        self.assertEqual(len(findings), 0)
    
    def test_classify_dart_finding_error_rules(self):
        """Test classification của Dart error rules."""
        test_cases = [
            ("undefined_name", "Error message", SeverityLevel.HIGH, FindingType.ERROR),
            ("missing_required_param", "Missing parameter", SeverityLevel.HIGH, FindingType.ERROR),
            ("invalid_assignment", "Invalid assignment", SeverityLevel.HIGH, FindingType.ERROR),
            ("syntax_error", "Syntax error", SeverityLevel.HIGH, FindingType.ERROR),
        ]
        
        for rule_id, message, expected_severity, expected_type in test_cases:
            with self.subTest(rule_id=rule_id):
                severity, finding_type = self.agent._classify_dart_finding(rule_id, message)
                self.assertEqual(severity, expected_severity)
                self.assertEqual(finding_type, expected_type)
    
    def test_classify_dart_finding_warning_rules(self):
        """Test classification của Dart warning rules."""
        test_cases = [
            ("unused_import", "Unused import", SeverityLevel.MEDIUM, FindingType.WARNING),
            ("dead_code", "Dead code detected", SeverityLevel.MEDIUM, FindingType.WARNING),
            ("deprecated_api", "Deprecated API", SeverityLevel.MEDIUM, FindingType.WARNING),
            ("avoid_print", "Avoid print", SeverityLevel.MEDIUM, FindingType.WARNING),
        ]
        
        for rule_id, message, expected_severity, expected_type in test_cases:
            with self.subTest(rule_id=rule_id):
                severity, finding_type = self.agent._classify_dart_finding(rule_id, message)
                self.assertEqual(severity, expected_severity)
                self.assertEqual(finding_type, expected_type)
    
    def test_classify_dart_finding_style_rules(self):
        """Test classification của Dart style rules."""
        test_cases = [
            ("prefer_const_constructors", "Prefer const", SeverityLevel.LOW, FindingType.STYLE),
            ("camel_case_types", "Use CamelCase", SeverityLevel.LOW, FindingType.STYLE),
            ("prefer_single_quotes", "Use single quotes", SeverityLevel.LOW, FindingType.STYLE),
            ("file_names", "File naming", SeverityLevel.LOW, FindingType.STYLE),
        ]
        
        for rule_id, message, expected_severity, expected_type in test_cases:
            with self.subTest(rule_id=rule_id):
                severity, finding_type = self.agent._classify_dart_finding(rule_id, message)
                self.assertEqual(severity, expected_severity)
                self.assertEqual(finding_type, expected_type)
    
    def test_classify_dart_finding_performance_rules(self):
        """Test classification của Dart performance rules."""
        test_cases = [
            ("avoid_function_literals_in_foreach_calls", "Performance issue", SeverityLevel.MEDIUM, FindingType.PERFORMANCE),
            ("prefer_foreach", "Use forEach", SeverityLevel.MEDIUM, FindingType.PERFORMANCE),
            ("avoid_slow_async_io", "Slow async IO", SeverityLevel.MEDIUM, FindingType.PERFORMANCE),
        ]
        
        for rule_id, message, expected_severity, expected_type in test_cases:
            with self.subTest(rule_id=rule_id):
                severity, finding_type = self.agent._classify_dart_finding(rule_id, message)
                self.assertEqual(severity, expected_severity)
                self.assertEqual(finding_type, expected_type)
    
    def test_get_dart_suggestion(self):
        """Test getting suggestions cho common Dart rules."""
        test_cases = [
            ("prefer_const_constructors", "const constructors"),
            ("avoid_print", "logging framework"),
            ("prefer_final_fields", "final"),
            ("unnecessary_new", "không cần thiết"),
            ("prefer_is_empty", "isempty"),
        ]
        
        for rule_id, expected_keyword in test_cases:
            with self.subTest(rule_id=rule_id):
                suggestion = self.agent._get_dart_suggestion(rule_id)
                self.assertIsNotNone(suggestion)
                self.assertIn(expected_keyword, suggestion.lower())
    
    def test_map_dart_severity(self):
        """Test mapping Dart severity strings."""
        test_cases = [
            ("error", SeverityLevel.HIGH),
            ("warning", SeverityLevel.MEDIUM),
            ("info", SeverityLevel.LOW),
            ("hint", SeverityLevel.LOW),
            ("unknown", SeverityLevel.LOW),  # Default case
        ]
        
        for severity_str, expected_severity in test_cases:
            with self.subTest(severity_str=severity_str):
                result = self.agent._map_dart_severity(severity_str)
                self.assertEqual(result, expected_severity)
    
    def test_map_dart_type(self):
        """Test mapping Dart type strings."""
        test_cases = [
            ("error", FindingType.ERROR),
            ("warning", FindingType.WARNING),
            ("info", FindingType.CONVENTION),
            ("hint", FindingType.STYLE),
            ("unknown", FindingType.STYLE),  # Default case
        ]
        
        for type_str, expected_type in test_cases:
            with self.subTest(type_str=type_str):
                result = self.agent._map_dart_type(type_str)
                self.assertEqual(result, expected_type)
    
    def test_run_analysis_includes_dart_analyze(self):
        """Test rằng run_analysis bao gồm dart_analyze khi được enabled."""
        # Set dart_analyze enabled in config
        self.agent.tools_config["dart_analyze"]["enabled"] = True
        
        with patch.object(self.agent, 'run_dart_analyze') as mock_dart_analyze:
            mock_dart_analyze.return_value = AnalysisResult(
                tool="dart_analyze",
                project_path=self.dart_project_path,
                total_files_analyzed=1,
                total_findings=0,
                findings=[],
                execution_time_seconds=1.0,
                success=True
            )
            
            results = self.agent.run_analysis(self.dart_project_path, tools=["dart_analyze"])
            
            self.assertIn("dart_analyze", results)
            mock_dart_analyze.assert_called_once_with(self.dart_project_path)
    
    def test_dart_analyze_with_config_options(self):
        """Test dart analyze với configuration options."""
        # Set config options
        self.agent.tools_config["dart_analyze"]["fatal_infos"] = True
        self.agent.tools_config["dart_analyze"]["fatal_warnings"] = True
        
        with patch('subprocess.run') as mock_subprocess:
            mock_result = Mock()
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_result.returncode = 0
            mock_subprocess.return_value = mock_result
            
            self.agent.run_dart_analyze(self.dart_project_path)
            
            # Check command includes config options
            called_command = mock_subprocess.call_args[0][0]
            self.assertIn("--fatal-infos", called_command)
            self.assertIn("--fatal-warnings", called_command)


if __name__ == '__main__':
    unittest.main() 