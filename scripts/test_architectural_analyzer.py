#!/usr/bin/env python3
"""
Demo script để test ArchitecturalAnalyzerAgent.

Script này test các tính năng phân tích kiến trúc cơ bản của ArchitecturalAnalyzerAgent.
"""

import sys
import os
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.code_analysis.architectural_analyzer import (
    ArchitecturalAnalyzerAgent,
    IssueType,
    SeverityLevel
)
from src.agents.ckg_operations.ckg_query_interface import CKGQueryInterfaceAgent


def create_mock_ckg_query_agent():
    """Tạo mock CKGQueryInterfaceAgent cho testing."""
    
    class MockCKGQueryAgent:
        def __init__(self):
            self.mock_dependencies = [
                {"source_file": "src/module_a.py", "target_file": "src/module_b.py"},
                {"source_file": "src/module_b.py", "target_file": "src/module_c.py"},
                {"source_file": "src/module_c.py", "target_file": "src/module_a.py"},  # Circular!
                {"source_file": "src/utils.py", "target_file": "src/helpers.py"},
            ]
            
            self.mock_unused_functions = [
                {"name": "unused_helper", "file_path": "src/utils.py", "line_number": 42},
                {"name": "legacy_function", "file_path": "src/old_module.py", "line_number": 15},
            ]
        
        def execute_query(self, query: str, parameters=None):
            """Mock execute_query method."""
            from src.agents.ckg_operations.ckg_query_interface import CKGQueryResult
            
            if "IMPORTS" in query or "CALLS" in query:
                return CKGQueryResult(
                    query=query,
                    results=self.mock_dependencies,
                    total_count=len(self.mock_dependencies),
                    execution_time_ms=50.0,
                    success=True
                )
            elif "Class" in query and "STARTS WITH '_'" in query:
                # Mock unused classes query
                mock_unused_classes = [
                    {"name": "UnusedClass", "file_path": "src/models.py", "line_number": 25}
                ]
                return CKGQueryResult(
                    query=query,
                    results=mock_unused_classes,
                    total_count=len(mock_unused_classes),
                    execution_time_ms=30.0,
                    success=True
                )
            else:
                return CKGQueryResult(
                    query=query,
                    results=[],
                    total_count=0,
                    execution_time_ms=10.0,
                    success=True
                )
        
        def get_unused_public_functions(self):
            """Mock get_unused_public_functions method."""
            from src.agents.ckg_operations.ckg_query_interface import CKGQueryResult
            
            return CKGQueryResult(
                query="get_unused_public_functions",
                results=self.mock_unused_functions,
                total_count=len(self.mock_unused_functions),
                execution_time_ms=40.0,
                success=True
            )
    
    return MockCKGQueryAgent()


def test_architectural_analyzer():
    """Test ArchitecturalAnalyzerAgent với mock data."""
    
    print("🔍 Testing ArchitecturalAnalyzerAgent...")
    print("=" * 60)
    
    # Tạo mock CKGQueryInterfaceAgent
    mock_ckg_agent = create_mock_ckg_query_agent()
    
    # Khởi tạo ArchitecturalAnalyzerAgent
    analyzer = ArchitecturalAnalyzerAgent(ckg_query_agent=mock_ckg_agent)
    
    # Test phân tích kiến trúc
    print("\n📊 Running architectural analysis...")
    result = analyzer.analyze_architecture("/mock/project/path")
    
    print(f"\n✅ Analysis completed: {result.success}")
    print(f"⏱️  Execution time: {result.execution_time_seconds:.3f} seconds")
    print(f"🔢 Total issues found: {result.total_issues}")
    
    # Hiển thị circular dependencies
    if result.circular_dependencies:
        print(f"\n🔄 Circular Dependencies ({len(result.circular_dependencies)}):")
        for i, cycle in enumerate(result.circular_dependencies, 1):
            print(f"   {i}. {cycle}")
    
    # Hiển thị unused elements
    if result.unused_elements:
        print(f"\n🗑️  Unused Public Elements ({len(result.unused_elements)}):")
        for i, element in enumerate(result.unused_elements, 1):
            print(f"   {i}. {element.element_type.title()}: {element.element_name}")
            print(f"      File: {element.file_path}")
            if element.line_number:
                print(f"      Line: {element.line_number}")
            if element.reason:
                print(f"      Reason: {element.reason}")
            print()
    
    # Hiển thị tất cả issues
    if result.issues:
        print(f"\n⚠️  All Issues ({len(result.issues)}):")
        for i, issue in enumerate(result.issues, 1):
            print(f"   {i}. [{issue.severity.value.upper()}] {issue.title}")
            print(f"      Type: {issue.issue_type.value}")
            print(f"      Description: {issue.description}")
            if issue.suggestion:
                print(f"      Suggestion: {issue.suggestion}")
            if issue.static_analysis_limitation:
                print(f"      Limitation: {issue.static_analysis_limitation}")
            print()
    
    # Hiển thị summary statistics
    print("\n📈 Summary Statistics:")
    stats = analyzer.get_summary_stats(result)
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for sub_key, sub_value in value.items():
                print(f"     - {sub_key}: {sub_value}")
        else:
            print(f"   {key}: {value}")
    
    # Hiển thị limitations
    print(f"\n⚠️  Analysis Limitations ({len(result.limitations)}):")
    for i, limitation in enumerate(result.limitations, 1):
        print(f"   {i}. {limitation}")
    
    print("\n" + "=" * 60)
    print("✅ ArchitecturalAnalyzerAgent test completed!")


def test_cycle_detection_algorithm():
    """Test thuật toán phát hiện cycle riêng biệt."""
    
    print("\n🔄 Testing cycle detection algorithm...")
    print("-" * 40)
    
    # Tạo analyzer
    analyzer = ArchitecturalAnalyzerAgent()
    
    # Test data với circular dependencies
    test_graph = {
        "A": {"B", "C"},
        "B": {"D"},
        "C": {"D"},
        "D": {"A"},  # Cycle: A -> B -> D -> A và A -> C -> D -> A
        "E": {"F"},
        "F": set(),  # No cycle
    }
    
    cycles = analyzer._find_cycles_in_graph(test_graph)
    
    print(f"Graph: {test_graph}")
    print(f"Cycles found: {len(cycles)}")
    for i, cycle in enumerate(cycles, 1):
        cycle_str = " -> ".join(cycle)
        print(f"   {i}. {cycle_str}")
    
    # Test empty graph
    empty_cycles = analyzer._find_cycles_in_graph({})
    print(f"\nEmpty graph cycles: {len(empty_cycles)}")
    
    # Test graph không có cycles
    acyclic_graph = {"A": {"B"}, "B": {"C"}, "C": set()}
    acyclic_cycles = analyzer._find_cycles_in_graph(acyclic_graph)
    print(f"Acyclic graph cycles: {len(acyclic_cycles)}")


if __name__ == "__main__":
    try:
        test_architectural_analyzer()
        test_cycle_detection_algorithm()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 