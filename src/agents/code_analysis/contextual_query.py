#!/usr/bin/env python3
"""
AI CodeScan - Contextual Query Agent

Agent thực hiện truy vấn contextual dựa trên Code Knowledge Graph và static analysis findings.
Kết hợp thông tin từ CKG với findings để cung cấp context deeper analysis.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

from .static_analysis_integrator import Finding, AnalysisResult, SeverityLevel, FindingType
from ..ckg_operations import CKGQueryInterfaceAgent, CKGQueryResult, ConnectionConfig


@dataclass 
class ContextualFinding:
    """Finding được bổ sung context từ CKG."""
    original_finding: Finding
    context: Dict[str, Any]
    related_findings: List[Finding]
    impact_score: float
    recommendations: List[str]


@dataclass
class ImpactScore:
    """Score đánh giá tác động của finding."""
    severity_score: float
    complexity_score: float
    usage_score: float
    total_score: float
    explanation: str


@dataclass
class ContextualAnalysisResult:
    """Kết quả phân tích contextual."""
    project_path: str
    total_contextual_findings: int
    contextual_findings: List[ContextualFinding]
    analysis_summary: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None


class ContextualQueryAgent:
    """
    Agent thực hiện contextual query.
    
    Trách nhiệm:
    - Enrich static analysis findings với CKG context
    - Tìm related code elements và dependencies  
    - Tính toán impact scores
    - Cung cấp contextual recommendations
    - Phân tích patterns và anti-patterns
    """
    
    def __init__(self, ckg_agent: Optional[CKGQueryInterfaceAgent] = None):
        """
        Khởi tạo ContextualQueryAgent.
        
        Args:
            ckg_agent: CKG query interface agent
        """
        self.ckg_agent = ckg_agent or CKGQueryInterfaceAgent()
    
    def analyze_findings_with_context(
        self, 
        analysis_results: Dict[str, AnalysisResult],
        project_path: str
    ) -> ContextualAnalysisResult:
        """
        Phân tích findings với context từ CKG.
        
        Args:
            analysis_results: Kết quả static analysis
            project_path: Đường dẫn project
            
        Returns:
            ContextualAnalysisResult: Kết quả contextual analysis
        """
        try:
            logger.info(f"Bắt đầu contextual analysis cho {project_path}")
            
            # Collect all findings
            all_findings = []
            for tool_result in analysis_results.values():
                if tool_result.success:
                    all_findings.extend(tool_result.findings)
            
            if not all_findings:
                logger.info("Không có findings để analyze")
                return ContextualAnalysisResult(
                    project_path=project_path,
                    total_contextual_findings=0,
                    contextual_findings=[],
                    analysis_summary={},
                    success=True
                )
            
            # Process findings với context
            contextual_findings = []
            for finding in all_findings:
                contextual_finding = self._enrich_finding_with_context(finding, project_path)
                if contextual_finding:
                    contextual_findings.append(contextual_finding)
            
            # Generate analysis summary
            summary = self._generate_analysis_summary(contextual_findings, project_path)
            
            logger.info(f"Hoàn thành contextual analysis: {len(contextual_findings)} findings")
            
            return ContextualAnalysisResult(
                project_path=project_path,
                total_contextual_findings=len(contextual_findings),
                contextual_findings=contextual_findings,
                analysis_summary=summary,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Lỗi contextual analysis: {str(e)}")
            return ContextualAnalysisResult(
                project_path=project_path,
                total_contextual_findings=0,
                contextual_findings=[],
                analysis_summary={},
                success=False,
                error_message=str(e)
            )
    
    def _enrich_finding_with_context(self, finding: Finding, project_path: str) -> Optional[ContextualFinding]:
        """
        Enrich một finding với context từ CKG.
        
        Args:
            finding: Finding cần enrich
            project_path: Đường dẫn project
            
        Returns:
            ContextualFinding hoặc None nếu không thể enrich
        """
        try:
            context = {}
            related_findings = []
            recommendations = []
            
            # Get basic file context
            file_context = self._get_file_context(finding.file_path)
            if file_context:
                context.update(file_context)
            
            # Get function/class context nếu có thể determine được
            code_element_context = self._get_code_element_context(finding)
            if code_element_context:
                context.update(code_element_context)
            
            # Find related findings
            related_findings = self._find_related_findings(finding, project_path)
            
            # Calculate impact score
            impact_score = self._calculate_impact_score(finding, context, related_findings)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(finding, context)
            
            return ContextualFinding(
                original_finding=finding,
                context=context,
                related_findings=related_findings,
                impact_score=impact_score,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.debug(f"Không thể enrich finding {finding}: {str(e)}")
            return None
    
    def _get_file_context(self, file_path: str) -> Dict[str, Any]:
        """
        Lấy context của file từ CKG.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            Dict với file context
        """
        context = {}
        
        try:
            # Get functions in file
            functions_result = self.ckg_agent.get_functions_in_file(file_path)
            if functions_result.success:
                context["functions"] = functions_result.results
                context["functions_count"] = len(functions_result.results)
            
            # Get classes in file
            classes_result = self.ckg_agent.get_classes_in_file(file_path)
            if classes_result.success:
                context["classes"] = classes_result.results
                context["classes_count"] = len(classes_result.results)
            
            # Get imports in file
            imports_result = self.ckg_agent.get_imports_in_file(file_path)
            if imports_result.success:
                context["imports"] = imports_result.results
                context["imports_count"] = len(imports_result.results)
            
            # Get file dependencies
            deps_result = self.ckg_agent.get_file_dependencies(file_path)
            if deps_result.success:
                context["dependencies"] = deps_result.results
                context["dependencies_count"] = len(deps_result.results)
            
        except Exception as e:
            logger.debug(f"Lỗi lấy file context cho {file_path}: {str(e)}")
        
        return context
    
    def _get_code_element_context(self, finding: Finding) -> Dict[str, Any]:
        """
        Lấy context của code element cụ thể (function, class).
        
        Args:
            finding: Finding để analyze
            
        Returns:
            Dict với code element context
        """
        context = {}
        
        try:
            # Attempt to identify function/class từ finding location
            # This is a simplified approach - could be more sophisticated
            
            # Search for functions around the finding line
            search_result = self.ckg_agent.search_by_name("*", ["Function"])
            if search_result.success:
                for func in search_result.results:
                    if (func.get("file_path") == finding.file_path and 
                        abs(func.get("line_number", 0) - finding.line_number) <= 10):
                        context["nearby_function"] = func
                        
                        # Get function callers/callees
                        callers = self.ckg_agent.find_function_callers(func["name"])
                        if callers.success:
                            context["function_callers"] = callers.results
                            
                        callees = self.ckg_agent.find_function_callees(func["name"], finding.file_path)
                        if callees.success:
                            context["function_callees"] = callees.results
                        break
            
            # Search for classes around the finding line
            search_result = self.ckg_agent.search_by_name("*", ["Class"])
            if search_result.success:
                for cls in search_result.results:
                    if (cls.get("file_path") == finding.file_path and 
                        abs(cls.get("line_number", 0) - finding.line_number) <= 20):
                        context["nearby_class"] = cls
                        
                        # Get class hierarchy
                        hierarchy = self.ckg_agent.get_class_hierarchy(cls["name"])
                        if hierarchy.success:
                            context["class_hierarchy"] = hierarchy.results
                        break
            
        except Exception as e:
            logger.debug(f"Lỗi lấy code element context: {str(e)}")
        
        return context
    
    def _find_related_findings(self, finding: Finding, project_path: str) -> List[Finding]:
        """
        Tìm findings liên quan đến finding hiện tại.
        
        Args:
            finding: Finding gốc
            project_path: Đường dẫn project
            
        Returns:
            List[Finding]: Danh sách related findings
        """
        # Placeholder implementation
        # Trong thực tế, có thể implement sophisticated logic để:
        # - Tìm findings trong cùng function/class
        # - Tìm findings trong related files (dependencies)
        # - Tìm findings với cùng rule_id
        # - Tìm findings có pattern tương tự
        
        return []
    
    def _calculate_impact_score(
        self, 
        finding: Finding, 
        context: Dict[str, Any], 
        related_findings: List[Finding]
    ) -> float:
        """
        Tính impact score cho finding dựa trên severity và context.
        
        Args:
            finding: Finding gốc
            context: Context từ CKG
            related_findings: Related findings
            
        Returns:
            float: Impact score (0-1)
        """
        base_score = 0.0
        
        # Base score từ severity
        severity_scores = {
            SeverityLevel.LOW: 0.2,
            SeverityLevel.MEDIUM: 0.5,
            SeverityLevel.HIGH: 0.8,
            SeverityLevel.CRITICAL: 1.0
        }
        base_score = severity_scores.get(finding.severity, 0.5)
        
        # Modifiers dựa trên context
        modifiers = 1.0
        
        # Increase score if function có nhiều callers (high impact)
        callers = context.get("function_callers", [])
        if len(callers) > 5:
            modifiers += 0.2
        elif len(callers) > 2:
            modifiers += 0.1
        
        # Increase score if file có nhiều dependencies (central file)
        deps_count = context.get("dependencies_count", 0)
        if deps_count > 10:
            modifiers += 0.2
        elif deps_count > 5:
            modifiers += 0.1
        
        # Increase score if có nhiều related findings
        if len(related_findings) > 3:
            modifiers += 0.1
        
        # Decrease score for certain finding types
        if finding.finding_type in [FindingType.STYLE, FindingType.CONVENTION]:
            modifiers *= 0.8
        
        final_score = min(base_score * modifiers, 1.0)
        return round(final_score, 2)
    
    def _generate_recommendations(self, finding: Finding, context: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations dựa trên finding và context.
        
        Args:
            finding: Finding gốc
            context: Context từ CKG
            
        Returns:
            List[str]: Danh sách recommendations
        """
        recommendations = []
        
        # Generic recommendations dựa trên finding type
        if finding.finding_type == FindingType.ERROR:
            recommendations.append("Fix this error immediately as it may cause runtime issues")
            
        elif finding.finding_type == FindingType.STYLE:
            recommendations.append("Consider fixing this style issue to improve code readability")
            
        elif finding.finding_type == FindingType.REFACTOR:
            recommendations.append("Refactor this code to reduce complexity and improve maintainability")
            
        elif finding.finding_type == FindingType.SECURITY:
            recommendations.append("Address this security issue to protect against vulnerabilities")
        
        # Context-specific recommendations
        callers_count = len(context.get("function_callers", []))
        if callers_count > 5:
            recommendations.append(f"This function is called by {callers_count} other functions. Changes here will have wide impact.")
        
        deps_count = context.get("dependencies_count", 0)
        if deps_count > 10:
            recommendations.append(f"This file has {deps_count} dependencies. Consider breaking it into smaller modules.")
        
        # Tool-specific recommendations
        if finding.tool == "flake8":
            if finding.rule_id.startswith("E501"):
                recommendations.append("Consider breaking long lines into multiple lines for better readability")
            elif finding.rule_id.startswith("F401"):
                recommendations.append("Remove unused imports to keep code clean")
                
        elif finding.tool == "pylint":
            if "too-many" in finding.rule_id:
                recommendations.append("Consider refactoring to reduce complexity (split into smaller functions/classes)")
        
        elif finding.tool == "mypy":
            recommendations.append("Add type annotations to improve code clarity and catch type-related errors")
        
        return recommendations
    
    def _generate_analysis_summary(self, contextual_findings: List[ContextualFinding], project_path: str) -> Dict[str, Any]:
        """
        Generate summary của contextual analysis.
        
        Args:
            contextual_findings: Danh sách contextual findings
            project_path: Đường dẫn project
            
        Returns:
            Dict với analysis summary
        """
        if not contextual_findings:
            return {}
        
        # Calculate statistics
        total_findings = len(contextual_findings)
        
        # Impact distribution
        high_impact = len([f for f in contextual_findings if f.impact_score >= 0.8])
        medium_impact = len([f for f in contextual_findings if 0.5 <= f.impact_score < 0.8])
        low_impact = len([f for f in contextual_findings if f.impact_score < 0.5])
        
        # Severity distribution
        severity_counts = {}
        for finding in contextual_findings:
            severity = finding.original_finding.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Type distribution
        type_counts = {}
        for finding in contextual_findings:
            ftype = finding.original_finding.finding_type.value
            type_counts[ftype] = type_counts.get(ftype, 0) + 1
        
        # File distribution
        file_counts = {}
        for finding in contextual_findings:
            file_path = finding.original_finding.file_path
            file_counts[file_path] = file_counts.get(file_path, 0) + 1
        
        # Top problematic files
        top_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Average impact score
        avg_impact = sum(f.impact_score for f in contextual_findings) / total_findings
        
        summary = {
            "total_findings": total_findings,
            "impact_distribution": {
                "high_impact": high_impact,
                "medium_impact": medium_impact,
                "low_impact": low_impact
            },
            "severity_distribution": severity_counts,
            "type_distribution": type_counts,
            "average_impact_score": round(avg_impact, 2),
            "top_problematic_files": top_files,
            "recommendations": {
                "priority_focus": "Focus on high-impact findings first" if high_impact > 0 else "Address medium-impact findings",
                "code_quality": "Consider refactoring if many complexity issues found",
                "testing": "Add unit tests for functions with many callers"
            }
        }
        
        return summary
    
    def get_function_complexity_analysis(self, file_path: str) -> CKGQueryResult:
        """
        Phân tích complexity của functions trong file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: Kết quả phân tích complexity
        """
        try:
            # Get complex functions (many parameters)
            complex_funcs = self.ckg_agent.get_complex_functions(min_parameters=4)
            
            if complex_funcs.success:
                # Filter by file path
                file_functions = [
                    func for func in complex_funcs.results 
                    if func.get("file_path") == file_path
                ]
                
                # Create custom result
                return CKGQueryResult(
                    query=f"Complex functions in {file_path}",
                    results=file_functions,
                    total_count=len(file_functions),
                    execution_time_ms=complex_funcs.execution_time_ms,
                    success=True
                )
            else:
                return complex_funcs
                
        except Exception as e:
            logger.error(f"Lỗi analyzing function complexity: {str(e)}")
            return CKGQueryResult(
                query=f"Complex functions in {file_path}",
                results=[],
                total_count=0,
                execution_time_ms=0,
                success=False,
                error_message=str(e)
            )
    
    def find_circular_dependencies_affecting_file(self, file_path: str) -> CKGQueryResult:
        """
        Tìm circular dependencies ảnh hưởng đến file.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            CKGQueryResult: Circular dependencies
        """
        try:
            # Get all circular dependencies
            circular_deps = self.ckg_agent.find_circular_dependencies()
            
            if circular_deps.success:
                # Filter cycles that involve this file
                relevant_cycles = []
                for cycle in circular_deps.results:
                    cycle_path = cycle.get("cycle_path", [])
                    # Check if any module in cycle matches file (convert file path to module name)
                    file_module = file_path.replace(".py", "").replace("/", ".")
                    if any(file_module in module for module in cycle_path):
                        relevant_cycles.append(cycle)
                
                return CKGQueryResult(
                    query=f"Circular dependencies affecting {file_path}",
                    results=relevant_cycles,
                    total_count=len(relevant_cycles),
                    execution_time_ms=circular_deps.execution_time_ms,
                    success=True
                )
            else:
                return circular_deps
                
        except Exception as e:
            logger.error(f"Lỗi finding circular dependencies: {str(e)}")
            return CKGQueryResult(
                query=f"Circular dependencies affecting {file_path}",
                results=[],
                total_count=0,
                execution_time_ms=0,
                success=False,
                error_message=str(e)
            ) 