#!/usr/bin/env python3
"""
Kotlin Code Analysis Agent - Bridge to CKG Operations KotlinParserAgent

Bridge class integrating CKG Operations KotlinParserAgent functionality
với Code Analysis workflows. Provides StaticAnalysisIntegratorAgent
compatible interface cho Kotlin code analysis.
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
    
    from agents.ckg_operations.kotlin_parser import KotlinParserAgent, KotlinNode, KotlinParseInfo
    from agents.ckg_operations.code_parser_coordinator import ParsedFile
    CKG_AVAILABLE = True
    logger.info("CKG Operations KotlinParserAgent available")
except ImportError as e:
    logger.warning(f"CKG Operations KotlinParserAgent not available: {e}")
    CKG_AVAILABLE = False
    KotlinParserAgent = None
    KotlinNode = None
    KotlinParseInfo = None
    ParsedFile = None

# Local imports
from .static_analysis_integrator import Finding, SeverityLevel, FindingType


@dataclass
class KotlinCodeElement:
    """Represents a Kotlin code element extracted from analysis."""
    element_type: str  # 'class', 'interface', 'object', 'function', 'property', 'enum', 'data_class', 'sealed_class'
    name: str
    full_qualified_name: str
    file_path: str
    line_number: int
    end_line_number: Optional[int] = None
    modifiers: List[str] = field(default_factory=list)
    parent_element: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KotlinAnalysisResult:
    """Result từ Kotlin code analysis."""
    project_path: str
    files_analyzed: int
    total_elements: int
    elements_by_type: Dict[str, int] = field(default_factory=dict)
    code_elements: List[KotlinCodeElement] = field(default_factory=list)
    parse_errors: List[str] = field(default_factory=list)
    analysis_time_seconds: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


class KotlinCodeAnalysisAgent:
    """
    Kotlin Code Analysis Agent - Bridge to CKG Operations.
    
    Provides code analysis functionality for Kotlin projects by bridging
    to the comprehensive CKG Operations KotlinParserAgent while maintaining
    compatibility with StaticAnalysisIntegratorAgent interface.
    
    Features:
    - AST-based Kotlin code parsing
    - Code element extraction (classes, objects, functions, data classes, etc.)
    - Android/Kotlin project structure analysis
    - Error handling và graceful degradation
    - Performance tracking
    """
    
    def __init__(self, kotlinc_path: Optional[str] = None):
        """
        Initialize Kotlin Code Analysis Agent.
        
        Args:
            kotlinc_path: Optional path to kotlinc compiler.
                         If None, will use CKG agent's auto-detection.
        """
        self.kotlinc_path = kotlinc_path
        self._ckg_parser: Optional[KotlinParserAgent] = None
        self._capabilities = self._initialize_capabilities()
        
        # Initialize CKG parser if available
        if CKG_AVAILABLE:
            try:
                # CKG KotlinParserAgent doesn't accept arguments
                self._ckg_parser = KotlinParserAgent()
                logger.info("KotlinCodeAnalysisAgent initialized với CKG integration")
            except Exception as e:
                logger.error(f"Failed to initialize CKG KotlinParserAgent: {e}")
                self._ckg_parser = None
        else:
            logger.warning("KotlinCodeAnalysisAgent initialized in fallback mode")
    
    def _initialize_capabilities(self) -> Dict[str, bool]:
        """Initialize và return agent capabilities."""
        if CKG_AVAILABLE:
            return {
                "parse_classes": True,
                "parse_objects": True,
                "parse_interfaces": True,
                "parse_functions": True,
                "parse_properties": True,
                "parse_data_classes": True,
                "parse_sealed_classes": True,
                "parse_enums": True,
                "parse_extensions": True,
                "parse_annotations": True,
                "static_analysis": True,
                "ast_extraction": True,
                "android_support": True,
                "ckg_integration": True,
                "placeholder": False
            }
        else:
            return {
                "parse_classes": False,
                "parse_objects": False,
                "parse_interfaces": False,
                "parse_functions": False,
                "parse_properties": False,
                "parse_data_classes": False,
                "parse_sealed_classes": False,
                "parse_enums": False,
                "parse_extensions": False,
                "parse_annotations": False,
                "static_analysis": False,
                "ast_extraction": False,
                "android_support": False,
                "ckg_integration": False,
                "placeholder": True
            }
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Get parser capabilities."""
        return self._capabilities.copy()
    
    def is_available(self) -> bool:
        """Check if Kotlin analysis is available."""
        return self._ckg_parser is not None
    
    def analyze_kotlin_project(self, project_path: str) -> KotlinAnalysisResult:
        """
        Analyze entire Kotlin project.
        
        Args:
            project_path: Path to Kotlin project root
            
        Returns:
            KotlinAnalysisResult: Comprehensive analysis results
        """
        start_time = time.time()
        
        if not self.is_available():
            return KotlinAnalysisResult(
                project_path=project_path,
                files_analyzed=0,
                total_elements=0,
                analysis_time_seconds=time.time() - start_time,
                success=False,
                error_message="Kotlin analysis not available - CKG parser not initialized"
            )
        
        try:
            # Find Kotlin files
            kotlin_files = self._find_kotlin_files(project_path)
            
            if not kotlin_files:
                logger.info(f"No Kotlin files found in {project_path}")
                return KotlinAnalysisResult(
                    project_path=project_path,
                    files_analyzed=0,
                    total_elements=0,
                    analysis_time_seconds=time.time() - start_time,
                    success=True
                )
            
            # Parse Kotlin files using CKG parser or fallback
            if self._ckg_parser is not None:
                try:
                    parsed_files = self._ckg_parser.parse_kotlin_files(kotlin_files)
                except Exception as e:
                    logger.warning(f"CKG parser failed: {e}, using fallback mode")
                    parsed_files = self._fallback_parse_kotlin_files(kotlin_files)
            else:
                logger.info("Using fallback parsing mode")
                parsed_files = self._fallback_parse_kotlin_files(kotlin_files)
            
            # Extract code elements
            code_elements = []
            parse_errors = []
            elements_by_type = {
                'packages': 0,
                'classes': 0,
                'interfaces': 0,
                'objects': 0,
                'functions': 0,
                'properties': 0,
                'data_classes': 0,
                'sealed_classes': 0,
                'enums': 0,
                'extensions': 0,
                'annotations': 0,
                'imports': 0
            }
            
            for file_path, kotlin_parse_info in parsed_files:
                if kotlin_parse_info and isinstance(kotlin_parse_info, KotlinParseInfo):
                    try:
                        elements = self._extract_code_elements_from_parse_info(kotlin_parse_info, file_path)
                        code_elements.extend(elements)
                        
                        # Count elements by type
                        for element in elements:
                            element_type = element.element_type
                            if element_type in elements_by_type:
                                elements_by_type[element_type] += 1
                    except Exception as e:
                        error_msg = f"Element extraction failed for {file_path}: {e}"
                        parse_errors.append(error_msg)
                        logger.warning(error_msg)
                else:
                    error_msg = f"Parse failed for {file_path}: Invalid parse result"
                    parse_errors.append(error_msg)
                    logger.warning(error_msg)
            
            analysis_time = time.time() - start_time
            
            result = KotlinAnalysisResult(
                project_path=project_path,
                files_analyzed=len(kotlin_files),
                total_elements=len(code_elements),
                elements_by_type=elements_by_type,
                code_elements=code_elements,
                parse_errors=parse_errors,
                analysis_time_seconds=analysis_time,
                success=True
            )
            
            logger.info(f"Kotlin analysis completed: {len(kotlin_files)} files, "
                       f"{len(code_elements)} elements, {analysis_time:.2f}s")
            
            return result
            
        except Exception as e:
            error_msg = f"Kotlin analysis failed: {str(e)}"
            logger.error(error_msg)
            
            return KotlinAnalysisResult(
                project_path=project_path,
                files_analyzed=0,
                total_elements=0,
                analysis_time_seconds=time.time() - start_time,
                success=False,
                error_message=error_msg
            )
    
    def parse_kotlin_file(self, file_path: str) -> KotlinAnalysisResult:
        """
        Parse single Kotlin file.
        
        Args:
            file_path: Path to Kotlin file
            
        Returns:
            KotlinAnalysisResult: Analysis results for single file
        """
        start_time = time.time()
        
        if not self.is_available():
            return KotlinAnalysisResult(
                project_path=os.path.dirname(file_path),
                files_analyzed=0,
                total_elements=0,
                analysis_time_seconds=time.time() - start_time,
                success=False,
                error_message="Kotlin analysis not available"
            )
        
        try:
            # Parse single file
            parsed_files = self._ckg_parser.parse_kotlin_files([file_path])
            
            if not parsed_files:
                return KotlinAnalysisResult(
                    project_path=os.path.dirname(file_path),
                    files_analyzed=0,
                    total_elements=0,
                    analysis_time_seconds=time.time() - start_time,
                    success=False,
                    error_message="No parsed results returned"
                )
            
            file_path_result, kotlin_parse_info = parsed_files[0]
            
            if not kotlin_parse_info or not isinstance(kotlin_parse_info, KotlinParseInfo):
                return KotlinAnalysisResult(
                    project_path=os.path.dirname(file_path),
                    files_analyzed=1,
                    total_elements=0,
                    parse_errors=["Parse failed - invalid parse result"],
                    analysis_time_seconds=time.time() - start_time,
                    success=False,
                    error_message="Parse failed - invalid parse result"
                )
            
            # Extract elements
            code_elements = self._extract_code_elements_from_parse_info(kotlin_parse_info, file_path)
            
            # Count by type
            elements_by_type = {}
            for element in code_elements:
                element_type = element.element_type
                elements_by_type[element_type] = elements_by_type.get(element_type, 0) + 1
            
            return KotlinAnalysisResult(
                project_path=os.path.dirname(file_path),
                files_analyzed=1,
                total_elements=len(code_elements),
                elements_by_type=elements_by_type,
                code_elements=code_elements,
                analysis_time_seconds=time.time() - start_time,
                success=True
            )
            
        except Exception as e:
            error_msg = f"Failed to parse Kotlin file {file_path}: {str(e)}"
            logger.error(error_msg)
            
            return KotlinAnalysisResult(
                project_path=os.path.dirname(file_path),
                files_analyzed=1,
                total_elements=0,
                analysis_time_seconds=time.time() - start_time,
                success=False,
                error_message=error_msg
            )
    
    def _find_kotlin_files(self, project_path: str) -> List[str]:
        """
        Find all Kotlin files trong project.
        
        Args:
            project_path: Project root path
            
        Returns:
            List of Kotlin file paths
        """
        kotlin_files = []
        project_path = Path(project_path)
        
        try:
            for kotlin_file in project_path.rglob("*.kt"):
                if kotlin_file.is_file():
                    # Skip generated files and build directories
                    relative_path = str(kotlin_file.relative_to(project_path))
                    if not self._should_skip_kotlin_file(relative_path):
                        kotlin_files.append(str(kotlin_file))
            
            # Also check for Kotlin script files
            for kotlin_script in project_path.rglob("*.kts"):
                if kotlin_script.is_file():
                    relative_path = str(kotlin_script.relative_to(project_path))
                    if not self._should_skip_kotlin_file(relative_path):
                        kotlin_files.append(str(kotlin_script))
            
            logger.info(f"Found {len(kotlin_files)} Kotlin files in {project_path}")
            return kotlin_files
            
        except Exception as e:
            logger.error(f"Error finding Kotlin files in {project_path}: {e}")
            return []
    
    def _should_skip_kotlin_file(self, relative_path: str) -> bool:
        """Check if Kotlin file should be skipped during analysis."""
        skip_patterns = [
            'build/',
            '.gradle/',
            'buildSrc/',
            '/generated/',
            'build.gradle.kts',  # Build scripts are special
            'settings.gradle.kts'
        ]
        
        for pattern in skip_patterns:
            if pattern in relative_path:
                return True
        
        return False
    
    def _extract_code_elements_from_parse_info(self, kotlin_parse_info: KotlinParseInfo, file_path: str) -> List[KotlinCodeElement]:
        """
        Extract code elements từ KotlinParseInfo.
        
        Args:
            kotlin_parse_info: KotlinParseInfo from CKG parser
            file_path: File path for reference
            
        Returns:
            List of KotlinCodeElement objects
        """
        elements = []
        
        try:
            # Package
            if kotlin_parse_info.package_name:
                elements.append(KotlinCodeElement(
                    element_type='packages',
                    name=kotlin_parse_info.package_name,
                    full_qualified_name=kotlin_parse_info.package_name,
                    file_path=file_path,
                    line_number=1
                ))
            
            # Imports
            for import_name in kotlin_parse_info.imports:
                elements.append(KotlinCodeElement(
                    element_type='imports',
                    name=import_name.split('.')[-1],
                    full_qualified_name=import_name,
                    file_path=file_path,
                    line_number=1
                ))
            
            # Classes
            for class_node in kotlin_parse_info.classes:
                elements.append(KotlinCodeElement(
                    element_type='classes',
                    name=class_node.name or 'UnknownClass',
                    full_qualified_name=self._build_qualified_name(kotlin_parse_info.package_name, class_node.name),
                    file_path=file_path,
                    line_number=class_node.start_line or 1,
                    end_line_number=class_node.end_line,
                    modifiers=class_node.modifiers,
                    properties=class_node.properties
                ))
            
            # Interfaces
            for interface_node in kotlin_parse_info.interfaces:
                elements.append(KotlinCodeElement(
                    element_type='interfaces',
                    name=interface_node.name or 'UnknownInterface',
                    full_qualified_name=self._build_qualified_name(kotlin_parse_info.package_name, interface_node.name),
                    file_path=file_path,
                    line_number=interface_node.start_line or 1,
                    end_line_number=interface_node.end_line,
                    modifiers=interface_node.modifiers,
                    properties=interface_node.properties
                ))
            
            # Objects
            for object_node in kotlin_parse_info.objects:
                elements.append(KotlinCodeElement(
                    element_type='objects',
                    name=object_node.name or 'UnknownObject',
                    full_qualified_name=self._build_qualified_name(kotlin_parse_info.package_name, object_node.name),
                    file_path=file_path,
                    line_number=object_node.start_line or 1,
                    end_line_number=object_node.end_line,
                    modifiers=object_node.modifiers,
                    properties=object_node.properties
                ))
            
            # Functions
            for function_node in kotlin_parse_info.functions:
                element_type = 'extensions' if function_node.properties.get('is_extension') else 'functions'
                elements.append(KotlinCodeElement(
                    element_type=element_type,
                    name=function_node.name or 'UnknownFunction',
                    full_qualified_name=self._build_qualified_name(kotlin_parse_info.package_name, function_node.name),
                    file_path=file_path,
                    line_number=function_node.start_line or 1,
                    end_line_number=function_node.end_line,
                    modifiers=function_node.modifiers,
                    properties=function_node.properties
                ))
            
            # Properties
            for property_node in kotlin_parse_info.properties:
                elements.append(KotlinCodeElement(
                    element_type='properties',
                    name=property_node.name or 'UnknownProperty',
                    full_qualified_name=self._build_qualified_name(kotlin_parse_info.package_name, property_node.name),
                    file_path=file_path,
                    line_number=property_node.start_line or 1,
                    end_line_number=property_node.end_line,
                    modifiers=property_node.modifiers,
                    properties=property_node.properties
                ))
            
            # Data Classes
            for data_class_node in kotlin_parse_info.data_classes:
                elements.append(KotlinCodeElement(
                    element_type='data_classes',
                    name=data_class_node.name or 'UnknownDataClass',
                    full_qualified_name=self._build_qualified_name(kotlin_parse_info.package_name, data_class_node.name),
                    file_path=file_path,
                    line_number=data_class_node.start_line or 1,
                    end_line_number=data_class_node.end_line,
                    modifiers=data_class_node.modifiers,
                    properties=data_class_node.properties
                ))
            
            # Sealed Classes
            for sealed_class_node in kotlin_parse_info.sealed_classes:
                elements.append(KotlinCodeElement(
                    element_type='sealed_classes',
                    name=sealed_class_node.name or 'UnknownSealedClass',
                    full_qualified_name=self._build_qualified_name(kotlin_parse_info.package_name, sealed_class_node.name),
                    file_path=file_path,
                    line_number=sealed_class_node.start_line or 1,
                    end_line_number=sealed_class_node.end_line,
                    modifiers=sealed_class_node.modifiers,
                    properties=sealed_class_node.properties
                ))
            
            # Enums
            for enum_node in kotlin_parse_info.enums:
                elements.append(KotlinCodeElement(
                    element_type='enums',
                    name=enum_node.name or 'UnknownEnum',
                    full_qualified_name=self._build_qualified_name(kotlin_parse_info.package_name, enum_node.name),
                    file_path=file_path,
                    line_number=enum_node.start_line or 1,
                    end_line_number=enum_node.end_line,
                    modifiers=enum_node.modifiers,
                    properties=enum_node.properties
                ))
            
            # Annotations
            for annotation_node in kotlin_parse_info.annotations:
                elements.append(KotlinCodeElement(
                    element_type='annotations',
                    name=annotation_node.name or 'UnknownAnnotation',
                    full_qualified_name=self._build_qualified_name(kotlin_parse_info.package_name, annotation_node.name),
                    file_path=file_path,
                    line_number=annotation_node.start_line or 1,
                    end_line_number=annotation_node.end_line,
                    modifiers=annotation_node.modifiers,
                    properties=annotation_node.properties
                ))
        
        except Exception as e:
            logger.error(f"Error extracting elements from {file_path}: {e}")
        
        return elements
    
    def _build_qualified_name(self, package_name: Optional[str], element_name: Optional[str]) -> str:
        """Build fully qualified name for Kotlin element."""
        if not element_name:
            return 'Unknown'
        
        if package_name:
            return f"{package_name}.{element_name}"
        return element_name
    
    def _fallback_parse_kotlin_files(self, kotlin_files: List[str]) -> List:
        """
        Fallback parsing method khi CKG parser không available.
        
        Args:
            kotlin_files: List of Kotlin file paths
            
        Returns:
            List of mock tuples (file_path, mock_parse_info)
        """
        from dataclasses import dataclass
        from typing import Any
        
        @dataclass
        class MockKotlinParseInfo:
            package_name: str = ""
            imports: List[str] = None
            classes: List[Any] = None
            interfaces: List[Any] = None
            objects: List[Any] = None
            functions: List[Any] = None
            properties: List[Any] = None
            data_classes: List[Any] = None
            sealed_classes: List[Any] = None
            enums: List[Any] = None
            annotations: List[Any] = None
            
            def __post_init__(self):
                if self.imports is None:
                    self.imports = []
                if self.classes is None:
                    self.classes = []
                if self.interfaces is None:
                    self.interfaces = []
                if self.objects is None:
                    self.objects = []
                if self.functions is None:
                    self.functions = []
                if self.properties is None:
                    self.properties = []
                if self.data_classes is None:
                    self.data_classes = []
                if self.sealed_classes is None:
                    self.sealed_classes = []
                if self.enums is None:
                    self.enums = []
                if self.annotations is None:
                    self.annotations = []
        
        parsed_files = []
        
        for file_path in kotlin_files:
            try:
                # Simple fallback parsing - just read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Create mock parse info with basic detection
                mock_parse_info = MockKotlinParseInfo()
                
                # Basic package detection
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('package '):
                        mock_parse_info.package_name = line.replace('package ', '').strip().rstrip(';')
                        break
                
                parsed_files.append((file_path, mock_parse_info))
                
            except Exception as e:
                logger.warning(f"Fallback parsing failed for {file_path}: {e}")
                # Return with empty parse info
                mock_parse_info = MockKotlinParseInfo()
                parsed_files.append((file_path, mock_parse_info))
        
        return parsed_files
    
    def get_project_statistics(self, analysis_result: KotlinAnalysisResult) -> Dict[str, Any]:
        """
        Get statistical information về Kotlin project.
        
        Args:
            analysis_result: Analysis result from analyze_kotlin_project
            
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
        
        # Add Kotlin-specific metrics
        if analysis_result.files_analyzed > 0:
            stats["avg_elements_per_file"] = analysis_result.total_elements / analysis_result.files_analyzed
        
        # Check for Android project
        has_android = any('android' in element.full_qualified_name.lower() 
                         for element in analysis_result.code_elements 
                         if element.element_type == 'imports')
        stats["is_android_project"] = has_android
        
        # Kotlin-specific features
        stats["data_classes_count"] = analysis_result.elements_by_type.get('data_classes', 0)
        stats["sealed_classes_count"] = analysis_result.elements_by_type.get('sealed_classes', 0)
        stats["extensions_count"] = analysis_result.elements_by_type.get('extensions', 0)
        stats["objects_count"] = analysis_result.elements_by_type.get('objects', 0)
        
        return stats
    
    def is_android_project(self, project_path: str) -> bool:
        """
        Check if project is an Android project.
        
        Args:
            project_path: Path to project root
            
        Returns:
            bool: True if Android project detected
        """
        try:
            # Check for Android manifest
            manifest_path = Path(project_path) / 'app' / 'src' / 'main' / 'AndroidManifest.xml'
            if manifest_path.exists():
                return True
            
            # Check for build.gradle with Android plugin
            build_gradle_path = Path(project_path) / 'app' / 'build.gradle'
            build_gradle_kts_path = Path(project_path) / 'app' / 'build.gradle.kts'
            
            for gradle_file in [build_gradle_path, build_gradle_kts_path]:
                if gradle_file.exists():
                    with open(gradle_file, 'r') as f:
                        content = f.read()
                        if 'com.android.application' in content or 'com.android.library' in content:
                            return True
        except Exception as e:
            logger.debug(f"Error checking Android project: {e}")
        
        return False


# Convenience function for external usage
def create_kotlin_analysis_agent(kotlinc_path: Optional[str] = None) -> KotlinCodeAnalysisAgent:
    """
    Factory function to create KotlinCodeAnalysisAgent.
    
    Args:
        kotlinc_path: Optional path to kotlinc compiler
        
    Returns:
        KotlinCodeAnalysisAgent instance
    """
    return KotlinCodeAnalysisAgent(kotlinc_path)


# Legacy alias for backward compatibility
KotlinParseResult = KotlinAnalysisResult 