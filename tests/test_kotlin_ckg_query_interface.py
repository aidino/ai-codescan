#!/usr/bin/env python3
"""
Tests cho Kotlin query methods trong CKGQueryInterfaceAgent.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.ckg_operations.ckg_query_interface import CKGQueryInterfaceAgent, CKGQueryResult


class TestKotlinCKGQueryInterface(unittest.TestCase):
    """Test Kotlin query methods trong CKGQueryInterfaceAgent."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent = CKGQueryInterfaceAgent()
        
        # Mock Neo4j connection
        self.agent.neo4j_connection = Mock()
        
        # Sample query results
        self.sample_class_result = [
            {"name": "TestClass", "package": "com.example", "modifiers": ["public"], "methods_count": 5}
        ]
        
        self.sample_function_result = [
            {"name": "testFunction", "return_type": "String", "parameters_count": 2, "complexity": 3}
        ]
        
        self.sample_inheritance_result = [
            {"child": "ChildClass", "parent": "ParentClass", "relationship": "KOTLIN_EXTENDS"}
        ]
    
    def test_get_kotlin_classes(self):
        """Test get_kotlin_classes method."""
        with patch.object(self.agent, 'execute_query') as mock_execute:
            mock_result = CKGQueryResult(success=True, data=self.sample_class_result)
            mock_execute.return_value = mock_result
            
            result = self.agent.get_kotlin_classes("com.example")
            
            self.assertTrue(result.success)
            self.assertEqual(len(result.data), 1)
            self.assertEqual(result.data[0]["name"], "TestClass")
            
            # Verify query contains proper Cypher
            call_args = mock_execute.call_args[0][0]
            self.assertIn("KOTLIN_CLASS", call_args)
            self.assertIn("com.example", call_args)
    
    def test_get_kotlin_functions(self):
        """Test get_kotlin_functions method."""
        with patch.object(self.agent, 'execute_query') as mock_execute:
            mock_result = CKGQueryResult(success=True, data=self.sample_function_result)
            mock_execute.return_value = mock_result
            
            result = self.agent.get_kotlin_functions("com.example", min_complexity=2)
            
            self.assertTrue(result.success)
            mock_execute.assert_called_once()
            
            # Verify query structure
            call_args = mock_execute.call_args[0][0]
            self.assertIn("KOTLIN_FUNCTION", call_args)
            self.assertIn("complexity", call_args)
    
    def test_get_kotlin_inheritance_tree(self):
        """Test get_kotlin_inheritance_tree method."""
        with patch.object(self.agent, 'execute_query') as mock_execute:
            mock_result = CKGQueryResult(success=True, data=self.sample_inheritance_result)
            mock_execute.return_value = mock_result
            
            result = self.agent.get_kotlin_inheritance_tree()
            
            self.assertTrue(result.success)
            mock_execute.assert_called_once()
            
            # Verify query contains inheritance relationships
            call_args = mock_execute.call_args[0][0]
            self.assertIn("KOTLIN_EXTENDS", call_args)
            self.assertIn("KOTLIN_IMPLEMENTS", call_args)
    
    def test_find_kotlin_data_classes(self):
        """Test find_kotlin_data_classes method."""
        with patch.object(self.agent, 'execute_query') as mock_execute:
            mock_result = CKGQueryResult(success=True, data=[])
            mock_execute.return_value = mock_result
            
            result = self.agent.find_kotlin_data_classes()
            
            self.assertTrue(result.success)
            mock_execute.assert_called_once()
            
            # Verify query targets data classes
            call_args = mock_execute.call_args[0][0]
            self.assertIn("KOTLIN_DATA_CLASS", call_args)
    
    def test_find_kotlin_objects(self):
        """Test find_kotlin_objects method."""
        with patch.object(self.agent, 'execute_query') as mock_execute:
            mock_result = CKGQueryResult(success=True, data=[])
            mock_execute.return_value = mock_result
            
            result = self.agent.find_kotlin_objects()
            
            self.assertTrue(result.success)
            mock_execute.assert_called_once()
            
            # Verify query targets objects
            call_args = mock_execute.call_args[0][0]
            self.assertIn("KOTLIN_OBJECT", call_args)
    
    def test_get_kotlin_extension_functions(self):
        """Test get_kotlin_extension_functions method."""
        with patch.object(self.agent, 'execute_query') as mock_execute:
            mock_result = CKGQueryResult(success=True, data=[])
            mock_execute.return_value = mock_result
            
            result = self.agent.get_kotlin_extension_functions("String")
            
            self.assertTrue(result.success)
            mock_execute.assert_called_once()
            
            # Verify query targets extension functions
            call_args = mock_execute.call_args[0][0]
            self.assertIn("KOTLIN_EXTENSION_FUNCTION", call_args)
            self.assertIn("String", call_args)
    
    def test_find_kotlin_companion_objects(self):
        """Test find_kotlin_companion_objects method."""
        with patch.object(self.agent, 'execute_query') as mock_execute:
            mock_result = CKGQueryResult(success=True, data=[])
            mock_execute.return_value = mock_result
            
            result = self.agent.find_kotlin_companion_objects()
            
            self.assertTrue(result.success)
            mock_execute.assert_called_once()
            
            # Verify query targets companion objects
            call_args = mock_execute.call_args[0][0]
            self.assertIn("KOTLIN_COMPANION_OBJECT", call_args)
    
    def test_get_kotlin_sealed_classes(self):
        """Test get_kotlin_sealed_classes method."""
        with patch.object(self.agent, 'execute_query') as mock_execute:
            mock_result = CKGQueryResult(success=True, data=[])
            mock_execute.return_value = mock_result
            
            result = self.agent.get_kotlin_sealed_classes()
            
            self.assertTrue(result.success)
            mock_execute.assert_called_once()
            
            # Verify query targets sealed classes
            call_args = mock_execute.call_args[0][0]
            self.assertIn("KOTLIN_SEALED_CLASS", call_args)
    
    def test_find_kotlin_annotations(self):
        """Test find_kotlin_annotations method."""
        with patch.object(self.agent, 'execute_query') as mock_execute:
            mock_result = CKGQueryResult(success=True, data=[])
            mock_execute.return_value = mock_result
            
            result = self.agent.find_kotlin_annotations()
            
            self.assertTrue(result.success)
            mock_execute.assert_called_once()
            
            # Verify query targets annotations
            call_args = mock_execute.call_args[0][0]
            self.assertIn("KOTLIN_ANNOTATION", call_args)
    
    def test_get_kotlin_type_aliases(self):
        """Test get_kotlin_type_aliases method."""
        with patch.object(self.agent, 'execute_query') as mock_execute:
            mock_result = CKGQueryResult(success=True, data=[])
            mock_execute.return_value = mock_result
            
            result = self.agent.get_kotlin_type_aliases()
            
            self.assertTrue(result.success)
            mock_execute.assert_called_once()
            
            # Verify query targets type aliases
            call_args = mock_execute.call_args[0][0]
            self.assertIn("KOTLIN_TYPEALIAS", call_args)
    
    def test_find_kotlin_complex_classes(self):
        """Test find_kotlin_complex_classes method."""
        with patch.object(self.agent, 'execute_query') as mock_execute:
            mock_result = CKGQueryResult(success=True, data=[])
            mock_execute.return_value = mock_result
            
            result = self.agent.find_kotlin_complex_classes(min_methods=10, min_fields=5)
            
            self.assertTrue(result.success)
            mock_execute.assert_called_once()
            
            # Verify query includes complexity filters
            call_args = mock_execute.call_args[0][0]
            self.assertIn("methods_count", call_args)
            self.assertIn("fields_count", call_args)
            self.assertIn("10", call_args)
            self.assertIn("5", call_args)
    
    def test_find_kotlin_circular_imports(self):
        """Test find_kotlin_circular_imports method."""
        with patch.object(self.agent, 'execute_query') as mock_execute:
            mock_result = CKGQueryResult(success=True, data=[])
            mock_execute.return_value = mock_result
            
            result = self.agent.find_kotlin_circular_imports()
            
            self.assertTrue(result.success)
            mock_execute.assert_called_once()
            
            # Verify query looks for circular dependencies
            call_args = mock_execute.call_args[0][0]
            self.assertIn("KOTLIN_IMPORTS", call_args)
            self.assertIn("path", call_args)
    
    def test_get_kotlin_overrides(self):
        """Test get_kotlin_overrides method."""
        with patch.object(self.agent, 'execute_query') as mock_execute:
            mock_result = CKGQueryResult(success=True, data=[])
            mock_execute.return_value = mock_result
            
            result = self.agent.get_kotlin_overrides("TestClass")
            
            self.assertTrue(result.success)
            mock_execute.assert_called_once()
            
            # Verify query looks for override relationships
            call_args = mock_execute.call_args[0][0]
            self.assertIn("KOTLIN_OVERRIDES", call_args)
            self.assertIn("TestClass", call_args)
    
    def test_error_handling(self):
        """Test error handling trong query methods."""
        with patch.object(self.agent, 'execute_query') as mock_execute:
            # Simulate query failure
            mock_result = CKGQueryResult(success=False, error="Connection failed")
            mock_execute.return_value = mock_result
            
            result = self.agent.get_kotlin_classes("com.example")
            
            self.assertFalse(result.success)
            self.assertEqual(result.error, "Connection failed")
    
    def test_empty_results(self):
        """Test handling của empty results."""
        with patch.object(self.agent, 'execute_query') as mock_execute:
            mock_result = CKGQueryResult(success=True, data=[])
            mock_execute.return_value = mock_result
            
            result = self.agent.get_kotlin_classes("nonexistent.package")
            
            self.assertTrue(result.success)
            self.assertEqual(len(result.data), 0)
    
    def test_query_with_optional_parameters(self):
        """Test query methods với optional parameters."""
        with patch.object(self.agent, 'execute_query') as mock_execute:
            mock_result = CKGQueryResult(success=True, data=[])
            mock_execute.return_value = mock_result
            
            # Test with no optional parameters
            result1 = self.agent.get_kotlin_functions()
            self.assertTrue(result1.success)
            
            # Test with package filter
            result2 = self.agent.get_kotlin_functions("com.example")
            self.assertTrue(result2.success)
            
            # Test with complexity filter
            result3 = self.agent.get_kotlin_functions(min_complexity=5)
            self.assertTrue(result3.success)
            
            # Verify all called execute_query
            self.assertEqual(mock_execute.call_count, 3)
    
    def test_all_kotlin_methods_exist(self):
        """Test rằng tất cả expected Kotlin query methods exist."""
        expected_methods = [
            'get_kotlin_classes',
            'get_kotlin_functions', 
            'get_kotlin_inheritance_tree',
            'find_kotlin_data_classes',
            'find_kotlin_objects',
            'get_kotlin_extension_functions',
            'find_kotlin_companion_objects',
            'get_kotlin_sealed_classes',
            'find_kotlin_annotations',
            'get_kotlin_type_aliases',
            'find_kotlin_complex_classes',
            'find_kotlin_circular_imports',
            'get_kotlin_overrides'
        ]
        
        for method_name in expected_methods:
            self.assertTrue(hasattr(self.agent, method_name), 
                          f"Method {method_name} không tồn tại")
            self.assertTrue(callable(getattr(self.agent, method_name)),
                          f"Method {method_name} không callable")


if __name__ == '__main__':
    unittest.main() 