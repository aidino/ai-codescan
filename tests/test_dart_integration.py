"""
Integration tests for Dart support in CodeParserCoordinatorAgent.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from datetime import datetime

from src.agents.ckg_operations.code_parser_coordinator import CodeParserCoordinatorAgent
from src.agents.data_acquisition import (
    ProjectDataContext, RepositoryInfo, ProjectLanguageProfile, 
    LanguageInfo, FileInfo, ProjectMetadata, DirectoryStructure
)


class TestDartIntegration(unittest.TestCase):
    """Test Dart integration with CodeParserCoordinatorAgent."""

    def setUp(self):
        """Set up test fixtures."""
        self.agent = CodeParserCoordinatorAgent()

    def test_dart_language_support(self):
        """Test that Dart is in supported languages."""
        self.assertIn('Dart', self.agent.supported_languages)

    def test_dart_parser_initialization(self):
        """Test that Dart parser initializes correctly."""
        self.assertIsNotNone(self.agent.dart_parser)

    def test_parse_dart_project_context(self):
        """Test parsing Dart project using ProjectDataContext."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a sample Dart project structure
            lib_dir = Path(temp_dir) / "lib"
            lib_dir.mkdir()
            
            # Create main.dart
            main_dart = lib_dir / "main.dart"
            main_dart.write_text('''
import 'package:flutter/material.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Demo',
      home: MyHomePage(),
    );
  }
}

class MyHomePage extends StatefulWidget {
  @override
  _MyHomePageState createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  int _counter = 0;

  void _incrementCounter() {
    setState(() {
      _counter++;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Flutter Demo')),
      body: Center(
        child: Column(
          children: [
            Text('You have pushed the button this many times:'),
            Text('$_counter', style: Theme.of(context).textTheme.headline4),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _incrementCounter,
        tooltip: 'Increment',
        child: Icon(Icons.add),
      ),
    );
  }
}
''')
            
            # Create widget.dart
            widget_dart = lib_dir / "widgets" / "my_widget.dart"
            widget_dart.parent.mkdir()
            widget_dart.write_text('''
import 'package:flutter/material.dart';

class CustomWidget extends StatelessWidget {
  final String title;
  
  const CustomWidget({Key? key, required this.title}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.0),
      child: Text(title),
    );
  }
}

mixin WidgetMixin {
  void logWidget() {
    print('Widget logged');
  }
}

extension StringExtensions on String {
  String get capitalize => this[0].toUpperCase() + this.substring(1);
}
''')
            
            # Create pubspec.yaml
            pubspec = Path(temp_dir) / "pubspec.yaml"
            pubspec.write_text('''
name: flutter_demo
description: A demo Flutter application
version: 1.0.0+1

environment:
  sdk: '>=2.17.0 <3.0.0'

dependencies:
  flutter:
    sdk: flutter
  cupertino_icons: ^1.0.2
''')
            
            # Create mock ProjectDataContext
            repo_info = RepositoryInfo(
                url="https://github.com/test/flutter_demo",
                local_path=temp_dir,
                default_branch="main",
                commit_hash="abc123",
                author="Test Author",
                commit_message="Initial commit",
                languages=["Dart"],
                size_mb=1.0,
                file_count=3
            )
            
            dart_lang_info = LanguageInfo(
                name="Dart",
                percentage=100.0,
                file_count=2,
                total_lines=100
            )
            
            language_profile = ProjectLanguageProfile(
                primary_language="Dart",
                languages=[dart_lang_info],
                frameworks=["Flutter"],
                build_tools=[],
                package_managers=["pub"],
                project_type="mobile_app",
                confidence_score=0.95
            )
            
            files = [
                FileInfo(
                    path=str(main_dart),
                    relative_path="lib/main.dart",
                    size_bytes=2000,
                    lines=50,
                    language="Dart",
                    last_modified=datetime.now(),
                    is_config_file=False
                ),
                FileInfo(
                    path=str(widget_dart),
                    relative_path="lib/widgets/my_widget.dart",
                    size_bytes=800,
                    lines=25,
                    language="Dart",
                    last_modified=datetime.now(),
                    is_config_file=False
                ),
                FileInfo(
                    path=str(pubspec),
                    relative_path="pubspec.yaml",
                    size_bytes=300,
                    lines=15,
                    language="YAML",
                    last_modified=datetime.now(),
                    is_config_file=True
                )
            ]
            
            project_metadata = ProjectMetadata(
                name="flutter_demo",
                version="1.0.0+1",
                description="A demo Flutter application"
            )
            
            directory_structure = DirectoryStructure(
                total_directories=2,
                total_files=3,
                max_depth=2,
                common_directories=["lib"],
                ignored_directories=[]
            )
            
            project_context = ProjectDataContext(
                repository_info=repo_info,
                language_profile=language_profile,
                project_metadata=project_metadata,
                directory_structure=directory_structure,
                files=files,
                analysis_timestamp=datetime.now(),
                preparation_config={}
            )
            
            # Mock the DartParserAgent to avoid requiring actual Dart SDK
            with patch.object(self.agent, 'dart_parser') as mock_parser:
                def mock_parse_side_effect(file_path):
                    from src.agents.ckg_operations.dart_parser import DartParseInfo
                    parse_info = DartParseInfo(file_path=file_path)
                    
                    if 'main.dart' in file_path:
                        parse_info.classes = ['MyApp', 'MyHomePage', '_MyHomePageState']
                        parse_info.functions = ['main', '_incrementCounter', 'build']
                        parse_info.imports = ['package:flutter/material.dart']
                        
                    elif 'my_widget.dart' in file_path:
                        parse_info.classes = ['CustomWidget']
                        parse_info.mixins = ['WidgetMixin']
                        parse_info.extensions = ['StringExtensions']
                        parse_info.functions = ['build', 'logWidget']
                        parse_info.imports = ['package:flutter/material.dart']
                    
                    return parse_info

                def mock_parse_dart_files(files):
                    from src.agents.ckg_operations.code_parser_coordinator import ParsedFile
                    parsed_files = []
                    
                    for file_path, relative_path in files:
                        # Create mock ParsedFile
                        parsed_file = ParsedFile(
                            file_path=file_path,
                            relative_path=relative_path,
                            language='Dart',
                            ast_tree=mock_parse_side_effect(file_path),  # Use parse info as AST
                            parse_success=True,
                            error_message=None,
                            nodes_count=20,  # Mock node count
                            lines_count=50   # Mock line count
                        )
                        parsed_files.append(parsed_file)
                    
                    return parsed_files

                mock_parser.parse_file.side_effect = mock_parse_side_effect
                mock_parser.parse_dart_files.side_effect = mock_parse_dart_files
                mock_parser.can_parse.return_value = True

                # Test parsing
                result = self.agent.parse_project(project_context)

                # Verify results
                self.assertIsNotNone(result)
                self.assertEqual(result.project_path, temp_dir)
                self.assertEqual(result.language_profile.primary_language, "Dart")
                
                # Should have parsed 2 Dart files (excluding pubspec.yaml)
                dart_files = [f for f in result.parsed_files if f.language == 'Dart']
                self.assertEqual(len(dart_files), 2)
                
                # Verify all Dart files were parsed successfully
                for dart_file in dart_files:
                    self.assertTrue(dart_file.parse_success)
                    self.assertIsNone(dart_file.error_message)
                    self.assertGreater(dart_file.nodes_count, 0)
                    self.assertGreater(dart_file.lines_count, 0)

    def test_dart_parser_not_available(self):
        """Test behavior when Dart parser is not available."""
        with patch.object(self.agent, 'dart_parser', None):
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create a simple Dart file
                dart_file = Path(temp_dir) / "test.dart"
                dart_file.write_text("void main() { print('Hello'); }")
                
                files = [(str(dart_file), "test.dart")]
                result = self.agent._parse_dart_files(files)
                
                # Should return parsed files with errors
                self.assertEqual(len(result), 1)
                self.assertFalse(result[0].parse_success)
                self.assertIsNotNone(result[0].error_message)

    def test_dart_file_filtering(self):
        """Test that only Dart files are parsed for Dart projects."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mixed files
            Path(temp_dir, "main.dart").touch()
            Path(temp_dir, "config.yaml").touch()
            Path(temp_dir, "readme.md").touch()
            
            # Create mock context with mixed files
            files = [
                FileInfo(
                    path=str(Path(temp_dir, "main.dart")),
                    relative_path="main.dart",
                    size_bytes=1000,
                    lines=30,
                    language="Dart",
                    last_modified=datetime.now(),
                    is_config_file=False
                ),
                FileInfo(
                    path=str(Path(temp_dir, "config.yaml")),
                    relative_path="config.yaml",
                    size_bytes=200,
                    lines=10,
                    language="YAML",
                    last_modified=datetime.now(),
                    is_config_file=True
                ),
                FileInfo(
                    path=str(Path(temp_dir, "readme.md")),
                    relative_path="readme.md",
                    size_bytes=500,
                    lines=20,
                    language="Markdown",
                    last_modified=datetime.now(),
                    is_config_file=False
                )
            ]
            
            language_profile = ProjectLanguageProfile(
                primary_language="Dart",
                languages=[],
                frameworks=[],
                build_tools=[],
                package_managers=[],
                project_type="library",
                confidence_score=0.8
            )
            
            project_metadata = ProjectMetadata(name="test_project")
            
            directory_structure = DirectoryStructure(
                total_directories=1,
                total_files=3,
                max_depth=1,
                common_directories=[],
                ignored_directories=[]
            )
            
            project_context = ProjectDataContext(
                repository_info=Mock(),
                language_profile=language_profile,
                project_metadata=project_metadata,
                directory_structure=directory_structure,
                files=files,
                analysis_timestamp=datetime.now(),
                preparation_config={}
            )
            
            # Get files to parse
            files_to_parse = self.agent._get_files_to_parse(project_context)
            
            # Should only include Dart files
            dart_files = [f for f in files_to_parse if f[0].endswith('.dart')]
            non_dart_files = [f for f in files_to_parse if not f[0].endswith('.dart')]
            
            self.assertEqual(len(dart_files), 1)
            self.assertEqual(len(non_dart_files), 0)
            self.assertTrue(dart_files[0][0].endswith('main.dart'))


if __name__ == '__main__':
    unittest.main() 