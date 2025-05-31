"""
Debug Logger System for AI CodeScan.

Cung cấp logging chi tiết cho việc debug và trace luồng phân tích repository.
Logs được lưu vào logs/debug/ với format chi tiết bao gồm function, file, và context.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, List, Union
from datetime import datetime
from functools import wraps
from loguru import logger
import traceback


class DebugLogger:
    """
    Debug logger chuyên cho việc trace luồng phân tích repository.
    
    Features:
    - Detailed function call logging
    - Context tracking through analysis workflow
    - Performance metrics
    - Error tracking với full stack traces
    - Session-based log grouping
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize debug logger.
        
        Args:
            session_id: Unique session ID để group logs
        """
        self.session_id = session_id or f"session_{int(time.time())}"
        self.start_time = time.time()
        self.call_stack: List[Dict[str, Any]] = []
        
        # Setup debug log directory
        self.debug_dir = Path("logs/debug")
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup log files
        self.setup_debug_logging()
        
        # Track analysis context
        self.analysis_context = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "repository_url": None,
            "current_stage": None,
            "stages_completed": [],
            "performance_metrics": {},
            "errors": []
        }
        
        self.log_session_start()
    
    def setup_debug_logging(self):
        """Setup detailed debug logging configuration."""
        
        # Main debug log file
        debug_log_file = self.debug_dir / f"debug_{self.session_id}.log"
        
        # Performance metrics log
        perf_log_file = self.debug_dir / f"performance_{self.session_id}.log"
        
        # Error tracking log
        error_log_file = self.debug_dir / f"errors_{self.session_id}.log"
        
        # Function calls trace log
        trace_log_file = self.debug_dir / f"trace_{self.session_id}.log"
        
        # Configure loguru for debug logging
        logger.add(
            str(debug_log_file),
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | SESSION:{extra[session_id]} | STAGE:{extra[stage]} | {message}",
            level="DEBUG",
            rotation="100 MB",
            retention="7 days",
            compression="gz",
            enqueue=True,
            backtrace=True,
            diagnose=True,
            filter=lambda record: record["extra"].get("log_type") == "debug"
        )
        
        # Performance logging
        logger.add(
            str(perf_log_file),
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | PERF | {extra[function_name]} | {extra[duration]:.3f}s | {message}",
            level="INFO",
            filter=lambda record: record["extra"].get("log_type") == "performance"
        )
        
        # Error logging
        logger.add(
            str(error_log_file),
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | ERROR | {name}:{function}:{line} | SESSION:{extra[session_id]} | {message}\n{extra[stack_trace]}",
            level="ERROR",
            filter=lambda record: record["extra"].get("log_type") == "error"
        )
        
        # Function trace logging
        logger.add(
            str(trace_log_file),
            format="{time:HH:mm:ss.SSS} | {extra[call_type]} | {extra[module]}::{extra[function_name]} | {message}",
            level="TRACE",
            filter=lambda record: record["extra"].get("log_type") == "trace"
        )
        
        self.debug_log_file = debug_log_file
        self.perf_log_file = perf_log_file
        self.error_log_file = error_log_file
        self.trace_log_file = trace_log_file
    
    def log_session_start(self):
        """Log session start với context information."""
        logger.bind(
            session_id=self.session_id,
            stage="INIT",
            log_type="debug"
        ).info(f"🚀 DEBUG SESSION STARTED: {self.session_id}")
        
        logger.bind(
            session_id=self.session_id,
            stage="INIT",
            log_type="debug"
        ).debug(f"Debug logs directory: {self.debug_dir}")
        
        logger.bind(
            session_id=self.session_id,
            stage="INIT",
            log_type="debug"
        ).debug(f"Session context initialized: {json.dumps(self.analysis_context, indent=2)}")
    
    def set_repository_context(self, repo_url: str, repo_name: str = None):
        """Set repository context cho session."""
        self.analysis_context["repository_url"] = repo_url
        self.analysis_context["repository_name"] = repo_name or repo_url.split('/')[-1]
        
        logger.bind(
            session_id=self.session_id,
            stage="CONTEXT",
            log_type="debug"
        ).info(f"📁 REPOSITORY CONTEXT SET: {repo_url}")
    
    def set_analysis_stage(self, stage: str):
        """Set current analysis stage."""
        if self.analysis_context["current_stage"]:
            self.analysis_context["stages_completed"].append(self.analysis_context["current_stage"])
        
        self.analysis_context["current_stage"] = stage
        
        logger.bind(
            session_id=self.session_id,
            stage=stage,
            log_type="debug"
        ).info(f"🔄 ANALYSIS STAGE: {stage}")
    
    def log_function_entry(self, func_name: str, module: str, args: Dict[str, Any] = None, **kwargs):
        """Log function entry với parameters."""
        call_info = {
            "function": func_name,
            "module": module,
            "entry_time": time.time(),
            "args": args or {},
            "kwargs": kwargs
        }
        self.call_stack.append(call_info)
        
        logger.bind(
            session_id=self.session_id,
            stage=self.analysis_context.get("current_stage", "UNKNOWN"),
            log_type="debug"
        ).debug(f"➡️ ENTER {module}::{func_name}")
        
        logger.bind(
            call_type="ENTER",
            module=module,
            function_name=func_name,
            log_type="trace"
        ).trace(f"Args: {json.dumps(args or {}, default=str)}")
    
    def log_function_exit(self, func_name: str, module: str, result: Any = None, **kwargs):
        """Log function exit với return value."""
        # Find và remove from call stack
        for i, call_info in enumerate(reversed(self.call_stack)):
            if call_info["function"] == func_name and call_info["module"] == module:
                duration = time.time() - call_info["entry_time"]
                self.call_stack.pop(len(self.call_stack) - 1 - i)
                break
        else:
            duration = 0
        
        logger.bind(
            session_id=self.session_id,
            stage=self.analysis_context.get("current_stage", "UNKNOWN"),
            log_type="debug"
        ).debug(f"⬅️ EXIT {module}::{func_name} ({duration:.3f}s)")
        
        logger.bind(
            call_type="EXIT",
            module=module,
            function_name=func_name,
            log_type="trace"
        ).trace(f"Duration: {duration:.3f}s")
        
        # Log performance metric
        logger.bind(
            function_name=f"{module}::{func_name}",
            duration=duration,
            log_type="performance"
        ).info(f"Function performance: {duration:.3f}s")
    
    def log_step(self, step_name: str, details: Dict[str, Any] = None, **kwargs):
        """Log analysis step với details."""
        logger.bind(
            session_id=self.session_id,
            stage=self.analysis_context.get("current_stage", "UNKNOWN"),
            log_type="debug"
        ).info(f"📋 STEP: {step_name}")
        
        if details:
            logger.bind(
                session_id=self.session_id,
                stage=self.analysis_context.get("current_stage", "UNKNOWN"),
                log_type="debug"
            ).debug(f"Step details: {json.dumps(details, default=str, indent=2)}")
    
    def log_data(self, data_type: str, data: Dict[str, Any], **kwargs):
        """Log data structures cho debugging."""
        logger.bind(
            session_id=self.session_id,
            stage=self.analysis_context.get("current_stage", "UNKNOWN"),
            log_type="debug"
        ).debug(f"📊 DATA ({data_type}): {json.dumps(data, default=str, indent=2)}")
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None, **kwargs):
        """Log error với full stack trace và context."""
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
            "current_stage": self.analysis_context.get("current_stage"),
            "call_stack": [f"{call['module']}::{call['function']}" for call in self.call_stack]
        }
        
        self.analysis_context["errors"].append(error_info)
        
        stack_trace = traceback.format_exc()
        
        logger.bind(
            session_id=self.session_id,
            stack_trace=stack_trace,
            log_type="error"
        ).error(f"❌ ERROR: {type(error).__name__}: {str(error)}")
        
        logger.bind(
            session_id=self.session_id,
            stage=self.analysis_context.get("current_stage", "ERROR"),
            log_type="debug"
        ).error(f"Error context: {json.dumps(error_info, default=str, indent=2)}")
    
    def log_performance_metric(self, metric_name: str, value: Union[float, int], unit: str = "", **kwargs):
        """Log performance metric."""
        self.analysis_context["performance_metrics"][metric_name] = {
            "value": value,
            "unit": unit,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.bind(
            function_name=metric_name,
            duration=value,
            log_type="performance"
        ).info(f"Metric {metric_name}: {value} {unit}")
    
    def log_session_summary(self):
        """Log session summary khi kết thúc."""
        end_time = time.time()
        total_duration = end_time - self.start_time
        
        summary = {
            "session_id": self.session_id,
            "total_duration": total_duration,
            "stages_completed": self.analysis_context["stages_completed"],
            "current_stage": self.analysis_context["current_stage"],
            "repository_url": self.analysis_context["repository_url"],
            "error_count": len(self.analysis_context["errors"]),
            "performance_metrics": self.analysis_context["performance_metrics"],
            "end_time": datetime.now().isoformat()
        }
        
        logger.bind(
            session_id=self.session_id,
            stage="SUMMARY",
            log_type="debug"
        ).info(f"🏁 SESSION COMPLETED in {total_duration:.3f}s")
        
        logger.bind(
            session_id=self.session_id,
            stage="SUMMARY",
            log_type="debug"
        ).info(f"Session summary: {json.dumps(summary, default=str, indent=2)}")
        
        # Save summary to file
        summary_file = self.debug_dir / f"summary_{self.session_id}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, default=str, indent=2)


def debug_trace(func_or_stage=None):
    """
    Decorator để auto-log function calls.
    
    Can be used with or without parameters:
    
    @debug_trace
    def some_function():
        pass
        
    @debug_trace("DATA_ACQUISITION")
    def some_other_function():
        pass
    
    Args:
        func_or_stage: Either a function (when used without parentheses) 
                      or a stage string (when used with parentheses)
    """
    def decorator(func):
        """
        Inner decorator function for debug tracing.
        
        Args:
            func: Function to be decorated với debug tracing.
            
        Returns:
            Wrapped function với debug logging capabilities.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            Wrapper function that adds debug logging around function execution.
            
            Args:
                *args: Positional arguments passed to the wrapped function.
                **kwargs: Keyword arguments passed to the wrapped function.
                
            Returns:
                Result of the wrapped function execution.
                
            Raises:
                Exception: Re-raises any exception from wrapped function after logging.
            """
            # Get debug logger from args hoặc create new one
            debug_logger = None
            
            # Check if first arg có _debug_logger attribute (self trong method)
            if args and hasattr(args[0], '_debug_logger'):
                debug_logger = args[0]._debug_logger
            elif 'debug_logger' in kwargs:
                debug_logger = kwargs.pop('debug_logger')
            
            if not debug_logger:
                # Create temporary debug logger
                debug_logger = DebugLogger()
            
            # Set stage if provided
            stage = func_or_stage if isinstance(func_or_stage, str) else None
            if stage:
                debug_logger.set_analysis_stage(stage)
            
            module_name = func.__module__.split('.')[-1] if func.__module__ else "unknown"
            func_name = func.__name__
            
            # Prepare args for logging (avoid sensitive data)
            safe_args = {}
            if args:
                # For methods, skip self (first arg)
                start_index = 1 if args and hasattr(args[0], '__dict__') else 0
                for i, arg in enumerate(args[start_index:], 1):
                    if isinstance(arg, (str, int, float, bool, list, dict)):
                        safe_args[f"arg_{i}"] = arg
                    else:
                        safe_args[f"arg_{i}"] = str(type(arg))
            
            safe_kwargs = {k: v for k, v in kwargs.items() 
                          if isinstance(v, (str, int, float, bool, list, dict))}
            
            debug_logger.log_function_entry(func_name, module_name, safe_args, **safe_kwargs)
            
            try:
                result = func(*args, **kwargs)
                debug_logger.log_function_exit(func_name, module_name, result)
                return result
            except Exception as e:
                debug_logger.log_error(e, {"function": func_name, "module": module_name})
                raise
        
        return wrapper
    
    # If called without parentheses (func_or_stage is the actual function)
    if callable(func_or_stage):
        return decorator(func_or_stage)
    
    # If called with parentheses (func_or_stage is the stage string or None)
    return decorator


# Global debug logger instance
_global_debug_logger: Optional[DebugLogger] = None


def get_debug_logger() -> DebugLogger:
    """Get hoặc create global debug logger instance."""
    global _global_debug_logger
    if _global_debug_logger is None:
        _global_debug_logger = DebugLogger()
    return _global_debug_logger


def set_debug_logger(debug_logger: DebugLogger):
    """Set global debug logger instance."""
    global _global_debug_logger
    _global_debug_logger = debug_logger


def create_session_debug_logger(session_id: str) -> DebugLogger:
    """Create và set new debug logger cho specific session."""
    debug_logger = DebugLogger(session_id)
    set_debug_logger(debug_logger)
    return debug_logger


# Utility functions
def log_repository_analysis_start(repo_url: str, session_id: str = None) -> DebugLogger:
    """Utility để start repository analysis logging."""
    debug_logger = create_session_debug_logger(session_id or f"repo_analysis_{int(time.time())}")
    debug_logger.set_repository_context(repo_url)
    debug_logger.set_analysis_stage("REPOSITORY_ANALYSIS_START")
    return debug_logger


def log_repository_analysis_end():
    """Utility để end repository analysis logging."""
    debug_logger = get_debug_logger()
    debug_logger.set_analysis_stage("REPOSITORY_ANALYSIS_END")
    debug_logger.log_session_summary() 