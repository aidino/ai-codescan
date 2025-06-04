#!/usr/bin/env python3
"""
Dart Code Analysis Agent - Bridge to CKG Operations DartParserAgent

Bridge class integrating CKG Operations DartParserAgent functionality
với Code Analysis workflows. Provides StaticAnalysisIntegratorAgent
compatible interface cho Dart code analysis.
"""

import os
import sys
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import time
from loguru import logger

# Import CKG Operations components
try:
    # Add path để import CKG components  
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    sys.path.insert(0, str(project_root))
    
    from agents.ckg_operations.dart_parser import DartParserAgent, DartNode, DartParseInfo
    from agents.ckg_operations.code_parser_coordinator import ParsedFile
    CKG_AVAILABLE = True
    logger.info("CKG Operations DartParserAgent available")
except ImportError as e:
    logger.warning(f"CKG Operations DartParserAgent not available: {e}")
    CKG_AVAILABLE = False
    DartParserAgent = None
    DartNode = None
    DartParseInfo = None
    ParsedFile = None

# Local imports
from .static_analysis_integrator import Finding, SeverityLevel, FindingType


@dataclass
class DartCodeElement:
    """Represents a Dart code element extracted from analysis."""
    element_type: str  # 'class', 'function', 'method', 'field', 'library', 'mixin'
    name: str
    full_qualified_name: str
    file_path: str
    line_number: int
    end_line_number: Optional[int] = None
    modifiers: List[str] = field(default_factory=list)
    parent_element: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DartAnalysisResult:
    """Result từ Dart code analysis."""
    project_path: str
    files_analyzed: int
    total_elements: int
    elements_by_type: Dict[str, int] = field(default_factory=dict)
    code_elements: List[DartCodeElement] = field(default_factory=list)
    parse_errors: List[str] = field(default_factory=list)
    analysis_time_seconds: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


class DartCodeAnalysisAgent:
    """
    Dart Code Analysis Agent - Bridge to CKG Operations.
    
    Provides code analysis functionality for Dart projects by bridging
    to the comprehensive CKG Operations DartParserAgent while maintaining  
    compatibility with StaticAnalysisIntegratorAgent interface.
    
    Features:
    - AST-based Dart code parsing
    - Code element extraction (classes, functions, methods, mixins, etc.)
    - Flutter/Dart project structure analysis
    - Error handling và graceful degradation
    - Performance tracking
    """
    
    def __init__(self, dart_sdk_path: Optional[str] = None):
        """
        Initialize Dart Code Analysis Agent.
        
        Args:
            dart_sdk_path: Optional path to Dart SDK directory.
                          If None, will use CKG agent's auto-detection.
        """
        self.dart_sdk_path = dart_sdk_path
        self._ckg_parser: Optional[DartParserAgent] = None
        self._capabilities = self._initialize_capabilities()
        
        # Initialize CKG parser if available (temporarily disabled due to infinite recursion issue)
        # Disable CKG integration until recursion issues are resolved
        # Force fallback mode for stability
        self._ckg_parser = None
        logger.warning("DartCodeAnalysisAgent initialized in fallback mode (CKG integration disabled due to recursion issues)")
    
    def _initialize_capabilities(self) -> Dict[str, bool]:
        """Initialize và return agent capabilities."""
        # Force fallback capabilities since CKG integration is disabled
        return {
            "parse_classes": True,  # Basic fallback parsing
            "parse_functions": True,
            "parse_methods": False,  # Limited in fallback mode
            "parse_mixins": False,
            "parse_enums": False,
            "parse_extensions": False,
            "parse_libraries": False,
            "static_analysis": False,
            "ast_extraction": False,
            "flutter_support": True,  # Basic detection still works
            "ckg_integration": False,  # Explicitly disabled
            "placeholder": False,
            "fallback_mode": True  # Add indication of fallback mode
        }
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Get parser capabilities."""
        return self._capabilities.copy()
    
    def is_available(self) -> bool:
        """Check if Dart analysis is available."""
        return self._ckg_parser is not None
    
    def analyze_dart_project(self, project_path: str) -> DartAnalysisResult:
        """
        Analyze entire Dart project.
        
        Args:
            project_path: Path to Dart project root
            
        Returns:
            DartAnalysisResult: Comprehensive analysis results
        """
        start_time = time.time()
        
        if not self.is_available():
            return DartAnalysisResult(
                project_path=project_path,
                files_analyzed=0,
                total_elements=0,
                analysis_time_seconds=time.time() - start_time,
                success=False,
                error_message="Dart analysis not available - CKG parser not initialized"
            )
        
        try:
            # Find Dart files
            dart_files = self._find_dart_files(project_path)
            
            if not dart_files:
                logger.info(f"No Dart files found in {project_path}")
                return DartAnalysisResult(
                    project_path=project_path,
                    files_analyzed=0,
                    total_elements=0,
                    analysis_time_seconds=time.time() - start_time,
                    success=True
                )
            
            # Parse Dart files using CKG parser or fallback
            if self._ckg_parser is not None:
                try:
                    parsed_files = self._ckg_parser.parse_dart_files(dart_files)
                except Exception as e:
                    logger.warning(f"CKG parser failed: {e}, using fallback mode")
                    parsed_files = self._fallback_parse_dart_files(dart_files)
            else:
                logger.info("Using fallback parsing mode")
                parsed_files = self._fallback_parse_dart_files(dart_files)
            
            # Extract code elements
            code_elements = []
            parse_errors = []
            elements_by_type = {
                'libraries': 0,
                'classes': 0,
                'functions': 0,
                'methods': 0,
                'fields': 0,
                'mixins': 0,
                'enums': 0,
                'extensions': 0,
                'imports': 0
            }
            
            for parsed_file in parsed_files:
                if parsed_file.parse_success:
                    elements = self._extract_code_elements(parsed_file)
                    code_elements.extend(elements)
                    
                    # Count elements by type
                    for element in elements:
                        element_type = element.element_type
                        if element_type in elements_by_type:
                            elements_by_type[element_type] += 1
                else:
                    error_msg = f"Parse failed for {parsed_file.relative_path}: {parsed_file.error_message}"
                    parse_errors.append(error_msg)
                    logger.warning(error_msg)
            
            analysis_time = time.time() - start_time
            
            result = DartAnalysisResult(
                project_path=project_path,
                files_analyzed=len(dart_files),
                total_elements=len(code_elements),
                elements_by_type=elements_by_type,
                code_elements=code_elements,
                parse_errors=parse_errors,
                analysis_time_seconds=analysis_time,
                success=True
            )
            
            logger.info(f"Dart analysis completed: {len(dart_files)} files, "
                       f"{len(code_elements)} elements, {analysis_time:.2f}s")
            
            return result
            
        except Exception as e:
            error_msg = f"Dart analysis failed: {str(e)}"
            logger.error(error_msg)
            
            return DartAnalysisResult(
                project_path=project_path,
                files_analyzed=0,
                total_elements=0,
                analysis_time_seconds=time.time() - start_time,
                success=False,
                error_message=error_msg
            )
    
    def parse_dart_file(self, file_path: str) -> DartAnalysisResult:
        """
        Parse single Dart file.
        
        Args:
            file_path: Path to Dart file
            
        Returns:
            DartAnalysisResult: Analysis results for single file
        """
        start_time = time.time()
        
        if not self.is_available():
            return DartAnalysisResult(
                project_path=os.path.dirname(file_path),
                files_analyzed=0,
                total_elements=0,
                analysis_time_seconds=time.time() - start_time,
                success=False,
                error_message="Dart analysis not available"
            )
        
        try:
            # Parse single file
            relative_path = os.path.basename(file_path)
            parsed_files = self._ckg_parser.parse_dart_files([(file_path, relative_path)])
            
            if not parsed_files:
                return DartAnalysisResult(
                    project_path=os.path.dirname(file_path),
                    files_analyzed=0,
                    total_elements=0,
                    analysis_time_seconds=time.time() - start_time,
                    success=False,
                    error_message="No parsed results returned"
                )
            
            parsed_file = parsed_files[0]
            
            if not parsed_file.parse_success:
                return DartAnalysisResult(
                    project_path=os.path.dirname(file_path),
                    files_analyzed=1,
                    total_elements=0,
                    parse_errors=[parsed_file.error_message or "Unknown parse error"],
                    analysis_time_seconds=time.time() - start_time,
                    success=False,
                    error_message=parsed_file.error_message
                )
            
            # Extract elements
            code_elements = self._extract_code_elements(parsed_file)
            
            # Count by type
            elements_by_type = {}
            for element in code_elements:
                element_type = element.element_type
                elements_by_type[element_type] = elements_by_type.get(element_type, 0) + 1
            
            return DartAnalysisResult(
                project_path=os.path.dirname(file_path),
                files_analyzed=1,
                total_elements=len(code_elements),
                elements_by_type=elements_by_type,
                code_elements=code_elements,
                analysis_time_seconds=time.time() - start_time,
                success=True
            )
            
        except Exception as e:
            error_msg = f"Failed to parse Dart file {file_path}: {str(e)}"
            logger.error(error_msg)
            
            return DartAnalysisResult(
                project_path=os.path.dirname(file_path),
                files_analyzed=1,
                total_elements=0,
                analysis_time_seconds=time.time() - start_time,
                success=False,
                error_message=error_msg
            )
    
    def _find_dart_files(self, project_path: str) -> List[Tuple[str, str]]:
        """
        Find all Dart files trong project.
        
        Args:
            project_path: Project root path
            
        Returns:
            List of (file_path, relative_path) tuples
        """
        dart_files = []
        project_path = Path(project_path)
        
        try:
            for dart_file in project_path.rglob("*.dart"):
                if dart_file.is_file():
                    # Skip generated files and build directories
                    relative_path = str(dart_file.relative_to(project_path))
                    if not self._should_skip_dart_file(relative_path):
                        dart_files.append((str(dart_file), relative_path))
            
            logger.info(f"Found {len(dart_files)} Dart files in {project_path}")
            return dart_files
            
        except Exception as e:
            logger.error(f"Error finding Dart files in {project_path}: {e}")
            return []
    
    def _should_skip_dart_file(self, relative_path: str) -> bool:
        """Check if Dart file should be skipped during analysis."""
        skip_patterns = [
            '.dart_tool/',
            'build/',
            '.packages',
            'pubspec.lock',
            '.g.dart',  # Generated files
            '.freezed.dart',  # Freezed generated files
            '.gr.dart',  # Auto route generated files
        ]
        
        for pattern in skip_patterns:
            if pattern in relative_path:
                return True
        
        return False
    
    def _extract_code_elements(self, parsed_file: ParsedFile) -> List[DartCodeElement]:
        """
        Extract code elements từ parsed Dart file.
        
        Args:
            parsed_file: ParsedFile from CKG parser
            
        Returns:
            List of DartCodeElement objects
        """
        elements = []
        
        try:
            if not parsed_file.ast_tree or not isinstance(parsed_file.ast_tree, DartParseInfo):
                return elements
                
            dart_ast = parsed_file.ast_tree
            
            # Library
            if dart_ast.library:
                elements.append(DartCodeElement(
                    element_type='libraries',
                    name=dart_ast.library,
                    full_qualified_name=dart_ast.library,
                    file_path=parsed_file.file_path,
                    line_number=1
                ))
            
            # Imports
            for import_info in dart_ast.imports:
                import_name = import_info.split('/')[-1].replace('.dart', '') if '/' in import_info else import_info
                elements.append(DartCodeElement(
                    element_type='imports',
                    name=import_name,
                    full_qualified_name=import_info,
                    file_path=parsed_file.file_path,
                    line_number=1
                ))
            
            # Classes
            for class_node in dart_ast.classes:
                elements.append(DartCodeElement(
                    element_type='classes',
                    name=class_node.name or 'UnknownClass',
                    full_qualified_name=self._build_qualified_name(dart_ast.library, class_node.name),
                    file_path=parsed_file.file_path,
                    line_number=class_node.start_line or 1,
                    end_line_number=class_node.end_line,
                    modifiers=class_node.modifiers,
                    properties=class_node.properties
                ))
            
            # Functions (top-level)
            for function_node in dart_ast.functions:
                elements.append(DartCodeElement(
                    element_type='functions',
                    name=function_node.name or 'UnknownFunction',
                    full_qualified_name=self._build_qualified_name(dart_ast.library, function_node.name),
                    file_path=parsed_file.file_path,
                    line_number=function_node.start_line or 1,
                    end_line_number=function_node.end_line,
                    modifiers=function_node.modifiers,
                    properties=function_node.properties
                ))
            
            # Mixins
            for mixin_node in dart_ast.mixins:
                elements.append(DartCodeElement(
                    element_type='mixins',
                    name=mixin_node.name or 'UnknownMixin',
                    full_qualified_name=self._build_qualified_name(dart_ast.library, mixin_node.name),
                    file_path=parsed_file.file_path,
                    line_number=mixin_node.start_line or 1,
                    end_line_number=mixin_node.end_line,
                    modifiers=mixin_node.modifiers,
                    properties=mixin_node.properties
                ))
            
            # Enums
            for enum_node in dart_ast.enums:
                elements.append(DartCodeElement(
                    element_type='enums',
                    name=enum_node.name or 'UnknownEnum',
                    full_qualified_name=self._build_qualified_name(dart_ast.library, enum_node.name),
                    file_path=parsed_file.file_path,
                    line_number=enum_node.start_line or 1,
                    end_line_number=enum_node.end_line,
                    modifiers=enum_node.modifiers,
                    properties=enum_node.properties
                ))
            
            # Extensions
            for extension_node in dart_ast.extensions:
                elements.append(DartCodeElement(
                    element_type='extensions',
                    name=extension_node.name or 'UnknownExtension',
                    full_qualified_name=self._build_qualified_name(dart_ast.library, extension_node.name),
                    file_path=parsed_file.file_path,
                    line_number=extension_node.start_line or 1,
                    end_line_number=extension_node.end_line,
                    modifiers=extension_node.modifiers,
                    properties=extension_node.properties
                ))
            
            # Variables (top-level)
            for variable_node in dart_ast.variables:
                elements.append(DartCodeElement(
                    element_type='fields',
                    name=variable_node.name or 'UnknownVariable',
                    full_qualified_name=self._build_qualified_name(dart_ast.library, variable_node.name),
                    file_path=parsed_file.file_path,
                    line_number=variable_node.start_line or 1,
                    end_line_number=variable_node.end_line,
                    modifiers=variable_node.modifiers,
                    properties=variable_node.properties
                ))
        
        except Exception as e:
            logger.error(f"Error extracting elements from {parsed_file.relative_path}: {e}")
        
        return elements
    
    def _build_qualified_name(self, library: Optional[str], element_name: Optional[str]) -> str:
        """Build fully qualified name for Dart element."""
        if not element_name:
            return 'Unknown'
        
        if library:
            return f"{library}.{element_name}"
        return element_name
    
    def get_project_statistics(self, analysis_result: DartAnalysisResult) -> Dict[str, Any]:
        """
        Get statistical information về Dart project.
        
        Args:
            analysis_result: Analysis result from analyze_dart_project
            
        Returns:
            Dict with project statistics
        """
        if not analysis_result.success:
            return {
                "error": analysis_result.error_message,
                "analysis_available": False
            }
        
        stats = {
            "analysis_available": True,
            "files_analyzed": analysis_result.files_analyzed,
            "total_elements": analysis_result.total_elements,
            "elements_by_type": analysis_result.elements_by_type,
            "analysis_time_seconds": analysis_result.analysis_time_seconds,
            "parse_errors_count": len(analysis_result.parse_errors),
            "success_rate": (analysis_result.files_analyzed - len(analysis_result.parse_errors)) / max(analysis_result.files_analyzed, 1)
        }
        
        # Add Dart-specific metrics
        if analysis_result.files_analyzed > 0:
            stats["avg_elements_per_file"] = analysis_result.total_elements / analysis_result.files_analyzed
        
        # Check for Flutter project
        has_flutter = any('flutter' in element.properties.get('imports', []) 
                         for element in analysis_result.code_elements 
                         if element.element_type == 'imports')
        stats["is_flutter_project"] = has_flutter
        
        return stats
    
    def _fallback_parse_dart_files(self, dart_files: List[Tuple[str, str]]) -> List:
        """
        Fallback parsing method khi CKG parser không available.
        
        Args:
            dart_files: List of (file_path, relative_path) tuples
            
        Returns:
            List of mock ParsedFile objects với basic information
        """
        from dataclasses import dataclass
        from typing import Any
        
        @dataclass
        class MockParsedFile:
            file_path: str
            relative_path: str
            language: str = 'Dart'
            ast_tree: Any = None
            parse_success: bool = True
            error_message: str = None
            nodes_count: int = 0
            lines_count: int = 0
        
        parsed_files = []
        
        for file_path, relative_path in dart_files:
            try:
                # Count lines in file
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    lines_count = len(lines)
                
                # Simple fallback parsing - just count basic elements
                nodes_count = 0
                for line in lines:
                    line = line.strip()
                    # Count basic Dart elements
                    if any(keyword in line for keyword in ['class ', 'mixin ', 'enum ', 'extension ', 'typedef ']):
                        nodes_count += 1
                    elif line.startswith('import ') or line.startswith('export '):
                        nodes_count += 1
                    elif any(keyword in line for keyword in ['void ', 'int ', 'String ', 'double ', 'bool ']):
                        nodes_count += 1
                
                parsed_file = MockParsedFile(
                    file_path=file_path,
                    relative_path=relative_path,
                    parse_success=True,
                    nodes_count=nodes_count,
                    lines_count=lines_count
                )
                
                parsed_files.append(parsed_file)
                
            except Exception as e:
                logger.warning(f"Fallback parsing failed for {file_path}: {e}")
                parsed_file = MockParsedFile(
                    file_path=file_path,
                    relative_path=relative_path,
                    parse_success=False,
                    error_message=str(e),
                    lines_count=0
                )
                parsed_files.append(parsed_file)
        
        return parsed_files

    def is_flutter_project(self, project_path: str) -> bool:
        """
        Check if project is a Flutter project.
        
        Args:
            project_path: Path to project root
            
        Returns:
            bool: True if Flutter project detected
        """
        try:
            pubspec_path = Path(project_path) / 'pubspec.yaml'
            if pubspec_path.exists():
                with open(pubspec_path, 'r') as f:
                    content = f.read()
                    return 'flutter:' in content or 'flutter' in content
        except Exception as e:
            logger.debug(f"Error checking Flutter project: {e}")
        
        return False


# Convenience function for external usage
def create_dart_analysis_agent(dart_sdk_path: Optional[str] = None) -> DartCodeAnalysisAgent:
    """
    Factory function to create DartCodeAnalysisAgent.
    
    Args:
        dart_sdk_path: Optional path to Dart SDK
        
    Returns:
        DartCodeAnalysisAgent instance
    """
    return DartCodeAnalysisAgent(dart_sdk_path)


# Legacy compatibility
class DartParserAgent(DartCodeAnalysisAgent):
    """Legacy compatibility class - use DartCodeAnalysisAgent instead."""
    
    def __init__(self, *args, **kwargs):
        logger.warning("DartParserAgent is deprecated - use DartCodeAnalysisAgent instead")
        super().__init__(*args, **kwargs)


# Backward compatibility exports
DartParseResult = DartAnalysisResult 