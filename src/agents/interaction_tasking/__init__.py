#!/usr/bin/env python3
"""
AI CodeScan - Interaction & Tasking Module

Module xử lý tương tác người dùng và khởi tạo tác vụ.
"""

from .user_intent_parser import (
    UserIntentParserAgent,
    IntentType,
    UserIntent,
    ParsedIntent
)

from .task_initiation import (
    TaskInitiationAgent,
    TaskType,
    TaskRequest,
    TaskContext,
    InitiatedTask
)

from .dialog_manager import DialogManagerAgent
from .history_manager import HistoryManagerAgent
from .pat_handler import PATHandlerAgent

from .qa_interaction import (
    QAInteractionAgent,
    QAMessage,
    QAConversation,
    QAAnswer
)

__all__ = [
    # Intent Parsing
    'UserIntentParserAgent',
    'IntentType',
    'UserIntent',
    'ParsedIntent',
    
    # Task Initiation
    'TaskInitiationAgent',
    'TaskType',
    'TaskRequest', 
    'TaskContext',
    'InitiatedTask',
    
    # Dialog & History Management
    'DialogManagerAgent',
    'HistoryManagerAgent',
    'PATHandlerAgent',
    
    # Q&A Interaction
    'QAInteractionAgent',
    'QAMessage',
    'QAConversation',
    'QAAnswer'
]
