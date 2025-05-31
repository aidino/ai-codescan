#!/usr/bin/env python3
"""
AI CodeScan - CKG Operations Agent

Agent tổng hợp các chức năng CKG operations.
"""

import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

from .code_parser_coordinator import CodeParserCoordinatorAgent, ParseResult
from .ast_to_ckg_builder import ASTtoCKGBuilderAgent, CKGBuildResult
from .ckg_query_interface import CKGQueryInterfaceAgent, CKGQueryResult, ConnectionConfig

logger = logging.getLogger(__name__)


class CKGOperationsAgent:
    """
    Agent tổng hợp các chức năng CKG operations.
    
    Provides high-level interface cho:
    - Code parsing và AST generation
    - CKG building từ AST
    - CKG querying và analysis
    """
    
    def __init__(self,
                 neo4j_config: Optional[ConnectionConfig] = None,
                 project_path: Optional[str] = None):
        """
        Initialize CKG Operations Agent.
        
        Args:
            neo4j_config: Neo4j connection configuration
            project_path: Path to project for analysis
        """
        self.project_path = project_path
        self.neo4j_config = neo4j_config or ConnectionConfig()
        
        # Initialize sub-agents
        try:
            self.parser_coordinator = CodeParserCoordinatorAgent()
            self.ckg_builder = ASTtoCKGBuilderAgent()
            self.query_interface = CKGQueryInterfaceAgent(self.neo4j_config)
            
            logger.info("CKGOperationsAgent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CKGOperationsAgent: {e}")
            # Initialize with None for graceful degradation
            self.parser_coordinator = None
            self.ckg_builder = None
            self.query_interface = None
    
    def parse_project(self, project_path: str) -> Optional[ParseResult]:
        """
        Parse project code to extract AST information.
        
        Args:
            project_path: Path to project directory
            
        Returns:
            ParseResult containing parsed information or None if failed
        """
        try:
            if not self.parser_coordinator:
                logger.warning("Parser coordinator not available")
                return None
                
            # Use parse_python_project for string path input
            return self.parser_coordinator.parse_python_project(project_path)
            
        except Exception as e:
            logger.error(f"Error parsing project {project_path}: {e}")
            return None
    
    def build_ckg(self, parse_result: ParseResult) -> Optional[CKGBuildResult]:
        """
        Build Code Knowledge Graph từ parse results.
        
        Args:
            parse_result: Results from code parsing
            
        Returns:
            CKGBuildResult containing build information or None if failed
        """
        try:
            if not self.ckg_builder:
                logger.warning("CKG builder not available")
                return None
                
            if not parse_result:
                logger.warning("No parse result provided for CKG building")
                return None
                
            return self.ckg_builder.build_ckg_from_parse_result(parse_result)
            
        except Exception as e:
            logger.error(f"Error building CKG: {e}")
            return None
    
    def query_ckg(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Optional[CKGQueryResult]:
        """
        Execute query against CKG database.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            CKGQueryResult containing query results or None if failed
        """
        try:
            if not self.query_interface:
                logger.warning("Query interface not available")
                return None
                
            return self.query_interface.execute_query(query, parameters)
            
        except Exception as e:
            logger.error(f"Error querying CKG: {e}")
            return None
    
    def get_functions_in_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Get all functions in a specific file.
        
        Args:
            file_path: Path to file
            
        Returns:
            List of function information dictionaries
        """
        try:
            if not self.query_interface:
                logger.warning("Query interface not available")
                return []
                
            return self.query_interface.get_functions_in_file(file_path)
            
        except Exception as e:
            logger.error(f"Error getting functions in file {file_path}: {e}")
            return []
    
    def get_classes_in_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Get all classes in a specific file.
        
        Args:
            file_path: Path to file
            
        Returns:
            List of class information dictionaries
        """
        try:
            if not self.query_interface:
                logger.warning("Query interface not available")
                return []
                
            return self.query_interface.get_classes_in_file(file_path)
            
        except Exception as e:
            logger.error(f"Error getting classes in file {file_path}: {e}")
            return []
    
    def find_function_callers(self, function_name: str) -> List[Dict[str, Any]]:
        """
        Find all functions that call a specific function.
        
        Args:
            function_name: Name of function to find callers for
            
        Returns:
            List of caller information dictionaries
        """
        try:
            if not self.query_interface:
                logger.warning("Query interface not available")
                return []
                
            return self.query_interface.find_function_callers(function_name)
            
        except Exception as e:
            logger.error(f"Error finding callers for function {function_name}: {e}")
            return []
    
    def find_function_callees(self, function_name: str) -> List[Dict[str, Any]]:
        """
        Find all functions called by a specific function.
        
        Args:
            function_name: Name of function to find callees for
            
        Returns:
            List of callee information dictionaries
        """
        try:
            if not self.query_interface:
                logger.warning("Query interface not available")
                return []
                
            return self.query_interface.find_function_callees(function_name)
            
        except Exception as e:
            logger.error(f"Error finding callees for function {function_name}: {e}")
            return []
    
    def get_project_statistics(self) -> Dict[str, Any]:
        """
        Get overall project statistics from CKG.
        
        Returns:
            Dictionary containing project statistics
        """
        try:
            if not self.query_interface:
                logger.warning("Query interface not available")
                return {
                    'total_files': 0,
                    'total_functions': 0,
                    'total_classes': 0,
                    'error': 'Query interface not available'
                }
                
            return self.query_interface.get_project_statistics()
            
        except Exception as e:
            logger.error(f"Error getting project statistics: {e}")
            return {
                'total_files': 0,
                'total_functions': 0,
                'total_classes': 0,
                'error': str(e)
            }
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """
        Find circular dependencies in the codebase.
        
        Returns:
            List of circular dependency chains
        """
        try:
            if not self.query_interface:
                logger.warning("Query interface not available")
                return []
                
            return self.query_interface.find_circular_dependencies()
            
        except Exception as e:
            logger.error(f"Error finding circular dependencies: {e}")
            return []
    
    def search_by_name(self, name_pattern: str) -> List[Dict[str, Any]]:
        """
        Search CKG by name pattern.
        
        Args:
            name_pattern: Pattern to search for (supports regex)
            
        Returns:
            List of matching elements
        """
        try:
            if not self.query_interface:
                logger.warning("Query interface not available")
                return []
                
            return self.query_interface.search_by_name(name_pattern)
            
        except Exception as e:
            logger.error(f"Error searching by name pattern {name_pattern}: {e}")
            return []
    
    def is_available(self) -> bool:
        """
        Check if CKG operations are available.
        
        Returns:
            True if all sub-agents are available
        """
        return all([
            self.parser_coordinator is not None,
            self.ckg_builder is not None,
            self.query_interface is not None
        ])
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status information về CKG operations.
        
        Returns:
            Status dictionary with component availability
        """
        return {
            'available': self.is_available(),
            'parser_coordinator': self.parser_coordinator is not None,
            'ckg_builder': self.ckg_builder is not None,
            'query_interface': self.query_interface is not None,
            'project_path': self.project_path,
            'neo4j_config': {
                'uri': self.neo4j_config.uri if self.neo4j_config else None,
                'database': self.neo4j_config.database if self.neo4j_config else None
            }
        } 