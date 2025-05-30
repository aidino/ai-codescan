#!/usr/bin/env python3
"""
AI CodeScan - Finding Aggregator Agent

Agent tổng hợp findings từ multiple sources (static analysis, CKG analysis, etc.).
Thực hiện deduplication, prioritization và categorization.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from loguru import logger
from collections import defaultdict
from enum import Enum

from ..code_analysis import Finding, AnalysisResult, SeverityLevel, FindingType, ContextualFinding


class AggregationStrategy(Enum):
    """Strategies cho finding aggregation."""
    MERGE_DUPLICATES = "merge_duplicates"
    KEEP_ALL = "keep_all"
    PRIORITIZE_SEVERE = "prioritize_severe"
    GROUP_BY_FILE = "group_by_file"


@dataclass
class AggregatedFinding:
    """Finding đã được aggregate với additional metadata."""
    primary_finding: Finding
    related_findings: List[Finding]
    sources: List[str]  # Tools/sources that reported this finding
    confidence_score: float
    priority_score: float
    aggregation_reason: str
    file_context: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class AggregationResult:
    """Kết quả của finding aggregation."""
    original_findings_count: int
    aggregated_findings_count: int
    aggregated_findings: List[AggregatedFinding]
    deduplication_stats: Dict[str, int]
    aggregation_strategy: AggregationStrategy
    success: bool
    error_message: Optional[str] = None


class FindingAggregatorAgent:
    """
    Agent tổng hợp findings từ multiple sources.
    
    Trách nhiệm:
    - Deduplicate similar findings
    - Merge related findings
    - Calculate priority scores
    - Group findings by categories
    - Provide aggregation statistics
    """
    
    def __init__(self, 
                 deduplication_threshold: float = 0.8,
                 priority_weights: Optional[Dict[str, float]] = None):
        """
        Khởi tạo FindingAggregatorAgent.
        
        Args:
            deduplication_threshold: Threshold cho similarity detection (0-1)
            priority_weights: Weights cho priority calculation
        """
        self.deduplication_threshold = deduplication_threshold
        self.priority_weights = priority_weights or {
            "severity": 0.4,
            "frequency": 0.3,
            "tool_consensus": 0.2,
            "context_importance": 0.1
        }
    
    def aggregate_findings(self, 
                          findings_by_source: Dict[str, List[Finding]],
                          strategy: AggregationStrategy = AggregationStrategy.MERGE_DUPLICATES) -> AggregationResult:
        """
        Aggregate findings từ multiple sources.
        
        Args:
            findings_by_source: Dict source_name -> findings
            strategy: Aggregation strategy
            
        Returns:
            AggregationResult: Kết quả aggregation
        """
        try:
            logger.info(f"Aggregating findings từ {len(findings_by_source)} sources với strategy {strategy.value}")
            
            # Flatten all findings
            all_findings = []
            source_mapping = {}  # finding_id -> source
            
            for source, findings in findings_by_source.items():
                for finding in findings:
                    finding_id = id(finding)
                    all_findings.append(finding)
                    source_mapping[finding_id] = source
            
            original_count = len(all_findings)
            logger.info(f"Total findings to aggregate: {original_count}")
            
            if not all_findings:
                return AggregationResult(
                    original_findings_count=0,
                    aggregated_findings_count=0,
                    aggregated_findings=[],
                    deduplication_stats={},
                    aggregation_strategy=strategy,
                    success=True
                )
            
            # Apply aggregation strategy
            if strategy == AggregationStrategy.MERGE_DUPLICATES:
                aggregated = self._merge_duplicate_findings(all_findings, source_mapping)
            elif strategy == AggregationStrategy.KEEP_ALL:
                aggregated = self._keep_all_findings(all_findings, source_mapping)
            elif strategy == AggregationStrategy.PRIORITIZE_SEVERE:
                aggregated = self._prioritize_severe_findings(all_findings, source_mapping)
            elif strategy == AggregationStrategy.GROUP_BY_FILE:
                aggregated = self._group_by_file(all_findings, source_mapping)
            else:
                raise ValueError(f"Unknown aggregation strategy: {strategy}")
            
            # Calculate deduplication stats
            dedup_stats = self._calculate_deduplication_stats(original_count, len(aggregated))
            
            return AggregationResult(
                original_findings_count=original_count,
                aggregated_findings_count=len(aggregated),
                aggregated_findings=aggregated,
                deduplication_stats=dedup_stats,
                aggregation_strategy=strategy,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error aggregating findings: {str(e)}")
            return AggregationResult(
                original_findings_count=0,
                aggregated_findings_count=0,
                aggregated_findings=[],
                deduplication_stats={},
                aggregation_strategy=strategy,
                success=False,
                error_message=str(e)
            )
    
    def _merge_duplicate_findings(self, 
                                 findings: List[Finding], 
                                 source_mapping: Dict[int, str]) -> List[AggregatedFinding]:
        """
        Merge duplicate và similar findings.
        
        Args:
            findings: List of findings
            source_mapping: Finding ID to source mapping
            
        Returns:
            List[AggregatedFinding]: Merged findings
        """
        aggregated = []
        processed_ids = set()
        
        for i, finding in enumerate(findings):
            if id(finding) in processed_ids:
                continue
            
            # Find similar findings
            similar_findings = []
            similar_sources = set([source_mapping[id(finding)]])
            
            for j, other_finding in enumerate(findings[i+1:], i+1):
                if id(other_finding) in processed_ids:
                    continue
                    
                if self._are_findings_similar(finding, other_finding):
                    similar_findings.append(other_finding)
                    similar_sources.add(source_mapping[id(other_finding)])
                    processed_ids.add(id(other_finding))
            
            # Create aggregated finding
            confidence_score = self._calculate_confidence_score(finding, similar_findings, similar_sources)
            priority_score = self._calculate_priority_score(finding, similar_findings, similar_sources)
            
            aggregated_finding = AggregatedFinding(
                primary_finding=finding,
                related_findings=similar_findings,
                sources=list(similar_sources),
                confidence_score=confidence_score,
                priority_score=priority_score,
                aggregation_reason="merged_duplicates" if similar_findings else "unique_finding"
            )
            
            aggregated.append(aggregated_finding)
            processed_ids.add(id(finding))
        
        # Sort by priority score
        aggregated.sort(key=lambda x: x.priority_score, reverse=True)
        
        return aggregated
    
    def _keep_all_findings(self, 
                          findings: List[Finding], 
                          source_mapping: Dict[int, str]) -> List[AggregatedFinding]:
        """
        Keep all findings without merging.
        
        Args:
            findings: List of findings
            source_mapping: Finding ID to source mapping
            
        Returns:
            List[AggregatedFinding]: All findings as individual aggregated findings
        """
        aggregated = []
        
        for finding in findings:
            source = source_mapping[id(finding)]
            priority_score = self._calculate_priority_score(finding, [], {source})
            
            aggregated_finding = AggregatedFinding(
                primary_finding=finding,
                related_findings=[],
                sources=[source],
                confidence_score=1.0,  # Single source, full confidence
                priority_score=priority_score,
                aggregation_reason="keep_all_strategy"
            )
            
            aggregated.append(aggregated_finding)
        
        # Sort by priority score
        aggregated.sort(key=lambda x: x.priority_score, reverse=True)
        
        return aggregated
    
    def _prioritize_severe_findings(self, 
                                   findings: List[Finding], 
                                   source_mapping: Dict[int, str]) -> List[AggregatedFinding]:
        """
        Prioritize severe findings, filter out low-severity ones.
        
        Args:
            findings: List of findings
            source_mapping: Finding ID to source mapping
            
        Returns:
            List[AggregatedFinding]: High-priority findings only
        """
        # Filter severe findings
        severe_findings = [
            f for f in findings 
            if f.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]
        ]
        
        # If no severe findings, include medium severity
        if not severe_findings:
            severe_findings = [
                f for f in findings 
                if f.severity == SeverityLevel.MEDIUM
            ]
        
        # Convert to aggregated findings
        aggregated = []
        for finding in severe_findings:
            source = source_mapping[id(finding)]
            priority_score = self._calculate_priority_score(finding, [], {source})
            
            aggregated_finding = AggregatedFinding(
                primary_finding=finding,
                related_findings=[],
                sources=[source],
                confidence_score=1.0,
                priority_score=priority_score,
                aggregation_reason="severity_prioritized"
            )
            
            aggregated.append(aggregated_finding)
        
        # Sort by severity then priority
        severity_order = {
            SeverityLevel.CRITICAL: 4,
            SeverityLevel.HIGH: 3,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.LOW: 1
        }
        
        aggregated.sort(
            key=lambda x: (severity_order[x.primary_finding.severity], x.priority_score),
            reverse=True
        )
        
        return aggregated
    
    def _group_by_file(self, 
                      findings: List[Finding], 
                      source_mapping: Dict[int, str]) -> List[AggregatedFinding]:
        """
        Group findings by file path.
        
        Args:
            findings: List of findings
            source_mapping: Finding ID to source mapping
            
        Returns:
            List[AggregatedFinding]: Findings grouped by file
        """
        file_groups = defaultdict(list)
        
        # Group by file
        for finding in findings:
            file_groups[finding.file_path].append(finding)
        
        aggregated = []
        
        for file_path, file_findings in file_groups.items():
            # Sort findings within file by severity và line number
            file_findings.sort(
                key=lambda f: (f.severity.value, f.line_number),
                reverse=True
            )
            
            # Use most severe finding as primary
            primary_finding = file_findings[0]
            related_findings = file_findings[1:] if len(file_findings) > 1 else []
            
            # Collect sources
            sources = list(set(source_mapping[id(f)] for f in file_findings))
            
            # Calculate scores
            confidence_score = self._calculate_confidence_score(primary_finding, related_findings, sources)
            priority_score = self._calculate_priority_score(primary_finding, related_findings, sources)
            
            aggregated_finding = AggregatedFinding(
                primary_finding=primary_finding,
                related_findings=related_findings,
                sources=sources,
                confidence_score=confidence_score,
                priority_score=priority_score,
                aggregation_reason=f"grouped_by_file_{len(file_findings)}_findings",
                file_context={"file_path": file_path, "findings_count": len(file_findings)}
            )
            
            aggregated.append(aggregated_finding)
        
        # Sort by number of findings per file, then priority
        aggregated.sort(
            key=lambda x: (len(x.related_findings) + 1, x.priority_score),
            reverse=True
        )
        
        return aggregated
    
    def _are_findings_similar(self, finding1: Finding, finding2: Finding) -> bool:
        """
        Kiểm tra 2 findings có similar không.
        
        Args:
            finding1: Finding thứ nhất
            finding2: Finding thứ hai
            
        Returns:
            bool: True nếu similar
        """
        # Same file và close line numbers
        if (finding1.file_path == finding2.file_path and
            abs(finding1.line_number - finding2.line_number) <= 3):
            
            # Same rule or similar message
            if (finding1.rule_id == finding2.rule_id or
                self._calculate_message_similarity(finding1.message, finding2.message) >= self.deduplication_threshold):
                return True
        
        # Same rule across different files (pattern issue)
        if (finding1.rule_id == finding2.rule_id and
            finding1.rule_id != "" and
            self._calculate_message_similarity(finding1.message, finding2.message) >= 0.9):
            return True
        
        return False
    
    def _calculate_message_similarity(self, message1: str, message2: str) -> float:
        """
        Calculate similarity giữa 2 messages.
        
        Args:
            message1: Message 1
            message2: Message 2
            
        Returns:
            float: Similarity score (0-1)
        """
        # Simple similarity based on common words
        words1 = set(message1.lower().split())
        words2 = set(message2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_confidence_score(self, 
                                   primary_finding: Finding, 
                                   related_findings: List[Finding], 
                                   sources: Set[str]) -> float:
        """
        Calculate confidence score based on consensus.
        
        Args:
            primary_finding: Primary finding
            related_findings: Related findings
            sources: Sources that reported this
            
        Returns:
            float: Confidence score (0-1)
        """
        base_confidence = 0.5
        
        # Boost confidence with multiple sources
        source_boost = min(len(sources) * 0.2, 0.4)
        
        # Boost confidence with multiple related findings
        related_boost = min(len(related_findings) * 0.1, 0.3)
        
        # Boost confidence for error types
        severity_boost = 0.0
        if primary_finding.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]:
            severity_boost = 0.2
        elif primary_finding.severity == SeverityLevel.MEDIUM:
            severity_boost = 0.1
        
        total_confidence = base_confidence + source_boost + related_boost + severity_boost
        return min(total_confidence, 1.0)
    
    def _calculate_priority_score(self, 
                                 primary_finding: Finding, 
                                 related_findings: List[Finding], 
                                 sources: Set[str]) -> float:
        """
        Calculate priority score cho finding.
        
        Args:
            primary_finding: Primary finding
            related_findings: Related findings
            sources: Sources that reported this
            
        Returns:
            float: Priority score (0-1)
        """
        weights = self.priority_weights
        
        # Severity component
        severity_scores = {
            SeverityLevel.CRITICAL: 1.0,
            SeverityLevel.HIGH: 0.8,
            SeverityLevel.MEDIUM: 0.5,
            SeverityLevel.LOW: 0.2
        }
        severity_component = severity_scores.get(primary_finding.severity, 0.5)
        
        # Frequency component (how many related findings)
        frequency_component = min((len(related_findings) + 1) / 5.0, 1.0)
        
        # Tool consensus component (how many sources agree)
        consensus_component = min(len(sources) / 3.0, 1.0)
        
        # Context importance (simplified - could be enhanced)
        context_component = 0.5  # Default value
        if primary_finding.finding_type == FindingType.ERROR:
            context_component = 1.0
        elif primary_finding.finding_type == FindingType.SECURITY:
            context_component = 0.9
        elif primary_finding.finding_type == FindingType.PERFORMANCE:
            context_component = 0.7
        
        # Weighted sum
        priority_score = (
            severity_component * weights["severity"] +
            frequency_component * weights["frequency"] +
            consensus_component * weights["tool_consensus"] +
            context_component * weights["context_importance"]
        )
        
        return round(priority_score, 3)
    
    def _calculate_deduplication_stats(self, original_count: int, aggregated_count: int) -> Dict[str, int]:
        """Calculate deduplication statistics."""
        duplicates_removed = original_count - aggregated_count
        reduction_percentage = int((duplicates_removed / original_count) * 100) if original_count > 0 else 0
        
        return {
            "original_count": original_count,
            "aggregated_count": aggregated_count,
            "duplicates_removed": duplicates_removed,
            "reduction_percentage": reduction_percentage
        }
    
    def get_aggregation_summary(self, result: AggregationResult) -> Dict[str, Any]:
        """
        Generate summary của aggregation result.
        
        Args:
            result: Aggregation result
            
        Returns:
            Dict với summary information
        """
        if not result.success:
            return {"error": result.error_message}
        
        # Calculate statistics
        severity_breakdown = defaultdict(int)
        type_breakdown = defaultdict(int)
        source_breakdown = defaultdict(int)
        file_breakdown = defaultdict(int)
        
        high_priority_count = 0
        avg_confidence = 0.0
        
        for finding in result.aggregated_findings:
            # Severity
            severity_breakdown[finding.primary_finding.severity.value] += 1
            
            # Type
            type_breakdown[finding.primary_finding.finding_type.value] += 1
            
            # Sources
            for source in finding.sources:
                source_breakdown[source] += 1
            
            # Files
            file_breakdown[finding.primary_finding.file_path] += 1
            
            # Priority
            if finding.priority_score >= 0.7:
                high_priority_count += 1
            
            # Confidence
            avg_confidence += finding.confidence_score
        
        if result.aggregated_findings:
            avg_confidence /= len(result.aggregated_findings)
        
        # Top problematic files
        top_files = sorted(file_breakdown.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "aggregation_strategy": result.aggregation_strategy.value,
            "deduplication": result.deduplication_stats,
            "summary": {
                "total_aggregated_findings": result.aggregated_findings_count,
                "high_priority_findings": high_priority_count,
                "average_confidence": round(avg_confidence, 2)
            },
            "breakdowns": {
                "severity": dict(severity_breakdown),
                "type": dict(type_breakdown),
                "source": dict(source_breakdown)
            },
            "top_problematic_files": top_files
        } 