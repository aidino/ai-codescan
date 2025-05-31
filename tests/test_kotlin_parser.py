#!/usr/bin/env python3
"""
Test suite cho KotlinParserAgent.

Kiểm tra việc parse Kotlin source code thành AST representation.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
import tempfile

# Add src to path để import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.ckg_operations.kotlin_parser import KotlinParserAgent, KotlinNode, KotlinParseInfo


class TestKotlinParserAgent(unittest.TestCase):
    """Test class cho KotlinParserAgent."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = KotlinParserAgent()
        
        # Sample Kotlin code for testing
        self.sample_kotlin_code = '''
package com.example.myapp

import android.app.Activity
import kotlinx.coroutines.launch

/**
 * Main activity class
 */
class MainActivity : Activity() {
    private val name: String = "Test"
    private var count: Int = 0
    
    override fun onCreate() {
        super.onCreate()
        setupViews()
    }
    
    private fun setupViews() {
        // Setup code here
    }
    
    companion object {
        const val TAG = "MainActivity"
    }
}

interface UserRepository {
    suspend fun getUser(id: String): User?
}

data class User(
    val id: String,
    val name: String,
    val email: String
)

object DatabaseConfig {
    const val DB_NAME = "app_database"
}

enum class Status {
    ACTIVE, INACTIVE, PENDING
}

typealias UserCallback = (User?) -> Unit

fun String.isValidEmail(): Boolean {
    return this.contains("@")
}

sealed class Result<T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error<T>(val message: String) : Result<T>()
}
'''

    def test_init(self):
        """Test KotlinParserAgent initialization."""
        parser = KotlinParserAgent()
        self.assertIsNotNone(parser)
        self.assertEqual(parser.timeout, 30)

    def test_ensure_kotlinc_available_not_found(self):
        """Test kotlinc detection when not available."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            with patch('os.path.isfile', return_value=False):
                parser = KotlinParserAgent()
                self.assertIsNone(parser.kotlinc_path)

    def test_ensure_kotlinc_available_found_in_path(self):
        """Test kotlinc detection in PATH."""
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = '/usr/bin/kotlinc\n'
            mock_run.return_value = mock_result
            
            parser = KotlinParserAgent()
            self.assertEqual(parser.kotlinc_path, '/usr/bin/kotlinc')

    def test_ensure_kotlinc_available_found_in_common_path(self):
        """Test kotlinc detection trong common installation paths."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            with patch('os.path.isfile') as mock_isfile:
                with patch('os.access', return_value=True):
                    def isfile_side_effect(path):
                        return path == '/usr/local/bin/kotlinc'
                    mock_isfile.side_effect = isfile_side_effect
                    
                    parser = KotlinParserAgent()
                    self.assertEqual(parser.kotlinc_path, '/usr/local/bin/kotlinc')

    def test_parse_kotlin_files_no_kotlinc(self):
        """Test parsing khi kotlinc không available."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            with patch('os.path.isfile', return_value=False):
                parser = KotlinParserAgent()
                
                result = parser.parse_kotlin_files(['test.kt'])
                self.assertEqual(result, [])

    def test_parse_kotlin_files_success(self):
        """Test successful parsing của Kotlin files."""
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = '/usr/bin/kotlinc\n'
            mock_run.return_value = mock_result
            
            parser = KotlinParserAgent()
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.kt', delete=False) as f:
                f.write(self.sample_kotlin_code)
                temp_file = f.name
            
            try:
                with patch.object(parser, '_parse_single_file') as mock_parse:
                    mock_parse_info = KotlinParseInfo(
                        package_name='com.example.myapp',
                        imports=['android.app.Activity'],
                        classes=[KotlinNode(type='CLASS', name='MainActivity')],
                        data_classes=[KotlinNode(type='CLASS', name='User')]
                    )
                    mock_parse.return_value = mock_parse_info
                    
                    results = parser.parse_kotlin_files([temp_file])
                    
                    self.assertEqual(len(results), 1)
                    file_path, parse_info = results[0]
                    self.assertEqual(file_path, temp_file)
                    self.assertIsInstance(parse_info, KotlinParseInfo)
            finally:
                os.unlink(temp_file)

    def test_parse_kotlin_files_filter_non_kotlin(self):
        """Test filtering non-Kotlin files."""
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = '/usr/bin/kotlinc\n'
            mock_run.return_value = mock_result
            
            parser = KotlinParserAgent()
            
            results = parser.parse_kotlin_files(['test.java', 'test.py'])
            self.assertEqual(len(results), 0)

    def test_check_kotlin_syntax_success(self):
        """Test successful Kotlin syntax check."""
        with patch('subprocess.run') as mock_run:
            # Mock kotlinc detection
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = '/usr/bin/kotlinc\n'
            mock_run.return_value = mock_result
            
            parser = KotlinParserAgent()
            
            # Mock kotlinc compilation success
            mock_compile_result = Mock()
            mock_compile_result.returncode = 0
            mock_run.return_value = mock_compile_result
            
            result = parser._check_kotlin_syntax('test.kt')
            self.assertTrue(result)

    def test_check_kotlin_syntax_failure(self):
        """Test Kotlin syntax check failure."""
        with patch('subprocess.run') as mock_run:
            # Mock kotlinc detection
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = '/usr/bin/kotlinc\n'
            mock_run.return_value = mock_result
            
            parser = KotlinParserAgent()
            
            # Mock kotlinc compilation failure
            mock_compile_result = Mock()
            mock_compile_result.returncode = 1
            mock_compile_result.stderr = 'Syntax error'
            mock_run.return_value = mock_compile_result
            
            result = parser._check_kotlin_syntax('test.kt')
            self.assertFalse(result)

    def test_manual_parse_kotlin(self):
        """Test manual parsing của Kotlin content."""
        parser = KotlinParserAgent()
        parse_info = parser._manual_parse_kotlin(self.sample_kotlin_code)
        
        # Test package detection
        self.assertEqual(parse_info.package_name, 'com.example.myapp')
        
        # Test imports
        self.assertIn('android.app.Activity', parse_info.imports)
        self.assertIn('kotlinx.coroutines.launch', parse_info.imports)
        
        # Test classes
        class_names = [cls.name for cls in parse_info.classes]
        self.assertIn('MainActivity', class_names)
        
        # Test interfaces
        interface_names = [iface.name for iface in parse_info.interfaces]
        self.assertIn('UserRepository', interface_names)
        
        # Test data classes
        data_class_names = [dc.name for dc in parse_info.data_classes]
        self.assertIn('User', data_class_names)
        
        # Test objects
        object_names = [obj.name for obj in parse_info.objects]
        self.assertIn('DatabaseConfig', object_names)
        
        # Test enums
        enum_names = [enum.name for enum in parse_info.enums]
        self.assertIn('Status', enum_names)
        
        # Test typealiases
        typealias_names = [ta.name for ta in parse_info.typealiases]
        self.assertIn('UserCallback', typealias_names)
        
        # Test functions (including extensions)
        function_names = [func.name for func in parse_info.functions]
        property_names = [prop.name for prop in parse_info.properties]
        
        # Test sealed classes
        sealed_class_names = [sc.name for sc in parse_info.sealed_classes]
        self.assertIn('Result', sealed_class_names)

    def test_is_class_declaration(self):
        """Test class declaration detection."""
        parser = KotlinParserAgent()
        
        self.assertTrue(parser._is_class_declaration('class MainActivity'))
        self.assertTrue(parser._is_class_declaration('data class User'))
        self.assertTrue(parser._is_class_declaration('sealed class Result<T>'))
        self.assertFalse(parser._is_class_declaration('fun test()'))
        self.assertFalse(parser._is_class_declaration('// class comment'))

    def test_is_interface_declaration(self):
        """Test interface declaration detection."""
        parser = KotlinParserAgent()
        
        self.assertTrue(parser._is_interface_declaration('interface UserRepository'))
        self.assertFalse(parser._is_interface_declaration('class MainActivity'))
        self.assertFalse(parser._is_interface_declaration('// interface comment'))

    def test_is_object_declaration(self):
        """Test object declaration detection."""
        parser = KotlinParserAgent()
        
        self.assertTrue(parser._is_object_declaration('object DatabaseConfig'))
        self.assertTrue(parser._is_object_declaration('companion object'))
        self.assertFalse(parser._is_object_declaration('class MainActivity'))

    def test_is_function_declaration(self):
        """Test function declaration detection."""
        parser = KotlinParserAgent()
        
        self.assertTrue(parser._is_function_declaration('fun onCreate()'))
        self.assertTrue(parser._is_function_declaration('suspend fun getUser()'))
        self.assertTrue(parser._is_function_declaration('fun String.isValidEmail()'))
        self.assertFalse(parser._is_function_declaration('class MainActivity'))
        self.assertFalse(parser._is_function_declaration('// fun comment'))

    def test_is_property_declaration(self):
        """Test property declaration detection."""
        parser = KotlinParserAgent()
        
        self.assertTrue(parser._is_property_declaration('val name: String'))
        self.assertTrue(parser._is_property_declaration('var count: Int = 0'))
        self.assertTrue(parser._is_property_declaration('const val TAG = "test"'))
        self.assertFalse(parser._is_property_declaration('fun test()'))

    def test_parse_class_declaration(self):
        """Test parsing class declarations."""
        parser = KotlinParserAgent()
        
        # Regular class
        node = parser._parse_class_declaration('class MainActivity : Activity()', 1)
        self.assertEqual(node.name, 'MainActivity')
        self.assertEqual(node.type, 'CLASS')
        self.assertEqual(node.start_line, 1)
        
        # Data class
        node = parser._parse_class_declaration('data class User(val id: String)', 1)
        self.assertEqual(node.name, 'User')
        self.assertIn('data', node.modifiers)

    def test_parse_function_declaration(self):
        """Test parsing function declarations."""
        parser = KotlinParserAgent()
        
        # Regular function
        node = parser._parse_function_declaration('fun onCreate()', 1)
        self.assertEqual(node.name, 'onCreate')
        self.assertEqual(node.type, 'FUNCTION')
        
        # Extension function
        node = parser._parse_function_declaration('fun String.isValidEmail(): Boolean', 1)
        self.assertEqual(node.name, 'isValidEmail')
        self.assertEqual(node.properties.get('receiver_type'), 'String')
        self.assertTrue(node.properties.get('is_extension', False))

    def test_parse_property_declaration(self):
        """Test parsing property declarations."""
        parser = KotlinParserAgent()
        
        # Val property
        node = parser._parse_property_declaration('val name: String = "test"', 1)
        self.assertEqual(node.name, 'name')
        self.assertTrue(node.properties['is_val'])
        self.assertFalse(node.properties['is_var'])
        
        # Var property
        node = parser._parse_property_declaration('var count: Int = 0', 1)
        self.assertEqual(node.name, 'count')
        self.assertFalse(node.properties['is_val'])
        self.assertTrue(node.properties['is_var'])

    def test_error_handling_file_not_found(self):
        """Test error handling khi file không tồn tại."""
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = '/usr/bin/kotlinc\n'
            mock_run.return_value = mock_result
            
            parser = KotlinParserAgent()
            
            results = parser.parse_kotlin_files(['nonexistent.kt'])
            self.assertEqual(len(results), 1)
            file_path, parse_info = results[0]
            self.assertEqual(file_path, 'nonexistent.kt')
            self.assertIsInstance(parse_info, KotlinParseInfo)

    def test_error_handling_timeout(self):
        """Test error handling khi timeout."""
        with patch('subprocess.run') as mock_run:
            # Mock kotlinc detection first
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = '/usr/bin/kotlinc\n'
            mock_run.return_value = mock_result
            
            parser = KotlinParserAgent()
            
            # Mock timeout cho syntax check
            from subprocess import TimeoutExpired
            mock_run.side_effect = TimeoutExpired('kotlinc', 30)
            
            result = parser._check_kotlin_syntax('test.kt')
            self.assertFalse(result)


if __name__ == '__main__':
    unittest.main() 