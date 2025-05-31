#!/usr/bin/env python3
"""
API Documentation Generator và Docstring Coverage Checker

Script để generate comprehensive API documentation và check
docstring coverage cho AI CodeScan project.

Usage:
    python scripts/generate_docs.py --coverage
    python scripts/generate_docs.py --generate
    python scripts/generate_docs.py --all
"""

import os
import sys
import ast
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@dataclass
class DocstringInfo:
    """Information về docstring của một element."""
    name: str
    file_path: str
    line_number: int
    element_type: str  # class, function, method
    has_docstring: bool
    docstring_length: int
    is_public: bool


class DocstringAnalyzer:
    """
    Analyzer cho docstring coverage và quality.
    
    Scans Python files để identify classes, functions, và methods,
    checks docstring presence và quality metrics.
    """
    
    def __init__(self, source_dir: str = "src"):
        """
        Initialize analyzer.
        
        Args:
            source_dir: Directory to scan for Python files.
        """
        self.source_dir = Path(source_dir)
        self.docstring_info: List[DocstringInfo] = []
        
    def analyze_file(self, file_path: Path) -> None:
        """
        Analyze a single Python file for docstring coverage.
        
        Args:
            file_path: Path to Python file to analyze.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            self._visit_node(tree, file_path, [])
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
    
    def _visit_node(self, node: ast.AST, file_path: Path, context: List[str]) -> None:
        """
        Recursively visit AST nodes to find classes and functions.
        
        Args:
            node: AST node to visit.
            file_path: Path to file being analyzed.
            context: Context stack (class names, etc.)
        """
        if isinstance(node, ast.ClassDef):
            self._analyze_class(node, file_path, context)
            
        elif isinstance(node, ast.FunctionDef):
            element_type = "method" if context else "function"
            self._analyze_function(node, file_path, context, element_type)
            
        elif isinstance(node, ast.AsyncFunctionDef):
            element_type = "async_method" if context else "async_function"
            self._analyze_function(node, file_path, context, element_type)
        
        # Continue traversing
        for child in ast.iter_child_nodes(node):
            new_context = context.copy()
            if isinstance(node, ast.ClassDef):
                new_context.append(node.name)
            self._visit_node(child, file_path, new_context)
    
    def _analyze_class(self, node: ast.ClassDef, file_path: Path, context: List[str]) -> None:
        """
        Analyze class docstring.
        
        Args:
            node: Class AST node.
            file_path: Path to file.
            context: Context stack.
        """
        name = ".".join(context + [node.name])
        docstring = ast.get_docstring(node)
        is_public = not node.name.startswith('_')
        
        info = DocstringInfo(
            name=name,
            file_path=str(file_path.relative_to(self.source_dir)),
            line_number=node.lineno,
            element_type="class",
            has_docstring=docstring is not None,
            docstring_length=len(docstring) if docstring else 0,
            is_public=is_public
        )
        self.docstring_info.append(info)
    
    def _analyze_function(self, node: ast.FunctionDef, file_path: Path, 
                         context: List[str], element_type: str) -> None:
        """
        Analyze function/method docstring.
        
        Args:
            node: Function AST node.
            file_path: Path to file.
            context: Context stack.
            element_type: Type of element (function, method, etc.)
        """
        name = ".".join(context + [node.name])
        docstring = ast.get_docstring(node)
        is_public = not node.name.startswith('_')
        
        info = DocstringInfo(
            name=name,
            file_path=str(file_path.relative_to(self.source_dir)),
            line_number=node.lineno,
            element_type=element_type,
            has_docstring=docstring is not None,
            docstring_length=len(docstring) if docstring else 0,
            is_public=is_public
        )
        self.docstring_info.append(info)
    
    def scan_directory(self) -> None:
        """Scan source directory for Python files."""
        python_files = list(self.source_dir.rglob("*.py"))
        
        print(f"📁 Scanning {len(python_files)} Python files in {self.source_dir}")
        
        for file_path in python_files:
            # Skip __pycache__ và similar
            if "__pycache__" in str(file_path) or ".pyc" in str(file_path):
                continue
                
            self.analyze_file(file_path)
    
    def generate_coverage_report(self) -> Dict[str, any]:
        """
        Generate docstring coverage report.
        
        Returns:
            Dict containing coverage statistics.
        """
        if not self.docstring_info:
            self.scan_directory()
        
        total_elements = len(self.docstring_info)
        public_elements = [info for info in self.docstring_info if info.is_public]
        documented_elements = [info for info in self.docstring_info if info.has_docstring]
        documented_public = [info for info in public_elements if info.has_docstring]
        
        # Coverage by type
        by_type = {}
        for element_type in ["class", "function", "method", "async_function", "async_method"]:
            type_elements = [info for info in self.docstring_info if info.element_type == element_type]
            type_documented = [info for info in type_elements if info.has_docstring]
            type_public = [info for info in type_elements if info.is_public]
            type_public_documented = [info for info in type_public if info.has_docstring]
            
            by_type[element_type] = {
                "total": len(type_elements),
                "documented": len(type_documented),
                "public": len(type_public),
                "public_documented": len(type_public_documented),
                "coverage": len(type_documented) / len(type_elements) * 100 if type_elements else 0,
                "public_coverage": len(type_public_documented) / len(type_public) * 100 if type_public else 0
            }
        
        # Missing docstrings
        missing_public = [info for info in public_elements if not info.has_docstring]
        
        return {
            "total_elements": total_elements,
            "total_documented": len(documented_elements),
            "total_coverage": len(documented_elements) / total_elements * 100 if total_elements else 0,
            "public_elements": len(public_elements),
            "public_documented": len(documented_public),
            "public_coverage": len(documented_public) / len(public_elements) * 100 if public_elements else 0,
            "by_type": by_type,
            "missing_public": missing_public,
            "files_analyzed": len(set(info.file_path for info in self.docstring_info))
        }
    
    def print_coverage_report(self) -> None:
        """Print comprehensive coverage report."""
        stats = self.generate_coverage_report()
        
        print("\n" + "="*60)
        print("📊 DOCSTRING COVERAGE REPORT")
        print("="*60)
        
        print(f"\n📈 Overall Statistics:")
        print(f"   📂 Files analyzed: {stats['files_analyzed']}")
        print(f"   🔍 Total elements: {stats['total_elements']}")
        print(f"   📝 Documented: {stats['total_documented']}")
        print(f"   📊 Total coverage: {stats['total_coverage']:.1f}%")
        print(f"   🔓 Public elements: {stats['public_elements']}")
        print(f"   📝 Public documented: {stats['public_documented']}")
        print(f"   📊 Public coverage: {stats['public_coverage']:.1f}%")
        
        print(f"\n📋 Coverage by Element Type:")
        for element_type, data in stats['by_type'].items():
            if data['total'] > 0:
                print(f"   {element_type:15}: {data['documented']:3}/{data['total']:3} "
                      f"({data['coverage']:5.1f}%) | "
                      f"Public: {data['public_documented']:3}/{data['public']:3} "
                      f"({data['public_coverage']:5.1f}%)")
        
        # Missing docstrings
        if stats['missing_public']:
            print(f"\n❌ Missing Public Docstrings ({len(stats['missing_public'])}):")
            by_file = {}
            for info in stats['missing_public']:
                if info.file_path not in by_file:
                    by_file[info.file_path] = []
                by_file[info.file_path].append(info)
            
            for file_path, infos in sorted(by_file.items()):
                print(f"\n   📄 {file_path}:")
                for info in sorted(infos, key=lambda x: x.line_number):
                    print(f"      Line {info.line_number:3}: {info.element_type} {info.name}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if stats['public_coverage'] < 80:
            print("   • Focus on documenting public APIs (classes, functions, methods)")
        if stats['by_type']['class']['public_coverage'] < 90:
            print("   • Add docstrings to public classes")
        if stats['by_type']['function']['public_coverage'] < 80:
            print("   • Add docstrings to public functions")
        
        print("\n✅ Documentation quality is important for maintainability!")


def generate_api_docs() -> None:
    """Generate API documentation files."""
    print("📚 Generating API Documentation...")
    
    docs_dir = Path("docs/api")
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Create main API index
    index_content = """# AI CodeScan API Documentation

This directory contains auto-generated API documentation for AI CodeScan.

## Modules

### Core
- [Orchestrator](orchestrator.md) - Central workflow coordination
- [Authentication](auth.md) - User authentication và authorization
- [Logging](logging.md) - Debug logging và monitoring

### Agents
- [Data Acquisition](data_acquisition.md) - Repository cloning và preparation
- [CKG Operations](ckg_operations.md) - Code Knowledge Graph construction
- [Code Analysis](code_analysis.md) - Static analysis và linting
- [LLM Services](llm_services.md) - AI integration và services
- [Synthesis & Reporting](synthesis_reporting.md) - Result aggregation
- [Interaction & Tasking](interaction_tasking.md) - Web UI và user interaction

## Coverage Report

Run the following command to check docstring coverage:

```bash
python scripts/generate_docs.py --coverage
```
"""
    
    (docs_dir / "README.md").write_text(index_content)
    
    print(f"   ✅ Created API documentation index at {docs_dir / 'README.md'}")
    print("   📝 To complete documentation, run pydoc or sphinx on individual modules")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="AI CodeScan Documentation Tools")
    parser.add_argument("--coverage", action="store_true", 
                       help="Generate docstring coverage report")
    parser.add_argument("--generate", action="store_true",
                       help="Generate API documentation")
    parser.add_argument("--all", action="store_true",
                       help="Run all documentation tasks")
    parser.add_argument("--source-dir", default="src",
                       help="Source directory to analyze (default: src)")
    
    args = parser.parse_args()
    
    if args.all:
        args.coverage = True
        args.generate = True
    
    if not (args.coverage or args.generate):
        parser.print_help()
        return
    
    if args.coverage:
        analyzer = DocstringAnalyzer(args.source_dir)
        analyzer.print_coverage_report()
    
    if args.generate:
        generate_api_docs()
    
    print("\n🎉 Documentation tasks completed!")


if __name__ == "__main__":
    main() 