#!/usr/bin/env python3
"""
Prompt Formatter Module for LLM Services.

Handles prompt templates và formatting for different LLM tasks.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PromptType(Enum):
    """Types of prompts."""
    CODE_EXPLANATION = "code_explanation"
    CODE_REVIEW = "code_review"
    BUG_ANALYSIS = "bug_analysis"
    SUGGESTION = "suggestion"
    SUMMARY = "summary"
    QA_ANSWER = "qa_answer"
    PR_ANALYSIS = "pr_analysis"


@dataclass
class PromptTemplate:
    """Template for LLM prompts."""
    name: str
    prompt_type: PromptType
    system_message: str
    user_template: str
    parameters: List[str]
    max_tokens: int = 500
    temperature: float = 0.3


@dataclass
class PromptContext:
    """Context information for prompt formatting."""
    code_snippet: str = ""
    file_path: str = ""
    language: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PromptFormatterModule:
    """Module for formatting prompts cho different LLM tasks."""
    
    def __init__(self):
        """Initialize Prompt Formatter Module."""
        self.templates = self._init_templates()
        self.template_types = list(self.templates.keys())
        logger.info(f"PromptFormatterModule initialized với {len(self.templates)} templates")
    
    def get_template(self, template_name: str) -> Optional[PromptTemplate]:
        """
        Get prompt template by name.
        
        Args:
            template_name: Name of template
            
        Returns:
            PromptTemplate or None if not found
        """
        return self.templates.get(template_name)
    
    def format_prompt(self, 
                     template_name: str, 
                     **kwargs) -> Optional[Dict[str, str]]:
        """
        Format prompt với template và parameters.
        
        Args:
            template_name: Name of template to use
            **kwargs: Parameters for template
            
        Returns:
            Dict with system and user messages
        """
        template = self.get_template(template_name)
        if not template:
            logger.error(f"Template not found: {template_name}")
            return None
        
        try:
            # Format user message với parameters
            user_message = template.user_template.format(**kwargs)
            
            return {
                "system": template.system_message,
                "user": user_message,
                "max_tokens": template.max_tokens,
                "temperature": template.temperature
            }
            
        except KeyError as e:
            logger.error(f"Missing parameter for template {template_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error formatting prompt: {e}")
            return None
    
    def _init_templates(self) -> Dict[str, PromptTemplate]:
        """Initialize prompt templates."""
        templates = {}
        
        # Code Explanation Template
        templates["code_explanation"] = PromptTemplate(
            name="code_explanation",
            prompt_type=PromptType.CODE_EXPLANATION,
            system_message="""You are an expert code analyst. Explain code clearly and concisely.
Focus on:
1. What the code does
2. How it works
3. Key design patterns or algorithms used
4. Potential improvements or concerns

Keep explanations clear and educational.""",
            user_template="""Please explain this code:

{code}

{context}""",
            parameters=["code", "context"],
            max_tokens=500,
            temperature=0.3
        )
        
        # Code Review Template  
        templates["code_review"] = PromptTemplate(
            name="code_review",
            prompt_type=PromptType.CODE_REVIEW,
            system_message="""You are a senior code reviewer. Provide constructive feedback focusing on:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance considerations
4. Maintainability and readability
5. Security concerns

Be specific and actionable in your feedback.""",
            user_template="""Please review this code:

{code}

File: {filename}
Context: {context}

Provide specific feedback and suggestions for improvement.""",
            parameters=["code", "filename", "context"],
            max_tokens=600,
            temperature=0.2
        )
        
        # Bug Analysis Template
        templates["bug_analysis"] = PromptTemplate(
            name="bug_analysis",
            prompt_type=PromptType.BUG_ANALYSIS,
            system_message="""You are a debugging expert. Analyze the reported issue and provide:
1. Likely root cause analysis
2. Steps to reproduce (if applicable)
3. Suggested fix approaches
4. Prevention strategies

Be methodical and thorough in your analysis.""",
            user_template="""Analyze this bug report:

Issue: {issue_description}
Code: {code}
Error: {error_message}
Context: {context}

Provide root cause analysis và suggested fixes.""",
            parameters=["issue_description", "code", "error_message", "context"],
            max_tokens=600,
            temperature=0.2
        )
        
        # PR Analysis Template
        templates["pr_analysis"] = PromptTemplate(
            name="pr_analysis",
            prompt_type=PromptType.PR_ANALYSIS,
            system_message="""You are a Pull Request analyst. Analyze the changes and provide:
1. Summary of changes
2. Impact assessment
3. Potential risks
4. Testing recommendations
5. Deployment considerations

Focus on helping reviewers understand the change impact.""",
            user_template="""Analyze this Pull Request:

Title: {pr_title}
Description: {pr_description}
Changes: {pr_diff}
Files Modified: {files_modified}

Provide a comprehensive analysis of the changes và their impact.""",
            parameters=["pr_title", "pr_description", "pr_diff", "files_modified"],
            max_tokens=700,
            temperature=0.3
        )
        
        # Q&A Answer Template
        templates["qa_answer"] = PromptTemplate(
            name="qa_answer",
            prompt_type=PromptType.QA_ANSWER,
            system_message="""You are a helpful code assistant. Answer questions about code clearly and accurately.
If you're not sure about something, say so. Provide examples when helpful.""",
            user_template="""Question: {question}

Code Context:
{code_context}

CKG Data:
{ckg_data}

Please provide a clear and helpful answer.""",
            parameters=["question", "code_context", "ckg_data"],
            max_tokens=400,
            temperature=0.4
        )
        
        # Summary Template
        templates["summary"] = PromptTemplate(
            name="summary", 
            prompt_type=PromptType.SUMMARY,
            system_message="""You are a technical writer. Create clear, concise summaries of technical content.
Focus on key points and actionable insights.""",
            user_template="""Create a summary of:

{content}

Focus on: {focus_areas}

Provide a clear and concise summary.""",
            parameters=["content", "focus_areas"],
            max_tokens=300,
            temperature=0.3
        )
        
        return templates 