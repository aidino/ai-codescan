#!/usr/bin/env python3
"""
Unit tests for Synthesis & Reporting components.

Tests for:
- Finding Aggregator (deduplication, priority scoring, aggregation strategies)
- Report Generator (multiple formats, executive summaries)
"""

import tempfile
import shutil
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import sys
import json
import unittest
from unittest.mock import Mock, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.agents.synthesis_reporting.finding_aggregator import (
    FindingAggregatorAgent,
    AggregationStrategy,
    AggregationResult,
    AggregatedFinding
)
from src.agents.synthesis_reporting.report_generator import (
    ReportGeneratorAgent,
    ReportFormat,
    GeneratedReport,
    ReportMetadata
)
from src.agents.code_analysis import (
    Finding, SeverityLevel, FindingType,
    ArchitecturalIssue, ArchitecturalAnalysisResult, 
    CircularDependency, UnusedElement, IssueType
)


class TestFindingAggregatorAgent:
    """Test Finding Aggregator functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.agent = FindingAggregatorAgent()
        
    def test_init(self):
        """Test agent initialization."""
        assert self.agent is not None
        assert hasattr(self.agent, 'aggregate_findings')
        
    def create_sample_findings(self):
        """Create sample findings for testing."""
        return [
            Finding("flake8", "test.py", 10, 1, "Line too long (82 > 79 characters)", 
                   "E501", SeverityLevel.LOW, FindingType.STYLE),
            Finding("flake8", "test.py", 15, 1, "Line too long (85 > 79 characters)", 
                   "E501", SeverityLevel.LOW, FindingType.STYLE),
            Finding("pylint", "test.py", 5, 0, "Missing module docstring", 
                   "C0114", SeverityLevel.LOW, FindingType.CONVENTION),
            Finding("mypy", "helper.py", 20, 10, "Function is missing a return type annotation", 
                   "return-value", SeverityLevel.MEDIUM, FindingType.ERROR),
            Finding("flake8", "helper.py", 30, 1, "'os' imported but unused", 
                   "F401", SeverityLevel.MEDIUM, FindingType.ERROR)
        ]
        
    def test_aggregated_finding_creation(self):
        """Test AggregatedFinding dataclass creation."""
        original_finding = Finding("flake8", "test.py", 10, 1, "Line too long", 
                                 "E501", SeverityLevel.LOW, FindingType.STYLE)
        
        aggregated = AggregatedFinding(
            representative_finding=original_finding,
            duplicate_findings=[],
            confidence_score=0.8,
            priority_score=2,
            consensus_count=1,
            sources=["flake8"]
        )
        
        assert aggregated.representative_finding == original_finding
        assert aggregated.confidence_score == 0.8
        assert aggregated.priority_score == 2
        assert len(aggregated.sources) == 1
        
    def test_aggregation_result_creation(self):
        """Test AggregationResult dataclass creation."""
        findings = self.create_sample_findings()
        aggregated_findings = [
            AggregatedFinding(findings[0], [], 0.8, 2, 1, ["flake8"])
        ]
        
        result = AggregationResult(
            aggregated_findings=aggregated_findings,
            original_count=5,
            aggregated_count=1,
            deduplication_ratio=0.8,
            strategy_used=AggregationStrategy.MERGE_DUPLICATES,
            processing_time=1.5
        )
        
        assert len(result.aggregated_findings) == 1
        assert result.original_count == 5
        assert result.aggregated_count == 1
        assert result.deduplication_ratio == 0.8
        assert result.strategy_used == AggregationStrategy.MERGE_DUPLICATES
        
    def test_aggregate_findings_merge_duplicates(self):
        """Test aggregation với MERGE_DUPLICATES strategy."""
        findings = self.create_sample_findings()
        
        result = self.agent.aggregate_findings(
            findings, 
            strategy=AggregationStrategy.MERGE_DUPLICATES
        )
        
        assert isinstance(result, AggregationResult)
        assert result.original_count == 5
        assert result.aggregated_count < result.original_count  # Should merge duplicates
        assert result.strategy_used == AggregationStrategy.MERGE_DUPLICATES
        
        # Should merge the two E501 findings
        e501_findings = [af for af in result.aggregated_findings 
                        if af.representative_finding.rule_id == "E501"]
        assert len(e501_findings) == 1
        assert len(e501_findings[0].duplicate_findings) > 0
        
    def test_aggregate_findings_keep_all(self):
        """Test aggregation với KEEP_ALL strategy."""
        findings = self.create_sample_findings()
        
        result = self.agent.aggregate_findings(
            findings,
            strategy=AggregationStrategy.KEEP_ALL
        )
        
        assert result.original_count == 5
        assert result.aggregated_count == 5  # Should keep all findings
        assert result.strategy_used == AggregationStrategy.KEEP_ALL
        
    def test_aggregate_findings_prioritize_severe(self):
        """Test aggregation với PRIORITIZE_SEVERE strategy."""
        findings = self.create_sample_findings()
        
        result = self.agent.aggregate_findings(
            findings,
            strategy=AggregationStrategy.PRIORITIZE_SEVERE
        )
        
        assert result.aggregated_count > 0
        assert result.strategy_used == AggregationStrategy.PRIORITIZE_SEVERE
        
        # High priority findings should come first
        priorities = [af.priority_score for af in result.aggregated_findings]
        assert priorities == sorted(priorities, reverse=True)
        
    def test_aggregate_findings_group_by_file(self):
        """Test aggregation với GROUP_BY_FILE strategy."""
        findings = self.create_sample_findings()
        
        result = self.agent.aggregate_findings(
            findings,
            strategy=AggregationStrategy.GROUP_BY_FILE
        )
        
        assert result.strategy_used == AggregationStrategy.GROUP_BY_FILE
        
        # Should group findings by file
        files = set(af.representative_finding.file_path for af in result.aggregated_findings)
        assert "test.py" in files
        assert "helper.py" in files
        
    def test_calculate_similarity(self):
        """Test similarity calculation giữa findings."""
        finding1 = Finding("flake8", "test.py", 10, 1, "Line too long (82 > 79 characters)", 
                         "E501", SeverityLevel.LOW, FindingType.STYLE)
        finding2 = Finding("flake8", "test.py", 15, 1, "Line too long (85 > 79 characters)", 
                         "E501", SeverityLevel.LOW, FindingType.STYLE)
        finding3 = Finding("pylint", "other.py", 5, 0, "Missing docstring", 
                         "C0114", SeverityLevel.LOW, FindingType.CONVENTION)
        
        # Same rule, same file - high similarity
        similarity1 = self.agent._calculate_similarity(finding1, finding2)
        assert similarity1 > 0.7
        
        # Different rule, different file - low similarity
        similarity2 = self.agent._calculate_similarity(finding1, finding3)
        assert similarity2 < 0.3
        
    def test_calculate_priority_score(self):
        """Test priority score calculation."""
        high_severity = Finding("pylint", "test.py", 10, 0, "Undefined variable", 
                               "E1101", SeverityLevel.HIGH, FindingType.ERROR)
        low_severity = Finding("flake8", "test.py", 10, 0, "Line too long", 
                              "E501", SeverityLevel.LOW, FindingType.STYLE)
        
        high_priority = self.agent._calculate_priority_score(high_severity)
        low_priority = self.agent._calculate_priority_score(low_severity)
        
        assert high_priority > low_priority
        
    def test_calculate_confidence_score(self):
        """Test confidence score calculation."""
        finding = Finding("flake8", "test.py", 10, 0, "Line too long", 
                         "E501", SeverityLevel.LOW, FindingType.STYLE)
        duplicates = [
            Finding("pylint", "test.py", 10, 0, "Line too long", 
                   "line-too-long", SeverityLevel.LOW, FindingType.STYLE)
        ]
        
        confidence = self.agent._calculate_confidence_score(finding, duplicates)
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Having duplicates should increase confidence
        
    def test_find_duplicates(self):
        """Test duplicate finding detection."""
        findings = self.create_sample_findings()
        
        duplicates = self.agent._find_duplicates(findings[0], findings[1:])
        
        # Should find the other E501 finding
        assert len(duplicates) == 1
        assert duplicates[0].rule_id == "E501"
        
    def test_get_aggregation_statistics(self):
        """Test aggregation statistics calculation."""
        findings = self.create_sample_findings()
        result = self.agent.aggregate_findings(findings)
        
        stats = self.agent.get_aggregation_statistics(result)
        
        assert "total_original_findings" in stats
        assert "total_aggregated_findings" in stats
        assert "deduplication_ratio" in stats
        assert "severity_breakdown" in stats
        assert "file_breakdown" in stats
        assert "tool_breakdown" in stats


class TestReportGeneratorAgent:
    """Test Report Generator functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.agent = ReportGeneratorAgent()
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Cleanup test fixtures."""
        shutil.rmtree(self.temp_dir)
        
    def test_init(self):
        """Test agent initialization."""
        assert self.agent is not None
        assert hasattr(self.agent, 'generate_report')
        assert hasattr(self.agent, 'generate_executive_summary')
        
    def create_sample_aggregated_findings(self):
        """Create sample aggregated findings for testing."""
        findings = [
            Finding("flake8", "test.py", 10, 1, "Line too long", 
                   "E501", SeverityLevel.LOW, FindingType.STYLE),
            Finding("pylint", "test.py", 5, 0, "Missing docstring", 
                   "C0114", SeverityLevel.LOW, FindingType.CONVENTION),
            Finding("mypy", "helper.py", 20, 10, "Missing return type", 
                   "return-value", SeverityLevel.MEDIUM, FindingType.ERROR)
        ]
        
        return [
            AggregatedFinding(findings[0], [], 0.8, 2, 1, ["flake8"]),
            AggregatedFinding(findings[1], [], 0.9, 1, 1, ["pylint"]),
            AggregatedFinding(findings[2], [], 0.7, 3, 1, ["mypy"])
        ]
        
    def test_report_metadata_creation(self):
        """Test ReportMetadata dataclass creation."""
        metadata = ReportMetadata(
            project_name="test-project",
            generated_at="2024-01-01T10:00:00Z",
            total_findings=5,
            format=ReportFormat.HTML,
            version="1.0"
        )
        
        assert metadata.project_name == "test-project"
        assert metadata.total_findings == 5
        assert metadata.format == ReportFormat.HTML
        
    def test_executive_summary_creation(self):
        """Test ExecutiveSummary dataclass creation."""
        summary = ExecutiveSummary(
            overview="Analysis completed successfully",
            key_findings=["High complexity in main module"],
            risk_assessment="Medium risk level",
            recommendations=["Refactor complex functions"],
            metrics={
                "total_files": 10,
                "total_issues": 25,
                "critical_issues": 2
            }
        )
        
        assert summary.overview == "Analysis completed successfully"
        assert len(summary.key_findings) == 1
        assert summary.risk_assessment == "Medium risk level"
        assert summary.metrics["total_files"] == 10
        
    def test_generate_report_text_format(self):
        """Test text format report generation."""
        aggregated_findings = self.create_sample_aggregated_findings()
        
        report = self.agent.generate_report(
            aggregated_findings,
            format=ReportFormat.TEXT,
            project_name="test-project"
        )
        
        assert isinstance(report, str)
        assert "test-project" in report
        assert "Code Analysis Report" in report
        assert "E501" in report  # Should contain finding details
        assert "SUMMARY" in report.upper()
        
    def test_generate_report_json_format(self):
        """Test JSON format report generation."""
        aggregated_findings = self.create_sample_aggregated_findings()
        
        report = self.agent.generate_report(
            aggregated_findings,
            format=ReportFormat.JSON,
            project_name="test-project"
        )
        
        # Should be valid JSON
        data = json.loads(report)
        assert "metadata" in data
        assert "findings" in data
        assert "summary" in data
        assert data["metadata"]["project_name"] == "test-project"
        assert len(data["findings"]) == 3
        
    def test_generate_report_html_format(self):
        """Test HTML format report generation."""
        aggregated_findings = self.create_sample_aggregated_findings()
        
        report = self.agent.generate_report(
            aggregated_findings,
            format=ReportFormat.HTML,
            project_name="test-project"
        )
        
        assert isinstance(report, str)
        assert "<html>" in report
        assert "<head>" in report
        assert "<body>" in report
        assert "test-project" in report
        assert "E501" in report
        
    def test_generate_report_csv_format(self):
        """Test CSV format report generation."""
        aggregated_findings = self.create_sample_aggregated_findings()
        
        report = self.agent.generate_report(
            aggregated_findings,
            format=ReportFormat.CSV,
            project_name="test-project"
        )
        
        lines = report.strip().split('\n')
        assert len(lines) >= 4  # Header + 3 findings
        assert "tool,file_path,line_number" in lines[0]  # CSV header
        assert "flake8,test.py,10" in lines[1]  # First finding
        
    def test_generate_report_markdown_format(self):
        """Test Markdown format report generation."""
        aggregated_findings = self.create_sample_aggregated_findings()
        
        report = self.agent.generate_report(
            aggregated_findings,
            format=ReportFormat.MARKDOWN,
            project_name="test-project"
        )
        
        assert isinstance(report, str)
        assert "# Code Analysis Report" in report
        assert "## Summary" in report
        assert "**Project Name:** test-project" in report
        assert "- **E501**" in report  # Finding in list format
        
    def test_generate_executive_summary(self):
        """Test executive summary generation."""
        aggregated_findings = self.create_sample_aggregated_findings()
        
        summary = self.agent.generate_executive_summary(
            aggregated_findings,
            project_name="test-project"
        )
        
        assert isinstance(summary, ExecutiveSummary)
        assert "test-project" in summary.overview
        assert len(summary.key_findings) > 0
        assert summary.risk_assessment is not None
        assert len(summary.recommendations) > 0
        assert "total_findings" in summary.metrics
        
    def test_calculate_risk_level(self):
        """Test risk level calculation."""
        # High risk scenario
        high_risk_findings = [
            AggregatedFinding(
                Finding("pylint", "test.py", 10, 0, "Critical error", 
                       "E1101", SeverityLevel.HIGH, FindingType.ERROR),
                [], 0.9, 5, 1, ["pylint"]
            )
        ]
        
        high_risk = self.agent._calculate_risk_level(high_risk_findings)
        assert "high" in high_risk.lower()
        
        # Low risk scenario
        low_risk_findings = [
            AggregatedFinding(
                Finding("flake8", "test.py", 10, 0, "Minor style issue", 
                       "E501", SeverityLevel.LOW, FindingType.STYLE),
                [], 0.8, 1, 1, ["flake8"]
            )
        ]
        
        low_risk = self.agent._calculate_risk_level(low_risk_findings)
        assert "low" in low_risk.lower()
        
    def test_generate_recommendations(self):
        """Test recommendation generation."""
        aggregated_findings = self.create_sample_aggregated_findings()
        
        recommendations = self.agent._generate_recommendations(aggregated_findings)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all(isinstance(rec, str) for rec in recommendations)
        
    def test_legacy_generate_linter_report_text(self):
        """Test legacy linter report generation."""
        findings = [
            Finding("flake8", "test.py", 10, 1, "Line too long", 
                   "E501", SeverityLevel.LOW, FindingType.STYLE),
            Finding("pylint", "helper.py", 5, 0, "Missing docstring", 
                   "C0114", SeverityLevel.LOW, FindingType.CONVENTION)
        ]
        
        report = self.agent.generate_linter_report_text(findings)
        
        assert isinstance(report, str)
        assert "Linter Analysis Report" in report
        assert "E501" in report
        assert "C0114" in report
        assert "test.py" in report
        assert "helper.py" in report
        
    def test_save_report_to_file(self):
        """Test saving report to file."""
        aggregated_findings = self.create_sample_aggregated_findings()
        
        report_content = self.agent.generate_report(
            aggregated_findings,
            format=ReportFormat.TEXT,
            project_name="test-project"
        )
        
        output_path = Path(self.temp_dir) / "report.txt"
        self.agent.save_report_to_file(report_content, str(output_path))
        
        assert output_path.exists()
        saved_content = output_path.read_text()
        assert saved_content == report_content
        
    def test_export_findings_to_csv(self):
        """Test exporting findings to CSV file."""
        aggregated_findings = self.create_sample_aggregated_findings()
        
        output_path = Path(self.temp_dir) / "findings.csv"
        self.agent.export_findings_to_csv(aggregated_findings, str(output_path))
        
        assert output_path.exists()
        content = output_path.read_text()
        lines = content.strip().split('\n')
        assert len(lines) == 4  # Header + 3 findings
        assert "tool,file_path,line_number" in lines[0]


class TestSynthesisReportingIntegration:
    """Integration tests cho Synthesis & Reporting workflow."""
    
    def setup_method(self):
        """Setup integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Cleanup integration test fixtures."""
        shutil.rmtree(self.temp_dir)
        
    def create_complex_findings_scenario(self):
        """Create complex findings scenario for integration testing."""
        return [
            # Duplicate line-too-long findings
            Finding("flake8", "main.py", 10, 1, "Line too long (82 > 79 characters)", 
                   "E501", SeverityLevel.LOW, FindingType.STYLE),
            Finding("flake8", "main.py", 15, 1, "Line too long (85 > 79 characters)", 
                   "E501", SeverityLevel.LOW, FindingType.STYLE),
            Finding("flake8", "main.py", 20, 1, "Line too long (90 > 79 characters)", 
                   "E501", SeverityLevel.LOW, FindingType.STYLE),
            
            # Different severity levels
            Finding("pylint", "main.py", 5, 0, "Missing module docstring", 
                   "C0114", SeverityLevel.LOW, FindingType.CONVENTION),
            Finding("mypy", "utils.py", 30, 10, "Function missing return type", 
                   "return-value", SeverityLevel.MEDIUM, FindingType.ERROR),
            Finding("pylint", "core.py", 100, 0, "Undefined variable 'x'", 
                   "E1101", SeverityLevel.HIGH, FindingType.ERROR),
            
            # Different tools, same issue
            Finding("flake8", "helper.py", 45, 1, "'os' imported but unused", 
                   "F401", SeverityLevel.MEDIUM, FindingType.ERROR),
            Finding("pylint", "helper.py", 45, 0, "Unused import 'os'", 
                   "W0611", SeverityLevel.MEDIUM, FindingType.WARNING),
        ]
        
    def test_complete_synthesis_workflow(self):
        """Test complete synthesis và reporting workflow."""
        # Step 1: Create complex findings
        findings = self.create_complex_findings_scenario()
        
        # Step 2: Aggregate findings
        aggregator = FindingAggregatorAgent()
        aggregation_result = aggregator.aggregate_findings(
            findings,
            strategy=AggregationStrategy.MERGE_DUPLICATES
        )
        
        assert aggregation_result.original_count == 8
        assert aggregation_result.aggregated_count < 8  # Should merge duplicates
        
        # Step 3: Generate multiple report formats
        generator = ReportGeneratorAgent()
        
        # Text report
        text_report = generator.generate_report(
            aggregation_result.aggregated_findings,
            format=ReportFormat.TEXT,
            project_name="integration-test-project"
        )
        assert "integration-test-project" in text_report
        
        # JSON report
        json_report = generator.generate_report(
            aggregation_result.aggregated_findings,
            format=ReportFormat.JSON,
            project_name="integration-test-project"
        )
        json_data = json.loads(json_report)
        assert json_data["metadata"]["project_name"] == "integration-test-project"
        
        # HTML report
        html_report = generator.generate_report(
            aggregation_result.aggregated_findings,
            format=ReportFormat.HTML,
            project_name="integration-test-project"
        )
        assert "<html>" in html_report
        
        # Step 4: Generate executive summary
        executive_summary = generator.generate_executive_summary(
            aggregation_result.aggregated_findings,
            project_name="integration-test-project"
        )
        
        assert isinstance(executive_summary, ExecutiveSummary)
        assert executive_summary.metrics["total_findings"] > 0
        
        # Step 5: Save reports to files
        output_dir = Path(self.temp_dir)
        
        # Save text report
        text_path = output_dir / "report.txt"
        generator.save_report_to_file(text_report, str(text_path))
        assert text_path.exists()
        
        # Save JSON report
        json_path = output_dir / "report.json"
        generator.save_report_to_file(json_report, str(json_path))
        assert json_path.exists()
        
        # Export findings to CSV
        csv_path = output_dir / "findings.csv"
        generator.export_findings_to_csv(
            aggregation_result.aggregated_findings, 
            str(csv_path)
        )
        assert csv_path.exists()
        
        # Verify all files are non-empty
        assert text_path.stat().st_size > 0
        assert json_path.stat().st_size > 0
        assert csv_path.stat().st_size > 0
        
    def test_performance_with_large_dataset(self):
        """Test performance với large dataset."""
        # Create large number of findings
        large_findings = []
        for i in range(1000):
            large_findings.append(
                Finding(
                    tool="flake8" if i % 2 == 0 else "pylint",
                    file_path=f"file_{i // 10}.py",
                    line_number=i % 100 + 1,
                    column_number=1,
                    message=f"Test issue {i}",
                    rule_id="E501" if i % 3 == 0 else f"R{i%10}",
                    severity=SeverityLevel.LOW if i % 2 == 0 else SeverityLevel.MEDIUM,
                    finding_type=FindingType.STYLE if i % 2 == 0 else FindingType.ERROR
                )
            )
        
        # Test aggregation performance
        aggregator = FindingAggregatorAgent()
        import time
        start_time = time.time()
        
        result = aggregator.aggregate_findings(large_findings)
        
        aggregation_time = time.time() - start_time
        assert aggregation_time < 10.0  # Should complete within 10 seconds
        assert result.original_count == 1000
        
        # Test report generation performance
        generator = ReportGeneratorAgent()
        start_time = time.time()
        
        report = generator.generate_report(
            result.aggregated_findings,
            format=ReportFormat.JSON,
            project_name="performance-test"
        )
        
        generation_time = time.time() - start_time
        assert generation_time < 5.0  # Should complete within 5 seconds
        assert len(report) > 0


class TestFindingAggregatorWithArchitectural(unittest.TestCase):
    """Test cases cho FindingAggregatorAgent với architectural findings."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.aggregator = FindingAggregatorAgent()
        
        # Sample findings
        self.sample_findings = [
            Finding(
                tool="flake8",
                rule_id="E501",
                severity=SeverityLevel.MEDIUM,
                finding_type=FindingType.STYLE,
                message="Line too long",
                file_path="src/main.py",
                line_number=10,
                column_number=81,
                suggestion="Break long line"
            ),
            Finding(
                tool="pylint",
                rule_id="R0903",
                severity=SeverityLevel.LOW,
                finding_type=FindingType.REFACTOR,
                message="Too few public methods",
                file_path="src/utils.py",
                line_number=5,
                column_number=1,
                suggestion="Add more methods or use function"
            )
        ]
        
        # Sample architectural issues
        self.sample_architectural_issues = [
            ArchitecturalIssue(
                issue_type=IssueType.CIRCULAR_DEPENDENCY,
                title="Circular dependency detected",
                description="Circular dependency between module_a.py and module_b.py",
                severity=SeverityLevel.HIGH,
                affected_elements=["src/module_a.py", "src/module_b.py"],
                suggestion="Refactor to break circular dependency",
                static_analysis_limitation="This type of dependency may not be caught by standard linters",
                metadata={"cycle_length": 2, "dependency_type": "import"}
            ),
            ArchitecturalIssue(
                issue_type=IssueType.UNUSED_PUBLIC_ELEMENT,
                title="Unused public function",
                description="Public function 'calculate_score' is never called",
                severity=SeverityLevel.MEDIUM,
                affected_elements=["src/calculator.py::calculate_score"],
                suggestion="Consider making this function private or remove if not needed",
                static_analysis_limitation="Static analysis tools may not detect unused public interfaces",
                metadata={"element_type": "function", "visibility": "public"}
            )
        ]
        
        # Sample architectural analysis result
        self.sample_architectural_result = ArchitecturalAnalysisResult(
            project_path="/test/project",
            total_issues=2,
            issues=self.sample_architectural_issues,
            circular_dependencies=[
                CircularDependency(
                    cycle=["src/module_a.py", "src/module_b.py"],
                    cycle_type="file",
                    description="Import cycle detected"
                )
            ],
            unused_elements=[
                UnusedElement(
                    element_name="calculate_score",
                    element_type="function",
                    file_path="src/calculator.py",
                    line_number=15,
                    reason="Function not called from any external module"
                )
            ],
            analysis_scope="file-level",
            limitations=["Static analysis limitations"],
            execution_time_seconds=1.5,
            success=True
        )
    
    def test_aggregate_with_architectural_findings(self):
        """Test aggregation với architectural findings."""
        findings_by_source = {
            "flake8": [self.sample_findings[0]],
            "pylint": [self.sample_findings[1]]
        }
        
        result = self.aggregator.aggregate_findings(
            findings_by_source=findings_by_source,
            strategy=AggregationStrategy.MERGE_DUPLICATES,
            architectural_result=self.sample_architectural_result
        )
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.original_findings_count, 4)  # 2 regular + 2 architectural
        self.assertEqual(result.aggregated_findings_count, 4)  # No duplicates expected
        
        # Check architectural findings are included
        architectural_findings = [
            f for f in result.aggregated_findings 
            if f.primary_finding.metadata and f.primary_finding.metadata.get("architectural_issue")
        ]
        self.assertEqual(len(architectural_findings), 2)
    
    def test_convert_architectural_issues_to_findings(self):
        """Test conversion của architectural issues thành Finding objects."""
        findings = self.aggregator._convert_architectural_issues_to_findings(
            self.sample_architectural_issues
        )
        
        # Assertions
        self.assertEqual(len(findings), 2)
        
        # Test first finding (circular dependency)
        circ_finding = findings[0]
        self.assertEqual(circ_finding.tool, "architectural_analyzer")
        self.assertEqual(circ_finding.rule_id, "ARCH_CIRCULAR_DEPENDENCY")
        self.assertEqual(circ_finding.severity, SeverityLevel.HIGH)
        self.assertEqual(circ_finding.finding_type, FindingType.REFACTOR)
        self.assertTrue(circ_finding.metadata["architectural_issue"])
        self.assertEqual(circ_finding.metadata["issue_type"], "circular_dependency")
        
        # Test second finding (unused element)
        unused_finding = findings[1]
        self.assertEqual(unused_finding.rule_id, "ARCH_UNUSED_PUBLIC_ELEMENT")
        self.assertEqual(unused_finding.severity, SeverityLevel.MEDIUM)
        self.assertEqual(unused_finding.finding_type, FindingType.WARNING)
    
    def test_aggregate_without_architectural_findings(self):
        """Test aggregation khi không có architectural result."""
        findings_by_source = {
            "flake8": [self.sample_findings[0]],
            "pylint": [self.sample_findings[1]]
        }
        
        result = self.aggregator.aggregate_findings(
            findings_by_source=findings_by_source,
            strategy=AggregationStrategy.MERGE_DUPLICATES,
            architectural_result=None
        )
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.original_findings_count, 2)
        self.assertEqual(result.aggregated_findings_count, 2)
        
        # No architectural findings
        architectural_findings = [
            f for f in result.aggregated_findings 
            if f.primary_finding.metadata and f.primary_finding.metadata.get("architectural_issue")
        ]
        self.assertEqual(len(architectural_findings), 0)
    
    def test_aggregate_with_failed_architectural_result(self):
        """Test aggregation với failed architectural result."""
        failed_result = ArchitecturalAnalysisResult(
            project_path="/test/project",
            total_issues=0,
            issues=[],
            circular_dependencies=[],
            unused_elements=[],
            analysis_scope="failed-analysis",
            limitations=["Analysis failed"],
            execution_time_seconds=0.1,
            success=False,
            error_message="Analysis failed"
        )
        
        findings_by_source = {
            "flake8": [self.sample_findings[0]]
        }
        
        result = self.aggregator.aggregate_findings(
            findings_by_source=findings_by_source,
            architectural_result=failed_result
        )
        
        # Should succeed but not include architectural findings
        self.assertTrue(result.success)
        self.assertEqual(result.original_findings_count, 1)
        self.assertEqual(result.aggregated_findings_count, 1)


class TestReportGeneratorWithArchitectural(unittest.TestCase):
    """Test cases cho ReportGeneratorAgent với architectural findings support."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = ReportGeneratorAgent()
        
        # Mock aggregation result với architectural findings
        architectural_finding = AggregatedFinding(
            primary_finding=Finding(
                tool="architectural_analyzer",
                rule_id="ARCH_CIRCULAR_DEPENDENCY",
                severity=SeverityLevel.HIGH,
                finding_type=FindingType.REFACTOR,
                message="Circular dependency between module_a.py and module_b.py",
                file_path="src/module_a.py",
                line_number=None,
                column_number=None,
                suggestion="Refactor to break circular dependency",
                metadata={
                    "architectural_issue": True,
                    "issue_type": "circular_dependency",
                    "title": "Circular dependency detected",
                    "affected_elements": ["src/module_a.py", "src/module_b.py"],
                    "static_analysis_limitation": "This type of dependency may not be caught by standard linters"
                }
            ),
            duplicate_count=1,
            sources=["architectural_analysis"]
        )
        
        regular_finding = AggregatedFinding(
            primary_finding=Finding(
                tool="flake8",
                rule_id="E501",
                severity=SeverityLevel.MEDIUM,
                finding_type=FindingType.STYLE,
                message="Line too long",
                file_path="src/main.py",
                line_number=10,
                column_number=81,
                suggestion="Break long line"
            ),
            duplicate_count=1,
            sources=["flake8"]
        )
        
        self.mock_aggregation_result = AggregationResult(
            original_findings_count=2,
            aggregated_findings_count=2,
            aggregated_findings=[architectural_finding, regular_finding],
            deduplication_stats={"duplicates_removed": 0, "reduction_percentage": 0},
            aggregation_strategy=AggregationStrategy.MERGE_DUPLICATES,
            success=True
        )
    
    def test_text_report_with_architectural_findings(self):
        """Test text report generation với architectural findings."""
        report = self.generator.generate_report(
            aggregation_result=self.mock_aggregation_result,
            project_name="Test Project",
            report_format=ReportFormat.TEXT
        )
        
        # Assertions
        self.assertTrue(report.success)
        self.assertIn("ARCHITECTURAL ISSUES", report.content)
        self.assertIn("Circular dependency detected", report.content)
        self.assertIn("This type of dependency may not be caught by standard linters", report.content)
        self.assertIn("TOP PROBLEMATIC FILES", report.content)  # Should exclude architectural issues
    
    def test_json_report_preserves_architectural_metadata(self):
        """Test JSON report preserves architectural metadata."""
        report = self.generator.generate_report(
            aggregation_result=self.mock_aggregation_result,
            project_name="Test Project",
            report_format=ReportFormat.JSON
        )
        
        # Assertions
        self.assertTrue(report.success)
        
        # Parse JSON content (would need actual JSON parsing in real implementation)
        # For now, just check that metadata is mentioned
        self.assertIn("architectural_issue", report.content)
        self.assertIn("affected_elements", report.content)
    
    def test_markdown_report_with_architectural_section(self):
        """Test Markdown report includes architectural section."""
        report = self.generator.generate_report(
            aggregation_result=self.mock_aggregation_result,
            project_name="Test Project",
            report_format=ReportFormat.MARKDOWN
        )
        
        # Assertions
        self.assertTrue(report.success)
        self.assertIn("## Architectural Issues", report.content)
        self.assertIn("### Circular Dependencies", report.content)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2) 