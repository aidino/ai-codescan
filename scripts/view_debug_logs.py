#!/usr/bin/env python3
"""
Debug Log Viewer and Analyzer.

Utility script để view, filter, và analyze debug logs từ AI CodeScan.
Supports real-time monitoring, filtering by stage, và searching.
"""

import sys
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import re


class DebugLogViewer:
    """Debug log viewer và analyzer."""
    
    def __init__(self, logs_dir: str = "logs/debug"):
        """Initialize log viewer."""
        self.logs_dir = Path(logs_dir)
        if not self.logs_dir.exists():
            raise FileNotFoundError(f"Debug logs directory not found: {logs_dir}")
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all debug log sessions."""
        sessions = []
        
        # Find all debug log files
        debug_files = list(self.logs_dir.glob("debug_*.log"))
        
        for debug_file in debug_files:
            session_id = debug_file.stem.replace("debug_", "")
            
            # Get session info
            session_info = {
                "session_id": session_id,
                "debug_log": debug_file,
                "size_kb": debug_file.stat().st_size / 1024,
                "created": datetime.fromtimestamp(debug_file.stat().st_ctime)
            }
            
            # Check for related files
            summary_file = self.logs_dir / f"summary_{session_id}.json"
            if summary_file.exists():
                try:
                    with open(summary_file, 'r') as f:
                        summary = json.load(f)
                        session_info.update({
                            "repository_url": summary.get("repository_url"),
                            "total_duration": summary.get("total_duration"),
                            "stages_completed": summary.get("stages_completed"),
                            "error_count": summary.get("error_count", 0)
                        })
                except:
                    pass
            
            # Check for other log files
            perf_file = self.logs_dir / f"performance_{session_id}.log"
            error_file = self.logs_dir / f"errors_{session_id}.log"
            trace_file = self.logs_dir / f"trace_{session_id}.log"
            
            session_info.update({
                "has_performance_log": perf_file.exists(),
                "has_error_log": error_file.exists(),
                "has_trace_log": trace_file.exists()
            })
            
            sessions.append(session_info)
        
        return sorted(sessions, key=lambda x: x["created"], reverse=True)
    
    def view_session_logs(
        self, 
        session_id: str, 
        log_type: str = "debug",
        filter_stage: Optional[str] = None,
        search_term: Optional[str] = None,
        tail: int = 0
    ) -> List[str]:
        """View logs cho specific session."""
        
        # Map log types to file names
        log_files = {
            "debug": f"debug_{session_id}.log",
            "performance": f"performance_{session_id}.log", 
            "error": f"errors_{session_id}.log",
            "trace": f"trace_{session_id}.log"
        }
        
        if log_type not in log_files:
            raise ValueError(f"Invalid log type: {log_type}. Options: {list(log_files.keys())}")
        
        log_file = self.logs_dir / log_files[log_type]
        if not log_file.exists():
            raise FileNotFoundError(f"Log file not found: {log_file}")
        
        lines = []
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    # Apply stage filter
                    if filter_stage and f"STAGE:{filter_stage}" not in line:
                        continue
                    
                    # Apply search filter
                    if search_term and search_term.lower() not in line.lower():
                        continue
                    
                    lines.append(line.rstrip())
            
            # Apply tail if specified
            if tail > 0:
                lines = lines[-tail:]
                
        except Exception as e:
            raise Exception(f"Error reading log file: {e}")
        
        return lines
    
    def view_session_summary(self, session_id: str) -> Dict[str, Any]:
        """View session summary."""
        summary_file = self.logs_dir / f"summary_{session_id}.json"
        
        if not summary_file.exists():
            raise FileNotFoundError(f"Summary file not found: {summary_file}")
        
        try:
            with open(summary_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Error reading summary file: {e}")
    
    def search_logs(
        self, 
        search_term: str, 
        session_id: Optional[str] = None,
        log_type: str = "debug"
    ) -> List[Dict[str, Any]]:
        """Search across logs."""
        results = []
        
        if session_id:
            sessions = [{"session_id": session_id}]
        else:
            sessions = self.list_sessions()
        
        for session in sessions:
            sid = session["session_id"]
            try:
                lines = self.view_session_logs(sid, log_type, search_term=search_term)
                for i, line in enumerate(lines):
                    results.append({
                        "session_id": sid,
                        "line_number": i + 1,
                        "content": line,
                        "match": search_term in line.lower()
                    })
            except:
                continue  # Skip sessions without the requested log type
        
        return results
    
    def monitor_session(
        self, 
        session_id: str, 
        log_type: str = "debug",
        filter_stage: Optional[str] = None
    ):
        """Monitor session logs in real-time."""
        log_files = {
            "debug": f"debug_{session_id}.log",
            "performance": f"performance_{session_id}.log",
            "error": f"errors_{session_id}.log", 
            "trace": f"trace_{session_id}.log"
        }
        
        log_file = self.logs_dir / log_files[log_type]
        
        print(f"📡 Monitoring {log_file.name} (Ctrl+C to stop)")
        print(f"🔍 Filter stage: {filter_stage or 'All'}")
        print("=" * 80)
        
        # Keep track of file position
        file_pos = 0
        if log_file.exists():
            file_pos = log_file.stat().st_size
        
        try:
            while True:
                if log_file.exists():
                    current_size = log_file.stat().st_size
                    if current_size > file_pos:
                        # Read new content
                        with open(log_file, 'r', encoding='utf-8') as f:
                            f.seek(file_pos)
                            new_lines = f.readlines()
                            
                            for line in new_lines:
                                line = line.rstrip()
                                # Apply stage filter
                                if filter_stage and f"STAGE:{filter_stage}" not in line:
                                    continue
                                print(line)
                            
                            file_pos = current_size
                
                time.sleep(0.5)  # Check every 500ms
                
        except KeyboardInterrupt:
            print("\n⏹️ Monitoring stopped")


def print_sessions_table(sessions: List[Dict[str, Any]]):
    """Print sessions in table format."""
    if not sessions:
        print("❌ No debug sessions found")
        return
    
    print(f"📊 Found {len(sessions)} debug sessions:")
    print()
    print(f"{'Session ID':<25} {'Repository':<30} {'Duration':<10} {'Stages':<8} {'Errors':<7} {'Size':<8}")
    print("=" * 100)
    
    for session in sessions:
        session_id = session["session_id"][:24]
        repo = (session.get("repository_url", "Unknown") or "Unknown")
        if len(repo) > 29:
            repo = repo[:26] + "..."
        
        duration = session.get("total_duration")
        duration_str = f"{duration:.1f}s" if duration else "Unknown"
        
        stages = len(session.get("stages_completed", []))
        errors = session.get("error_count", 0)
        size = f"{session['size_kb']:.1f}KB"
        
        print(f"{session_id:<25} {repo:<30} {duration_str:<10} {stages:<8} {errors:<7} {size:<8}")


def print_session_detail(session_summary: Dict[str, Any]):
    """Print detailed session information."""
    print(f"📋 Session: {session_summary.get('session_id', 'Unknown')}")
    print("=" * 60)
    
    # Basic info
    print(f"🔗 Repository: {session_summary.get('repository_url', 'Unknown')}")
    print(f"⏱️  Duration: {session_summary.get('total_duration', 0):.2f} seconds")
    print(f"❌ Errors: {session_summary.get('error_count', 0)}")
    print(f"📅 Started: {session_summary.get('start_time', 'Unknown')}")
    print(f"🏁 Ended: {session_summary.get('end_time', 'Unknown')}")
    
    # Stages
    stages = session_summary.get('stages_completed', [])
    current_stage = session_summary.get('current_stage')
    if stages or current_stage:
        print(f"\n🔄 Stages:")
        for stage in stages:
            print(f"   ✅ {stage}")
        if current_stage and current_stage not in stages:
            print(f"   🔄 {current_stage} (current)")
    
    # Performance metrics
    metrics = session_summary.get('performance_metrics', {})
    if metrics:
        print(f"\n📊 Performance Metrics:")
        for metric, data in metrics.items():
            value = data.get('value', 0)
            unit = data.get('unit', '')
            print(f"   📈 {metric}: {value} {unit}")
    
    # Errors
    errors = session_summary.get('errors', [])
    if errors:
        print(f"\n❌ Errors ({len(errors)}):")
        for i, error in enumerate(errors[:5], 1):  # Show first 5 errors
            print(f"   {i}. {error.get('error_type', 'Unknown')}: {error.get('error_message', 'No message')}")
        if len(errors) > 5:
            print(f"   ... và {len(errors) - 5} errors khác")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="AI CodeScan Debug Log Viewer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all debug sessions
  python scripts/view_debug_logs.py list
  
  # View specific session logs
  python scripts/view_debug_logs.py view session_12345 --type debug
  
  # View session summary
  python scripts/view_debug_logs.py summary session_12345
  
  # Search for errors
  python scripts/view_debug_logs.py search "ERROR" --type error
  
  # Monitor session in real-time
  python scripts/view_debug_logs.py monitor session_12345 --stage DATA_ACQUISITION
  
  # View last 20 lines of a session
  python scripts/view_debug_logs.py view session_12345 --tail 20
        """
    )
    
    parser.add_argument("command", choices=["list", "view", "summary", "search", "monitor"],
                        help="Command to execute")
    parser.add_argument("session_id", nargs="?", help="Session ID for view/summary/monitor commands")
    parser.add_argument("search_term", nargs="?", help="Search term for search command")
    
    parser.add_argument("--type", default="debug", 
                        choices=["debug", "performance", "error", "trace"],
                        help="Log type to view (default: debug)")
    parser.add_argument("--stage", help="Filter by analysis stage")
    parser.add_argument("--tail", type=int, help="Show last N lines")
    parser.add_argument("--logs-dir", default="logs/debug", help="Debug logs directory")
    
    args = parser.parse_args()
    
    try:
        viewer = DebugLogViewer(args.logs_dir)
        
        if args.command == "list":
            sessions = viewer.list_sessions()
            print_sessions_table(sessions)
            
        elif args.command == "view":
            if not args.session_id:
                print("❌ Session ID required for view command")
                sys.exit(1)
            
            lines = viewer.view_session_logs(
                args.session_id, 
                args.type,
                filter_stage=args.stage,
                tail=args.tail or 0
            )
            
            print(f"📄 {args.type.title()} logs for session {args.session_id}:")
            if args.stage:
                print(f"🔍 Filtered by stage: {args.stage}")
            if args.tail:
                print(f"📋 Showing last {args.tail} lines")
            print("=" * 80)
            
            for line in lines:
                print(line)
            
        elif args.command == "summary":
            if not args.session_id:
                print("❌ Session ID required for summary command")
                sys.exit(1)
            
            summary = viewer.view_session_summary(args.session_id)
            print_session_detail(summary)
            
        elif args.command == "search":
            if not args.search_term:
                print("❌ Search term required for search command")
                sys.exit(1)
            
            results = viewer.search_logs(args.search_term, args.session_id, args.type)
            
            print(f"🔍 Search results for '{args.search_term}' in {args.type} logs:")
            print(f"Found {len(results)} matches")
            print("=" * 80)
            
            for result in results[:50]:  # Show first 50 results
                print(f"[{result['session_id']}:{result['line_number']}] {result['content']}")
            
            if len(results) > 50:
                print(f"\n... và {len(results) - 50} matches khác")
            
        elif args.command == "monitor":
            if not args.session_id:
                print("❌ Session ID required for monitor command")
                sys.exit(1)
            
            viewer.monitor_session(args.session_id, args.type, args.stage)
        
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 