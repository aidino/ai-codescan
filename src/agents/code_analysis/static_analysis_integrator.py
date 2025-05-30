#!/usr/bin/env python3
"""
AI CodeScan - Static Analysis Integrator Agent

Agent tích hợp các công cụ static analysis như flake8, pylint, mypy.
Chạy analysis tools và parse kết quả thành structured findings.
"""

import subprocess
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from loguru import logger
from enum import Enum


class SeverityLevel(Enum):
    """Mức độ nghiêm trọng của finding."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingType(Enum):
    """Loại finding."""
    STYLE = "style"
    ERROR = "error"
    WARNING = "warning"
    CONVENTION = "convention"
    REFACTOR = "refactor"
    SECURITY = "security"
    PERFORMANCE = "performance"


@dataclass
class Finding:
    """Một finding từ static analysis."""
    file_path: str
    line_number: int
    column_number: int
    severity: SeverityLevel
    finding_type: FindingType
    rule_id: str
    message: str
    tool: str
    suggestion: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.file_path}:{self.line_number}:{self.column_number} [{self.severity.value}] {self.rule_id}: {self.message}"


@dataclass
class AnalysisResult:
    """Kết quả phân tích static analysis."""
    tool: str
    project_path: str
    total_files_analyzed: int
    total_findings: int
    findings: List[Finding]
    execution_time_seconds: float
    success: bool
    error_message: Optional[str] = None
    command_executed: Optional[str] = None
    raw_output: Optional[str] = None


class StaticAnalysisIntegratorAgent:
    """
    Agent tích hợp static analysis tools.
    
    Trách nhiệm:
    - Chạy flake8, pylint, mypy trên Python projects
    - Parse output thành structured findings
    - Chuẩn hóa severity levels và finding types
    - Aggregate results từ multiple tools
    """
    
    def __init__(self, tools_config: Optional[Dict[str, Any]] = None):
        """
        Khởi tạo StaticAnalysisIntegratorAgent.
        
        Args:
            tools_config: Cấu hình cho các tools
        """
        self.tools_config = tools_config or self._get_default_config()
        self.supported_tools = ["flake8", "pylint", "mypy"]
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Lấy cấu hình mặc định cho tools."""
        return {
            "flake8": {
                "enabled": True,
                "max_line_length": 88,
                "ignore": ["E203", "W503"],  # Compatible với black
                "exclude": ["__pycache__", "*.pyc", ".git", ".tox", "venv", "env"]
            },
            "pylint": {
                "enabled": True,
                "disable": ["C0114", "C0115", "C0116"],  # Missing docstring warnings
                "max_line_length": 88
            },
            "mypy": {
                "enabled": True,
                "ignore_missing_imports": True,
                "strict": False
            }
        }
    
    def run_analysis(self, project_path: str, tools: Optional[List[str]] = None) -> Dict[str, AnalysisResult]:
        """
        Chạy static analysis trên project.
        
        Args:
            project_path: Đường dẫn đến project
            tools: Danh sách tools cần chạy (default: all enabled)
            
        Returns:
            Dict[str, AnalysisResult]: Kết quả từ mỗi tool
        """
        if not os.path.exists(project_path):
            logger.error(f"Project path không tồn tại: {project_path}")
            return {}
        
        # Determine tools to run
        if tools is None:
            tools = [tool for tool in self.supported_tools 
                    if self.tools_config.get(tool, {}).get("enabled", False)]
        
        logger.info(f"Chạy static analysis trên {project_path} với tools: {tools}")
        
        results = {}
        for tool in tools:
            if tool in self.supported_tools:
                logger.info(f"Chạy {tool}...")
                result = self._run_tool(tool, project_path)
                results[tool] = result
            else:
                logger.warning(f"Tool không được hỗ trợ: {tool}")
        
        return results
    
    def _run_tool(self, tool: str, project_path: str) -> AnalysisResult:
        """
        Chạy một tool cụ thể.
        
        Args:
            tool: Tên tool
            project_path: Đường dẫn project
            
        Returns:
            AnalysisResult: Kết quả analysis
        """
        if tool == "flake8":
            return self.run_flake8(project_path)
        elif tool == "pylint":
            return self.run_pylint(project_path)
        elif tool == "mypy":
            return self.run_mypy(project_path)
        else:
            return AnalysisResult(
                tool=tool,
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=0,
                success=False,
                error_message=f"Tool không được hỗ trợ: {tool}"
            )
    
    def run_flake8(self, project_path: str) -> AnalysisResult:
        """
        Chạy flake8 trên project.
        
        Args:
            project_path: Đường dẫn đến project
            
        Returns:
            AnalysisResult: Kết quả flake8 analysis
        """
        import time
        start_time = time.time()
        
        # Build flake8 command
        config = self.tools_config.get("flake8", {})
        cmd = ["flake8", project_path]
        
        # Add configuration options
        if "max_line_length" in config:
            cmd.extend(["--max-line-length", str(config["max_line_length"])])
        
        if "ignore" in config and config["ignore"]:
            cmd.extend(["--ignore", ",".join(config["ignore"])])
        
        if "exclude" in config and config["exclude"]:
            cmd.extend(["--exclude", ",".join(config["exclude"])])
        
        # Add format for easier parsing
        cmd.extend(["--format", "%(path)s:%(row)d:%(col)d: %(code)s %(text)s"])
        
        try:
            logger.debug(f"Chạy command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            execution_time = time.time() - start_time
            raw_output = result.stdout
            
            # Parse flake8 output
            findings = self.parse_flake8_output(raw_output, project_path)
            
            # Count analyzed files
            analyzed_files = self._count_python_files(project_path)
            
            return AnalysisResult(
                tool="flake8",
                project_path=project_path,
                total_files_analyzed=analyzed_files,
                total_findings=len(findings),
                findings=findings,
                execution_time_seconds=execution_time,
                success=True,
                command_executed=" ".join(cmd),
                raw_output=raw_output
            )
            
        except subprocess.TimeoutExpired:
            logger.error("Flake8 timeout")
            return AnalysisResult(
                tool="flake8",
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message="Flake8 execution timeout",
                command_executed=" ".join(cmd)
            )
            
        except FileNotFoundError:
            logger.error("Flake8 không được cài đặt")
            return AnalysisResult(
                tool="flake8",
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message="Flake8 không được cài đặt. Cài đặt với: pip install flake8",
                command_executed=" ".join(cmd)
            )
            
        except Exception as e:
            logger.error(f"Lỗi chạy flake8: {str(e)}")
            return AnalysisResult(
                tool="flake8",
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message=str(e),
                command_executed=" ".join(cmd)
            )
    
    def parse_flake8_output(self, output_str: str, project_path: str) -> List[Finding]:
        """
        Parse flake8 output thành danh sách Finding objects.
        
        Args:
            output_str: Raw output từ flake8
            project_path: Base project path
            
        Returns:
            List[Finding]: Danh sách findings
        """
        findings = []
        
        if not output_str.strip():
            return findings
        
        # Pattern cho flake8 output: path:line:col: code message
        pattern = r'^(.+?):(\d+):(\d+):\s*([A-Z]\d+)\s*(.+)$'
        
        for line in output_str.strip().split('\n'):
            if not line.strip():
                continue
                
            match = re.match(pattern, line.strip())
            if match:
                file_path, line_num, col_num, rule_id, message = match.groups()
                
                # Convert to relative path if possible
                try:
                    rel_path = os.path.relpath(file_path, project_path)
                    if not rel_path.startswith('..'):
                        file_path = rel_path
                except ValueError:
                    pass  # Keep absolute path if relpath fails
                
                # Determine severity và type từ rule_id
                severity, finding_type = self._classify_flake8_rule(rule_id)
                
                finding = Finding(
                    file_path=file_path,
                    line_number=int(line_num),
                    column_number=int(col_num),
                    severity=severity,
                    finding_type=finding_type,
                    rule_id=rule_id,
                    message=message.strip(),
                    tool="flake8"
                )
                
                findings.append(finding)
            else:
                logger.debug(f"Không parse được line: {line}")
        
        return findings
    
    def _classify_flake8_rule(self, rule_id: str) -> Tuple[SeverityLevel, FindingType]:
        """
        Phân loại flake8 rule thành severity và type.
        
        Args:
            rule_id: Rule ID (ví dụ: E501, W503)
            
        Returns:
            Tuple[SeverityLevel, FindingType]: Severity và type
        """
        # E: Error (PEP 8 violations)
        # W: Warning (PEP 8 violations)  
        # F: PyFlakes (logical errors)
        # C: McCabe complexity
        # N: PEP 8 naming conventions
        
        if rule_id.startswith('F'):
            # PyFlakes - logical errors
            return SeverityLevel.HIGH, FindingType.ERROR
        elif rule_id.startswith('E'):
            # PEP 8 errors
            if rule_id in ['E999']:  # Syntax errors
                return SeverityLevel.CRITICAL, FindingType.ERROR
            elif rule_id.startswith('E9'):  # Runtime errors
                return SeverityLevel.HIGH, FindingType.ERROR
            else:
                return SeverityLevel.MEDIUM, FindingType.STYLE
        elif rule_id.startswith('W'):
            # PEP 8 warnings
            return SeverityLevel.LOW, FindingType.WARNING
        elif rule_id.startswith('C'):
            # McCabe complexity
            return SeverityLevel.MEDIUM, FindingType.REFACTOR
        elif rule_id.startswith('N'):
            # Naming conventions
            return SeverityLevel.LOW, FindingType.CONVENTION
        else:
            # Default
            return SeverityLevel.MEDIUM, FindingType.WARNING
    
    def run_pylint(self, project_path: str) -> AnalysisResult:
        """
        Chạy pylint trên project.
        
        Args:
            project_path: Đường dẫn đến project
            
        Returns:
            AnalysisResult: Kết quả pylint analysis
        """
        import time
        start_time = time.time()
        
        # Build pylint command
        config = self.tools_config.get("pylint", {})
        cmd = ["pylint", project_path]
        
        # Add configuration options
        if "disable" in config and config["disable"]:
            cmd.extend(["--disable", ",".join(config["disable"])])
        
        if "max_line_length" in config:
            cmd.extend(["--max-line-length", str(config["max_line_length"])])
        
        # Output format for easier parsing
        cmd.extend(["--output-format", "parseable"])
        
        # Don't fail on warnings/errors
        cmd.append("--exit-zero")
        
        try:
            logger.debug(f"Chạy command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout (pylint slower than flake8)
            )
            
            execution_time = time.time() - start_time
            raw_output = result.stdout
            
            # Parse pylint output
            findings = self.parse_pylint_output(raw_output, project_path)
            
            # Count analyzed files
            analyzed_files = self._count_python_files(project_path)
            
            return AnalysisResult(
                tool="pylint",
                project_path=project_path,
                total_files_analyzed=analyzed_files,
                total_findings=len(findings),
                findings=findings,
                execution_time_seconds=execution_time,
                success=True,
                command_executed=" ".join(cmd),
                raw_output=raw_output
            )
            
        except subprocess.TimeoutExpired:
            logger.error("Pylint timeout")
            return AnalysisResult(
                tool="pylint",
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message="Pylint execution timeout",
                command_executed=" ".join(cmd)
            )
            
        except FileNotFoundError:
            logger.error("Pylint không được cài đặt")
            return AnalysisResult(
                tool="pylint",
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message="Pylint không được cài đặt. Cài đặt với: pip install pylint",
                command_executed=" ".join(cmd)
            )
            
        except Exception as e:
            logger.error(f"Lỗi chạy pylint: {str(e)}")
            return AnalysisResult(
                tool="pylint",
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message=str(e),
                command_executed=" ".join(cmd)
            )
    
    def parse_pylint_output(self, output_str: str, project_path: str) -> List[Finding]:
        """
        Parse pylint output thành danh sách Finding objects.
        
        Args:
            output_str: Raw output từ pylint
            project_path: Base project path
            
        Returns:
            List[Finding]: Danh sách findings
        """
        findings = []
        
        if not output_str.strip():
            return findings
        
        # Pattern cho pylint parseable output: path:line:column: message-type: message (rule-id)
        pattern = r'^(.+?):(\d+):(\d+):\s*([A-Z]\d+):\s*(.+?)\s*\(([^)]+)\)$'
        
        for line in output_str.strip().split('\n'):
            if not line.strip():
                continue
                
            # Skip non-message lines
            if not ':' in line or 'rated at' in line.lower():
                continue
                
            match = re.match(pattern, line.strip())
            if match:
                file_path, line_num, col_num, msg_type, message, rule_id = match.groups()
                
                # Convert to relative path
                try:
                    rel_path = os.path.relpath(file_path, project_path)
                    if not rel_path.startswith('..'):
                        file_path = rel_path
                except ValueError:
                    pass
                
                # Classify pylint message
                severity, finding_type = self._classify_pylint_message(msg_type, rule_id)
                
                finding = Finding(
                    file_path=file_path,
                    line_number=int(line_num),
                    column_number=int(col_num),
                    severity=severity,
                    finding_type=finding_type,
                    rule_id=rule_id,
                    message=message.strip(),
                    tool="pylint"
                )
                
                findings.append(finding)
        
        return findings
    
    def _classify_pylint_message(self, msg_type: str, rule_id: str) -> Tuple[SeverityLevel, FindingType]:
        """
        Phân loại pylint message.
        
        Args:
            msg_type: Message type (C, R, W, E, F)
            rule_id: Rule ID
            
        Returns:
            Tuple[SeverityLevel, FindingType]: Severity và type
        """
        # C: Convention (coding standard violation)
        # R: Refactor (design issue)
        # W: Warning (potential issue)
        # E: Error (likely bug)
        # F: Fatal (error prevented further processing)
        
        if msg_type.startswith('F'):
            return SeverityLevel.CRITICAL, FindingType.ERROR
        elif msg_type.startswith('E'):
            return SeverityLevel.HIGH, FindingType.ERROR
        elif msg_type.startswith('W'):
            return SeverityLevel.MEDIUM, FindingType.WARNING
        elif msg_type.startswith('R'):
            return SeverityLevel.MEDIUM, FindingType.REFACTOR
        elif msg_type.startswith('C'):
            return SeverityLevel.LOW, FindingType.CONVENTION
        else:
            return SeverityLevel.MEDIUM, FindingType.WARNING
    
    def run_mypy(self, project_path: str) -> AnalysisResult:
        """
        Chạy mypy trên project.
        
        Args:
            project_path: Đường dẫn đến project
            
        Returns:
            AnalysisResult: Kết quả mypy analysis
        """
        import time
        start_time = time.time()
        
        # Build mypy command
        config = self.tools_config.get("mypy", {})
        cmd = ["mypy", project_path]
        
        # Add configuration options
        if config.get("ignore_missing_imports", False):
            cmd.append("--ignore-missing-imports")
        
        if config.get("strict", False):
            cmd.append("--strict")
        
        # Show error context
        cmd.append("--show-error-context")
        
        try:
            logger.debug(f"Chạy command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            execution_time = time.time() - start_time
            raw_output = result.stdout + result.stderr  # mypy uses stderr
            
            # Parse mypy output
            findings = self.parse_mypy_output(raw_output, project_path)
            
            # Count analyzed files
            analyzed_files = self._count_python_files(project_path)
            
            return AnalysisResult(
                tool="mypy",
                project_path=project_path,
                total_files_analyzed=analyzed_files,
                total_findings=len(findings),
                findings=findings,
                execution_time_seconds=execution_time,
                success=True,
                command_executed=" ".join(cmd),
                raw_output=raw_output
            )
            
        except subprocess.TimeoutExpired:
            logger.error("MyPy timeout")
            return AnalysisResult(
                tool="mypy",
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message="MyPy execution timeout",
                command_executed=" ".join(cmd)
            )
            
        except FileNotFoundError:
            logger.error("MyPy không được cài đặt")
            return AnalysisResult(
                tool="mypy",
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message="MyPy không được cài đặt. Cài đặt với: pip install mypy",
                command_executed=" ".join(cmd)
            )
            
        except Exception as e:
            logger.error(f"Lỗi chạy mypy: {str(e)}")
            return AnalysisResult(
                tool="mypy",
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message=str(e),
                command_executed=" ".join(cmd)
            )
    
    def parse_mypy_output(self, output_str: str, project_path: str) -> List[Finding]:
        """
        Parse mypy output thành danh sách Finding objects.
        
        Args:
            output_str: Raw output từ mypy
            project_path: Base project path
            
        Returns:
            List[Finding]: Danh sách findings
        """
        findings = []
        
        if not output_str.strip():
            return findings
        
        # Pattern cho mypy output: path:line: error/note: message
        pattern = r'^(.+?):(\d+):\s*(error|warning|note):\s*(.+)$'
        
        for line in output_str.strip().split('\n'):
            if not line.strip():
                continue
                
            # Skip success messages
            if 'success' in line.lower() or 'found' in line.lower():
                continue
                
            match = re.match(pattern, line.strip())
            if match:
                file_path, line_num, msg_type, message = match.groups()
                
                # Convert to relative path
                try:
                    rel_path = os.path.relpath(file_path, project_path)
                    if not rel_path.startswith('..'):
                        file_path = rel_path
                except ValueError:
                    pass
                
                # Classify mypy message
                severity, finding_type = self._classify_mypy_message(msg_type)
                
                finding = Finding(
                    file_path=file_path,
                    line_number=int(line_num),
                    column_number=0,  # MyPy không cung cấp column
                    severity=severity,
                    finding_type=finding_type,
                    rule_id="mypy",
                    message=message.strip(),
                    tool="mypy"
                )
                
                findings.append(finding)
        
        return findings
    
    def _classify_mypy_message(self, msg_type: str) -> Tuple[SeverityLevel, FindingType]:
        """
        Phân loại mypy message.
        
        Args:
            msg_type: Message type (error, warning, note)
            
        Returns:
            Tuple[SeverityLevel, FindingType]: Severity và type
        """
        if msg_type == "error":
            return SeverityLevel.HIGH, FindingType.ERROR
        elif msg_type == "warning":
            return SeverityLevel.MEDIUM, FindingType.WARNING
        elif msg_type == "note":
            return SeverityLevel.LOW, FindingType.WARNING
        else:
            return SeverityLevel.MEDIUM, FindingType.WARNING
    
    def _count_python_files(self, project_path: str) -> int:
        """
        Đếm số file Python trong project.
        
        Args:
            project_path: Đường dẫn project
            
        Returns:
            int: Số file Python
        """
        try:
            count = 0
            for root, dirs, files in os.walk(project_path):
                # Skip common excluded directories
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.tox', 'venv', 'env', '.venv']]
                
                for file in files:
                    if file.endswith('.py'):
                        count += 1
            
            return count
        except Exception as e:
            logger.warning(f"Lỗi đếm Python files: {str(e)}")
            return 0
    
    def aggregate_results(self, results: Dict[str, AnalysisResult]) -> Dict[str, Any]:
        """
        Tổng hợp kết quả từ multiple tools.
        
        Args:
            results: Dict tool -> AnalysisResult
            
        Returns:
            Dict[str, Any]: Aggregated statistics
        """
        total_findings = 0
        total_files = 0
        total_execution_time = 0
        successful_tools = []
        failed_tools = []
        
        severity_counts = {
            SeverityLevel.LOW: 0,
            SeverityLevel.MEDIUM: 0,
            SeverityLevel.HIGH: 0,
            SeverityLevel.CRITICAL: 0
        }
        
        type_counts = {
            FindingType.STYLE: 0,
            FindingType.ERROR: 0,
            FindingType.WARNING: 0,
            FindingType.CONVENTION: 0,
            FindingType.REFACTOR: 0,
            FindingType.SECURITY: 0,
            FindingType.PERFORMANCE: 0
        }
        
        all_findings = []
        
        for tool, result in results.items():
            total_execution_time += result.execution_time_seconds
            
            if result.success:
                successful_tools.append(tool)
                total_findings += result.total_findings
                total_files = max(total_files, result.total_files_analyzed)
                
                # Count by severity and type
                for finding in result.findings:
                    severity_counts[finding.severity] += 1
                    type_counts[finding.finding_type] += 1
                    all_findings.append(finding)
            else:
                failed_tools.append(tool)
        
        return {
            "summary": {
                "total_findings": total_findings,
                "total_files_analyzed": total_files,
                "total_execution_time_seconds": total_execution_time,
                "successful_tools": successful_tools,
                "failed_tools": failed_tools
            },
            "severity_breakdown": {level.value: count for level, count in severity_counts.items()},
            "type_breakdown": {ftype.value: count for ftype, count in type_counts.items()},
            "all_findings": all_findings,
            "tool_results": results
        } 