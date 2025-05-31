"""
Java Parser Agent for CKG Operations Team.

Handles Java AST parsing using JavaParser library via subprocess.
Converts Java code into AST representation for CKG building.
"""

import os
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

from .code_parser_coordinator import ParsedFile, ParseResult


@dataclass
class JavaNode:
    """Represents a Java AST node."""
    node_type: str
    name: Optional[str] = None
    modifiers: List[str] = None
    start_line: int = 0
    end_line: int = 0
    children: List['JavaNode'] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.modifiers is None:
            self.modifiers = []
        if self.children is None:
            self.children = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class JavaParseInfo:
    """Information extracted from Java parsing."""
    package_name: Optional[str] = None
    imports: List[str] = None
    classes: List[str] = None
    interfaces: List[str] = None
    methods: List[str] = None
    fields: List[str] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.imports is None:
            self.imports = []
        if self.classes is None:
            self.classes = []
        if self.interfaces is None:
            self.interfaces = []
        if self.methods is None:
            self.methods = []
        if self.fields is None:
            self.fields = []
        if self.dependencies is None:
            self.dependencies = []


class JavaParserAgent:
    """
    Agent responsible for parsing Java source code into AST representation.
    
    Uses JavaParser library via subprocess to handle Java parsing without
    requiring Java runtime in the main application.
    """
    
    def __init__(self, javaparser_jar_path: Optional[str] = None):
        """
        Initialize Java Parser Agent.
        
        Args:
            javaparser_jar_path: Path to JavaParser JAR file.
                                If None, will try to download automatically.
        """
        self.javaparser_jar_path = javaparser_jar_path
        self.java_cmd = self._find_java_command()
        self._ensure_javaparser_available()
        
    def _find_java_command(self) -> str:
        """Find Java command in system PATH."""
        java_commands = ['java', 'java.exe']
        
        for cmd in java_commands:
            try:
                result = subprocess.run(
                    [cmd, '-version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    logger.info(f"Found Java command: {cmd}")
                    return cmd
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
                
        raise RuntimeError("Java not found in system PATH. Please install Java JRE/JDK.")
    
    def _ensure_javaparser_available(self):
        """Ensure JavaParser JAR is available."""
        if self.javaparser_jar_path and os.path.exists(self.javaparser_jar_path):
            logger.info(f"Using existing JavaParser JAR: {self.javaparser_jar_path}")
            return
            
        # Try to download JavaParser JAR
        jar_dir = Path.home() / '.ai_codescan' / 'jars'
        jar_dir.mkdir(parents=True, exist_ok=True)
        
        jar_path = jar_dir / 'javaparser-core-3.26.4.jar'
        
        if jar_path.exists():
            self.javaparser_jar_path = str(jar_path)
            logger.info(f"Using cached JavaParser JAR: {jar_path}")
            return
            
        # Download JavaParser JAR
        try:
            import requests
            url = "https://repo1.maven.org/maven2/com/github/javaparser/javaparser-core/3.26.4/javaparser-core-3.26.4.jar"
            
            logger.info("Downloading JavaParser JAR...")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(jar_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            self.javaparser_jar_path = str(jar_path)
            logger.success(f"Downloaded JavaParser JAR: {jar_path}")
            
        except Exception as e:
            logger.error(f"Failed to download JavaParser JAR: {e}")
            raise RuntimeError(f"JavaParser JAR not available: {e}")
    
    def parse_java_files(self, java_files: List[Tuple[str, str]]) -> List[ParsedFile]:
        """
        Parse multiple Java files.
        
        Args:
            java_files: List of (file_path, relative_path) tuples
            
        Returns:
            List of ParsedFile objects
        """
        parsed_files = []
        
        for file_path, relative_path in java_files:
            try:
                parsed_file = self._parse_java_file(file_path, relative_path)
                parsed_files.append(parsed_file)
                
            except Exception as e:
                logger.error(f"Failed to parse Java file {relative_path}: {e}")
                parsed_files.append(ParsedFile(
                    file_path=file_path,
                    relative_path=relative_path,
                    language='Java',
                    ast_tree=None,
                    parse_success=False,
                    error_message=str(e),
                    lines_count=self._count_file_lines(file_path)
                ))
                
        return parsed_files
    
    def _parse_java_file(self, file_path: str, relative_path: str) -> ParsedFile:
        """
        Parse a single Java file using JavaParser.
        
        Args:
            file_path: Full path to Java file
            relative_path: Relative path for display
            
        Returns:
            ParsedFile object with Java AST information
        """
        try:
            # Create temporary script to run JavaParser
            java_ast_json = self._run_javaparser(file_path)
            
            # Parse the AST JSON
            java_ast = self._parse_ast_json(java_ast_json)
            
            # Extract information
            parse_info = self._extract_java_info(java_ast)
            
            # Count lines and nodes
            lines_count = self._count_file_lines(file_path)
            nodes_count = self._count_java_nodes(java_ast)
            
            return ParsedFile(
                file_path=file_path,
                relative_path=relative_path,
                language='Java',
                ast_tree={
                    'ast_nodes': java_ast,
                    'parse_info': parse_info.__dict__
                },
                parse_success=True,
                nodes_count=nodes_count,
                lines_count=lines_count
            )
            
        except subprocess.TimeoutExpired:
            logger.error(f"JavaParser timeout for file: {relative_path}")
            return ParsedFile(
                file_path=file_path,
                relative_path=relative_path,
                language='Java',
                ast_tree=None,
                parse_success=False,
                error_message="JavaParser execution timeout",
                lines_count=self._count_file_lines(file_path)
            )
            
        except subprocess.CalledProcessError as e:
            logger.error(f"JavaParser failed for file {relative_path}: {e.stderr}")
            return ParsedFile(
                file_path=file_path,
                relative_path=relative_path,
                language='Java',
                ast_tree=None,
                parse_success=False,
                error_message=f"JavaParser error: {e.stderr}",
                lines_count=self._count_file_lines(file_path)
            )
            
        except Exception as e:
            logger.error(f"Unexpected error parsing {relative_path}: {e}")
            return ParsedFile(
                file_path=file_path,
                relative_path=relative_path,
                language='Java',
                ast_tree=None,
                parse_success=False,
                error_message=f"Parsing error: {str(e)}",
                lines_count=self._count_file_lines(file_path)
            )
    
    def _run_javaparser(self, java_file_path: str) -> Dict[str, Any]:
        """
        Run JavaParser on a Java file via subprocess.
        
        Args:
            java_file_path: Path to Java file to parse
            
        Returns:
            AST as JSON dictionary
        """
        # Create temporary Java program to run JavaParser
        java_parser_code = f'''
import com.github.javaparser.JavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.Node;
import com.github.javaparser.ast.body.*;
import com.github.javaparser.ast.expr.*;
import com.github.javaparser.ast.stmt.*;
import com.github.javaparser.ast.type.*;
import com.github.javaparser.ast.ImportDeclaration;
import com.github.javaparser.ast.PackageDeclaration;
import java.io.File;
import java.io.FileNotFoundException;
import java.util.List;
import java.util.Optional;

public class JavaParserRunner {{
    public static void main(String[] args) {{
        try {{
            JavaParser parser = new JavaParser();
            CompilationUnit cu = parser.parse(new File("{java_file_path}")).getResult().get();
            
            System.out.println("{{");
            System.out.println("\\"node_type\\": \\"CompilationUnit\\",");
            
            // Package declaration
            Optional<PackageDeclaration> pkg = cu.getPackageDeclaration();
            if (pkg.isPresent()) {{
                System.out.println("\\"package\\": \\"" + pkg.get().getNameAsString() + "\\",");
            }}
            
            // Imports
            List<ImportDeclaration> imports = cu.getImports();
            System.out.print("\\"imports\\": [");
            for (int i = 0; i < imports.size(); i++) {{
                System.out.print("\\"" + imports.get(i).getNameAsString() + "\\"");
                if (i < imports.size() - 1) System.out.print(", ");
            }}
            System.out.println("],");
            
            // Types (classes, interfaces, enums)
            System.out.print("\\"types\\": [");
            List<TypeDeclaration<?>> types = cu.getTypes();
            for (int i = 0; i < types.size(); i++) {{
                TypeDeclaration<?> type = types.get(i);
                System.out.print("{{");
                System.out.print("\\"type\\": \\"" + type.getClass().getSimpleName() + "\\", ");
                System.out.print("\\"name\\": \\"" + type.getNameAsString() + "\\"");
                
                if (type instanceof ClassOrInterfaceDeclaration) {{
                    ClassOrInterfaceDeclaration clazz = (ClassOrInterfaceDeclaration) type;
                    System.out.print(", \\"isInterface\\": " + clazz.isInterface());
                    
                    // Methods
                    List<MethodDeclaration> methods = clazz.getMethods();
                    System.out.print(", \\"methods\\": [");
                    for (int j = 0; j < methods.size(); j++) {{
                        MethodDeclaration method = methods.get(j);
                        System.out.print("\\"" + method.getNameAsString() + "\\"");
                        if (j < methods.size() - 1) System.out.print(", ");
                    }}
                    System.out.print("]");
                    
                    // Fields
                    List<FieldDeclaration> fields = clazz.getFields();
                    System.out.print(", \\"fields\\": [");
                    for (int j = 0; j < fields.size(); j++) {{
                        FieldDeclaration field = fields.get(j);
                        field.getVariables().forEach(var -> {{
                            System.out.print("\\"" + var.getNameAsString() + "\\"");
                        }});
                        if (j < fields.size() - 1) System.out.print(", ");
                    }}
                    System.out.print("]");
                }}
                
                System.out.print("}}");
                if (i < types.size() - 1) System.out.print(", ");
            }}
            System.out.println("]");
            
            System.out.println("}}");
            
        }} catch (FileNotFoundException e) {{
            System.err.println("File not found: " + e.getMessage());
            System.exit(1);
        }} catch (Exception e) {{
            System.err.println("Parsing error: " + e.getMessage());
            System.exit(1);
        }}
    }}
}}
'''
        
        # Create temporary files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write Java parser runner
            runner_file = os.path.join(temp_dir, 'JavaParserRunner.java')
            with open(runner_file, 'w', encoding='utf-8') as f:
                f.write(java_parser_code)
            
            # Compile Java parser runner
            compile_cmd = [
                self.java_cmd, '-cp', self.javaparser_jar_path,
                '-d', temp_dir,
                runner_file
            ]
            
            result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode, compile_cmd, 
                    stdout=result.stdout, stderr=result.stderr
                )
            
            # Run Java parser
            run_cmd = [
                self.java_cmd, '-cp',
                f"{temp_dir}{os.pathsep}{self.javaparser_jar_path}",
                'JavaParserRunner'
            ]
            
            result = subprocess.run(
                run_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode, run_cmd,
                    stdout=result.stdout, stderr=result.stderr
                )
            
            # Parse JSON output
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JavaParser JSON output: {e}")
                logger.debug(f"JavaParser output: {result.stdout}")
                raise
    
    def _parse_ast_json(self, ast_json: Dict[str, Any]) -> JavaNode:
        """
        Parse JavaParser JSON output into JavaNode structure.
        
        Args:
            ast_json: JSON output from JavaParser
            
        Returns:
            JavaNode representing the AST
        """
        root = JavaNode(
            node_type='CompilationUnit',
            name='root',
            metadata=ast_json
        )
        
        # Extract types (classes, interfaces, etc.)
        if 'types' in ast_json:
            for type_info in ast_json['types']:
                type_node = JavaNode(
                    node_type=type_info.get('type', 'Unknown'),
                    name=type_info.get('name'),
                    metadata=type_info
                )
                
                # Add methods as children
                if 'methods' in type_info:
                    for method_name in type_info['methods']:
                        method_node = JavaNode(
                            node_type='MethodDeclaration',
                            name=method_name
                        )
                        type_node.children.append(method_node)
                
                # Add fields as children
                if 'fields' in type_info:
                    for field_name in type_info['fields']:
                        field_node = JavaNode(
                            node_type='FieldDeclaration',
                            name=field_name
                        )
                        type_node.children.append(field_node)
                
                root.children.append(type_node)
        
        return root
    
    def _extract_java_info(self, java_ast: JavaNode) -> JavaParseInfo:
        """
        Extract Java-specific information from AST.
        
        Args:
            java_ast: JavaNode representing the AST
            
        Returns:
            JavaParseInfo with extracted information
        """
        info = JavaParseInfo()
        
        if java_ast.metadata:
            # Package information
            info.package_name = java_ast.metadata.get('package')
            
            # Imports
            info.imports = java_ast.metadata.get('imports', [])
            
            # Extract class and interface information
            types = java_ast.metadata.get('types', [])
            for type_info in types:
                type_name = type_info.get('name')
                if type_name:
                    if type_info.get('isInterface', False):
                        info.interfaces.append(type_name)
                    else:
                        info.classes.append(type_name)
                    
                    # Extract methods and fields
                    info.methods.extend(type_info.get('methods', []))
                    info.fields.extend(type_info.get('fields', []))
            
            # Extract dependencies from imports
            for import_name in info.imports:
                # Extract package dependencies
                if '.' in import_name:
                    package_parts = import_name.split('.')
                    if len(package_parts) >= 2:
                        dependency = '.'.join(package_parts[:-1])
                        if dependency not in info.dependencies:
                            info.dependencies.append(dependency)
        
        return info
    
    def _count_java_nodes(self, java_ast: JavaNode) -> int:
        """
        Count total number of nodes in Java AST.
        
        Args:
            java_ast: JavaNode representing the AST
            
        Returns:
            Total node count
        """
        count = 1  # Count current node
        for child in java_ast.children:
            count += self._count_java_nodes(child)
        return count
    
    def _count_file_lines(self, file_path: str) -> int:
        """
        Count lines in a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Line count
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except Exception:
            return 0 