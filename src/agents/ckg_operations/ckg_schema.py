#!/usr/bin/env python3
"""
AI CodeScan - CKG Schema Definition

Định nghĩa schema cơ bản cho Code Knowledge Graph (CKG) bao gồm
các loại nodes, relationships và properties cho Python.
"""

from enum import Enum
from typing import Dict, List, Any
from dataclasses import dataclass


class NodeType(Enum):
    """Định nghĩa các loại nodes trong CKG."""
    # Common nodes
    FILE = "File"
    MODULE = "Module"
    
    # Python nodes
    CLASS = "Class"
    FUNCTION = "Function"
    METHOD = "Method"
    VARIABLE = "Variable"
    PARAMETER = "Parameter"
    IMPORT = "Import"
    DECORATOR = "Decorator"
    
    # Java nodes
    JAVA_CLASS = "JavaClass"
    JAVA_INTERFACE = "JavaInterface"
    JAVA_METHOD = "JavaMethod"
    JAVA_FIELD = "JavaField"
    JAVA_CONSTRUCTOR = "JavaConstructor"
    JAVA_PACKAGE = "JavaPackage"
    JAVA_IMPORT = "JavaImport"
    JAVA_ANNOTATION = "JavaAnnotation"
    JAVA_ENUM = "JavaEnum"
    JAVA_ENUM_CONSTANT = "JavaEnumConstant"
    
    # Dart nodes
    DART_CLASS = "DartClass"
    DART_MIXIN = "DartMixin"
    DART_EXTENSION = "DartExtension"
    DART_FUNCTION = "DartFunction"
    DART_METHOD = "DartMethod"
    DART_GETTER = "DartGetter"
    DART_SETTER = "DartSetter"
    DART_CONSTRUCTOR = "DartConstructor"
    DART_FIELD = "DartField"
    DART_VARIABLE = "DartVariable"
    DART_PARAMETER = "DartParameter"
    DART_IMPORT = "DartImport"
    DART_EXPORT = "DartExport"
    DART_PART = "DartPart"
    DART_LIBRARY = "DartLibrary"
    DART_ENUM = "DartEnum"
    DART_ENUM_VALUE = "DartEnumValue"
    DART_TYPEDEF = "DartTypedef"
    
    # Kotlin nodes
    KOTLIN_CLASS = "KotlinClass"
    KOTLIN_INTERFACE = "KotlinInterface"
    KOTLIN_DATA_CLASS = "KotlinDataClass"
    KOTLIN_SEALED_CLASS = "KotlinSealedClass"
    KOTLIN_OBJECT = "KotlinObject"
    KOTLIN_COMPANION_OBJECT = "KotlinCompanionObject"
    KOTLIN_FUNCTION = "KotlinFunction"
    KOTLIN_METHOD = "KotlinMethod"
    KOTLIN_EXTENSION_FUNCTION = "KotlinExtensionFunction"
    KOTLIN_CONSTRUCTOR = "KotlinConstructor"
    KOTLIN_PROPERTY = "KotlinProperty"
    KOTLIN_FIELD = "KotlinField"
    KOTLIN_PARAMETER = "KotlinParameter"
    KOTLIN_IMPORT = "KotlinImport"
    KOTLIN_PACKAGE = "KotlinPackage"
    KOTLIN_ANNOTATION = "KotlinAnnotation"
    KOTLIN_ENUM = "KotlinEnum"
    KOTLIN_ENUM_ENTRY = "KotlinEnumEntry"
    KOTLIN_TYPEALIAS = "KotlinTypealias"


class RelationshipType(Enum):
    """Định nghĩa các loại relationships trong CKG."""
    # Common relationships
    IMPORTS = "IMPORTS"
    CALLS = "CALLS"
    CONTAINS = "CONTAINS"
    BELONGS_TO = "BELONGS_TO"
    
    # Python relationships
    DEFINES_CLASS = "DEFINES_CLASS"
    DEFINES_FUNCTION = "DEFINES_FUNCTION"
    DEFINES_METHOD = "DEFINES_METHOD"
    DEFINES_VARIABLE = "DEFINES_VARIABLE"
    HAS_PARAMETER = "HAS_PARAMETER"
    INHERITS_FROM = "INHERITS_FROM"
    DECORATED_BY = "DECORATED_BY"
    ASSIGNS_TO = "ASSIGNS_TO"
    ACCESSES = "ACCESSES"
    
    # Java relationships
    DEFINES_JAVA_CLASS = "DEFINES_JAVA_CLASS"
    DEFINES_JAVA_INTERFACE = "DEFINES_JAVA_INTERFACE"
    DEFINES_JAVA_METHOD = "DEFINES_JAVA_METHOD"
    DEFINES_JAVA_FIELD = "DEFINES_JAVA_FIELD"
    DEFINES_JAVA_CONSTRUCTOR = "DEFINES_JAVA_CONSTRUCTOR"
    JAVA_EXTENDS = "JAVA_EXTENDS"
    JAVA_IMPLEMENTS = "JAVA_IMPLEMENTS"
    JAVA_ANNOTATED_BY = "JAVA_ANNOTATED_BY"
    JAVA_THROWS = "JAVA_THROWS"
    JAVA_OVERRIDES = "JAVA_OVERRIDES"
    JAVA_USES_TYPE = "JAVA_USES_TYPE"
    
    # Dart relationships
    DEFINES_DART_CLASS = "DEFINES_DART_CLASS"
    DEFINES_DART_MIXIN = "DEFINES_DART_MIXIN"
    DEFINES_DART_EXTENSION = "DEFINES_DART_EXTENSION"
    DEFINES_DART_FUNCTION = "DEFINES_DART_FUNCTION"
    DEFINES_DART_METHOD = "DEFINES_DART_METHOD"
    DEFINES_DART_GETTER = "DEFINES_DART_GETTER"
    DEFINES_DART_SETTER = "DEFINES_DART_SETTER"
    DEFINES_DART_CONSTRUCTOR = "DEFINES_DART_CONSTRUCTOR"
    DEFINES_DART_FIELD = "DEFINES_DART_FIELD"
    DEFINES_DART_VARIABLE = "DEFINES_DART_VARIABLE"
    DEFINES_DART_ENUM = "DEFINES_DART_ENUM"
    DEFINES_DART_TYPEDEF = "DEFINES_DART_TYPEDEF"
    DART_EXTENDS = "DART_EXTENDS"
    DART_IMPLEMENTS = "DART_IMPLEMENTS"
    DART_MIXES_IN = "DART_MIXES_IN"
    DART_EXTENDS_TYPE = "DART_EXTENDS_TYPE"  # For extension types
    DART_OVERRIDES = "DART_OVERRIDES"
    DART_USES_TYPE = "DART_USES_TYPE"
    DART_EXPORTS = "DART_EXPORTS"
    DART_PARTS = "DART_PARTS"
    
    # Kotlin relationships
    DEFINES_KOTLIN_CLASS = "DEFINES_KOTLIN_CLASS"
    DEFINES_KOTLIN_INTERFACE = "DEFINES_KOTLIN_INTERFACE"
    DEFINES_KOTLIN_DATA_CLASS = "DEFINES_KOTLIN_DATA_CLASS"
    DEFINES_KOTLIN_SEALED_CLASS = "DEFINES_KOTLIN_SEALED_CLASS"
    DEFINES_KOTLIN_OBJECT = "DEFINES_KOTLIN_OBJECT"
    DEFINES_KOTLIN_COMPANION_OBJECT = "DEFINES_KOTLIN_COMPANION_OBJECT"
    DEFINES_KOTLIN_FUNCTION = "DEFINES_KOTLIN_FUNCTION"
    DEFINES_KOTLIN_METHOD = "DEFINES_KOTLIN_METHOD"
    DEFINES_KOTLIN_EXTENSION_FUNCTION = "DEFINES_KOTLIN_EXTENSION_FUNCTION"
    DEFINES_KOTLIN_CONSTRUCTOR = "DEFINES_KOTLIN_CONSTRUCTOR"
    DEFINES_KOTLIN_PROPERTY = "DEFINES_KOTLIN_PROPERTY"
    DEFINES_KOTLIN_FIELD = "DEFINES_KOTLIN_FIELD"
    DEFINES_KOTLIN_ENUM = "DEFINES_KOTLIN_ENUM"
    DEFINES_KOTLIN_TYPEALIAS = "DEFINES_KOTLIN_TYPEALIAS"
    KOTLIN_EXTENDS = "KOTLIN_EXTENDS"
    KOTLIN_IMPLEMENTS = "KOTLIN_IMPLEMENTS"
    KOTLIN_OVERRIDES = "KOTLIN_OVERRIDES"
    KOTLIN_USES_TYPE = "KOTLIN_USES_TYPE"
    KOTLIN_ANNOTATED_BY = "KOTLIN_ANNOTATED_BY"
    KOTLIN_COMPILES_TO = "KOTLIN_COMPILES_TO"
    KOTLIN_DEPENDS_ON = "KOTLIN_DEPENDS_ON"


@dataclass
class NodeProperties:
    """Thuộc tính cơ bản cho tất cả các nodes."""
    name: str
    type: NodeType
    file_path: str
    line_number: int
    end_line_number: int = None
    column_offset: int = None
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


@dataclass
class RelationshipProperties:
    """Thuộc tính cho relationships."""
    type: RelationshipType
    source_node_id: str
    target_node_id: str
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


class CKGSchema:
    """
    CKG Schema Definition cho Python, Java, và Dart.
    
    Định nghĩa cấu trúc và quy tắc cho việc xây dựng Code Knowledge Graph
    hỗ trợ Python, Java, và Dart programming languages.
    
    Features:
    - Python nodes: Class, Function, Method, Variable, Parameter, Import, Decorator
    - Java nodes: JavaClass, JavaInterface, JavaMethod, JavaField, JavaConstructor, 
                  JavaPackage, JavaImport, JavaAnnotation, JavaEnum, JavaEnumConstant
    - Dart nodes: DartClass, DartMixin, DartExtension, DartFunction, DartMethod, DartGetter, DartSetter,
                  DartConstructor, DartField, DartVariable, DartParameter, DartImport, DartExport,
                  DartPart, DartLibrary, DartEnum, DartEnumValue, DartTypedef
    - Common relationships: IMPORTS, CALLS, CONTAINS, BELONGS_TO
    - Language-specific relationships: 
      * Python: INHERITS_FROM, DECORATED_BY
      * Java: JAVA_EXTENDS, JAVA_IMPLEMENTS, JAVA_ANNOTATED_BY
      * Dart: DART_EXTENDS, DART_IMPLEMENTS, DART_MIXES_IN, DART_EXTENDS_TYPE, DART_EXPORTS, DART_PARTS
    """
    
    # Properties cho từng loại node
    NODE_PROPERTIES = {
        # Common nodes
        NodeType.FILE: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['size_bytes', 'encoding', 'is_test_file', 'language']
        },
        NodeType.MODULE: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['docstring', 'imports_count', 'classes_count', 'functions_count']
        },
        
        # Python nodes
        NodeType.CLASS: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['docstring', 'is_abstract', 'base_classes', 'methods_count', 'attributes_count']
        },
        NodeType.FUNCTION: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['docstring', 'return_type', 'parameters_count', 'complexity', 'is_async', 'is_generator']
        },
        NodeType.METHOD: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['docstring', 'return_type', 'parameters_count', 'complexity', 'is_async', 'is_static', 'is_class_method', 'is_property']
        },
        NodeType.VARIABLE: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['value_type', 'is_global', 'is_constant', 'assigned_value']
        },
        NodeType.PARAMETER: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['param_type', 'default_value', 'is_keyword_only', 'is_positional_only']
        },
        NodeType.IMPORT: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['module_name', 'imported_name', 'alias', 'is_from_import']
        },
        NodeType.DECORATOR: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['arguments', 'is_builtin']
        },
        
        # Java nodes
        NodeType.JAVA_PACKAGE: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['full_name', 'classes_count', 'interfaces_count']
        },
        NodeType.JAVA_CLASS: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['package_name', 'full_name', 'modifiers', 'is_abstract', 'is_final', 'is_static', 
                        'extends_class', 'implements_interfaces', 'methods_count', 'fields_count', 'constructors_count']
        },
        NodeType.JAVA_INTERFACE: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['package_name', 'full_name', 'modifiers', 'extends_interfaces', 'methods_count', 'fields_count']
        },
        NodeType.JAVA_METHOD: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['modifiers', 'return_type', 'parameters', 'throws_exceptions', 'is_abstract', 
                        'is_static', 'is_final', 'is_synchronized', 'is_native', 'overrides_method']
        },
        NodeType.JAVA_CONSTRUCTOR: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['modifiers', 'parameters', 'throws_exceptions']
        },
        NodeType.JAVA_FIELD: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['field_type', 'modifiers', 'is_static', 'is_final', 'is_volatile', 'is_transient', 'initial_value']
        },
        NodeType.JAVA_IMPORT: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['imported_name', 'is_static_import', 'is_wildcard_import']
        },
        NodeType.JAVA_ANNOTATION: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['arguments', 'target_type']
        },
        NodeType.JAVA_ENUM: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['package_name', 'full_name', 'modifiers', 'implements_interfaces', 'constants_count', 'methods_count']
        },
        NodeType.JAVA_ENUM_CONSTANT: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['arguments', 'ordinal']
        },
        
        # Dart nodes
        NodeType.DART_CLASS: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['package_name', 'full_name', 'modifiers', 'is_abstract', 'is_final', 'is_static', 
                        'extends_class', 'implements_interfaces', 'methods_count', 'fields_count', 'constructors_count']
        },
        NodeType.DART_MIXIN: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['package_name', 'full_name', 'extends_interfaces', 'methods_count']
        },
        NodeType.DART_EXTENSION: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['extends_class', 'implements_interfaces', 'methods_count']
        },
        NodeType.DART_FUNCTION: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['return_type', 'parameters_count', 'complexity', 'is_async', 'is_generator']
        },
        NodeType.DART_METHOD: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['return_type', 'parameters_count', 'complexity', 'is_async', 'is_static', 'is_class_method', 'is_property']
        },
        NodeType.DART_GETTER: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['return_type']
        },
        NodeType.DART_SETTER: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['param_type']
        },
        NodeType.DART_CONSTRUCTOR: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['parameters']
        },
        NodeType.DART_FIELD: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['field_type', 'modifiers', 'is_static', 'is_final', 'is_volatile', 'is_transient', 'initial_value']
        },
        NodeType.DART_VARIABLE: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['value_type']
        },
        NodeType.DART_PARAMETER: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['param_type', 'default_value', 'is_keyword_only', 'is_positional_only']
        },
        NodeType.DART_IMPORT: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['module_name', 'imported_name', 'alias', 'is_from_import']
        },
        NodeType.DART_EXPORT: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['full_name']
        },
        NodeType.DART_PART: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['package_name', 'full_name']
        },
        NodeType.DART_LIBRARY: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['full_name']
        },
        NodeType.DART_ENUM: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['package_name', 'full_name', 'modifiers', 'implements_interfaces', 'constants_count', 'methods_count']
        },
        NodeType.DART_ENUM_VALUE: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['arguments', 'ordinal']
        },
        NodeType.DART_TYPEDEF: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['full_name']
        },
        
        # Kotlin nodes
        NodeType.KOTLIN_CLASS: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['package_name', 'full_name', 'modifiers', 'is_abstract', 'is_final', 'is_static', 
                        'extends_class', 'implements_interfaces', 'methods_count', 'fields_count', 'constructors_count']
        },
        NodeType.KOTLIN_INTERFACE: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['package_name', 'full_name', 'modifiers', 'extends_interfaces', 'methods_count', 'fields_count']
        },
        NodeType.KOTLIN_DATA_CLASS: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['package_name', 'full_name', 'modifiers', 'is_abstract', 'is_final', 'is_static', 
                        'extends_class', 'implements_interfaces', 'methods_count', 'fields_count', 'constructors_count']
        },
        NodeType.KOTLIN_SEALED_CLASS: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['package_name', 'full_name', 'modifiers', 'is_abstract', 'is_final', 'is_static', 
                        'extends_class', 'implements_interfaces', 'methods_count', 'fields_count', 'constructors_count']
        },
        NodeType.KOTLIN_OBJECT: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['package_name', 'full_name', 'modifiers', 'is_abstract', 'is_final', 'is_static', 
                        'extends_class', 'implements_interfaces', 'methods_count', 'fields_count', 'constructors_count']
        },
        NodeType.KOTLIN_COMPANION_OBJECT: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['package_name', 'full_name', 'modifiers', 'is_abstract', 'is_final', 'is_static', 
                        'extends_class', 'implements_interfaces', 'methods_count', 'fields_count', 'constructors_count']
        },
        NodeType.KOTLIN_FUNCTION: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['return_type', 'parameters_count', 'complexity', 'is_async', 'is_generator']
        },
        NodeType.KOTLIN_METHOD: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['return_type', 'parameters_count', 'complexity', 'is_async', 'is_static', 'is_class_method', 'is_property']
        },
        NodeType.KOTLIN_EXTENSION_FUNCTION: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['return_type', 'parameters_count', 'complexity', 'is_async', 'is_generator']
        },
        NodeType.KOTLIN_CONSTRUCTOR: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['parameters']
        },
        NodeType.KOTLIN_PROPERTY: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['return_type']
        },
        NodeType.KOTLIN_FIELD: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['field_type', 'modifiers', 'is_static', 'is_final', 'is_volatile', 'is_transient', 'initial_value']
        },
        NodeType.KOTLIN_PARAMETER: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['param_type', 'default_value', 'is_keyword_only', 'is_positional_only']
        },
        NodeType.KOTLIN_IMPORT: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['module_name', 'imported_name', 'alias', 'is_from_import']
        },
        NodeType.KOTLIN_PACKAGE: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['full_name', 'classes_count', 'interfaces_count']
        },
        NodeType.KOTLIN_ANNOTATION: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['arguments', 'target_type']
        },
        NodeType.KOTLIN_ENUM: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['package_name', 'full_name', 'modifiers', 'implements_interfaces', 'constants_count', 'methods_count']
        },
        NodeType.KOTLIN_ENUM_ENTRY: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['arguments', 'ordinal']
        },
        NodeType.KOTLIN_TYPEALIAS: {
            'required': ['name', 'type', 'file_path', 'line_number'],
            'optional': ['full_name']
        }
    }
    
    # Relationships hợp lệ giữa các loại nodes
    VALID_RELATIONSHIPS = {
        # Common relationships
        RelationshipType.IMPORTS: [
            (NodeType.MODULE, NodeType.MODULE), (NodeType.FILE, NodeType.MODULE),
            (NodeType.JAVA_PACKAGE, NodeType.JAVA_PACKAGE), (NodeType.FILE, NodeType.JAVA_PACKAGE)
        ],
        RelationshipType.CALLS: [
            (NodeType.FUNCTION, NodeType.FUNCTION), (NodeType.METHOD, NodeType.FUNCTION), (NodeType.METHOD, NodeType.METHOD),
            (NodeType.JAVA_METHOD, NodeType.JAVA_METHOD), (NodeType.JAVA_CONSTRUCTOR, NodeType.JAVA_METHOD)
        ],
        RelationshipType.CONTAINS: [
            (NodeType.FILE, NodeType.MODULE), (NodeType.MODULE, NodeType.CLASS), (NodeType.MODULE, NodeType.FUNCTION),
            (NodeType.FILE, NodeType.JAVA_PACKAGE), (NodeType.JAVA_PACKAGE, NodeType.JAVA_CLASS), 
            (NodeType.JAVA_PACKAGE, NodeType.JAVA_INTERFACE), (NodeType.JAVA_PACKAGE, NodeType.JAVA_ENUM)
        ],
        RelationshipType.BELONGS_TO: [
            (NodeType.CLASS, NodeType.MODULE), (NodeType.FUNCTION, NodeType.MODULE), (NodeType.METHOD, NodeType.CLASS),
            (NodeType.JAVA_CLASS, NodeType.JAVA_PACKAGE), (NodeType.JAVA_INTERFACE, NodeType.JAVA_PACKAGE),
            (NodeType.JAVA_ENUM, NodeType.JAVA_PACKAGE)
        ],
        
        # Python relationships
        RelationshipType.DEFINES_CLASS: [(NodeType.MODULE, NodeType.CLASS), (NodeType.FILE, NodeType.CLASS)],
        RelationshipType.DEFINES_FUNCTION: [(NodeType.MODULE, NodeType.FUNCTION), (NodeType.FILE, NodeType.FUNCTION)],
        RelationshipType.DEFINES_METHOD: [(NodeType.CLASS, NodeType.METHOD)],
        RelationshipType.DEFINES_VARIABLE: [(NodeType.MODULE, NodeType.VARIABLE), (NodeType.CLASS, NodeType.VARIABLE), (NodeType.FUNCTION, NodeType.VARIABLE)],
        RelationshipType.HAS_PARAMETER: [(NodeType.FUNCTION, NodeType.PARAMETER), (NodeType.METHOD, NodeType.PARAMETER)],
        RelationshipType.INHERITS_FROM: [(NodeType.CLASS, NodeType.CLASS)],
        RelationshipType.DECORATED_BY: [(NodeType.FUNCTION, NodeType.DECORATOR), (NodeType.METHOD, NodeType.DECORATOR), (NodeType.CLASS, NodeType.DECORATOR)],
        RelationshipType.ASSIGNS_TO: [(NodeType.FUNCTION, NodeType.VARIABLE), (NodeType.METHOD, NodeType.VARIABLE)],
        RelationshipType.ACCESSES: [(NodeType.FUNCTION, NodeType.VARIABLE), (NodeType.METHOD, NodeType.VARIABLE)],
        
        # Java relationships
        RelationshipType.DEFINES_JAVA_CLASS: [(NodeType.JAVA_PACKAGE, NodeType.JAVA_CLASS), (NodeType.FILE, NodeType.JAVA_CLASS)],
        RelationshipType.DEFINES_JAVA_INTERFACE: [(NodeType.JAVA_PACKAGE, NodeType.JAVA_INTERFACE), (NodeType.FILE, NodeType.JAVA_INTERFACE)],
        RelationshipType.DEFINES_JAVA_METHOD: [(NodeType.JAVA_CLASS, NodeType.JAVA_METHOD), (NodeType.JAVA_INTERFACE, NodeType.JAVA_METHOD), (NodeType.JAVA_ENUM, NodeType.JAVA_METHOD)],
        RelationshipType.DEFINES_JAVA_FIELD: [(NodeType.JAVA_CLASS, NodeType.JAVA_FIELD), (NodeType.JAVA_INTERFACE, NodeType.JAVA_FIELD), (NodeType.JAVA_ENUM, NodeType.JAVA_FIELD)],
        RelationshipType.DEFINES_JAVA_CONSTRUCTOR: [(NodeType.JAVA_CLASS, NodeType.JAVA_CONSTRUCTOR), (NodeType.JAVA_ENUM, NodeType.JAVA_CONSTRUCTOR)],
        RelationshipType.JAVA_EXTENDS: [(NodeType.JAVA_CLASS, NodeType.JAVA_CLASS), (NodeType.JAVA_INTERFACE, NodeType.JAVA_INTERFACE)],
        RelationshipType.JAVA_IMPLEMENTS: [(NodeType.JAVA_CLASS, NodeType.JAVA_INTERFACE), (NodeType.JAVA_ENUM, NodeType.JAVA_INTERFACE)],
        RelationshipType.JAVA_ANNOTATED_BY: [(NodeType.JAVA_CLASS, NodeType.JAVA_ANNOTATION), (NodeType.JAVA_METHOD, NodeType.JAVA_ANNOTATION), 
                                            (NodeType.JAVA_FIELD, NodeType.JAVA_ANNOTATION), (NodeType.JAVA_CONSTRUCTOR, NodeType.JAVA_ANNOTATION)],
        RelationshipType.JAVA_THROWS: [(NodeType.JAVA_METHOD, NodeType.JAVA_CLASS), (NodeType.JAVA_CONSTRUCTOR, NodeType.JAVA_CLASS)],
        RelationshipType.JAVA_OVERRIDES: [(NodeType.JAVA_METHOD, NodeType.JAVA_METHOD)],
        RelationshipType.JAVA_USES_TYPE: [(NodeType.JAVA_METHOD, NodeType.JAVA_CLASS), (NodeType.JAVA_FIELD, NodeType.JAVA_CLASS), 
                                         (NodeType.JAVA_CONSTRUCTOR, NodeType.JAVA_CLASS)],
        
        # Dart relationships
        RelationshipType.DEFINES_DART_CLASS: [(NodeType.JAVA_PACKAGE, NodeType.DART_CLASS), (NodeType.FILE, NodeType.DART_CLASS)],
        RelationshipType.DEFINES_DART_MIXIN: [(NodeType.JAVA_PACKAGE, NodeType.DART_MIXIN), (NodeType.FILE, NodeType.DART_MIXIN)],
        RelationshipType.DEFINES_DART_EXTENSION: [(NodeType.JAVA_PACKAGE, NodeType.DART_EXTENSION), (NodeType.FILE, NodeType.DART_EXTENSION)],
        RelationshipType.DEFINES_DART_FUNCTION: [(NodeType.DART_CLASS, NodeType.DART_FUNCTION), (NodeType.DART_MIXIN, NodeType.DART_FUNCTION), (NodeType.DART_EXTENSION, NodeType.DART_FUNCTION)],
        RelationshipType.DEFINES_DART_METHOD: [(NodeType.DART_CLASS, NodeType.DART_METHOD), (NodeType.DART_MIXIN, NodeType.DART_METHOD), (NodeType.DART_EXTENSION, NodeType.DART_METHOD)],
        RelationshipType.DEFINES_DART_GETTER: [(NodeType.DART_CLASS, NodeType.DART_GETTER), (NodeType.DART_MIXIN, NodeType.DART_GETTER), (NodeType.DART_EXTENSION, NodeType.DART_GETTER)],
        RelationshipType.DEFINES_DART_SETTER: [(NodeType.DART_CLASS, NodeType.DART_SETTER), (NodeType.DART_MIXIN, NodeType.DART_SETTER), (NodeType.DART_EXTENSION, NodeType.DART_SETTER)],
        RelationshipType.DEFINES_DART_CONSTRUCTOR: [(NodeType.DART_CLASS, NodeType.DART_CONSTRUCTOR), (NodeType.DART_MIXIN, NodeType.DART_CONSTRUCTOR), (NodeType.DART_EXTENSION, NodeType.DART_CONSTRUCTOR)],
        RelationshipType.DEFINES_DART_FIELD: [(NodeType.DART_CLASS, NodeType.DART_FIELD), (NodeType.DART_MIXIN, NodeType.DART_FIELD), (NodeType.DART_EXTENSION, NodeType.DART_FIELD)],
        RelationshipType.DEFINES_DART_VARIABLE: [(NodeType.DART_CLASS, NodeType.DART_VARIABLE), (NodeType.DART_MIXIN, NodeType.DART_VARIABLE), (NodeType.DART_EXTENSION, NodeType.DART_VARIABLE)],
        RelationshipType.DEFINES_DART_ENUM: [(NodeType.DART_CLASS, NodeType.DART_ENUM), (NodeType.DART_MIXIN, NodeType.DART_ENUM), (NodeType.DART_EXTENSION, NodeType.DART_ENUM)],
        RelationshipType.DEFINES_DART_TYPEDEF: [(NodeType.DART_CLASS, NodeType.DART_TYPEDEF), (NodeType.DART_MIXIN, NodeType.DART_TYPEDEF), (NodeType.DART_EXTENSION, NodeType.DART_TYPEDEF)],
        RelationshipType.DART_EXTENDS: [(NodeType.DART_CLASS, NodeType.DART_CLASS), (NodeType.DART_MIXIN, NodeType.DART_CLASS)],
        RelationshipType.DART_IMPLEMENTS: [(NodeType.DART_CLASS, NodeType.DART_MIXIN), (NodeType.DART_MIXIN, NodeType.DART_MIXIN)],
        RelationshipType.DART_MIXES_IN: [(NodeType.DART_CLASS, NodeType.DART_MIXIN)],
        RelationshipType.DART_EXTENDS_TYPE: [(NodeType.DART_CLASS, NodeType.DART_CLASS)],
        RelationshipType.DART_OVERRIDES: [(NodeType.DART_METHOD, NodeType.DART_METHOD)],
        RelationshipType.DART_USES_TYPE: [(NodeType.DART_METHOD, NodeType.DART_CLASS)],
        RelationshipType.DART_EXPORTS: [(NodeType.DART_CLASS, NodeType.DART_EXPORT)],
        RelationshipType.DART_PARTS: [(NodeType.DART_CLASS, NodeType.DART_PART)],
        
        # Kotlin relationships
        RelationshipType.DEFINES_KOTLIN_CLASS: [(NodeType.JAVA_PACKAGE, NodeType.KOTLIN_CLASS), (NodeType.FILE, NodeType.KOTLIN_CLASS)],
        RelationshipType.DEFINES_KOTLIN_INTERFACE: [(NodeType.JAVA_PACKAGE, NodeType.KOTLIN_INTERFACE), (NodeType.FILE, NodeType.KOTLIN_INTERFACE)],
        RelationshipType.DEFINES_KOTLIN_DATA_CLASS: [(NodeType.JAVA_PACKAGE, NodeType.KOTLIN_DATA_CLASS), (NodeType.FILE, NodeType.KOTLIN_DATA_CLASS)],
        RelationshipType.DEFINES_KOTLIN_SEALED_CLASS: [(NodeType.JAVA_PACKAGE, NodeType.KOTLIN_SEALED_CLASS), (NodeType.FILE, NodeType.KOTLIN_SEALED_CLASS)],
        RelationshipType.DEFINES_KOTLIN_OBJECT: [(NodeType.JAVA_PACKAGE, NodeType.KOTLIN_OBJECT), (NodeType.FILE, NodeType.KOTLIN_OBJECT)],
        RelationshipType.DEFINES_KOTLIN_COMPANION_OBJECT: [(NodeType.JAVA_PACKAGE, NodeType.KOTLIN_COMPANION_OBJECT), (NodeType.FILE, NodeType.KOTLIN_COMPANION_OBJECT)],
        RelationshipType.DEFINES_KOTLIN_FUNCTION: [(NodeType.JAVA_PACKAGE, NodeType.KOTLIN_FUNCTION), (NodeType.FILE, NodeType.KOTLIN_FUNCTION)],
        RelationshipType.DEFINES_KOTLIN_METHOD: [(NodeType.KOTLIN_CLASS, NodeType.KOTLIN_METHOD), (NodeType.KOTLIN_INTERFACE, NodeType.KOTLIN_METHOD)],
        RelationshipType.DEFINES_KOTLIN_EXTENSION_FUNCTION: [(NodeType.KOTLIN_CLASS, NodeType.KOTLIN_EXTENSION_FUNCTION), (NodeType.KOTLIN_INTERFACE, NodeType.KOTLIN_EXTENSION_FUNCTION)],
        RelationshipType.DEFINES_KOTLIN_CONSTRUCTOR: [(NodeType.KOTLIN_CLASS, NodeType.KOTLIN_CONSTRUCTOR), (NodeType.KOTLIN_INTERFACE, NodeType.KOTLIN_CONSTRUCTOR)],
        RelationshipType.DEFINES_KOTLIN_PROPERTY: [(NodeType.KOTLIN_CLASS, NodeType.KOTLIN_PROPERTY), (NodeType.KOTLIN_INTERFACE, NodeType.KOTLIN_PROPERTY)],
        RelationshipType.DEFINES_KOTLIN_FIELD: [(NodeType.KOTLIN_CLASS, NodeType.KOTLIN_FIELD), (NodeType.KOTLIN_INTERFACE, NodeType.KOTLIN_FIELD)],
        RelationshipType.DEFINES_KOTLIN_ENUM: [(NodeType.KOTLIN_CLASS, NodeType.KOTLIN_ENUM), (NodeType.KOTLIN_INTERFACE, NodeType.KOTLIN_ENUM)],
        RelationshipType.DEFINES_KOTLIN_TYPEALIAS: [(NodeType.JAVA_PACKAGE, NodeType.KOTLIN_TYPEALIAS), (NodeType.FILE, NodeType.KOTLIN_TYPEALIAS)],
        RelationshipType.KOTLIN_EXTENDS: [(NodeType.KOTLIN_CLASS, NodeType.KOTLIN_CLASS), (NodeType.KOTLIN_INTERFACE, NodeType.KOTLIN_INTERFACE)],
        RelationshipType.KOTLIN_IMPLEMENTS: [(NodeType.KOTLIN_CLASS, NodeType.KOTLIN_INTERFACE), (NodeType.KOTLIN_INTERFACE, NodeType.KOTLIN_INTERFACE)],
        RelationshipType.KOTLIN_OVERRIDES: [(NodeType.KOTLIN_METHOD, NodeType.KOTLIN_METHOD)],
        RelationshipType.KOTLIN_USES_TYPE: [(NodeType.KOTLIN_METHOD, NodeType.KOTLIN_CLASS)],
        RelationshipType.KOTLIN_ANNOTATED_BY: [(NodeType.KOTLIN_CLASS, NodeType.KOTLIN_ANNOTATION), (NodeType.KOTLIN_METHOD, NodeType.KOTLIN_ANNOTATION)],
        RelationshipType.KOTLIN_COMPILES_TO: [(NodeType.KOTLIN_CLASS, NodeType.KOTLIN_FUNCTION)],
        RelationshipType.KOTLIN_DEPENDS_ON: [(NodeType.KOTLIN_FUNCTION, NodeType.KOTLIN_CLASS)]
    }
    
    @classmethod
    def validate_node(cls, node: NodeProperties) -> bool:
        """
        Validate node properties theo schema.
        
        Args:
            node: Node cần validate
            
        Returns:
            bool: True nếu node hợp lệ
        """
        if node.type not in cls.NODE_PROPERTIES:
            return False
        
        required_props = cls.NODE_PROPERTIES[node.type]['required']
        
        # Kiểm tra required properties
        for prop in required_props:
            if not hasattr(node, prop) or getattr(node, prop) is None:
                return False
        
        return True
    
    @classmethod
    def validate_relationship(cls, relationship: RelationshipProperties, 
                            source_node_type: NodeType, target_node_type: NodeType) -> bool:
        """
        Validate relationship theo schema.
        
        Args:
            relationship: Relationship cần validate
            source_node_type: Loại node nguồn
            target_node_type: Loại node đích
            
        Returns:
            bool: True nếu relationship hợp lệ
        """
        if relationship.type not in cls.VALID_RELATIONSHIPS:
            return False
        
        valid_pairs = cls.VALID_RELATIONSHIPS[relationship.type]
        return (source_node_type, target_node_type) in valid_pairs
    
    @classmethod
    def get_cypher_create_node(cls, node: NodeProperties) -> str:
        """
        Tạo Cypher query để tạo node.
        
        Args:
            node: Node cần tạo
            
        Returns:
            str: Cypher query
        """
        properties = {
            'name': node.name,
            'type': node.type.value,
            'file_path': node.file_path,
            'line_number': node.line_number
        }
        
        if node.end_line_number:
            properties['end_line_number'] = node.end_line_number
        
        if node.column_offset:
            properties['column_offset'] = node.column_offset
        
        if node.properties:
            properties.update(node.properties)
        
        # Tạo properties string cho Cypher
        props_str = ', '.join([f'{k}: {repr(v)}' for k, v in properties.items()])
        
        # Generate unique ID
        node_id = f"{node.type.value}_{node.file_path}_{node.line_number}_{node.name}".replace('/', '_').replace('.', '_')
        
        return f"CREATE (n:{node.type.value} {{{props_str}}}) SET n.id = '{node_id}' RETURN n"
    
    @classmethod
    def get_cypher_create_relationship(cls, relationship: RelationshipProperties) -> str:
        """
        Tạo Cypher query để tạo relationship.
        
        Args:
            relationship: Relationship cần tạo
            
        Returns:
            str: Cypher query
        """
        properties_str = ""
        if relationship.properties:
            props = ', '.join([f'{k}: {repr(v)}' for k, v in relationship.properties.items()])
            properties_str = f" {{{props}}}"
        
        return f"""
        MATCH (source {{id: '{relationship.source_node_id}'}})
        MATCH (target {{id: '{relationship.target_node_id}'}})
        CREATE (source)-[r:{relationship.type.value}{properties_str}]->(target)
        RETURN r
        """
    
    @classmethod
    def get_cypher_find_node(cls, node_type: NodeType, **filters) -> str:
        """
        Tạo Cypher query để tìm nodes.
        
        Args:
            node_type: Loại node cần tìm
            **filters: Các bộ lọc
            
        Returns:
            str: Cypher query
        """
        where_conditions = []
        for key, value in filters.items():
            where_conditions.append(f"n.{key} = {repr(value)}")
        
        where_clause = ""
        if where_conditions:
            where_clause = f" WHERE {' AND '.join(where_conditions)}"
        
        return f"MATCH (n:{node_type.value}){where_clause} RETURN n"
    
    @classmethod
    def get_cypher_find_relationships(cls, relationship_type: RelationshipType, **filters) -> str:
        """
        Tạo Cypher query để tìm relationships.
        
        Args:
            relationship_type: Loại relationship cần tìm
            **filters: Các bộ lọc
            
        Returns:
            str: Cypher query
        """
        where_conditions = []
        for key, value in filters.items():
            where_conditions.append(f"r.{key} = {repr(value)}")
        
        where_clause = ""
        if where_conditions:
            where_clause = f" WHERE {' AND '.join(where_conditions)}"
        
        return f"MATCH (source)-[r:{relationship_type.value}]->(target){where_clause} RETURN source, r, target" 