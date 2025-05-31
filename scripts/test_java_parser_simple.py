#!/usr/bin/env python3
"""
Simple test script cho JavaParserAgent.

Test JavaParserAgent functionality mà không phụ thuộc vào các module khác.
"""

import sys
import tempfile
import os
import json
import subprocess
from pathlib import Path
from loguru import logger
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple


@dataclass
class ParsedFile:
    """Simple ParsedFile dataclass for testing."""
    file_path: str
    relative_path: str
    language: str
    ast_tree: Optional[Dict[str, Any]] = None
    parse_success: bool = False
    error_message: Optional[str] = None
    nodes_count: int = 0
    lines_count: int = 0


def test_java_command():
    """Test if Java is available."""
    logger.info("🧪 Testing Java availability...")
    
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
                logger.info(f"✅ Found Java command: {cmd}")
                logger.info(f"   Version info: {result.stderr.split()[0:3]}")
                return cmd
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue
    
    logger.error("❌ Java not found in system PATH")
    return None


def test_javaparser_jar():
    """Test if JavaParser JAR is available or can be downloaded."""
    logger.info("🧪 Testing JavaParser JAR availability...")
    
    # Check if JAR exists
    jar_dir = Path.home() / '.ai_codescan' / 'jars'
    jar_path = jar_dir / 'javaparser-core-3.26.4.jar'
    
    if jar_path.exists():
        logger.info(f"✅ Found existing JavaParser JAR: {jar_path}")
        return str(jar_path)
    
    # Try to download
    try:
        import requests
        jar_dir.mkdir(parents=True, exist_ok=True)
        
        url = "https://repo1.maven.org/maven2/com/github/javaparser/javaparser-core/3.26.4/javaparser-core-3.26.4.jar"
        
        logger.info("📥 Downloading JavaParser JAR...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(jar_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        logger.info(f"✅ Downloaded JavaParser JAR: {jar_path}")
        return str(jar_path)
        
    except Exception as e:
        logger.error(f"❌ Failed to download JavaParser JAR: {e}")
        return None


def create_simple_java_file() -> str:
    """Tạo một Java file đơn giản để test."""
    temp_dir = tempfile.mkdtemp(prefix="java_simple_test_")
    java_file = Path(temp_dir) / "SimpleTest.java"
    
    content = '''package com.test;

import java.util.List;
import java.util.ArrayList;

/**
 * Simple test class.
 */
public class SimpleTest {
    private String name;
    private int value;
    
    public SimpleTest(String name, int value) {
        this.name = name;
        this.value = value;
    }
    
    public String getName() {
        return name;
    }
    
    public int getValue() {
        return value;
    }
    
    public void setValue(int value) {
        this.value = value;
    }
    
    public static void main(String[] args) {
        SimpleTest test = new SimpleTest("Test", 42);
        System.out.println("Name: " + test.getName());
        System.out.println("Value: " + test.getValue());
    }
}
'''
    
    java_file.write_text(content)
    return str(java_file)


def test_java_parsing(java_cmd: str, jar_path: str):
    """Test Java parsing với JavaParser."""
    logger.info("🧪 Testing Java parsing...")
    
    # Create test file
    java_file_path = create_simple_java_file()
    logger.info(f"Created test file: {java_file_path}")
    
    try:
        # Create simple Java program to parse the file
        temp_dir = tempfile.mkdtemp(prefix="javaparser_test_")
        parser_java = Path(temp_dir) / "SimpleParser.java"
        
        parser_content = f'''
import com.github.javaparser.JavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ParseResult;
import java.io.File;
import java.util.Optional;

public class SimpleParser {{
    public static void main(String[] args) {{
        try {{
            JavaParser parser = new JavaParser();
            ParseResult<CompilationUnit> result = parser.parse(new File("{java_file_path}"));
            
            if (result.isSuccessful() && result.getResult().isPresent()) {{
                CompilationUnit cu = result.getResult().get();
                System.out.println("PARSE_SUCCESS");
                System.out.println("Package: " + cu.getPackageDeclaration().map(p -> p.getNameAsString()).orElse("none"));
                
                // Count classes
                int classCount = cu.findAll(ClassOrInterfaceDeclaration.class).size();
                System.out.println("Classes: " + classCount);
                
                // Count methods
                int methodCount = cu.findAll(MethodDeclaration.class).size();
                System.out.println("Methods: " + methodCount);
                
            }} else {{
                System.out.println("PARSE_FAILED");
                if (!result.getProblems().isEmpty()) {{
                    System.out.println("Problems: " + result.getProblems().get(0).getMessage());
                }}
            }}
        }} catch (Exception e) {{
            System.out.println("PARSE_ERROR: " + e.getMessage());
        }}
    }}
}}
'''
        
        parser_java.write_text(parser_content)
        
        # Compile the parser
        compile_cmd = [
            java_cmd.replace('java', 'javac'),
            '-cp', jar_path,
            str(parser_java)
        ]
        
        logger.info("Compiling parser...")
        compile_result = subprocess.run(
            compile_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if compile_result.returncode != 0:
            logger.error(f"❌ Compilation failed: {compile_result.stderr}")
            return False
        
        # Run the parser
        run_cmd = [
            java_cmd,
            '-cp', f"{jar_path}:{temp_dir}",
            'SimpleParser'
        ]
        
        logger.info("Running parser...")
        run_result = subprocess.run(
            run_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if run_result.returncode == 0:
            output = run_result.stdout.strip()
            logger.info(f"✅ Parser output:")
            for line in output.split('\n'):
                logger.info(f"   {line}")
            
            if "PARSE_SUCCESS" in output:
                logger.info("🎉 Java parsing successful!")
                return True
            else:
                logger.error("❌ Parse failed")
                return False
        else:
            logger.error(f"❌ Parser execution failed: {run_result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Exception during parsing: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if os.path.exists(java_file_path):
            os.remove(java_file_path)
            os.rmdir(os.path.dirname(java_file_path))
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)


def main():
    """Main test function."""
    logger.info("🚀 Starting Simple Java Parser Test")
    
    # Test 1: Java availability
    java_cmd = test_java_command()
    if not java_cmd:
        logger.error("❌ Java not available. Cannot proceed.")
        return False
    
    # Test 2: JavaParser JAR
    jar_path = test_javaparser_jar()
    if not jar_path:
        logger.error("❌ JavaParser JAR not available. Cannot proceed.")
        return False
    
    # Test 3: Java parsing
    success = test_java_parsing(java_cmd, jar_path)
    
    if success:
        logger.info("🎉 All tests passed! Java parsing infrastructure is working.")
    else:
        logger.error("❌ Java parsing test failed.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 