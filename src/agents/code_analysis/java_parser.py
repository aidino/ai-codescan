import threading
from typing import Optional
#!/usr/bin/env python3
"""
Java Code Analysis Agent - Bridge to CKG Operations JavaParserAgent

Bridge class integrating CKG Operations JavaParserAgent functionality
với Code Analysis workflows. Provides StaticAnalysisIntegratorAgent
compatible interface cho Java code analysis.
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
    
    from agents.ckg_operations.java_parser import JavaParserAgent, JavaNode, JavaParseInfo
    from agents.ckg_operations.code_parser_coordinator import ParsedFile
    CKG_AVAILABLE = True
    logger.info("CKG Operations JavaParserAgent available")
except ImportError as e:
    logger.warning(f"CKG Operations JavaParserAgent not available: {e}")
    CKG_AVAILABLE = False
    JavaParserAgent = None
    JavaNode = None
    JavaParseInfo = None
    ParsedFile = None

# Local imports
from .static_analysis_integrator import Finding, SeverityLevel, FindingType


@dataclass
class JavaCodeElement:
    """Represents a Java code element extracted from analysis."""
    element_type: str  # 'class', 'interface', 'method', 'field', 'package'
    name: str
    full_qualified_name: str
    file_path: str
    line_number: int
    end_line_number: Optional[int] = None
    modifiers: List[str] = field(default_factory=list)
    parent_element: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JavaAnalysisResult:
    """Result từ Java code analysis."""
    project_path: str
    files_analyzed: int
    total_elements: int
    elements_by_type: Dict[str, int] = field(default_factory=dict)
    code_elements: List[JavaCodeElement] = field(default_factory=list)
    parse_errors: List[str] = field(default_factory=list)
    analysis_time_seconds: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


class JavaCodeAnalysisAgent:
    """
    Java Code Analysis Agent - Bridge to CKG Operations.
    
    Provides code analysis functionality for Java projects by bridging
    to the comprehensive CKG Operations JavaParserAgent while maintaining
    compatibility with StaticAnalysisIntegratorAgent interface.
    
    Features:
    - AST-based Java code parsing
    - Code element extraction (classes, methods, fields, etc.)
    - Project structure analysis
    - Error handling và graceful degradation
    - Performance tracking
    """
    
    _instance: Optional['JavaCodeAnalysisAgent'] = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(JavaCodeAnalysisAgent, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, javaparser_jar_path: Optional[str] = None):
        """
        Initialize Java Code Analysis Agent.
        
        Args:
            javaparser_jar_path: Optional path to JavaParser JAR file.
                                If None, will use CKG agent's auto-download.
        """
        self.javaparser_jar_path = javaparser_jar_path
        self._ckg_parser: Optional[JavaParserAgent] = None
        self._capabilities = self._initialize_capabilities()
        
        # Initialize CKG parser if available
        if CKG_AVAILABLE:
            try:
                self._ckg_parser = JavaParserAgent(javaparser_jar_path)
                logger.info("JavaCodeAnalysisAgent initialized với CKG integration")
            except Exception as e:
                logger.error(f"Failed to initialize CKG JavaParserAgent: {e}")
                self._ckg_parser = None
        else:
            logger.warning("JavaCodeAnalysisAgent initialized in fallback mode")
    
    def _initialize_capabilities(self) -> Dict[str, bool]:
        """Initialize và return agent capabilities."""
        if CKG_AVAILABLE:
            return {
                "parse_classes": True,
                "parse_methods": True,
                "parse_fields": True,
                "parse_annotations": True,
                "parse_generics": True,
                "static_analysis": True,
                "ast_extraction": True,
                "ckg_integration": True,
                "placeholder": False
            }
        else:
            return {
                "parse_classes": False,
                "parse_methods": False,
                "parse_fields": False,
                "parse_annotations": False,
                "parse_generics": False,
                "static_analysis": False,
                "ast_extraction": False,
                "ckg_integration": False,
                "placeholder": True
            }
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Get parser capabilities."""
        return self._capabilities.copy()
    
    def is_available(self) -> bool:
        """Check if Java analysis is available."""
        return self._ckg_parser is not None
    
    def analyze_java_project(self, project_path: str) -> JavaAnalysisResult:
        """
        Analyze entire Java project.
        
        Args:
            project_path: Path to Java project root
            
        Returns:
            JavaAnalysisResult: Comprehensive analysis results
        """
        start_time = time.time()
        
        if not self.is_available():
            return JavaAnalysisResult(
                project_path=project_path,
                files_analyzed=0,
                total_elements=0,
                analysis_time_seconds=time.time() - start_time,
                success=False,
                error_message="Java analysis not available - CKG parser not initialized"
            )
        
        try:
            # Find Java files
            java_files = self._find_java_files(project_path)
            
            if not java_files:
                logger.info(f"No Java files found in {project_path}")
                return JavaAnalysisResult(
                    project_path=project_path,
                    files_analyzed=0,
                    total_elements=0,
                    analysis_time_seconds=time.time() - start_time,
                    success=True
                )
            
            # Parse Java files using CKG parser or fallback
            if self._ckg_parser is not None:
                try:
                    parsed_files = self._ckg_parser.parse_java_files(java_files)
                except Exception as e:
                    logger.warning(f"CKG parser failed: {e}, using fallback mode")
                    parsed_files = self._fallback_parse_java_files(java_files)
            else:
                logger.info("Using fallback parsing mode")
                parsed_files = self._fallback_parse_java_files(java_files)
            
            # Extract code elements
            code_elements = []
            parse_errors = []
            elements_by_type = {
                'packages': 0,
                'classes': 0,
                'interfaces': 0,
                'methods': 0,
                'fields': 0,
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
            
            result = JavaAnalysisResult(
                project_path=project_path,
                files_analyzed=len(java_files),
                total_elements=len(code_elements),
                elements_by_type=elements_by_type,
                code_elements=code_elements,
                parse_errors=parse_errors,
                analysis_time_seconds=analysis_time,
                success=True
            )
            
            logger.info(f"Java analysis completed: {len(java_files)} files, "
                       f"{len(code_elements)} elements, {analysis_time:.2f}s")
            
            return result
            
        except Exception as e:
            error_msg = f"Java analysis failed: {str(e)}"
            logger.error(error_msg)
            
            return JavaAnalysisResult(
                project_path=project_path,
                files_analyzed=0,
                total_elements=0,
                analysis_time_seconds=time.time() - start_time,
                success=False,
                error_message=error_msg
            )
    
    def parse_java_file(self, file_path: str) -> JavaAnalysisResult:
        """
        Parse single Java file.
        
        Args:
            file_path: Path to Java file
            
        Returns:
            JavaAnalysisResult: Analysis results for single file
        """
        start_time = time.time()
        
        if not self.is_available():
            return JavaAnalysisResult(
                project_path=os.path.dirname(file_path),
                files_analyzed=0,
                total_elements=0,
                analysis_time_seconds=time.time() - start_time,
                success=False,
                error_message="Java analysis not available"
            )
        
        try:
            # Parse single file
            relative_path = os.path.basename(file_path)
            parsed_files = self._ckg_parser.parse_java_files([(file_path, relative_path)])
            
            if not parsed_files:
                return JavaAnalysisResult(
                    project_path=os.path.dirname(file_path),
                    files_analyzed=0,
                    total_elements=0,
                    analysis_time_seconds=time.time() - start_time,
                    success=False,
                    error_message="No parsed results returned"
                )
            
            parsed_file = parsed_files[0]
            
            if not parsed_file.parse_success:
                return JavaAnalysisResult(
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
            
            return JavaAnalysisResult(
                project_path=os.path.dirname(file_path),
                files_analyzed=1,
                total_elements=len(code_elements),
                elements_by_type=elements_by_type,
                code_elements=code_elements,
                analysis_time_seconds=time.time() - start_time,
                success=True
            )
            
        except Exception as e:
            error_msg = f"Failed to parse Java file {file_path}: {str(e)}"
            logger.error(error_msg)
            
            return JavaAnalysisResult(
                project_path=os.path.dirname(file_path),
                files_analyzed=1,
                total_elements=0,
                analysis_time_seconds=time.time() - start_time,
                success=False,
                error_message=error_msg
            )
    
    def _find_java_files(self, project_path: str) -> List[Tuple[str, str]]:
        """
        Find all Java files trong project.
        
        Args:
            project_path: Project root path
            
        Returns:
            List of (file_path, relative_path) tuples
        """
        java_files = []
        project_path = Path(project_path)
        
        try:
            for java_file in project_path.rglob("*.java"):
                if java_file.is_file():
                    relative_path = str(java_file.relative_to(project_path))
                    java_files.append((str(java_file), relative_path))
            
            logger.info(f"Found {len(java_files)} Java files in {project_path}")
            return java_files
            
        except Exception as e:
            logger.error(f"Error finding Java files in {project_path}: {e}")
            return []
    
    def _extract_code_elements(self, parsed_file: ParsedFile) -> List[JavaCodeElement]:
        """
        Extract code elements từ parsed Java file.
        
        Args:
            parsed_file: ParsedFile from CKG parser
            
        Returns:
            List of JavaCodeElement objects
        """
        elements = []
        
        try:
            if not parsed_file.ast_tree:
                return elements
                
            ast_tree = parsed_file.ast_tree
            
            # Extract from parse_info if available
            if 'parse_info' in ast_tree:
                parse_info = ast_tree['parse_info']
                
                # Package
                if parse_info.get('package_name'):
                    elements.append(JavaCodeElement(
                        element_type='packages',
                        name=parse_info['package_name'],
                        full_qualified_name=parse_info['package_name'],
                        file_path=parsed_file.file_path,
                        line_number=1
                    ))
                
                # Imports
                for import_name in parse_info.get('imports', []):
                    elements.append(JavaCodeElement(
                        element_type='imports',
                        name=import_name.split('.')[-1],
                        full_qualified_name=import_name,
                        file_path=parsed_file.file_path,
                        line_number=1
                    ))
                
                # Classes
                for class_name in parse_info.get('classes', []):
                    package_name = parse_info.get('package_name', '')
                    full_name = f"{package_name}.{class_name}" if package_name else class_name
                    
                    elements.append(JavaCodeElement(
                        element_type='classes',
                        name=class_name,
                        full_qualified_name=full_name,
                        file_path=parsed_file.file_path,
                        line_number=1
                    ))
                
                # Interfaces
                for interface_name in parse_info.get('interfaces', []):
                    package_name = parse_info.get('package_name', '')
                    full_name = f"{package_name}.{interface_name}" if package_name else interface_name
                    
                    elements.append(JavaCodeElement(
                        element_type='interfaces',
                        name=interface_name,
                        full_qualified_name=full_name,
                        file_path=parsed_file.file_path,
                        line_number=1
                    ))
                
                # Methods
                for method_name in parse_info.get('methods', []):
                    elements.append(JavaCodeElement(
                        element_type='methods',
                        name=method_name,
                        full_qualified_name=method_name,
                        file_path=parsed_file.file_path,
                        line_number=1
                    ))
                
                # Fields
                for field_name in parse_info.get('fields', []):
                    elements.append(JavaCodeElement(
                        element_type='fields',
                        name=field_name,
                        full_qualified_name=field_name,
                        file_path=parsed_file.file_path,
                        line_number=1
                    ))
            
            # Extract from AST nodes if available
            if 'ast_nodes' in ast_tree:
                elements.extend(self._extract_from_ast_nodes(
                    ast_tree['ast_nodes'], parsed_file
                ))
        
        except Exception as e:
            logger.error(f"Error extracting elements from {parsed_file.relative_path}: {e}")
        
        return elements
    
    def _extract_from_ast_nodes(self, ast_nodes: Any, parsed_file: ParsedFile) -> List[JavaCodeElement]:
        """Extract elements from JavaNode AST structure."""
        elements = []
        
        try:
            if hasattr(ast_nodes, 'children') and ast_nodes.children:
                for child in ast_nodes.children:
                    if hasattr(child, 'node_type') and hasattr(child, 'name'):
                        element_type = self._map_node_type_to_element_type(child.node_type)
                        if element_type and child.name:
                            elements.append(JavaCodeElement(
                                element_type=element_type,
                                name=child.name,
                                full_qualified_name=child.name,
                                file_path=parsed_file.file_path,
                                line_number=getattr(child, 'start_line', 1),
                                end_line_number=getattr(child, 'end_line', None),
                                modifiers=getattr(child, 'modifiers', [])
                            ))
                    
                    # Recursively process children
                    elements.extend(self._extract_from_ast_nodes(child, parsed_file))
        
        except Exception as e:
            logger.debug(f"Error extracting from AST nodes: {e}")
        
        return elements
    
    def _map_node_type_to_element_type(self, node_type: str) -> Optional[str]:
        """Map JavaParser node types to our element types."""
        mapping = {
            'ClassOrInterfaceDeclaration': 'classes',
            'MethodDeclaration': 'methods',
            'FieldDeclaration': 'fields',
            'ConstructorDeclaration': 'methods',
            'EnumDeclaration': 'classes',
            'AnnotationDeclaration': 'classes'
        }
        return mapping.get(node_type)
    
    def _fallback_parse_java_files(self, java_files: List[Tuple[str, str]]) -> List:
        """
        Fallback parsing method khi CKG parser không available.
        
        Args:
            java_files: List of (file_path, relative_path) tuples
            
        Returns:
            List of mock ParsedFile objects với basic information
        """
        from dataclasses import dataclass
        from typing import Any
        
        @dataclass
        class MockParsedFile:
            file_path: str
            relative_path: str
            language: str = 'Java'
            ast_tree: Any = None
            parse_success: bool = True
            error_message: str = None
            nodes_count: int = 0
            lines_count: int = 0
        
        parsed_files = []
        
        for file_path, relative_path in java_files:
            try:
                # Count lines in file
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    lines_count = len(lines)
                
                # Simple fallback parsing - count basic Java elements
                nodes_count = 0
                for line in lines:
                    line = line.strip()
                    # Count basic Java elements
                    if any(keyword in line for keyword in ['class ', 'interface ', 'enum ', '@interface ']):
                        nodes_count += 1
                    elif line.startswith('import ') or line.startswith('package '):
                        nodes_count += 1
                    elif any(keyword in line for keyword in ['public ', 'private ', 'protected ']):
                        if any(method_keyword in line for method_keyword in ['void ', 'int ', 'String ', 'boolean ', 'double ', 'float ', 'long ', 'char ', 'byte ', 'short ']):
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
    
    def get_project_statistics(self, analysis_result: JavaAnalysisResult) -> Dict[str, Any]:
        """
        Get statistical information về Java project.
        
        Args:
            analysis_result: Analysis result from analyze_java_project
            
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
        
        # Add element density metrics
        if analysis_result.files_analyzed > 0:
            stats["avg_elements_per_file"] = analysis_result.total_elements / analysis_result.files_analyzed
        
        return stats


# Convenience function for external usage
def create_java_analysis_agent(javaparser_jar_path: Optional[str] = None) -> JavaCodeAnalysisAgent:
    """
    Factory function to create JavaCodeAnalysisAgent.
    
    Args:
        javaparser_jar_path: Optional path to JavaParser JAR
        
    Returns:
        JavaCodeAnalysisAgent instance
    """
    return JavaCodeAnalysisAgent(javaparser_jar_path)


# Legacy compatibility
class JavaParserAgent(JavaCodeAnalysisAgent):
    """Legacy compatibility class - use JavaCodeAnalysisAgent instead."""
    
    def __init__(self, *args, **kwargs):
        logger.warning("JavaParserAgent is deprecated - use JavaCodeAnalysisAgent instead")
        super().__init__(*args, **kwargs)


# Backward compatibility exports
JavaParseResult = JavaAnalysisResult 