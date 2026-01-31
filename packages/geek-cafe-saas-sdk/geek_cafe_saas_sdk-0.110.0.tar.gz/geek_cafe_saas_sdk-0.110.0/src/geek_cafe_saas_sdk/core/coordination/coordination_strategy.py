"""
Generic coordination strategy interface for distributed workflow steps.

This module defines the protocol for coordinating parallel work execution.
Implementations can check completion status for batches, child workflows,
or any custom parallel execution pattern.
"""

from typing import Protocol, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class CoordinationResult:
    """Result of a coordination check."""
    
    is_complete: bool
    """Whether all parallel work is complete."""
    
    completed_count: int = 0
    """Number of completed items."""
    
    total_count: int = 0
    """Total number of items to complete."""
    
    metadata: Optional[Dict[str, Any]] = None
    """Additional coordination metadata."""
    
    error: Optional[str] = None
    """Error message if coordination check failed."""
    
    @property
    def success(self) -> bool:
        """Whether the coordination check succeeded (no errors)."""
        return self.error is None
    
    @property
    def progress_percentage(self) -> float:
        """Progress as a percentage (0-100)."""
        if self.total_count == 0:
            return 0.0
        return (self.completed_count / self.total_count) * 100


class CoordinationStrategy(Protocol):
    """
    Protocol for coordination strategies that check parallel work completion.
    
    Implementations should be stateless and injectable, allowing different
    coordination mechanisms (batch records, child executions, custom polling)
    to be used interchangeably.
    
    Example:
        ```python
        class MyBatchStrategy:
            def check_completion(
                self, 
                execution_id: str, 
                coordination_metadata: Dict[str, Any],
                context: RequestContext
            ) -> CoordinationResult:
                # Check if all batches are complete
                total = coordination_metadata["total_batches"]
                completed = self.batch_service.count_completed(execution_id)
                
                return CoordinationResult(
                    is_complete=(completed == total),
                    completed_count=completed,
                    total_count=total
                )
        ```
    """
    
    def check_completion(
        self,
        execution_id: str,
        coordination_metadata: Dict[str, Any],
        context: Any,  # RequestContext, but avoid circular import
    ) -> CoordinationResult:
        """
        Check if all parallel work is complete.
        
        Args:
            execution_id: Execution ID to check
            coordination_metadata: Metadata from coordination event (e.g., total_batches)
            context: Request context for accessing services
            
        Returns:
            CoordinationResult with completion status and progress
        """
        ...
    
    def get_coordination_type(self) -> str:
        """
        Get the coordination type identifier.
        
        Returns:
            Type identifier (e.g., "batches", "child_executions")
        """
        ...
