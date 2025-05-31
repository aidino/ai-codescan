"""
Pull Request Analyzer Agent for AI CodeScan.

This agent analyzes Pull Requests by examining diffs, identifying affected
components via CKG queries, and generating intelligent summaries using LLM services.
"""

import logging
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from pathlib import Path
import re

# Import related agents and data structures
from ..data_acquisition import PullRequestInfo
from .contextual_query import ContextualQueryAgent
from .llm_analysis_support import (
    LLMAnalysisSupportAgent, 
    PRSummaryRequest
)

logger = logging.getLogger(__name__)


@dataclass
class PRImpactAnalysis:
    """Analysis of PR impact on codebase."""
    
    # Affected components
    affected_functions: List[str]
    affected_classes: List[str]
    affected_modules: List[str]
    affected_packages: List[str]
    
    # Dependency analysis
    direct_dependencies: List[str]
    transitive_dependencies: List[str]
    reverse_dependencies: List[str]
    
    # Risk assessment
    risk_level: str  # low, medium, high, critical
    risk_factors: List[str]
    complexity_score: float
    
    # Change categorization
    change_types: List[str]  # feature, bugfix, refactor, etc.
    breaking_changes: List[str]
    api_changes: List[str]
    
    # Metadata
    analysis_metadata: Dict[str, Any]


@dataclass
class PRAnalysisResult:
    """Complete PR analysis result."""
    
    # Original PR info
    pr_info: PullRequestInfo
    
    # Impact analysis
    impact_analysis: PRImpactAnalysis
    
    # LLM-generated summary
    summary: str
    risk_assessment: str
    testing_recommendations: str
    review_priorities: str
    
    # Quality metrics
    confidence_score: float
    analysis_completeness: float
    
    # Additional insights
    architectural_issues: List[str]
    best_practice_violations: List[str]
    optimization_suggestions: List[str]
    
    # Metadata
    analysis_timestamp: str
    analysis_duration: float
    tools_used: List[str]


class PRAnalyzerAgent:
    """
    Agent for comprehensive Pull Request analysis.
    
    This agent combines static analysis, CKG queries, and LLM intelligence
    to provide detailed PR impact assessment and recommendations.
    """
    
    def __init__(self,
                 contextual_query_agent: Optional[ContextualQueryAgent] = None,
                 llm_analysis_agent: Optional[LLMAnalysisSupportAgent] = None):
        """
        Initialize PR Analyzer Agent.
        
        Args:
            contextual_query_agent: Agent for CKG queries
            llm_analysis_agent: Agent for LLM-powered analysis
        """
        self.contextual_query_agent = contextual_query_agent
        self.llm_analysis_agent = llm_analysis_agent
        
        # Analysis configuration
        self.risk_thresholds = {
            'critical': {'functions': 10, 'classes': 5, 'modules': 3},
            'high': {'functions': 7, 'classes': 3, 'modules': 2},
            'medium': {'functions': 4, 'classes': 2, 'modules': 1},
            'low': {'functions': 2, 'classes': 1, 'modules': 1}
        }
        
        self.change_patterns = {
            'feature': [r'add', r'new', r'implement', r'feat'],
            'bugfix': [r'fix', r'bug', r'issue', r'patch'],
            'refactor': [r'refactor', r'cleanup', r'improve', r'optimize'],
            'docs': [r'doc', r'readme', r'comment'],
            'test': [r'test', r'spec'],
            'config': [r'config', r'setting', r'env']
        }
        
        logger.info("PRAnalyzerAgent initialized successfully")
    
    async def analyze_pull_request(self, 
                                 pr_info: PullRequestInfo,
                                 ckg_context: Optional[Dict[str, Any]] = None,
                                 **kwargs) -> PRAnalysisResult:
        """
        Perform comprehensive PR analysis.
        
        Args:
            pr_info: Pull Request information with diff
            ckg_context: Code Knowledge Graph context
            **kwargs: Additional analysis parameters
            
        Returns:
            PRAnalysisResult with complete analysis
        """
        logger.info(f"Starting PR analysis for PR #{pr_info.pr_id}: {pr_info.title}")
        
        try:
            import time
            start_time = time.time()
            
            # Step 1: Analyze diff and identify affected components
            impact_analysis = await self._analyze_pr_impact(pr_info, ckg_context)
            
            # Step 2: Generate LLM-powered summary and assessment
            llm_analysis = await self._generate_llm_analysis(pr_info, impact_analysis, ckg_context)
            
            # Step 3: Perform risk assessment
            risk_level, risk_factors = self._assess_risk(pr_info, impact_analysis)
            
            # Step 4: Generate recommendations
            testing_recommendations = self._generate_testing_recommendations(pr_info, impact_analysis)
            review_priorities = self._generate_review_priorities(pr_info, impact_analysis)
            
            # Step 5: Identify architectural and quality issues
            architectural_issues = self._identify_architectural_issues(pr_info, impact_analysis)
            best_practice_violations = self._identify_best_practice_violations(pr_info)
            optimization_suggestions = self._generate_optimization_suggestions(pr_info, impact_analysis)
            
            # Calculate quality metrics
            confidence_score = self._calculate_confidence_score(impact_analysis, llm_analysis)
            completeness_score = self._calculate_completeness_score(pr_info, impact_analysis)
            
            analysis_duration = time.time() - start_time
            
            # Create comprehensive result
            result = PRAnalysisResult(
                pr_info=pr_info,
                impact_analysis=impact_analysis,
                summary=llm_analysis.get('summary', 'Summary not available'),
                risk_assessment=llm_analysis.get('risk_assessment', f"Risk Level: {risk_level}"),
                testing_recommendations=testing_recommendations,
                review_priorities=review_priorities,
                confidence_score=confidence_score,
                analysis_completeness=completeness_score,
                architectural_issues=architectural_issues,
                best_practice_violations=best_practice_violations,
                optimization_suggestions=optimization_suggestions,
                analysis_timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                analysis_duration=analysis_duration,
                tools_used=['PRAnalyzer', 'CKGQuery', 'LLMAnalysis']
            )
            
            logger.info(f"PR analysis completed for #{pr_info.pr_id} in {analysis_duration:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze PR #{pr_info.pr_id}: {e}")
            raise
    
    async def _analyze_pr_impact(self, 
                               pr_info: PullRequestInfo,
                               ckg_context: Optional[Dict[str, Any]] = None) -> PRImpactAnalysis:
        """Analyze PR impact on codebase components."""
        logger.info(f"Analyzing impact for PR #{pr_info.pr_id}")
        
        # Parse diff to identify changed functions/classes
        affected_functions, affected_classes = self._parse_diff_components(pr_info.diff_text)
        
        # Identify affected modules and packages
        affected_modules = list(set([
            self._file_to_module(file) for file in pr_info.changed_files
        ]))
        affected_packages = list(set([
            self._file_to_package(file) for file in pr_info.changed_files
        ]))
        
        # Query CKG for dependency information
        dependencies = await self._query_dependencies(
            affected_functions + affected_classes + affected_modules,
            ckg_context
        )
        
        # Assess risk level
        risk_level = self._calculate_impact_risk(
            len(affected_functions), len(affected_classes), len(affected_modules)
        )
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(pr_info, affected_functions, affected_classes)
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(pr_info)
        
        # Categorize change types
        change_types = self._categorize_changes(pr_info)
        
        # Identify breaking changes and API changes
        breaking_changes = self._identify_breaking_changes(pr_info, affected_functions, affected_classes)
        api_changes = self._identify_api_changes(pr_info, affected_functions, affected_classes)
        
        return PRImpactAnalysis(
            affected_functions=affected_functions,
            affected_classes=affected_classes,
            affected_modules=affected_modules,
            affected_packages=affected_packages,
            direct_dependencies=dependencies.get('direct', []),
            transitive_dependencies=dependencies.get('transitive', []),
            reverse_dependencies=dependencies.get('reverse', []),
            risk_level=risk_level,
            risk_factors=risk_factors,
            complexity_score=complexity_score,
            change_types=change_types,
            breaking_changes=breaking_changes,
            api_changes=api_changes,
            analysis_metadata={
                'diff_lines': pr_info.changed_lines,
                'files_changed': len(pr_info.changed_files),
                'additions': pr_info.additions,
                'deletions': pr_info.deletions
            }
        )
    
    async def _generate_llm_analysis(self, 
                                   pr_info: PullRequestInfo,
                                   impact_analysis: PRImpactAnalysis,
                                   ckg_context: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """Generate LLM-powered analysis and summary."""
        if not self.llm_analysis_agent:
            logger.warning("No LLM analysis agent available, using fallback")
            return {
                'summary': f"PR #{pr_info.pr_id}: {pr_info.title} affects {len(impact_analysis.affected_modules)} modules",
                'risk_assessment': f"Risk Level: {impact_analysis.risk_level}"
            }
        
        try:
            # Prepare affected components info for LLM
            affected_components_info = {
                'functions': impact_analysis.affected_functions,
                'classes': impact_analysis.affected_classes,
                'modules': impact_analysis.affected_modules,
                'packages': impact_analysis.affected_packages,
                'dependencies': impact_analysis.direct_dependencies,
                'risk_level': impact_analysis.risk_level,
                'complexity_score': impact_analysis.complexity_score
            }
            
            # Create PR summary request
            pr_request = PRSummaryRequest(
                diff_text=pr_info.diff_text,
                pr_metadata={
                    'id': pr_info.pr_id,
                    'title': pr_info.title,
                    'description': pr_info.description,
                    'author': pr_info.author,
                    'status': pr_info.status,
                    'platform': pr_info.platform
                },
                changed_files=pr_info.changed_files,
                affected_components_info=affected_components_info,
                ckg_context=ckg_context
            )
            
            # Get LLM analysis
            response = await self.llm_analysis_agent.request_pr_summary(pr_request)
            
            if response.success:
                # Parse LLM response for different components
                content = response.content
                return {
                    'summary': content,
                    'risk_assessment': f"Risk Level: {impact_analysis.risk_level} - {content[:200]}..."
                }
            else:
                logger.warning(f"LLM analysis failed: {response.error_message}")
                return {
                    'summary': f"LLM analysis unavailable for PR #{pr_info.pr_id}",
                    'risk_assessment': f"Risk Level: {impact_analysis.risk_level}"
                }
                
        except Exception as e:
            logger.error(f"Failed to generate LLM analysis: {e}")
            return {
                'summary': f"Error in LLM analysis for PR #{pr_info.pr_id}: {str(e)}",
                'risk_assessment': f"Risk Level: {impact_analysis.risk_level}"
            }
    
    async def _query_dependencies(self, 
                                components: List[str],
                                ckg_context: Optional[Dict[str, Any]] = None) -> Dict[str, List[str]]:
        """Query CKG for component dependencies."""
        if not self.contextual_query_agent or not components:
            return {'direct': [], 'transitive': [], 'reverse': []}
        
        try:
            # Query direct dependencies
            direct_deps = []
            reverse_deps = []
            
            for component in components:
                # This would be actual CKG queries in real implementation
                # For now, returning mock data structure
                pass
            
            return {
                'direct': direct_deps,
                'transitive': [],  # Would implement transitive dependency analysis
                'reverse': reverse_deps
            }
            
        except Exception as e:
            logger.error(f"Failed to query dependencies: {e}")
            return {'direct': [], 'transitive': [], 'reverse': []}
    
    def _parse_diff_components(self, diff_text: str) -> tuple[List[str], List[str]]:
        """Parse diff to extract affected functions and classes."""
        functions = []
        classes = []
        
        if not diff_text:
            return functions, classes
        
        # Regex patterns for different languages
        patterns = {
            'python': {
                'function': r'^\+.*def\s+(\w+)\s*\(',
                'class': r'^\+.*class\s+(\w+)\s*[\(:]'
            },
            'java': {
                'function': r'^\+.*(?:public|private|protected)?\s*\w+\s+(\w+)\s*\(',
                'class': r'^\+.*(?:public|private|protected)?\s*class\s+(\w+)\s*[{<]'
            },
            'javascript': {
                'function': r'^\+.*(?:function\s+(\w+)|(\w+)\s*[=:]\s*function)',
                'class': r'^\+.*class\s+(\w+)\s*[{]'
            }
        }
        
        # Extract functions and classes from diff
        for line in diff_text.split('\n'):
            if line.startswith('+'):
                # Try patterns for all languages
                for lang, lang_patterns in patterns.items():
                    # Function patterns
                    func_match = re.search(lang_patterns['function'], line)
                    if func_match:
                        func_name = func_match.group(1)
                        if func_name and func_name not in functions:
                            functions.append(func_name)
                    
                    # Class patterns
                    class_match = re.search(lang_patterns['class'], line)
                    if class_match:
                        class_name = class_match.group(1)
                        if class_name and class_name not in classes:
                            classes.append(class_name)
        
        return functions, classes
    
    def _file_to_module(self, file_path: str) -> str:
        """Convert file path to module name."""
        path = Path(file_path)
        return str(path.with_suffix(''))
    
    def _file_to_package(self, file_path: str) -> str:
        """Convert file path to package name."""
        path = Path(file_path)
        return str(path.parent) if path.parent != Path('.') else 'root'
    
    def _calculate_impact_risk(self, num_functions: int, num_classes: int, num_modules: int) -> str:
        """Calculate impact risk level based on affected components."""
        for risk_level, thresholds in self.risk_thresholds.items():
            if (num_functions >= thresholds['functions'] or
                num_classes >= thresholds['classes'] or
                num_modules >= thresholds['modules']):
                return risk_level
        return 'low'
    
    def _identify_risk_factors(self, pr_info: PullRequestInfo, 
                              functions: List[str], classes: List[str]) -> List[str]:
        """Identify specific risk factors in the PR."""
        risk_factors = []
        
        # Large changeset
        if pr_info.changed_lines > 500:
            risk_factors.append("Large changeset (>500 lines)")
        
        # Many files changed
        if len(pr_info.changed_files) > 10:
            risk_factors.append(f"Many files changed ({len(pr_info.changed_files)})")
        
        # Core system files
        core_patterns = ['main', 'core', 'base', 'config', 'init']
        for file in pr_info.changed_files:
            if any(pattern in file.lower() for pattern in core_patterns):
                risk_factors.append("Core system files modified")
                break
        
        # Database/schema changes
        db_patterns = ['.sql', 'migration', 'schema']
        for file in pr_info.changed_files:
            if any(pattern in file.lower() for pattern in db_patterns):
                risk_factors.append("Database/schema changes")
                break
        
        return risk_factors
    
    def _calculate_complexity_score(self, pr_info: PullRequestInfo) -> float:
        """Calculate complexity score for the PR."""
        # Base score from line changes
        base_score = min(pr_info.changed_lines / 100.0, 5.0)
        
        # File diversity factor
        file_types = set()
        for file in pr_info.changed_files:
            ext = Path(file).suffix.lower()
            file_types.add(ext)
        
        diversity_factor = len(file_types) * 0.1
        
        # Deletion vs addition ratio (higher deletion ratio = more complex)
        if pr_info.additions > 0:
            deletion_ratio = pr_info.deletions / pr_info.additions
            deletion_factor = min(deletion_ratio * 0.5, 1.0)
        else:
            deletion_factor = 0.0
        
        complexity_score = base_score + diversity_factor + deletion_factor
        return min(complexity_score, 10.0)  # Cap at 10
    
    def _categorize_changes(self, pr_info: PullRequestInfo) -> List[str]:
        """Categorize the type of changes in the PR."""
        change_types = []
        
        # Analyze title and description
        text = f"{pr_info.title} {pr_info.description}".lower()
        
        for change_type, patterns in self.change_patterns.items():
            if any(re.search(pattern, text) for pattern in patterns):
                change_types.append(change_type)
        
        # Analyze file patterns
        for file in pr_info.changed_files:
            if 'test' in file.lower() and 'test' not in change_types:
                change_types.append('test')
            elif file.lower().endswith(('.md', '.txt', '.rst')) and 'docs' not in change_types:
                change_types.append('docs')
            elif file.lower().endswith(('.yml', '.yaml', '.json', '.config')) and 'config' not in change_types:
                change_types.append('config')
        
        return change_types if change_types else ['unknown']
    
    def _identify_breaking_changes(self, pr_info: PullRequestInfo, 
                                  functions: List[str], classes: List[str]) -> List[str]:
        """Identify potential breaking changes."""
        breaking_changes = []
        
        # Check for removed/renamed functions and classes
        for line in pr_info.diff_text.split('\n'):
            if line.startswith('-'):
                # Look for function/class removals
                if 'def ' in line or 'class ' in line:
                    breaking_changes.append(f"Function/class removal detected: {line.strip()}")
        
        # Check for API signature changes
        # This would be more sophisticated in real implementation
        
        return breaking_changes
    
    def _identify_api_changes(self, pr_info: PullRequestInfo,
                             functions: List[str], classes: List[str]) -> List[str]:
        """Identify API changes that may affect consumers."""
        api_changes = []
        
        # Look for public API changes
        for file in pr_info.changed_files:
            if 'api' in file.lower() or 'interface' in file.lower():
                api_changes.append(f"API file modified: {file}")
        
        return api_changes
    
    def _assess_risk(self, pr_info: PullRequestInfo, 
                    impact_analysis: PRImpactAnalysis) -> tuple[str, List[str]]:
        """Assess overall risk level and factors."""
        return impact_analysis.risk_level, impact_analysis.risk_factors
    
    def _generate_testing_recommendations(self, pr_info: PullRequestInfo,
                                        impact_analysis: PRImpactAnalysis) -> str:
        """Generate testing recommendations for the PR."""
        recommendations = []
        
        if impact_analysis.affected_functions:
            recommendations.append("• Unit tests cho các functions đã thay đổi")
        
        if impact_analysis.affected_classes:
            recommendations.append("• Integration tests cho các classes bị ảnh hưởng")
        
        if impact_analysis.risk_level in ['high', 'critical']:
            recommendations.append("• Regression testing toàn diện")
            recommendations.append("• Performance testing")
        
        if 'config' in impact_analysis.change_types:
            recommendations.append("• Configuration validation tests")
        
        if 'database' in ' '.join(impact_analysis.risk_factors).lower():
            recommendations.append("• Database migration tests")
        
        return '\n'.join(recommendations) if recommendations else "Standard testing protocols"
    
    def _generate_review_priorities(self, pr_info: PullRequestInfo,
                                  impact_analysis: PRImpactAnalysis) -> str:
        """Generate review priorities for the PR."""
        priorities = []
        
        if impact_analysis.risk_level == 'critical':
            priorities.append("🔴 CRITICAL: Architecture review required")
        elif impact_analysis.risk_level == 'high':
            priorities.append("🟠 HIGH: Senior developer review")
        
        if impact_analysis.breaking_changes:
            priorities.append("⚠️  Breaking changes - API compatibility review")
        
        if impact_analysis.complexity_score > 7:
            priorities.append("🔍 Complex changes - detailed code review")
        
        if 'security' in ' '.join(impact_analysis.risk_factors).lower():
            priorities.append("🔒 Security review required")
        
        return '\n'.join(priorities) if priorities else "Standard code review"
    
    def _identify_architectural_issues(self, pr_info: PullRequestInfo,
                                     impact_analysis: PRImpactAnalysis) -> List[str]:
        """Identify potential architectural issues."""
        issues = []
        
        # Too many modules affected
        if len(impact_analysis.affected_modules) > 5:
            issues.append("PR affects too many modules - consider splitting")
        
        # High complexity score
        if impact_analysis.complexity_score > 8:
            issues.append("High complexity - consider refactoring")
        
        return issues
    
    def _identify_best_practice_violations(self, pr_info: PullRequestInfo) -> List[str]:
        """Identify best practice violations."""
        violations = []
        
        # Large PR
        if pr_info.changed_lines > 1000:
            violations.append("PR too large - difficult to review effectively")
        
        # No description
        if not pr_info.description or len(pr_info.description.strip()) < 10:
            violations.append("Missing or insufficient PR description")
        
        return violations
    
    def _generate_optimization_suggestions(self, pr_info: PullRequestInfo,
                                         impact_analysis: PRImpactAnalysis) -> List[str]:
        """Generate optimization suggestions."""
        suggestions = []
        
        if impact_analysis.complexity_score > 6:
            suggestions.append("Consider breaking into smaller, focused PRs")
        
        if len(impact_analysis.affected_modules) > 3:
            suggestions.append("Review module coupling - consider refactoring")
        
        return suggestions
    
    def _calculate_confidence_score(self, impact_analysis: PRImpactAnalysis,
                                   llm_analysis: Dict[str, str]) -> float:
        """Calculate confidence score for the analysis."""
        base_score = 0.7
        
        # Boost if we have CKG data
        if impact_analysis.direct_dependencies:
            base_score += 0.1
        
        # Boost if LLM analysis was successful
        if 'Error' not in llm_analysis.get('summary', ''):
            base_score += 0.1
        
        # Reduce if fallback methods were used
        if 'unavailable' in llm_analysis.get('summary', '').lower():
            base_score -= 0.2
        
        return max(0.0, min(1.0, base_score))
    
    def _calculate_completeness_score(self, pr_info: PullRequestInfo,
                                    impact_analysis: PRImpactAnalysis) -> float:
        """Calculate analysis completeness score."""
        score = 0.0
        
        # Basic PR info available
        if pr_info.diff_text:
            score += 0.3
        if pr_info.changed_files:
            score += 0.2
        
        # Impact analysis completeness
        if impact_analysis.affected_functions or impact_analysis.affected_classes:
            score += 0.2
        if impact_analysis.risk_factors:
            score += 0.1
        if impact_analysis.change_types:
            score += 0.1
        
        # Dependency analysis
        if impact_analysis.direct_dependencies:
            score += 0.1
        
        return min(1.0, score) 