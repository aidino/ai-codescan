#!/usr/bin/env python3
"""
Tests for Java static analysis integration (Checkstyle and PMD).
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

from src.agents.code_analysis.static_analysis_integrator import (
    StaticAnalysisIntegratorAgent, 
    AnalysisResult, 
    Finding, 
    SeverityLevel, 
    FindingType
)


class TestJavaStaticAnalysisIntegration:
    """Test Java static analysis tools integration."""
    
    def setup_method(self):
        """Setup test environment."""
        # Custom config for testing
        self.config = {
            "checkstyle": {
                "enabled": True,
                "version": "10.12.4",
                "jar_path": None  # Will use mocked download
            },
            "pmd": {
                "enabled": True,
                "version": "7.0.0",
                "jar_path": None,  # Will use mocked download
                "rulesets": ["java-basic", "java-design"]
            }
        }
        self.integrator = StaticAnalysisIntegratorAgent(self.config)
        
    def create_temp_java_project(self) -> str:
        """Create a temporary Java project for testing."""
        temp_dir = tempfile.mkdtemp()
        
        # Create a simple Java file
        java_content = '''
package com.test.example;

import java.util.List;
import java.util.ArrayList;

public class TestClass {
    private List<String> items;
    
    public TestClass() {
        this.items = new ArrayList<>();
    }
    
    public void addItem(String item) {
        items.add(item);
    }
    
    public List<String> getItems() {
        return items;
    }
    
    // Method with potential issues for testing
    public void badMethod() {
        String s = "test";  // Unused variable
        if (true) {  // Always true condition
            System.out.println("Hello");
        }
    }
}
'''
        
        # Create directory structure
        package_dir = Path(temp_dir) / "src" / "main" / "java" / "com" / "test" / "example"
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # Write Java file
        with open(package_dir / "TestClass.java", "w") as f:
            f.write(java_content)
            
        return temp_dir
    
    def test_java_files_count(self):
        """Test counting Java files in project."""
        project_path = self.create_temp_java_project()
        
        count = self.integrator._count_java_files(project_path)
        
        assert count == 1
        
        # Cleanup
        import shutil
        shutil.rmtree(project_path)
    
    def test_java_files_count_empty_project(self):
        """Test counting Java files in empty project."""
        temp_dir = tempfile.mkdtemp()
        
        count = self.integrator._count_java_files(temp_dir)
        
        assert count == 0
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
    
    @patch('src.agents.code_analysis.static_analysis_integrator.StaticAnalysisIntegratorAgent._get_checkstyle_jar')
    @patch('subprocess.run')
    def test_run_checkstyle_success(self, mock_subprocess, mock_get_jar):
        """Test successful Checkstyle execution."""
        project_path = self.create_temp_java_project()
        
        # Mock JAR path
        mock_get_jar.return_value = "/mock/checkstyle.jar"
        
        # Mock subprocess result
        mock_result = Mock()
        mock_result.stdout = '''<?xml version="1.0" encoding="UTF-8"?>
<checkstyle version="10.12.4">
    <file name="/test/TestClass.java">
        <error line="10" column="5" severity="warning" message="Unused variable" source="com.puppycrawl.tools.checkstyle.checks.coding.UnusedLocalVariableCheck"/>
        <error line="15" column="1" severity="error" message="Method too long" source="com.puppycrawl.tools.checkstyle.checks.sizes.MethodLengthCheck"/>
    </file>
</checkstyle>'''
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        # Run Checkstyle
        result = self.integrator.run_checkstyle(project_path)
        
        # Verify result
        assert result.success
        assert result.tool == "checkstyle"
        assert result.total_files_analyzed == 1
        assert result.total_findings == 2
        assert len(result.findings) == 2
        
        # Check findings
        finding1 = result.findings[0]
        assert finding1.line_number == 10
        assert finding1.severity == SeverityLevel.MEDIUM
        assert "Unused variable" in finding1.message
        
        finding2 = result.findings[1]
        assert finding2.line_number == 15
        assert finding2.severity == SeverityLevel.HIGH
        assert "Method too long" in finding2.message
        
        # Cleanup
        import shutil
        shutil.rmtree(project_path)
    
    @patch('src.agents.code_analysis.static_analysis_integrator.StaticAnalysisIntegratorAgent._get_checkstyle_jar')
    def test_run_checkstyle_no_jar(self, mock_get_jar):
        """Test Checkstyle execution when JAR not available."""
        project_path = self.create_temp_java_project()
        
        # Mock JAR not found
        mock_get_jar.return_value = None
        
        # Run Checkstyle
        result = self.integrator.run_checkstyle(project_path)
        
        # Verify result
        assert not result.success
        assert "Không thể download hoặc tìm thấy Checkstyle JAR" in result.error_message
        
        # Cleanup
        import shutil
        shutil.rmtree(project_path)
    
    def test_run_checkstyle_no_java_files(self):
        """Test Checkstyle on project with no Java files."""
        temp_dir = tempfile.mkdtemp()
        
        # Run Checkstyle
        result = self.integrator.run_checkstyle(temp_dir)
        
        # Verify result
        assert result.success  # Success but no files to analyze
        assert result.total_files_analyzed == 0
        assert result.total_findings == 0
        assert "Không có file Java để analyze" in result.error_message
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
    
    def test_parse_checkstyle_xml_output(self):
        """Test parsing Checkstyle XML output."""
        xml_output = '''<?xml version="1.0" encoding="UTF-8"?>
<checkstyle version="10.12.4">
    <file name="/project/src/TestClass.java">
        <error line="10" column="5" severity="warning" message="Unused import" source="com.puppycrawl.tools.checkstyle.checks.imports.UnusedImportsCheck"/>
        <error line="20" column="1" severity="error" message="Line too long" source="com.puppycrawl.tools.checkstyle.checks.sizes.LineLengthCheck"/>
    </file>
    <file name="/project/src/AnotherClass.java">
        <error line="5" column="1" severity="info" message="Missing javadoc" source="com.puppycrawl.tools.checkstyle.checks.javadoc.MissingJavadocMethodCheck"/>
    </file>
</checkstyle>'''
        
        findings = self.integrator.parse_checkstyle_output(xml_output, "/project")
        
        assert len(findings) == 3
        
        # Check first finding
        finding1 = findings[0]
        assert finding1.file_path == "src/TestClass.java"
        assert finding1.line_number == 10
        assert finding1.column_number == 5
        assert finding1.severity == SeverityLevel.MEDIUM
        assert finding1.rule_id == "UnusedImportsCheck"
        assert "Unused import" in finding1.message
        assert finding1.tool == "checkstyle"
        
        # Check second finding
        finding2 = findings[1]
        assert finding2.severity == SeverityLevel.HIGH
        assert finding2.rule_id == "LineLengthCheck"
        
        # Check third finding
        finding3 = findings[2]
        assert finding3.file_path == "src/AnotherClass.java"
        assert finding3.severity == SeverityLevel.LOW
        assert finding3.rule_id == "MissingJavadocMethodCheck"
    
    def test_parse_checkstyle_text_fallback(self):
        """Test Checkstyle text fallback parser."""
        text_output = """[WARN] /project/src/Test.java:10:5: Unused variable
[ERROR] /project/src/Test.java:15:1: Line too long
[INFO] /project/src/Test.java:20:1: Missing javadoc"""
        
        findings = self.integrator._parse_checkstyle_text_fallback(text_output, "/project")
        
        assert len(findings) == 3
        
        # Check severity mapping
        assert findings[0].severity == SeverityLevel.MEDIUM  # WARN
        assert findings[1].severity == SeverityLevel.HIGH    # ERROR
        assert findings[2].severity == SeverityLevel.LOW     # INFO
    
    def test_classify_checkstyle_finding(self):
        """Test Checkstyle finding classification."""
        # Test severity mapping
        severity_high, _ = self.integrator._classify_checkstyle_finding("error", "TestRule")
        assert severity_high == SeverityLevel.HIGH
        
        severity_medium, _ = self.integrator._classify_checkstyle_finding("warning", "TestRule")
        assert severity_medium == SeverityLevel.MEDIUM
        
        severity_low, _ = self.integrator._classify_checkstyle_finding("info", "TestRule")
        assert severity_low == SeverityLevel.LOW
        
        # Test finding type mapping
        _, type_security = self.integrator._classify_checkstyle_finding("warning", "SecurityRule")
        assert type_security == FindingType.SECURITY
        
        _, type_style = self.integrator._classify_checkstyle_finding("warning", "IndentationCheck")
        assert type_style == FindingType.STYLE
        
        _, type_refactor = self.integrator._classify_checkstyle_finding("warning", "DesignForExtension")
        assert type_refactor == FindingType.REFACTOR
    
    @patch('src.agents.code_analysis.static_analysis_integrator.StaticAnalysisIntegratorAgent._get_pmd_jar')
    @patch('subprocess.run')
    def test_run_pmd_success(self, mock_subprocess, mock_get_jar):
        """Test successful PMD execution."""
        project_path = self.create_temp_java_project()
        
        # Mock JAR path
        mock_get_jar.return_value = "/mock/pmd.jar"
        
        # Mock subprocess result
        mock_result = Mock()
        mock_result.stdout = '''<?xml version="1.0" encoding="UTF-8"?>
<pmd xmlns="http://pmd.sourceforge.net/report/2.0.0">
    <file name="/test/TestClass.java">
        <violation beginline="10" begincolumn="5" priority="3" rule="UnusedLocalVariable" ruleset="java-basic">
            Avoid unused local variables such as 'unusedVar'.
        </violation>
        <violation beginline="15" begincolumn="1" priority="2" rule="ExcessiveMethodLength" ruleset="java-design">
            This method is too long.
        </violation>
    </file>
</pmd>'''
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        # Run PMD
        result = self.integrator.run_pmd(project_path)
        
        # Verify result
        assert result.success
        assert result.tool == "pmd"
        assert result.total_files_analyzed == 1
        assert result.total_findings == 2
        assert len(result.findings) == 2
        
        # Check findings
        finding1 = result.findings[0]
        assert finding1.line_number == 10
        assert finding1.severity == SeverityLevel.MEDIUM  # Priority 3
        assert "unused" in finding1.message.lower()
        
        finding2 = result.findings[1]
        assert finding2.line_number == 15
        assert finding2.severity == SeverityLevel.HIGH  # Priority 2
        assert "too long" in finding2.message.lower()
        
        # Cleanup
        import shutil
        shutil.rmtree(project_path)
    
    def test_parse_pmd_xml_output(self):
        """Test parsing PMD XML output."""
        xml_output = '''<?xml version="1.0" encoding="UTF-8"?>
<pmd xmlns="http://pmd.sourceforge.net/report/2.0.0">
    <file name="/project/src/TestClass.java">
        <violation beginline="10" begincolumn="5" priority="1" rule="CriticalRule" ruleset="java-security">
            Critical security issue found.
        </violation>
        <violation beginline="20" begincolumn="1" priority="4" rule="MinorStyle" ruleset="java-codestyle">
            Minor style issue.
        </violation>
    </file>
</pmd>'''
        
        findings = self.integrator.parse_pmd_output(xml_output, "/project")
        
        assert len(findings) == 2
        
        # Check first finding (critical)
        finding1 = findings[0]
        assert finding1.file_path == "src/TestClass.java"
        assert finding1.line_number == 10
        assert finding1.column_number == 5
        assert finding1.severity == SeverityLevel.CRITICAL  # Priority 1
        assert finding1.rule_id == "java-security/CriticalRule"
        assert finding1.finding_type == FindingType.SECURITY
        assert "Critical security issue" in finding1.message
        assert finding1.tool == "pmd"
        
        # Check second finding (low priority)
        finding2 = findings[1]
        assert finding2.severity == SeverityLevel.LOW  # Priority 4
        assert finding2.finding_type == FindingType.STYLE
    
    def test_classify_pmd_finding(self):
        """Test PMD finding classification."""
        # Test security
        finding_type = self.integrator._classify_pmd_finding("java-security", "SecurityRule")
        assert finding_type == FindingType.SECURITY
        
        # Test performance
        finding_type = self.integrator._classify_pmd_finding("java-performance", "PerformanceRule")
        assert finding_type == FindingType.PERFORMANCE
        
        # Test design/refactor
        finding_type = self.integrator._classify_pmd_finding("java-design", "ComplexityRule")
        assert finding_type == FindingType.REFACTOR
        
        # Test style
        finding_type = self.integrator._classify_pmd_finding("java-codestyle", "NamingRule")
        assert finding_type == FindingType.STYLE
        
        # Test error prone
        finding_type = self.integrator._classify_pmd_finding("java-errorprone", "ErrorRule")
        assert finding_type == FindingType.ERROR
        
        # Test default
        finding_type = self.integrator._classify_pmd_finding("java-basic", "GenericRule")
        assert finding_type == FindingType.WARNING
    
    @patch('urllib.request.urlretrieve')
    @patch('os.path.exists')
    def test_download_jar_checkstyle(self, mock_exists, mock_urlretrieve):
        """Test downloading Checkstyle JAR."""
        # Mock file doesn't exist initially
        mock_exists.return_value = False
        
        # Mock successful download
        mock_urlretrieve.return_value = None
        
        jar_path = self.integrator._download_jar(
            "checkstyle", 
            "10.12.4", 
            "https://github.com/checkstyle/checkstyle/releases/download/checkstyle-10.12.4/checkstyle-10.12.4-all.jar"
        )
        
        assert jar_path is not None
        assert "checkstyle-10.12.4.jar" in jar_path
        
        # Verify download was called
        mock_urlretrieve.assert_called_once()
    
    @patch('urllib.request.urlretrieve')
    @patch('zipfile.ZipFile')
    @patch('os.path.exists')
    def test_download_jar_pmd_zip(self, mock_exists, mock_zipfile, mock_urlretrieve):
        """Test downloading PMD ZIP and extracting JAR."""
        # Mock file doesn't exist initially
        mock_exists.return_value = False
        
        # Mock successful download
        mock_urlretrieve.return_value = None
        
        # Mock ZIP extraction
        mock_zip = Mock()
        mock_zip.namelist.return_value = ["pmd-dist-7.0.0/lib/pmd-core-7.0.0.jar", "other-file.txt"]
        mock_zipfile.return_value.__enter__.return_value = mock_zip
        
        # Mock Path operations
        with patch('pathlib.Path.rename'), patch('pathlib.Path.mkdir'):
            jar_path = self.integrator._download_jar(
                "pmd",
                "7.0.0",
                "https://github.com/pmd/pmd/releases/download/pmd_releases%2F7.0.0/pmd-dist-7.0.0-bin.zip"
            )
        
        assert jar_path is not None
        assert "pmd-7.0.0.jar" in jar_path
        
        # Verify extraction was called
        mock_zip.extract.assert_called_once()
    
    def test_java_tools_in_supported_list(self):
        """Test that Java tools are in supported tools list."""
        assert "checkstyle" in self.integrator.supported_tools
        assert "pmd" in self.integrator.supported_tools
    
    def test_java_tools_default_config(self):
        """Test default configuration for Java tools."""
        config = self.integrator._get_default_config()
        
        # Check Checkstyle config
        assert "checkstyle" in config
        checkstyle_config = config["checkstyle"]
        assert checkstyle_config["enabled"] is True
        assert checkstyle_config["version"] == "10.12.4"
        assert checkstyle_config["jar_path"] is None
        
        # Check PMD config
        assert "pmd" in config
        pmd_config = config["pmd"]
        assert pmd_config["enabled"] is True
        assert pmd_config["version"] == "7.0.0"
        assert pmd_config["jar_path"] is None
        assert "java-basic" in pmd_config["rulesets"]
    
    @patch('src.agents.code_analysis.static_analysis_integrator.StaticAnalysisIntegratorAgent._get_checkstyle_jar')
    @patch('src.agents.code_analysis.static_analysis_integrator.StaticAnalysisIntegratorAgent._get_pmd_jar')
    @patch('subprocess.run')
    def test_run_analysis_java_tools(self, mock_subprocess, mock_get_pmd_jar, mock_get_checkstyle_jar):
        """Test running analysis with Java tools."""
        project_path = self.create_temp_java_project()
        
        # Mock JAR paths
        mock_get_checkstyle_jar.return_value = "/mock/checkstyle.jar"
        mock_get_pmd_jar.return_value = "/mock/pmd.jar"
        
        # Mock subprocess results
        mock_result = Mock()
        mock_result.stdout = '<?xml version="1.0" encoding="UTF-8"?><checkstyle version="10.12.4"></checkstyle>'
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        # Run analysis with Java tools
        results = self.integrator.run_analysis(project_path, tools=["checkstyle", "pmd"])
        
        # Verify results
        assert "checkstyle" in results
        assert "pmd" in results
        assert results["checkstyle"].success
        assert results["pmd"].success
        
        # Cleanup
        import shutil
        shutil.rmtree(project_path)


if __name__ == "__main__":
    pytest.main([__file__]) 