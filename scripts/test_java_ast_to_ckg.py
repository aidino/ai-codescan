#!/usr/bin/env python3
"""
Demo script để test Java AST to CKG Builder integration.

Script này test end-to-end flow từ Java source code → parsing → CKG build.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add src to path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.ckg_operations.java_parser import JavaParserAgent
from agents.ckg_operations.code_parser_coordinator import CodeParserCoordinatorAgent, ParsedFile
from agents.ckg_operations.ast_to_ckg_builder import ASTtoCKGBuilderAgent
from agents.data_acquisition import LanguageInfo, ProjectLanguageProfile


def create_test_java_file() -> str:
    """Tạo file Java test cho demo."""
    java_code = '''
package com.example.demo;

import java.util.List;
import java.util.ArrayList;
import java.io.IOException;

/**
 * Demo class for testing Java CKG integration.
 */
public class DemoClass extends BaseClass implements DemoInterface {
    
    private String name;
    private int value;
    private List<String> items;
    
    public static final String CONSTANT = "TEST";
    
    /**
     * Constructor for DemoClass.
     */
    public DemoClass(String name, int value) {
        this.name = name;
        this.value = value;
        this.items = new ArrayList<>();
    }
    
    /**
     * Get the name.
     */
    public String getName() {
        return name;
    }
    
    /**
     * Set the name.
     */
    public void setName(String name) {
        this.name = name;
    }
    
    /**
     * Process items with error handling.
     */
    public void processItems() throws IOException {
        for (String item : items) {
            System.out.println("Processing: " + item);
        }
    }
    
    /**
     * Static utility method.
     */
    public static void utilityMethod(String input) {
        System.out.println("Utility: " + input);
    }
    
    @Override
    public void interfaceMethod() {
        System.out.println("Interface implementation");
    }
}

/**
 * Demo interface.
 */
interface DemoInterface {
    void interfaceMethod();
}

/**
 * Demo enum.
 */
enum DemoEnum {
    OPTION_A("A"),
    OPTION_B("B"),
    OPTION_C("C");
    
    private final String value;
    
    DemoEnum(String value) {
        this.value = value;
    }
    
    public String getValue() {
        return value;
    }
}
'''
    
    # Tạo temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
        f.write(java_code)
        return f.name


def test_java_ast_to_ckg_integration():
    """Test tích hợp Java AST to CKG Builder."""
    print("🧪 Testing Java AST to CKG Builder Integration...")
    print("=" * 60)
    
    try:
        # Step 1: Tạo test file
        print("📁 Tạo test Java file...")
        java_file_path = create_test_java_file()
        print(f"   ✅ Created: {java_file_path}")
        
        # Step 2: Initialize Java Parser
        print("\n🔧 Khởi tạo Java Parser...")
        java_parser = JavaParserAgent()
        print("   ✅ JavaParserAgent initialized")
        
        # Step 3: Parse Java file  
        print("\n📊 Parse Java file...")
        parse_info = java_parser.parse_file(java_file_path)
        
        if parse_info.success:
            print(f"   ✅ Parse thành công!")
            print(f"   📋 Package: {parse_info.package_name}")
            print(f"   📦 Classes: {parse_info.class_count}")
            print(f"   🔧 Methods: {parse_info.method_count}")
            print(f"   📄 Lines: {parse_info.lines_count}")
        else:
            print(f"   ❌ Parse failed: {parse_info.error_message}")
            return False
        
        # Step 4: Tạo ParsedFile object
        print("\n🗂️  Tạo ParsedFile object...")
        parsed_file = ParsedFile(
            file_path=java_file_path,
            relative_path="DemoClass.java",
            language="Java",
            ast_tree=parse_info.ast_root,
            parse_success=True,
            nodes_count=parse_info.method_count + parse_info.class_count,
            lines_count=parse_info.lines_count
        )
        print("   ✅ ParsedFile created successfully")
        
        # Step 5: Initialize CKG Builder
        print("\n🏗️  Khởi tạo AST to CKG Builder...")
        ckg_builder = ASTtoCKGBuilderAgent()
        print("   ✅ ASTtoCKGBuilderAgent initialized")
        
        # Step 6: Tạo mock ParseResult
        print("\n📊 Tạo ParseResult...")
        java_lang_info = LanguageInfo(
            name="Java",
            percentage=100.0,
            file_count=1,
            total_lines=parse_info.lines_count
        )
        
        language_profile = ProjectLanguageProfile(
            primary_language="Java",
            languages=[java_lang_info],
            frameworks=[],
            build_tools=[],
            package_managers=[],
            project_type="demo",
            confidence_score=1.0
        )
        
        from agents.ckg_operations.code_parser_coordinator import ParseResult
        parse_result = ParseResult(
            project_path=os.path.dirname(java_file_path),
            language_profile=language_profile,
            parsed_files=[parsed_file],
            total_files=1,
            successful_files=1,
            failed_files=0,
            parse_errors=[],
            parsing_stats={"primary_language": "Java"}
        )
        print("   ✅ ParseResult created")
        
        # Step 7: Build CKG
        print("\n🎯 Build Code Knowledge Graph...")
        ckg_result = ckg_builder.build_ckg_from_parse_result(parse_result)
        
        if ckg_result.build_success:
            print(f"   ✅ CKG build thành công!")
            print(f"   🏗️  Total nodes created: {ckg_result.total_nodes_created}")
            print(f"   🔗 Total relationships created: {ckg_result.total_relationships_created}")
            print(f"   📝 Cypher queries executed: {ckg_result.cypher_queries_executed}")
        else:
            print(f"   ❌ CKG build failed!")
            for error in ckg_result.error_messages:
                print(f"      • {error}")
            return False
        
        # Step 8: Inspect created nodes
        print("\n🔍 Phân tích created nodes...")
        node_types = {}
        for node in ckg_builder.created_nodes.values():
            node_type = node.type.value
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        print("   📊 Node types created:")
        for node_type, count in sorted(node_types.items()):
            print(f"      • {node_type}: {count}")
        
        # Step 9: Inspect relationships
        print("\n🔗 Phân tích relationships...")
        rel_types = {}
        for rel in ckg_builder.created_relationships:
            rel_type = rel.type.value
            rel_types[rel_type] = rel_types.get(rel_type, 0) + 1
        
        print("   📊 Relationship types created:")
        for rel_type, count in sorted(rel_types.items()):
            print(f"      • {rel_type}: {count}")
        
        # Step 10: Sample Cypher queries
        print("\n📝 Sample Cypher queries generated:")
        sample_queries = ckg_builder._process_file(parsed_file)[:3]  # First 3 queries
        for i, query in enumerate(sample_queries, 1):
            print(f"   {i}. {query[:100]}...")
        
        print("\n🎉 Java AST to CKG integration test PASSED!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed với lỗi: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        if 'java_file_path' in locals():
            try:
                os.unlink(java_file_path)
                print(f"🧹 Cleaned up: {java_file_path}")
            except:
                pass


def main():
    """Main function để chạy test."""
    print("🚀 Java AST to CKG Builder Integration Test")
    print("Testing end-to-end Java parsing và CKG generation...")
    print()
    
    success = test_java_ast_to_ckg_integration()
    
    if success:
        print("\n✅ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 