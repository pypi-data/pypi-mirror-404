"""
Counter-based coordination strategy using atomic counters.

This strategy uses CoordinationService with atomic counters instead of
scanning batch records. Provides O(1) completion checking.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any, Protocol
from .coordination_strategy import CoordinationStrategy, CoordinationResult


class ICoordinationService(Protocol):
    """
    Protocol for services that provide coordination status.
    
    Implementations should provide a method to check coordination status
    using atomic counters.
    """
    
    def get_status(self, execution_id: str, step_type: str) -> Any:
        """
        Get coordination status.
        
        Args:
            execution_id: Execution ID to check
            step_type: Step type being coordinated
            
        Returns:
            Service result with status data including:
            - is_complete: bool
            - is_finalized: bool
            - has_failures: bool
            - completed: int
            - failed: int
            - total: int
            - pending: int
            - progress_percentage: float
        """
        ...


class CounterCoordinationStrategy:
    """
    Coordination strategy using atomic counters.
    
    This strategy checks coordination status using atomic counters
    instead of scanning all items. Provides O(1) completion checking
    that scales to millions of items.
    
    Example:
        ```python
        # In orchestrator setup
        counter_strategy = CounterCoordinationStrategy(
            coordination_service=coordination_service
        )
        
        # When checking coordination
        result = counter_strategy.check_completion(
            execution_id="exec-123",
            coordination_metadata={"step_type": "calculation"},
            context=request_context
        )
        
        if result.is_complete:
            # All items done - dispatch dependent steps
            dispatch_dependents()
        else:
            # Still waiting - return message to queue
            # SQS visibility timeout will retry later
            return message_to_queue()
        ```
    """
    
    def __init__(self, coordination_service: ICoordinationService):
        """
        Initialize counter coordination strategy.
        
        Args:
            coordination_service: Service that provides coordination status
        """
        self.coordination_service = coordination_service
    
    def check_completion(
        self,
        execution_id: str,
        coordination_metadata: Dict[str, Any],
        context: Any,
    ) -> CoordinationResult:
        """
        Check if coordination is complete using atomic counters.
        
        This is an O(1) operation that reads a single coordination record
        instead of scanning all items.
        
        Args:
            execution_id: Execution ID to check
            coordination_metadata: Must contain 'step_type' key
            context: Request context (unused but required by protocol)
            
        Returns:
            CoordinationResult with completion status
        """
        try:
            # Get step type from metadata
            step_type = coordination_metadata.get("step_type")
            if not step_type:
                return CoordinationResult(
                    is_complete=False,
                    completed_count=0,
                    total_count=0,
                    error="Missing step_type in coordination_metadata"
                )
            
            # Get coordination status (O(1) lookup!)
            status_result = self.coordination_service.get_status(execution_id, step_type)
            
            if not status_result.success:
                return CoordinationResult(
                    is_complete=False,
                    completed_count=0,
                    total_count=0,
                    error=f"Failed to check coordination status: {status_result.message}"
                )
            
            status = status_result.data
            
            # Check if finalized yet
            if not status.get("is_finalized"):
                return CoordinationResult(
                    is_complete=False,
                    completed_count=status.get("completed", 0),
                    total_count=0,
                    metadata={
                        "status": "streaming",
                        "message": "Still streaming items, total not yet known"
                    }
                )
            
            # Check for failures
            if status.get("has_failures"):
                return CoordinationResult(
                    is_complete=True,
                    completed_count=status.get("completed", 0),
                    total_count=status.get("total", 0),
                    error=f"Coordination failed: {status.get('failed', 0)} items failed",
                    metadata={
                        "failed": status.get("failed", 0),
                        "error_message": status.get("error_message")
                    }
                )
            
            # Check if complete
            is_complete = status.get("is_complete", False)
            completed = status.get("completed", 0)
            total = status.get("total", 0)
            
            return CoordinationResult(
                is_complete=is_complete,
                completed_count=completed,
                total_count=total,
                metadata={
                    "pending": status.get("pending", 0),
                    "progress_percentage": status.get("progress_percentage", 0.0),
                    "status": status.get("status")
                }
            )
            
        except Exception as e:
            return CoordinationResult(
                is_complete=False,
                completed_count=0,
                total_count=0,
                error=f"Exception checking coordination: {str(e)}"
            )
    
    def get_coordination_type(self) -> str:
        """Get coordination type identifier."""
        return "counter"
