"""
WorkflowStepService for managing workflow steps within executions.

Provides CRUD operations and query methods for tracking steps,
including dependency resolution and dispatching logic.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import time
import uuid
from datetime import datetime, UTC
from typing import Optional, Dict, Any, List

from aws_lambda_powertools import Logger
from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3_assist.dynamodb.dynamodb_key import DynamoDBKey

from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
from geek_cafe_saas_sdk.core.request_context import RequestContext
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from ..models.workflow_step import WorkflowStep, StepStatus

logger = Logger()


class WorkflowStepService(DatabaseService[WorkflowStep]):
    """
    Service for managing workflow steps.
    
    Provides methods for creating, updating, and querying steps
    with support for dependency tracking and status management.
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

    @service_method("create_step")
    def create(
        self,
        execution_id: str,
        step_type: str,
        step_id: Optional[str] = None,
        step_name: Optional[str] = None,
        step_index: int = 0,
        depends_on: Optional[List[str]] = None,
        queue_name: Optional[str] = None,
        queue_url: Optional[str] = None,
        input_payload: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
        max_retries: int = 3,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ServiceResult[WorkflowStep]:
        """
        Create a new workflow step.
        
        Args:
            execution_id: Parent execution ID
            step_type: Type of step (e.g., 'data_cleaning', 'calculation')
            step_id: Optional step ID (auto-generated if not provided)
            step_name: Human-readable step name
            step_index: Order in the workflow (0-based)
            depends_on: List of step_ids this step depends on
            queue_name: Queue name for this step
            queue_url: SQS queue URL
            input_payload: Input data for the step
            timeout_seconds: Timeout for this step
            max_retries: Maximum retry attempts
            metadata: Additional metadata
            
        Returns:
            ServiceResult containing the created step
        """
        result = ServiceResult(success=True)
        
        step = WorkflowStep()
        step.id = step_id or f"{execution_id}:{step_type}:{uuid.uuid4().hex[:8]}"
        step.step_id = step.id
        step.execution_id = execution_id
        step.step_type = step_type
        step.step_name = step_name or step_type
        step.step_index = step_index
        step.depends_on = depends_on or []
        step.queue_name = queue_name
        step.queue_url = queue_url
        step.input_payload = input_payload
        step.timeout_seconds = timeout_seconds
        step.max_retries = max_retries
        step.metadata = metadata
        step.status = StepStatus.PENDING
        
        # Set tenant/owner from context
        if self.request_context:
            step.tenant_id = self.request_context.authenticated_tenant_id            
            step.user_id = self.request_context.authenticated_user_id
        
        save_result = self._save_model(step)
        if not save_result.success:
            return ServiceResult.error_result(save_result.message, save_result.error_code)
        
        result.data = save_result.data
        return result

    # =========================================================================
    # Update Operations
    # =========================================================================

    @service_method("dispatch_step")
    def dispatch(
        self,
        step_id: str,
        execution_id: str,
        message_id: Optional[str] = None,
    ) -> ServiceResult[WorkflowStep]:
        """
        Mark a step as dispatched to its queue.
        
        Args:
            step_id: Step ID
            execution_id: Parent execution ID
            message_id: SQS message ID
            
        Returns:
            ServiceResult containing the updated step
        """
        result = ServiceResult(success=True)
        
        get_result = self.get(step_id, execution_id)
        if not get_result.success or not get_result.data:
            return ServiceResult.error_result(f"Step {step_id} not found", ErrorCode.NOT_FOUND)
        
        step = get_result.data
        
        if not StepStatus.can_transition(step.status, StepStatus.DISPATCHED):
            return ServiceResult.error_result(f"Cannot dispatch step in status {step.status}"
            , 
                ErrorCode.INVALID_STATE)
        
        now = datetime.now(UTC)
        step.status = StepStatus.DISPATCHED
        step.dispatched_utc = now.isoformat()
        step.dispatched_utc_ts = now.timestamp()
        step.message_id = message_id
        
        save_result = self._save_model(step)
        if not save_result.success:
            return ServiceResult.error_result(save_result.message, save_result.error_code)
        
        result.data = save_result.data
        return result

    @service_method("start_step")
    def start(
        self,
        step_id: str,
        execution_id: str,
    ) -> ServiceResult[WorkflowStep]:
        """
        Mark a step as started (running).
        
        Args:
            step_id: Step ID
            execution_id: Parent execution ID
            
        Returns:
            ServiceResult containing the updated step
        """
        result = ServiceResult(success=True)
        
        get_result = self.get(step_id, execution_id)
        if not get_result.success or not get_result.data:
            return ServiceResult.error_result(f"Step {step_id} not found", ErrorCode.NOT_FOUND)
        
        step = get_result.data
        
        if not StepStatus.can_transition(step.status, StepStatus.RUNNING):
            return ServiceResult.error_result(f"Cannot start step in status {step.status}"
            , 
                ErrorCode.INVALID_STATE)
        
        now = datetime.now(UTC)
        step.status = StepStatus.RUNNING
        step.started_utc = now.isoformat()
        step.started_utc_ts = now.timestamp()
        
        save_result = self._save_model(step)
        if not save_result.success:
            return ServiceResult.error_result(save_result.message, save_result.error_code)
        
        result.data = save_result.data
        return result

    @service_method("complete_step")
    def complete(
        self,
        step_id: str,
        execution_id: str,
        output_payload: Optional[Dict[str, Any]] = None,
    ) -> ServiceResult[WorkflowStep]:
        """
        Mark a step as completed successfully.
        
        Args:
            step_id: Step ID
            execution_id: Parent execution ID
            output_payload: Output data from the step
            
        Returns:
            ServiceResult containing the updated step
        """
        result = ServiceResult(success=True)
        
        get_result = self.get(step_id, execution_id)
        if not get_result.success or not get_result.data:
            return ServiceResult.error_result(f"Step {step_id} not found", ErrorCode.NOT_FOUND)
        
        step = get_result.data
        
        if not StepStatus.can_transition(step.status, StepStatus.COMPLETED):
            return ServiceResult.error_result(f"Cannot complete step in status {step.status}"
            , 
                ErrorCode.INVALID_STATE)
        
        now = datetime.now(UTC)
        step.status = StepStatus.COMPLETED
        step.completed_utc = now.isoformat()
        step.completed_utc_ts = now.timestamp()
        step.output_payload = output_payload
        
        # Calculate duration
        if step.started_utc_ts:
            step.duration_ms = int((now.timestamp() - step.started_utc_ts) * 1000)
        
        save_result = self._save_model(step)
        if not save_result.success:
            return ServiceResult.error_result(save_result.message, save_result.error_code)
        
        result.data = save_result.data
        return result

    @service_method("fail_step")
    def fail(
        self,
        step_id: str,
        execution_id: str,
        error_message: str,
        error_code: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> ServiceResult[WorkflowStep]:
        """
        Mark a step as failed.
        
        Args:
            step_id: Step ID
            execution_id: Parent execution ID
            error_message: Error message
            error_code: Error code
            error_details: Additional error details
            
        Returns:
            ServiceResult containing the updated step
        """
        result = ServiceResult(success=True)
        
        get_result = self.get(step_id, execution_id)
        if not get_result.success or not get_result.data:
            return ServiceResult.error_result(f"Step {step_id} not found", ErrorCode.NOT_FOUND)
        
        step = get_result.data
        
        if not StepStatus.can_transition(step.status, StepStatus.FAILED):
            return ServiceResult.error_result(f"Cannot fail step in status {step.status}"
            , 
                ErrorCode.INVALID_STATE)
        
        now = datetime.now(UTC)
        step.status = StepStatus.FAILED
        step.completed_utc = now.isoformat()
        step.completed_utc_ts = now.timestamp()
        step.error_message = error_message
        step.error_code = error_code
        step.error_details = error_details
        
        # Calculate duration
        if step.started_utc_ts:
            step.duration_ms = int((now.timestamp() - step.started_utc_ts) * 1000)
        
        save_result = self._save_model(step)
        if not save_result.success:
            return ServiceResult.error_result(save_result.message, save_result.error_code)
        
        result.data = save_result.data
        return result

    @service_method("skip_step")
    def skip(
        self,
        step_id: str,
        execution_id: str,
        reason: Optional[str] = None,
    ) -> ServiceResult[WorkflowStep]:
        """
        Mark a step as skipped.
        
        Args:
            step_id: Step ID
            execution_id: Parent execution ID
            reason: Reason for skipping
            
        Returns:
            ServiceResult containing the updated step
        """
        result = ServiceResult(success=True)
        
        get_result = self.get(step_id, execution_id)
        if not get_result.success or not get_result.data:
            return ServiceResult.error_result(f"Step {step_id} not found", ErrorCode.NOT_FOUND)
        
        step = get_result.data
        
        if not StepStatus.can_transition(step.status, StepStatus.SKIPPED):
            return ServiceResult.error_result(f"Cannot skip step in status {step.status}"
            , 
                ErrorCode.INVALID_STATE)
        
        now = datetime.now(UTC)
        step.status = StepStatus.SKIPPED
        step.completed_utc = now.isoformat()
        step.completed_utc_ts = now.timestamp()
        if reason:
            step.metadata = step.metadata or {}
            step.metadata["skip_reason"] = reason
        
        save_result = self._save_model(step)
        if not save_result.success:
            return ServiceResult.error_result(save_result.message, save_result.error_code)
        
        result.data = save_result.data
        return result

    @service_method("cancel_step")
    def cancel(
        self,
        step_id: str,
        execution_id: str,
        reason: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> ServiceResult[WorkflowStep]:
        """
        Mark a step as cancelled.
        
        Used when a step cannot proceed due to failed dependencies or
        other workflow-level issues. Unlike fail(), this is for steps
        that never started execution.
        
        Args:
            step_id: Step ID
            execution_id: Parent execution ID
            reason: Reason for cancellation
            error_code: Optional error code
            
        Returns:
            ServiceResult containing the updated step
        """
        result = ServiceResult(success=True)
        
        get_result = self.get(step_id, execution_id)
        if not get_result.success or not get_result.data:
            return ServiceResult.error_result(f"Step {step_id} not found", ErrorCode.NOT_FOUND)
        
        step = get_result.data
        
        if not StepStatus.can_transition(step.status, StepStatus.CANCELLED):
            return ServiceResult.error_result(f"Cannot cancel step in status {step.status}"
            , 
                ErrorCode.INVALID_STATE)
        
        now = datetime.now(UTC)
        step.status = StepStatus.CANCELLED
        step.completed_utc = now.isoformat()
        step.completed_utc_ts = now.timestamp()
        
        if reason:
            step.error_message = reason
        if error_code:
            step.error_code = error_code
        
        # Store cancellation details in metadata
        step.metadata = step.metadata or {}
        step.metadata["cancelled_utc_ts"] = now.isoformat()
        if reason:
            step.metadata["cancellation_reason"] = reason
        
        save_result = self._save_model(step)
        if not save_result.success:
            return ServiceResult.error_result(save_result.message, save_result.error_code)
        
        result.data = save_result.data
        return result

    # =========================================================================
    # Query Operations
    # =========================================================================

    @service_method("get_step")
    def get(
        self,
        step_id: str,
        execution_id: str,
    ) -> ServiceResult[WorkflowStep]:
        """
        Get a step by ID.
        
        Args:
            step_id: Step ID
            execution_id: Parent execution ID
            
        Returns:
            ServiceResult containing the step
        """
        result = ServiceResult(success=True)
        
        step = WorkflowStep()
        step.execution_id = execution_id
        step.id = step_id
                
        item = self.dynamodb.get(
            table_name=self.table_name,
            model=step,
        )
        
        if not item:
            return ServiceResult.error_result(f"Step {step_id} not found", ErrorCode.NOT_FOUND)
        
        result.data = step.map(item)
        return result

    @service_method("get_steps_for_execution")
    def get_steps_for_execution(
        self,
        execution_id: str,
        status: Optional[str] = None,
    ) -> ServiceResult[List[WorkflowStep]]:
        """
        Get all steps for an execution.
        
        Args:
            execution_id: Execution ID
            status: Optional status filter
            
        Returns:
            ServiceResult containing list of steps
        """
        result = ServiceResult(success=True)
        
        step: WorkflowStep = WorkflowStep()
        step.execution_id = execution_id
        step.status = status
        response = self._query_by_index(
                model=step,
                index_name="gsi1",                
            )
        
        if not response.success:
            return ServiceResult.error_result(response.message, response.error_code)
        
        items = response.data

        steps = [WorkflowStep().map(item) for item in items]
        
        # Sort by step_index, treating None as infinity (sorted to end)
        steps.sort(key=lambda s: s.step_index if s.step_index is not None else float('inf'))
        
        result.data = steps
        return result

    @service_method("get_pending_steps")
    def get_pending_steps(
        self,
        execution_id: str,
    ) -> ServiceResult[List[WorkflowStep]]:
        """
        Get all pending steps for an execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            ServiceResult containing list of pending steps
        """
        return self.get_steps_for_execution(execution_id, status=StepStatus.PENDING)

    @service_method("get_dispatchable_steps")
    def get_dispatchable_steps(
        self,
        execution_id: str,
    ) -> ServiceResult[List[WorkflowStep]]:
        """
        Get steps that are ready to be dispatched.
        
        A step is dispatchable if:
        - Status is PENDING
        - All dependencies are in a success state (COMPLETED or SKIPPED)
        
        Args:
            execution_id: Execution ID
            
        Returns:
            ServiceResult containing list of dispatchable steps
        """
        result = ServiceResult(success=True)
        
        # Get all steps for the execution
        all_steps_result = self.get_steps_for_execution(execution_id)
        if not all_steps_result.success:
            return ServiceResult.error_result(all_steps_result.error_message, all_steps_result.error_code)
        
        all_steps = all_steps_result.data or []
        
        # Build status map
        status_map = {step.step_id: step.status for step in all_steps}
        
        dispatchable = []
        for step in all_steps:
            if step.status != StepStatus.PENDING:
                continue
            
            # Check if all dependencies are satisfied
            all_deps_satisfied = True
            for dep_id in step.depends_on:
                dep_status = status_map.get(dep_id)
                if not dep_status or not StepStatus.is_success(dep_status):
                    all_deps_satisfied = False
                    break
            
            if all_deps_satisfied:
                dispatchable.append(step)
        
        result.data = dispatchable
        return result

    @service_method("check_execution_complete")
    def is_execution_complete(
        self,
        execution_id: str,
    ) -> ServiceResult[bool]:
        """
        Check if all steps in an execution are complete.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            ServiceResult containing True if all steps are terminal
        """
        result = ServiceResult(success=True)
        
        all_steps_result = self.get_steps_for_execution(execution_id)
        if not all_steps_result.success:
            return ServiceResult.error_result(all_steps_result.error_message, all_steps_result.error_code)
        
        all_steps = all_steps_result.data or []
        
        if not all_steps:
            result.data = True
            return result
        
        all_terminal = all(StepStatus.is_terminal(step.status) for step in all_steps)
        result.data = all_terminal
        return result

    @service_method("check_execution_failed")
    def has_execution_failed(
        self,
        execution_id: str,
    ) -> ServiceResult[bool]:
        """
        Check if any step in an execution has failed.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            ServiceResult containing True if any step failed
        """
        result = ServiceResult(success=True)
        
        all_steps_result = self.get_steps_for_execution(execution_id)
        if not all_steps_result.success:
            return ServiceResult.error_result(all_steps_result.error_message, all_steps_result.error_code)
        
        all_steps = all_steps_result.data or []
        
        any_failed = any(step.status == StepStatus.FAILED for step in all_steps)
        result.data = any_failed
        return result

    # =========================================================================
    # Abstract Method Implementations (required by DatabaseService)
    # =========================================================================

    def get_by_id(
        self, resource_id: str, tenant_id: str, user_id: str
    ) -> ServiceResult[WorkflowStep]:
        """Get step by ID with access control."""
        result = ServiceResult(success=True)
        
        # Extract step_id and execution_id from resource_id
        # Format: execution_id:step_type or full step_id
        parts = resource_id.split(":")
        if len(parts) < 2:
            return ServiceResult.error_result(f"Invalid step ID format: {resource_id}", ErrorCode.INVALID_INPUT)
        
        execution_id = parts[0]
        step_id = resource_id
        
        return self.get(step_id, execution_id)

    def update(
        self, resource_id: str, tenant_id: str, user_id: str, updates: Dict[str, Any]
    ) -> ServiceResult[WorkflowStep]:
        """Update step with access control."""
        result = ServiceResult(success=True)
        
        # Extract execution_id from resource_id
        parts = resource_id.split(":")
        if len(parts) < 2:
            return ServiceResult.error_result(f"Invalid step ID format: {resource_id}", ErrorCode.INVALID_INPUT)
        
        execution_id = parts[0]
        
        # Get existing step
        get_result = self.get(resource_id, execution_id)
        if not get_result.success or not get_result.data:
            return ServiceResult.error_result(f"Step {resource_id} not found", ErrorCode.NOT_FOUND)
        
        step = get_result.data
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(step, key):
                setattr(step, key, value)
        
        # Save updated step
        save_result = self._save_model(step, old_model=get_result.data)
        if not save_result.success:
            return ServiceResult.error_result(save_result.message, save_result.error_code)
        
        result.data = save_result.data
        return result

    def delete(
        self, resource_id: str, tenant_id: str, user_id: str
    ) -> ServiceResult[bool]:
        """Delete step with access control."""
        result = ServiceResult(success=True)
        
        # Extract execution_id from resource_id
        parts = resource_id.split(":")
        if len(parts) < 2:
            return ServiceResult.error_result(f"Invalid step ID format: {resource_id}", ErrorCode.INVALID_INPUT)
        
        execution_id = parts[0]
        
        # Get existing step
        get_result = self.get(resource_id, execution_id)
        if not get_result.success or not get_result.data:
            return ServiceResult.error_result(f"Step {resource_id} not found", ErrorCode.NOT_FOUND)
        
        step = get_result.data
        
        # Delete step
        return self._delete_model(step)

    def save(self, step: WorkflowStep) -> ServiceResult[WorkflowStep]:
        """
        Convenience wrapper for _save_model.
        
        This method provides backward compatibility for code that calls save() directly.
        """
        return self._save_model(step)
