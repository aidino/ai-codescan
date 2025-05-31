"""
Prompt Formatter Module for AI CodeScan.

This module provides a comprehensive prompt template library and formatting
capabilities for various LLM tasks including PR analysis, code explanation,
and Q&A interactions.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class PromptTemplate(Enum):
    """Enumeration of available prompt templates."""
    
    # Code explanation templates
    CODE_EXPLANATION = "code_explanation"
    FUNCTION_EXPLANATION = "function_explanation"
    CLASS_EXPLANATION = "class_explanation"
    
    # PR analysis templates
    PR_SUMMARY = "pr_summary"
    PR_IMPACT_ANALYSIS = "pr_impact_analysis"
    PR_RISK_ASSESSMENT = "pr_risk_assessment"
    
    # Q&A templates
    CODE_QA_GENERAL = "code_qa_general"
    CODE_QA_STRUCTURE = "code_qa_structure"
    CODE_QA_BEST_PRACTICES = "code_qa_best_practices"
    
    # Architecture analysis templates
    ARCHITECTURE_SUMMARY = "architecture_summary"
    CIRCULAR_DEPENDENCY_EXPLANATION = "circular_dependency_explanation"
    UNUSED_CODE_EXPLANATION = "unused_code_explanation"
    
    # Report generation templates
    EXECUTIVE_SUMMARY = "executive_summary"
    TECHNICAL_SUMMARY = "technical_summary"
    ISSUE_PRIORITIZATION = "issue_prioritization"


@dataclass
class PromptContext:
    """Context data container for prompt formatting."""
    
    # Code-related context
    code_snippet: Optional[str] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    file_path: Optional[str] = None
    language: Optional[str] = None
    
    # CKG-related context
    ckg_data: Optional[Dict[str, Any]] = None
    related_components: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    
    # PR-related context
    diff_text: Optional[str] = None
    changed_files: Optional[List[str]] = None
    pr_metadata: Optional[Dict[str, Any]] = None
    
    # Q&A context
    user_question: Optional[str] = None
    search_results: Optional[List[Dict[str, Any]]] = None
    
    # Analysis context
    findings: Optional[List[Dict[str, Any]]] = None
    architectural_issues: Optional[List[Dict[str, Any]]] = None
    complexity_metrics: Optional[Dict[str, Any]] = None
    
    # Additional metadata
    project_name: Optional[str] = None
    project_type: Optional[str] = None
    framework: Optional[str] = None
    custom_data: Optional[Dict[str, Any]] = None


class PromptFormatterModule:
    """
    Module for formatting prompts using templates and context data.
    
    This module provides a comprehensive system for managing prompt templates
    and formatting them with dynamic context data for various LLM tasks.
    """
    
    def __init__(self, custom_templates_path: Optional[str] = None):
        """
        Initialize the PromptFormatterModule.
        
        Args:
            custom_templates_path: Optional path to custom template files
        """
        self.templates = self._load_default_templates()
        self.custom_templates_path = custom_templates_path
        
        if custom_templates_path:
            self._load_custom_templates(custom_templates_path)
    
    def _load_default_templates(self) -> Dict[str, str]:
        """Load default prompt templates."""
        return {
            # Code explanation templates
            PromptTemplate.CODE_EXPLANATION.value: """
Hãy phân tích và giải thích đoạn code sau:

**File:** {file_path}
**Ngôn ngữ:** {language}

```{language}
{code_snippet}
```

Vui lòng cung cấp:
1. **Mục đích chính** của đoạn code này
2. **Các thành phần chính** và chức năng của chúng
3. **Luồng thực thi** chính
4. **Dependencies và relationships** với các thành phần khác
5. **Potential issues** hoặc điểm cần cải thiện (nếu có)

{ckg_context}
""",

            PromptTemplate.FUNCTION_EXPLANATION.value: """
Phân tích function `{function_name}` trong file `{file_path}`:

```{language}
{code_snippet}
```

**CKG Context:**
{ckg_context}

Hãy giải thích:
1. **Chức năng** của function này
2. **Parameters và return value**
3. **Complexity** và performance characteristics
4. **Usage patterns** trong codebase
5. **Recommendations** cho improvement hoặc refactoring

{related_components}
""",

            PromptTemplate.CLASS_EXPLANATION.value: """
Phân tích class `{class_name}` trong project:

**File:** {file_path}
**Language:** {language}

```{language}
{code_snippet}
```

**Class Dependencies:**
{dependencies}

**Related Components:**
{related_components}

Vui lòng cung cấp:
1. **Purpose và responsibility** của class
2. **Key methods và properties**
3. **Design patterns** được sử dụng
4. **Inheritance hierarchy** và relationships
5. **Potential improvements** về design

{ckg_context}
""",

            # PR analysis templates
            PromptTemplate.PR_SUMMARY.value: """
Tạo tóm tắt cho Pull Request sau:

**PR Metadata:**
{pr_metadata}

**Changed Files:**
{changed_files}

**Diff Content:**
```diff
{diff_text}
```

**Affected Components (từ CKG):**
{related_components}

Hãy cung cấp:
1. **Summary ngắn gọn** về những thay đổi chính
2. **Impact analysis** - các thành phần bị ảnh hưởng
3. **Risk assessment** - mức độ rủi ro của thay đổi
4. **Testing recommendations** - areas cần test kỹ
5. **Review priorities** - điểm nào reviewer nên focus

{ckg_context}
""",

            PromptTemplate.PR_IMPACT_ANALYSIS.value: """
Phân tích tác động của Pull Request:

**Changes Summary:**
{changed_files}

**CKG Analysis:**
{ckg_data}

**Architectural Context:**
{architectural_issues}

Đánh giá:
1. **Direct Impact** - file/function được thay đổi trực tiếp
2. **Indirect Impact** - components phụ thuộc vào thay đổi
3. **Breaking Changes** - có thể gây break existing functionality
4. **Performance Impact** - ảnh hưởng đến performance
5. **Security Implications** - security considerations

Recommendations:
- Testing strategy
- Deployment considerations
- Monitoring requirements
""",

            # Q&A templates
            PromptTemplate.CODE_QA_GENERAL.value: """
Trả lời câu hỏi về codebase:

**Câu hỏi:** {user_question}

**Code Context:**
{code_snippet}

**CKG Information:**
{ckg_data}

**Search Results:**
{search_results}

**Project Context:**
- Project: {project_name}
- Type: {project_type}
- Framework: {framework}
- Language: {language}

Vui lòng cung cấp câu trả lời chi tiết và accurate dựa trên context đã cung cấp. Nếu cần thêm thông tin, hãy đề xuất câu hỏi follow-up.
""",

            PromptTemplate.CODE_QA_STRUCTURE.value: """
Trả lời câu hỏi về cấu trúc code:

**Question:** {user_question}

**Architectural Information:**
{ckg_data}

**Related Components:**
{related_components}

**Dependencies:**
{dependencies}

Phân tích và trả lời về:
1. **Cấu trúc hiện tại** của component được hỏi
2. **Relationships** với các components khác
3. **Design patterns** và architectural decisions
4. **Potential improvements** cho cấu trúc
""",

            # Architecture analysis
            PromptTemplate.ARCHITECTURE_SUMMARY.value: """
Tạo tóm tắt kiến trúc cho project:

**Project:** {project_name}
**Type:** {project_type}
**Languages:** {language}

**Architectural Issues:**
{architectural_issues}

**Complexity Metrics:**
{complexity_metrics}

**CKG Analysis:**
{ckg_data}

Cung cấp:
1. **Overall Architecture** overview
2. **Key Components** và roles của chúng
3. **Design Patterns** được sử dụng
4. **Architectural Issues** cần attention
5. **Improvement Recommendations**
""",

            PromptTemplate.CIRCULAR_DEPENDENCY_EXPLANATION.value: """
Giải thích circular dependencies được phát hiện:

**Circular Dependencies:**
{architectural_issues}

**Affected Components:**
{related_components}

**CKG Context:**
{ckg_data}

Hãy:
1. **Mô tả** circular dependency cycle
2. **Giải thích** tại sao đây là vấn đề
3. **Đánh giá** impact lên maintainability
4. **Đề xuất** solutions để break the cycle
5. **Prioritize** which dependencies nên fix trước
""",

            # Executive summary
            PromptTemplate.EXECUTIVE_SUMMARY.value: """
Tạo executive summary cho code analysis:

**Project:** {project_name}
**Analysis Scope:** {language} codebase

**Key Findings:**
{findings}

**Architectural Issues:**
{architectural_issues}

**Complexity Overview:**
{complexity_metrics}

Target audience: Non-technical stakeholders

Cung cấp:
1. **High-level Overview** - tình trạng general của codebase
2. **Key Risks** - main concerns cần attention
3. **Business Impact** - how issues affect business goals
4. **Recommended Actions** - prioritized improvement plan
5. **Resource Requirements** - effort estimation for fixes

Tone: Professional, clear, non-technical language.
""",

            PromptTemplate.TECHNICAL_SUMMARY.value: """
Tạo technical summary cho development team:

**Analysis Results:**
{findings}

**Code Quality Metrics:**
{complexity_metrics}

**Architectural Analysis:**
{architectural_issues}

**CKG Insights:**
{ckg_data}

Target: Software developers và technical leads

Include:
1. **Code Quality Assessment** - detailed technical findings
2. **Architecture Review** - structural issues và patterns
3. **Performance Considerations** - potential bottlenecks
4. **Security Review** - security-related findings
5. **Refactoring Opportunities** - specific improvement areas
6. **Technical Debt** - areas requiring attention

Format: Technical detail với actionable recommendations.
"""
        }
    
    def _load_custom_templates(self, templates_path: str) -> None:
        """
        Load custom templates from file.
        
        Args:
            templates_path: Path to custom templates file
        """
        try:
            path = Path(templates_path)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    custom_templates = json.load(f)
                    self.templates.update(custom_templates)
                    logger.info(f"Loaded {len(custom_templates)} custom templates from {templates_path}")
        except Exception as e:
            logger.warning(f"Failed to load custom templates: {e}")
    
    def format_prompt(self, 
                     template_name: Union[str, PromptTemplate], 
                     context: PromptContext,
                     max_length: Optional[int] = None) -> str:
        """
        Format a prompt template with provided context data.
        
        Args:
            template_name: Name or enum of the template to use
            context: Context data for template formatting
            max_length: Optional maximum length for the formatted prompt
            
        Returns:
            Formatted prompt string
            
        Raises:
            ValueError: If template not found or formatting fails
        """
        # Convert enum to string if needed
        if isinstance(template_name, PromptTemplate):
            template_name = template_name.value
        
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = self.templates[template_name]
        
        try:
            # Prepare context data for formatting
            format_data = self._prepare_format_data(context)
            
            # Format the template
            formatted_prompt = template.format(**format_data)
            
            # Apply length constraints if specified
            if max_length and len(formatted_prompt) > max_length:
                formatted_prompt = self._truncate_prompt(formatted_prompt, max_length)
            
            logger.debug(f"Formatted prompt using template '{template_name}', length: {len(formatted_prompt)}")
            return formatted_prompt
            
        except KeyError as e:
            raise ValueError(f"Missing required context data for template '{template_name}': {e}")
        except Exception as e:
            raise ValueError(f"Failed to format template '{template_name}': {e}")
    
    def _prepare_format_data(self, context: PromptContext) -> Dict[str, str]:
        """
        Prepare context data for template formatting.
        
        Args:
            context: PromptContext object
            
        Returns:
            Dictionary with formatted context data
        """
        format_data = {}
        
        # Basic context fields
        format_data['code_snippet'] = context.code_snippet or ""
        format_data['function_name'] = context.function_name or "Unknown"
        format_data['class_name'] = context.class_name or "Unknown"
        format_data['file_path'] = context.file_path or "Unknown"
        format_data['language'] = context.language or "Unknown"
        format_data['project_name'] = context.project_name or "Project"
        format_data['project_type'] = context.project_type or "Unknown"
        format_data['framework'] = context.framework or "N/A"
        format_data['user_question'] = context.user_question or ""
        format_data['diff_text'] = context.diff_text or ""
        
        # Complex context formatting
        format_data['ckg_context'] = self._format_ckg_context(context.ckg_data)
        format_data['ckg_data'] = self._format_ckg_data(context.ckg_data)
        format_data['related_components'] = self._format_list_data(context.related_components, "Related Components")
        format_data['dependencies'] = self._format_list_data(context.dependencies, "Dependencies")
        format_data['changed_files'] = self._format_list_data(context.changed_files, "Changed Files")
        format_data['findings'] = self._format_findings(context.findings)
        format_data['architectural_issues'] = self._format_architectural_issues(context.architectural_issues)
        format_data['complexity_metrics'] = self._format_complexity_metrics(context.complexity_metrics)
        format_data['pr_metadata'] = self._format_pr_metadata(context.pr_metadata)
        format_data['search_results'] = self._format_search_results(context.search_results)
        
        return format_data
    
    def _format_ckg_context(self, ckg_data: Optional[Dict[str, Any]]) -> str:
        """Format CKG data for context inclusion."""
        if not ckg_data:
            return "No CKG context available."
        
        context_parts = []
        
        if 'nodes' in ckg_data:
            context_parts.append(f"CKG Nodes: {len(ckg_data['nodes'])} components analyzed")
        
        if 'relationships' in ckg_data:
            context_parts.append(f"Relationships: {len(ckg_data['relationships'])} connections found")
        
        if 'complexity' in ckg_data:
            context_parts.append(f"Complexity Score: {ckg_data['complexity']}")
        
        return "\n".join(context_parts) if context_parts else "CKG data available but not detailed."
    
    def _format_ckg_data(self, ckg_data: Optional[Dict[str, Any]]) -> str:
        """Format detailed CKG data."""
        if not ckg_data:
            return "No CKG data available."
        
        return json.dumps(ckg_data, indent=2, ensure_ascii=False)[:1000] + "..." if len(str(ckg_data)) > 1000 else json.dumps(ckg_data, indent=2, ensure_ascii=False)
    
    def _format_list_data(self, data: Optional[List[str]], title: str) -> str:
        """Format list data with title."""
        if not data:
            return f"No {title.lower()} available."
        
        return f"{title}:\n" + "\n".join(f"- {item}" for item in data[:10]) + ("..." if len(data) > 10 else "")
    
    def _format_findings(self, findings: Optional[List[Dict[str, Any]]]) -> str:
        """Format analysis findings."""
        if not findings:
            return "No findings available."
        
        formatted = []
        for finding in findings[:20]:  # Limit to first 20 findings
            severity = finding.get('severity', 'Unknown')
            message = finding.get('message', 'No message')
            file_path = finding.get('file', 'Unknown file')
            formatted.append(f"[{severity}] {file_path}: {message}")
        
        return "\n".join(formatted) + ("..." if len(findings) > 20 else "")
    
    def _format_architectural_issues(self, issues: Optional[List[Dict[str, Any]]]) -> str:
        """Format architectural issues."""
        if not issues:
            return "No architectural issues detected."
        
        formatted = []
        for issue in issues[:10]:  # Limit to first 10 issues
            issue_type = issue.get('type', 'Unknown')
            description = issue.get('description', 'No description')
            severity = issue.get('severity', 'Unknown')
            formatted.append(f"[{severity}] {issue_type}: {description}")
        
        return "\n".join(formatted)
    
    def _format_complexity_metrics(self, metrics: Optional[Dict[str, Any]]) -> str:
        """Format complexity metrics."""
        if not metrics:
            return "No complexity metrics available."
        
        formatted = []
        for key, value in metrics.items():
            formatted.append(f"{key}: {value}")
        
        return "\n".join(formatted)
    
    def _format_pr_metadata(self, metadata: Optional[Dict[str, Any]]) -> str:
        """Format PR metadata."""
        if not metadata:
            return "No PR metadata available."
        
        formatted = []
        important_fields = ['title', 'author', 'created_at', 'status', 'branch']
        
        for field in important_fields:
            if field in metadata:
                formatted.append(f"{field.title()}: {metadata[field]}")
        
        return "\n".join(formatted)
    
    def _format_search_results(self, results: Optional[List[Dict[str, Any]]]) -> str:
        """Format search results."""
        if not results:
            return "No search results available."
        
        formatted = []
        for i, result in enumerate(results[:5], 1):  # Limit to top 5 results
            title = result.get('title', 'Unknown')
            snippet = result.get('snippet', 'No snippet')
            formatted.append(f"{i}. {title}: {snippet}")
        
        return "\n".join(formatted)
    
    def _truncate_prompt(self, prompt: str, max_length: int) -> str:
        """
        Truncate prompt to maximum length while preserving structure.
        
        Args:
            prompt: Original prompt
            max_length: Maximum allowed length
            
        Returns:
            Truncated prompt
        """
        if len(prompt) <= max_length:
            return prompt
        
        # Try to truncate at paragraph boundaries
        paragraphs = prompt.split('\n\n')
        truncated = ""
        
        for paragraph in paragraphs:
            if len(truncated + paragraph) <= max_length - 50:  # Leave room for truncation message
                truncated += paragraph + '\n\n'
            else:
                break
        
        if truncated:
            truncated += "\n[... Truncated for length ...]"
        else:
            # If even first paragraph is too long, do simple truncation
            truncated = prompt[:max_length-30] + "\n[... Truncated for length ...]"
        
        return truncated
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template names."""
        return list(self.templates.keys())
    
    def add_custom_template(self, name: str, template: str) -> None:
        """
        Add a custom template.
        
        Args:
            name: Template name
            template: Template string with format placeholders
        """
        self.templates[name] = template
        logger.info(f"Added custom template: {name}")
    
    def validate_template(self, template_name: str, context: PromptContext) -> bool:
        """
        Validate that a template can be formatted with given context.
        
        Args:
            template_name: Name of template to validate
            context: Context to validate against
            
        Returns:
            True if template can be formatted, False otherwise
        """
        try:
            self.format_prompt(template_name, context)
            return True
        except Exception as e:
            logger.warning(f"Template validation failed for {template_name}: {e}")
            return False 