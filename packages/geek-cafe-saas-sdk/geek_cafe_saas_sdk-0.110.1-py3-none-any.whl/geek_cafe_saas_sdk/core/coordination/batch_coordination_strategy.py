"""
Batch coordination strategy for parallel batch execution.

This strategy coordinates completion of parallel batches by checking
batch record status. It's generic and can be used for any batch-based
parallel execution pattern (calculations, reports, data processing, etc.).
"""

from typing import Dict, Any, Protocol
from .coordination_strategy import CoordinationStrategy, CoordinationResult


class IBatchStatusService(Protocol):
    """
    Protocol for services that can check batch execution status.
    
    Implementations should provide a method to check how many batches
    have completed for a given execution.
    """
    
    def get_execution_status(self, execution_id: str) -> Any:
        """
        Get batch execution status.
        
        Args:
            execution_id: Execution ID to check
            
        Returns:
            Service result with status data including:
            - all_complete: bool
            - completed: int
            - total: int
        """
        ...


class BatchCoordinationStrategy:
    """
    Coordination strategy for parallel batch execution.
    
    This strategy checks batch record completion status and determines
    when all batches have finished executing. It's generic and works
    with any service that implements IBatchStatusService.
    
    Example:
        ```python
        # In orchestrator setup
        batch_strategy = BatchCoordinationStrategy(
            batch_service=batch_record_service
        )
        
        # When checking coordination
        result = batch_strategy.check_completion(
            execution_id="exec-123",
            coordination_metadata={"total_batches": 5},
            context=request_context
        )
        
        if result.is_complete:
            # All batches done - dispatch dependent steps
            dispatch_dependents()
        else:
            # Still waiting - return message to queue
            # SQS visibility timeout will retry later
            return message_to_queue()
        ```
    """
    
    def __init__(self, batch_service: IBatchStatusService):
        """
        Initialize batch coordination strategy.
        
        Args:
            batch_service: Service that can check batch status
        """
        self.batch_service = batch_service
    
    def check_completion(
        self,
        execution_id: str,
        coordination_metadata: Dict[str, Any],
        context: Any,
    ) -> CoordinationResult:
        """
        Check if all batches are complete.
        
        Args:
            execution_id: Execution ID to check
            coordination_metadata: Must contain 'total_batches' key
            context: Request context (unused but required by protocol)
            
        Returns:
            CoordinationResult with completion status
        """
        try:
            # Get expected total from metadata
            expected_total = coordination_metadata.get("total_batches", 0)
            
            # Check batch status
            status_result = self.batch_service.get_execution_status(execution_id)
            
            if not status_result.success:
                return CoordinationResult(
                    is_complete=False,
                    completed_count=0,
                    total_count=expected_total,
                    error=f"Failed to check batch status: {status_result.message}"
                )
            
            status = status_result.data
            completed = status.get("completed", 0)
            total = status.get("total", expected_total)
            all_complete = status.get("all_complete", False)
            
            return CoordinationResult(
                is_complete=all_complete,
                completed_count=completed,
                total_count=total,
                metadata={
                    "failed": status.get("failed", 0),
                    "pending": status.get("pending", 0),
                }
            )
            
        except Exception as e:
            return CoordinationResult(
                is_complete=False,
                completed_count=0,
                total_count=coordination_metadata.get("total_batches", 0),
                error=f"Exception checking batch completion: {str(e)}"
            )
    
    def get_coordination_type(self) -> str:
        """Get coordination type identifier."""
        return "batches"
