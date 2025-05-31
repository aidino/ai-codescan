#!/usr/bin/env python3

"""
KotlinParserAgent - AST parsing agent cho Kotlin code.

Agent này responsible cho việc parse Kotlin source code thành AST representation
để phục vụ cho Code Knowledge Graph construction.
"""

import os
import json
import subprocess
import tempfile
import urllib.request
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging

# Use standard logging instead of custom DebugLogger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src to path để import modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Kotlin Node representations
@dataclass
class KotlinNode:
    """Represents a node trong Kotlin AST."""
    type: str
    name: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    start_column: Optional[int] = None
    end_column: Optional[int] = None
    modifiers: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    children: List['KotlinNode'] = field(default_factory=list)
    text: Optional[str] = None

@dataclass
class KotlinParseInfo:
    """Contains structured information parsed từ Kotlin AST."""
    package_name: Optional[str] = None
    imports: List[str] = field(default_factory=list)
    classes: List[KotlinNode] = field(default_factory=list)
    interfaces: List[KotlinNode] = field(default_factory=list)
    objects: List[KotlinNode] = field(default_factory=list)
    functions: List[KotlinNode] = field(default_factory=list)
    properties: List[KotlinNode] = field(default_factory=list)
    enums: List[KotlinNode] = field(default_factory=list)
    data_classes: List[KotlinNode] = field(default_factory=list)
    sealed_classes: List[KotlinNode] = field(default_factory=list)
    annotations: List[KotlinNode] = field(default_factory=list)
    extensions: List[KotlinNode] = field(default_factory=list)
    typealiases: List[KotlinNode] = field(default_factory=list)

class KotlinParserAgent:
    """
    Agent chuyên dụng parse Kotlin source code thành AST.
    
    Sử dụng kotlinc compiler với subprocess approach để extract AST information
    từ Kotlin files, tương tự approach thành công của JavaParserAgent.
    """
    
    def __init__(self):
        """Initialize KotlinParserAgent."""
        self.kotlinc_path = self._ensure_kotlinc_available()
        self.timeout = 30  # 30 seconds timeout
        
    def _ensure_kotlinc_available(self) -> Optional[str]:
        """
        Ensure kotlinc compiler is available.
        
        Returns:
            Optional[str]: Path to kotlinc or None if not found
        """
        try:
            # Try to find kotlinc in PATH
            result = subprocess.run(['which', 'kotlinc'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                kotlinc_path = result.stdout.strip()
                logger.info(f"Found kotlinc at: {kotlinc_path}")
                return kotlinc_path
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
            
        # Try common installation paths
        common_paths = [
            '/usr/bin/kotlinc',
            '/usr/local/bin/kotlinc',
            os.path.expanduser('~/.sdkman/candidates/kotlin/current/bin/kotlinc'),
            '/opt/kotlinc/bin/kotlinc'
        ]
        
        for path in common_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                logger.info(f"Found kotlinc at: {path}")
                return path
                
        logger.warning("kotlinc not found. Kotlin parsing will not be available.")
        return None
    
    def parse_kotlin_files(self, file_paths: List[str]) -> List[tuple]:
        """
        Parse multiple Kotlin files và return AST information.
        
        Args:
            file_paths: List of Kotlin file paths to parse
            
        Returns:
            List[tuple]: List of (file_path, KotlinParseInfo) tuples
        """
        if not self.kotlinc_path:
            logger.error("kotlinc not available for parsing")
            return []
            
        results = []
        for file_path in file_paths:
            if file_path.endswith(('.kt', '.kts')):
                try:
                    parse_info = self._parse_single_file(file_path)
                    results.append((file_path, parse_info))
                except Exception as e:
                    logger.error(f"Failed to parse {file_path}: {e}")
                    results.append((file_path, KotlinParseInfo()))
                    
        return results
    
    def _parse_single_file(self, file_path: str) -> KotlinParseInfo:
        """
        Parse một Kotlin file và extract AST information.
        
        Args:
            file_path: Path to Kotlin file
            
        Returns:
            KotlinParseInfo: Parsed information từ file
        """
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Try to compile và check for syntax errors
            compile_result = self._check_kotlin_syntax(file_path)
            
            # Parse content manually (fallback approach)
            parse_info = self._manual_parse_kotlin(content)
            
            return parse_info
            
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return KotlinParseInfo()
    
    def _check_kotlin_syntax(self, file_path: str) -> bool:
        """
        Check Kotlin file syntax using kotlinc.
        
        Args:
            file_path: Path to Kotlin file
            
        Returns:
            bool: True if syntax is valid
        """
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                output_dir = os.path.join(temp_dir, 'output')
                os.makedirs(output_dir, exist_ok=True)
                
                # Run kotlinc to check syntax
                cmd = [self.kotlinc_path, '-d', output_dir, file_path]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                
                if result.returncode == 0:
                    logger.debug(f"Kotlin syntax check passed for {file_path}")
                    return True
                else:
                    logger.warning(f"Kotlin syntax issues in {file_path}: {result.stderr}")
                    return False
                    
        except subprocess.TimeoutExpired:
            logger.error(f"Kotlin syntax check timeout for {file_path}")
            return False
        except Exception as e:
            logger.error(f"Error checking Kotlin syntax for {file_path}: {e}")
            return False
    
    def _manual_parse_kotlin(self, content: str) -> KotlinParseInfo:
        """
        Manual parsing của Kotlin content để extract basic information.
        
        Args:
            content: Kotlin source code content
            
        Returns:
            KotlinParseInfo: Extracted information
        """
        lines = content.split('\n')
        parse_info = KotlinParseInfo()
        
        current_line = 0
        in_comment_block = False
        in_string = False
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                continue
                
            # Handle comment blocks
            if '/*' in stripped and not in_string:
                in_comment_block = True
            if '*/' in stripped and in_comment_block:
                in_comment_block = False
                continue
            if in_comment_block or stripped.startswith('//'):
                continue
                
            # Package declaration
            if stripped.startswith('package ') and not parse_info.package_name:
                package_match = stripped[8:].strip()
                if package_match.endswith(';'):
                    package_match = package_match[:-1]
                parse_info.package_name = package_match
                continue
                
            # Import statements
            if stripped.startswith('import '):
                import_stmt = stripped[7:].strip()
                if import_stmt.endswith(';'):
                    import_stmt = import_stmt[:-1]
                parse_info.imports.append(import_stmt)
                continue
                
            # Class declarations
            if self._is_class_declaration(stripped):
                class_node = self._parse_class_declaration(stripped, line_num)
                if 'data' in stripped:
                    parse_info.data_classes.append(class_node)
                elif 'sealed' in stripped:
                    parse_info.sealed_classes.append(class_node)
                else:
                    parse_info.classes.append(class_node)
                continue
                
            # Interface declarations
            if self._is_interface_declaration(stripped):
                interface_node = self._parse_interface_declaration(stripped, line_num)
                parse_info.interfaces.append(interface_node)
                continue
                
            # Object declarations
            if self._is_object_declaration(stripped):
                object_node = self._parse_object_declaration(stripped, line_num)
                parse_info.objects.append(object_node)
                continue
                
            # Function declarations
            if self._is_function_declaration(stripped):
                function_node = self._parse_function_declaration(stripped, line_num)
                # Check if it's an extension function
                if '.' in function_node.name and 'fun ' in stripped:
                    parse_info.extensions.append(function_node)
                else:
                    parse_info.functions.append(function_node)
                continue
                
            # Property declarations
            if self._is_property_declaration(stripped):
                property_node = self._parse_property_declaration(stripped, line_num)
                parse_info.properties.append(property_node)
                continue
                
            # Enum declarations
            if self._is_enum_declaration(stripped):
                enum_node = self._parse_enum_declaration(stripped, line_num)
                parse_info.enums.append(enum_node)
                continue
                
            # Annotation declarations
            if self._is_annotation_declaration(stripped):
                annotation_node = self._parse_annotation_declaration(stripped, line_num)
                parse_info.annotations.append(annotation_node)
                continue
                
            # Typealias declarations
            if self._is_typealias_declaration(stripped):
                typealias_node = self._parse_typealias_declaration(stripped, line_num)
                parse_info.typealiases.append(typealias_node)
                continue
                
        return parse_info
    
    def _is_class_declaration(self, line: str) -> bool:
        """Check if line is a class declaration."""
        words = line.split()
        return 'class' in words and not line.strip().startswith('//')
    
    def _is_interface_declaration(self, line: str) -> bool:
        """Check if line is an interface declaration."""
        words = line.split()
        return 'interface' in words and not line.strip().startswith('//')
    
    def _is_object_declaration(self, line: str) -> bool:
        """Check if line is an object declaration."""
        words = line.split()
        return 'object' in words and not line.strip().startswith('//')
    
    def _is_function_declaration(self, line: str) -> bool:
        """Check if line is a function declaration."""
        return 'fun ' in line and not line.strip().startswith('//')
    
    def _is_property_declaration(self, line: str) -> bool:
        """Check if line is a property declaration."""
        words = line.split()
        return ('val ' in line or 'var ' in line) and not line.strip().startswith('//')
    
    def _is_enum_declaration(self, line: str) -> bool:
        """Check if line is an enum declaration."""
        words = line.split()
        return 'enum' in words and 'class' in words and not line.strip().startswith('//')
    
    def _is_annotation_declaration(self, line: str) -> bool:
        """Check if line is an annotation declaration."""
        words = line.split()
        return 'annotation' in words and 'class' in words and not line.strip().startswith('//')
    
    def _is_typealias_declaration(self, line: str) -> bool:
        """Check if line is a typealias declaration."""
        return 'typealias' in line and not line.strip().startswith('//')
    
    def _parse_class_declaration(self, line: str, line_num: int) -> KotlinNode:
        """Parse class declaration line."""
        words = line.split()
        class_name = None
        modifiers = []
        
        for i, word in enumerate(words):
            if word == 'class' and i + 1 < len(words):
                class_name = words[i + 1].split('(')[0].split('<')[0].split(':')[0]
                break
        
        # Extract modifiers
        for word in words:
            if word in ['public', 'private', 'protected', 'internal', 'open', 'final', 'abstract', 'data', 'sealed', 'inner']:
                modifiers.append(word)
        
        return KotlinNode(
            type='CLASS',
            name=class_name,
            start_line=line_num,
            modifiers=modifiers,
            text=line
        )
    
    def _parse_interface_declaration(self, line: str, line_num: int) -> KotlinNode:
        """Parse interface declaration line."""
        words = line.split()
        interface_name = None
        modifiers = []
        
        for i, word in enumerate(words):
            if word == 'interface' and i + 1 < len(words):
                interface_name = words[i + 1].split('<')[0].split(':')[0]
                break
        
        # Extract modifiers
        for word in words:
            if word in ['public', 'private', 'protected', 'internal']:
                modifiers.append(word)
        
        return KotlinNode(
            type='INTERFACE',
            name=interface_name,
            start_line=line_num,
            modifiers=modifiers,
            text=line
        )
    
    def _parse_object_declaration(self, line: str, line_num: int) -> KotlinNode:
        """Parse object declaration line."""
        words = line.split()
        object_name = None
        modifiers = []
        
        for i, word in enumerate(words):
            if word == 'object' and i + 1 < len(words):
                object_name = words[i + 1].split(':')[0]
                break
        
        # Extract modifiers
        for word in words:
            if word in ['public', 'private', 'protected', 'internal']:
                modifiers.append(word)
        
        return KotlinNode(
            type='OBJECT',
            name=object_name,
            start_line=line_num,
            modifiers=modifiers,
            text=line
        )
    
    def _parse_function_declaration(self, line: str, line_num: int) -> KotlinNode:
        """Parse function declaration line."""
        # Extract function name
        fun_index = line.find('fun ')
        if fun_index == -1:
            return KotlinNode(type='FUNCTION', start_line=line_num, text=line)
        
        after_fun = line[fun_index + 4:].strip()
        
        # Handle extension functions
        if '.' in after_fun and '(' in after_fun:
            dot_index = after_fun.find('.')
            paren_index = after_fun.find('(')
            if dot_index < paren_index:
                # Extension function
                function_name = after_fun[dot_index + 1:paren_index].strip()
                receiver_type = after_fun[:dot_index].strip()
            else:
                function_name = after_fun.split('(')[0].strip()
                receiver_type = None
        else:
            function_name = after_fun.split('(')[0].strip()
            receiver_type = None
        
        # Extract modifiers
        modifiers = []
        words = line.split()
        for word in words:
            if word in ['public', 'private', 'protected', 'internal', 'open', 'override', 'abstract', 'final', 'suspend', 'inline', 'external']:
                modifiers.append(word)
        
        properties = {}
        if receiver_type:
            properties['receiver_type'] = receiver_type
            properties['is_extension'] = True
        
        return KotlinNode(
            type='FUNCTION',
            name=function_name,
            start_line=line_num,
            modifiers=modifiers,
            properties=properties,
            text=line
        )
    
    def _parse_property_declaration(self, line: str, line_num: int) -> KotlinNode:
        """Parse property declaration line."""
        words = line.split()
        property_name = None
        is_val = False
        is_var = False
        modifiers = []
        
        for i, word in enumerate(words):
            if word == 'val':
                is_val = True
                if i + 1 < len(words):
                    property_name = words[i + 1].split(':')[0].split('=')[0].strip()
            elif word == 'var':
                is_var = True
                if i + 1 < len(words):
                    property_name = words[i + 1].split(':')[0].split('=')[0].strip()
        
        # Extract modifiers
        for word in words:
            if word in ['public', 'private', 'protected', 'internal', 'open', 'override', 'abstract', 'final', 'const', 'lateinit']:
                modifiers.append(word)
        
        return KotlinNode(
            type='PROPERTY',
            name=property_name,
            start_line=line_num,
            modifiers=modifiers,
            properties={'is_val': is_val, 'is_var': is_var},
            text=line
        )
    
    def _parse_enum_declaration(self, line: str, line_num: int) -> KotlinNode:
        """Parse enum declaration line."""
        words = line.split()
        enum_name = None
        
        for i, word in enumerate(words):
            if word == 'class' and i + 1 < len(words):
                enum_name = words[i + 1].split('(')[0].split('<')[0].split(':')[0]
                break
        
        return KotlinNode(
            type='ENUM',
            name=enum_name,
            start_line=line_num,
            text=line
        )
    
    def _parse_annotation_declaration(self, line: str, line_num: int) -> KotlinNode:
        """Parse annotation declaration line."""
        words = line.split()
        annotation_name = None
        
        for i, word in enumerate(words):
            if word == 'class' and i + 1 < len(words):
                annotation_name = words[i + 1].split('(')[0].split('<')[0].split(':')[0]
                break
        
        return KotlinNode(
            type='ANNOTATION',
            name=annotation_name,
            start_line=line_num,
            text=line
        )
    
    def _parse_typealias_declaration(self, line: str, line_num: int) -> KotlinNode:
        """Parse typealias declaration line."""
        typealias_index = line.find('typealias')
        if typealias_index == -1:
            return KotlinNode(type='TYPEALIAS', start_line=line_num, text=line)
        
        after_typealias = line[typealias_index + 9:].strip()
        typealias_name = after_typealias.split('=')[0].strip()
        
        return KotlinNode(
            type='TYPEALIAS',
            name=typealias_name,
            start_line=line_num,
            text=line
        )

# Export public interface
__all__ = ['KotlinParserAgent', 'KotlinNode', 'KotlinParseInfo'] 