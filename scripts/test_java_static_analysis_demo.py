#!/usr/bin/env python3
"""
Demo script để test Java static analysis integration.

Script này demo integration của Checkstyle và PMD với StaticAnalysisIntegratorAgent.
"""

import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from agents.code_analysis.static_analysis_integrator import (
        StaticAnalysisIntegratorAgent, 
        AnalysisResult,
        SeverityLevel,
        FindingType
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Chạy script từ test environment thay vì direct import.")
    sys.exit(1)


def create_test_java_project() -> str:
    """Tạo Java project test."""
    temp_dir = tempfile.mkdtemp()
    
    # Create a Java file với intentional issues cho testing
    java_content = '''
package com.test.demo;

import java.util.List;
import java.util.ArrayList;
import java.io.File;  // Unused import

public class DemoClass {
    private static final String CONSTANT_VALUE = "test";
    private List<String> items;
    
    public DemoClass() {
        this.items = new ArrayList<>();
    }
    
    // Method với potential issues
    public void methodWithIssues() {
        String unusedVariable = "unused";  // Unused variable
        
        // Long if-else chain
        if (items.size() > 0) {
            System.out.println("Has items");
        } else if (items.size() == 0) {
            System.out.println("No items"); 
        } else if (items.size() < 0) {  // Impossible condition
            System.out.println("Negative items");
        }
        
        // Potential performance issue
        for (int i = 0; i < items.size(); i++) {
            String item = items.get(i);
            System.out.println("Item: " + item);
        }
    }
    
    // Method without proper javadoc
    public void addItem(String item) {
        if (item != null) {
            items.add(item);
        }
    }
    
    // Method với complexity issues
    public void complexMethod(int param1, String param2, boolean param3, List<String> param4) {
        if (param1 > 0) {
            if (param2 != null) {
                if (param3) {
                    if (param4 != null && param4.size() > 0) {
                        for (String s : param4) {
                            if (s.length() > 5) {
                                System.out.println("Long string: " + s);
                            } else {
                                System.out.println("Short string: " + s);
                            }
                        }
                    }
                }
            }
        }
    }
}
'''
    
    # Create directory structure
    package_dir = Path(temp_dir) / "src" / "main" / "java" / "com" / "test" / "demo"
    package_dir.mkdir(parents=True, exist_ok=True)
    
    # Write Java file
    with open(package_dir / "DemoClass.java", "w") as f:
        f.write(java_content)
    
    print(f"📁 Created test Java project at: {temp_dir}")
    print(f"📄 Java file: {package_dir / 'DemoClass.java'}")
    
    return temp_dir


def test_checkstyle_integration():
    """Test Checkstyle integration."""
    print("\n🔍 Testing Checkstyle Integration")
    print("=" * 50)
    
    project_path = create_test_java_project()
    
    try:
        # Initialize StaticAnalysisIntegratorAgent
        integrator = StaticAnalysisIntegratorAgent()
        
        # Check if Checkstyle is supported
        if "checkstyle" not in integrator.supported_tools:
            print("❌ Checkstyle không được support")
            return
        
        print("✅ Checkstyle supported")
        
        # Mock Checkstyle execution cho demo
        with patch('subprocess.run') as mock_subprocess:
            with patch.object(integrator, '_get_checkstyle_jar', return_value="/mock/checkstyle.jar"):
                
                # Mock successful Checkstyle output
                mock_result = Mock()
                mock_result.stdout = '''<?xml version="1.0" encoding="UTF-8"?>
<checkstyle version="10.12.4">
    <file name="''' + os.path.join(project_path, "src/main/java/com/test/demo/DemoClass.java") + '''">
        <error line="6" column="1" severity="warning" message="Unused import - java.io.File" source="com.puppycrawl.tools.checkstyle.checks.imports.UnusedImportsCheck"/>
        <error line="14" column="16" severity="warning" message="Unused local variable 'unusedVariable'" source="com.puppycrawl.tools.checkstyle.checks.coding.UnusedLocalVariableCheck"/>
        <error line="32" column="5" severity="info" message="Missing javadoc for method 'addItem'" source="com.puppycrawl.tools.checkstyle.checks.javadoc.MissingJavadocMethodCheck"/>
        <error line="38" column="5" severity="error" message="Method 'complexMethod' is too complex (cyclomatic complexity is 8)" source="com.puppycrawl.tools.checkstyle.checks.metrics.CyclomaticComplexityCheck"/>
    </file>
</checkstyle>'''
                mock_result.stderr = ""
                mock_result.returncode = 0
                mock_subprocess.return_value = mock_result
                
                # Run Checkstyle
                result = integrator.run_checkstyle(project_path)
                
                # Display results
                print(f"📊 Checkstyle Analysis Results:")
                print(f"   Success: {result.success}")
                print(f"   Files analyzed: {result.total_files_analyzed}")
                print(f"   Total findings: {result.total_findings}")
                print(f"   Execution time: {result.execution_time_seconds:.2f}s")
                
                print(f"\n📋 Findings Detail:")
                for i, finding in enumerate(result.findings, 1):
                    print(f"   {i}. {finding.file_path}:{finding.line_number}")
                    print(f"      Severity: {finding.severity.value}")
                    print(f"      Type: {finding.finding_type.value}")
                    print(f"      Rule: {finding.rule_id}")
                    print(f"      Message: {finding.message}")
                    print()
                
    except Exception as e:
        print(f"❌ Error testing Checkstyle: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(project_path)


def test_pmd_integration():
    """Test PMD integration."""
    print("\n🔍 Testing PMD Integration")
    print("=" * 50)
    
    project_path = create_test_java_project()
    
    try:
        # Initialize StaticAnalysisIntegratorAgent
        integrator = StaticAnalysisIntegratorAgent()
        
        # Check if PMD is supported
        if "pmd" not in integrator.supported_tools:
            print("❌ PMD không được support")
            return
        
        print("✅ PMD supported")
        
        # Mock PMD execution cho demo
        with patch('subprocess.run') as mock_subprocess:
            with patch.object(integrator, '_get_pmd_jar', return_value="/mock/pmd.jar"):
                
                # Mock successful PMD output
                mock_result = Mock()
                mock_result.stdout = '''<?xml version="1.0" encoding="UTF-8"?>
<pmd xmlns="http://pmd.sourceforge.net/report/2.0.0">
    <file name="''' + os.path.join(project_path, "src/main/java/com/test/demo/DemoClass.java") + '''">
        <violation beginline="6" begincolumn="1" priority="3" rule="UnusedImports" ruleset="java-imports">
            Avoid unused imports such as 'java.io.File'
        </violation>
        <violation beginline="14" begincolumn="16" priority="3" rule="UnusedLocalVariable" ruleset="java-basic">
            Avoid unused local variables such as 'unusedVariable'
        </violation>
        <violation beginline="24" begincolumn="9" priority="2" rule="ForLoopCanBeForeach" ruleset="java-performance">
            This for loop can be replaced by a foreach loop
        </violation>
        <violation beginline="38" begincolumn="5" priority="1" rule="ExcessiveParameterList" ruleset="java-design">
            Avoid really long parameter lists (4+ parameters)
        </violation>
        <violation beginline="38" begincolumn="5" priority="2" rule="CyclomaticComplexity" ruleset="java-design">
            The method 'complexMethod()' has a cyclomatic complexity of 8
        </violation>
    </file>
</pmd>'''
                mock_result.stderr = ""
                mock_result.returncode = 0
                mock_subprocess.return_value = mock_result
                
                # Run PMD
                result = integrator.run_pmd(project_path)
                
                # Display results
                print(f"📊 PMD Analysis Results:")
                print(f"   Success: {result.success}")
                print(f"   Files analyzed: {result.total_files_analyzed}")
                print(f"   Total findings: {result.total_findings}")
                print(f"   Execution time: {result.execution_time_seconds:.2f}s")
                
                print(f"\n📋 Findings Detail:")
                for i, finding in enumerate(result.findings, 1):
                    print(f"   {i}. {finding.file_path}:{finding.line_number}")
                    print(f"      Severity: {finding.severity.value}")
                    print(f"      Type: {finding.finding_type.value}")
                    print(f"      Rule: {finding.rule_id}")
                    print(f"      Message: {finding.message}")
                    print()
                
    except Exception as e:
        print(f"❌ Error testing PMD: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(project_path)


def test_integrated_analysis():
    """Test integrated analysis với cả Checkstyle và PMD."""
    print("\n🔍 Testing Integrated Java Analysis")
    print("=" * 50)
    
    project_path = create_test_java_project()
    
    try:
        # Initialize StaticAnalysisIntegratorAgent
        integrator = StaticAnalysisIntegratorAgent()
        
        # Mock both tools
        with patch('subprocess.run') as mock_subprocess:
            with patch.object(integrator, '_get_checkstyle_jar', return_value="/mock/checkstyle.jar"):
                with patch.object(integrator, '_get_pmd_jar', return_value="/mock/pmd.jar"):
                    
                    # Mock results cho cả 2 tools
                    def mock_subprocess_side_effect(*args, **kwargs):
                        mock_result = Mock()
                        if 'checkstyle' in str(args):
                            mock_result.stdout = '<?xml version="1.0" encoding="UTF-8"?><checkstyle version="10.12.4"></checkstyle>'
                        else:  # PMD
                            mock_result.stdout = '<?xml version="1.0" encoding="UTF-8"?><pmd xmlns="http://pmd.sourceforge.net/report/2.0.0"></pmd>'
                        mock_result.stderr = ""
                        mock_result.returncode = 0
                        return mock_result
                    
                    mock_subprocess.side_effect = mock_subprocess_side_effect
                    
                    # Run integrated analysis
                    results = integrator.run_analysis(project_path, tools=["checkstyle", "pmd"])
                    
                    print(f"📊 Integrated Analysis Results:")
                    for tool_name, result in results.items():
                        print(f"   {tool_name.upper()}:")
                        print(f"     Success: {result.success}")
                        print(f"     Files: {result.total_files_analyzed}")
                        print(f"     Findings: {result.total_findings}")
                        print(f"     Time: {result.execution_time_seconds:.2f}s")
                    
                    # Aggregate results
                    summary = integrator.aggregate_results(results)
                    print(f"\n📈 Summary:")
                    print(f"   Total tools run: {summary['total_tools_run']}")
                    print(f"   Successful tools: {summary['successful_tools']}")
                    print(f"   Total findings: {summary['total_findings']}")
                    print(f"   Total execution time: {summary['total_execution_time']:.2f}s")
                
    except Exception as e:
        print(f"❌ Error testing integrated analysis: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(project_path)


def main():
    """Main demo function."""
    print("🚀 Java Static Analysis Integration Demo")
    print("=" * 60)
    
    # Test individual tools
    test_checkstyle_integration()
    test_pmd_integration()
    
    # Test integrated analysis
    test_integrated_analysis()
    
    print("\n✅ Demo completed!")


if __name__ == "__main__":
    main() 