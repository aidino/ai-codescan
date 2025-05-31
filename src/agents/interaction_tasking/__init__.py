#!/usr/bin/env python3
"""
AI CodeScan - Interaction & Tasking Module

Module xử lý tương tác người dùng và khởi tạo tác vụ.
"""

from .user_intent_parser import UserIntentParserAgent
from .task_initiation import TaskInitiationAgent
from .dialog_manager import DialogManagerAgent
from .history_manager import HistoryManager
from .pat_handler import PATHandlerAgent
from .qa_interaction import QAInteractionAgent
from .presentation_agent import PresentationAgent
from .feedback_collector import FeedbackCollectorAgent, UIImprovementAgent

__all__ = [
    # Intent Parsing
    'UserIntentParserAgent',
    
    # Task Initiation
    'TaskInitiationAgent',
    
    # Dialog & History Management
    'DialogManagerAgent',
    'HistoryManager',
    'PATHandlerAgent',
    
    # Q&A Interaction
    'QAInteractionAgent',
    
    # Presentation & UI
    'PresentationAgent',
    
    # Feedback & Improvement
    'FeedbackCollectorAgent',
    'UIImprovementAgent'
]
