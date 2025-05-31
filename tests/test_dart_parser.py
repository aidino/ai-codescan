"""
Tests for DartParserAgent.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock

from src.agents.ckg_operations.dart_parser import DartParserAgent, DartParseInfo, DartNode


class TestDartParserAgent(unittest.TestCase):
    """Test cases for DartParserAgent."""

    def setUp(self):
        """Set up test fixtures."""
        self.agent = DartParserAgent()

    def test_init_with_dart_available(self):
        """Test initialization when Dart is available."""
        with patch('shutil.which', return_value='/usr/bin/dart'), \
             patch('subprocess.run') as mock_run:
            
            mock_run.return_value = Mock(returncode=0, stderr="Dart SDK version: 3.2.0")
            
            agent = DartParserAgent()
            self.assertIsNotNone(agent.dart_command)
            self.assertEqual(agent.dart_command, '/usr/bin/dart')

    def test_init_without_dart(self):
        """Test initialization when Dart is not available."""
        with patch('shutil.which', return_value=None):
            agent = DartParserAgent()
            self.assertIsNone(agent.dart_command)

    def test_can_parse_dart_file(self):
        """Test can_parse method with Dart files."""
        with patch('shutil.which', return_value='/usr/bin/dart'), \
             patch('subprocess.run', return_value=Mock(returncode=0, stderr="Dart 3.2.0")):
            
            agent = DartParserAgent()
            
            self.assertTrue(agent.can_parse("test.dart"))
            self.assertTrue(agent.can_parse("lib/main.dart"))
            self.assertTrue(agent.can_parse("TEST.DART"))
            self.assertFalse(agent.can_parse("test.py"))
            self.assertFalse(agent.can_parse("test.java"))

    def test_can_parse_without_dart_command(self):
        """Test can_parse when Dart command not available."""
        with patch('shutil.which', return_value=None):
            agent = DartParserAgent()
            self.assertFalse(agent.can_parse("test.dart"))

    def test_extract_quoted_value(self):
        """Test _extract_quoted_value method."""
        agent = DartParserAgent()
        
        # Single quotes
        self.assertEqual(
            agent._extract_quoted_value("import 'package:flutter/material.dart';"),
            "package:flutter/material.dart"
        )
        
        # Double quotes
        self.assertEqual(
            agent._extract_quoted_value('import "dart:async";'),
            "dart:async"
        )
        
        # No quotes
        self.assertIsNone(agent._extract_quoted_value("import something"))

    def test_extract_declaration_name(self):
        """Test _extract_declaration_name method."""
        agent = DartParserAgent()
        
        # Class declarations
        self.assertEqual(
            agent._extract_declaration_name("class MyWidget extends StatelessWidget {", "class"),
            "MyWidget"
        )
        
        self.assertEqual(
            agent._extract_declaration_name("abstract class AbstractWidget {", "class"),
            "AbstractWidget"
        )
        
        # Mixin declarations
        self.assertEqual(
            agent._extract_declaration_name("mixin MyMixin {", "mixin"),
            "MyMixin"
        )
        
        # Extension declarations
        self.assertEqual(
            agent._extract_declaration_name("extension StringExtensions on String {", "extension"),
            "StringExtensions"
        )
        
        # With generics
        self.assertEqual(
            agent._extract_declaration_name("class MyClass<T> {", "class"),
            "MyClass"
        )

    def test_is_function_declaration(self):
        """Test _is_function_declaration method."""
        agent = DartParserAgent()
        
        # Valid function declarations
        self.assertTrue(agent._is_function_declaration("void main() {"))
        self.assertTrue(agent._is_function_declaration("String getName() => 'test';"))
        self.assertTrue(agent._is_function_declaration("int calculate(int a, int b);"))
        
        # Invalid cases
        self.assertFalse(agent._is_function_declaration("class MyClass {"))
        self.assertFalse(agent._is_function_declaration("// void main() {"))
        self.assertFalse(agent._is_function_declaration("enum Color {"))

    def test_extract_function_name(self):
        """Test _extract_function_name method."""
        agent = DartParserAgent()
        
        self.assertEqual(agent._extract_function_name("void main() {"), "main")
        self.assertEqual(agent._extract_function_name("String getName() => 'test';"), "getName")
        self.assertEqual(agent._extract_function_name("Future<int> fetchData() async {"), "fetchData")
        self.assertEqual(agent._extract_function_name("static bool isValid(String input) {"), "isValid")

    def test_extract_package_name_from_pubspec(self):
        """Test _extract_package_name method with pubspec.yaml."""
        agent = DartParserAgent()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create pubspec.yaml
            pubspec_content = """
name: my_flutter_app
description: A test Flutter application.
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
"""
            pubspec_path = Path(temp_dir) / "pubspec.yaml"
            with open(pubspec_path, 'w') as f:
                f.write(pubspec_content)
            
            # Create a dart file in lib directory
            lib_dir = Path(temp_dir) / "lib"
            lib_dir.mkdir()
            dart_file = lib_dir / "main.dart"
            dart_file.touch()
            
            package_name = agent._extract_package_name(str(dart_file))
            self.assertEqual(package_name, "my_flutter_app")

    def test_extract_file_structure(self):
        """Test _extract_file_structure method."""
        agent = DartParserAgent()
        
        dart_content = '''
library my_library;

import 'dart:async';
import 'package:flutter/material.dart';
export 'package:my_package/widgets.dart';

class MyWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container();
  }
}

mixin MyMixin {
  void mixinMethod();
}

extension StringExtensions on String {
  String get capitalize => this[0].toUpperCase() + this.substring(1);
}

enum Color { red, green, blue }

typedef StringCallback = void Function(String);

void main() {
  runApp(MyApp());
}

String getString() => 'test';
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dart', delete=False) as f:
            f.write(dart_content)
            f.flush()
            
            try:
                parse_info = DartParseInfo(file_path=f.name)
                agent._extract_file_structure(f.name, parse_info)
                
                # Check extracted information
                self.assertEqual(parse_info.library_name, "my_library")
                self.assertIn("dart:async", parse_info.imports)
                self.assertIn("package:flutter/material.dart", parse_info.imports)
                self.assertIn("package:my_package/widgets.dart", parse_info.exports)
                self.assertIn("MyWidget", parse_info.classes)
                self.assertIn("MyMixin", parse_info.mixins)
                self.assertIn("StringExtensions", parse_info.extensions)
                self.assertIn("Color", parse_info.enums)
                self.assertIn("StringCallback", parse_info.typedefs)
                self.assertIn("main", parse_info.functions)
                self.assertIn("getString", parse_info.functions)
                self.assertIn("flutter", parse_info.dependencies)
                
            finally:
                os.unlink(f.name)

    def test_run_dart_analyze(self):
        """Test _run_dart_analyze method."""
        agent = DartParserAgent()
        agent.dart_command = "/usr/bin/dart"
        
        # Mock successful analysis with issues
        mock_analysis_result = {
            "version": 1,
            "diagnostics": [
                {
                    "code": "unused_import",
                    "severity": "INFO",
                    "type": "HINT",
                    "location": {
                        "file": "/path/to/file.dart",
                        "range": {
                            "start": {"offset": 0, "line": 1, "column": 1},
                            "end": {"offset": 10, "line": 1, "column": 11}
                        }
                    },
                    "problemMessage": "Unused import.",
                    "correctionMessage": "Remove unused import."
                }
            ]
        }
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=json.dumps(mock_analysis_result),
                stderr=""
            )
            
            result = agent._run_dart_analyze("test.dart")
            
            self.assertIsNotNone(result)
            self.assertEqual(result["version"], 1)
            self.assertEqual(len(result["diagnostics"]), 1)
            self.assertEqual(result["diagnostics"][0]["code"], "unused_import")

    def test_run_dart_analyze_no_issues(self):
        """Test _run_dart_analyze with no issues."""
        agent = DartParserAgent()
        agent.dart_command = "/usr/bin/dart"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="",
                stderr=""
            )
            
            result = agent._run_dart_analyze("test.dart")
            
            self.assertEqual(result, {})

    def test_run_dart_analyze_command_not_available(self):
        """Test _run_dart_analyze when dart command not available."""
        agent = DartParserAgent()
        agent.dart_command = None
        
        result = agent._run_dart_analyze("test.dart")
        self.assertIsNone(result)

    def test_process_ast_data(self):
        """Test _process_ast_data method."""
        agent = DartParserAgent()
        
        ast_data = [
            {
                "source": "lib/main.dart",
                "declarations": [
                    {
                        "kind": "class",
                        "name": "MyWidget",
                        "members": [
                            {
                                "kind": "method",
                                "name": "build",
                                "returns": "Widget"
                            }
                        ]
                    },
                    {
                        "kind": "function",
                        "name": "main",
                        "returns": "void"
                    }
                ]
            }
        ]
        
        root = agent._process_ast_data(ast_data)
        
        self.assertIsNotNone(root)
        self.assertEqual(root.type, "CompilationUnit")
        self.assertEqual(root.name, "root")
        self.assertEqual(len(root.children), 1)
        
        unit = root.children[0]
        self.assertEqual(unit.type, "CompilationUnit")
        self.assertEqual(unit.name, "lib/main.dart")
        self.assertEqual(len(unit.children), 2)
        
        class_node = unit.children[0]
        self.assertEqual(class_node.type, "class")
        self.assertEqual(class_node.name, "MyWidget")
        self.assertEqual(len(class_node.children), 1)
        
        method_node = class_node.children[0]
        self.assertEqual(method_node.type, "method")
        self.assertEqual(method_node.name, "build")

    def test_parse_file_success(self):
        """Test successful file parsing."""
        agent = DartParserAgent()
        agent.dart_command = "/usr/bin/dart"
        
        dart_content = '''
import 'dart:async';

class MyWidget {
  void method() {}
}
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dart', delete=False) as f:
            f.write(dart_content)
            f.flush()
            
            try:
                with patch.object(agent, '_run_dart_analyze', return_value={}), \
                     patch.object(agent, '_extract_detailed_ast'):
                    
                    result = agent.parse_file(f.name)
                    
                    self.assertIsNotNone(result)
                    self.assertIsInstance(result, DartParseInfo)
                    self.assertEqual(result.file_path, f.name)
                    self.assertIn("dart:async", result.imports)
                    self.assertIn("MyWidget", result.classes)
                    
            finally:
                os.unlink(f.name)

    def test_parse_file_invalid_file(self):
        """Test parsing non-Dart file."""
        agent = DartParserAgent()
        
        result = agent.parse_file("test.py")
        self.assertIsNone(result)

    def test_parse_files_multiple(self):
        """Test parsing multiple files."""
        agent = DartParserAgent()
        
        with patch.object(agent, 'parse_file') as mock_parse:
            mock_parse.side_effect = [
                DartParseInfo(file_path="file1.dart"),
                DartParseInfo(file_path="file2.dart"),
                None  # Failed to parse
            ]
            
            results = agent.parse_files(["file1.dart", "file2.dart", "file3.dart"])
            
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0].file_path, "file1.dart")
            self.assertEqual(results[1].file_path, "file2.dart")

    def test_parse_directory(self):
        """Test parsing directory."""
        agent = DartParserAgent()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some Dart files
            lib_dir = Path(temp_dir) / "lib"
            lib_dir.mkdir()
            
            (lib_dir / "main.dart").touch()
            (lib_dir / "widget.dart").touch()
            
            # Create subdirectory with Dart file
            sub_dir = lib_dir / "widgets"
            sub_dir.mkdir()
            (sub_dir / "button.dart").touch()
            
            # Create non-Dart file
            (lib_dir / "readme.txt").touch()
            
            with patch.object(agent, 'parse_file') as mock_parse:
                mock_parse.return_value = DartParseInfo(file_path="dummy")
                
                results = agent.parse_directory(str(lib_dir))
                
                # Should have called parse_file for 3 Dart files
                self.assertEqual(mock_parse.call_count, 3)
                self.assertEqual(len(results), 3)

    def test_extract_from_ast(self):
        """Test _extract_from_ast method."""
        agent = DartParserAgent()
        parse_info = DartParseInfo(file_path="test.dart")
        
        ast_data = [
            {
                "source": "lib/main.dart",
                "directives": [
                    {
                        "kind": "import",
                        "uri": "dart:async"
                    },
                    {
                        "kind": "export",
                        "uri": "package:my_package/widgets.dart"
                    }
                ]
            }
        ]
        
        agent._extract_from_ast(ast_data, parse_info)
        
        self.assertIn("dart:async", parse_info.imports)
        self.assertIn("package:my_package/widgets.dart", parse_info.exports)

    def test_is_inside_class_context(self):
        """Test _is_inside_class_context method."""
        agent = DartParserAgent()
        
        lines = [
            "import 'dart:async';",
            "",
            "class MyWidget {",
            "  void method() {",
            "    print('hello');",
            "  }",
            "}",
            "",
            "void topLevelFunction() {",
            "}"
        ]
        
        # Line 4 (method declaration) should be inside class
        self.assertTrue(agent._is_inside_class_context(lines, 4))
        
        # Line 8 (top-level function) should not be inside class
        self.assertFalse(agent._is_inside_class_context(lines, 8))


if __name__ == '__main__':
    unittest.main() 