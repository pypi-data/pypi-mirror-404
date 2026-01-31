"""
WorkflowHistoryService for managing execution history entries.

Provides methods for creating and querying execution history records.
History entries are append-only and immutable.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, UTC

from aws_lambda_powertools import Logger
from boto3_assist.dynamodb.dynamodb import DynamoDB

from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
from geek_cafe_saas_sdk.core.request_context import RequestContext
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from ..models.workflow_history import WorkflowHistory, WorkflowHistoryEventType

logger = Logger()


class WorkflowHistoryService(DatabaseService[WorkflowHistory]):
    """
    Service for managing execution history entries.
    
    History entries are append-only - once created, they cannot be modified or deleted.
    This provides an immutable audit trail of execution state changes.
    """

    def __init__(
        self,
        *,
        dynamodb: Optional[DynamoDB] = None,
        table_name: Optional[str] = None,
        request_context: Optional[RequestContext] = None,        
        **kwargs
    ):
        super().__init__(
            dynamodb=dynamodb,
            table_name=table_name,
            request_context=request_context,
            **kwargs
        )

    # =========================================================================
    # Create Operations
    # =========================================================================

    @service_method("create_execution_history")
    def create(
        self,
        execution_id: str,
        event_type: str,
        from_status: Optional[str] = None,
        to_status: Optional[str] = None,
        step_name: Optional[str] = None,
        step_index: Optional[int] = None,
        progress_percent: Optional[int] = None,
        message: Optional[str] = None,
        duration_ms: Optional[int] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        actor: Optional[str] = None,
        actor_type: Optional[str] = None,
    ) -> ServiceResult[WorkflowHistory]:
        """
        Create a new execution history entry.
        
        Args:
            execution_id: ID of the execution this history belongs to
            event_type: Type of event (created, started, progress, etc.)
            from_status: Previous status before this event
            to_status: New status after this event
            step_name: Name of the step (for step events)
            step_index: Index of the step (0-based)
            progress_percent: Progress percentage at time of event
            message: Human-readable message
            duration_ms: Time spent in previous state (milliseconds)
            error_code: Error code (for failed events)
            error_message: Error message (for failed events)
            error_details: Additional error details
            metadata: Event-specific metadata
            actor: ID of the actor who triggered this event
            actor_type: Type of actor (user, system, lambda, etc.)
            
        Returns:
            ServiceResult with created WorkflowHistory
        """
        try:
            history = WorkflowHistory()
            
            # Generate ordering keys (timestamp + uuid suffix)
            history.generate_ordering_keys()
            history.id = history.history_id
            
            # Core fields
            history.execution_id = execution_id
            history.event_type = event_type
            
            # State transition
            history.from_status = from_status
            history.to_status = to_status
            
            # Step tracking
            history.step_name = step_name
            history.step_index = step_index
            history.progress_percent = progress_percent
            
            # Message and duration
            history.message = message
            history.duration_ms = duration_ms
            
            # Error details
            history.error_code = error_code
            history.error_message = error_message
            history.error_details = error_details
            
            # Metadata
            history.metadata = metadata
            
            # Actor
            history.actor = actor or (self.request_context.authenticated_user_id if self.request_context else None)
            history.actor_type = actor_type or "user"
            
            # Inject security context from request
            if self.request_context:
                history.tenant_id = self.request_context.authenticated_tenant_id
                history.owner_id = self.request_context.authenticated_user_id
                history.user_id = self.request_context.authenticated_user_id
            
            # Save
            history.prep_for_save()
            result = self._save_model(history)
            
            return result
            
        except Exception as e:
            logger.exception(f"Error creating execution history: {e}")
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.INTERNAL_ERROR
            )

    # =========================================================================
    # Convenience Methods for Common Events
    # =========================================================================

    def record_created(
        self,
        execution_id: str,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ServiceResult[WorkflowHistory]:
        """Record an execution created event."""
        return self.create(
            execution_id=execution_id,
            event_type=WorkflowHistoryEventType.CREATED,
            to_status="pending",
            message=message or "Execution created",
            metadata=metadata,
        )

    def record_started(
        self,
        execution_id: str,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ServiceResult[WorkflowHistory]:
        """Record an execution started event."""
        return self.create(
            execution_id=execution_id,
            event_type=WorkflowHistoryEventType.STARTED,
            from_status="pending",
            to_status="running",
            message=message or "Execution started",
            metadata=metadata,
        )

    def record_progress(
        self,
        execution_id: str,
        progress_percent: int,
        current_step: Optional[str] = None,
        step_index: Optional[int] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ServiceResult[WorkflowHistory]:
        """Record an execution progress event."""
        return self.create(
            execution_id=execution_id,
            event_type=WorkflowHistoryEventType.PROGRESS,
            progress_percent=progress_percent,
            step_name=current_step,
            step_index=step_index,
            message=message or f"Progress: {progress_percent}%",
            metadata=metadata,
        )

    def record_step_started(
        self,
        execution_id: str,
        step_name: str,
        step_index: Optional[int] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ServiceResult[WorkflowHistory]:
        """Record a step started event."""
        return self.create(
            execution_id=execution_id,
            event_type=WorkflowHistoryEventType.STEP_STARTED,
            step_name=step_name,
            step_index=step_index,
            message=message or f"Step started: {step_name}",
            metadata=metadata,
        )

    def record_step_completed(
        self,
        execution_id: str,
        step_name: str,
        step_index: Optional[int] = None,
        duration_ms: Optional[int] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ServiceResult[WorkflowHistory]:
        """Record a step completed event."""
        return self.create(
            execution_id=execution_id,
            event_type=WorkflowHistoryEventType.STEP_COMPLETED,
            step_name=step_name,
            step_index=step_index,
            duration_ms=duration_ms,
            message=message or f"Step completed: {step_name}",
            metadata=metadata,
        )

    def record_step_failed(
        self,
        execution_id: str,
        step_name: str,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        step_index: Optional[int] = None,
        duration_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ServiceResult[WorkflowHistory]:
        """Record a step failed event."""
        return self.create(
            execution_id=execution_id,
            event_type=WorkflowHistoryEventType.STEP_FAILED,
            step_name=step_name,
            step_index=step_index,
            duration_ms=duration_ms,
            error_code=error_code,
            error_message=error_message,
            error_details=error_details,
            message=f"Step failed: {step_name} - {error_message or 'Unknown error'}",
            metadata=metadata,
        )

    def record_succeeded(
        self,
        execution_id: str,
        duration_ms: Optional[int] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ServiceResult[WorkflowHistory]:
        """Record an execution succeeded event."""
        return self.create(
            execution_id=execution_id,
            event_type=WorkflowHistoryEventType.SUCCEEDED,
            from_status="running",
            to_status="succeeded",
            duration_ms=duration_ms,
            message=message or "Execution succeeded",
            metadata=metadata,
        )

    def record_failed(
        self,
        execution_id: str,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ServiceResult[WorkflowHistory]:
        """Record an execution failed event."""
        return self.create(
            execution_id=execution_id,
            event_type=WorkflowHistoryEventType.FAILED,
            from_status="running",
            to_status="failed",
            duration_ms=duration_ms,
            error_code=error_code,
            error_message=error_message,
            error_details=error_details,
            message=f"Execution failed: {error_message or 'Unknown error'}",
            metadata=metadata,
        )

    def record_cancelled(
        self,
        execution_id: str,
        duration_ms: Optional[int] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ServiceResult[WorkflowHistory]:
        """Record an execution cancelled event."""
        return self.create(
            execution_id=execution_id,
            event_type=WorkflowHistoryEventType.CANCELLED,
            from_status="running",
            to_status="cancelled",
            duration_ms=duration_ms,
            message=message or "Execution cancelled",
            metadata=metadata,
        )

    def record_retried(
        self,
        execution_id: str,
        retry_count: int,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ServiceResult[WorkflowHistory]:
        """Record an execution retry event."""
        return self.create(
            execution_id=execution_id,
            event_type=WorkflowHistoryEventType.RETRIED,
            from_status="failed",
            to_status="pending",
            message=message or f"Execution retried (attempt {retry_count})",
            metadata={"retry_count": retry_count, **(metadata or {})},
        )

    # =========================================================================
    # Read Operations
    # =========================================================================

    @service_method("list_execution_history")
    def list_by_execution(
        self,
        execution_id: str,
        limit: int = 100,
        ascending: bool = True,
    ) -> ServiceResult[List[WorkflowHistory]]:
        """
        List all history entries for an execution.
        
        Args:
            execution_id: ID of the execution
            limit: Maximum results (default: 100)
            ascending: Sort order by timestamp (default: True = oldest first)
            
        Returns:
            ServiceResult with list of WorkflowHistory entries
        """
        try:
            # Create query model with execution_id set
            query_model = WorkflowHistory()
            query_model.execution_id = execution_id
            
            # Get key for primary index with begins_with condition on sort key
            key = query_model.get_key("primary").key(query_key=True, condition="begins_with")
            
            # Execute query
            response = self.dynamodb.query(
                table_name=self.table_name,
                key=key,
                ascending=ascending,
                limit=limit,
            )
            
            # Map items to models
            items = response.get("Items", [])
            histories = [WorkflowHistory().map(item) for item in items]
            
            return ServiceResult.success_result(histories)
            
        except Exception as e:
            logger.exception(f"Error listing execution history: {e}")
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.INTERNAL_ERROR
            )

    @service_method("list_history_by_event_type")
    def list_by_event_type(
        self,
        event_type: str,
        limit: int = 50,
        ascending: bool = False,
    ) -> ServiceResult[List[WorkflowHistory]]:
        """
        List history entries by event type for the current user.
        
        Args:
            event_type: Type of event to filter by
            limit: Maximum results
            ascending: Sort order by timestamp
            
        Returns:
            ServiceResult with list of WorkflowHistory entries
        """
        try:
            user_id = self.request_context.authenticated_user_id
            tenant_id = self.request_context.authenticated_tenant_id
            
            query_model = WorkflowHistory()
            query_model.tenant_id = tenant_id
            query_model.owner_id = user_id
            query_model.event_type = event_type
            
            return self._query_by_index(
                query_model, "gsi2", limit=limit, ascending=ascending
            )
            
        except Exception as e:
            logger.exception(f"Error listing history by event type: {e}")
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.INTERNAL_ERROR
            )

    @service_method("get_latest_history")
    def get_latest(
        self,
        execution_id: str,
    ) -> ServiceResult[WorkflowHistory]:
        """
        Get the most recent history entry for an execution.
        
        Args:
            execution_id: ID of the execution
            
        Returns:
            ServiceResult with latest WorkflowHistory entry
        """
        try:
            result = self.list_by_execution(execution_id, limit=1, ascending=False)
            
            if not result.success:
                return result
            
            if not result.data:
                return ServiceResult.error_result(
                    message=f"No history found for execution {execution_id}",
                    error_code=ErrorCode.NOT_FOUND
                )
            
            return ServiceResult.success_result(result.data[0])
            
        except Exception as e:
            logger.exception(f"Error getting latest history: {e}")
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.INTERNAL_ERROR
            )

    # =========================================================================
    # Abstract Method Implementations (required by DatabaseService)
    # =========================================================================

    def get_by_id(self, **kwargs) -> ServiceResult[WorkflowHistory]:
        """
        Get history entry by ID.
        
        Note: History entries are typically queried by execution_id, not individual ID.
        This method is provided for interface compliance.
        """
        history_id = kwargs.get("history_id") or kwargs.get("id")
        execution_id = kwargs.get("execution_id")
        
        if not execution_id:
            return ServiceResult.error_result(
                message="execution_id is required to get history entry",
                error_code=ErrorCode.VALIDATION_ERROR
            )
        
        # Query all history for execution and find matching entry
        result = self.list_by_execution(execution_id)
        if not result.success:
            return result
        
        for entry in result.data:
            if entry.history_id == history_id:
                return ServiceResult.success_result(entry)
        
        return ServiceResult.error_result(
            message=f"History entry {history_id} not found",
            error_code=ErrorCode.NOT_FOUND
        )

    def update(self, **kwargs) -> ServiceResult[WorkflowHistory]:
        """
        Update is not supported for history entries.
        
        History entries are immutable once created.
        """
        return ServiceResult.error_result(
            message="History entries are immutable and cannot be updated",
            error_code=ErrorCode.VALIDATION_ERROR
        )

    def delete(self, **kwargs) -> ServiceResult[bool]:
        """
        Delete is not supported for history entries.
        
        History entries are immutable and cannot be deleted.
        """
        return ServiceResult.error_result(
            message="History entries are immutable and cannot be deleted",
            error_code=ErrorCode.VALIDATION_ERROR
        )
