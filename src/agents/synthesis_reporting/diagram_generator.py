"""
Diagram Generator Agent for AI CodeScan.

This agent generates various types of diagrams (class diagrams, architectural diagrams)
from Code Knowledge Graph data, supporting PlantUML and Mermaid.js output formats.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import re

logger = logging.getLogger(__name__)


class DiagramType(Enum):
    """Types of diagrams that can be generated."""
    
    CLASS_DIAGRAM = "class_diagram"
    INTERFACE_DIAGRAM = "interface_diagram"
    PACKAGE_DIAGRAM = "package_diagram"
    DEPENDENCY_DIAGRAM = "dependency_diagram"
    INHERITANCE_DIAGRAM = "inheritance_diagram"


class DiagramFormat(Enum):
    """Output formats for diagrams."""
    
    PLANTUML = "plantuml"
    MERMAID = "mermaid"


@dataclass
class DiagramGenerationRequest:
    """Request for diagram generation."""
    
    target_element: str  # Class name, module path, package name
    diagram_type: DiagramType
    output_format: DiagramFormat
    include_relationships: bool = True
    include_methods: bool = True
    include_attributes: bool = True
    max_depth: int = 2  # Max depth for related elements
    filter_private: bool = True  # Filter private members
    custom_options: Dict[str, Any] = None


@dataclass
class DiagramGenerationResult:
    """Result of diagram generation."""
    
    diagram_code: str
    diagram_type: DiagramType
    output_format: DiagramFormat
    target_element: str
    elements_included: List[str]
    relationships_included: List[str]
    generation_time: float
    success: bool = True
    error_message: Optional[str] = None
    warnings: List[str] = None


@dataclass
class ClassInfo:
    """Information about a class extracted from CKG."""
    
    name: str
    full_name: str
    file_path: str
    package: Optional[str] = None
    methods: List[Dict[str, Any]] = None
    attributes: List[Dict[str, Any]] = None
    parent_classes: List[str] = None
    implemented_interfaces: List[str] = None
    nested_classes: List[str] = None
    is_abstract: bool = False
    is_interface: bool = False


class DiagramGeneratorAgent:
    """
    Agent responsible for generating various types of diagrams from CKG data.
    
    This agent queries the Code Knowledge Graph to extract structural information
    and converts it into diagram code (PlantUML or Mermaid.js).
    """
    
    def __init__(self, ckg_query_agent=None):
        """
        Initialize the Diagram Generator Agent.
        
        Args:
            ckg_query_agent: CKGQueryInterfaceAgent instance for querying the graph
        """
        self.ckg_query_agent = ckg_query_agent
        logger.info("DiagramGeneratorAgent initialized")
    
    def generate_class_diagram_code(self, 
                                  class_name_or_module_path: str,
                                  diagram_type: str = "plantuml",
                                  **options) -> DiagramGenerationResult:
        """
        Generate class diagram code from CKG data.
        
        Args:
            class_name_or_module_path: Target class name or module path
            diagram_type: Output format ("plantuml" or "mermaid")
            **options: Additional generation options
            
        Returns:
            DiagramGenerationResult with generated diagram code
        """
        try:
            # Parse diagram type
            output_format = DiagramFormat.PLANTUML if diagram_type.lower() == "plantuml" else DiagramFormat.MERMAID
            
            # Create generation request
            request = DiagramGenerationRequest(
                target_element=class_name_or_module_path,
                diagram_type=DiagramType.CLASS_DIAGRAM,
                output_format=output_format,
                include_relationships=options.get('include_relationships', True),
                include_methods=options.get('include_methods', True),
                include_attributes=options.get('include_attributes', True),
                max_depth=options.get('max_depth', 2),
                filter_private=options.get('filter_private', True),
                custom_options=options
            )
            
            return self.generate_diagram(request)
            
        except Exception as e:
            logger.error(f"Failed to generate class diagram: {e}")
            return DiagramGenerationResult(
                diagram_code="",
                diagram_type=DiagramType.CLASS_DIAGRAM,
                output_format=DiagramFormat.PLANTUML,
                target_element=class_name_or_module_path,
                elements_included=[],
                relationships_included=[],
                generation_time=0.0,
                success=False,
                error_message=str(e)
            )
    
    def generate_diagram(self, request: DiagramGenerationRequest) -> DiagramGenerationResult:
        """
        Generate diagram based on the request.
        
        Args:
            request: DiagramGenerationRequest with generation parameters
            
        Returns:
            DiagramGenerationResult with generated diagram
        """
        import time
        start_time = time.time()
        
        try:
            # Extract information from CKG
            if request.diagram_type == DiagramType.CLASS_DIAGRAM:
                diagram_code = self._generate_class_diagram(request)
            elif request.diagram_type == DiagramType.DEPENDENCY_DIAGRAM:
                diagram_code = self._generate_dependency_diagram(request)
            elif request.diagram_type == DiagramType.INHERITANCE_DIAGRAM:
                diagram_code = self._generate_inheritance_diagram(request)
            else:
                raise ValueError(f"Unsupported diagram type: {request.diagram_type}")
            
            generation_time = time.time() - start_time
            
            return DiagramGenerationResult(
                diagram_code=diagram_code,
                diagram_type=request.diagram_type,
                output_format=request.output_format,
                target_element=request.target_element,
                elements_included=[],  # Will be populated by specific generators
                relationships_included=[],  # Will be populated by specific generators
                generation_time=generation_time,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Diagram generation failed: {e}")
            generation_time = time.time() - start_time
            
            return DiagramGenerationResult(
                diagram_code="",
                diagram_type=request.diagram_type,
                output_format=request.output_format,
                target_element=request.target_element,
                elements_included=[],
                relationships_included=[],
                generation_time=generation_time,
                success=False,
                error_message=str(e)
            )
    
    def _generate_class_diagram(self, request: DiagramGenerationRequest) -> str:
        """Generate class diagram code."""
        # Extract class information from CKG
        class_info = self._extract_class_info(request.target_element)
        
        if not class_info:
            # Try to extract as module/package
            classes_in_module = self._extract_module_classes(request.target_element)
            if not classes_in_module:
                raise ValueError(f"No class or module found: {request.target_element}")
            class_info = classes_in_module
        elif isinstance(class_info, ClassInfo):
            class_info = [class_info]
        
        # Get related classes if requested
        if request.include_relationships and request.max_depth > 0:
            related_classes = self._get_related_classes(class_info, request.max_depth)
            class_info.extend(related_classes)
        
        # Remove duplicates
        unique_classes = {}
        for cls in class_info:
            unique_classes[cls.full_name] = cls
        class_info = list(unique_classes.values())
        
        # Generate diagram code based on format
        if request.output_format == DiagramFormat.PLANTUML:
            return self._generate_plantuml_class_diagram(class_info, request)
        else:
            return self._generate_mermaid_class_diagram(class_info, request)
    
    def _generate_dependency_diagram(self, request: DiagramGenerationRequest) -> str:
        """Generate dependency diagram code."""
        # Extract dependency information
        dependencies = self._extract_dependencies(request.target_element)
        
        if request.output_format == DiagramFormat.PLANTUML:
            return self._generate_plantuml_dependency_diagram(dependencies, request)
        else:
            return self._generate_mermaid_dependency_diagram(dependencies, request)
    
    def _generate_inheritance_diagram(self, request: DiagramGenerationRequest) -> str:
        """Generate inheritance hierarchy diagram."""
        # Extract inheritance information
        inheritance_tree = self._extract_inheritance_tree(request.target_element)
        
        if request.output_format == DiagramFormat.PLANTUML:
            return self._generate_plantuml_inheritance_diagram(inheritance_tree, request)
        else:
            return self._generate_mermaid_inheritance_diagram(inheritance_tree, request)
    
    def _extract_class_info(self, class_name: str) -> Optional[ClassInfo]:
        """Extract class information from CKG."""
        if not self.ckg_query_agent:
            logger.warning("No CKG query agent available, returning mock data")
            return self._create_mock_class_info(class_name)
        
        try:
            # Query CKG for class information
            # This would be actual CKG queries in real implementation
            classes = self.ckg_query_agent.get_classes_in_file("")
            for cls_data in classes:
                if cls_data.get('name') == class_name:
                    return self._convert_ckg_to_class_info(cls_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract class info for {class_name}: {e}")
            return self._create_mock_class_info(class_name)
    
    def _extract_module_classes(self, module_path: str) -> List[ClassInfo]:
        """Extract all classes from a module."""
        if not self.ckg_query_agent:
            logger.warning("No CKG query agent available, returning mock data")
            return [self._create_mock_class_info(f"Class{i}") for i in range(1, 4)]
        
        try:
            # Query CKG for module classes
            classes = self.ckg_query_agent.get_classes_in_file(module_path)
            return [self._convert_ckg_to_class_info(cls_data) for cls_data in classes]
            
        except Exception as e:
            logger.error(f"Failed to extract module classes for {module_path}: {e}")
            return [self._create_mock_class_info(f"MockClass{i}") for i in range(1, 3)]
    
    def _get_related_classes(self, classes: List[ClassInfo], max_depth: int) -> List[ClassInfo]:
        """Get classes related to the given classes up to max_depth."""
        related = []
        
        for cls in classes:
            # Add parent classes
            if cls.parent_classes:
                for parent in cls.parent_classes:
                    parent_info = self._extract_class_info(parent)
                    if parent_info:
                        related.append(parent_info)
            
            # Add implemented interfaces
            if cls.implemented_interfaces:
                for interface in cls.implemented_interfaces:
                    interface_info = self._extract_class_info(interface)
                    if interface_info:
                        related.append(interface_info)
        
        return related
    
    def _convert_ckg_to_class_info(self, ckg_data: Dict[str, Any]) -> ClassInfo:
        """Convert CKG data to ClassInfo object."""
        return ClassInfo(
            name=ckg_data.get('name', 'Unknown'),
            full_name=ckg_data.get('full_name', ckg_data.get('name', 'Unknown')),
            file_path=ckg_data.get('file_path', ''),
            package=ckg_data.get('package'),
            methods=ckg_data.get('methods', []),
            attributes=ckg_data.get('attributes', []),
            parent_classes=ckg_data.get('parent_classes', []),
            implemented_interfaces=ckg_data.get('interfaces', []),
            is_abstract=ckg_data.get('is_abstract', False),
            is_interface=ckg_data.get('is_interface', False)
        )
    
    def _create_mock_class_info(self, class_name: str) -> ClassInfo:
        """Create mock class info for testing/demo purposes."""
        return ClassInfo(
            name=class_name,
            full_name=f"com.example.{class_name}",
            file_path=f"src/main/java/com/example/{class_name}.java",
            package="com.example",
            methods=[
                {'name': 'init', 'visibility': 'public', 'return_type': 'void'},
                {'name': 'process', 'visibility': 'public', 'return_type': 'String'},
                {'name': 'validate', 'visibility': 'private', 'return_type': 'boolean'}
            ],
            attributes=[
                {'name': 'id', 'type': 'String', 'visibility': 'private'},
                {'name': 'status', 'type': 'Status', 'visibility': 'private'}
            ],
            parent_classes=['BaseClass'] if class_name != 'BaseClass' else [],
            implemented_interfaces=['Processable'] if 'Process' in class_name else []
        )
    
    def _generate_plantuml_class_diagram(self, classes: List[ClassInfo], request: DiagramGenerationRequest) -> str:
        """Generate PlantUML class diagram code."""
        lines = ["@startuml"]
        lines.append("!theme plain")
        lines.append("skinparam classAttributeIconSize 0")
        lines.append("")
        
        # Add classes
        for cls in classes:
            lines.append(self._generate_plantuml_class(cls, request))
        
        lines.append("")
        
        # Add relationships
        for cls in classes:
            lines.extend(self._generate_plantuml_relationships(cls, classes))
        
        lines.append("@enduml")
        return "\n".join(lines)
    
    def _generate_plantuml_class(self, cls: ClassInfo, request: DiagramGenerationRequest) -> str:
        """Generate PlantUML code for a single class."""
        class_type = "interface" if cls.is_interface else "abstract class" if cls.is_abstract else "class"
        lines = [f"{class_type} {cls.name} {{"]
        
        # Add attributes
        if request.include_attributes and cls.attributes:
            for attr in cls.attributes:
                if request.filter_private and attr.get('visibility') == 'private':
                    continue
                visibility = self._get_plantuml_visibility(attr.get('visibility', 'public'))
                attr_line = f"  {visibility}{attr['name']}: {attr.get('type', 'Object')}"
                lines.append(attr_line)
        
        # Add separator if both attributes and methods exist
        if (request.include_attributes and cls.attributes and 
            request.include_methods and cls.methods):
            lines.append("  --")
        
        # Add methods
        if request.include_methods and cls.methods:
            for method in cls.methods:
                if request.filter_private and method.get('visibility') == 'private':
                    continue
                visibility = self._get_plantuml_visibility(method.get('visibility', 'public'))
                return_type = method.get('return_type', 'void')
                method_line = f"  {visibility}{method['name']}(): {return_type}"
                lines.append(method_line)
        
        lines.append("}")
        return "\n".join(lines)
    
    def _generate_plantuml_relationships(self, cls: ClassInfo, all_classes: List[ClassInfo]) -> List[str]:
        """Generate PlantUML relationship lines for a class."""
        lines = []
        class_names = {c.name for c in all_classes}
        
        # Inheritance relationships
        if cls.parent_classes:
            for parent in cls.parent_classes:
                if parent in class_names:
                    lines.append(f"{parent} <|-- {cls.name}")
        
        # Interface implementation
        if cls.implemented_interfaces:
            for interface in cls.implemented_interfaces:
                if interface in class_names:
                    lines.append(f"{interface} <|.. {cls.name}")
        
        return lines
    
    def _generate_mermaid_class_diagram(self, classes: List[ClassInfo], request: DiagramGenerationRequest) -> str:
        """Generate Mermaid class diagram code."""
        lines = ["classDiagram"]
        
        # Add classes
        for cls in classes:
            lines.extend(self._generate_mermaid_class(cls, request))
        
        lines.append("")
        
        # Add relationships
        for cls in classes:
            lines.extend(self._generate_mermaid_relationships(cls, classes))
        
        return "\n".join(lines)
    
    def _generate_mermaid_class(self, cls: ClassInfo, request: DiagramGenerationRequest) -> List[str]:
        """Generate Mermaid code for a single class."""
        lines = []
        
        # Class declaration
        if cls.is_interface:
            lines.append(f"    class {cls.name} {{")
            lines.append(f"        <<interface>>")
        elif cls.is_abstract:
            lines.append(f"    class {cls.name} {{")
            lines.append(f"        <<abstract>>")
        else:
            lines.append(f"    class {cls.name} {{")
        
        # Add attributes
        if request.include_attributes and cls.attributes:
            for attr in cls.attributes:
                if request.filter_private and attr.get('visibility') == 'private':
                    continue
                visibility = self._get_mermaid_visibility(attr.get('visibility', 'public'))
                attr_line = f"        {visibility}{attr.get('type', 'Object')} {attr['name']}"
                lines.append(attr_line)
        
        # Add methods
        if request.include_methods and cls.methods:
            for method in cls.methods:
                if request.filter_private and method.get('visibility') == 'private':
                    continue
                visibility = self._get_mermaid_visibility(method.get('visibility', 'public'))
                return_type = method.get('return_type', 'void')
                method_line = f"        {visibility}{method['name']}() {return_type}"
                lines.append(method_line)
        
        lines.append("    }")
        return lines
    
    def _generate_mermaid_relationships(self, cls: ClassInfo, all_classes: List[ClassInfo]) -> List[str]:
        """Generate Mermaid relationship lines for a class."""
        lines = []
        class_names = {c.name for c in all_classes}
        
        # Inheritance relationships
        if cls.parent_classes:
            for parent in cls.parent_classes:
                if parent in class_names:
                    lines.append(f"    {parent} <|-- {cls.name}")
        
        # Interface implementation
        if cls.implemented_interfaces:
            for interface in cls.implemented_interfaces:
                if interface in class_names:
                    lines.append(f"    {interface} <|.. {cls.name}")
        
        return lines
    
    def _get_plantuml_visibility(self, visibility: str) -> str:
        """Convert visibility to PlantUML notation."""
        visibility_map = {
            'public': '+',
            'private': '-',
            'protected': '#',
            'package': '~'
        }
        return visibility_map.get(visibility, '+')
    
    def _get_mermaid_visibility(self, visibility: str) -> str:
        """Convert visibility to Mermaid notation."""
        visibility_map = {
            'public': '+',
            'private': '-',
            'protected': '#',
            'package': '~'
        }
        return visibility_map.get(visibility, '+')
    
    def _extract_dependencies(self, target: str) -> Dict[str, Any]:
        """Extract dependency information for dependency diagrams."""
        # Mock implementation
        return {
            'modules': ['ModuleA', 'ModuleB', 'ModuleC'],
            'dependencies': [
                ('ModuleA', 'ModuleB'),
                ('ModuleB', 'ModuleC'),
                ('ModuleA', 'ModuleC')
            ]
        }
    
    def _extract_inheritance_tree(self, target: str) -> Dict[str, Any]:
        """Extract inheritance tree information."""
        # Mock implementation
        return {
            'root_classes': ['BaseClass'],
            'inheritance_chains': [
                ['BaseClass', 'MiddleClass', 'ConcreteClass'],
                ['BaseClass', 'AnotherClass']
            ]
        }
    
    def _generate_plantuml_dependency_diagram(self, dependencies: Dict[str, Any], request: DiagramGenerationRequest) -> str:
        """Generate PlantUML dependency diagram."""
        lines = ["@startuml"]
        lines.append("!theme plain")
        lines.append("")
        
        for module in dependencies['modules']:
            lines.append(f"component {module}")
        
        lines.append("")
        
        for src, dest in dependencies['dependencies']:
            lines.append(f"{src} --> {dest}")
        
        lines.append("@enduml")
        return "\n".join(lines)
    
    def _generate_mermaid_dependency_diagram(self, dependencies: Dict[str, Any], request: DiagramGenerationRequest) -> str:
        """Generate Mermaid dependency diagram."""
        lines = ["graph TD"]
        
        for src, dest in dependencies['dependencies']:
            lines.append(f"    {src} --> {dest}")
        
        return "\n".join(lines)
    
    def _generate_plantuml_inheritance_diagram(self, inheritance_tree: Dict[str, Any], request: DiagramGenerationRequest) -> str:
        """Generate PlantUML inheritance diagram."""
        lines = ["@startuml"]
        lines.append("!theme plain")
        lines.append("")
        
        # Extract all classes
        all_classes = set()
        for chain in inheritance_tree['inheritance_chains']:
            all_classes.update(chain)
        
        for cls in all_classes:
            lines.append(f"class {cls}")
        
        lines.append("")
        
        for chain in inheritance_tree['inheritance_chains']:
            for i in range(len(chain) - 1):
                lines.append(f"{chain[i]} <|-- {chain[i+1]}")
        
        lines.append("@enduml")
        return "\n".join(lines)
    
    def _generate_mermaid_inheritance_diagram(self, inheritance_tree: Dict[str, Any], request: DiagramGenerationRequest) -> str:
        """Generate Mermaid inheritance diagram."""
        lines = ["classDiagram"]
        
        for chain in inheritance_tree['inheritance_chains']:
            for i in range(len(chain) - 1):
                lines.append(f"    {chain[i]} <|-- {chain[i+1]}")
        
        return "\n".join(lines)
    
    def get_supported_diagram_types(self) -> List[str]:
        """Get list of supported diagram types."""
        return [dt.value for dt in DiagramType]
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported output formats."""
        return [df.value for df in DiagramFormat]
    
    def validate_request(self, request: DiagramGenerationRequest) -> Tuple[bool, Optional[str]]:
        """Validate a diagram generation request."""
        if not request.target_element:
            return False, "Target element cannot be empty"
        
        if request.max_depth < 0:
            return False, "Max depth must be non-negative"
        
        return True, None


def create_diagram_generator(ckg_query_agent=None) -> DiagramGeneratorAgent:
    """
    Factory function to create DiagramGeneratorAgent.
    
    Args:
        ckg_query_agent: Optional CKG query agent
        
    Returns:
        DiagramGeneratorAgent instance
    """
    return DiagramGeneratorAgent(ckg_query_agent=ckg_query_agent) 