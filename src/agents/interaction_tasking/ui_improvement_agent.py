#!/usr/bin/env python3
"""
UI Improvement Agent for Web Interface Enhancement

This module analyzes user feedback and implements UI/UX improvements
to enhance user experience and interface usability.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import json
from pathlib import Path
from loguru import logger

from .feedback_collector import (
    FeedbackCollectorAgent, 
    UserFeedback, 
    FeedbackAnalytics,
    FeedbackType,
    FeatureArea,
    SatisfactionLevel
)


class ImprovementPriority(Enum):
    """Priority levels for UI improvements."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ImprovementStatus(Enum):
    """Status of improvement implementation."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    TESTED = "tested"
    DEPLOYED = "deployed"
    CANCELLED = "cancelled"


class ImprovementCategory(Enum):
    """Categories of UI improvements."""
    LAYOUT = "layout"
    NAVIGATION = "navigation"
    VISUAL_DESIGN = "visual_design"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"
    USABILITY = "usability"
    RESPONSIVENESS = "responsiveness"
    FEEDBACK_INTEGRATION = "feedback_integration"


@dataclass
class UIImprovement:
    """Structure for UI improvement recommendations."""
    improvement_id: str
    title: str
    description: str
    category: ImprovementCategory
    priority: ImprovementPriority
    feature_area: FeatureArea
    related_feedback_ids: List[str]
    estimated_effort: str  # "Small", "Medium", "Large"
    expected_impact: str   # "Low", "Medium", "High"
    implementation_notes: str
    status: ImprovementStatus
    created_at: datetime
    updated_at: datetime
    implemented_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert improvement to dictionary for storage."""
        data = asdict(self)
        data['category'] = self.category.value
        data['priority'] = self.priority.value
        data['feature_area'] = self.feature_area.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.implemented_at:
            data['implemented_at'] = self.implemented_at.isoformat()
        return data


@dataclass
class ImprovementPlan:
    """Plan for implementing UI improvements."""
    plan_id: str
    title: str
    description: str
    improvements: List[UIImprovement]
    total_estimated_effort: str
    expected_completion: datetime
    created_at: datetime
    status: str


class UIImprovementAgent:
    """Agent responsible for analyzing feedback and implementing UI improvements."""
    
    def __init__(self, feedback_collector: FeedbackCollectorAgent, storage_path: str = "logs/ui_improvements"):
        """
        Initialize UI Improvement Agent.
        
        Args:
            feedback_collector: FeedbackCollectorAgent instance
            storage_path: Path to store improvement data
        """
        self.feedback_collector = feedback_collector
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.improvements_file = self.storage_path / "ui_improvements.jsonl"
        self.plans_file = self.storage_path / "improvement_plans.json"
        
        logger.info(f"UIImprovementAgent initialized with storage at {self.storage_path}")
    
    def analyze_feedback_for_improvements(self) -> List[UIImprovement]:
        """
        Analyze collected feedback to generate UI improvement recommendations.
        
        Returns:
            List[UIImprovement]: List of recommended improvements
        """
        improvements = []
        
        try:
            # Get feedback analytics
            analytics = self.feedback_collector.get_feedback_summary()
            critical_issues = self.feedback_collector.get_critical_issues()
            
            # Analyze common issues and generate improvements
            improvements.extend(self._analyze_satisfaction_issues(analytics))
            improvements.extend(self._analyze_feature_area_issues(analytics))
            improvements.extend(self._analyze_critical_issues(critical_issues))
            improvements.extend(self._generate_proactive_improvements(analytics))
            
            # Store improvements
            for improvement in improvements:
                self._save_improvement(improvement)
            
            logger.info(f"Generated {len(improvements)} UI improvement recommendations")
            return improvements
            
        except Exception as e:
            logger.error(f"Failed to analyze feedback for improvements: {e}")
            return []
    
    def get_improvement_roadmap(self, priority_filter: Optional[ImprovementPriority] = None) -> List[UIImprovement]:
        """
        Get UI improvement roadmap prioritized by impact and effort.
        
        Args:
            priority_filter: Filter by specific priority level
            
        Returns:
            List[UIImprovement]: Prioritized list of improvements
        """
        try:
            improvements = self._load_improvements()
            
            if priority_filter:
                improvements = [imp for imp in improvements if imp.priority == priority_filter]
            
            # Sort by priority (descending) and creation date
            improvements.sort(key=lambda x: (x.priority.value, x.created_at), reverse=True)
            
            return improvements
            
        except Exception as e:
            logger.error(f"Failed to get improvement roadmap: {e}")
            return []
    
    def implement_improvement(self, improvement_id: str, implementation_notes: str = "") -> bool:
        """
        Mark improvement as implemented.
        
        Args:
            improvement_id: ID of the improvement
            implementation_notes: Notes about implementation
            
        Returns:
            bool: True if successfully updated
        """
        try:
            improvements = self._load_improvements()
            
            for improvement in improvements:
                if improvement.improvement_id == improvement_id:
                    improvement.status = ImprovementStatus.IMPLEMENTED
                    improvement.implemented_at = datetime.now()
                    improvement.updated_at = datetime.now()
                    if implementation_notes:
                        improvement.implementation_notes += f"\n\nImplementation: {implementation_notes}"
                    
                    self._save_improvement(improvement)
                    logger.info(f"Improvement {improvement_id} marked as implemented")
                    return True
            
            logger.warning(f"Improvement {improvement_id} not found")
            return False
            
        except Exception as e:
            logger.error(f"Failed to implement improvement: {e}")
            return False
    
    def create_improvement_plan(self, title: str, improvement_ids: List[str]) -> ImprovementPlan:
        """
        Create an improvement plan with selected improvements.
        
        Args:
            title: Title for the improvement plan
            improvement_ids: List of improvement IDs to include
            
        Returns:
            ImprovementPlan: Created improvement plan
        """
        try:
            improvements = self._load_improvements()
            selected_improvements = [
                imp for imp in improvements 
                if imp.improvement_id in improvement_ids
            ]
            
            # Calculate total effort and expected completion
            effort_mapping = {"Small": 1, "Medium": 3, "Large": 8}
            total_effort = sum(effort_mapping.get(imp.estimated_effort, 3) for imp in selected_improvements)
            
            # Estimate completion (assuming 1 effort point = 1 day)
            from datetime import timedelta
            expected_completion = datetime.now() + timedelta(days=total_effort)
            
            plan = ImprovementPlan(
                plan_id=self._generate_plan_id(),
                title=title,
                description=f"Implementation plan with {len(selected_improvements)} improvements",
                improvements=selected_improvements,
                total_estimated_effort=f"{total_effort} days",
                expected_completion=expected_completion,
                created_at=datetime.now(),
                status="active"
            )
            
            self._save_plan(plan)
            logger.info(f"Created improvement plan: {plan.plan_id}")
            return plan
            
        except Exception as e:
            logger.error(f"Failed to create improvement plan: {e}")
            raise
    
    def get_improvement_stats(self) -> Dict[str, Any]:
        """
        Get statistics about UI improvements.
        
        Returns:
            Dict[str, Any]: Improvement statistics
        """
        try:
            improvements = self._load_improvements()
            
            if not improvements:
                return {
                    "total_improvements": 0,
                    "by_priority": {},
                    "by_category": {},
                    "by_status": {},
                    "implementation_rate": 0.0
                }
            
            stats = {
                "total_improvements": len(improvements),
                "by_priority": {},
                "by_category": {},
                "by_status": {},
                "by_feature_area": {}
            }
            
            # Count by priority
            for priority in ImprovementPriority:
                stats["by_priority"][priority.name] = sum(
                    1 for imp in improvements if imp.priority == priority
                )
            
            # Count by category
            for category in ImprovementCategory:
                stats["by_category"][category.name] = sum(
                    1 for imp in improvements if imp.category == category
                )
            
            # Count by status
            for status in ImprovementStatus:
                stats["by_status"][status.name] = sum(
                    1 for imp in improvements if imp.status == status
                )
            
            # Count by feature area
            for area in FeatureArea:
                stats["by_feature_area"][area.name] = sum(
                    1 for imp in improvements if imp.feature_area == area
                )
            
            # Implementation rate
            implemented_count = sum(
                1 for imp in improvements 
                if imp.status in [ImprovementStatus.IMPLEMENTED, ImprovementStatus.DEPLOYED]
            )
            stats["implementation_rate"] = (implemented_count / len(improvements)) * 100
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get improvement stats: {e}")
            return {}
    
    def _analyze_satisfaction_issues(self, analytics: FeedbackAnalytics) -> List[UIImprovement]:
        """Analyze satisfaction levels and generate improvements."""
        improvements = []
        
        # Low satisfaction indicates UI issues
        dissatisfied_count = (
            analytics.satisfaction_distribution.get("VERY_DISSATISFIED", 0) +
            analytics.satisfaction_distribution.get("DISSATISFIED", 0)
        )
        
        if dissatisfied_count > 0:
            improvements.append(UIImprovement(
                improvement_id=self._generate_improvement_id(),
                title="Improve Overall User Satisfaction",
                description=f"Address low satisfaction with {dissatisfied_count} dissatisfied users",
                category=ImprovementCategory.USABILITY,
                priority=ImprovementPriority.HIGH,
                feature_area=FeatureArea.WEB_INTERFACE,
                related_feedback_ids=[],
                estimated_effort="Medium",
                expected_impact="High",
                implementation_notes="Focus on usability testing and interface simplification",
                status=ImprovementStatus.PLANNED,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ))
        
        return improvements
    
    def _analyze_feature_area_issues(self, analytics: FeedbackAnalytics) -> List[UIImprovement]:
        """Analyze feature area feedback and generate improvements."""
        improvements = []
        
        # Areas with high feedback volume may need attention
        for area_name, count in analytics.feature_area_distribution.items():
            if count >= 5:  # Threshold for high feedback volume
                try:
                    feature_area = FeatureArea[area_name]
                    improvements.append(UIImprovement(
                        improvement_id=self._generate_improvement_id(),
                        title=f"Enhance {area_name.replace('_', ' ').title()} Interface",
                        description=f"High feedback volume ({count} items) indicates need for improvement",
                        category=ImprovementCategory.USABILITY,
                        priority=ImprovementPriority.MEDIUM,
                        feature_area=feature_area,
                        related_feedback_ids=[],
                        estimated_effort="Medium",
                        expected_impact="Medium",
                        implementation_notes=f"Review {area_name} interface based on user feedback",
                        status=ImprovementStatus.PLANNED,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    ))
                except KeyError:
                    continue
        
        return improvements
    
    def _analyze_critical_issues(self, critical_issues: List[UserFeedback]) -> List[UIImprovement]:
        """Analyze critical issues and generate improvements."""
        improvements = []
        
        for issue in critical_issues[:3]:  # Top 3 critical issues
            category = ImprovementCategory.USABILITY
            if issue.feedback_type == FeedbackType.BUG_REPORT:
                category = ImprovementCategory.PERFORMANCE
            elif issue.feedback_type == FeedbackType.UI_IMPROVEMENT:
                category = ImprovementCategory.VISUAL_DESIGN
            
            improvements.append(UIImprovement(
                improvement_id=self._generate_improvement_id(),
                title=f"Fix Critical Issue: {issue.title}",
                description=issue.description,
                category=category,
                priority=ImprovementPriority.CRITICAL,
                feature_area=issue.feature_area,
                related_feedback_ids=[issue.feedback_id],
                estimated_effort="Small" if issue.feedback_type == FeedbackType.UI_IMPROVEMENT else "Medium",
                expected_impact="High",
                implementation_notes=f"Based on critical feedback: {issue.suggestions}",
                status=ImprovementStatus.PLANNED,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ))
        
        return improvements
    
    def _generate_proactive_improvements(self, analytics: FeedbackAnalytics) -> List[UIImprovement]:
        """Generate proactive improvements based on trends."""
        improvements = []
        
        # If average rating is below 4, suggest general improvements
        if analytics.average_rating < 4.0:
            improvements.extend([
                UIImprovement(
                    improvement_id=self._generate_improvement_id(),
                    title="Enhance Visual Design",
                    description="Improve overall visual appeal and modern design elements",
                    category=ImprovementCategory.VISUAL_DESIGN,
                    priority=ImprovementPriority.MEDIUM,
                    feature_area=FeatureArea.WEB_INTERFACE,
                    related_feedback_ids=[],
                    estimated_effort="Large",
                    expected_impact="High",
                    implementation_notes="Update color scheme, typography, and layout patterns",
                    status=ImprovementStatus.PLANNED,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                ),
                UIImprovement(
                    improvement_id=self._generate_improvement_id(),
                    title="Improve Navigation Flow",
                    description="Streamline navigation and reduce cognitive load",
                    category=ImprovementCategory.NAVIGATION,
                    priority=ImprovementPriority.MEDIUM,
                    feature_area=FeatureArea.WEB_INTERFACE,
                    related_feedback_ids=[],
                    estimated_effort="Medium",
                    expected_impact="Medium",
                    implementation_notes="Simplify menu structure and add breadcrumbs",
                    status=ImprovementStatus.PLANNED,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            ])
        
        return improvements
    
    def _save_improvement(self, improvement: UIImprovement) -> None:
        """Save improvement to storage."""
        try:
            with open(self.improvements_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(improvement.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to save improvement: {e}")
    
    def _load_improvements(self) -> List[UIImprovement]:
        """Load improvements from storage."""
        improvements = []
        
        if not self.improvements_file.exists():
            return improvements
        
        try:
            with open(self.improvements_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        
                        improvement = UIImprovement(
                            improvement_id=data['improvement_id'],
                            title=data['title'],
                            description=data['description'],
                            category=ImprovementCategory(data['category']),
                            priority=ImprovementPriority(data['priority']),
                            feature_area=FeatureArea(data['feature_area']),
                            related_feedback_ids=data['related_feedback_ids'],
                            estimated_effort=data['estimated_effort'],
                            expected_impact=data['expected_impact'],
                            implementation_notes=data['implementation_notes'],
                            status=ImprovementStatus(data['status']),
                            created_at=datetime.fromisoformat(data['created_at']),
                            updated_at=datetime.fromisoformat(data['updated_at']),
                            implemented_at=datetime.fromisoformat(data['implemented_at']) if data.get('implemented_at') else None
                        )
                        improvements.append(improvement)
                        
        except Exception as e:
            logger.error(f"Failed to load improvements: {e}")
        
        return improvements
    
    def _save_plan(self, plan: ImprovementPlan) -> None:
        """Save improvement plan to storage."""
        try:
            plans = []
            if self.plans_file.exists():
                with open(self.plans_file, 'r', encoding='utf-8') as f:
                    plans = json.load(f)
            
            plan_data = asdict(plan)
            plan_data['created_at'] = plan.created_at.isoformat()
            plan_data['expected_completion'] = plan.expected_completion.isoformat()
            
            plans.append(plan_data)
            
            with open(self.plans_file, 'w', encoding='utf-8') as f:
                json.dump(plans, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to save plan: {e}")
    
    def _generate_improvement_id(self) -> str:
        """Generate unique improvement ID."""
        import uuid
        return f"ui_imp_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
    
    def _generate_plan_id(self) -> str:
        """Generate unique plan ID."""
        import uuid
        return f"plan_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"


def create_ui_improvement_agent(feedback_collector: FeedbackCollectorAgent, 
                               storage_path: str = "logs/ui_improvements") -> UIImprovementAgent:
    """
    Factory function to create UIImprovementAgent.
    
    Args:
        feedback_collector: FeedbackCollectorAgent instance
        storage_path: Path to store improvement data
        
    Returns:
        UIImprovementAgent: Configured UI improvement agent
    """
    return UIImprovementAgent(feedback_collector, storage_path) 