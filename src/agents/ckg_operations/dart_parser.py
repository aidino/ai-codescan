"""
DartParserAgent - Agent xử lý parsing Dart code.

Agent này sử dụng Dart analyzer command line tool để phân tích mã Dart,
extract AST information và provide structured data về Dart code structure.
"""

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
import shutil
import logging

# Use standard logging instead of custom DebugLogger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DartNode:
    """Represents a Dart AST node."""
    type: str
    name: Optional[str] = None
    parent: Optional['DartNode'] = None
    children: List['DartNode'] = None
    properties: Dict[str, Any] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    column_start: Optional[int] = None
    column_end: Optional[int] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.properties is None:
            self.properties = {}


@dataclass
class DartParseInfo:
    """Information about parsed Dart file."""
    file_path: str
    package_name: Optional[str] = None
    library_name: Optional[str] = None
    imports: List[str] = None
    exports: List[str] = None
    classes: List[str] = None
    mixins: List[str] = None
    extensions: List[str] = None
    functions: List[str] = None
    variables: List[str] = None
    enums: List[str] = None
    typedefs: List[str] = None
    dependencies: List[str] = None
    ast_root: Optional[DartNode] = None
    analysis_issues: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.imports is None:
            self.imports = []
        if self.exports is None:
            self.exports = []
        if self.classes is None:
            self.classes = []
        if self.mixins is None:
            self.mixins = []
        if self.extensions is None:
            self.extensions = []
        if self.functions is None:
            self.functions = []
        if self.variables is None:
            self.variables = []
        if self.enums is None:
            self.enums = []
        if self.typedefs is None:
            self.typedefs = []
        if self.dependencies is None:
            self.dependencies = []
        if self.analysis_issues is None:
            self.analysis_issues = []


class DartParserAgent:
    """Agent để parse Dart code sử dụng Dart analyzer command line tool."""

    def __init__(self):
        """Initialize DartParserAgent."""
        self.dart_command = self._find_dart_command()
        if not self.dart_command:
            logger.warning("Dart command not found in system PATH")

    def _find_dart_command(self) -> Optional[str]:
        """Find dart command in system PATH."""
        try:
            # Try to find dart command
            dart_cmd = shutil.which("dart")
            if dart_cmd:
                # Verify dart command works
                result = subprocess.run(
                    [dart_cmd, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    logger.info(f"Found Dart command: {dart_cmd}")
                    logger.info(f"Dart version: {result.stderr.strip()}")
                    return dart_cmd
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            logger.warning(f"Error finding Dart command: {e}")
        
        return None

    def can_parse(self, file_path: str) -> bool:
        """Check if agent can parse given file."""
        if not self.dart_command:
            return False
        
        return file_path.lower().endswith('.dart')

    def parse_file(self, file_path: str) -> Optional[DartParseInfo]:
        """Parse single Dart file."""
        if not self.can_parse(file_path):
            logger.warning(f"Cannot parse file: {file_path}")
            return None

        try:
            # Create parse info object
            parse_info = DartParseInfo(file_path=file_path)
            
            # Run dart analyze to get analysis information
            analysis_result = self._run_dart_analyze(file_path)
            if analysis_result:
                parse_info.analysis_issues = analysis_result.get('diagnostics', [])
            
            # Extract basic structure information from file content
            self._extract_file_structure(file_path, parse_info)
            
            # Try to extract more detailed AST using dartdoc_json if available
            self._extract_detailed_ast(file_path, parse_info)
            
            logger.info(f"Successfully parsed Dart file: {file_path}")
            return parse_info
            
        except Exception as e:
            logger.error(f"Error parsing Dart file {file_path}: {e}")
            return None

    def parse_files(self, file_paths: List[str]) -> List[DartParseInfo]:
        """Parse multiple Dart files."""
        results = []
        for file_path in file_paths:
            parse_info = self.parse_file(file_path)
            if parse_info:
                results.append(parse_info)
        return results

    def parse_directory(self, directory_path: str) -> List[DartParseInfo]:
        """Parse all Dart files in directory recursively."""
        dart_files = []
        directory = Path(directory_path)
        
        if directory.is_dir():
            dart_files = list(directory.rglob("*.dart"))
        
        file_paths = [str(f) for f in dart_files]
        return self.parse_files(file_paths)

    def parse_dart_files(self, files: List[Tuple[str, str]]) -> List:
        """
        Parse list of Dart files for CodeParserCoordinatorAgent interface.
        
        Args:
            files: List of (file_path, relative_path) tuples
            
        Returns:
            List[ParsedFile]: List of parsed files
        """
        from . import ParsedFile  # Import here to avoid circular imports
        
        parsed_files = []
        
        for file_path, relative_path in files:
            try:
                # Parse the Dart file
                parse_info = self.parse_file(file_path)
                
                if parse_info:
                    # Count lines
                    lines_count = self._count_file_lines(file_path)
                    
                    # Create ParsedFile object
                    parsed_file = ParsedFile(
                        file_path=file_path,
                        relative_path=relative_path,
                        language='Dart',
                        ast_tree=parse_info.ast_root,
                        parse_success=True,
                        error_message=None,
                        nodes_count=self._count_dart_nodes(parse_info),
                        lines_count=lines_count
                    )
                else:
                    # Parse failed
                    parsed_file = ParsedFile(
                        file_path=file_path,
                        relative_path=relative_path,
                        language='Dart',
                        ast_tree=None,
                        parse_success=False,
                        error_message="Failed to parse Dart file",
                        nodes_count=0,
                        lines_count=self._count_file_lines(file_path)
                    )
                
                parsed_files.append(parsed_file)
                
            except Exception as e:
                logger.error(f"Error parsing Dart file {file_path}: {e}")
                parsed_file = ParsedFile(
                    file_path=file_path,
                    relative_path=relative_path,
                    language='Dart',
                    ast_tree=None,
                    parse_success=False,
                    error_message=str(e),
                    nodes_count=0,
                    lines_count=self._count_file_lines(file_path)
                )
                parsed_files.append(parsed_file)
        
        return parsed_files

    def _run_dart_analyze(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Run dart analyze command on file and return JSON results."""
        if not self.dart_command:
            return None
            
        try:
            # Run dart analyze with JSON format
            result = subprocess.run(
                [self.dart_command, "analyze", "--format=json", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse JSON output
            if result.stdout.strip():
                try:
                    return json.loads(result.stdout.strip())
                except json.JSONDecodeError:
                    # Try to extract JSON from output (in case there's extra text)
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.startswith('{') and line.endswith('}'):
                            return json.loads(line)
            
            return {}
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            logger.warning(f"Error running dart analyze on {file_path}: {e}")
            return None

    def _extract_file_structure(self, file_path: str, parse_info: DartParseInfo):
        """Extract basic structure information from Dart file content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Extract imports
                if line.startswith('import '):
                    import_match = self._extract_quoted_value(line)
                    if import_match:
                        parse_info.imports.append(import_match)
                        # Add to dependencies if it's a package import
                        if import_match.startswith('package:'):
                            package_name = import_match.split('/')[0].replace('package:', '')
                            if package_name not in parse_info.dependencies:
                                parse_info.dependencies.append(package_name)
                
                # Extract exports
                elif line.startswith('export '):
                    export_match = self._extract_quoted_value(line)
                    if export_match:
                        parse_info.exports.append(export_match)
                
                # Extract library name
                elif line.startswith('library '):
                    parse_info.library_name = line.replace('library ', '').replace(';', '').strip()
                
                # Extract classes
                elif line.startswith('class ') or ' class ' in line:
                    class_name = self._extract_declaration_name(line, 'class')
                    if class_name:
                        parse_info.classes.append(class_name)
                
                # Extract mixins
                elif line.startswith('mixin ') or ' mixin ' in line:
                    mixin_name = self._extract_declaration_name(line, 'mixin')
                    if mixin_name:
                        parse_info.mixins.append(mixin_name)
                
                # Extract extensions
                elif line.startswith('extension ') or ' extension ' in line:
                    extension_name = self._extract_declaration_name(line, 'extension')
                    if extension_name:
                        parse_info.extensions.append(extension_name)
                
                # Extract enums
                elif line.startswith('enum ') or ' enum ' in line:
                    enum_name = self._extract_declaration_name(line, 'enum')
                    if enum_name:
                        parse_info.enums.append(enum_name)
                
                # Extract typedefs
                elif line.startswith('typedef ') or ' typedef ' in line:
                    typedef_name = self._extract_declaration_name(line, 'typedef')
                    if typedef_name:
                        parse_info.typedefs.append(typedef_name)
                
                # Extract top-level functions (improved logic)
                elif self._is_function_declaration(line):
                    # Check if we're inside a class/mixin/extension
                    if not self._is_inside_class_context(lines, i):
                        function_name = self._extract_function_name(line)
                        if function_name:
                            parse_info.functions.append(function_name)
            
            # Extract package name from file path or pubspec.yaml
            parse_info.package_name = self._extract_package_name(file_path)
            
        except Exception as e:
            logger.warning(f"Error extracting structure from {file_path}: {e}")

    def _extract_detailed_ast(self, file_path: str, parse_info: DartParseInfo):
        """Try to extract detailed AST using dartdoc_json if available."""
        try:
            # Check if dartdoc_json is available
            result = subprocess.run(
                ["dart", "pub", "global", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if "dartdoc_json" in result.stdout:
                # Run dartdoc_json to extract detailed AST
                with tempfile.TemporaryDirectory() as temp_dir:
                    output_file = os.path.join(temp_dir, "ast_output.json")
                    
                    result = subprocess.run(
                        ["dartdoc_json", "--output", output_file, file_path],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0 and os.path.exists(output_file):
                        with open(output_file, 'r', encoding='utf-8') as f:
                            ast_data = json.load(f)
                        
                        # Process AST data and create DartNode structure
                        parse_info.ast_root = self._process_ast_data(ast_data)
                        
                        # Extract additional information from AST
                        self._extract_from_ast(ast_data, parse_info)
            
        except Exception as e:
            logger.debug(f"Could not extract detailed AST for {file_path}: {e}")

    def _process_ast_data(self, ast_data: List[Dict[str, Any]]) -> Optional[DartNode]:
        """Process AST data from dartdoc_json and create DartNode structure."""
        if not ast_data:
            return None
        
        # Create root node
        root = DartNode(type="CompilationUnit", name="root")
        
        for compilation_unit in ast_data:
            source = compilation_unit.get('source', '')
            declarations = compilation_unit.get('declarations', [])
            
            unit_node = DartNode(
                type="CompilationUnit",
                name=source,
                parent=root,
                properties={'source': source}
            )
            root.children.append(unit_node)
            
            # Process declarations
            for declaration in declarations:
                decl_node = self._process_declaration(declaration, unit_node)
                if decl_node:
                    unit_node.children.append(decl_node)
        
        return root

    def _process_declaration(self, declaration: Dict[str, Any], parent: DartNode) -> Optional[DartNode]:
        """Process a declaration and create DartNode."""
        kind = declaration.get('kind', '')
        name = declaration.get('name', '')
        
        node = DartNode(
            type=kind,
            name=name,
            parent=parent,
            properties=declaration.copy()
        )
        
        # Process members if they exist
        members = declaration.get('members', [])
        for member in members:
            member_node = self._process_declaration(member, node)
            if member_node:
                node.children.append(member_node)
        
        return node

    def _extract_from_ast(self, ast_data: List[Dict[str, Any]], parse_info: DartParseInfo):
        """Extract additional information from AST data."""
        for compilation_unit in ast_data:
            # Extract directives (imports, exports, etc.)
            directives = compilation_unit.get('directives', [])
            for directive in directives:
                kind = directive.get('kind', '')
                uri = directive.get('uri', '')
                
                if kind == 'import' and uri:
                    if uri not in parse_info.imports:
                        parse_info.imports.append(uri)
                elif kind == 'export' and uri:
                    if uri not in parse_info.exports:
                        parse_info.exports.append(uri)

    def _extract_quoted_value(self, line: str) -> Optional[str]:
        """Extract quoted value from line (e.g., import 'package:...')."""
        if "'" in line:
            start = line.find("'") + 1
            end = line.find("'", start)
            if end != -1:
                return line[start:end]
        elif '"' in line:
            start = line.find('"') + 1
            end = line.find('"', start)
            if end != -1:
                return line[start:end]
        return None

    def _extract_declaration_name(self, line: str, keyword: str) -> Optional[str]:
        """Extract declaration name from line."""
        try:
            # Remove comments
            if '//' in line:
                line = line[:line.find('//')]
            
            # Find the keyword
            keyword_index = line.find(keyword)
            if keyword_index == -1:
                return None
            
            # Extract the part after keyword
            after_keyword = line[keyword_index + len(keyword):].strip()
            
            # Extract name (first word before space, < or {)
            name_part = after_keyword.split()[0] if after_keyword.split() else ""
            
            # Clean name (remove generic parameters, etc.)
            name = ""
            for char in name_part:
                if char.isalnum() or char == '_':
                    name += char
                elif char in ['<', '{', '(', ' ']:
                    break
            
            return name if name else None
            
        except Exception:
            return None

    def _is_function_declaration(self, line: str) -> bool:
        """Check if line contains a function declaration."""
        # Simple heuristic for function declarations
        line = line.strip()
        
        # Skip comments and non-functional lines
        if not line or line.startswith('//') or line.startswith('/*'):
            return False
            
        # Skip class-related keywords
        if any(keyword in line for keyword in ['class ', 'enum ', 'mixin ', 'extension ', 'typedef ']):
            return False
            
        # Skip obviously non-declaration lines
        if line.startswith('return ') or line.startswith('throw ') or line.startswith('@'):
            return False
            
        # Check for function patterns
        has_parentheses = '(' in line and ')' in line
        has_body_or_arrow = '{' in line or ';' in line or '=>' in line
        
        if not (has_parentheses and has_body_or_arrow):
            return False
            
        # Look for patterns that suggest this is a declaration:
        # 1. Line starts with return type or modifier keywords
        # 2. Line contains function name followed by parentheses
        
        # Split line to analyze structure
        words = line.split()
        if not words:
            return False
            
        # Check if line looks like a function declaration
        # Should have structure like: [modifiers] [returnType] functionName(params) [body]
        
        # Find the word with parentheses
        func_word_index = -1
        for i, word in enumerate(words):
            if '(' in word:
                func_word_index = i
                break
                
        if func_word_index == -1:
            return False
            
        # If the parentheses word is the first word, it might be a function call
        # unless it has typical declaration keywords before it
        if func_word_index == 0:
            # First word has parentheses - likely a function call unless it's a constructor
            # or getter/setter
            if not any(keyword in line for keyword in ['get ', 'set ', 'operator ']):
                return False
        
        return True

    def _extract_function_name(self, line: str) -> Optional[str]:
        """Extract function name from function declaration line."""
        try:
            # Remove comments first
            if '//' in line:
                line = line[:line.find('//')]
            
            line = line.strip()
            
            # Handle special cases first
            # Pattern for getters: "Type get name => ..." 
            if ' get ' in line:
                parts = line.split(' get ')
                if len(parts) >= 2:
                    getter_part = parts[1].strip()
                    # Extract name before '=>' or '{'
                    if '=>' in getter_part:
                        getter_name = getter_part.split('=>')[0].strip()
                    elif '{' in getter_part:
                        getter_name = getter_part.split('{')[0].strip()
                    else:
                        getter_name = getter_part.split()[0] if getter_part.split() else None
                    
                    if getter_name and getter_name.isidentifier():
                        return getter_name
            
            # Pattern for setters: "set name(value) => ..." or "set name(value) {"
            if ' set ' in line:
                parts = line.split(' set ')
                if len(parts) >= 2:
                    setter_part = parts[1].strip()
                    # Extract name before '('
                    if '(' in setter_part:
                        setter_name = setter_part.split('(')[0].strip()
                        if setter_name and setter_name.isidentifier():
                            return setter_name
            
            # Handle different function declaration patterns
            # Pattern 1: returnType functionName(params)
            # Pattern 2: functionName(params) 
            # Pattern 3: modifier returnType functionName(params)
            
            # Find the opening parenthesis
            paren_index = line.find('(')
            if paren_index == -1:
                return None
                
            # Extract the part before parentheses
            before_paren = line[:paren_index].strip()
            
            # Split by spaces and get the last part (should be function name)
            words = before_paren.split()
            if not words:
                return None
                
            # The function name should be the last word before parentheses
            func_name = words[-1]
            
            # Clean the name (remove any non-alphanumeric except underscore)
            clean_name = ""
            for char in func_name:
                if char.isalnum() or char == '_':
                    clean_name += char
                else:
                    break
                    
            # Validate it's a reasonable function name
            if clean_name and clean_name[0].isalpha() and clean_name not in ['if', 'for', 'while', 'switch', 'return']:
                return clean_name
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting function name from '{line}': {e}")
            return None

    def _is_inside_class_context(self, lines: List[str], current_line_index: int) -> bool:
        """Check if current line is inside a class/mixin/extension context."""
        # Simple but more accurate heuristic: track brace depth from the start
        brace_depth = 0
        inside_container = False
        container_depth = 0
        
        for i in range(current_line_index + 1):  # Go from start to current line
            line = lines[i].strip()
            
            # Check if this line starts a class/mixin/extension
            if any(line.startswith(keyword) for keyword in ['class ', 'mixin ', 'extension ']):
                if '{' in line:
                    # Container declaration with opening brace on same line
                    inside_container = True
                    container_depth = brace_depth + 1
                elif i < len(lines) - 1:
                    # Check next line for opening brace
                    next_line = lines[i + 1].strip()
                    if next_line == '{':
                        inside_container = True
                        container_depth = brace_depth + 1
            
            # Count braces on this line
            opening_braces = line.count('{')
            closing_braces = line.count('}')
            
            brace_depth += opening_braces - closing_braces
            
            # If we were inside a container and depth drops below container depth,
            # we've exited the container
            if inside_container and brace_depth < container_depth:
                inside_container = False
                container_depth = 0
        
        return inside_container

    def _extract_package_name(self, file_path: str) -> Optional[str]:
        """Extract package name from file path or pubspec.yaml."""
        try:
            # Try to find pubspec.yaml
            current_dir = Path(file_path).parent
            while current_dir != current_dir.parent:
                pubspec_path = current_dir / "pubspec.yaml"
                if pubspec_path.exists():
                    with open(pubspec_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    for line in content.split('\n'):
                        if line.strip().startswith('name:'):
                            package_name = line.split(':', 1)[1].strip()
                            # Remove quotes if present
                            package_name = package_name.strip('"\'')
                            return package_name
                    break
                current_dir = current_dir.parent
            
            # Fallback: extract from file path
            path_parts = Path(file_path).parts
            if 'lib' in path_parts:
                lib_index = path_parts.index('lib')
                if lib_index > 0:
                    return path_parts[lib_index - 1]
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not extract package name for {file_path}: {e}")
            return None

    def _count_dart_nodes(self, parse_info: DartParseInfo) -> int:
        """Count total nodes in Dart parse info."""
        node_count = 0
        
        # Count basic extracted elements
        node_count += len(parse_info.imports)
        node_count += len(parse_info.exports)
        node_count += len(parse_info.classes)
        node_count += len(parse_info.mixins)
        node_count += len(parse_info.extensions)
        node_count += len(parse_info.functions)
        node_count += len(parse_info.variables)
        node_count += len(parse_info.enums)
        node_count += len(parse_info.typedefs)
        
        # Count AST nodes if available
        if parse_info.ast_root:
            node_count += self._count_ast_nodes_recursive(parse_info.ast_root)
        
        return node_count

    def _count_ast_nodes_recursive(self, node: DartNode) -> int:
        """Count AST nodes recursively."""
        count = 1  # Count the current node
        
        if node.children:
            for child in node.children:
                count += self._count_ast_nodes_recursive(child)
        
        return count

    def _count_file_lines(self, file_path: str) -> int:
        """Count lines in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return len(f.readlines())
        except Exception as e:
            logger.warning(f"Could not count lines in {file_path}: {e}")
            return 0 