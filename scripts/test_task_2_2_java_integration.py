#!/usr/bin/env python3
"""
Demo script để test Task 2.2 Java Integration.

Script này test:
1. JavaParserAgent functionality
2. CodeParserCoordinatorAgent với Java support
3. End-to-end Java parsing workflow
"""

import sys
import tempfile
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import without debug logging dependencies
from agents.ckg_operations.java_parser import JavaParserAgent


def create_test_java_project() -> str:
    """Tạo test Java project."""
    temp_dir = tempfile.mkdtemp(prefix="java_test_")
    project_path = Path(temp_dir)
    
    # Create Java files
    (project_path / "src" / "main" / "java" / "com" / "example").mkdir(parents=True, exist_ok=True)
    
    # Main class
    main_content = '''package com.example;

import java.util.List;
import java.util.ArrayList;

/**
 * Main application class.
 */
public class Application {
    private String name;
    private List<String> items;
    
    public Application(String name) {
        this.name = name;
        this.items = new ArrayList<>();
    }
    
    public void addItem(String item) {
        items.add(item);
    }
    
    public List<String> getItems() {
        return items;
    }
    
    public static void main(String[] args) {
        Application app = new Application("TestApp");
        app.addItem("item1");
        app.addItem("item2");
        
        System.out.println("Items: " + app.getItems());
    }
}
'''
    
    # Service interface
    service_content = '''package com.example;

import java.util.Optional;

/**
 * Service interface for data operations.
 */
public interface DataService {
    Optional<String> findById(Long id);
    void save(String data);
    void delete(Long id);
}
'''
    
    # Service implementation
    impl_content = '''package com.example;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

/**
 * Implementation of DataService.
 */
public class DataServiceImpl implements DataService {
    private Map<Long, String> storage = new HashMap<>();
    
    @Override
    public Optional<String> findById(Long id) {
        return Optional.ofNullable(storage.get(id));
    }
    
    @Override
    public void save(String data) {
        Long id = System.currentTimeMillis();
        storage.put(id, data);
    }
    
    @Override
    public void delete(Long id) {
        storage.remove(id);
    }
}
'''
    
    # Write files
    (project_path / "src" / "main" / "java" / "com" / "example" / "Application.java").write_text(main_content)
    (project_path / "src" / "main" / "java" / "com" / "example" / "DataService.java").write_text(service_content)
    (project_path / "src" / "main" / "java" / "com" / "example" / "DataServiceImpl.java").write_text(impl_content)
    
    return str(project_path)


def test_java_parser_agent():
    """Test JavaParserAgent standalone."""
    logger.info("🧪 Testing JavaParserAgent...")
    
    project_path = create_test_java_project()
    java_files = list(Path(project_path).glob("**/*.java"))
    
    if not java_files:
        logger.error("No Java files found in test project")
        return False
    
    logger.info(f"Found {len(java_files)} Java files")
    
    # Initialize Java parser
    try:
        java_parser = JavaParserAgent()
        logger.info("✅ JavaParserAgent initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize JavaParserAgent: {e}")
        return False
    
    # Parse Java files
    try:
        file_tuples = [(str(f), str(f.relative_to(project_path))) for f in java_files]
        parsed_files = java_parser.parse_java_files(file_tuples)
        
        logger.info(f"✅ Parsed {len(parsed_files)} Java files")
        
        # Show results
        for parsed_file in parsed_files:
            logger.info(f"📄 {parsed_file.relative_path}:")
            logger.info(f"   Language: {parsed_file.language}")
            logger.info(f"   Success: {parsed_file.parse_success}")
            logger.info(f"   Nodes: {parsed_file.nodes_count}")
            logger.info(f"   Lines: {parsed_file.lines_count}")
            
            if not parsed_file.parse_success and parsed_file.error_message:
                logger.warning(f"   Error: {parsed_file.error_message}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to parse Java files: {e}")
        return False


def test_code_parser_coordinator():
    """Test CodeParserCoordinatorAgent với Java support."""
    logger.info("🧪 Testing CodeParserCoordinatorAgent với Java...")
    
    project_path = create_test_java_project()
    
    # Create mock ProjectDataContext
    files = list(Path(project_path).glob("**/*.java"))
    file_infos = [
        FileInfo(
            file_path=str(f),
            relative_path=str(f.relative_to(project_path)),
            size_bytes=f.stat().st_size,
            language="java",
            timestamp=f.stat().st_mtime
        ) for f in files
    ]
    
    language_info = LanguageInfo(
        language="java",
        confidence=1.0,
        file_extensions=[".java"],
        framework_info={"type": "standard", "version": "unknown"}
    )
    
    project_context = ProjectDataContext(
        repository_info=None,  # Mock
        language_profile=None,  # Mock
        files=file_infos,
        project_metadata=None,  # Mock
        directory_structure=None  # Mock
    )
    project_context.project_path = project_path
    
    # Initialize coordinator
    try:
        coordinator = CodeParserCoordinatorAgent()
        logger.info("✅ CodeParserCoordinatorAgent initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize coordinator: {e}")
        return False
    
    # Parse project
    try:
        parse_result = coordinator.parse_project(project_context)
        
        logger.info(f"✅ Project parsing completed:")
        logger.info(f"   Total files: {parse_result.total_files}")
        logger.info(f"   Successful: {parse_result.successful_files}")
        logger.info(f"   Failed: {parse_result.failed_files}")
        
        # Show parsing stats
        stats = coordinator.get_parsing_statistics(parse_result)
        logger.info(f"📊 Parsing Statistics:")
        for key, value in stats.items():
            logger.info(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to parse project: {e}")
        return False


def main():
    """Main demo function."""
    logger.info("🚀 Starting Task 2.2 Java Integration Demo")
    
    success = True
    
    # Test 1: JavaParserAgent
    logger.info("\n" + "="*60)
    if not test_java_parser_agent():
        success = False
    
    # Test 2: CodeParserCoordinatorAgent
    logger.info("\n" + "="*60)
    if not test_code_parser_coordinator():
        success = False
    
    # Final result
    logger.info("\n" + "="*60)
    if success:
        logger.info("🎉 All tests passed! Java integration is working.")
    else:
        logger.error("❌ Some tests failed. Check logs above.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 