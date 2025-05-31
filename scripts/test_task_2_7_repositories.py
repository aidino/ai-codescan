#!/usr/bin/env python3
"""
Test Task 2.7: Tìm kiếm và chuẩn bị các project open-source (Java, Dart, Kotlin)

Script này sẽ:
1. Đề xuất danh sách các repository phù hợp cho testing
2. Phân tích repositories để tạo baseline
3. Test với AI CodeScan system để verify functionality
4. Document kết quả cho Task 2.7

Requirements:
- Repository có kích thước vừa phải (< 100 files, < 10000 lines)
- Có đủ issues để test static analysis
- Publicly accessible
- Active project với good structure
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add src to path để import các modules
script_dir = Path(__file__).parent
src_dir = script_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from agents.data_acquisition.git_operations import GitOperationsAgent
from agents.data_acquisition.language_identifier import LanguageIdentifierAgent
from agents.data_acquisition.data_preparation import DataPreparationAgent

class RepositoryCandidate:
    """Ứng viên repository cho testing."""
    
    def __init__(self, name: str, url: str, language: str, description: str, 
                 estimated_size: str, expected_issues: str):
        self.name = name
        self.url = url
        self.language = language
        self.description = description
        self.estimated_size = estimated_size
        self.expected_issues = expected_issues
        self.analysis_result: Optional[Dict[str, Any]] = None

class Task27RepositoryTester:
    """Main tester cho Task 2.7 repositories."""
    
    def __init__(self):
        self.git_agent = GitOperationsAgent()
        self.language_agent = LanguageIdentifierAgent()
        self.data_agent = DataPreparationAgent()
        self.temp_dir = Path("temp_repos/task_2_7")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
    def get_repository_candidates(self) -> List[RepositoryCandidate]:
        """Danh sách ứng viên repositories cho testing."""
        
        candidates = []
        
        # Java Projects
        candidates.extend([
            RepositoryCandidate(
                name="Spring PetClinic",
                url="https://github.com/spring-projects/spring-petclinic",
                language="Java",
                description="Spring Boot sample application - pet clinic management",
                estimated_size="~80 files, ~8000 lines",
                expected_issues="Style issues, potential complexity warnings"
            ),
            RepositoryCandidate(
                name="Guava Samples",
                url="https://github.com/google/guava",
                language="Java", 
                description="Google core libraries for Java (subset for testing)",
                estimated_size="Large (sẽ test subset)",
                expected_issues="High code quality, few issues expected"
            ),
            RepositoryCandidate(
                name="JUnit4",
                url="https://github.com/junit-team/junit4",
                language="Java",
                description="Testing framework - good for analysis testing",
                estimated_size="~200 files, ~15000 lines",
                expected_issues="Well-maintained, some legacy patterns"
            ),
            RepositoryCandidate(
                name="Simple Java Calculator",
                url="https://github.com/HouariZegai/Calculator",
                language="Java",
                description="Simple calculator implementation",
                estimated_size="~20 files, ~2000 lines", 
                expected_issues="Educational code, likely some style issues"
            )
        ])
        
        # Dart Projects
        candidates.extend([
            RepositoryCandidate(
                name="Flutter Samples",
                url="https://github.com/flutter/samples",
                language="Dart",
                description="Collection of Flutter sample apps",
                estimated_size="Multiple small projects",
                expected_issues="Varied quality, good for testing"
            ),
            RepositoryCandidate(
                name="Dart Pad",
                url="https://github.com/dart-lang/dart-pad", 
                language="Dart",
                description="Online Dart editor",
                estimated_size="~100 files, ~8000 lines",
                expected_issues="Production quality, fewer issues"
            ),
            RepositoryCandidate(
                name="Flutter Gallery",
                url="https://github.com/flutter/gallery",
                language="Dart",
                description="Material Design gallery app",
                estimated_size="~150 files, ~12000 lines",
                expected_issues="Demo app, some style variations"
            ),
            RepositoryCandidate(
                name="Dart HTTP",
                url="https://github.com/dart-lang/http",
                language="Dart", 
                description="HTTP client library",
                estimated_size="~50 files, ~5000 lines",
                expected_issues="Library code, high quality expected"
            )
        ])
        
        # Kotlin Projects  
        candidates.extend([
            RepositoryCandidate(
                name="Kotlin Examples",
                url="https://github.com/JetBrains/kotlin-examples",
                language="Kotlin",
                description="Official Kotlin example projects",
                estimated_size="Multiple small examples",
                expected_issues="Educational code, varied quality"
            ),
            RepositoryCandidate(
                name="KTOR Samples",
                url="https://github.com/ktorio/ktor-samples",
                language="Kotlin",
                description="Ktor framework samples",
                estimated_size="~80 files, ~6000 lines",
                expected_issues="Framework samples, good structure"
            ),
            RepositoryCandidate(
                name="Android Architecture Samples",
                url="https://github.com/android/architecture-samples",
                language="Kotlin",
                description="Android app architecture examples", 
                estimated_size="~200 files, ~15000 lines",
                expected_issues="Production examples, well-structured"
            ),
            RepositoryCandidate(
                name="Simple Kotlin Examples",
                url="https://github.com/SimpleMobileTools/Simple-Commons",
                language="Kotlin",
                description="Common utility classes for Android apps",
                estimated_size="~60 files, ~4000 lines",
                expected_issues="Utility library, moderate complexity"
            )
        ])
        
        return candidates
    
    def test_repository(self, candidate: RepositoryCandidate) -> Dict[str, Any]:
        """Test một repository candidate."""
        
        print(f"\n🔍 Testing Repository: {candidate.name}")
        print(f"   URL: {candidate.url}")
        print(f"   Language: {candidate.language}")
        print(f"   Description: {candidate.description}")
        
        result = {
            "name": candidate.name,
            "url": candidate.url,
            "language": candidate.language, 
            "success": False,
            "error": None,
            "analysis": None,
            "timing": {},
            "recommendations": []
        }
        
        try:
            start_time = time.time()
            local_path = None  # Initialize local_path
            
            # Step 1: Clone repository
            print(f"   📥 Cloning repository...")
            clone_start = time.time()
            repo_info = self.git_agent.clone_repository(
                candidate.url, 
                str(self.temp_dir / candidate.name.replace(" ", "_"))
            )
            result["timing"]["clone"] = time.time() - clone_start
            
            if not repo_info:
                result["error"] = "Failed to clone repository"
                return result
            
            local_path = repo_info.local_path
            
            # Step 2: Language identification
            print(f"   🔍 Analyzing language...")
            lang_start = time.time()
            language_profile = self.language_agent.identify_language(local_path)
            result["timing"]["language_analysis"] = time.time() - lang_start
            
            result["languages"] = {
                "primary": language_profile.primary_language,
                "all": [lang.name for lang in language_profile.languages],
                "frameworks": language_profile.frameworks,
                "project_type": language_profile.project_type,
                "confidence": language_profile.confidence_score
            }
            
            # Step 3: Data preparation 
            print(f"   📊 Preparing project context...")
            data_start = time.time()
            project_context = self.data_agent.prepare_project_context(
                candidate.url, local_path, candidate.language.lower()
            )
            result["timing"]["data_preparation"] = time.time() - data_start
            
            # Step 4: Analysis results
            result["analysis"] = {
                "languages_detected": {
                    lang.language: {
                        "file_count": lang.file_count,
                        "line_count": lang.line_count,
                        "confidence": lang.confidence,
                        "frameworks": lang.frameworks
                    } for lang in language_profile.languages
                },
                "project_info": {
                    "total_files": len(project_context.files),
                    "total_lines": sum(f.line_count for f in project_context.files if f.line_count),
                    "directories": len(project_context.directory_structure.subdirectories),
                    "config_files": len(project_context.metadata.dependencies)
                },
                "file_breakdown": {}
            }
            
            # Phân tích file types
            file_types = {}
            for file_info in project_context.files:
                ext = Path(file_info.path).suffix.lower()
                file_types[ext] = file_types.get(ext, 0) + 1
            result["analysis"]["file_breakdown"] = file_types
            
            # Recommendations
            total_files = result["analysis"]["project_info"]["total_files"]
            total_lines = result["analysis"]["project_info"]["total_lines"]
            
            if total_files > 100:
                result["recommendations"].append("⚠️  Large project - consider testing subset")
            if total_lines > 10000:
                result["recommendations"].append("⚠️  Many lines of code - may take longer to analyze")
            
            # Check target language presence
            target_lang_found = False
            for lang_info in language_profile.languages:
                if lang_info.language.lower() == candidate.language.lower():
                    if lang_info.confidence > 0.3:
                        target_lang_found = True
                        result["recommendations"].append(f"✅ Good {candidate.language} content detected")
                    break
            
            if not target_lang_found:
                result["recommendations"].append(f"⚠️  Limited {candidate.language} content detected")
            
            # Size recommendations
            if total_files < 20:
                result["recommendations"].append("ℹ️  Small project - good for quick testing")
            elif 20 <= total_files <= 80:
                result["recommendations"].append("✅ Medium size - ideal for comprehensive testing")
            
            result["timing"]["total"] = time.time() - start_time
            result["success"] = True
            
            print(f"   ✅ Analysis completed in {result['timing']['total']:.2f}s")
            print(f"   📁 Files: {total_files}, Lines: {total_lines}")
            
        except Exception as e:
            result["error"] = str(e)
            print(f"   ❌ Error: {e}")
            
        finally:
            # Cleanup
            if local_path and os.path.exists(local_path):
                try:
                    self.git_agent.cleanup_repository(local_path)
                except:
                    pass
        
        return result
    
    def run_analysis(self) -> Dict[str, Any]:
        """Chạy phân tích cho tất cả repository candidates."""
        
        print("🚀 Starting Task 2.7: Multi-language Repository Analysis")
        print("=" * 60)
        
        candidates = self.get_repository_candidates()
        results = {
            "total_candidates": len(candidates),
            "tested": 0,
            "successful": 0,
            "failed": 0,
            "results_by_language": {},
            "recommendations": [],
            "selected_repositories": []
        }
        
        # Group by language for analysis
        by_language = {}
        for candidate in candidates:
            if candidate.language not in by_language:
                by_language[candidate.language] = []
            by_language[candidate.language].append(candidate)
        
        # Test repositories by language
        for language, lang_candidates in by_language.items():
            print(f"\n📋 Testing {language} Repositories:")
            print("-" * 40)
            
            language_results = []
            successful_count = 0
            
            # Test first 2 repositories for each language (to save time)
            test_candidates = lang_candidates[:2]
            
            for candidate in test_candidates:
                results["tested"] += 1
                test_result = self.test_repository(candidate)
                language_results.append(test_result)
                
                if test_result["success"]:
                    results["successful"] += 1
                    successful_count += 1
                else:
                    results["failed"] += 1
            
            results["results_by_language"][language] = {
                "candidates_tested": len(test_candidates),
                "successful": successful_count,
                "results": language_results
            }
            
            # Select best repository for each language
            best_repo = None
            for test_result in language_results:
                if test_result["success"]:
                    if best_repo is None:
                        best_repo = test_result
                    else:
                        # Choose based on size and quality indicators
                        current_files = test_result["analysis"]["project_info"]["total_files"]
                        best_files = best_repo["analysis"]["project_info"]["total_files"]
                        
                        # Prefer medium-sized projects (20-80 files)
                        if 20 <= current_files <= 80 and not (20 <= best_files <= 80):
                            best_repo = test_result
            
            if best_repo:
                results["selected_repositories"].append(best_repo)
                print(f"   🏆 Selected for {language}: {best_repo['name']}")
        
        # Generate overall recommendations
        if results["successful"] >= 3:  # At least one per language
            results["recommendations"].append("✅ Found suitable repositories for all target languages")
        
        if results["failed"] > 0:
            results["recommendations"].append(f"⚠️  {results['failed']} repositories failed analysis")
        
        results["recommendations"].append("💡 Consider testing with smaller subsets of large repositories")
        results["recommendations"].append("🔧 Verify static analysis tools are properly installed")
        
        return results
    
    def print_summary(self, results: Dict[str, Any]):
        """In tóm tắt kết quả."""
        
        print("\n" + "=" * 60)
        print("📊 TASK 2.7 ANALYSIS SUMMARY")
        print("=" * 60)
        
        print(f"Total Candidates Tested: {results['tested']}")
        print(f"Successful Analyses: {results['successful']}")
        print(f"Failed Analyses: {results['failed']}")
        print(f"Success Rate: {results['successful']/results['tested']*100:.1f}%")
        
        print("\n🎯 SELECTED REPOSITORIES:")
        print("-" * 30)
        
        for repo in results["selected_repositories"]:
            analysis = repo["analysis"]
            print(f"\n📁 {repo['name']} ({repo['language']})")
            print(f"   URL: {repo['url']}")
            print(f"   Files: {analysis['project_info']['total_files']}")
            print(f"   Lines: {analysis['project_info']['total_lines']}")
            print(f"   Analysis Time: {repo['timing']['total']:.2f}s")
            
            # Show language detection
            for lang, info in analysis["languages_detected"].items():
                if info["confidence"] > 0.1:
                    print(f"   Language: {lang} ({info['confidence']:.1%} confidence)")
        
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 30)
        for rec in results["recommendations"]:
            print(f"   {rec}")
        
        print("\n🔗 READY FOR NEXT STEPS:")
        print("-" * 30)
        print("   📝 Document selected repositories in docs/TEST_REPOSITORIES_TASK_2_7.md")
        print("   🧪 Run full static analysis on selected repositories")
        print("   ⚡ Test CKG operations và architectural analysis")
        print("   📊 Compare with manual analysis baselines")


def main():
    """Main function."""
    
    try:
        tester = Task27RepositoryTester()
        results = tester.run_analysis()
        tester.print_summary(results)
        
        # Save results to file
        output_file = Path("logs/task_2_7_repository_analysis.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Results saved to: {output_file}")
        print("\n🎉 Task 2.7 Repository Analysis Completed Successfully!")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during Task 2.7 analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main()) 