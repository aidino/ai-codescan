"""
Q&A Interaction Agent for AI CodeScan.

This agent handles user questions about code, provides intelligent answers
using LLM and CKG integration, and manages Q&A conversation flows.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import uuid

# Import related agents and data structures
from ..code_analysis import (
    LLMAnalysisSupportAgent,
    QARequest,
    ContextualQueryAgent
)
from ..ckg_operations import CKGOperationsAgent

logger = logging.getLogger(__name__)


@dataclass
class QAMessage:
    """Represents a message in Q&A conversation."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    role: str = "user"  # user, assistant, system
    content: str = ""
    message_type: str = "text"  # text, code, image, etc.
    
    # Context information
    related_files: List[str] = field(default_factory=list)
    related_functions: List[str] = field(default_factory=list)
    related_classes: List[str] = field(default_factory=list)
    
    # Metadata
    confidence_score: Optional[float] = None
    sources: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QAConversation:
    """Represents a Q&A conversation session."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    project_id: str = ""
    title: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Conversation data
    messages: List[QAMessage] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Session state
    is_active: bool = True
    total_questions: int = 0
    total_answers: int = 0
    
    # Quality metrics
    avg_confidence_score: float = 0.0
    user_satisfaction: Optional[float] = None


@dataclass
class QAAnswer:
    """Represents a comprehensive Q&A answer."""
    
    answer_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question: str = ""
    answer: str = ""
    
    # Answer quality
    confidence_score: float = 0.0
    completeness_score: float = 0.0
    relevance_score: float = 0.0
    
    # Supporting information
    code_examples: List[Dict[str, str]] = field(default_factory=list)
    related_components: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    
    # Answer metadata
    answer_type: str = "general"  # general, code_explanation, architectural, troubleshooting
    complexity_level: str = "medium"  # basic, medium, advanced
    estimated_reading_time: int = 0  # in seconds
    
    # Generation info
    generated_by: str = "llm"  # llm, template, hybrid
    generation_time: float = 0.0
    sources_used: List[str] = field(default_factory=list)
    
    # Follow-up suggestions
    follow_up_questions: List[str] = field(default_factory=list)
    related_topics: List[str] = field(default_factory=list)


class QAInteractionAgent:
    """
    Agent for handling Q&A interactions about code.
    
    This agent provides intelligent answers to user questions by:
    - Understanding question context and intent
    - Querying CKG for relevant code information
    - Using LLM for intelligent answer generation
    - Managing conversation flow and history
    """
    
    def __init__(self,
                 llm_analysis_agent: Optional[LLMAnalysisSupportAgent] = None,
                 contextual_query_agent: Optional[ContextualQueryAgent] = None,
                 ckg_operations_agent: Optional[CKGOperationsAgent] = None):
        """
        Initialize Q&A Interaction Agent.
        
        Args:
            llm_analysis_agent: Agent for LLM-powered analysis
            contextual_query_agent: Agent for CKG queries
            ckg_operations_agent: Agent for CKG operations
        """
        self.llm_analysis_agent = llm_analysis_agent
        self.contextual_query_agent = contextual_query_agent
        self.ckg_operations_agent = ckg_operations_agent
        
        # Conversation management
        self.active_conversations: Dict[str, QAConversation] = {}
        self.conversation_history: Dict[str, List[str]] = {}
        
        # Question categorization patterns
        self.question_patterns = {
            'code_explanation': [
                r'what does.*do', r'how does.*work', r'explain.*function',
                r'what is.*class', r'purpose of.*', r'functionality of.*'
            ],
            'architectural': [
                r'architecture of.*', r'design pattern.*', r'structure of.*',
                r'relationship between.*', r'dependencies.*', r'coupling.*'
            ],
            'troubleshooting': [
                r'error.*', r'bug.*', r'problem.*', r'issue.*', r'fix.*',
                r'not working.*', r'failing.*', r'exception.*'
            ],
            'best_practices': [
                r'best practice.*', r'recommendation.*', r'should i.*',
                r'better way.*', r'optimize.*', r'improve.*'
            ],
            'usage': [
                r'how to use.*', r'example.*', r'tutorial.*', r'guide.*',
                r'steps to.*', r'process.*'
            ]
        }
        
        # Answer templates
        self.answer_templates = {
            'code_explanation': """
## Giải thích về {component_name}

{explanation}

### Chức năng chính:
{main_functions}

### Cách sử dụng:
{usage_examples}

### Liên quan đến:
{related_components}
""",
            'architectural': """
## Phân tích kiến trúc

{architectural_analysis}

### Thành phần liên quan:
{components}

### Mối quan hệ:
{relationships}

### Đề xuất:
{recommendations}
""",
            'troubleshooting': """
## Hướng dẫn xử lý vấn đề

### Vấn đề:
{problem_description}

### Nguyên nhân có thể:
{possible_causes}

### Cách khắc phục:
{solutions}

### Phòng ngừa:
{prevention_tips}
"""
        }
        
        logger.info("QAInteractionAgent initialized successfully")
    
    async def start_conversation(self, 
                               user_id: str,
                               project_id: str,
                               initial_context: Optional[Dict[str, Any]] = None) -> QAConversation:
        """
        Start a new Q&A conversation.
        
        Args:
            user_id: User identifier
            project_id: Project identifier
            initial_context: Initial conversation context
            
        Returns:
            QAConversation object
        """
        conversation = QAConversation(
            user_id=user_id,
            project_id=project_id,
            title=f"Q&A Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            context=initial_context or {}
        )
        
        self.active_conversations[conversation.id] = conversation
        
        # Initialize conversation history
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        self.conversation_history[user_id].append(conversation.id)
        
        logger.info(f"Started new Q&A conversation {conversation.id} for user {user_id}")
        return conversation
    
    async def ask_question(self,
                         conversation_id: str,
                         question: str,
                         context_files: Optional[List[str]] = None,
                         **kwargs) -> QAAnswer:
        """
        Process a user question and generate an intelligent answer.
        
        Args:
            conversation_id: Conversation identifier
            question: User's question
            context_files: Files related to the question
            **kwargs: Additional parameters
            
        Returns:
            QAAnswer with comprehensive response
        """
        if conversation_id not in self.active_conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation = self.active_conversations[conversation_id]
        
        logger.info(f"Processing question in conversation {conversation_id}: {question[:100]}...")
        
        try:
            import time
            start_time = time.time()
            
            # Step 1: Categorize the question
            question_type = self._categorize_question(question)
            
            # Step 2: Extract context from CKG
            ckg_context = await self._extract_ckg_context(
                question, context_files, conversation.project_id
            )
            
            # Step 3: Prepare conversation context
            conversation_context = self._prepare_conversation_context(conversation, question)
            
            # Step 4: Generate answer using LLM
            answer_content = await self._generate_llm_answer(
                question, question_type, ckg_context, conversation_context
            )
            
            # Step 5: Extract supporting information
            supporting_info = self._extract_supporting_info(ckg_context, answer_content)
            
            # Step 6: Generate follow-up suggestions
            follow_ups = self._generate_follow_up_questions(question, question_type, ckg_context)
            
            # Step 7: Calculate quality scores
            confidence_score = self._calculate_confidence_score(answer_content, ckg_context)
            completeness_score = self._calculate_completeness_score(answer_content, supporting_info)
            relevance_score = self._calculate_relevance_score(question, answer_content)
            
            generation_time = time.time() - start_time
            
            # Create comprehensive answer
            answer = QAAnswer(
                question=question,
                answer=answer_content,
                confidence_score=confidence_score,
                completeness_score=completeness_score,
                relevance_score=relevance_score,
                code_examples=supporting_info.get('code_examples', []),
                related_components=supporting_info.get('components', []),
                references=supporting_info.get('references', []),
                answer_type=question_type,
                complexity_level=self._assess_complexity_level(question, answer_content),
                estimated_reading_time=self._estimate_reading_time(answer_content),
                generated_by="llm" if self.llm_analysis_agent else "template",
                generation_time=generation_time,
                sources_used=supporting_info.get('sources', []),
                follow_up_questions=follow_ups,
                related_topics=supporting_info.get('related_topics', [])
            )
            
            # Update conversation
            await self._update_conversation(conversation, question, answer)
            
            logger.info(f"Generated answer for conversation {conversation_id} in {generation_time:.2f}s")
            return answer
            
        except Exception as e:
            logger.error(f"Failed to generate answer for conversation {conversation_id}: {e}")
            # Return fallback answer
            return QAAnswer(
                question=question,
                answer=f"Xin lỗi, tôi không thể trả lời câu hỏi này do lỗi kỹ thuật: {str(e)}",
                confidence_score=0.0,
                generated_by="fallback"
            )
    
    async def get_conversation_history(self, conversation_id: str) -> List[QAMessage]:
        """Get conversation message history."""
        if conversation_id not in self.active_conversations:
            return []
        
        return self.active_conversations[conversation_id].messages
    
    async def end_conversation(self, 
                             conversation_id: str,
                             user_satisfaction: Optional[float] = None):
        """End a Q&A conversation."""
        if conversation_id in self.active_conversations:
            conversation = self.active_conversations[conversation_id]
            conversation.is_active = False
            conversation.user_satisfaction = user_satisfaction
            
            logger.info(f"Ended conversation {conversation_id}")
    
    def _categorize_question(self, question: str) -> str:
        """Categorize the question type using pattern matching."""
        import re
        
        question_lower = question.lower()
        
        for category, patterns in self.question_patterns.items():
            for pattern in patterns:
                if re.search(pattern, question_lower):
                    return category
        
        return 'general'
    
    async def _extract_ckg_context(self, 
                                 question: str,
                                 context_files: Optional[List[str]],
                                 project_id: str) -> Dict[str, Any]:
        """Extract relevant context from CKG."""
        ckg_context = {}
        
        try:
            if self.contextual_query_agent:
                # Query CKG for relevant components
                # This would be actual CKG queries in real implementation
                ckg_context = {
                    'related_functions': [],
                    'related_classes': [],
                    'dependencies': [],
                    'usage_examples': []
                }
            
            if context_files:
                ckg_context['context_files'] = context_files
            
        except Exception as e:
            logger.error(f"Failed to extract CKG context: {e}")
        
        return ckg_context
    
    def _prepare_conversation_context(self, 
                                    conversation: QAConversation,
                                    current_question: str) -> str:
        """Prepare conversation context for LLM."""
        context_parts = []
        
        # Add recent conversation history (last 5 messages)
        recent_messages = conversation.messages[-5:] if len(conversation.messages) > 5 else conversation.messages
        
        if recent_messages:
            context_parts.append("## Lịch sử hội thoại gần đây:")
            for msg in recent_messages:
                role = "Người dùng" if msg.role == "user" else "AI"
                context_parts.append(f"**{role}:** {msg.content}")
        
        # Add project context
        if conversation.context:
            context_parts.append(f"## Ngữ cảnh dự án:")
            for key, value in conversation.context.items():
                context_parts.append(f"- {key}: {value}")
        
        return "\n".join(context_parts)
    
    async def _generate_llm_answer(self,
                                 question: str,
                                 question_type: str,
                                 ckg_context: Dict[str, Any],
                                 conversation_context: str) -> str:
        """Generate answer using LLM."""
        if not self.llm_analysis_agent:
            return self._generate_template_answer(question, question_type, ckg_context)
        
        try:
            # Create Q&A request for LLM
            qa_request = QARequest(
                user_question=question,
                code_context=conversation_context,
                ckg_context=ckg_context,
                project_metadata={
                    'question_type': question_type,
                    'language': 'vietnamese'
                }
            )
            
            # Get LLM response
            response = await self.llm_analysis_agent.request_qna_answer(qa_request)
            
            if response.success:
                return response.content
            else:
                logger.warning(f"LLM answer generation failed: {response.error_message}")
                return self._generate_template_answer(question, question_type, ckg_context)
                
        except Exception as e:
            logger.error(f"Failed to generate LLM answer: {e}")
            return self._generate_template_answer(question, question_type, ckg_context)
    
    def _generate_template_answer(self,
                                question: str,
                                question_type: str,
                                ckg_context: Dict[str, Any]) -> str:
        """Generate template-based answer as fallback."""
        if question_type in self.answer_templates:
            template = self.answer_templates[question_type]
            
            # Fill template with available data
            try:
                return template.format(
                    component_name=ckg_context.get('component_name', 'thành phần'),
                    explanation="Đang phân tích để cung cấp giải thích chi tiết...",
                    main_functions="Chức năng chính đang được xác định...",
                    usage_examples="Ví dụ sử dụng sẽ được cung cấp...",
                    related_components=", ".join(ckg_context.get('related_functions', [])),
                    architectural_analysis="Phân tích kiến trúc đang được thực hiện...",
                    components=", ".join(ckg_context.get('related_classes', [])),
                    relationships="Mối quan hệ đang được phân tích...",
                    recommendations="Đề xuất sẽ được cung cấp...",
                    problem_description="Vấn đề đang được phân tích...",
                    possible_causes="Nguyên nhân có thể đang được xác định...",
                    solutions="Giải pháp đang được chuẩn bị...",
                    prevention_tips="Mẹo phòng ngừa sẽ được cung cấp..."
                )
            except KeyError:
                pass
        
        # Generic fallback
        return f"""
## Trả lời cho câu hỏi của bạn

Cảm ơn bạn đã đặt câu hỏi: "{question}"

Tôi đang phân tích câu hỏi này và sẽ cung cấp thông tin chi tiết. Loại câu hỏi: {question_type}

### Thông tin hiện tại:
{self._format_ckg_context(ckg_context)}

### Cần thêm thông tin:
Để trả lời chính xác hơn, vui lòng cung cấp thêm ngữ cảnh hoặc cụ thể hóa câu hỏi.
"""
    
    def _format_ckg_context(self, ckg_context: Dict[str, Any]) -> str:
        """Format CKG context for display."""
        if not ckg_context:
            return "Chưa có thông tin ngữ cảnh"
        
        formatted = []
        for key, value in ckg_context.items():
            if value:
                if isinstance(value, list):
                    formatted.append(f"- {key}: {', '.join(value)}")
                else:
                    formatted.append(f"- {key}: {value}")
        
        return "\n".join(formatted) if formatted else "Thông tin ngữ cảnh đang được thu thập..."
    
    def _extract_supporting_info(self, 
                               ckg_context: Dict[str, Any],
                               answer_content: str) -> Dict[str, Any]:
        """Extract supporting information from context and answer."""
        supporting_info = {
            'code_examples': [],
            'components': ckg_context.get('related_functions', []) + ckg_context.get('related_classes', []),
            'references': ckg_context.get('context_files', []),
            'sources': ['CKG', 'LLM Analysis'],
            'related_topics': []
        }
        
        # Extract code blocks from answer
        import re
        code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', answer_content, re.DOTALL)
        for lang, code in code_blocks:
            supporting_info['code_examples'].append({
                'language': lang or 'text',
                'code': code.strip()
            })
        
        return supporting_info
    
    def _generate_follow_up_questions(self,
                                    question: str,
                                    question_type: str,
                                    ckg_context: Dict[str, Any]) -> List[str]:
        """Generate relevant follow-up questions."""
        follow_ups = []
        
        if question_type == 'code_explanation':
            follow_ups = [
                "Làm thế nào để sử dụng thành phần này?",
                "Có ví dụ thực tế nào không?",
                "Thành phần này liên quan đến những gì khác?"
            ]
        elif question_type == 'architectural':
            follow_ups = [
                "Làm thế nào để cải thiện kiến trúc này?",
                "Có vấn đề gì về hiệu suất không?",
                "Cách tối ưu hóa thiết kế này?"
            ]
        elif question_type == 'troubleshooting':
            follow_ups = [
                "Làm thế nào để phòng ngừa vấn đề này?",
                "Có công cụ nào để debug không?",
                "Cách test để đảm bảo fix được?"
            ]
        else:
            follow_ups = [
                "Bạn cần thêm thông tin gì?",
                "Có câu hỏi liên quan nào khác không?",
                "Cần giải thích chi tiết hơn phần nào?"
            ]
        
        return follow_ups[:3]  # Limit to 3 follow-ups
    
    def _calculate_confidence_score(self, 
                                  answer_content: str,
                                  ckg_context: Dict[str, Any]) -> float:
        """Calculate confidence score for the answer."""
        base_score = 0.5
        
        # Boost for having CKG context
        if ckg_context and any(ckg_context.values()):
            base_score += 0.2
        
        # Boost for answer length and detail
        if len(answer_content) > 200:
            base_score += 0.1
        if len(answer_content) > 500:
            base_score += 0.1
        
        # Boost for code examples
        if '```' in answer_content:
            base_score += 0.1
        
        # Reduce for template-based answers
        if "đang được phân tích" in answer_content.lower():
            base_score -= 0.2
        
        return max(0.0, min(1.0, base_score))
    
    def _calculate_completeness_score(self, 
                                    answer_content: str,
                                    supporting_info: Dict[str, Any]) -> float:
        """Calculate completeness score for the answer."""
        score = 0.0
        
        # Basic answer content
        if len(answer_content) > 100:
            score += 0.3
        if len(answer_content) > 300:
            score += 0.2
        
        # Supporting information
        if supporting_info.get('code_examples'):
            score += 0.2
        if supporting_info.get('components'):
            score += 0.1
        if supporting_info.get('references'):
            score += 0.1
        
        # Structure indicators
        if '##' in answer_content or '###' in answer_content:
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_relevance_score(self, question: str, answer_content: str) -> float:
        """Calculate relevance score between question and answer."""
        # Simple keyword matching for now
        question_words = set(question.lower().split())
        answer_words = set(answer_content.lower().split())
        
        if not question_words:
            return 0.0
        
        common_words = question_words.intersection(answer_words)
        relevance = len(common_words) / len(question_words)
        
        return min(1.0, relevance)
    
    def _assess_complexity_level(self, question: str, answer_content: str) -> str:
        """Assess complexity level of the Q&A."""
        # Simple heuristics
        technical_terms = ['function', 'class', 'method', 'algorithm', 'architecture', 'pattern']
        
        question_lower = question.lower()
        answer_lower = answer_content.lower()
        
        tech_count = sum(1 for term in technical_terms if term in question_lower or term in answer_lower)
        
        if tech_count >= 3 or len(answer_content) > 800:
            return 'advanced'
        elif tech_count >= 1 or len(answer_content) > 300:
            return 'medium'
        else:
            return 'basic'
    
    def _estimate_reading_time(self, content: str) -> int:
        """Estimate reading time in seconds (average 200 WPM)."""
        word_count = len(content.split())
        reading_time = (word_count / 200) * 60  # Convert to seconds
        return max(30, int(reading_time))  # Minimum 30 seconds
    
    async def _update_conversation(self,
                                 conversation: QAConversation,
                                 question: str,
                                 answer: QAAnswer):
        """Update conversation with new Q&A exchange."""
        # Add user message
        user_message = QAMessage(
            role="user",
            content=question,
            related_files=answer.references
        )
        conversation.messages.append(user_message)
        
        # Add assistant message
        assistant_message = QAMessage(
            role="assistant",
            content=answer.answer,
            related_files=answer.references,
            related_functions=[comp for comp in answer.related_components if '(' in comp],
            related_classes=[comp for comp in answer.related_components if '(' not in comp],
            confidence_score=answer.confidence_score,
            sources=answer.sources_used
        )
        conversation.messages.append(assistant_message)
        
        # Update conversation statistics
        conversation.total_questions += 1
        conversation.total_answers += 1
        conversation.updated_at = datetime.now()
        
        # Update average confidence score
        confidence_scores = [msg.confidence_score for msg in conversation.messages 
                           if msg.confidence_score is not None]
        if confidence_scores:
            conversation.avg_confidence_score = sum(confidence_scores) / len(confidence_scores)
    
    def get_conversation_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get Q&A statistics for a user."""
        user_conversations = [
            conv for conv in self.active_conversations.values() 
            if conv.user_id == user_id
        ]
        
        if not user_conversations:
            return {'total_conversations': 0}
        
        total_questions = sum(conv.total_questions for conv in user_conversations)
        total_answers = sum(conv.total_answers for conv in user_conversations)
        avg_confidence = sum(conv.avg_confidence_score for conv in user_conversations) / len(user_conversations)
        
        return {
            'total_conversations': len(user_conversations),
            'total_questions': total_questions,
            'total_answers': total_answers,
            'average_confidence_score': avg_confidence,
            'active_conversations': len([c for c in user_conversations if c.is_active])
        } 