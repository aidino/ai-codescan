#!/usr/bin/env python3
"""
AI CodeScan - Synthesis & Reporting Module

Module thực hiện synthesis và reporting của analysis results.
"""

from .finding_aggregator import (
    FindingAggregatorAgent,
    AggregatedFinding,
    AggregationResult,
    AggregationStrategy
)

from .report_generator import (
    ReportGeneratorAgent,
    ReportFormat,
    ReportMetadata,
    GeneratedReport
)

__all__ = [
    # Finding Aggregator
    'FindingAggregatorAgent',
    'AggregatedFinding',
    'AggregationResult',
    'AggregationStrategy',
    
    # Report Generator
    'ReportGeneratorAgent',
    'ReportFormat',
    'ReportMetadata',
    'GeneratedReport'
]
