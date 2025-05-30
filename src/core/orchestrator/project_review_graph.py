#!/usr/bin/env python3
"""
AI CodeScan - Project Review Graph

Implementation cụ thể của LangGraph workflow cho project review,
bao gồm các nodes và edges để phân tích dự án code.
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from .base_graph import BaseGraph, CodeScanState, TaskType, TaskStatus, Repository
from loguru import logger

class ProjectReviewGraph(BaseGraph):
    """
    LangGraph implementation cho project review workflow.
    
    Workflow này thực hiện:
    1. Data Acquisition - Thu thập và chuẩn bị dữ liệu từ repository
    2. Code Analysis - Phân tích code structure, quality, patterns
    3. CKG Operations - Xây dựng Code Knowledge Graph 
    4. LLM Services - Sinh báo cáo và insights
    5. Synthesis Reporting - Tổng hợp kết quả cuối cùng
    """
    
    def __init__(self, **kwargs):
        """Khởi tạo ProjectReviewGraph với cấu hình cụ thể."""
        super().__init__(**kwargs)
        self.agent_prompts = self._load_agent_prompts()
    
    def _load_agent_prompts(self) -> Dict[str, str]:
        """Load prompts cho các agents."""
        return {
            "data_acquisition": """
            Bạn là Agent Data Acquisition chuyên trách thu thập và chuẩn bị dữ liệu code.
            Nhiệm vụ: Phân tích repository và thu thập thông tin cần thiết cho việc review.
            
            Đầu vào: Repository URL và thông tin access
            Đầu ra: Danh sách files code, structure, metadata
            
            Hãy thực hiện một cách có hệ thống và chính xác.
            """,
            
            "code_analysis": """
            Bạn là Agent Code Analysis chuyên phân tích chất lượng và cấu trúc code.
            Nhiệm vụ: Đánh giá code quality, architecture patterns, potential issues.
            
            Tập trung vào:
            - Code structure và organization
            - Best practices compliance
            - Security vulnerabilities
            - Performance issues
            - Maintainability
            
            Cung cấp analysis chi tiết và actionable insights.
            """,
            
            "ckg_operations": """
            Bạn là Agent CKG Operations chuyên xây dựng Code Knowledge Graph.
            Nhiệm vụ: Tạo graph representation của codebase với relationships.
            
            Xây dựng:
            - Entities: Functions, Classes, Modules, Dependencies
            - Relationships: Calls, Inherits, Imports, Uses
            - Properties: Complexity, Coupling, Cohesion
            
            Tạo ra structured knowledge có thể query được.
            """,
            
            "llm_services": """
            Bạn là Agent LLM Services chuyên sinh insights và recommendations.
            Nhiệm vụ: Dựa trên analysis results, tạo ra insights và suggestions.
            
            Tạo ra:
            - Executive summary
            - Key findings
            - Recommendations
            - Action items
            - Risk assessment
            
            Viết một cách clear, concise và actionable.
            """,
            
            "synthesis_reporting": """
            Bạn là Agent Synthesis Reporting chuyên tổng hợp báo cáo cuối cùng.
            Nhiệm vụ: Kết hợp tất cả analysis thành báo cáo hoàn chỉnh.
            
            Báo cáo bao gồm:
            - Overview tổng quan
            - Detailed findings từ mỗi agent
            - Consolidated recommendations
            - Priority matrix
            - Implementation roadmap
            
            Đảm bảo báo cáo professional và dễ hiểu.
            """
        }
    
    def build_graph(self) -> StateGraph:
        """
        Xây dựng LangGraph cho project review workflow.
        
        Returns:
            StateGraph: Configured graph với tất cả nodes và edges
        """
        graph = StateGraph(CodeScanState)
        
        # Add nodes
        graph.add_node("data_acquisition", self.data_acquisition_node)
        graph.add_node("code_analysis", self.code_analysis_node)
        graph.add_node("ckg_operations", self.ckg_operations_node)
        graph.add_node("llm_services", self.llm_services_node)
        graph.add_node("synthesis_reporting", self.synthesis_reporting_node)
        graph.add_node("error_handler", self.error_handler_node)
        
        # Define edges - workflow sequence
        graph.set_entry_point("data_acquisition")
        
        # Main flow
        graph.add_edge("data_acquisition", "code_analysis")
        graph.add_edge("code_analysis", "ckg_operations")
        graph.add_edge("ckg_operations", "llm_services")
        graph.add_edge("llm_services", "synthesis_reporting")
        graph.add_edge("synthesis_reporting", END)
        
        # Error handling edges
        graph.add_conditional_edges(
            "data_acquisition",
            self.check_data_acquisition_success,
            {
                "continue": "code_analysis",
                "error": "error_handler"
            }
        )
        
        graph.add_conditional_edges(
            "code_analysis", 
            self.check_code_analysis_success,
            {
                "continue": "ckg_operations",
                "error": "error_handler"
            }
        )
        
        graph.add_edge("error_handler", END)
        
        return graph
    
    # Node implementations
    def data_acquisition_node(self, state: CodeScanState) -> Dict[str, Any]:
        """
        Agent Data Acquisition - Thu thập dữ liệu từ repository.
        
        Args:
            state: Current state của graph
            
        Returns:
            Dict với updates cho state
        """
        logger.info(f"[Data Acquisition] Bắt đầu thu thập dữ liệu cho task {state['task_id']}")
        
        try:
            # Update status
            state["status"] = TaskStatus.IN_PROGRESS
            state["next_action"] = "data_acquisition"
            
            # Simulate data acquisition logic
            repository = state.get("repository")
            if not repository:
                raise ValueError("Repository information is required")
            
            # Mock implementation - trong thực tế sẽ clone repo và scan files
            code_files = [
                {
                    "path": "src/main.py",
                    "type": "python",
                    "size": 1024,
                    "last_modified": datetime.now().isoformat(),
                    "content_hash": "abc123"
                },
                {
                    "path": "src/utils/helpers.py", 
                    "type": "python",
                    "size": 512,
                    "last_modified": datetime.now().isoformat(),
                    "content_hash": "def456"
                },
                {
                    "path": "tests/test_main.py",
                    "type": "python_test",
                    "size": 256,
                    "last_modified": datetime.now().isoformat(),
                    "content_hash": "ghi789"
                }
            ]
            
            # Cập nhật metadata
            metadata = {
                "total_files": len(code_files),
                "languages_detected": ["python"],
                "project_size": sum(f["size"] for f in code_files),
                "acquisition_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"[Data Acquisition] Thu thập được {len(code_files)} files")
            
            return {
                "code_files": code_files,
                "metadata": {**state.get("metadata", {}), **metadata},
                "next_action": "code_analysis"
            }
            
        except Exception as e:
            logger.error(f"[Data Acquisition] Lỗi: {str(e)}")
            return {
                "errors": state.get("errors", []) + [f"Data Acquisition Error: {str(e)}"],
                "status": TaskStatus.FAILED,
                "next_action": "error_handler"
            }
    
    def code_analysis_node(self, state: CodeScanState) -> Dict[str, Any]:
        """
        Agent Code Analysis - Phân tích chất lượng code.
        
        Args:
            state: Current state của graph
            
        Returns:
            Dict với updates cho state
        """
        logger.info(f"[Code Analysis] Bắt đầu phân tích code cho task {state['task_id']}")
        
        try:
            state["next_action"] = "code_analysis"
            
            code_files = state.get("code_files", [])
            if not code_files:
                raise ValueError("No code files available for analysis")
            
            # Mock analysis results
            analysis_results = {
                "code_quality": {
                    "overall_score": 8.5,
                    "maintainability": 8.0,
                    "complexity": 7.5,
                    "test_coverage": 85.0
                },
                "security_analysis": {
                    "vulnerabilities_found": 2,
                    "severity_breakdown": {
                        "high": 0,
                        "medium": 1, 
                        "low": 1
                    }
                },
                "architecture_patterns": {
                    "patterns_detected": ["MVC", "Repository Pattern"],
                    "anti_patterns": ["God Class"],
                    "recommendations": [
                        "Consider breaking down large classes",
                        "Add more unit tests for edge cases"
                    ]
                },
                "performance_analysis": {
                    "potential_bottlenecks": 1,
                    "optimization_opportunities": [
                        "Database query optimization in user_service.py"
                    ]
                }
            }
            
            logger.info(f"[Code Analysis] Hoàn thành phân tích với overall score: {analysis_results['code_quality']['overall_score']}")
            
            return {
                "analysis_results": {
                    **state.get("analysis_results", {}),
                    "code_analysis": analysis_results
                },
                "next_action": "ckg_operations"
            }
            
        except Exception as e:
            logger.error(f"[Code Analysis] Lỗi: {str(e)}")
            return {
                "errors": state.get("errors", []) + [f"Code Analysis Error: {str(e)}"],
                "next_action": "error_handler"
            }
    
    def ckg_operations_node(self, state: CodeScanState) -> Dict[str, Any]:
        """
        Agent CKG Operations - Xây dựng Code Knowledge Graph.
        
        Args:
            state: Current state của graph
            
        Returns:
            Dict với updates cho state
        """
        logger.info(f"[CKG Operations] Bắt đầu xây dựng knowledge graph cho task {state['task_id']}")
        
        try:
            state["next_action"] = "ckg_operations"
            
            # Mock CKG construction
            knowledge_graph = {
                "entities": {
                    "functions": [
                        {"name": "main", "module": "src.main", "complexity": 3},
                        {"name": "helper_function", "module": "src.utils.helpers", "complexity": 1}
                    ],
                    "classes": [
                        {"name": "UserService", "module": "src.services", "methods": 5},
                        {"name": "DatabaseConnection", "module": "src.db", "methods": 3}
                    ],
                    "modules": [
                        {"name": "src.main", "loc": 150, "dependencies": 2},
                        {"name": "src.utils.helpers", "loc": 75, "dependencies": 0}
                    ]
                },
                "relationships": {
                    "calls": [
                        {"from": "main", "to": "helper_function", "frequency": 5},
                        {"from": "UserService.get_user", "to": "DatabaseConnection.query", "frequency": 10}
                    ],
                    "imports": [
                        {"from": "src.main", "to": "src.utils.helpers"},
                        {"from": "src.services", "to": "src.db"}
                    ]
                },
                "metrics": {
                    "total_entities": 8,
                    "total_relationships": 6,
                    "graph_density": 0.75,
                    "max_depth": 3
                }
            }
            
            logger.info(f"[CKG Operations] Xây dựng graph với {knowledge_graph['metrics']['total_entities']} entities")
            
            return {
                "knowledge_graph": knowledge_graph,
                "next_action": "llm_services"
            }
            
        except Exception as e:
            logger.error(f"[CKG Operations] Lỗi: {str(e)}")
            return {
                "errors": state.get("errors", []) + [f"CKG Operations Error: {str(e)}"],
                "next_action": "error_handler"
            }
    
    def llm_services_node(self, state: CodeScanState) -> Dict[str, Any]:
        """
        Agent LLM Services - Sinh insights và recommendations.
        
        Args:
            state: Current state của graph
            
        Returns:
            Dict với updates cho state
        """
        logger.info(f"[LLM Services] Bắt đầu sinh insights cho task {state['task_id']}")
        
        try:
            state["next_action"] = "llm_services"
            
            # Prepare context từ previous analysis
            analysis_context = state.get("analysis_results", {})
            kg_context = state.get("knowledge_graph", {})
            
            # Generate insights using LLM
            prompt = self.agent_prompts["llm_services"]
            context_msg = f"""
            Analysis Results: {analysis_context}
            Knowledge Graph: {kg_context}
            """
            
            # Mock LLM response - trong thực tế sẽ call LLM
            llm_insights = {
                "executive_summary": "Codebase có chất lượng tốt với điểm số 8.5/10. Kiến trúc rõ ràng với patterns tốt, nhưng cần cải thiện test coverage và tối ưu hóa một số queries.",
                "key_findings": [
                    "Code quality score 8.5/10 - tốt hơn 80% projects tương tự",
                    "Test coverage 85% - đạt mức acceptable",
                    "2 security vulnerabilities minor level",
                    "1 performance bottleneck cần attention"
                ],
                "recommendations": [
                    {
                        "priority": "High",
                        "title": "Tối ưu hóa database queries",
                        "description": "Optimize queries trong user_service.py để cải thiện performance",
                        "estimated_effort": "2-3 days"
                    },
                    {
                        "priority": "Medium", 
                        "title": "Tăng test coverage",
                        "description": "Thêm unit tests cho edge cases, target 90%+",
                        "estimated_effort": "1 week"
                    }
                ],
                "risk_assessment": {
                    "overall_risk": "Low",
                    "technical_debt": "Moderate",
                    "maintainability_risk": "Low"
                }
            }
            
            logger.info(f"[LLM Services] Sinh được {len(llm_insights['recommendations'])} recommendations")
            
            return {
                "analysis_results": {
                    **state.get("analysis_results", {}),
                    "llm_insights": llm_insights
                },
                "next_action": "synthesis_reporting"
            }
            
        except Exception as e:
            logger.error(f"[LLM Services] Lỗi: {str(e)}")
            return {
                "errors": state.get("errors", []) + [f"LLM Services Error: {str(e)}"],
                "next_action": "error_handler"
            }
    
    def synthesis_reporting_node(self, state: CodeScanState) -> Dict[str, Any]:
        """
        Agent Synthesis Reporting - Tổng hợp báo cáo cuối cùng.
        
        Args:
            state: Current state của graph
            
        Returns:
            Dict với updates cho state
        """
        logger.info(f"[Synthesis Reporting] Bắt đầu tổng hợp báo cáo cho task {state['task_id']}")
        
        try:
            # Tổng hợp tất cả kết quả
            final_report = {
                "task_id": state["task_id"],
                "repository": state.get("repository"),
                "analysis_timestamp": datetime.now().isoformat(),
                "metadata": state.get("metadata", {}),
                "analysis_results": state.get("analysis_results", {}),
                "knowledge_graph_summary": {
                    "entities_count": state.get("knowledge_graph", {}).get("metrics", {}).get("total_entities", 0),
                    "relationships_count": state.get("knowledge_graph", {}).get("metrics", {}).get("total_relationships", 0)
                },
                "executive_summary": state.get("analysis_results", {}).get("llm_insights", {}).get("executive_summary", ""),
                "recommendations": state.get("analysis_results", {}).get("llm_insights", {}).get("recommendations", []),
                "completion_status": "success"
            }
            
            logger.info(f"[Synthesis Reporting] Hoàn thành báo cáo cho task {state['task_id']}")
            
            return {
                "analysis_results": {
                    **state.get("analysis_results", {}),
                    "final_report": final_report
                },
                "status": TaskStatus.COMPLETED,
                "next_action": None,
                "responses": state.get("responses", []) + [
                    f"Project review completed successfully. Overall score: {state.get('analysis_results', {}).get('code_analysis', {}).get('code_quality', {}).get('overall_score', 'N/A')}"
                ]
            }
            
        except Exception as e:
            logger.error(f"[Synthesis Reporting] Lỗi: {str(e)}")
            return {
                "errors": state.get("errors", []) + [f"Synthesis Reporting Error: {str(e)}"],
                "status": TaskStatus.FAILED,
                "next_action": "error_handler"
            }
    
    def error_handler_node(self, state: CodeScanState) -> Dict[str, Any]:
        """
        Node xử lý lỗi và recovery.
        
        Args:
            state: Current state với errors
            
        Returns:
            Dict với error handling results
        """
        logger.error(f"[Error Handler] Xử lý lỗi cho task {state['task_id']}")
        
        errors = state.get("errors", [])
        
        # Log all errors
        for error in errors:
            logger.error(f"Task {state['task_id']} error: {error}")
        
        # Tạo error report
        error_report = {
            "task_id": state["task_id"],
            "error_timestamp": datetime.now().isoformat(),
            "errors": errors,
            "recovery_attempted": False,
            "suggestions": [
                "Check repository access permissions",
                "Verify network connectivity",
                "Review configuration settings"
            ]
        }
        
        return {
            "status": TaskStatus.FAILED,
            "analysis_results": {
                **state.get("analysis_results", {}),
                "error_report": error_report
            },
            "responses": state.get("responses", []) + [
                f"Task failed with {len(errors)} errors. Please check the error report for details."
            ]
        }
    
    # Conditional edge functions
    def check_data_acquisition_success(self, state: CodeScanState) -> str:
        """Check nếu data acquisition thành công."""
        if state.get("code_files") and len(state.get("code_files", [])) > 0:
            return "continue"
        return "error"
    
    def check_code_analysis_success(self, state: CodeScanState) -> str:
        """Check nếu code analysis thành công."""
        analysis_results = state.get("analysis_results", {})
        if "code_analysis" in analysis_results:
            return "continue"
        return "error"

# Factory function để tạo graph instance
def create_project_review_graph(**kwargs) -> ProjectReviewGraph:
    """
    Factory function để tạo ProjectReviewGraph instance.
    
    Args:
        **kwargs: Arguments cho graph initialization
        
    Returns:
        ProjectReviewGraph: Configured graph instance
    """
    return ProjectReviewGraph(**kwargs) 