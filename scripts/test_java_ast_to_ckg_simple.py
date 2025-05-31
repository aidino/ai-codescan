#!/usr/bin/env python3
"""
Simple demo script để test Java AST to CKG Builder functionality.
"""

import sys
import os
import tempfile

# Add src to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, '..', 'src')
sys.path.insert(0, src_dir)

def main():
    """Simple test của Java AST to CKG functionality."""
    print("🚀 Simple Java AST to CKG Test")
    print("=" * 40)
    
    try:
        # Test basic imports
        print("📦 Testing imports...")
        
        from agents.ckg_operations.java_parser import JavaParserAgent
        print("   ✅ JavaParserAgent imported")
        
        from agents.ckg_operations.ast_to_ckg_builder import ASTtoCKGBuilderAgent
        print("   ✅ ASTtoCKGBuilderAgent imported")
        
        from agents.ckg_operations.ckg_schema import NodeType, RelationshipType
        print("   ✅ CKG Schema imported")
        
        # Create simple Java code
        print("\n📝 Creating test Java code...")
        java_code = '''
package com.test;

public class SimpleClass {
    private String name;
    
    public SimpleClass(String name) {
        this.name = name;
    }
    
    public String getName() {
        return name;
    }
}
'''
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(java_code)
            java_file = f.name
        
        print(f"   ✅ Created temp file: {java_file}")
        
        # Test Java parsing
        print("\n🔧 Testing Java parsing...")
        java_parser = JavaParserAgent()
        parse_info = java_parser.parse_file(java_file)
        
        if parse_info.success:
            print(f"   ✅ Parse successful!")
            print(f"   📋 Package: {parse_info.package_name}")
            print(f"   📦 Classes: {parse_info.class_count}")
            print(f"   🔧 Methods: {parse_info.method_count}")
        else:
            print(f"   ❌ Parse failed: {parse_info.error_message}")
            return False
        
        # Test CKG Builder (without full integration)
        print("\n🏗️  Testing CKG Builder...")
        ckg_builder = ASTtoCKGBuilderAgent()
        
        # Create simple ParsedFile
        from agents.ckg_operations.code_parser_coordinator import ParsedFile
        parsed_file = ParsedFile(
            file_path=java_file,
            relative_path="SimpleClass.java",
            language="Java",
            ast_tree=parse_info.ast_root,
            parse_success=True,
            nodes_count=parse_info.class_count + parse_info.method_count,
            lines_count=parse_info.lines_count
        )
        
        # Process file to generate Cypher queries
        queries = ckg_builder._process_file(parsed_file)
        print(f"   ✅ Generated {len(queries)} Cypher queries")
        
        # Show sample queries
        if queries:
            print("\n📝 Sample queries:")
            for i, query in enumerate(queries[:3], 1):
                print(f"   {i}. {query[:80]}...")
        
        # Show created nodes
        print(f"\n🏗️  Created {len(ckg_builder.created_nodes)} nodes:")
        node_types = {}
        for node in ckg_builder.created_nodes.values():
            node_type = node.type.value
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        for node_type, count in sorted(node_types.items()):
            print(f"   • {node_type}: {count}")
        
        # Show relationships
        print(f"\n🔗 Created {len(ckg_builder.created_relationships)} relationships:")
        rel_types = {}
        for rel in ckg_builder.created_relationships:
            rel_type = rel.type.value
            rel_types[rel_type] = rel_types.get(rel_type, 0) + 1
        
        for rel_type, count in sorted(rel_types.items()):
            print(f"   • {rel_type}: {count}")
        
        print("\n🎉 Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        if 'java_file' in locals():
            try:
                os.unlink(java_file)
                print(f"\n🧹 Cleaned up temp file")
            except:
                pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 