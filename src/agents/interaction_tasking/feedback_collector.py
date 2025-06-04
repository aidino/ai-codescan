#!/usr/bin/env python3
"""
Feedback Collector Agent for Interaction & Tasking Team.

Handles collecting and processing user feedback for UX improvements.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of feedback."""
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    UI_ISSUE = "ui_issue"
    PERFORMANCE = "performance"
    GENERAL = "general"


class SatisfactionLevel(Enum):
    """User satisfaction levels."""
    VERY_DISSATISFIED = "very_dissatisfied"
    DISSATISFIED = "dissatisfied"
    NEUTRAL = "neutral"
    SATISFIED = "satisfied"
    VERY_SATISFIED = "very_satisfied"


class FeatureArea(Enum):
    """Feature areas for feedback categorization."""
    REPOSITORY_ANALYSIS = "repository_analysis"
    CODE_DIAGRAMS = "code_diagrams"
    PR_REVIEW = "pr_review"
    CODE_QNA = "code_qna"
    WEB_INTERFACE = "web_interface"
    AUTHENTICATION = "authentication"
    REPORTING = "reporting"
    MULTI_LANGUAGE_SUPPORT = "multi_language_support"


@dataclass
class FeedbackEntry:
    """Single feedback entry."""
    feedback_id: str
    feedback_type: FeedbackType
    title: str
    description: str
    user_id: Optional[str]
    timestamp: datetime
    severity: str  # low, medium, high, critical
    category: str
    status: str = "open"  # open, in_progress, resolved, closed
    metadata: Dict[str, Any] = None


# Alias for backward compatibility
UserFeedback = FeedbackEntry


class FeedbackCollectorAgent:
    """Agent responsible for collecting và managing user feedback."""
    
    def __init__(self):
        """Initialize Feedback Collector Agent."""
        self.feedback_types = {
            'bug_report': FeedbackType.BUG_REPORT,
            'feature_request': FeedbackType.FEATURE_REQUEST,
            'ui_issue': FeedbackType.UI_ISSUE,
            'performance': FeedbackType.PERFORMANCE,
            'general': FeedbackType.GENERAL
        }
        
        self.feedback_storage: List[FeedbackEntry] = []
        
        logger.info("FeedbackCollectorAgent initialized")
    
    def collect_feedback(self,
                        feedback_type: str,
                        title: str,
                        description: str,
                        severity: str = "medium",
                        user_id: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Collect user feedback.
        
        Args:
            feedback_type: Type of feedback
            title: Feedback title
            description: Detailed description
            severity: Severity level
            user_id: Optional user identifier
            metadata: Additional metadata
            
        Returns:
            Feedback ID
        """
        feedback_id = f"feedback_{int(datetime.now().timestamp())}"
        
        entry = FeedbackEntry(
            feedback_id=feedback_id,
            feedback_type=self.feedback_types.get(feedback_type, FeedbackType.GENERAL),
            title=title,
            description=description,
            user_id=user_id,
            timestamp=datetime.now(),
            severity=severity,
            category=feedback_type,
            metadata=metadata or {}
        )
        
        self.feedback_storage.append(entry)
        
        logger.info(f"Feedback collected: {feedback_id} - {title}")
        return feedback_id
    
    def get_feedback_statistics(self) -> Dict[str, Any]:
        """Get feedback statistics."""
        if not self.feedback_storage:
            return {"total": 0, "by_type": {}, "by_severity": {}}
        
        stats = {
            "total": len(self.feedback_storage),
            "by_type": {},
            "by_severity": {},
            "by_status": {}
        }
        
        for entry in self.feedback_storage:
            # By type
            type_key = entry.feedback_type.value
            stats["by_type"][type_key] = stats["by_type"].get(type_key, 0) + 1
            
            # By severity
            stats["by_severity"][entry.severity] = stats["by_severity"].get(entry.severity, 0) + 1
            
            # By status
            stats["by_status"][entry.status] = stats["by_status"].get(entry.status, 0) + 1
        
        return stats
    
    def get_recent_feedback(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent feedback entries."""
        recent = sorted(self.feedback_storage, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        return [
            {
                "id": entry.feedback_id,
                "type": entry.feedback_type.value,
                "title": entry.title,
                "description": entry.description,
                "severity": entry.severity,
                "status": entry.status,
                "timestamp": entry.timestamp.isoformat()
            }
            for entry in recent
        ]
    
    def mark_feedback_resolved(self, feedback_id: str) -> bool:
        """Mark feedback as resolved."""
        for entry in self.feedback_storage:
            if entry.feedback_id == feedback_id:
                entry.status = "resolved"
                logger.info(f"Feedback {feedback_id} marked as resolved")
                return True
        return False
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get comprehensive feedback summary for analysis."""
        return self.get_feedback_statistics()
    
    def get_critical_issues(self) -> List[Dict[str, Any]]:
        """Get critical and high-severity feedback entries."""
        critical_issues = []
        for entry in self.feedback_storage:
            if entry.severity in ['critical', 'high']:
                critical_issues.append({
                    "id": entry.feedback_id,
                    "type": entry.feedback_type.value,
                    "title": entry.title,
                    "description": entry.description,
                    "severity": entry.severity,
                    "status": entry.status,
                    "timestamp": entry.timestamp.isoformat()
                })
        return critical_issues


class UIImprovementAgent:
    """Agent for analyzing feedback và suggesting UI improvements."""
    
    def __init__(self):
        """Initialize UI Improvement Agent."""
        self.improvement_suggestions: List[Dict[str, Any]] = []
        logger.info("UIImprovementAgent initialized")
    
    def analyze_feedback_patterns(self, feedback_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze feedback patterns và generate improvement suggestions.
        
        Args:
            feedback_list: List of feedback entries
            
        Returns:
            Analysis results with improvement suggestions
        """
        if not feedback_list:
            return {"patterns": [], "suggestions": []}
        
        # Count by type and severity
        type_counts = {}
        severity_counts = {}
        common_issues = {}
        
        for feedback in feedback_list:
            fb_type = feedback.get('type', 'general')
            severity = feedback.get('severity', 'medium')
            title = feedback.get('title', '')
            
            type_counts[fb_type] = type_counts.get(fb_type, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Look for common keywords in titles
            words = title.lower().split()
            for word in words:
                if len(word) > 3:  # Filter short words
                    common_issues[word] = common_issues.get(word, 0) + 1
        
        # Generate patterns
        patterns = []
        if type_counts:
            most_common_type = max(type_counts, key=type_counts.get)
            patterns.append(f"Most common feedback type: {most_common_type} ({type_counts[most_common_type]} issues)")
        
        if severity_counts:
            high_severity = severity_counts.get('high', 0) + severity_counts.get('critical', 0)
            if high_severity > 0:
                patterns.append(f"High/Critical severity issues: {high_severity}")
        
        # Generate suggestions
        suggestions = self._generate_improvement_suggestions(type_counts, severity_counts, common_issues)
        
        return {
            "patterns": patterns,
            "suggestions": suggestions,
            "type_distribution": type_counts,
            "severity_distribution": severity_counts,
            "common_keywords": dict(sorted(common_issues.items(), key=lambda x: x[1], reverse=True)[:5])
        }
    
    def _generate_improvement_suggestions(self, 
                                        type_counts: Dict[str, int],
                                        severity_counts: Dict[str, int],
                                        common_issues: Dict[str, int]) -> List[str]:
        """Generate specific improvement suggestions based on feedback patterns."""
        suggestions = []
        
        # Suggestions based on feedback types
        if type_counts.get('ui_issue', 0) > 2:
            suggestions.append("Consider UI/UX review - multiple UI issues reported")
        
        if type_counts.get('performance', 0) > 1:
            suggestions.append("Performance optimization needed - slow response times reported")
        
        if type_counts.get('bug_report', 0) > 3:
            suggestions.append("Increase testing coverage - multiple bugs reported")
        
        # Suggestions based on severity
        critical_count = severity_counts.get('critical', 0)
        if critical_count > 0:
            suggestions.append(f"Address {critical_count} critical issues immediately")
        
        high_count = severity_counts.get('high', 0)
        if high_count > 2:
            suggestions.append(f"Prioritize {high_count} high-severity issues")
        
        # Suggestions based on common keywords
        if 'slow' in common_issues or 'loading' in common_issues:
            suggestions.append("Investigate loading performance issues")
        
        if 'confusing' in common_issues or 'unclear' in common_issues:
            suggestions.append("Improve user interface clarity and documentation")
        
        if 'error' in common_issues:
            suggestions.append("Enhance error handling and user-friendly error messages")
        
        return suggestions


def create_feedback_collector() -> FeedbackCollectorAgent:
    """Factory function to create FeedbackCollectorAgent instance."""
    return FeedbackCollectorAgent() 