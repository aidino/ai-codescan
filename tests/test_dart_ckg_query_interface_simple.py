#!/usr/bin/env python3
"""
Simplified tests cho Dart CKG Query Interface functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
from typing import Dict, List, Any

from src.agents.ckg_operations.ckg_query_interface import CKGQueryInterfaceAgent, CKGQueryResult


class TestDartCKGQueryInterfaceSimple(unittest.TestCase):
    """Simplified test cho Dart-specific CKG query functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock Neo4j driver để không cần real database
        with patch('src.agents.ckg_operations.ckg_query_interface.GraphDatabase'):
            self.agent = CKGQueryInterfaceAgent()
        
        # Mock driver và set driver to None để test simple methods
        self.agent.driver = None
        
        # Common test data
        self.test_file_path = "/test/project/lib/main.dart"
        self.test_class_name = "TestClass"
    
    def test_dart_methods_exist(self):
        """Test rằng các Dart-specific methods tồn tại trong agent."""
        # Check Dart-specific methods exist
        self.assertTrue(hasattr(self.agent, 'get_dart_classes_in_file'))
        self.assertTrue(hasattr(self.agent, 'get_dart_mixins_in_file'))
        self.assertTrue(hasattr(self.agent, 'get_dart_extensions_in_file'))
        self.assertTrue(hasattr(self.agent, 'get_dart_functions_in_file'))
        self.assertTrue(hasattr(self.agent, 'get_dart_enums_in_file'))
        self.assertTrue(hasattr(self.agent, 'get_dart_imports_in_file'))
        self.assertTrue(hasattr(self.agent, 'get_dart_exports_in_file'))
        self.assertTrue(hasattr(self.agent, 'get_dart_library_info'))
        self.assertTrue(hasattr(self.agent, 'find_dart_class_hierarchy'))
        self.assertTrue(hasattr(self.agent, 'get_dart_project_statistics'))
        self.assertTrue(hasattr(self.agent, 'search_dart_elements_by_name'))
        self.assertTrue(hasattr(self.agent, 'find_dart_unused_exports'))
        self.assertTrue(hasattr(self.agent, 'find_dart_circular_imports'))
    
    def test_dart_methods_callable(self):
        """Test rằng các Dart-specific methods có thể được call."""
        # All methods should be callable
        self.assertTrue(callable(self.agent.get_dart_classes_in_file))
        self.assertTrue(callable(self.agent.get_dart_mixins_in_file))
        self.assertTrue(callable(self.agent.get_dart_extensions_in_file))
        self.assertTrue(callable(self.agent.get_dart_functions_in_file))
        self.assertTrue(callable(self.agent.get_dart_enums_in_file))
        self.assertTrue(callable(self.agent.get_dart_imports_in_file))
        self.assertTrue(callable(self.agent.get_dart_exports_in_file))
        self.assertTrue(callable(self.agent.get_dart_library_info))
        self.assertTrue(callable(self.agent.find_dart_class_hierarchy))
        self.assertTrue(callable(self.agent.get_dart_project_statistics))
        self.assertTrue(callable(self.agent.search_dart_elements_by_name))
        self.assertTrue(callable(self.agent.find_dart_unused_exports))
        self.assertTrue(callable(self.agent.find_dart_circular_imports))
    
    def test_no_driver_error_handling(self):
        """Test error handling khi không có Neo4j driver."""
        # Test all methods with no driver
        result1 = self.agent.get_dart_classes_in_file(self.test_file_path)
        self.assertFalse(result1.success)
        self.assertIn("Không có kết nối Neo4j", result1.error_message)
        
        result2 = self.agent.get_dart_mixins_in_file(self.test_file_path)
        self.assertFalse(result2.success)
        self.assertIn("Không có kết nối Neo4j", result2.error_message)
        
        result3 = self.agent.get_dart_extensions_in_file(self.test_file_path)
        self.assertFalse(result3.success)
        self.assertIn("Không có kết nối Neo4j", result3.error_message)
        
        result4 = self.agent.get_dart_functions_in_file(self.test_file_path)
        self.assertFalse(result4.success)
        self.assertIn("Không có kết nối Neo4j", result4.error_message)
        
        result5 = self.agent.get_dart_enums_in_file(self.test_file_path)
        self.assertFalse(result5.success)
        self.assertIn("Không có kết nối Neo4j", result5.error_message)
    
    def test_dart_query_patterns(self):
        """Test rằng Dart queries chứa đúng patterns/keywords."""
        # Mock driver để test query generation
        mock_driver = Mock()
        mock_session = Mock()
        mock_result = Mock()
        
        # Mock result iteration
        mock_result.__iter__ = Mock(return_value=iter([]))
        mock_session.run.return_value = mock_result
        
        # Mock context manager for session
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=False)
        
        self.agent.driver = mock_driver
        
        # Test get_dart_classes_in_file query
        self.agent.get_dart_classes_in_file(self.test_file_path)
        mock_session.run.assert_called()
        query_args = mock_session.run.call_args[0]
        self.assertIn('DEFINES_DART_CLASS', query_args[0])
        self.assertIn('DartClass', query_args[0])
        
        # Reset mock for next test
        mock_session.run.reset_mock()
        
        # Test get_dart_mixins_in_file query
        self.agent.get_dart_mixins_in_file(self.test_file_path)
        mock_session.run.assert_called()
        query_args = mock_session.run.call_args[0]
        self.assertIn('DEFINES_DART_MIXIN', query_args[0])
        self.assertIn('DartMixin', query_args[0])
        
        # Reset mock for next test
        mock_session.run.reset_mock()
        
        # Test get_dart_extensions_in_file query
        self.agent.get_dart_extensions_in_file(self.test_file_path)
        mock_session.run.assert_called()
        query_args = mock_session.run.call_args[0]
        self.assertIn('DEFINES_DART_EXTENSION', query_args[0])
        self.assertIn('DartExtension', query_args[0])
        
        # Reset mock for next test
        mock_session.run.reset_mock()
        
        # Test get_dart_functions_in_file query
        self.agent.get_dart_functions_in_file(self.test_file_path)
        mock_session.run.assert_called()
        query_args = mock_session.run.call_args[0]
        self.assertIn('DEFINES_DART_FUNCTION', query_args[0])
        self.assertIn('DartFunction', query_args[0])
        
        # Reset mock for next test
        mock_session.run.reset_mock()
        
        # Test find_dart_class_hierarchy query
        self.agent.find_dart_class_hierarchy(self.test_class_name)
        mock_session.run.assert_called()
        query_args = mock_session.run.call_args[0]
        self.assertIn('DART_EXTENDS', query_args[0])
        self.assertIn('DART_IMPLEMENTS', query_args[0])
        self.assertIn('DART_MIXES_IN', query_args[0])
        
        # Reset mock for next test
        mock_session.run.reset_mock()
        
        # Test get_dart_project_statistics query
        self.agent.get_dart_project_statistics()
        mock_session.run.assert_called()
        query_args = mock_session.run.call_args[0]
        self.assertIn('DartClass', query_args[0])
        self.assertIn('DartMixin', query_args[0])
        self.assertIn('DartExtension', query_args[0])
        self.assertIn('COUNT', query_args[0])
    
    def test_search_dart_elements_default_types(self):
        """Test search_dart_elements_by_name với default element types."""
        # Mock driver để test default element types
        mock_driver = Mock()
        mock_session = Mock()
        mock_result = Mock()
        
        # Mock result iteration
        mock_result.__iter__ = Mock(return_value=iter([]))
        mock_session.run.return_value = mock_result
        
        # Mock context manager for session
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=False)
        
        self.agent.driver = mock_driver
        
        # Test search với default types
        self.agent.search_dart_elements_by_name("Test")
        mock_session.run.assert_called()
        query_args = mock_session.run.call_args[0]
        
        # Check default Dart element types are included
        self.assertIn('DartClass', query_args[0])
        self.assertIn('DartMixin', query_args[0])
        self.assertIn('DartExtension', query_args[0])
        self.assertIn('DartFunction', query_args[0])
        self.assertIn('DartEnum', query_args[0])
        
        # Check regex pattern is used
        self.assertIn('=~', query_args[0])
        
        # Check parameters
        call_args = mock_session.run.call_args
        if len(call_args[0]) > 1:
            query_params = call_args[0][1]
            self.assertIn('.*Test.*', query_params['pattern'])
        elif call_args[1]:
            self.assertIn('.*Test.*', call_args[1]['pattern'])
    
    def test_find_dart_unused_exports_with_and_without_file(self):
        """Test find_dart_unused_exports với và không có file_path."""
        # Mock driver
        mock_driver = Mock()
        mock_session = Mock()
        mock_result = Mock()
        
        # Mock result iteration
        mock_result.__iter__ = Mock(return_value=iter([]))
        mock_session.run.return_value = mock_result
        
        # Mock context manager for session
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=False)
        
        self.agent.driver = mock_driver
        
        # Test with file_path
        self.agent.find_dart_unused_exports(self.test_file_path)
        mock_session.run.assert_called()
        query_args = mock_session.run.call_args[0]
        self.assertIn('DartExport', query_args[0])
        self.assertIn('NOT EXISTS', query_args[0])
        
        # Reset mock for next test
        mock_session.run.reset_mock()
        
        # Test without file_path
        self.agent.find_dart_unused_exports()
        mock_session.run.assert_called()
        query_args = mock_session.run.call_args[0]
        self.assertIn('DartExport', query_args[0])
        self.assertIn('NOT EXISTS', query_args[0])
    
    def test_find_dart_circular_imports_query_pattern(self):
        """Test find_dart_circular_imports query pattern."""
        # Mock driver
        mock_driver = Mock()
        mock_session = Mock()
        mock_result = Mock()
        
        # Mock result iteration
        mock_result.__iter__ = Mock(return_value=iter([]))
        mock_session.run.return_value = mock_result
        
        # Mock context manager for session
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=False)
        
        self.agent.driver = mock_driver
        
        # Test circular imports query
        self.agent.find_dart_circular_imports()
        mock_session.run.assert_called()
        query_args = mock_session.run.call_args[0]
        
        # Check circular import pattern
        self.assertIn('IMPORTS*2..10', query_args[0])  # Path pattern
        self.assertIn('type(rel) = \'IMPORTS\'', query_args[0])
        self.assertIn('LIMIT 20', query_args[0])  # Result limit
    
    def test_dart_query_parameter_passing(self):
        """Test rằng parameters được pass đúng cách cho queries."""
        # Mock driver
        mock_driver = Mock()
        mock_session = Mock()
        mock_result = Mock()
        
        # Mock result iteration
        mock_result.__iter__ = Mock(return_value=iter([]))
        mock_session.run.return_value = mock_result
        
        # Mock context manager for session
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=False)
        
        self.agent.driver = mock_driver
        
        # Test parameter passing cho get_dart_classes_in_file
        self.agent.get_dart_classes_in_file(self.test_file_path)
        mock_session.run.assert_called()
        # Check actual call - parameters are in args[1] not kwargs
        call_args = mock_session.run.call_args
        if len(call_args[0]) > 1:
            # Parameters passed as second argument
            query_params = call_args[0][1]
            self.assertEqual(query_params, {"file_path": self.test_file_path})
        elif call_args[1]:
            # Parameters passed as kwargs  
            self.assertEqual(call_args[1], {"file_path": self.test_file_path})
        
        # Reset mock for next test
        mock_session.run.reset_mock()
        
        # Test parameter passing cho find_dart_class_hierarchy
        self.agent.find_dart_class_hierarchy(self.test_class_name)
        mock_session.run.assert_called()
        call_args = mock_session.run.call_args
        if len(call_args[0]) > 1:
            query_params = call_args[0][1]
            self.assertEqual(query_params, {"class_name": self.test_class_name})
        elif call_args[1]:
            self.assertEqual(call_args[1], {"class_name": self.test_class_name})
        
        # Reset mock for next test
        mock_session.run.reset_mock()
        
        # Test parameter passing cho search_dart_elements_by_name
        search_pattern = "TestPattern"
        self.agent.search_dart_elements_by_name(search_pattern)
        mock_session.run.assert_called()
        call_args = mock_session.run.call_args
        if len(call_args[0]) > 1:
            query_params = call_args[0][1]
            self.assertEqual(query_params, {"pattern": f".*{search_pattern}.*"})
        elif call_args[1]:
            self.assertEqual(call_args[1], {"pattern": f".*{search_pattern}.*"})


if __name__ == '__main__':
    unittest.main() 