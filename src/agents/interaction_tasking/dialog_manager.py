"""
Dialog Manager Agent

Manages dialog state and user interaction flow in the web UI.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from loguru import logger
import time


class DialogState(Enum):
    """Enumeration of possible dialog states."""
    WAITING_INPUT = "waiting_input"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    INTERRUPTED = "interrupted"


class DialogManagerAgent:
    """
    Agent responsible for managing dialog state and user interaction flow.
    
    This agent tracks the current state of user interactions and manages
    the flow of conversation between user and the AI CodeScan system.
    """
    
    def __init__(self):
        """Initialize the DialogManagerAgent."""
        self.current_state = DialogState.WAITING_INPUT
        self.state_history: List[Dict[str, Any]] = []
        self.current_session_id: Optional[str] = None
        self.interaction_context: Dict[str, Any] = {}
    
    def start_session(self, session_id: str) -> None:
        """
        Start a new dialog session.
        
        Args:
            session_id: Unique identifier for the session
        """
        logger.info(f"Starting new dialog session: {session_id}")
        
        self.current_session_id = session_id
        self.current_state = DialogState.WAITING_INPUT
        self.state_history = []
        self.interaction_context = {
            'session_id': session_id,
            'start_time': time.time(),
            'interactions': []
        }
        
        self._record_state_change(DialogState.WAITING_INPUT, "Session started")
    
    def update_state(self, new_state: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Update the current dialog state.
        
        Args:
            new_state: New state to transition to
            context: Additional context for the state change
        """
        try:
            if isinstance(new_state, str):
                new_state_enum = DialogState(new_state)
            else:
                new_state_enum = new_state
                
            old_state = self.current_state
            self.current_state = new_state_enum
            
            logger.info(f"Dialog state changed: {old_state.value} -> {new_state_enum.value}")
            
            self._record_state_change(
                new_state_enum, 
                f"State changed from {old_state.value}",
                context
            )
            
        except ValueError as e:
            logger.error(f"Invalid dialog state: {new_state}")
            raise ValueError(f"Invalid dialog state: {new_state}")
    
    def get_current_state(self) -> DialogState:
        """
        Get the current dialog state.
        
        Returns:
            Current DialogState
        """
        return self.current_state
    
    def is_processing(self) -> bool:
        """
        Check if system is currently processing a request.
        
        Returns:
            True if processing, False otherwise
        """
        return self.current_state == DialogState.PROCESSING
    
    def can_accept_input(self) -> bool:
        """
        Check if system can accept new user input.
        
        Returns:
            True if can accept input, False otherwise
        """
        return self.current_state in [
            DialogState.WAITING_INPUT,
            DialogState.COMPLETED,
            DialogState.ERROR
        ]
    
    def record_user_interaction(self, interaction_type: str, data: Dict[str, Any]) -> None:
        """
        Record a user interaction.
        
        Args:
            interaction_type: Type of interaction (e.g., 'repository_input', 'button_click')
            data: Data associated with the interaction
        """
        interaction = {
            'type': interaction_type,
            'timestamp': time.time(),
            'data': data,
            'state_at_time': self.current_state.value
        }
        
        self.interaction_context['interactions'].append(interaction)
        logger.debug(f"Recorded interaction: {interaction_type}")
    
    def get_interaction_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of user interactions in current session.
        
        Returns:
            List of interaction records
        """
        return self.interaction_context.get('interactions', [])
    
    def get_state_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of state changes.
        
        Returns:
            List of state change records
        """
        return self.state_history
    
    def set_error_state(self, error_message: str, error_details: Optional[Dict[str, Any]] = None) -> None:
        """
        Set the dialog to error state with error information.
        
        Args:
            error_message: Human-readable error message
            error_details: Additional error details
        """
        logger.error(f"Setting error state: {error_message}")
        
        error_context = {
            'error_message': error_message,
            'error_details': error_details or {},
            'timestamp': time.time()
        }
        
        self.update_state(DialogState.ERROR, error_context)
    
    def clear_error(self) -> None:
        """Clear error state and return to waiting for input."""
        if self.current_state == DialogState.ERROR:
            logger.info("Clearing error state")
            self.update_state(DialogState.WAITING_INPUT, {'cleared_error': True})
    
    def get_suggested_actions(self) -> List[Dict[str, str]]:
        """
        Get suggested actions based on current state.
        
        Returns:
            List of suggested action dictionaries
        """
        suggestions = []
        
        if self.current_state == DialogState.WAITING_INPUT:
            suggestions = [
                {
                    'action': 'repository_analysis',
                    'label': 'Analyze Repository',
                    'description': 'Enter a repository URL to analyze'
                },
                {
                    'action': 'pr_review', 
                    'label': 'Review Pull Request',
                    'description': 'Review a specific Pull Request'
                },
                {
                    'action': 'code_qna',
                    'label': 'Ask Questions',
                    'description': 'Ask questions about your code'
                }
            ]
        elif self.current_state == DialogState.COMPLETED:
            suggestions = [
                {
                    'action': 'new_analysis',
                    'label': 'New Analysis',
                    'description': 'Start a new repository analysis'
                },
                {
                    'action': 'export_results',
                    'label': 'Export Results',
                    'description': 'Export analysis results'
                }
            ]
        elif self.current_state == DialogState.ERROR:
            suggestions = [
                {
                    'action': 'retry',
                    'label': 'Retry',
                    'description': 'Retry the last operation'
                },
                {
                    'action': 'start_over',
                    'label': 'Start Over',
                    'description': 'Start a new analysis'
                }
            ]
        
        return suggestions
    
    def get_progress_message(self) -> str:
        """
        Get current progress message based on state.
        
        Returns:
            Human-readable progress message
        """
        messages = {
            DialogState.WAITING_INPUT: "Ready for your input",
            DialogState.PROCESSING: "Processing your request...",
            DialogState.COMPLETED: "Analysis completed successfully",
            DialogState.ERROR: "An error occurred",
            DialogState.INTERRUPTED: "Processing was interrupted"
        }
        
        return messages.get(self.current_state, "Unknown state")
    
    def should_show_progress(self) -> bool:
        """
        Determine if progress indicator should be shown.
        
        Returns:
            True if progress should be shown
        """
        return self.current_state == DialogState.PROCESSING
    
    def should_show_results(self) -> bool:
        """
        Determine if results should be displayed.
        
        Returns:
            True if results should be shown
        """
        return self.current_state == DialogState.COMPLETED
    
    def estimate_remaining_time(self) -> Optional[int]:
        """
        Estimate remaining processing time in seconds.
        
        Returns:
            Estimated seconds remaining, or None if not applicable
        """
        if self.current_state != DialogState.PROCESSING:
            return None
        
        # This would be implemented based on actual processing metrics
        # For now, return a placeholder
        return None
    
    def _record_state_change(
        self, 
        new_state: DialogState, 
        reason: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a state change in the history.
        
        Args:
            new_state: The new state
            reason: Reason for the change
            context: Additional context
        """
        record = {
            'timestamp': time.time(),
            'state': new_state.value,
            'reason': reason,
            'context': context or {}
        }
        
        self.state_history.append(record)
        
        # Keep only last 50 state changes to prevent memory bloat
        if len(self.state_history) > 50:
            self.state_history = self.state_history[-50:]
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current session.
        
        Returns:
            Dictionary containing session summary
        """
        if not self.current_session_id:
            return {}
        
        total_interactions = len(self.interaction_context.get('interactions', []))
        session_duration = time.time() - self.interaction_context.get('start_time', time.time())
        
        return {
            'session_id': self.current_session_id,
            'duration_seconds': session_duration,
            'total_interactions': total_interactions,
            'current_state': self.current_state.value,
            'state_changes': len(self.state_history),
            'start_time': self.interaction_context.get('start_time'),
            'last_activity': max(
                [record['timestamp'] for record in self.state_history] + [time.time()]
            )
        } 