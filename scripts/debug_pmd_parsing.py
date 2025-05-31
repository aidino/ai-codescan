#!/usr/bin/env python3
"""
Debug script để test PMD XML parsing.
"""

import xml.etree.ElementTree as ET

def debug_pmd_xml_parsing():
    """Debug PMD XML parsing."""
    
    xml_output = '''<?xml version="1.0" encoding="UTF-8"?>
<pmd xmlns="http://pmd.sourceforge.net/report/2.0.0">
    <file name="/test/TestClass.java">
        <violation beginline="10" begincolumn="5" priority="3" rule="UnusedLocalVariable" ruleset="java-basic">
            Avoid unused local variables such as 'unusedVar'.
        </violation>
        <violation beginline="15" begincolumn="1" priority="2" rule="ExcessiveMethodLength" ruleset="java-design">
            This method is too long.
        </violation>
    </file>
</pmd>'''
    
    print("🔍 Debug PMD XML Parsing")
    print("=" * 40)
    
    print(f"📄 XML Content:")
    print(xml_output)
    print()
    
    try:
        # Parse XML directly to see structure
        print("🔗 XML Parsing Analysis:")
        root = ET.fromstring(xml_output)
        print(f"Root tag: {root.tag}")
        print(f"Root attrib: {root.attrib}")
        print(f"Root namespace: {root.tag.split('}')[0] if '}' in root.tag else 'None'}")
        print()
        
        # Check for file elements
        files = root.findall('file')
        print(f"Files found (no namespace): {len(files)}")
        
        # Try with namespace
        ns = {'pmd': 'http://pmd.sourceforge.net/report/2.0.0'}
        files_ns = root.findall('pmd:file', ns)
        print(f"Files found (with namespace): {len(files_ns)}")
        print()
        
        # Try different approach
        files_all = root.findall('.//{http://pmd.sourceforge.net/report/2.0.0}file')
        print(f"Files found (full namespace xpath): {len(files_all)}")
        print()
        
        # Manual iteration
        print("🔍 Manual XML iteration:")
        for i, child in enumerate(root):
            print(f"Child {i}: tag={child.tag}, attrib={child.attrib}")
            if 'file' in child.tag:
                print(f"  Found file element!")
                for j, grandchild in enumerate(child):
                    print(f"    Grandchild {j}: tag={grandchild.tag}, attrib={grandchild.attrib}")
                    print(f"    Grandchild text: {grandchild.text}")
        print()
        
        # Test PMD XML parsing logic
        print("🧪 Testing PMD XML parsing logic:")
        findings = []
        
        # Process each file
        for file_elem in root.findall('.//{http://pmd.sourceforge.net/report/2.0.0}file'):
            file_path = file_elem.get('name', '')
            print(f"Processing file: {file_path}")
            
            # Process violations in this file
            for violation_elem in file_elem.findall('.//{http://pmd.sourceforge.net/report/2.0.0}violation'):
                begin_line = int(violation_elem.get('beginline', '0'))
                begin_column = int(violation_elem.get('begincolumn', '0'))
                priority = int(violation_elem.get('priority', '3'))
                rule = violation_elem.get('rule', '')
                ruleset = violation_elem.get('ruleset', '')
                message = violation_elem.text or ''
                
                print(f"  Violation: line={begin_line}, rule={rule}, message={message.strip()}")
                findings.append({
                    'file_path': file_path,
                    'line': begin_line,
                    'rule': rule,
                    'message': message.strip()
                })
        
        print(f"\nTotal findings: {len(findings)}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_pmd_xml_parsing() 