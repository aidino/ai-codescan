#!/usr/bin/env python3
"""
AI CodeScan - Final System Validation Script

Comprehensive end-to-end validation của toàn bộ AI CodeScan system.
Kiểm tra integration giữa tất cả components.
"""

import os
import sys
import tempfile
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add src to path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root / "src"))

def test_core_imports():
    """Test import của tất cả core components."""
    print("\n📦 Testing Core Imports...")
    
    imports_to_test = {
        # Data Acquisition
        "GitOperationsAgent": "from agents.data_acquisition import GitOperationsAgent",
        "LanguageIdentifierAgent": "from agents.data_acquisition import LanguageIdentifierAgent",
        "DataPreparationAgent": "from agents.data_acquisition import DataPreparationAgent",
        
        # CKG Operations
        "CKGQueryInterfaceAgent": "from agents.ckg_operations import CKGQueryInterfaceAgent",
        "CodeParserCoordinatorAgent": "from agents.ckg_operations import CodeParserCoordinatorAgent",
        
        # Code Analysis
        "StaticAnalysisIntegratorAgent": "from agents.code_analysis import StaticAnalysisIntegratorAgent",
        "ArchitecturalAnalyzerAgent": "from agents.code_analysis import ArchitecturalAnalyzerAgent",
        "LLMAnalysisSupportAgent": "from agents.code_analysis import LLMAnalysisSupportAgent",
        
        # Synthesis & Reporting
        "FindingAggregatorAgent": "from agents.synthesis_reporting import FindingAggregatorAgent",
        "ReportGeneratorAgent": "from agents.synthesis_reporting import ReportGeneratorAgent"
    }
    
    import_results = {}
    for component_name, import_statement in imports_to_test.items():
        try:
            exec(import_statement)
            print(f"  ✅ {component_name}")
            import_results[component_name] = True
        except Exception as e:
            print(f"  ❌ {component_name}: {str(e)}")
            import_results[component_name] = False
    
    successful_imports = sum(import_results.values())
    total_imports = len(import_results)
    
    print(f"\n📊 Import Results: {successful_imports}/{total_imports} successful")
    return import_results

def create_comprehensive_test_project(temp_dir: Path) -> Path:
    """Tạo comprehensive test project với multiple languages."""
    project_dir = temp_dir / "comprehensive_test"
    project_dir.mkdir(exist_ok=True)
    
    # Python files với issues
    python_dir = project_dir / "python"
    python_dir.mkdir(exist_ok=True)
    
    (python_dir / "main.py").write_text('''#!/usr/bin/env python3
"""Main Python file với issues."""

import unused_import
import os

def very_long_function_name_that_exceeds_recommended_line_length_and_triggers_flake8():
    """Function với tên dài."""
    unused_var = "trigger warning"
    return unused_var

class TestClass:
    def method_without_self(cls):
        print("Missing self parameter")
    
    def __init__(self):
        self.value = 42

if __name__ == "__main__":
    test = TestClass()
    print(test.value)
''')
    
    # Java files cho testing (nếu có java)
    java_dir = project_dir / "java"
    java_dir.mkdir(exist_ok=True)
    
    (java_dir / "TestClass.java").write_text('''
public class TestClass {
    private String unusedField;
    
    public void methodWithoutJavadoc() {
        System.out.println("Missing javadoc");
    }
    
    public static void main(String[] args) {
        TestClass test = new TestClass();
        test.methodWithoutJavadoc();
    }
}
''')
    
    # Requirements.txt
    (project_dir / "requirements.txt").write_text("requests==2.28.0\nnumpy>=1.21.0\n")
    
    # Setup.py
    (project_dir / "setup.py").write_text('''from setuptools import setup, find_packages

setup(
    name="comprehensive-test",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "numpy>=1.21.0"
    ]
)
''')
    
    print(f"  📁 Created comprehensive test project: {project_dir}")
    return project_dir

def test_data_acquisition_workflow(project_path: Path):
    """Test Data Acquisition workflow."""
    print("\n🔄 Testing Data Acquisition Workflow...")
    
    try:
        from agents.data_acquisition import LanguageIdentifierAgent, DataPreparationAgent, RepositoryInfo
        
        # Test Language Identification
        print("  🔍 Testing LanguageIdentifierAgent...")
        lang_agent = LanguageIdentifierAgent()
        language_profile = lang_agent.identify_language(str(project_path))
        
        if language_profile:
            print(f"    ✅ Language identification successful")
            print(f"    📝 Primary language: {language_profile.primary_language}")
            print(f"    📊 Languages detected: {len(language_profile.languages)}")
        else:
            print(f"    ❌ Language identification failed")
            return {"language_identification": False}
        
        # Test Data Preparation
        print("  📋 Testing DataPreparationAgent...")
        data_agent = DataPreparationAgent()
        
        # Create proper RepositoryInfo instance for testing
        mock_repo_info = RepositoryInfo(
            url="file://" + str(project_path),
            local_path=str(project_path),
            default_branch="main",
            commit_hash="test123",
            author="test",
            commit_message="Test commit",
            languages=["Python", "Java"],
            size_mb=0.1,
            file_count=10
        )
        
        project_context = data_agent.prepare_project_context(
            repo_info=mock_repo_info,
            language_profile=language_profile
        )
        
        if project_context:
            print(f"    ✅ Data preparation successful")
            print(f"    📁 Files analyzed: {len(project_context.files)}")
            print(f"    📊 Directories: {len(project_context.directory_structure.common_directories)}")
        else:
            print(f"    ❌ Data preparation failed")
            return {"data_preparation": False}
        
        return {
            "language_identification": True,
            "data_preparation": True,
            "language_profile": language_profile,
            "project_context": project_context
        }
        
    except Exception as e:
        print(f"    ❌ Data Acquisition workflow failed: {str(e)}")
        return {"error": str(e)}

def test_static_analysis_workflow(project_path: Path):
    """Test Static Analysis workflow."""
    print("\n🔍 Testing Static Analysis Workflow...")
    
    try:
        from agents.code_analysis import StaticAnalysisIntegratorAgent
        
        agent = StaticAnalysisIntegratorAgent()
        
        # Test với Python tools only
        python_tools = ["flake8", "pylint", "mypy"]
        results = agent.run_analysis(str(project_path), python_tools)
        
        if results:
            print(f"    ✅ Static analysis successful")
            print(f"    🔧 Tools run: {len(results)}")
            
            total_findings = sum(r.total_findings for r in results.values() if r.success)
            print(f"    📊 Total findings: {total_findings}")
            
            # Test aggregation
            aggregated = agent.aggregate_results(results)
            print(f"    📈 Aggregation successful: {aggregated['summary']['total_findings']} findings")
            
            return {
                "success": True,
                "tools_run": len(results),
                "total_findings": total_findings,
                "successful_tools": [tool for tool, result in results.items() if result.success],
                "failed_tools": [tool for tool, result in results.items() if not result.success]
            }
        else:
            print(f"    ❌ Static analysis failed - no results")
            return {"success": False, "error": "No results"}
            
    except Exception as e:
        print(f"    ❌ Static analysis workflow failed: {str(e)}")
        return {"success": False, "error": str(e)}

def test_architectural_analysis_workflow(project_path: Path):
    """Test Architectural Analysis workflow."""
    print("\n🏗️ Testing Architectural Analysis Workflow...")
    
    try:
        from agents.code_analysis import ArchitecturalAnalyzerAgent
        
        # Test với hoặc không có CKG agent (mock mode)
        agent = ArchitecturalAnalyzerAgent(ckg_query_agent=None)
        
        result = agent.analyze_architecture(str(project_path))
        
        if result and result.success:
            print(f"    ✅ Architectural analysis successful")
            print(f"    🔄 Circular dependencies: {len(result.circular_dependencies)}")
            print(f"    📦 Unused elements: {len(result.unused_elements)}")
            print(f"    📊 Issues found: {len(result.issues)}")
            
            return {
                "success": True,
                "circular_dependencies": len(result.circular_dependencies),
                "unused_elements": len(result.unused_elements),
                "total_issues": len(result.issues)
            }
        else:
            error_msg = result.error_message if result else "No result returned"
            print(f"    ❌ Architectural analysis failed: {error_msg}")
            return {"success": False, "error": error_msg}
            
    except Exception as e:
        print(f"    ❌ Architectural analysis workflow failed: {str(e)}")
        return {"success": False, "error": str(e)}

def test_reporting_workflow():
    """Test Reporting workflow."""
    print("\n📊 Testing Reporting Workflow...")
    
    try:
        from agents.synthesis_reporting import FindingAggregatorAgent, ReportGeneratorAgent
        from agents.code_analysis import Finding, SeverityLevel, FindingType
        
        # Create mock findings
        mock_findings = [
            Finding(
                file_path="test.py",
                line_number=10,
                column_number=5,
                severity=SeverityLevel.HIGH,
                finding_type=FindingType.ERROR,
                rule_id="F401",
                message="Unused import",
                tool="flake8"
            ),
            Finding(
                file_path="test.py",
                line_number=20,
                column_number=1,
                severity=SeverityLevel.MEDIUM,
                finding_type=FindingType.STYLE,
                rule_id="E302",
                message="Expected 2 blank lines",
                tool="flake8"
            )
        ]
        
        # Test Finding Aggregation
        print("  📋 Testing FindingAggregatorAgent...")
        aggregator = FindingAggregatorAgent()
        
        # Use correct parameter name: findings_by_source instead of findings_by_tool
        aggregation_result = aggregator.aggregate_findings(
            findings_by_source={"flake8": mock_findings}
        )
        
        if aggregation_result.success:
            print(f"    ✅ Aggregation successful: {len(aggregation_result.aggregated_findings)} findings")
        else:
            print(f"    ❌ Aggregation failed: {aggregation_result.error_message}")
            return {"success": False, "error": aggregation_result.error_message}
        
        # Test Report Generation
        print("  📄 Testing ReportGeneratorAgent...")
        reporter = ReportGeneratorAgent()
        
        # Test text report with all required parameters
        text_report = reporter._generate_text_report(
            aggregation_result,
            "Test Project",
            {"include_all_findings": False}  # Add required options parameter
        )
        
        if text_report and len(text_report) > 100:  # Should be substantial
            print(f"    ✅ Text report generated: {len(text_report)} characters")
        else:
            print(f"    ⚠️ Text report too short: {len(text_report) if text_report else 0} characters")
        
        # Test JSON report  
        json_report = reporter._generate_json_report(
            aggregation_result,
            "Test Project",
            {}
        )
        
        if json_report:
            print(f"    ✅ JSON report generated")
        else:
            print(f"    ❌ JSON report failed")
        
        return {
            "success": True,
            "aggregated_findings": len(aggregation_result.aggregated_findings),
            "text_report_length": len(text_report) if text_report else 0,
            "json_report_success": bool(json_report)
        }
        
    except Exception as e:
        print(f"    ❌ Reporting workflow failed: {str(e)}")
        return {"success": False, "error": str(e)}

def main():
    """Main comprehensive validation."""
    print("🚀 AI CodeScan - Final System Validation")
    print("=" * 60)
    
    # Phase 1: Test imports
    import_results = test_core_imports()
    
    # Phase 2: Create test project
    print("\n📁 Creating comprehensive test project...")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = create_comprehensive_test_project(temp_path)
        
        # Phase 3: Test workflows
        data_acquisition_results = test_data_acquisition_workflow(project_path)
        static_analysis_results = test_static_analysis_workflow(project_path)
        architectural_results = test_architectural_analysis_workflow(project_path)
        reporting_results = test_reporting_workflow()
        
        # Phase 4: Overall summary
        print("\n📊 FINAL VALIDATION SUMMARY")
        print("=" * 50)
        
        # Import status
        successful_imports = sum(1 for r in import_results.values() if r)
        total_imports = len(import_results)
        print(f"📦 Imports: {successful_imports}/{total_imports} successful")
        
        # Workflow status
        workflows = {
            "Data Acquisition": data_acquisition_results.get("language_identification", False) and data_acquisition_results.get("data_preparation", False),
            "Static Analysis": static_analysis_results.get("success", False),
            "Architectural Analysis": architectural_results.get("success", False),
            "Reporting": reporting_results.get("success", False)
        }
        
        for workflow, success in workflows.items():
            status = "✅" if success else "❌"
            print(f"🔄 {workflow}: {status}")
        
        # Overall status
        successful_workflows = sum(workflows.values())
        total_workflows = len(workflows)
        overall_success = successful_workflows >= 3  # At least 3/4 workflows should work
        
        print(f"\n🎯 Overall Status: {successful_workflows}/{total_workflows} workflows successful")
        
        # Save results
        validation_results = {
            "timestamp": time.time(),
            "import_results": import_results,
            "workflow_results": {
                "data_acquisition": data_acquisition_results,
                "static_analysis": static_analysis_results,
                "architectural_analysis": architectural_results,
                "reporting": reporting_results
            },
            "summary": {
                "successful_imports": successful_imports,
                "total_imports": total_imports,
                "successful_workflows": successful_workflows,
                "total_workflows": total_workflows,
                "overall_success": overall_success,
                "validation_status": "PASS" if overall_success else "FAIL"
            }
        }
        
        results_file = project_root / "logs" / "final_system_validation.json"
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(validation_results, f, indent=2, default=str)
        
        print(f"\n📄 Results saved to: {results_file}")
        
        # Final verdict
        if overall_success:
            print("\n🎉 SYSTEM VALIDATION PASSED!")
            print("   AI CodeScan system is ready for production!")
        else:
            print("\n⚠️ SYSTEM VALIDATION ISSUES DETECTED!")
            print("   Some components need attention before production.")

if __name__ == "__main__":
    main() 