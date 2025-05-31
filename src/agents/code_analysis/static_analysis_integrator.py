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
        self.supported_tools = ["flake8", "pylint", "mypy", "checkstyle", "pmd", "dart_analyze", "detekt"]
        
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
            },
            "checkstyle": {
                "enabled": True,
                "config_file": None,  # Use default Google style if None
                "jar_path": None,  # Auto-download if None
                "version": "10.12.4",
                "exclude_patterns": ["**/target/**", "**/build/**", "**/.git/**"]
            },
            "pmd": {
                "enabled": True,
                "rulesets": ["java-basic", "java-design", "java-codestyle"],
                "jar_path": None,  # Auto-download if None
                "version": "7.0.0",
                "exclude_patterns": ["**/target/**", "**/build/**", "**/.git/**"]
            },
            "dart_analyze": {
                "enabled": True,
                "fatal_infos": False,
                "fatal_warnings": False,
                "exclude_patterns": ["**/.dart_tool/**", "**/build/**", "**/.git/**"],
                "exclude_files": [],
                "include_transitive_dependencies": False
            },
            "detekt": {
                "enabled": True,
                "config_file": None,  # Use default config if None
                "jar_path": None,  # Auto-download if None
                "version": "1.23.4",
                "build_upon_default_config": True,
                "exclude_patterns": ["**/build/**", "**/.git/**", "**/src/test/**"],
                "baseline": None,
                "create_baseline": False,
                "fail_fast": False,
                "auto_correct": False
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
        elif tool == "checkstyle":
            return self.run_checkstyle(project_path)
        elif tool == "pmd":
            return self.run_pmd(project_path)
        elif tool == "dart_analyze":
            return self.run_dart_analyze(project_path)
        elif tool == "detekt":
            return self.run_detekt(project_path)
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
        
    # ===== JAVA STATIC ANALYSIS METHODS =====
    
    def run_checkstyle(self, project_path: str) -> AnalysisResult:
        """
        Chạy Checkstyle trên Java project.
        
        Args:
            project_path: Đường dẫn đến project
            
        Returns:
            AnalysisResult: Kết quả Checkstyle analysis
        """
        import time
        start_time = time.time()
        
        # Check if there are Java files
        java_files_count = self._count_java_files(project_path)
        if java_files_count == 0:
            logger.warning(f"Không tìm thấy file Java trong {project_path}")
            return AnalysisResult(
                tool="checkstyle",
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=True,
                error_message="Không có file Java để analyze"
            )
        
        # Get Checkstyle JAR path
        config = self.tools_config.get("checkstyle", {})
        jar_path = self._get_checkstyle_jar(config)
        
        if not jar_path:
            return AnalysisResult(
                tool="checkstyle",
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message="Không thể download hoặc tìm thấy Checkstyle JAR"
            )
        
        # Build Checkstyle command
        cmd = ["java", "-jar", jar_path]
        
        # Add configuration
        config_file = config.get("config_file")
        if config_file and os.path.exists(config_file):
            cmd.extend(["-c", config_file])
        else:
            # Use Google style as default
            cmd.extend(["-c", "google_checks.xml"])
        
        # Output format
        cmd.extend(["-f", "xml"])
        
        # Add project path
        cmd.append(project_path)
        
        try:
            logger.info(f"Chạy Checkstyle command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=project_path
            )
            
            execution_time = time.time() - start_time
            
            # Parse findings
            findings = self.parse_checkstyle_output(result.stdout, project_path)
            
            return AnalysisResult(
                tool="checkstyle",
                project_path=project_path,
                total_files_analyzed=java_files_count,
                total_findings=len(findings),
                findings=findings,
                execution_time_seconds=execution_time,
                success=True,
                command_executed=" ".join(cmd),
                raw_output=result.stdout
            )
            
        except subprocess.TimeoutExpired:
            logger.error("Checkstyle execution timeout")
            return AnalysisResult(
                tool="checkstyle",
                project_path=project_path,
                total_files_analyzed=java_files_count,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message="Checkstyle execution timeout",
                command_executed=" ".join(cmd)
            )
            
        except FileNotFoundError:
            logger.error("Java không được cài đặt hoặc không có trong PATH")
            return AnalysisResult(
                tool="checkstyle",
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message="Java không được cài đặt hoặc không có trong PATH",
                command_executed=" ".join(cmd)
            )
            
        except Exception as e:
            logger.error(f"Lỗi chạy Checkstyle: {str(e)}")
            return AnalysisResult(
                tool="checkstyle",
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message=str(e),
                command_executed=" ".join(cmd)
            )
    
    def parse_checkstyle_output(self, output_str: str, project_path: str) -> List[Finding]:
        """
        Parse Checkstyle XML output thành danh sách Finding objects.
        
        Args:
            output_str: Raw XML output từ Checkstyle
            project_path: Base project path
            
        Returns:
            List[Finding]: Danh sách findings
        """
        findings = []
        
        if not output_str.strip():
            return findings
        
        try:
            import xml.etree.ElementTree as ET
            
            # Parse XML
            root = ET.fromstring(output_str)
            
            # Process each file
            for file_elem in root.findall('file'):
                file_path = file_elem.get('name', '')
                
                # Convert to relative path
                try:
                    rel_path = os.path.relpath(file_path, project_path)
                    if not rel_path.startswith('..'):
                        file_path = rel_path
                except ValueError:
                    pass
                
                # Process errors in this file
                for error_elem in file_elem.findall('error'):
                    line_num = int(error_elem.get('line', '0'))
                    column_num = int(error_elem.get('column', '0'))
                    severity = error_elem.get('severity', 'warning')
                    source = error_elem.get('source', '')
                    message = error_elem.get('message', '')
                    
                    # Extract rule name from source
                    rule_id = source.split('.')[-1] if '.' in source else source
                    
                    # Classify finding
                    severity_level, finding_type = self._classify_checkstyle_finding(severity, rule_id)
                    
                    finding = Finding(
                        file_path=file_path,
                        line_number=line_num,
                        column_number=column_num,
                        severity=severity_level,
                        finding_type=finding_type,
                        rule_id=rule_id,
                        message=message,
                        tool="checkstyle"
                    )
                    
                    findings.append(finding)
        
        except Exception as e:
            logger.error(f"Lỗi parse Checkstyle output: {str(e)}")
            # Try to parse as text format fallback
            return self._parse_checkstyle_text_fallback(output_str, project_path)
        
        return findings
    
    def _parse_checkstyle_text_fallback(self, output_str: str, project_path: str) -> List[Finding]:
        """
        Fallback parser cho Checkstyle text output.
        
        Args:
            output_str: Raw text output
            project_path: Base project path
            
        Returns:
            List[Finding]: Danh sách findings
        """
        findings = []
        
        # Pattern cho text output: [WARN] path:line:column: message
        pattern = r'\[(WARN|ERROR|INFO)\]\s+([^:]+):(\d+):(\d+):\s*(.+)'
        
        for line in output_str.strip().split('\n'):
            if not line.strip():
                continue
            
            match = re.match(pattern, line.strip())
            if match:
                severity, file_path, line_num, column_num, message = match.groups()
                
                # Convert to relative path
                try:
                    rel_path = os.path.relpath(file_path, project_path)
                    if not rel_path.startswith('..'):
                        file_path = rel_path
                except ValueError:
                    pass
                
                # Classify finding
                severity_level = SeverityLevel.MEDIUM
                if severity == "ERROR":
                    severity_level = SeverityLevel.HIGH
                elif severity == "WARN":
                    severity_level = SeverityLevel.MEDIUM
                elif severity == "INFO":
                    severity_level = SeverityLevel.LOW
                
                finding = Finding(
                    file_path=file_path,
                    line_number=int(line_num),
                    column_number=int(column_num),
                    severity=severity_level,
                    finding_type=FindingType.STYLE,
                    rule_id="checkstyle",
                    message=message.strip(),
                    tool="checkstyle"
                )
                
                findings.append(finding)
        
        return findings
    
    def _classify_checkstyle_finding(self, severity: str, rule_id: str) -> Tuple[SeverityLevel, FindingType]:
        """
        Phân loại Checkstyle finding.
        
        Args:
            severity: Severity từ Checkstyle (error, warning, info)
            rule_id: Rule ID
            
        Returns:
            Tuple[SeverityLevel, FindingType]: Severity và type
        """
        # Map severity
        if severity.lower() == "error":
            severity_level = SeverityLevel.HIGH
        elif severity.lower() == "warning":
            severity_level = SeverityLevel.MEDIUM
        elif severity.lower() == "info":
            severity_level = SeverityLevel.LOW
        else:
            severity_level = SeverityLevel.MEDIUM
        
        # Map finding type based on rule
        rule_lower = rule_id.lower()
        
        if any(keyword in rule_lower for keyword in ['security', 'vulnerability']):
            finding_type = FindingType.SECURITY
        elif any(keyword in rule_lower for keyword in ['performance', 'efficiency']):
            finding_type = FindingType.PERFORMANCE
        elif any(keyword in rule_lower for keyword in ['style', 'format', 'indent', 'whitespace']):
            finding_type = FindingType.STYLE
        elif any(keyword in rule_lower for keyword in ['design', 'complexity', 'coupling']):
            finding_type = FindingType.REFACTOR
        elif any(keyword in rule_lower for keyword in ['convention', 'naming']):
            finding_type = FindingType.CONVENTION
        else:
            finding_type = FindingType.WARNING
        
        return severity_level, finding_type
    
    def run_pmd(self, project_path: str) -> AnalysisResult:
        """
        Chạy PMD trên Java project.
        
        Args:
            project_path: Đường dẫn đến project
            
        Returns:
            AnalysisResult: Kết quả PMD analysis
        """
        import time
        start_time = time.time()
        
        # Check if there are Java files
        java_files_count = self._count_java_files(project_path)
        if java_files_count == 0:
            logger.warning(f"Không tìm thấy file Java trong {project_path}")
            return AnalysisResult(
                tool="pmd",
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=True,
                error_message="Không có file Java để analyze"
            )
        
        # Get PMD JAR path
        config = self.tools_config.get("pmd", {})
        jar_path = self._get_pmd_jar(config)
        
        if not jar_path:
            return AnalysisResult(
                tool="pmd",
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message="Không thể download hoặc tìm thấy PMD JAR"
            )
        
        # Build PMD command
        cmd = ["java", "-jar", jar_path, "check"]
        
        # Add source directory
        cmd.extend(["-d", project_path])
        
        # Add rulesets
        rulesets = config.get("rulesets", ["java-basic"])
        ruleset_arg = ",".join([f"category/java/{rs}.xml" for rs in rulesets])
        cmd.extend(["-R", ruleset_arg])
        
        # Output format
        cmd.extend(["-f", "xml"])
        
        try:
            logger.info(f"Chạy PMD command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                cwd=project_path
            )
            
            execution_time = time.time() - start_time
            
            # Parse findings
            findings = self.parse_pmd_output(result.stdout, project_path)
            
            return AnalysisResult(
                tool="pmd",
                project_path=project_path,
                total_files_analyzed=java_files_count,
                total_findings=len(findings),
                findings=findings,
                execution_time_seconds=execution_time,
                success=True,
                command_executed=" ".join(cmd),
                raw_output=result.stdout
            )
            
        except subprocess.TimeoutExpired:
            logger.error("PMD execution timeout")
            return AnalysisResult(
                tool="pmd",
                project_path=project_path,
                total_files_analyzed=java_files_count,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message="PMD execution timeout",
                command_executed=" ".join(cmd)
            )
            
        except FileNotFoundError:
            logger.error("Java không được cài đặt hoặc không có trong PATH")
            return AnalysisResult(
                tool="pmd",
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message="Java không được cài đặt hoặc không có trong PATH",
                command_executed=" ".join(cmd)
            )
            
        except Exception as e:
            logger.error(f"Lỗi chạy PMD: {str(e)}")
            return AnalysisResult(
                tool="pmd",
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message=str(e),
                command_executed=" ".join(cmd)
            )
    
    def parse_pmd_output(self, output_str: str, project_path: str) -> List[Finding]:
        """
        Parse PMD XML output thành danh sách Finding objects.
        
        Args:
            output_str: Raw XML output từ PMD
            project_path: Base project path
            
        Returns:
            List[Finding]: Danh sách findings
        """
        findings = []
        
        if not output_str.strip():
            return findings
        
        try:
            import xml.etree.ElementTree as ET
            
            # Parse XML
            root = ET.fromstring(output_str)
            
            # PMD uses namespace, so we need to use full namespace xpath
            namespace = "http://pmd.sourceforge.net/report/2.0.0"
            
            # Process each file using full namespace xpath
            for file_elem in root.findall(f'.//{{{namespace}}}file'):
                file_path = file_elem.get('name', '')
                
                # Convert to relative path
                try:
                    rel_path = os.path.relpath(file_path, project_path)
                    if not rel_path.startswith('..'):
                        file_path = rel_path
                except ValueError:
                    pass
                
                # Process violations in this file using full namespace xpath
                for violation_elem in file_elem.findall(f'.//{{{namespace}}}violation'):
                    begin_line = int(violation_elem.get('beginline', '0'))
                    begin_column = int(violation_elem.get('begincolumn', '0'))
                    priority = int(violation_elem.get('priority', '3'))
                    rule = violation_elem.get('rule', '')
                    ruleset = violation_elem.get('ruleset', '')
                    message = violation_elem.text or ''
                    
                    # Map priority to severity
                    if priority == 1:
                        severity_level = SeverityLevel.CRITICAL
                    elif priority == 2:
                        severity_level = SeverityLevel.HIGH
                    elif priority == 3:
                        severity_level = SeverityLevel.MEDIUM
                    else:
                        severity_level = SeverityLevel.LOW
                    
                    # Classify finding type based on ruleset and rule
                    finding_type = self._classify_pmd_finding(ruleset, rule)
                    
                    finding = Finding(
                        file_path=file_path,
                        line_number=begin_line,
                        column_number=begin_column,
                        severity=severity_level,
                        finding_type=finding_type,
                        rule_id=f"{ruleset}/{rule}",
                        message=message.strip(),
                        tool="pmd"
                    )
                    
                    findings.append(finding)
        
        except Exception as e:
            logger.error(f"Lỗi parse PMD output: {str(e)}")
            # Try text fallback
            return self._parse_pmd_text_fallback(output_str, project_path)
        
        return findings
    
    def _parse_pmd_text_fallback(self, output_str: str, project_path: str) -> List[Finding]:
        """
        Fallback parser cho PMD text output.
        
        Args:
            output_str: Raw text output
            project_path: Base project path
            
        Returns:
            List[Finding]: Danh sách findings
        """
        findings = []
        
        # Pattern cho text output: path:line:column: rule: message
        pattern = r'^([^:]+):(\d+):(\d+):\s*([^:]+):\s*(.+)$'
        
        for line in output_str.strip().split('\n'):
            if not line.strip():
                continue
            
            match = re.match(pattern, line.strip())
            if match:
                file_path, line_num, column_num, rule, message = match.groups()
                
                # Convert to relative path
                try:
                    rel_path = os.path.relpath(file_path, project_path)
                    if not rel_path.startswith('..'):
                        file_path = rel_path
                except ValueError:
                    pass
                
                finding = Finding(
                    file_path=file_path,
                    line_number=int(line_num),
                    column_number=int(column_num),
                    severity=SeverityLevel.MEDIUM,
                    finding_type=FindingType.WARNING,
                    rule_id=rule.strip(),
                    message=message.strip(),
                    tool="pmd"
                )
                
                findings.append(finding)
        
        return findings
    
    def _classify_pmd_finding(self, ruleset: str, rule: str) -> FindingType:
        """
        Phân loại PMD finding dựa trên ruleset và rule.
        
        Args:
            ruleset: PMD ruleset
            rule: PMD rule name
            
        Returns:
            FindingType: Loại finding
        """
        ruleset_lower = ruleset.lower()
        rule_lower = rule.lower()
        
        if 'security' in ruleset_lower or 'security' in rule_lower:
            return FindingType.SECURITY
        elif 'performance' in ruleset_lower or 'performance' in rule_lower:
            return FindingType.PERFORMANCE
        elif 'design' in ruleset_lower or any(keyword in rule_lower for keyword in ['complexity', 'coupling', 'cohesion']):
            return FindingType.REFACTOR
        elif 'codestyle' in ruleset_lower or any(keyword in rule_lower for keyword in ['naming', 'format', 'style']):
            return FindingType.STYLE
        elif 'errorprone' in ruleset_lower or 'error' in rule_lower:
            return FindingType.ERROR
        else:
            return FindingType.WARNING
    
    def _count_java_files(self, project_path: str) -> int:
        """
        Đếm số file Java trong project.
        
        Args:
            project_path: Đường dẫn project
            
        Returns:
            int: Số file Java
        """
        try:
            count = 0
            for root, dirs, files in os.walk(project_path):
                # Skip common excluded directories
                dirs[:] = [d for d in dirs if d not in ['.git', 'target', 'build', '.gradle', '.mvn']]
                
                for file in files:
                    if file.endswith('.java'):
                        count += 1
            
            return count
        except Exception as e:
            logger.warning(f"Lỗi đếm Java files: {str(e)}")
            return 0
    
    def _get_checkstyle_jar(self, config: Dict[str, Any]) -> Optional[str]:
        """
        Lấy đường dẫn đến Checkstyle JAR file.
        
        Args:
            config: Checkstyle configuration
            
        Returns:
            Optional[str]: Đường dẫn JAR file hoặc None nếu không tìm thấy
        """
        jar_path = config.get("jar_path")
        if jar_path and os.path.exists(jar_path):
            return jar_path
        
        # Try to download JAR
        version = config.get("version", "10.12.4")
        return self._download_jar(
            "checkstyle",
            version,
            f"https://github.com/checkstyle/checkstyle/releases/download/checkstyle-{version}/checkstyle-{version}-all.jar"
        )
    
    def _get_pmd_jar(self, config: Dict[str, Any]) -> Optional[str]:
        """
        Lấy đường dẫn đến PMD JAR file.
        
        Args:
            config: PMD configuration
            
        Returns:
            Optional[str]: Đường dẫn JAR file hoặc None nếu không tìm thấy
        """
        jar_path = config.get("jar_path")
        if jar_path and os.path.exists(jar_path):
            return jar_path
        
        # Try to download JAR
        version = config.get("version", "7.0.0")
        return self._download_jar(
            "pmd",
            version,
            f"https://github.com/pmd/pmd/releases/download/pmd_releases%2F{version}/pmd-dist-{version}-bin.zip"
        )
    
    def _download_jar(self, tool: str, version: str, download_url: str) -> Optional[str]:
        """
        Download JAR file cho static analysis tools.
        
        Args:
            tool: Tool name (checkstyle, pmd)
            version: Tool version
            download_url: Download URL
            
        Returns:
            Optional[str]: Path to downloaded JAR or None if failed
        """
        try:
            import urllib.request
            import tempfile
            from pathlib import Path
            
            # Create cache directory
            cache_dir = Path.home() / ".ai_codescan" / "jars"
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            jar_filename = f"{tool}-{version}.jar"
            jar_path = cache_dir / jar_filename
            
            # Return if already exists
            if jar_path.exists():
                logger.info(f"Using cached {tool} JAR: {jar_path}")
                return str(jar_path)
            
            logger.info(f"Downloading {tool} v{version}...")
            
            # Download file
            if download_url.endswith('.zip'):
                # Handle ZIP files (like PMD)
                with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
                    urllib.request.urlretrieve(download_url, tmp_zip.name)
                    
                    # Extract JAR from ZIP
                    import zipfile
                    with zipfile.ZipFile(tmp_zip.name, 'r') as zip_ref:
                        # Find the main JAR file
                        jar_files = [f for f in zip_ref.namelist() if f.endswith('.jar') and 'pmd' in f.lower()]
                        if jar_files:
                            # Extract the first JAR file found
                            zip_ref.extract(jar_files[0], cache_dir)
                            extracted_path = cache_dir / jar_files[0]
                            # Rename to standard format
                            extracted_path.rename(jar_path)
                        else:
                            logger.error(f"No JAR file found in {tool} ZIP")
                            return None
                    
                    os.unlink(tmp_zip.name)
            else:
                # Direct JAR download
                urllib.request.urlretrieve(download_url, jar_path)
            
            logger.info(f"Downloaded {tool} JAR: {jar_path}")
            return str(jar_path)
            
        except Exception as e:
            logger.error(f"Failed to download {tool} JAR: {str(e)}")
            return None

    # === Dart Analysis Methods ===
    
    def run_dart_analyze(self, project_path: str) -> AnalysisResult:
        """
        Chạy dart analyze trên Dart project.
        
        Args:
            project_path: Đường dẫn đến Dart project
            
        Returns:
            AnalysisResult: Kết quả dart analyze analysis
        """
        import time
        start_time = time.time()
        
        # Check if it's a Dart project
        pubspec_path = os.path.join(project_path, "pubspec.yaml")
        if not os.path.exists(pubspec_path):
            logger.warning(f"Không tìm thấy pubspec.yaml trong {project_path}")
            return AnalysisResult(
                tool="dart_analyze",
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message="Không phải Dart project (thiếu pubspec.yaml)"
            )
        
        # Build dart analyze command
        config = self.tools_config.get("dart_analyze", {})
        cmd = ["dart", "analyze"]
        
        # Add configuration options
        if config.get("fatal_infos", False):
            cmd.append("--fatal-infos")
        
        if config.get("fatal_warnings", False):
            cmd.append("--fatal-warnings")
        
        # Add project path
        cmd.append(project_path)
        
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
            raw_output = result.stdout + result.stderr
            
            # Parse dart analyze output
            findings = self.parse_dart_analyze_output(raw_output, project_path)
            
            # Count analyzed files
            analyzed_files = self._count_dart_files(project_path)
            
            # Dart analyze returns 0 for success, non-zero for issues
            success = True  # We consider it successful if it ran, regardless of findings
            
            return AnalysisResult(
                tool="dart_analyze",
                project_path=project_path,
                total_files_analyzed=analyzed_files,
                total_findings=len(findings),
                findings=findings,
                execution_time_seconds=execution_time,
                success=success,
                command_executed=" ".join(cmd),
                raw_output=raw_output
            )
            
        except subprocess.TimeoutExpired:
            logger.error("Dart analyze timeout")
            return AnalysisResult(
                tool="dart_analyze",
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message="Dart analyze execution timeout",
                command_executed=" ".join(cmd)
            )
            
        except FileNotFoundError:
            logger.error("Dart SDK không được cài đặt")
            return AnalysisResult(
                tool="dart_analyze",
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message="Dart SDK không được cài đặt. Cài đặt Dart từ https://dart.dev/get-dart",
                command_executed=" ".join(cmd)
            )
            
        except Exception as e:
            logger.error(f"Lỗi chạy dart analyze: {str(e)}")
            return AnalysisResult(
                tool="dart_analyze",
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message=str(e),
                command_executed=" ".join(cmd)
            )
    
    def parse_dart_analyze_output(self, output_str: str, project_path: str) -> List[Finding]:
        """
        Parse dart analyze output thành danh sách Finding objects.
        
        Args:
            output_str: Raw output từ dart analyze
            project_path: Đường dẫn project
            
        Returns:
            List[Finding]: Danh sách findings được parse
        """
        findings = []
        
        if not output_str.strip():
            logger.info("Dart analyze output trống - không có findings")
            return findings
        
        lines = output_str.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip summary lines và header
            # Note: Chỉ skip lines mà là summary, không phải finding lines
            skip_patterns = [
                'analyzing', 'no issues found', 'issue found', 'issues found',
                'completed', 'summary:'
            ]
            
            # Check if this is a summary line (not a finding line)
            if any(skip in line.lower() for skip in skip_patterns):
                continue
            
            # Parse dart analyze output format:
            # file_path:line:column • message • rule_id
            # Example: lib/main.dart:10:5 • Prefer const with constant constructors • prefer_const_constructors
            pattern = r'^(.+?):(\d+):(\d+)\s*•\s*(.+?)\s*•\s*(.+)$'
            match = re.match(pattern, line)
            
            if match:
                file_path = match.group(1).strip()
                line_number = int(match.group(2))
                column_number = int(match.group(3))
                message = match.group(4).strip()
                rule_id = match.group(5).strip()
                
                # Make file path absolute
                if not os.path.isabs(file_path):
                    file_path = os.path.join(project_path, file_path)
                
                # Classify finding
                severity, finding_type = self._classify_dart_finding(rule_id, message)
                
                finding = Finding(
                    file_path=file_path,
                    line_number=line_number,
                    column_number=column_number,
                    severity=severity,
                    finding_type=finding_type,
                    rule_id=rule_id,
                    message=message,
                    tool="dart_analyze",
                    suggestion=self._get_dart_suggestion(rule_id)
                )
                
                findings.append(finding)
            else:
                # Alternative format parsing if standard format doesn't match
                # Try: file_path:line:column: severity: message
                alt_pattern = r'^(.+?):(\d+):(\d+):\s*(\w+):\s*(.+)$'
                alt_match = re.match(alt_pattern, line)
                
                if alt_match:
                    file_path = alt_match.group(1).strip()
                    line_number = int(alt_match.group(2))
                    column_number = int(alt_match.group(3))
                    severity_str = alt_match.group(4).strip().lower()
                    message = alt_match.group(5).strip()
                    
                    # Make file path absolute
                    if not os.path.isabs(file_path):
                        file_path = os.path.join(project_path, file_path)
                    
                    # Map severity
                    severity = self._map_dart_severity(severity_str)
                    finding_type = self._map_dart_type(severity_str)
                    
                    finding = Finding(
                        file_path=file_path,
                        line_number=line_number,
                        column_number=column_number,
                        severity=severity,
                        finding_type=finding_type,
                        rule_id="dart_" + severity_str,
                        message=message,
                        tool="dart_analyze"
                    )
                    
                    findings.append(finding)
        
        logger.info(f"Parsed {len(findings)} findings từ dart analyze output")
        return findings
    
    def _classify_dart_finding(self, rule_id: str, message: str) -> Tuple[SeverityLevel, FindingType]:
        """
        Phân loại Dart finding theo rule_id và message.
        
        Args:
            rule_id: Rule ID từ dart analyze
            message: Message text
            
        Returns:
            Tuple[SeverityLevel, FindingType]: Severity và type
        """
        # Dart analyzer rules mapping
        error_rules = [
            'undefined_', 'missing_', 'invalid_', 'duplicate_',
            'syntax_error', 'type_error', 'compile_time_error'
        ]
        
        warning_rules = [
            'unused_', 'dead_code', 'unreachable_code', 'deprecated_',
            'avoid_', 'prefer_not_', 'unnecessary_'
        ]
        
        style_rules = [
            'prefer_', 'use_', 'camel_case', 'snake_case', 'constant_identifier_names',
            'file_names', 'library_names', 'type_init_formals', 'sort_constructors_first'
        ]
        
        performance_rules = [
            'avoid_function_literals_in_foreach_calls', 'prefer_foreach',
            'avoid_slow_async_io', 'unnecessary_lambdas'
        ]
        
        # Check rule patterns
        rule_lower = rule_id.lower()
        
        # Errors (high severity)
        if any(pattern in rule_lower for pattern in error_rules):
            return SeverityLevel.HIGH, FindingType.ERROR
        
        # Performance issues
        if any(pattern in rule_lower for pattern in performance_rules):
            return SeverityLevel.MEDIUM, FindingType.PERFORMANCE
        
        # Warnings
        if any(pattern in rule_lower for pattern in warning_rules):
            return SeverityLevel.MEDIUM, FindingType.WARNING
        
        # Style issues (most Dart rules are style)
        if any(pattern in rule_lower for pattern in style_rules):
            return SeverityLevel.LOW, FindingType.STYLE
        
        # Check message content for additional clues
        message_lower = message.lower()
        if any(word in message_lower for word in ['error', 'failed', 'invalid']):
            return SeverityLevel.HIGH, FindingType.ERROR
        elif any(word in message_lower for word in ['warning', 'deprecated']):
            return SeverityLevel.MEDIUM, FindingType.WARNING
        elif any(word in message_lower for word in ['prefer', 'consider', 'style']):
            return SeverityLevel.LOW, FindingType.STYLE
        
        # Default: low severity style issue
        return SeverityLevel.LOW, FindingType.STYLE
    
    def _map_dart_severity(self, severity_str: str) -> SeverityLevel:
        """Map Dart severity string to SeverityLevel enum."""
        severity_map = {
            'error': SeverityLevel.HIGH,
            'warning': SeverityLevel.MEDIUM,
            'info': SeverityLevel.LOW,
            'hint': SeverityLevel.LOW
        }
        return severity_map.get(severity_str.lower(), SeverityLevel.LOW)
    
    def _map_dart_type(self, severity_str: str) -> FindingType:
        """Map Dart severity string to FindingType enum."""
        type_map = {
            'error': FindingType.ERROR,
            'warning': FindingType.WARNING,
            'info': FindingType.CONVENTION,
            'hint': FindingType.STYLE
        }
        return type_map.get(severity_str.lower(), FindingType.STYLE)
    
    def _get_dart_suggestion(self, rule_id: str) -> Optional[str]:
        """
        Lấy suggestion cho Dart rule.
        
        Args:
            rule_id: Dart rule ID
            
        Returns:
            Optional[str]: Suggestion text
        """
        suggestions = {
            'prefer_const_constructors': 'Sử dụng const constructors khi có thể để tối ưu performance',
            'prefer_final_fields': 'Khai báo fields là final nếu không cần thay đổi',
            'avoid_print': 'Sử dụng logging framework thay vì print() trong production code',
            'prefer_collection_literals': 'Sử dụng collection literals [] {} thay vì constructors',
            'unnecessary_new': 'Từ khóa "new" không cần thiết trong Dart 2+',
            'prefer_is_empty': 'Sử dụng .isEmpty thay vì .length == 0',
            'prefer_is_not_empty': 'Sử dụng .isNotEmpty thay vì .length != 0',
            'avoid_function_literals_in_foreach_calls': 'Sử dụng for-in loop thay vì forEach với function literals',
            'prefer_single_quotes': 'Sử dụng single quotes cho strings không chứa single quotes',
            'camel_case_types': 'Sử dụng UpperCamelCase cho type names',
            'constant_identifier_names': 'Sử dụng SCREAMING_SNAKE_CASE cho constants'
        }
        
        return suggestions.get(rule_id)
    
    def _count_dart_files(self, project_path: str) -> int:
        """
        Đếm số file .dart trong project.
        
        Args:
            project_path: Đường dẫn project
            
        Returns:
            int: Số file .dart
        """
        dart_files = 0
        
        for root, dirs, files in os.walk(project_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in ['.dart_tool', 'build', '.git', '.idea']]
            
            for file in files:
                if file.endswith('.dart'):
                    dart_files += 1
        
        return dart_files

    # === Kotlin Support với Detekt ===
    
    def run_detekt(self, project_path: str) -> AnalysisResult:
        """
        Chạy Detekt trên Kotlin project.
        
        Args:
            project_path: Đường dẫn đến project
            
        Returns:
            AnalysisResult: Kết quả từ Detekt
        """
        import time
        start_time = time.time()
        
        config = self.tools_config.get("detekt", {})
        
        # Check if this is a Kotlin project
        kotlin_files = self._count_kotlin_files(project_path)
        if kotlin_files == 0:
            return AnalysisResult(
                tool="detekt",
                project_path=project_path,
                total_files_analyzed=0,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message="Không tìm thấy file .kt trong project"
            )
        
        # Get or download Detekt JAR
        jar_path = self._get_detekt_jar(config)
        if not jar_path:
            return AnalysisResult(
                tool="detekt",
                project_path=project_path,
                total_files_analyzed=kotlin_files,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message="Không thể download hoặc tìm thấy Detekt JAR"
            )
        
        # Build command
        cmd = [
            "java", "-jar", jar_path,
            "--input", project_path,
            "--report", "xml:detekt-report.xml"
        ]
        
        # Add config file if specified
        if config.get("config_file"):
            cmd.extend(["--config", config["config_file"]])
        elif config.get("build_upon_default_config", True):
            cmd.append("--build-upon-default-config")
        
        # Add baseline if specified
        if config.get("baseline"):
            cmd.extend(["--baseline", config["baseline"]])
        elif config.get("create_baseline"):
            cmd.extend(["--create-baseline", "detekt-baseline.xml"])
        
        # Add other options
        if config.get("fail_fast"):
            cmd.append("--fail-fast")
        
        if config.get("auto_correct"):
            cmd.append("--auto-correct")
        
        # Add excludes
        exclude_patterns = config.get("exclude_patterns", [])
        for pattern in exclude_patterns:
            cmd.extend(["--excludes", pattern])
        
        logger.info(f"Chạy Detekt command: {' '.join(cmd)}")
        
        try:
            # Run Detekt
            result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            execution_time = time.time() - start_time
            
            # Read XML report if it exists
            xml_report_path = os.path.join(project_path, "detekt-report.xml")
            raw_output = result.stdout
            
            if os.path.exists(xml_report_path):
                with open(xml_report_path, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
                    findings = self.parse_detekt_output(xml_content, project_path)
                    # Clean up report file
                    os.remove(xml_report_path)
            else:
                # Fallback to parsing stderr/stdout
                findings = self.parse_detekt_text_output(result.stderr + result.stdout, project_path)
            
            success = True
            error_message = None
            
            # Log command
            command_executed = ' '.join(cmd)
            
            return AnalysisResult(
                tool="detekt",
                project_path=project_path,
                total_files_analyzed=kotlin_files,
                total_findings=len(findings),
                findings=findings,
                execution_time_seconds=execution_time,
                success=success,
                error_message=error_message,
                command_executed=command_executed,
                raw_output=raw_output
            )
            
        except subprocess.TimeoutExpired:
            return AnalysisResult(
                tool="detekt",
                project_path=project_path,
                total_files_analyzed=kotlin_files,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message="Detekt timeout (>5 minutes)"
            )
        except Exception as e:
            logger.error(f"Lỗi chạy Detekt: {str(e)}")
            return AnalysisResult(
                tool="detekt",
                project_path=project_path,
                total_files_analyzed=kotlin_files,
                total_findings=0,
                findings=[],
                execution_time_seconds=time.time() - start_time,
                success=False,
                error_message=f"Lỗi chạy Detekt: {str(e)}"
            )
    
    def parse_detekt_output(self, xml_content: str, project_path: str) -> List[Finding]:
        """
        Parse XML output từ Detekt.
        
        Args:
            xml_content: Nội dung XML từ Detekt
            project_path: Đường dẫn project
            
        Returns:
            List[Finding]: Danh sách findings
        """
        findings = []
        
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            
            # Detekt XML format:
            # <checkstyle>
            #   <file name="path/to/file.kt">
            #     <error line="10" column="5" severity="error" message="..." source="detekt.style.MagicNumber"/>
            #   </file>
            # </checkstyle>
            
            for file_elem in root.findall('.//file'):
                file_path = file_elem.get('name', '')
                
                # Make absolute path
                if not os.path.isabs(file_path):
                    file_path = os.path.join(project_path, file_path)
                
                for error_elem in file_elem.findall('error'):
                    line_number = int(error_elem.get('line', '1'))
                    column_number = int(error_elem.get('column', '1'))
                    severity_str = error_elem.get('severity', '')
                    message = error_elem.get('message', '')
                    source = error_elem.get('source', '')
                    
                    # Extract rule name từ source (e.g., "detekt.style.MagicNumber" -> "MagicNumber")
                    rule_id = source.split('.')[-1] if source else 'unknown'
                    
                    # Classify finding
                    severity, finding_type = self._classify_detekt_finding(severity_str, rule_id, source)
                    
                    finding = Finding(
                        file_path=file_path,
                        line_number=line_number,
                        column_number=column_number,
                        severity=severity,
                        finding_type=finding_type,
                        rule_id=rule_id,
                        message=message,
                        tool="detekt",
                        suggestion=self._get_detekt_suggestion(rule_id)
                    )
                    
                    findings.append(finding)
            
        except Exception as e:
            logger.error(f"Lỗi parse Detekt XML: {str(e)}")
            # Fallback to text parsing
            return self.parse_detekt_text_output(xml_content, project_path)
        
        logger.info(f"Parsed {len(findings)} findings từ Detekt XML output")
        return findings
    
    def parse_detekt_text_output(self, output_str: str, project_path: str) -> List[Finding]:
        """
        Parse text output từ Detekt khi XML không available.
        
        Args:
            output_str: Text output từ Detekt
            project_path: Đường dẫn project
            
        Returns:
            List[Finding]: Danh sách findings
        """
        findings = []
        
        if not output_str or not output_str.strip():
            return findings
        
        lines = output_str.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detekt text format patterns:
            # 1. file.kt:line:column: ruleName: message
            # 2. file.kt:line: ruleName - message
            
            # Pattern 1: file.kt:line:column: ruleName: message
            pattern1 = r'^(.+?):(\d+):(\d+):\s*([^:]+):\s*(.+)$'
            match1 = re.match(pattern1, line)
            
            if match1:
                file_path = match1.group(1).strip()
                line_number = int(match1.group(2))
                column_number = int(match1.group(3))
                rule_id = match1.group(4).strip()
                message = match1.group(5).strip()
                
                # Make absolute path
                if not os.path.isabs(file_path):
                    file_path = os.path.join(project_path, file_path)
                
                severity, finding_type = self._classify_detekt_finding("warning", rule_id, "")
                
                finding = Finding(
                    file_path=file_path,
                    line_number=line_number,
                    column_number=column_number,
                    severity=severity,
                    finding_type=finding_type,
                    rule_id=rule_id,
                    message=message,
                    tool="detekt",
                    suggestion=self._get_detekt_suggestion(rule_id)
                )
                
                findings.append(finding)
                continue
            
            # Pattern 2: file.kt:line: ruleName - message
            pattern2 = r'^(.+?):(\d+):\s*([^-]+)\s*-\s*(.+)$'
            match2 = re.match(pattern2, line)
            
            if match2:
                file_path = match2.group(1).strip()
                line_number = int(match2.group(2))
                rule_id = match2.group(3).strip()
                message = match2.group(4).strip()
                
                # Make absolute path
                if not os.path.isabs(file_path):
                    file_path = os.path.join(project_path, file_path)
                
                severity, finding_type = self._classify_detekt_finding("warning", rule_id, "")
                
                finding = Finding(
                    file_path=file_path,
                    line_number=line_number,
                    column_number=1,  # Default column
                    severity=severity,
                    finding_type=finding_type,
                    rule_id=rule_id,
                    message=message,
                    tool="detekt",
                    suggestion=self._get_detekt_suggestion(rule_id)
                )
                
                findings.append(finding)
        
        logger.info(f"Parsed {len(findings)} findings từ Detekt text output")
        return findings
    
    def _classify_detekt_finding(self, severity_str: str, rule_id: str, source: str) -> Tuple[SeverityLevel, FindingType]:
        """
        Phân loại Detekt finding theo severity, rule ID và source.
        
        Args:
            severity_str: Severity từ Detekt ("error", "warning", etc.)
            rule_id: Rule ID (e.g., "MagicNumber")
            source: Full source path (e.g., "detekt.style.MagicNumber")
            
        Returns:
            Tuple[SeverityLevel, FindingType]: Severity và type
        """
        # Map severity
        severity_map = {
            'error': SeverityLevel.HIGH,
            'warning': SeverityLevel.MEDIUM,
            'info': SeverityLevel.LOW
        }
        severity = severity_map.get(severity_str.lower(), SeverityLevel.MEDIUM)
        
        # Detekt rule categories based on source package
        if 'security' in source.lower():
            finding_type = FindingType.SECURITY
        elif 'performance' in source.lower():
            finding_type = FindingType.PERFORMANCE
        elif 'complexity' in source.lower():
            finding_type = FindingType.REFACTOR
        elif 'style' in source.lower():
            finding_type = FindingType.STYLE
        elif 'naming' in source.lower():
            finding_type = FindingType.CONVENTION
        elif 'exceptions' in source.lower():
            finding_type = FindingType.ERROR
        elif 'coroutines' in source.lower():
            finding_type = FindingType.WARNING
        else:
            # Classify by rule name patterns
            rule_lower = rule_id.lower()
            
            if any(word in rule_lower for word in ['magic', 'number', 'string', 'hardcoded']):
                finding_type = FindingType.REFACTOR
            elif any(word in rule_lower for word in ['unused', 'dead', 'unnecessary']):
                finding_type = FindingType.WARNING
            elif any(word in rule_lower for word in ['naming', 'case', 'length']):
                finding_type = FindingType.CONVENTION
            elif any(word in rule_lower for word in ['complexity', 'cognitive', 'cyclomatic']):
                finding_type = FindingType.REFACTOR
            elif any(word in rule_lower for word in ['performance', 'slow', 'inefficient']):
                finding_type = FindingType.PERFORMANCE
            elif any(word in rule_lower for word in ['security', 'unsafe', 'vulnerable']):
                finding_type = FindingType.SECURITY
            else:
                finding_type = FindingType.STYLE
        
        return severity, finding_type
    
    def _get_detekt_suggestion(self, rule_id: str) -> Optional[str]:
        """
        Lấy suggestion cho Detekt rule.
        
        Args:
            rule_id: Detekt rule ID
            
        Returns:
            Optional[str]: Suggestion text
        """
        suggestions = {
            'MagicNumber': 'Định nghĩa magic numbers thành named constants để improve readability',
            'LongMethod': 'Chia method dài thành nhiều methods nhỏ hơn',
            'LongParameterList': 'Sử dụng data class hoặc builder pattern để reduce parameter count',
            'ComplexMethod': 'Simplify method logic hoặc extract thành helper methods',
            'TooManyFunctions': 'Consider splitting class thành multiple smaller classes',
            'LargeClass': 'Refactor large class thành smaller, focused classes',
            'UnusedPrivateMember': 'Remove unused private members để clean up code',
            'DeadCode': 'Remove unreachable code để improve maintainability',
            'EmptyCodeBlock': 'Remove empty code blocks hoặc add meaningful implementation',
            'UnnecessaryParentheses': 'Remove unnecessary parentheses để improve readability',
            'FunctionName': 'Sử dụng camelCase naming convention cho function names',
            'ClassNaming': 'Sử dụng PascalCase naming convention cho class names',
            'VariableNaming': 'Sử dụng camelCase naming convention cho variable names',
            'PackageNaming': 'Sử dụng lowercase naming convention cho package names',
            'WildcardImport': 'Sử dụng specific imports thay vì wildcard imports',
            'UnusedImports': 'Remove unused imports để clean up code',
            'NoWildcardImports': 'Avoid wildcard imports để improve code clarity',
            'MaxLineLength': 'Break long lines để improve readability (max 120 characters)',
            'TrailingWhitespace': 'Remove trailing whitespace từ lines',
            'FinalNewline': 'Add final newline at end of file',
            'SpacingBetweenPackageAndImports': 'Add proper spacing between package và import declarations'
        }
        
        return suggestions.get(rule_id)
    
    def _count_kotlin_files(self, project_path: str) -> int:
        """
        Đếm số file .kt trong project.
        
        Args:
            project_path: Đường dẫn project
            
        Returns:
            int: Số file .kt
        """
        kotlin_files = 0
        
        for root, dirs, files in os.walk(project_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in ['build', '.git', '.idea', '.gradle']]
            
            for file in files:
                if file.endswith('.kt'):
                    kotlin_files += 1
        
        return kotlin_files
    
    def _get_detekt_jar(self, config: Dict[str, Any]) -> Optional[str]:
        """
        Lấy đường dẫn đến Detekt JAR, download nếu cần.
        
        Args:
            config: Detekt configuration
            
        Returns:
            Optional[str]: Đường dẫn đến JAR file
        """
        jar_path = config.get("jar_path")
        if jar_path and os.path.exists(jar_path):
            return jar_path
        
        # Auto-download
        version = config.get("version", "1.23.4")
        tools_dir = os.path.expanduser("~/.ai_codescan/jars")
        jar_filename = f"detekt-cli-{version}-all.jar"
        jar_path = os.path.join(tools_dir, jar_filename)
        
        if os.path.exists(jar_path):
            return jar_path
        
        # Download từ GitHub releases
        download_url = f"https://github.com/detekt/detekt/releases/download/v{version}/detekt-cli-{version}-all.jar"
        
        return self._download_jar("detekt", version, download_url) 