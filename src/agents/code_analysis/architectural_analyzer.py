"""
ArchitecturalAnalyzerAgent - Phân tích kiến trúc cơ bản cho code.

Agent này thực hiện phân tích kiến trúc cấp cao trên code knowledge graph (CKG)
để phát hiện các vấn đề kiến trúc như circular dependencies và unused public elements.
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Set, Any, Optional, Tuple
from enum import Enum

# Setup fallback logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from ..ckg_operations.ckg_query_interface import CKGQueryInterfaceAgent, CKGQueryResult


class IssueType(Enum):
    """Loại vấn đề kiến trúc."""
    CIRCULAR_DEPENDENCY = "circular_dependency"
    UNUSED_PUBLIC_ELEMENT = "unused_public_element"
    ORPHANED_MODULE = "orphaned_module"
    EXCESSIVE_COUPLING = "excessive_coupling"


class SeverityLevel(Enum):
    """Mức độ nghiêm trọng của vấn đề kiến trúc."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ArchitecturalIssue:
    """Một vấn đề kiến trúc được phát hiện."""
    issue_type: IssueType
    severity: SeverityLevel
    title: str
    description: str
    affected_elements: List[str]
    suggestion: Optional[str] = None
    static_analysis_limitation: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        """String representation."""
        return f"[{self.severity.value.upper()}] {self.title}: {self.description}"


@dataclass
class CircularDependency:
    """Một circular dependency được phát hiện."""
    cycle: List[str]  # Danh sách các elements trong cycle
    cycle_type: str   # 'file', 'module', 'class', etc.
    description: str
    
    def __str__(self) -> str:
        """String representation."""
        cycle_str = " -> ".join(self.cycle + [self.cycle[0]])
        return f"Circular {self.cycle_type} dependency: {cycle_str}"


@dataclass
class UnusedElement:
    """Một public element không được sử dụng."""
    element_name: str
    element_type: str  # 'class', 'function', 'method', etc.
    file_path: str
    line_number: Optional[int] = None
    reason: Optional[str] = None


@dataclass
class ArchitecturalAnalysisResult:
    """Kết quả phân tích kiến trúc."""
    project_path: str
    total_issues: int
    issues: List[ArchitecturalIssue]
    circular_dependencies: List[CircularDependency]
    unused_elements: List[UnusedElement]
    analysis_scope: str
    limitations: List[str]
    execution_time_seconds: float
    success: bool
    error_message: Optional[str] = None


class ArchitecturalAnalyzerAgent:
    """Agent phân tích kiến trúc cơ bản."""

    def __init__(self, ckg_query_agent: Optional[CKGQueryInterfaceAgent] = None):
        """
        Khởi tạo ArchitecturalAnalyzerAgent.
        
        Args:
            ckg_query_agent: CKGQueryInterfaceAgent để truy vấn code knowledge graph.
                           Nếu None, sẽ tạo instance mới.
        """
        self.logger = logger
        self.ckg_query_agent = ckg_query_agent or CKGQueryInterfaceAgent()
        
        # Các hạn chế của phân tích tĩnh
        self.static_analysis_limitations = [
            "Phân tích tĩnh không thể phát hiện việc sử dụng qua reflection",
            "Dependency injection có thể làm cho các phần tử có vẻ như không được sử dụng",
            "Dynamic loading và runtime code generation không được phát hiện",
            "External API calls và framework callbacks có thể bị bỏ qua",
            "Chỉ phân tích trong phạm vi codebase đã được parse"
        ]

    def analyze_architecture(self, project_path: str) -> ArchitecturalAnalysisResult:
        """
        Thực hiện phân tích kiến trúc toàn diện.
        
        Args:
            project_path: Đường dẫn đến project cần phân tích.
            
        Returns:
            ArchitecturalAnalysisResult: Kết quả phân tích kiến trúc.
        """
        import time
        start_time = time.time()
        
        try:
            self.logger.info(f"Bắt đầu phân tích kiến trúc cho project: {project_path}")
            
            issues = []
            circular_deps = []
            unused_elements = []
            
            # Phân tích circular dependencies
            self.logger.info("Phân tích circular dependencies...")
            circular_deps = self._analyze_circular_dependencies()
            
            # Chuyển đổi circular dependencies thành issues
            for cycle in circular_deps:
                issue = self._create_circular_dependency_issue(cycle)
                issues.append(issue)
            
            # Phân tích unused public elements
            self.logger.info("Phân tích unused public elements...")
            unused_elements = self._analyze_unused_public_elements()
            
            # Chuyển đổi unused elements thành issues
            for element in unused_elements:
                issue = self._create_unused_element_issue(element)
                issues.append(issue)
            
            execution_time = time.time() - start_time
            
            result = ArchitecturalAnalysisResult(
                project_path=project_path,
                total_issues=len(issues),
                issues=issues,
                circular_dependencies=circular_deps,
                unused_elements=unused_elements,
                analysis_scope="File-level và module-level dependencies",
                limitations=self.static_analysis_limitations,
                execution_time_seconds=execution_time,
                success=True
            )
            
            self.logger.info(f"Hoàn thành phân tích kiến trúc: {len(issues)} issues, {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Lỗi trong phân tích kiến trúc: {str(e)}")
            
            return ArchitecturalAnalysisResult(
                project_path=project_path,
                total_issues=0,
                issues=[],
                circular_dependencies=[],
                unused_elements=[],
                analysis_scope="Failed analysis",
                limitations=self.static_analysis_limitations,
                execution_time_seconds=execution_time,
                success=False,
                error_message=str(e)
            )

    def _analyze_circular_dependencies(self) -> List[CircularDependency]:
        """
        Phát hiện circular dependencies trong codebase.
        
        Returns:
            List[CircularDependency]: Danh sách các circular dependencies được phát hiện.
        """
        circular_deps = []
        
        try:
            # Lấy tất cả file dependencies
            deps_result = self._get_all_file_dependencies()
            if not deps_result.success:
                self.logger.warning(f"Không thể lấy file dependencies: {deps_result.error_message}")
                return circular_deps
            
            # Xây dựng dependency graph
            dep_graph = self._build_dependency_graph(deps_result.results)
            
            # Tìm cycles trong graph
            cycles = self._find_cycles_in_graph(dep_graph)
            
            # Chuyển đổi cycles thành CircularDependency objects
            for cycle in cycles:
                circular_dep = CircularDependency(
                    cycle=cycle,
                    cycle_type="file",
                    description=f"Circular dependency giữa {len(cycle)} files"
                )
                circular_deps.append(circular_dep)
                
        except Exception as e:
            self.logger.error(f"Lỗi trong phân tích circular dependencies: {str(e)}")
        
        return circular_deps

    def _get_all_file_dependencies(self) -> CKGQueryResult:
        """
        Lấy tất cả file dependencies từ CKG.
        
        Returns:
            CKGQueryResult: Kết quả truy vấn chứa file dependencies.
        """
        query = """
        MATCH (f1:File)-[r:IMPORTS]->(f2:File)
        RETURN f1.path as source_file, f2.path as target_file
        UNION
        MATCH (f1:File)-[r:CALLS]->(f2:File)
        RETURN f1.path as source_file, f2.path as target_file
        """
        
        return self.ckg_query_agent.execute_query(query)

    def _build_dependency_graph(self, dependency_data: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
        """
        Xây dựng dependency graph từ dữ liệu dependencies.
        
        Args:
            dependency_data: Danh sách các dependency records.
            
        Returns:
            Dict[str, Set[str]]: Dependency graph dạng adjacency list.
        """
        graph = {}
        
        for record in dependency_data:
            source = record.get('source_file', '')
            target = record.get('target_file', '')
            
            if source and target:
                if source not in graph:
                    graph[source] = set()
                graph[source].add(target)
                
                # Đảm bảo target cũng có entry trong graph
                if target not in graph:
                    graph[target] = set()
        
        return graph

    def _find_cycles_in_graph(self, graph: Dict[str, Set[str]]) -> List[List[str]]:
        """
        Tìm tất cả cycles trong directed graph sử dụng DFS.
        
        Args:
            graph: Dependency graph dạng adjacency list.
            
        Returns:
            List[List[str]]: Danh sách các cycles được phát hiện.
        """
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str) -> bool:
            """DFS để tìm cycles."""
            if node in rec_stack:
                # Tìm thấy cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return True
            
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            # Duyệt tất cả neighbors
            for neighbor in graph.get(node, []):
                if dfs(neighbor):
                    pass  # Continue tìm kiếm cycles khác
            
            rec_stack.remove(node)
            path.pop()
            return False
        
        # Duyệt tất cả nodes trong graph
        for node in graph:
            if node not in visited:
                dfs(node)
        
        return cycles

    def _analyze_unused_public_elements(self) -> List[UnusedElement]:
        """
        Phát hiện public elements không được sử dụng.
        
        Returns:
            List[UnusedElement]: Danh sách các public elements không được sử dụng.
        """
        unused_elements = []
        
        try:
            # Phân tích unused public functions
            unused_functions = self._find_unused_public_functions()
            unused_elements.extend(unused_functions)
            
            # Phân tích unused public classes
            unused_classes = self._find_unused_public_classes()
            unused_elements.extend(unused_classes)
            
        except Exception as e:
            self.logger.error(f"Lỗi trong phân tích unused public elements: {str(e)}")
        
        return unused_elements

    def _find_unused_public_functions(self) -> List[UnusedElement]:
        """
        Tìm public functions không được sử dụng.
        
        Returns:
            List[UnusedElement]: Danh sách unused public functions.
        """
        unused_functions = []
        
        try:
            # Sử dụng method có sẵn từ CKGQueryInterfaceAgent
            result = self.ckg_query_agent.get_unused_public_functions()
            
            if result.success:
                for record in result.results:
                    element = UnusedElement(
                        element_name=record.get('name', 'Unknown'),
                        element_type='function',
                        file_path=record.get('file_path', 'Unknown'),
                        line_number=record.get('line_number'),
                        reason="Không được gọi từ bên ngoài module của nó"
                    )
                    unused_functions.append(element)
            else:
                self.logger.warning(f"Không thể lấy unused public functions: {result.error_message}")
                
        except Exception as e:
            self.logger.error(f"Lỗi trong tìm kiếm unused public functions: {str(e)}")
        
        return unused_functions

    def _find_unused_public_classes(self) -> List[UnusedElement]:
        """
        Tìm public classes không được sử dụng.
        
        Returns:
            List[UnusedElement]: Danh sách unused public classes.
        """
        unused_classes = []
        
        try:
            # Query để tìm public classes không được sử dụng
            query = """
            MATCH (c:Class)
            WHERE NOT c.name STARTS WITH '_'  // Public classes (không bắt đầu với _)
            AND NOT EXISTS(
                (f:File)-[:IMPORTS|CALLS]->(c)
                WHERE f.path <> c.file_path  // Không được import/sử dụng từ file khác
            )
            AND NOT EXISTS(
                (other:Class)-[:INHERITS_FROM]->(c)  // Không được inherit
            )
            RETURN c.name as name, c.file_path as file_path, c.line_number as line_number
            """
            
            result = self.ckg_query_agent.execute_query(query)
            
            if result.success:
                for record in result.results:
                    element = UnusedElement(
                        element_name=record.get('name', 'Unknown'),
                        element_type='class',
                        file_path=record.get('file_path', 'Unknown'),
                        line_number=record.get('line_number'),
                        reason="Không được import, inherit hoặc sử dụng từ bên ngoài module"
                    )
                    unused_classes.append(element)
            else:
                self.logger.warning(f"Không thể lấy unused public classes: {result.error_message}")
                
        except Exception as e:
            self.logger.error(f"Lỗi trong tìm kiếm unused public classes: {str(e)}")
        
        return unused_classes

    def _create_circular_dependency_issue(self, cycle: CircularDependency) -> ArchitecturalIssue:
        """
        Tạo ArchitecturalIssue từ CircularDependency.
        
        Args:
            cycle: CircularDependency đã phát hiện.
            
        Returns:
            ArchitecturalIssue: Issue tương ứng.
        """
        severity = SeverityLevel.HIGH if len(cycle.cycle) > 3 else SeverityLevel.MEDIUM
        
        return ArchitecturalIssue(
            issue_type=IssueType.CIRCULAR_DEPENDENCY,
            severity=severity,
            title=f"Circular Dependency trong {len(cycle.cycle)} files",
            description=str(cycle),
            affected_elements=cycle.cycle,
            suggestion="Cân nhắc refactor để loại bỏ circular dependency. "
                      "Có thể tạo interface chung hoặc tách logic chung ra module riêng.",
            static_analysis_limitation="Circular dependency được phát hiện dựa trên import statements. "
                                     "Dynamic imports có thể không được phát hiện."
        )

    def _create_unused_element_issue(self, element: UnusedElement) -> ArchitecturalIssue:
        """
        Tạo ArchitecturalIssue từ UnusedElement.
        
        Args:
            element: UnusedElement đã phát hiện.
            
        Returns:
            ArchitecturalIssue: Issue tương ứng.
        """
        return ArchitecturalIssue(
            issue_type=IssueType.UNUSED_PUBLIC_ELEMENT,
            severity=SeverityLevel.LOW,
            title=f"Unused Public {element.element_type.title()}: {element.element_name}",
            description=f"Public {element.element_type} '{element.element_name}' trong file "
                       f"'{element.file_path}' có vẻ như không được sử dụng bên ngoài module của nó.",
            affected_elements=[f"{element.file_path}:{element.element_name}"],
            suggestion="Cân nhắc xóa element này nếu không cần thiết, "
                      "hoặc chuyển thành private nếu chỉ sử dụng nội bộ.",
            static_analysis_limitation="Phân tích tĩnh có thể bỏ qua việc sử dụng qua reflection, "
                                     "dynamic loading, hoặc external API calls.",
            metadata={
                "element_type": element.element_type,
                "file_path": element.file_path,
                "line_number": element.line_number,
                "reason": element.reason
            }
        )

    def get_summary_stats(self, result: ArchitecturalAnalysisResult) -> Dict[str, Any]:
        """
        Tạo thống kê tóm tắt từ kết quả phân tích.
        
        Args:
            result: Kết quả phân tích kiến trúc.
            
        Returns:
            Dict[str, Any]: Thống kê tóm tắt.
        """
        stats = {
            "total_issues": result.total_issues,
            "circular_dependencies": len(result.circular_dependencies),
            "unused_elements": len(result.unused_elements),
            "execution_time": result.execution_time_seconds,
            "success": result.success
        }
        
        # Thống kê theo severity
        severity_counts = {}
        for issue in result.issues:
            severity = issue.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        stats["severity_distribution"] = severity_counts
        
        # Thống kê theo issue type
        issue_type_counts = {}
        for issue in result.issues:
            issue_type = issue.issue_type.value
            issue_type_counts[issue_type] = issue_type_counts.get(issue_type, 0) + 1
        
        stats["issue_type_distribution"] = issue_type_counts
        
        return stats 