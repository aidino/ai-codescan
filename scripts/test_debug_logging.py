#!/usr/bin/env python3
"""
Test Debug Logging System.

Script để test và demonstrate debug logging capabilities
cho luồng phân tích repository trong AI CodeScan.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.logging import (
    DebugLogger, 
    debug_trace,
    log_repository_analysis_start,
    log_repository_analysis_end
)
from agents.data_acquisition.git_operations import GitOperationsAgent


@debug_trace(stage="TEST_SETUP")
def test_basic_logging():
    """Test basic debug logging functionality."""
    debug_logger = DebugLogger("test_basic_logging")
    
    debug_logger.log_step("Starting basic logging test", {
        "test_type": "basic_functionality",
        "expected_duration": "5 seconds"
    })
    
    # Test error logging
    try:
        raise ValueError("Test error for logging demonstration")
    except Exception as e:
        debug_logger.log_error(e, {"test_context": "intentional_error"})
    
    # Test performance metric
    debug_logger.log_performance_metric("test_metric", 1.23, "seconds")
    
    # Test data logging
    debug_logger.log_data("test_data", {
        "sample_key": "sample_value",
        "numbers": [1, 2, 3],
        "nested": {"inner": "value"}
    })
    
    debug_logger.log_session_summary()
    print("✅ Basic logging test completed")


@debug_trace(stage="INTEGRATION_TEST")
def test_git_operations_logging():
    """Test GitOperationsAgent với debug logging."""
    print("🔍 Testing GitOperationsAgent với debug logging...")
    
    # Create debug logger for this test
    debug_logger = DebugLogger("test_git_operations")
    debug_logger.set_repository_context("https://github.com/psf/requests")
    
    # Create GitOperationsAgent
    git_agent = GitOperationsAgent()
    git_agent._debug_logger = debug_logger
    
    try:
        # Test URL validation
        debug_logger.log_step("Testing URL validation", {
            "test_urls": [
                "https://github.com/psf/requests",
                "invalid-url",
                "https://gitlab.com/example/repo"
            ]
        })
        
        valid_url = "https://github.com/psf/requests"
        is_valid = git_agent._is_valid_git_url(valid_url)
        debug_logger.log_step("URL validation result", {
            "url": valid_url,
            "is_valid": is_valid
        })
        
        # Test repository name extraction
        repo_name = git_agent._extract_repo_name(valid_url)
        debug_logger.log_step("Repository name extraction", {
            "url": valid_url,
            "extracted_name": repo_name
        })
        
        # Note: We don't actually clone in this test to avoid network dependencies
        debug_logger.log_step("Skipping actual clone operation", {
            "reason": "avoid_network_dependencies",
            "would_clone": valid_url
        })
        
        print("✅ GitOperationsAgent logging test completed")
        
    except Exception as e:
        debug_logger.log_error(e, {"test_stage": "git_operations_test"})
        print(f"❌ GitOperationsAgent test failed: {e}")
    
    finally:
        debug_logger.log_session_summary()


@debug_trace(stage="WORKFLOW_SIMULATION")
def test_repository_analysis_workflow():
    """Simulate complete repository analysis workflow với debug logging."""
    print("🚀 Simulating complete repository analysis workflow...")
    
    repo_url = "https://github.com/example/test-repo"
    
    # Start repository analysis logging
    debug_logger = log_repository_analysis_start(repo_url, "workflow_simulation_test")
    
    try:
        # Stage 1: Data Acquisition
        debug_logger.set_analysis_stage("DATA_ACQUISITION")
        debug_logger.log_step("Starting data acquisition", {
            "repo_url": repo_url,
            "clone_depth": 1,
            "target_directory": "/tmp/test_repo"
        })
        time.sleep(0.5)  # Simulate work
        
        # Mock successful clone
        debug_logger.log_data("repository_clone_result", {
            "status": "success",
            "local_path": "/tmp/test_repo",
            "size_mb": 2.5,
            "file_count": 35,
            "languages_detected": ["Python", "JavaScript"]
        })
        
        # Stage 2: Language Identification
        debug_logger.set_analysis_stage("LANGUAGE_IDENTIFICATION")
        debug_logger.log_step("Starting language identification", {
            "files_to_analyze": 35,
            "supported_languages": ["Python", "JavaScript", "Java", "Dart"]
        })
        time.sleep(0.3)
        
        debug_logger.log_data("language_analysis_result", {
            "primary_language": "Python",
            "confidence": 0.92,
            "file_breakdown": {
                "python": 28,
                "javascript": 7
            },
            "frameworks_detected": ["Flask", "React"]
        })
        
        # Stage 3: Code Analysis
        debug_logger.set_analysis_stage("CODE_ANALYSIS")
        debug_logger.log_step("Starting static code analysis", {
            "tools": ["flake8", "pylint", "mypy"],
            "files_to_analyze": 28
        })
        time.sleep(0.8)
        
        debug_logger.log_data("static_analysis_result", {
            "total_issues": 47,
            "severity_breakdown": {
                "critical": 3,
                "major": 12,
                "minor": 22,
                "info": 10
            },
            "tool_results": {
                "flake8": {"issues": 25, "duration": 0.3},
                "pylint": {"issues": 18, "duration": 0.4},
                "mypy": {"issues": 4, "duration": 0.1}
            }
        })
        
        # Stage 4: CKG Operations
        debug_logger.set_analysis_stage("CKG_OPERATIONS")
        debug_logger.log_step("Building Code Knowledge Graph", {
            "parser": "AST",
            "nodes_to_create": ["File", "Function", "Class", "Import"],
            "estimated_complexity": "medium"
        })
        time.sleep(0.6)
        
        debug_logger.log_data("ckg_construction_result", {
            "nodes_created": 245,
            "relationships_created": 384,
            "node_breakdown": {
                "files": 35,
                "functions": 156,
                "classes": 38,
                "imports": 16
            },
            "complexity_metrics": {
                "avg_function_complexity": 3.2,
                "max_class_methods": 15,
                "circular_dependencies": 2
            }
        })
        
        # Stage 5: LLM Services  
        debug_logger.set_analysis_stage("LLM_SERVICES")
        debug_logger.log_step("Generating LLM insights", {
            "model": "gpt-4-turbo",
            "context_size": "medium",
            "tasks": ["code_explanation", "recommendations", "summary"]
        })
        time.sleep(0.4)
        
        debug_logger.log_data("llm_analysis_result", {
            "tokens_used": 1850,
            "cost_usd": 0.0925,
            "insights_generated": 12,
            "recommendation_categories": [
                "code_quality",
                "performance", 
                "security",
                "maintainability"
            ]
        })
        
        # Stage 6: Synthesis & Reporting
        debug_logger.set_analysis_stage("SYNTHESIS_REPORTING")
        debug_logger.log_step("Generating final report", {
            "report_format": "comprehensive",
            "sections": ["summary", "issues", "recommendations", "metrics"],
            "export_formats": ["json", "html", "pdf"]
        })
        time.sleep(0.2)
        
        debug_logger.log_data("final_report", {
            "total_analysis_time": 2.8,
            "quality_score": 78,
            "recommendation_priority": "medium",
            "actionable_items": 15,
            "report_size_kb": 156
        })
        
        # Log performance summary
        debug_logger.log_performance_metric("total_analysis_duration", 2.8, "seconds")
        debug_logger.log_performance_metric("files_per_second", 35/2.8, "files/sec")
        debug_logger.log_performance_metric("issues_found_rate", 47/35, "issues/file")
        
        print("✅ Repository analysis workflow simulation completed successfully")
        
    except Exception as e:
        debug_logger.log_error(e, {"workflow_stage": "simulation"})
        print(f"❌ Workflow simulation failed: {e}")
    
    finally:
        # End repository analysis logging
        log_repository_analysis_end()


def print_log_files_info():
    """Print information about generated log files."""
    print("\n📄 Debug Log Files Generated:")
    print("=" * 50)
    
    logs_dir = Path("logs/debug")
    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.log")) + list(logs_dir.glob("*.json"))
        
        for log_file in sorted(log_files):
            size_kb = log_file.stat().st_size / 1024
            print(f"📁 {log_file.name} ({size_kb:.1f} KB)")
            
            if log_file.suffix == ".log":
                # Show last few lines for preview
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        print(f"   Last entry: {lines[-1].strip() if lines else 'Empty'}")
                except:
                    print(f"   (Could not preview)")
    else:
        print("❌ No debug logs directory found")
    
    print("\n💡 Tips:")
    print("- Use 'tail -f logs/debug/debug_*.log' để follow logs real-time")
    print("- Check 'logs/debug/summary_*.json' cho session summaries")
    print("- Performance metrics trong 'logs/debug/performance_*.log'")


def main():
    """Main test function."""
    print("🧪 AI CodeScan Debug Logging Test Suite")
    print("=" * 60)
    
    try:
        # Test 1: Basic logging functionality
        print("\n1️⃣ Testing basic logging functionality...")
        test_basic_logging()
        
        # Test 2: GitOperationsAgent logging
        print("\n2️⃣ Testing GitOperationsAgent logging...")
        test_git_operations_logging()
        
        # Test 3: Complete workflow simulation
        print("\n3️⃣ Testing complete workflow simulation...")
        test_repository_analysis_workflow()
        
        # Show log files info
        print_log_files_info()
        
        print("\n🎉 All debug logging tests completed successfully!")
        print("\n📍 Check logs/debug/ directory cho detailed logs")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 