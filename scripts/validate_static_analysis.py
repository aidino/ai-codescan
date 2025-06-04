#!/usr/bin/env python3
"""
AI CodeScan - StaticAnalysisIntegratorAgent Validation Script

Script để validate và debug StaticAnalysisIntegratorAgent implementation.
Kiểm tra dependencies, tools, và functionality.
"""

import os
import sys
import subprocess
import tempfile
import json
from pathlib import Path
from typing import Dict, List, Any
import time

# Add src to path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root / "src"))

def test_tool_availability() -> Dict[str, bool]:
    """Test availability của các static analysis tools."""
    print("\n🔧 Kiểm tra tool availability...")
    
    tools = {
        "python": ["python", "--version"],
        "flake8": ["flake8", "--version"],
        "pylint": ["pylint", "--version"],
        "mypy": ["mypy", "--version"],
        "java": ["java", "-version"],
        "dart": ["dart", "--version"]
    }
    
    results = {}
    for tool, cmd in tools.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            available = result.returncode == 0
            results[tool] = available
            status = "✅" if available else "❌"
            print(f"  {status} {tool}: {'Available' if available else 'Not available'}")
            if available and result.stdout:
                version = result.stdout.strip().split('\n')[0]
                print(f"    Version: {version}")
        except Exception as e:
            results[tool] = False
            print(f"  ❌ {tool}: Error - {str(e)}")
    
    return results

def test_staticanalysis_import():
    """Test import StaticAnalysisIntegratorAgent."""
    print("\n📦 Kiểm tra import StaticAnalysisIntegratorAgent...")
    
    try:
        from agents.code_analysis import StaticAnalysisIntegratorAgent, Finding, AnalysisResult
        print("  ✅ Import StaticAnalysisIntegratorAgent successful")
        
        # Test initialization
        agent = StaticAnalysisIntegratorAgent()
        print("  ✅ StaticAnalysisIntegratorAgent initialization successful")
        print(f"  📝 Supported tools: {agent.supported_tools}")
        
        # Test configuration
        config = agent._get_default_config()
        print(f"  📝 Default configuration loaded: {len(config)} tools configured")
        
        return True, agent
        
    except Exception as e:
        print(f"  ❌ Import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

def create_test_python_project(temp_dir: Path) -> Path:
    """Tạo test Python project với known issues."""
    project_dir = temp_dir / "test_project"
    project_dir.mkdir(exist_ok=True)
    
    # Create test Python file với deliberate issues
    test_file = project_dir / "test_file.py"
    test_content = '''#!/usr/bin/env python3
"""Test file với various issues cho static analysis."""

import unused_import
import os

# Long line to trigger E501
def very_long_function_name_that_exceeds_the_recommended_line_length_limit_and_should_trigger_flake8_warning():
    pass

def unused_function():
    """Function không được sử dụng."""
    variable_not_used = "this will trigger warnings"
    return variable_not_used

class TestClass:
    def method_without_self(cls):  # Missing self parameter
        print("This method has issues")
    
    def unused_method(self):
        pass

if __name__ == "__main__":
    print("Test file")
'''
    
    test_file.write_text(test_content)
    
    # Create setup.py để make it a proper Python project
    setup_file = project_dir / "setup.py"
    setup_content = '''from setuptools import setup, find_packages

setup(
    name="test-project",
    version="0.1.0",
    packages=find_packages(),
)
'''
    setup_file.write_text(setup_content)
    
    print(f"  📁 Created test project: {project_dir}")
    print(f"  📄 Created test file: {test_file}")
    
    return project_dir

def test_staticanalysis_functionality(agent, project_path: Path, available_tools: Dict[str, bool]):
    """Test StaticAnalysisIntegratorAgent functionality."""
    print(f"\n⚙️ Testing StaticAnalysisIntegratorAgent functionality...")
    print(f"   Project path: {project_path}")
    
    # Determine which tools to test based on availability
    tools_to_test = []
    if available_tools.get("flake8", False):
        tools_to_test.append("flake8")
    if available_tools.get("pylint", False):
        tools_to_test.append("pylint")
    if available_tools.get("mypy", False):
        tools_to_test.append("mypy")
    
    if not tools_to_test:
        print("  ⚠️ No Python static analysis tools available for testing")
        return {}
    
    print(f"  🔍 Testing với tools: {tools_to_test}")
    
    results = {}
    
    # Test individual tools
    for tool in tools_to_test:
        print(f"\n  Testing {tool}...")
        try:
            start_time = time.time()
            result = agent._run_tool(tool, str(project_path))
            execution_time = time.time() - start_time
            
            results[tool] = {
                "success": result.success,
                "total_findings": result.total_findings,
                "execution_time": execution_time,
                "error_message": result.error_message
            }
            
            if result.success:
                print(f"    ✅ {tool} completed successfully")
                print(f"    📊 Files analyzed: {result.total_files_analyzed}")
                print(f"    🔍 Findings: {result.total_findings}")
                print(f"    ⏱️ Execution time: {execution_time:.2f}s")
                
                # Show sample findings
                if result.findings and len(result.findings) > 0:
                    print(f"    📝 Sample findings:")
                    for i, finding in enumerate(result.findings[:3]):  # Show first 3
                        print(f"      {i+1}. {finding.rule_id}: {finding.message}")
                        print(f"         📁 {finding.file_path}:{finding.line_number}")
            else:
                print(f"    ❌ {tool} failed: {result.error_message}")
                
        except Exception as e:
            print(f"    ❌ {tool} exception: {str(e)}")
            results[tool] = {
                "success": False,
                "error_message": str(e),
                "execution_time": 0,
                "total_findings": 0
            }
    
    # Test aggregate analysis
    if tools_to_test:
        print(f"\n  Testing aggregate analysis...")
        try:
            start_time = time.time()
            aggregate_results = agent.run_analysis(str(project_path), tools_to_test)
            execution_time = time.time() - start_time
            
            print(f"    ✅ Aggregate analysis completed")
            print(f"    📊 Tools run: {len(aggregate_results)}")
            print(f"    ⏱️ Total execution time: {execution_time:.2f}s")
            
            # Test aggregation
            if aggregate_results:
                aggregated = agent.aggregate_results(aggregate_results)
                print(f"    📈 Aggregated results:")
                print(f"      Total findings: {aggregated['summary']['total_findings']}")
                print(f"      Successful tools: {aggregated['summary']['successful_tools']}")
                print(f"      Failed tools: {aggregated['summary']['failed_tools']}")
                
                results["aggregate"] = {
                    "success": True,
                    "tools_run": len(aggregate_results),
                    "total_findings": aggregated['summary']['total_findings'],
                    "successful_tools": aggregated['summary']['successful_tools'],
                    "failed_tools": aggregated['summary']['failed_tools']
                }
        except Exception as e:
            print(f"    ❌ Aggregate analysis failed: {str(e)}")
            results["aggregate"] = {
                "success": False,
                "error_message": str(e)
            }
    
    return results

def main():
    """Main validation function."""
    print("🚀 AI CodeScan - StaticAnalysisIntegratorAgent Validation")
    print("=" * 60)
    
    # Phase 1: Check tool availability
    available_tools = test_tool_availability()
    
    # Phase 2: Test import và initialization
    import_success, agent = test_staticanalysis_import()
    if not import_success:
        print("\n❌ Cannot proceed without successful import")
        return
    
    # Phase 3: Create test project
    print("\n📁 Creating test Python project...")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = create_test_python_project(temp_path)
        
        # Phase 4: Test functionality
        test_results = test_staticanalysis_functionality(agent, project_path, available_tools)
        
        # Phase 5: Summary
        print("\n📊 VALIDATION SUMMARY")
        print("=" * 40)
        
        print(f"🔧 Tool Availability:")
        for tool, available in available_tools.items():
            status = "✅" if available else "❌"
            print(f"  {status} {tool}")
        
        print(f"\n⚙️ StaticAnalysis Tests:")
        if test_results:
            for tool, result in test_results.items():
                if result.get("success", False):
                    print(f"  ✅ {tool}: {result.get('total_findings', 0)} findings")
                else:
                    print(f"  ❌ {tool}: {result.get('error_message', 'Unknown error')}")
        else:
            print("  ⚠️ No tests run")
        
        # Save results
        results_file = project_root / "logs" / "static_analysis_validation.json"
        results_file.parent.mkdir(exist_ok=True)
        
        validation_results = {
            "timestamp": time.time(),
            "tool_availability": available_tools,
            "test_results": test_results,
            "summary": {
                "import_success": import_success,
                "tools_available": sum(available_tools.values()),
                "tools_tested": len([r for r in test_results.values() if r.get("success", False)]),
                "validation_status": "PASS" if import_success and any(r.get("success", False) for r in test_results.values()) else "FAIL"
            }
        }
        
        with open(results_file, 'w') as f:
            json.dump(validation_results, f, indent=2)
        
        print(f"\n📄 Results saved to: {results_file}")
        
        # Final status
        if validation_results["summary"]["validation_status"] == "PASS":
            print("\n🎉 VALIDATION PASSED: StaticAnalysisIntegratorAgent is working!")
        else:
            print("\n⚠️ VALIDATION ISSUES: StaticAnalysisIntegratorAgent has problems!")

if __name__ == "__main__":
    main() 