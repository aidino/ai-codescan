#!/usr/bin/env python3
"""
Tests cho Dart CKG Query Interface functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

from src.agents.ckg_operations.ckg_query_interface import CKGQueryInterfaceAgent, CKGQueryResult, ConnectionConfig


class TestDartCKGQueryInterface(unittest.TestCase):
    """Test Dart-specific CKG query functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock Neo4j driver để không cần real database
        with patch('src.agents.ckg_operations.ckg_query_interface.GraphDatabase'):
            self.agent = CKGQueryInterfaceAgent()
        
        # Mock driver
        self.agent.driver = Mock()
        
        # Common test data
        self.test_file_path = "/test/project/lib/main.dart"
        self.test_class_name = "TestClass"
    
    def _create_mock_record(self, data_dict: Dict[str, Any]) -> Mock:
        """Helper để tạo mock record với proper __getitem__ support."""
        mock_record = Mock()
        mock_record.keys.return_value = list(data_dict.keys())
        mock_record.__getitem__ = Mock(side_effect=lambda key: data_dict[key])
        return mock_record
    
    def _setup_mock_session(self, records_data: List[Dict[str, Any]]) -> Mock:
        """Helper để setup mock session với multiple records."""
        mock_session = Mock()
        mock_result = Mock()
        
        # Create mock records
        mock_records = [self._create_mock_record(data) for data in records_data]
        mock_result.__iter__.return_value = mock_records
        
        mock_session.run.return_value = mock_result
        self.agent.driver.session.return_value.__enter__.return_value = mock_session
        
        return mock_session
    
    def test_get_dart_classes_in_file(self):
        """Test getting Dart classes in file."""
        # Setup mock data
        test_data = [{
            'name': 'TestClass',
            'line_number': 10,
            'package': 'com.example',
            'is_abstract': False,
            'extends_class': 'BaseClass',
            'implements_interfaces': ['Interface1']
        }]
        
        mock_session = self._setup_mock_session(test_data)
        
        # Execute test
        result = self.agent.get_dart_classes_in_file(self.test_file_path)
        
        # Verify
        self.assertTrue(result.success)
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0]['name'], 'TestClass')
        
        # Verify query was called with correct parameters
        mock_session.run.assert_called_once()
        args, kwargs = mock_session.run.call_args
        self.assertIn('DEFINES_DART_CLASS', args[0])
        self.assertEqual(kwargs, {"file_path": self.test_file_path})
    
    def test_get_dart_mixins_in_file(self):
        """Test getting Dart mixins in file."""
        # Setup mock data
        test_data = [{
            'name': 'TestMixin',
            'line_number': 5,
            'package': 'com.example',
            'extends_interfaces': ['Interface1']
        }]
        
        mock_session = self._setup_mock_session(test_data)
        
        # Execute test
        result = self.agent.get_dart_mixins_in_file(self.test_file_path)
        
        # Verify
        self.assertTrue(result.success)
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0]['name'], 'TestMixin')
        
        # Verify query contains DEFINES_DART_MIXIN
        mock_session.run.assert_called_once()
        args, _ = mock_session.run.call_args
        self.assertIn('DEFINES_DART_MIXIN', args[0])
    
    def test_get_dart_extensions_in_file(self):
        """Test getting Dart extensions in file."""
        # Setup mock data
        test_data = [{
            'name': 'StringExtension',
            'line_number': 15,
            'extends_class': 'String',
            'implements_interfaces': []
        }]
        
        mock_session = self._setup_mock_session(test_data)
        
        # Execute test
        result = self.agent.get_dart_extensions_in_file(self.test_file_path)
        
        # Verify
        self.assertTrue(result.success)
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0]['name'], 'StringExtension')
        
        # Verify query contains DEFINES_DART_EXTENSION
        mock_session.run.assert_called_once()
        args, _ = mock_session.run.call_args
        self.assertIn('DEFINES_DART_EXTENSION', args[0])
    
    def test_get_dart_functions_in_file(self):
        """Test getting Dart functions in file."""
        # Setup mock data
        test_data = [{
            'name': 'testFunction',
            'line_number': 20,
            'return_type': 'String',
            'params_count': 2,
            'is_async': True,
            'is_generator': False
        }]
        
        mock_session = self._setup_mock_session(test_data)
        
        # Execute test
        result = self.agent.get_dart_functions_in_file(self.test_file_path)
        
        # Verify
        self.assertTrue(result.success)
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0]['name'], 'testFunction')
        self.assertTrue(result.results[0]['is_async'])
        
        # Verify query contains DEFINES_DART_FUNCTION
        mock_session.run.assert_called_once()
        args, _ = mock_session.run.call_args
        self.assertIn('DEFINES_DART_FUNCTION', args[0])
    
    def test_get_dart_enums_in_file(self):
        """Test getting Dart enums in file."""
        # Setup mock data
        test_data = [{
            'name': 'Color',
            'line_number': 25,
            'package': 'com.example',
            'constants_count': 3
        }]
        
        mock_session = self._setup_mock_session(test_data)
        
        # Execute test
        result = self.agent.get_dart_enums_in_file(self.test_file_path)
        
        # Verify
        self.assertTrue(result.success)
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0]['name'], 'Color')
        self.assertEqual(result.results[0]['constants_count'], 3)
        
        # Verify query contains DEFINES_DART_ENUM
        mock_session.run.assert_called_once()
        args, _ = mock_session.run.call_args
        self.assertIn('DEFINES_DART_ENUM', args[0])
    
    def test_get_dart_imports_in_file(self):
        """Test getting Dart imports in file."""
        # Setup mock data
        test_data = [{
            'name': 'dart:core',
            'line_number': 1,
            'imported_name': 'dart:core',
            'is_package_import': True,
            'is_relative_import': False
        }]
        
        mock_session = self._setup_mock_session(test_data)
        
        # Execute test
        result = self.agent.get_dart_imports_in_file(self.test_file_path)
        
        # Verify
        self.assertTrue(result.success)
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0]['name'], 'dart:core')
        self.assertTrue(result.results[0]['is_package_import'])
        
        # Verify query uses correct relationship
        mock_session.run.assert_called_once()
        args, _ = mock_session.run.call_args
        self.assertIn('IMPORTS', args[0])
        self.assertIn('DartImport', args[0])
    
    def test_get_dart_exports_in_file(self):
        """Test getting Dart exports in file."""
        # Setup mock data
        test_data = [{
            'name': 'TestClass',
            'line_number': 30,
            'full_name': 'com.example.TestClass'
        }]
        
        mock_session = self._setup_mock_session(test_data)
        
        # Execute test
        result = self.agent.get_dart_exports_in_file(self.test_file_path)
        
        # Verify
        self.assertTrue(result.success)
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0]['name'], 'TestClass')
        
        # Verify query uses DART_EXPORTS relationship
        mock_session.run.assert_called_once()
        args, _ = mock_session.run.call_args
        self.assertIn('DART_EXPORTS', args[0])
        self.assertIn('DartExport', args[0])
    
    def test_get_dart_library_info(self):
        """Test getting Dart library info."""
        # Setup mock data
        test_data = [{
            'name': 'my_app',
            'line_number': 1,
            'full_name': 'com.example.my_app'
        }]
        
        mock_session = self._setup_mock_session(test_data)
        
        # Execute test
        result = self.agent.get_dart_library_info(self.test_file_path)
        
        # Verify
        self.assertTrue(result.success)
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0]['name'], 'my_app')
        
        # Verify query uses CONTAINS relationship với DartLibrary
        mock_session.run.assert_called_once()
        args, _ = mock_session.run.call_args
        self.assertIn('CONTAINS', args[0])
        self.assertIn('DartLibrary', args[0])
    
    def test_find_dart_class_hierarchy(self):
        """Test finding Dart class hierarchy."""
        # Setup mock data
        test_data = [{
            'class_name': 'TestClass',
            'extends_classes': ['BaseClass'],
            'implements_interfaces': ['TestInterface'],
            'mixes_in_mixins': ['TestMixin']
        }]
        
        mock_session = self._setup_mock_session(test_data)
        
        # Execute test
        result = self.agent.find_dart_class_hierarchy(self.test_class_name)
        
        # Verify
        self.assertTrue(result.success)
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0]['class_name'], 'TestClass')
        self.assertEqual(result.results[0]['extends_classes'], ['BaseClass'])
        
        # Verify query contains Dart relationship types
        mock_session.run.assert_called_once()
        args, _ = mock_session.run.call_args
        self.assertIn('DART_EXTENDS', args[0])
        self.assertIn('DART_IMPLEMENTS', args[0])
        self.assertIn('DART_MIXES_IN', args[0])
    
    def test_get_dart_project_statistics(self):
        """Test getting Dart project statistics."""
        # Setup mock data
        test_data = [{
            'dart_classes_count': 5,
            'dart_mixins_count': 2,
            'dart_extensions_count': 1,
            'dart_functions_count': 10,
            'dart_enums_count': 3,
            'dart_imports_count': 15,
            'dart_exports_count': 8,
            'dart_libraries_count': 1
        }]
        
        mock_session = self._setup_mock_session(test_data)
        
        # Execute test
        result = self.agent.get_dart_project_statistics()
        
        # Verify
        self.assertTrue(result.success)
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0]['dart_classes_count'], 5)
        self.assertEqual(result.results[0]['dart_functions_count'], 10)
        
        # Verify query counts Dart node types
        mock_session.run.assert_called_once()
        args, _ = mock_session.run.call_args
        self.assertIn('DartClass', args[0])
        self.assertIn('DartMixin', args[0])
        self.assertIn('COUNT', args[0])
    
    def test_search_dart_elements_by_name(self):
        """Test searching Dart elements by name pattern."""
        # Setup mock data
        test_data = [{
            'name': 'TestClass',
            'type': 'DartClass',
            'file_path': self.test_file_path,
            'line_number': 10
        }]
        
        mock_session = self._setup_mock_session(test_data)
        
        # Execute test
        result = self.agent.search_dart_elements_by_name("Test")
        
        # Verify
        self.assertTrue(result.success)
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0]['name'], 'TestClass')
        self.assertEqual(result.results[0]['type'], 'DartClass')
        
        # Verify query uses regex pattern
        mock_session.run.assert_called_once()
        args, kwargs = mock_session.run.call_args
        self.assertIn('=~', args[0])  # Regex operator
        self.assertIn('.*Test.*', kwargs['pattern'])
    
    def test_find_dart_unused_exports(self):
        """Test finding unused Dart exports."""
        # Setup mock data
        test_data = [{
            'export_name': 'UnusedClass',
            'file_path': self.test_file_path,
            'line_number': 30
        }]
        
        mock_session = self._setup_mock_session(test_data)
        
        # Execute test
        result = self.agent.find_dart_unused_exports()
        
        # Verify
        self.assertTrue(result.success)
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0]['export_name'], 'UnusedClass')
        
        # Verify query checks for unused exports
        mock_session.run.assert_called_once()
        args, _ = mock_session.run.call_args
        self.assertIn('DartExport', args[0])
        self.assertIn('NOT EXISTS', args[0])
    
    def test_find_dart_circular_imports(self):
        """Test finding circular imports in Dart code."""
        # Setup mock data
        test_data = [{
            'circular_path': ['/path/file1.dart', '/path/file2.dart', '/path/file1.dart'],
            'path_length': 2
        }]
        
        mock_session = self._setup_mock_session(test_data)
        
        # Execute test
        result = self.agent.find_dart_circular_imports()
        
        # Verify
        self.assertTrue(result.success)
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0]['path_length'], 2)
        self.assertIn('/path/file1.dart', result.results[0]['circular_path'])
        
        # Verify query finds circular paths
        mock_session.run.assert_called_once()
        args, _ = mock_session.run.call_args
        self.assertIn('IMPORTS*2..10', args[0])  # Path pattern
        self.assertIn('type(rel) = \'IMPORTS\'', args[0])
    
    def test_no_driver_connection(self):
        """Test behavior when no Neo4j driver available."""
        # Set agent driver to None
        self.agent.driver = None
        
        # Execute test
        result = self.agent.get_dart_classes_in_file(self.test_file_path)
        
        # Verify error handling
        self.assertFalse(result.success)
        self.assertEqual(result.total_count, 0)
        self.assertIn("Không có kết nối Neo4j", result.error_message)
    
    def test_query_execution_error(self):
        """Test error handling during query execution."""
        # Mock session to raise exception
        mock_session = Mock()
        mock_session.run.side_effect = Exception("Database error")
        
        # Mock context manager properly
        context_manager = Mock()
        context_manager.__enter__.return_value = mock_session
        context_manager.__exit__.return_value = False
        
        self.agent.driver.session.return_value = context_manager
        
        # Execute test
        result = self.agent.get_dart_classes_in_file(self.test_file_path)
        
        # Verify error handling
        self.assertFalse(result.success)
        self.assertEqual(result.total_count, 0)
        self.assertIn("Database error", result.error_message)


if __name__ == '__main__':
    unittest.main() 