#!/usr/bin/env python3
"""
AI CodeScan - Base Graph Module

This module provides the base graph class for LangGraph integration,
handling graph construction, state management, and execution flow.
"""

import sys
import logging
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from dataclasses import dataclass
from enum import Enum
import os

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from loguru import logger

class TaskType(Enum):
    """Định nghĩa các loại task trong hệ thống."""
    PROJECT_REVIEW = "project_review"
    PR_REVIEW = "pr_review"
    QNA = "qna"
    DIAGRAM_GENERATION = "diagram_generation"

class TaskStatus(Enum):
    """Trạng thái của task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Repository:
    """Thông tin repository để phân tích."""
    url: str
    branch: str = "main"
    commit_hash: Optional[str] = None
    access_token: Optional[str] = None

@dataclass
class PRInfo:
    """Thông tin Pull Request."""
    pr_id: str
    title: str
    description: str
    author: str
    target_branch: str
    source_branch: str
    files_changed: List[str]

class CodeScanState(TypedDict):
    """
    State class cho AI CodeScan graph.
    
    Attributes:
        task_id: UUID của task
        task_type: Loại task (project_review, pr_review, etc.)
        status: Trạng thái hiện tại của task
        repository: Thông tin repository 
        pr_info: Thông tin PR (nếu có)
        code_files: Danh sách files code đã được phân tích
        analysis_results: Kết quả phân tích từ các agents
        knowledge_graph: Dữ liệu CKG (Code Knowledge Graph)
        user_questions: Câu hỏi từ user
        responses: Câu trả lời từ hệ thống
        errors: Danh sách lỗi nếu có
        metadata: Metadata bổ sung
        next_action: Action tiếp theo cần thực hiện
    """
    task_id: str
    task_type: TaskType
    status: TaskStatus
    repository: Optional[Repository]
    pr_info: Optional[PRInfo]
    code_files: List[Dict[str, Any]]
    analysis_results: Dict[str, Any]
    knowledge_graph: Dict[str, Any]
    user_questions: List[str]
    responses: List[str]
    errors: List[str]
    metadata: Dict[str, Any]
    next_action: Optional[str]

class BaseGraph:
    """
    Base class cho tất cả LangGraph workflows trong AI CodeScan.
    
    Cung cấp chức năng cơ bản để:
    - Khởi tạo graph với state management
    - Checkpoint/restore functionality
    - Error handling và logging
    - Integration với LLM và tools
    """
    
    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        checkpointer: Optional[Any] = None,
        use_memory_saver: bool = True
    ):
        """
        Khởi tạo base graph.
        
        Args:
            llm: LLM instance (mặc định sử dụng OpenAI)
            checkpointer: Checkpoint saver instance
            use_memory_saver: Sử dụng MemorySaver nếu True
        """
        self.llm = llm or self._create_default_llm()
        self.checkpointer = checkpointer or self._create_checkpointer(use_memory_saver)
        self.graph = None
        self.compiled_graph = None
        
        # Setup logging
        logger.add(
            "logs/langgraph_{time}.log",
            rotation="1 day",
            retention="30 days",
            level="INFO"
        )
    
    def _create_default_llm(self) -> ChatOpenAI:
        """Tạo LLM mặc định."""
        # Check nếu có API key thực
        api_key = os.getenv("OPENAI_API_KEY")
        
        if api_key and api_key != "your-api-key-here":
            return ChatOpenAI(
                model="gpt-4",
                temperature=0.1,
                max_tokens=4000
            )
        else:
            # Mock LLM cho testing
            from .mock_llm import MockChatOpenAI
            return MockChatOpenAI()
    
    def _create_checkpointer(self, use_memory: bool = True) -> Any:
        """
        Tạo checkpointer cho state persistence.
        
        Args:
            use_memory: Sử dụng MemorySaver thay vì PostgresSaver
        """
        if use_memory:
            return MemorySaver()
        else:
            # Sử dụng PostgresSaver cho production
            # Cần configuration từ environment
            try:
                from config import Config
                return PostgresSaver.from_conn_string(
                    f"postgresql://{Config.NEO4J_USER}:{Config.NEO4J_PASSWORD}@{Config.NEO4J_HOST}:5432/{Config.NEO4J_DATABASE}"
                )
            except ImportError:
                logger.warning("Không thể tạo PostgresSaver, sử dụng MemorySaver")
                return MemorySaver()
    
    def create_initial_state(self, **kwargs) -> CodeScanState:
        """
        Tạo state ban đầu cho graph.
        
        Args:
            **kwargs: Các tham số để khởi tạo state
            
        Returns:
            CodeScanState: State ban đầu
        """
        return CodeScanState(
            task_id=kwargs.get("task_id", ""),
            task_type=kwargs.get("task_type", TaskType.PROJECT_REVIEW),
            status=TaskStatus.PENDING,
            repository=kwargs.get("repository"),
            pr_info=kwargs.get("pr_info"),
            code_files=[],
            analysis_results={},
            knowledge_graph={},
            user_questions=[],
            responses=[],
            errors=[],
            metadata=kwargs.get("metadata", {}),
            next_action=None
        )
    
    def build_graph(self) -> StateGraph:
        """
        Abstract method để build graph structure.
        Các subclass cần override method này.
        
        Returns:
            StateGraph: Configured graph
        """
        raise NotImplementedError("Subclasses must implement build_graph()")
    
    def compile_graph(self) -> Any:
        """
        Compile graph với checkpointer.
        
        Returns:
            Compiled graph ready for execution
        """
        if not self.graph:
            self.graph = self.build_graph()
        
        self.compiled_graph = self.graph.compile(
            checkpointer=self.checkpointer,
            interrupt_before=[],  # Có thể override trong subclass
            interrupt_after=[]
        )
        
        return self.compiled_graph
    
    def execute(
        self,
        initial_state: CodeScanState,
        config: Optional[RunnableConfig] = None
    ) -> CodeScanState:
        """
        Thực thi graph với state ban đầu.
        
        Args:
            initial_state: State ban đầu
            config: Configuration cho execution
            
        Returns:
            CodeScanState: Final state sau khi thực thi
        """
        if not self.compiled_graph:
            self.compile_graph()
        
        try:
            logger.info(f"Bắt đầu thực thi task {initial_state['task_id']}")
            
            result = self.compiled_graph.invoke(
                initial_state,
                config=config or {"configurable": {"thread_id": initial_state["task_id"]}}
            )
            
            logger.info(f"Hoàn thành task {initial_state['task_id']}")
            return result
            
        except Exception as e:
            logger.error(f"Lỗi khi thực thi task {initial_state['task_id']}: {str(e)}")
            # Update state với error
            initial_state["status"] = TaskStatus.FAILED
            initial_state["errors"].append(str(e))
            return initial_state
    
    def stream_execute(
        self,
        initial_state: CodeScanState,
        config: Optional[RunnableConfig] = None
    ):
        """
        Thực thi graph với streaming output.
        
        Args:
            initial_state: State ban đầu
            config: Configuration cho execution
            
        Yields:
            State updates trong quá trình thực thi
        """
        if not self.compiled_graph:
            self.compile_graph()
        
        try:
            logger.info(f"Bắt đầu streaming execution cho task {initial_state['task_id']}")
            
            for chunk in self.compiled_graph.stream(
                initial_state,
                config=config or {"configurable": {"thread_id": initial_state["task_id"]}}
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"Lỗi trong streaming execution: {str(e)}")
            yield {"error": str(e)}
    
    def get_state(self, thread_id: str) -> Optional[CodeScanState]:
        """
        Lấy state hiện tại từ checkpointer.
        
        Args:
            thread_id: ID của thread/task
            
        Returns:
            CodeScanState hoặc None nếu không tìm thấy
        """
        if not self.compiled_graph:
            return None
        
        try:
            config = {"configurable": {"thread_id": thread_id}}
            state_snapshot = self.compiled_graph.get_state(config)
            return state_snapshot.values if state_snapshot else None
        except Exception as e:
            logger.error(f"Lỗi khi lấy state: {str(e)}")
            return None
    
    def get_state_history(self, thread_id: str, limit: int = 10) -> List[Any]:
        """
        Lấy lịch sử state của một thread.
        
        Args:
            thread_id: ID của thread
            limit: Số lượng state tối đa
            
        Returns:
            List các state snapshots
        """
        if not self.compiled_graph:
            return []
        
        try:
            config = {"configurable": {"thread_id": thread_id}}
            history = list(self.compiled_graph.get_state_history(config, limit=limit))
            return history
        except Exception as e:
            logger.error(f"Lỗi khi lấy state history: {str(e)}")
            return []
    
    def interrupt_execution(self, thread_id: str, message: str = ""):
        """
        Interrupt graph execution tại thread cụ thể.
        
        Args:
            thread_id: ID của thread cần interrupt
            message: Message kèm theo interrupt
        """
        logger.info(f"Interrupting execution for thread {thread_id}: {message}")
        # Implementation tùy thuộc vào use case cụ thể
    
    def resume_execution(self, thread_id: str, input_data: Dict[str, Any] = None):
        """
        Resume execution từ interrupt point.
        
        Args:
            thread_id: ID của thread cần resume
            input_data: Dữ liệu bổ sung để resume
        """
        if not self.compiled_graph:
            return None
        
        try:
            config = {"configurable": {"thread_id": thread_id}}
            return self.compiled_graph.invoke(input_data or {}, config=config)
        except Exception as e:
            logger.error(f"Lỗi khi resume execution: {str(e)}")
            return None 