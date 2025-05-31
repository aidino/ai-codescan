#!/usr/bin/env python3
"""
AI CodeScan - Code Parser Coordinator Agent

Agent điều phối việc phân tích cú pháp (parsing) mã nguồn cho các ngôn ngữ khác nhau.
Hiện tại hỗ trợ Python sử dụng module ast built-in.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

from ..data_acquisition import ProjectDataContext, ProjectLanguageProfile


@dataclass
class ParsedFile:
    """Thông tin về file đã được parse."""
    file_path: str
    relative_path: str
    language: str
    ast_tree: Any
    parse_success: bool
    error_message: Optional[str] = None
    nodes_count: int = 0
    lines_count: int = 0


@dataclass
class ParseResult:
    """Kết quả parse của toàn bộ project."""
    project_path: str
    language_profile: ProjectLanguageProfile
    parsed_files: List[ParsedFile]
    total_files: int
    successful_files: int
    failed_files: int
    parse_errors: List[str]
    parsing_stats: Dict[str, Any]


class CodeParserCoordinatorAgent:
    """
    Agent điều phối phân tích cú pháp cho các ngôn ngữ lập trình khác nhau.
    
    Trách nhiệm:
    - Dựa trên danh sách ngôn ngữ từ ProjectDataContext, chọn parser phù hợp
    - Quản lý việc parse song song các file code
    - Thu thập kết quả AST từ các parser
    - Xử lý lỗi parse và báo cáo trạng thái
    """
    
    def __init__(self, max_file_size_mb: float = 5.0):
        """
        Khởi tạo CodeParserCoordinatorAgent.
        
        Args:
            max_file_size_mb: Kích thước file tối đa để parse (MB)
        """
        self.max_file_size_bytes = int(max_file_size_mb * 1024 * 1024)
        self.supported_languages = {
            'Python': self._parse_python_files,
            'Java': self._parse_java_files,
            'Dart': self._parse_dart_files,
        }
        
        # Initialize Java parser
        try:
            from .java_parser import JavaParserAgent
            self.java_parser = JavaParserAgent()
            logger.info("Java parser initialized successfully")
        except Exception as e:
            logger.warning(f"Java parser initialization failed: {e}")
            self.java_parser = None
        
        # Initialize Dart parser
        try:
            from .dart_parser import DartParserAgent
            self.dart_parser = DartParserAgent()
            logger.info("Dart parser initialized successfully")
        except Exception as e:
            logger.warning(f"Dart parser initialization failed: {e}")
            self.dart_parser = None
        
    def parse_project(self, project_context: ProjectDataContext) -> ParseResult:
        """
        Parse toàn bộ project dựa trên ProjectDataContext.
        
        Args:
            project_context: Context chứa thông tin project
            
        Returns:
            ParseResult: Kết quả parse toàn bộ project
            
        Raises:
            ValueError: Nếu ngôn ngữ chính không được hỗ trợ
        """
        logger.info(f"Bắt đầu parse project: {project_context.repository_info.local_path}")
        
        primary_language = project_context.language_profile.primary_language
        project_path = project_context.repository_info.local_path
        
        # Kiểm tra ngôn ngữ được hỗ trợ
        if primary_language not in self.supported_languages:
            raise ValueError(f"Ngôn ngữ {primary_language} chưa được hỗ trợ")
        
        # Lấy danh sách file cần parse
        files_to_parse = self._get_files_to_parse(project_context)
        logger.info(f"Tìm thấy {len(files_to_parse)} file {primary_language} cần parse")
        
        # Parse files
        parser_func = self.supported_languages[primary_language]
        parsed_files = parser_func(files_to_parse)
        
        # Tính toán stats
        successful_files = sum(1 for f in parsed_files if f.parse_success)
        failed_files = len(parsed_files) - successful_files
        parse_errors = [f.error_message for f in parsed_files if f.error_message]
        
        parsing_stats = {
            'primary_language': primary_language,
            'total_nodes': sum(f.nodes_count for f in parsed_files if f.parse_success),
            'total_lines': sum(f.lines_count for f in parsed_files),
            'average_nodes_per_file': successful_files and sum(f.nodes_count for f in parsed_files if f.parse_success) / successful_files or 0,
            'success_rate': successful_files / len(parsed_files) if parsed_files else 0,
            'largest_file_lines': max((f.lines_count for f in parsed_files), default=0),
            'parsing_coverage': successful_files / len(files_to_parse) if files_to_parse else 0
        }
        
        result = ParseResult(
            project_path=project_path,
            language_profile=project_context.language_profile,
            parsed_files=parsed_files,
            total_files=len(parsed_files),
            successful_files=successful_files,
            failed_files=failed_files,
            parse_errors=parse_errors,
            parsing_stats=parsing_stats
        )
        
        logger.info(f"Parse hoàn tất: {successful_files}/{len(parsed_files)} files thành công")
        return result
    
    def parse_python_project(self, project_path: str) -> ParseResult:
        """
        Parse Python project (để tương thích với interface cũ).
        
        Args:
            project_path: Đường dẫn đến project
            
        Returns:
            ParseResult: Kết quả parse
        """
        logger.info(f"Parse Python project: {project_path}")
        
        # Tìm tất cả file .py
        python_files = []
        for root, dirs, files in os.walk(project_path):
            # Bỏ qua các thư mục ẩn và cache
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, project_path)
                    
                    # Kiểm tra kích thước file
                    if os.path.getsize(file_path) <= self.max_file_size_bytes:
                        python_files.append((file_path, relative_path))
        
        # Parse files
        parsed_files = self._parse_python_files(python_files)
        
        # Tạo mock language profile
        from ..data_acquisition import LanguageInfo, ProjectLanguageProfile
        primary_lang_info = LanguageInfo(
            name="Python",
            percentage=100.0,
            file_count=len(python_files),
            total_lines=sum(f.lines_count for f in parsed_files)
        )
        
        mock_language_profile = ProjectLanguageProfile(
            primary_language="Python",
            languages=[primary_lang_info],
            frameworks=[],
            build_tools=[],
            package_managers=[],
            project_type="library",
            confidence_score=0.9
        )
        
        # Tính stats
        successful_files = sum(1 for f in parsed_files if f.parse_success)
        failed_files = len(parsed_files) - successful_files
        parse_errors = [f.error_message for f in parsed_files if f.error_message]
        
        parsing_stats = {
            'primary_language': 'Python',
            'total_nodes': sum(f.nodes_count for f in parsed_files if f.parse_success),
            'total_lines': sum(f.lines_count for f in parsed_files),
            'average_nodes_per_file': successful_files and sum(f.nodes_count for f in parsed_files if f.parse_success) / successful_files or 0,
            'success_rate': successful_files / len(parsed_files) if parsed_files else 0,
            'largest_file_lines': max((f.lines_count for f in parsed_files), default=0),
            'parsing_coverage': 1.0
        }
        
        return ParseResult(
            project_path=project_path,
            language_profile=mock_language_profile,
            parsed_files=parsed_files,
            total_files=len(parsed_files),
            successful_files=successful_files,
            failed_files=failed_files,
            parse_errors=parse_errors,
            parsing_stats=parsing_stats
        )
    
    def _get_files_to_parse(self, project_context: ProjectDataContext) -> List[Tuple[str, str]]:
        """
        Lấy danh sách file cần parse từ ProjectDataContext.
        
        Args:
            project_context: Context chứa thông tin project
            
        Returns:
            List[Tuple[str, str]]: Danh sách (file_path, relative_path)
        """
        files_to_parse = []
        primary_language = project_context.language_profile.primary_language
        
        for file_info in project_context.files:
            # Chỉ parse file của ngôn ngữ chính và không phải config file
            if (file_info.language == primary_language and 
                not file_info.is_config_file and 
                file_info.size_bytes <= self.max_file_size_bytes):
                
                files_to_parse.append((file_info.path, file_info.relative_path))
        
        return files_to_parse
    
    def _parse_python_files(self, files: List[Tuple[str, str]]) -> List[ParsedFile]:
        """
        Parse danh sách Python files.
        
        Args:
            files: Danh sách (file_path, relative_path)
            
        Returns:
            List[ParsedFile]: Danh sách file đã parse
        """
        parsed_files = []
        
        for file_path, relative_path in files:
            parsed_file = self._parse_python_file(file_path, relative_path)
            parsed_files.append(parsed_file)
        
        return parsed_files
    
    def _parse_python_file(self, file_path: str, relative_path: str) -> ParsedFile:
        """
        Parse một Python file sử dụng ast module.
        
        Args:
            file_path: Đường dẫn đầy đủ đến file
            relative_path: Đường dẫn relative
            
        Returns:
            ParsedFile: Thông tin file đã parse
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content, filename=file_path)
            
            # Đếm nodes
            nodes_count = self._count_ast_nodes(tree)
            lines_count = len(content.splitlines())
            
            return ParsedFile(
                file_path=file_path,
                relative_path=relative_path,
                language='Python',
                ast_tree=tree,
                parse_success=True,
                nodes_count=nodes_count,
                lines_count=lines_count
            )
            
        except SyntaxError as e:
            logger.warning(f"Syntax error trong file {relative_path}: {str(e)}")
            return ParsedFile(
                file_path=file_path,
                relative_path=relative_path,
                language='Python',
                ast_tree=None,
                parse_success=False,
                error_message=f"Syntax error: {str(e)}",
                lines_count=self._count_file_lines(file_path)
            )
            
        except UnicodeDecodeError as e:
            logger.warning(f"Encoding error trong file {relative_path}: {str(e)}")
            return ParsedFile(
                file_path=file_path,
                relative_path=relative_path,
                language='Python',
                ast_tree=None,
                parse_success=False,
                error_message=f"Encoding error: {str(e)}",
                lines_count=0
            )
            
        except Exception as e:
            logger.error(f"Unexpected error parsing file {relative_path}: {str(e)}")
            return ParsedFile(
                file_path=file_path,
                relative_path=relative_path,
                language='Python',
                ast_tree=None,
                parse_success=False,
                error_message=f"Parse error: {str(e)}",
                lines_count=self._count_file_lines(file_path)
            )
    
    def _count_ast_nodes(self, tree: ast.AST) -> int:
        """
        Đếm số lượng nodes trong AST.
        
        Args:
            tree: AST tree
            
        Returns:
            int: Số lượng nodes
        """
        count = 0
        for node in ast.walk(tree):
            count += 1
        return count
    
    def _count_file_lines(self, file_path: str) -> int:
        """
        Đếm số dòng trong file khi không thể parse.
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            int: Số dòng
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return len(f.readlines())
        except Exception:
            return 0
    
    def get_parsing_statistics(self, parse_result: ParseResult) -> Dict[str, Any]:
        """
        Lấy thống kê chi tiết về quá trình parsing.
        
        Args:
            parse_result: Kết quả parse
            
        Returns:
            Dict[str, Any]: Thống kê chi tiết
        """
        successful_files = [f for f in parse_result.parsed_files if f.parse_success]
        failed_files = [f for f in parse_result.parsed_files if not f.parse_success]
        
        stats = {
            'summary': parse_result.parsing_stats,
            'file_details': {
                'successful_count': len(successful_files),
                'failed_count': len(failed_files),
                'successful_files': [f.relative_path for f in successful_files],
                'failed_files': [
                    {
                        'file': f.relative_path,
                        'error': f.error_message
                    } for f in failed_files
                ]
            },
            'size_distribution': {
                'small_files': len([f for f in successful_files if f.lines_count < 100]),
                'medium_files': len([f for f in successful_files if 100 <= f.lines_count < 500]),
                'large_files': len([f for f in successful_files if f.lines_count >= 500])
            },
            'complexity_metrics': {
                'files_with_high_node_count': len([f for f in successful_files if f.nodes_count > 1000]),
                'average_complexity': parse_result.parsing_stats.get('average_nodes_per_file', 0)
            }
        }
        
        return stats 

    def _parse_java_files(self, files: List[Tuple[str, str]]) -> List[ParsedFile]:
        """
        Parse danh sách Java files.
        
        Args:
            files: Danh sách (file_path, relative_path)
            
        Returns:
            List[ParsedFile]: Danh sách file đã parse
        """
        if not self.java_parser:
            logger.error("Java parser not available")
            # Create failed ParsedFile entries
            parsed_files = []
            for file_path, relative_path in files:
                parsed_files.append(ParsedFile(
                    file_path=file_path,
                    relative_path=relative_path,
                    language='Java',
                    ast_tree=None,
                    parse_success=False,
                    error_message="Java parser not available",
                    lines_count=self._count_file_lines(file_path)
                ))
            return parsed_files
        
        return self.java_parser.parse_java_files(files) 

    def _parse_dart_files(self, files: List[Tuple[str, str]]) -> List[ParsedFile]:
        """
        Parse danh sách Dart files.
        
        Args:
            files: Danh sách (file_path, relative_path)
            
        Returns:
            List[ParsedFile]: Danh sách file đã parse
        """
        if not self.dart_parser:
            logger.error("Dart parser not available")
            # Create failed ParsedFile entries
            parsed_files = []
            for file_path, relative_path in files:
                parsed_files.append(ParsedFile(
                    file_path=file_path,
                    relative_path=relative_path,
                    language='Dart',
                    ast_tree=None,
                    parse_success=False,
                    error_message="Dart parser not available",
                    lines_count=self._count_file_lines(file_path)
                ))
            return parsed_files
        
        return self.dart_parser.parse_dart_files(files) 