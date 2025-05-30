#!/usr/bin/env python3
"""
AI CodeScan - Report Generator Agent

Agent generate các loại reports từ aggregated findings.
Supports multiple report formats: text, JSON, HTML, CSV.
"""

import json
import csv
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from loguru import logger
from io import StringIO
from enum import Enum

from .finding_aggregator import AggregatedFinding, AggregationResult, AggregationStrategy
from ..code_analysis import SeverityLevel, FindingType


class ReportFormat(Enum):
    """Supported report formats."""
    TEXT = "text"
    JSON = "json"
    HTML = "html"
    CSV = "csv"
    MARKDOWN = "markdown"


@dataclass
class ReportMetadata:
    """Metadata cho report."""
    generated_at: datetime
    project_name: str
    total_findings: int
    aggregation_strategy: str
    report_format: ReportFormat
    generator_version: str = "1.0"


@dataclass
class GeneratedReport:
    """Generated report with metadata."""
    content: str
    metadata: ReportMetadata
    format: ReportFormat
    success: bool
    error_message: Optional[str] = None


class ReportGeneratorAgent:
    """
    Agent generate reports từ analysis results.
    
    Trách nhiệm:
    - Generate reports trong multiple formats
    - Create executive summaries
    - Format findings với details
    - Export reports đến different outputs
    - Customize report templates
    """
    
    def __init__(self, 
                 default_format: ReportFormat = ReportFormat.TEXT,
                 include_metadata: bool = True):
        """
        Khởi tạo ReportGeneratorAgent.
        
        Args:
            default_format: Default report format
            include_metadata: Whether to include metadata in reports
        """
        self.default_format = default_format
        self.include_metadata = include_metadata
    
    def generate_report(self, 
                       aggregation_result: AggregationResult,
                       project_name: str = "Unknown Project",
                       report_format: Optional[ReportFormat] = None,
                       options: Optional[Dict[str, Any]] = None) -> GeneratedReport:
        """
        Generate report từ aggregation result.
        
        Args:
            aggregation_result: Aggregated findings
            project_name: Tên project
            report_format: Format của report
            options: Additional options cho report generation
            
        Returns:
            GeneratedReport: Generated report
        """
        format_to_use = report_format or self.default_format
        options = options or {}
        
        try:
            logger.info(f"Generating {format_to_use.value} report cho project: {project_name}")
            
            if not aggregation_result.success:
                return GeneratedReport(
                    content="",
                    metadata=ReportMetadata(
                        generated_at=datetime.now(),
                        project_name=project_name,
                        total_findings=0,
                        aggregation_strategy="failed",
                        report_format=format_to_use
                    ),
                    format=format_to_use,
                    success=False,
                    error_message=f"Aggregation failed: {aggregation_result.error_message}"
                )
            
            # Generate content based on format
            if format_to_use == ReportFormat.TEXT:
                content = self._generate_text_report(aggregation_result, project_name, options)
            elif format_to_use == ReportFormat.JSON:
                content = self._generate_json_report(aggregation_result, project_name, options)
            elif format_to_use == ReportFormat.HTML:
                content = self._generate_html_report(aggregation_result, project_name, options)
            elif format_to_use == ReportFormat.CSV:
                content = self._generate_csv_report(aggregation_result, project_name, options)
            elif format_to_use == ReportFormat.MARKDOWN:
                content = self._generate_markdown_report(aggregation_result, project_name, options)
            else:
                raise ValueError(f"Unsupported report format: {format_to_use}")
            
            # Create metadata
            metadata = ReportMetadata(
                generated_at=datetime.now(),
                project_name=project_name,
                total_findings=aggregation_result.aggregated_findings_count,
                aggregation_strategy=aggregation_result.aggregation_strategy.value,
                report_format=format_to_use
            )
            
            return GeneratedReport(
                content=content,
                metadata=metadata,
                format=format_to_use,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return GeneratedReport(
                content="",
                metadata=ReportMetadata(
                    generated_at=datetime.now(),
                    project_name=project_name,
                    total_findings=0,
                    aggregation_strategy="error",
                    report_format=format_to_use
                ),
                format=format_to_use,
                success=False,
                error_message=str(e)
            )
    
    def _generate_text_report(self, 
                             result: AggregationResult,
                             project_name: str,
                             options: Dict[str, Any]) -> str:
        """Generate plain text report."""
        lines = []
        
        # Header
        lines.append("=" * 60)
        lines.append(f"AI CodeScan Analysis Report")
        lines.append("=" * 60)
        lines.append(f"Project: {project_name}")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Strategy: {result.aggregation_strategy.value}")
        lines.append("")
        
        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 20)
        lines.append(f"Total Findings: {result.aggregated_findings_count}")
        lines.append(f"Original Findings: {result.original_findings_count}")
        
        dedup_stats = result.deduplication_stats
        if dedup_stats.get("duplicates_removed", 0) > 0:
            lines.append(f"Duplicates Removed: {dedup_stats['duplicates_removed']} ({dedup_stats['reduction_percentage']}%)")
        
        lines.append("")
        
        # Severity breakdown
        severity_counts = {}
        type_counts = {}
        file_counts = {}
        
        for finding in result.aggregated_findings:
            severity = finding.primary_finding.severity.value
            ftype = finding.primary_finding.finding_type.value
            fpath = finding.primary_finding.file_path
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            type_counts[ftype] = type_counts.get(ftype, 0) + 1
            file_counts[fpath] = file_counts.get(fpath, 0) + 1
        
        if severity_counts:
            lines.append("SEVERITY BREAKDOWN")
            lines.append("-" * 20)
            for severity in ["critical", "high", "medium", "low"]:
                count = severity_counts.get(severity, 0)
                if count > 0:
                    lines.append(f"{severity.capitalize()}: {count}")
            lines.append("")
        
        if type_counts:
            lines.append("FINDING TYPES")
            lines.append("-" * 20)
            for ftype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"{ftype.capitalize()}: {count}")
            lines.append("")
        
        # Top problematic files
        if file_counts:
            lines.append("TOP PROBLEMATIC FILES")
            lines.append("-" * 20)
            top_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            for fpath, count in top_files:
                lines.append(f"{fpath}: {count} finding(s)")
            lines.append("")
        
        # High priority findings
        high_priority = [f for f in result.aggregated_findings if f.priority_score >= 0.7]
        if high_priority:
            lines.append("HIGH PRIORITY FINDINGS")
            lines.append("-" * 20)
            for i, finding in enumerate(high_priority[:10], 1):
                pf = finding.primary_finding
                lines.append(f"{i}. {pf.file_path}:{pf.line_number}")
                lines.append(f"   {pf.severity.value.upper()}: {pf.message}")
                lines.append(f"   Rule: {pf.rule_id} | Tool: {pf.tool}")
                lines.append(f"   Priority: {finding.priority_score:.2f} | Confidence: {finding.confidence_score:.2f}")
                if len(finding.sources) > 1:
                    lines.append(f"   Sources: {', '.join(finding.sources)}")
                lines.append("")
        
        # Detailed findings (if requested)
        if options.get("include_all_findings", False):
            lines.append("ALL FINDINGS")
            lines.append("-" * 20)
            for i, finding in enumerate(result.aggregated_findings, 1):
                pf = finding.primary_finding
                lines.append(f"{i}. {pf.file_path}:{pf.line_number}:{pf.column_number}")
                lines.append(f"   {pf.severity.value.upper()} - {pf.finding_type.value.upper()}")
                lines.append(f"   {pf.message}")
                lines.append(f"   Rule: {pf.rule_id} | Tool: {pf.tool}")
                if finding.related_findings:
                    lines.append(f"   Related: {len(finding.related_findings)} similar finding(s)")
                lines.append("")
        
        return "\n".join(lines)
    
    def _generate_json_report(self, 
                             result: AggregationResult,
                             project_name: str,
                             options: Dict[str, Any]) -> str:
        """Generate JSON report."""
        
        # Convert findings to serializable format
        findings_data = []
        for finding in result.aggregated_findings:
            pf = finding.primary_finding
            finding_data = {
                "file_path": pf.file_path,
                "line_number": pf.line_number,
                "column_number": pf.column_number,
                "severity": pf.severity.value,
                "finding_type": pf.finding_type.value,
                "rule_id": pf.rule_id,
                "message": pf.message,
                "tool": pf.tool,
                "priority_score": finding.priority_score,
                "confidence_score": finding.confidence_score,
                "sources": finding.sources,
                "aggregation_reason": finding.aggregation_reason,
                "related_findings_count": len(finding.related_findings)
            }
            
            if options.get("include_related_findings", False):
                finding_data["related_findings"] = [
                    {
                        "file_path": rf.file_path,
                        "line_number": rf.line_number,
                        "message": rf.message,
                        "tool": rf.tool
                    }
                    for rf in finding.related_findings
                ]
            
            findings_data.append(finding_data)
        
        report_data = {
            "metadata": {
                "project_name": project_name,
                "generated_at": datetime.now().isoformat(),
                "generator_version": "1.0",
                "aggregation_strategy": result.aggregation_strategy.value
            },
            "summary": {
                "total_findings": result.aggregated_findings_count,
                "original_findings": result.original_findings_count,
                "deduplication_stats": result.deduplication_stats
            },
            "findings": findings_data
        }
        
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    
    def _generate_csv_report(self, 
                            result: AggregationResult,
                            project_name: str,
                            options: Dict[str, Any]) -> str:
        """Generate CSV report."""
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        headers = [
            "File Path", "Line", "Column", "Severity", "Type", 
            "Rule ID", "Message", "Tool", "Priority Score", 
            "Confidence Score", "Sources", "Related Count"
        ]
        writer.writerow(headers)
        
        # Data rows
        for finding in result.aggregated_findings:
            pf = finding.primary_finding
            row = [
                pf.file_path,
                pf.line_number,
                pf.column_number,
                pf.severity.value,
                pf.finding_type.value,
                pf.rule_id,
                pf.message,
                pf.tool,
                finding.priority_score,
                finding.confidence_score,
                "; ".join(finding.sources),
                len(finding.related_findings)
            ]
            writer.writerow(row)
        
        return output.getvalue()
    
    def _generate_html_report(self, 
                             result: AggregationResult,
                             project_name: str,
                             options: Dict[str, Any]) -> str:
        """Generate HTML report."""
        
        html_parts = []
        
        # HTML header
        html_parts.append("""
<!DOCTYPE html>
<html>
<head>
    <title>AI CodeScan Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 5px; }
        .summary { margin: 20px 0; }
        .finding { border: 1px solid #ddd; margin: 10px 0; padding: 10px; border-radius: 5px; }
        .critical { border-left: 5px solid #dc3545; }
        .high { border-left: 5px solid #fd7e14; }
        .medium { border-left: 5px solid #ffc107; }
        .low { border-left: 5px solid #28a745; }
        .stats { display: flex; gap: 20px; }
        .stat-box { background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
""")
        
        # Header
        html_parts.append(f"""
<div class="header">
    <h1>AI CodeScan Analysis Report</h1>
    <p><strong>Project:</strong> {project_name}</p>
    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><strong>Strategy:</strong> {result.aggregation_strategy.value}</p>
</div>
""")
        
        # Summary stats
        severity_counts = {}
        for finding in result.aggregated_findings:
            severity = finding.primary_finding.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        html_parts.append(f"""
<div class="summary">
    <h2>Summary</h2>
    <div class="stats">
        <div class="stat-box">
            <h3>{result.aggregated_findings_count}</h3>
            <p>Total Findings</p>
        </div>
        <div class="stat-box">
            <h3>{severity_counts.get('critical', 0)}</h3>
            <p>Critical</p>
        </div>
        <div class="stat-box">
            <h3>{severity_counts.get('high', 0)}</h3>
            <p>High</p>
        </div>
        <div class="stat-box">
            <h3>{severity_counts.get('medium', 0)}</h3>
            <p>Medium</p>
        </div>
        <div class="stat-box">
            <h3>{severity_counts.get('low', 0)}</h3>
            <p>Low</p>
        </div>
    </div>
</div>
""")
        
        # Findings table
        html_parts.append("""
<h2>Findings</h2>
<table>
    <thead>
        <tr>
            <th>File</th>
            <th>Line</th>
            <th>Severity</th>
            <th>Type</th>
            <th>Message</th>
            <th>Tool</th>
            <th>Priority</th>
        </tr>
    </thead>
    <tbody>
""")
        
        for finding in result.aggregated_findings:
            pf = finding.primary_finding
            severity_class = pf.severity.value
            html_parts.append(f"""
        <tr class="{severity_class}">
            <td>{pf.file_path}</td>
            <td>{pf.line_number}</td>
            <td><strong>{pf.severity.value.upper()}</strong></td>
            <td>{pf.finding_type.value}</td>
            <td>{pf.message}</td>
            <td>{pf.tool}</td>
            <td>{finding.priority_score:.2f}</td>
        </tr>
""")
        
        html_parts.append("""
    </tbody>
</table>
</body>
</html>
""")
        
        return "".join(html_parts)
    
    def _generate_markdown_report(self, 
                                 result: AggregationResult,
                                 project_name: str,
                                 options: Dict[str, Any]) -> str:
        """Generate Markdown report."""
        
        lines = []
        
        # Header
        lines.append(f"# AI CodeScan Analysis Report")
        lines.append("")
        lines.append(f"**Project:** {project_name}")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Strategy:** {result.aggregation_strategy.value}")
        lines.append("")
        
        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Total Findings:** {result.aggregated_findings_count}")
        lines.append(f"- **Original Findings:** {result.original_findings_count}")
        
        dedup_stats = result.deduplication_stats
        if dedup_stats.get("duplicates_removed", 0) > 0:
            lines.append(f"- **Duplicates Removed:** {dedup_stats['duplicates_removed']} ({dedup_stats['reduction_percentage']}%)")
        
        lines.append("")
        
        # Severity breakdown
        severity_counts = {}
        for finding in result.aggregated_findings:
            severity = finding.primary_finding.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        if severity_counts:
            lines.append("### Severity Breakdown")
            lines.append("")
            for severity in ["critical", "high", "medium", "low"]:
                count = severity_counts.get(severity, 0)
                if count > 0:
                    emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(severity, "")
                    lines.append(f"- {emoji} **{severity.capitalize()}:** {count}")
            lines.append("")
        
        # High priority findings
        high_priority = [f for f in result.aggregated_findings if f.priority_score >= 0.7]
        if high_priority:
            lines.append("## High Priority Findings")
            lines.append("")
            for i, finding in enumerate(high_priority[:10], 1):
                pf = finding.primary_finding
                lines.append(f"### {i}. {pf.file_path}:{pf.line_number}")
                lines.append("")
                lines.append(f"**Severity:** {pf.severity.value.upper()}")
                lines.append(f"**Type:** {pf.finding_type.value}")
                lines.append(f"**Rule:** {pf.rule_id}")
                lines.append(f"**Tool:** {pf.tool}")
                lines.append(f"**Priority Score:** {finding.priority_score:.2f}")
                lines.append("")
                lines.append(f"**Message:** {pf.message}")
                lines.append("")
                if len(finding.sources) > 1:
                    lines.append(f"**Sources:** {', '.join(finding.sources)}")
                    lines.append("")
        
        return "\n".join(lines)
    
    def generate_executive_summary(self, 
                                  aggregation_result: AggregationResult,
                                  project_name: str) -> str:
        """
        Generate executive summary cho non-technical stakeholders.
        
        Args:
            aggregation_result: Aggregated findings
            project_name: Tên project
            
        Returns:
            str: Executive summary
        """
        if not aggregation_result.success:
            return f"Analysis of {project_name} failed: {aggregation_result.error_message}"
        
        findings = aggregation_result.aggregated_findings
        if not findings:
            return f"✅ {project_name} analysis completed with no issues found."
        
        # Calculate stats
        total = len(findings)
        critical = len([f for f in findings if f.primary_finding.severity == SeverityLevel.CRITICAL])
        high = len([f for f in findings if f.primary_finding.severity == SeverityLevel.HIGH])
        medium = len([f for f in findings if f.primary_finding.severity == SeverityLevel.MEDIUM])
        low = len([f for f in findings if f.primary_finding.severity == SeverityLevel.LOW])
        
        high_priority = len([f for f in findings if f.priority_score >= 0.7])
        
        # Generate summary
        summary_lines = []
        summary_lines.append(f"📊 **{project_name} Code Quality Report**")
        summary_lines.append("")
        
        if critical > 0:
            summary_lines.append(f"🔴 **URGENT ACTION REQUIRED:** {critical} critical issue(s) found that need immediate attention.")
        elif high > 0:
            summary_lines.append(f"🟠 **HIGH PRIORITY:** {high} high-severity issue(s) should be addressed soon.")
        elif medium > 0:
            summary_lines.append(f"🟡 **MODERATE:** {medium} medium-severity issue(s) identified for improvement.")
        else:
            summary_lines.append(f"🟢 **GOOD:** Only {low} low-severity issue(s) found.")
        
        summary_lines.append("")
        summary_lines.append(f"**Total Issues:** {total}")
        summary_lines.append(f"**High Priority:** {high_priority}")
        summary_lines.append("")
        
        # Risk assessment
        risk_score = (critical * 4 + high * 3 + medium * 2 + low * 1) / max(total, 1)
        if risk_score >= 3.5:
            risk_level = "🔴 HIGH RISK"
            recommendation = "Immediate code review and fixes recommended before production deployment."
        elif risk_score >= 2.5:
            risk_level = "🟠 MEDIUM RISK"
            recommendation = "Address critical and high severity issues before next release."
        elif risk_score >= 1.5:
            risk_level = "🟡 LOW RISK"
            recommendation = "Consider addressing issues during regular maintenance cycles."
        else:
            risk_level = "🟢 MINIMAL RISK"
            recommendation = "Code quality is good. Minor improvements can be made over time."
        
        summary_lines.append(f"**Risk Level:** {risk_level}")
        summary_lines.append(f"**Recommendation:** {recommendation}")
        
        return "\n".join(summary_lines)
    
    def generate_linter_report_text(self, aggregated_findings: List[AggregatedFinding]) -> str:
        """
        Generate simple linter report text (legacy method for compatibility).
        
        Args:
            aggregated_findings: List of aggregated findings
            
        Returns:
            str: Simple text report
        """
        if not aggregated_findings:
            return "No linting issues found."
        
        lines = []
        lines.append(f"Found {len(aggregated_findings)} issue(s):")
        lines.append("")
        
        for i, finding in enumerate(aggregated_findings, 1):
            pf = finding.primary_finding
            lines.append(f"{i}. {pf.file_path}:{pf.line_number}:{pf.column_number}")
            lines.append(f"   {pf.severity.value.upper()}: {pf.message}")
            lines.append(f"   Rule: {pf.rule_id} ({pf.tool})")
            lines.append("")
        
        return "\n".join(lines) 