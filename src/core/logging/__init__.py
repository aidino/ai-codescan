"""
Core Logging Module for AI CodeScan.

Provides debug logging và tracing capabilities cho repository analysis workflow.
"""

from .debug_logger import (
    DebugLogger,
    debug_trace,
    get_debug_logger,
    set_debug_logger,
    create_session_debug_logger,
    log_repository_analysis_start,
    log_repository_analysis_end
)

__all__ = [
    "DebugLogger",
    "debug_trace", 
    "get_debug_logger",
    "set_debug_logger",
    "create_session_debug_logger",
    "log_repository_analysis_start",
    "log_repository_analysis_end"
] 