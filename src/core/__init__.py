"""
Core module for AI CodeScan.

Contains orchestrator, authentication, và logging components.
"""

# Import logging utilities
from .logging import (
    DebugLogger,
    debug_trace,
    get_debug_logger,
    set_debug_logger,
    create_session_debug_logger,
    log_repository_analysis_start,
    log_repository_analysis_end
)

__all__ = [
    # Logging utilities
    "DebugLogger",
    "debug_trace", 
    "get_debug_logger",
    "set_debug_logger",
    "create_session_debug_logger",
    "log_repository_analysis_start",
    "log_repository_analysis_end"
]
