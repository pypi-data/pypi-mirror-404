"""
Base Workflow Step Handler for processing step completion messages.

This handler listens to the step completion queue and controls
workflow progression by dispatching next steps when dependencies
are satisfied.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import boto3
from aws_lambda_powertools import Logger

from ..models.workflow_step import WorkflowStep, StepStatus
from ..models.step_messages import StepMessage, StepCompletionMessage
from ..services.workflow_step_service import WorkflowStepService
from ..services.step_dispatch_service import StepDispatchService, DispatchResult

logger = Logger()


class BaseWorkflowStepHandler(ABC):
    """
    Base handler for workflow step completion processing.
    
    This handler:
    1. Receives step completion notifications
    2. Updates step status in the database
    3. Finds steps that can now be dispatched
    4. Dispatches next steps to their queues
    5. Detects when execution is complete
    
    Subclasses must implement:
    - get_queue_url_for_step_type(): Map step types to queue URLs
    - on_execution_complete(): Handle execution completion
    - on_execution_failed(): Handle execution failure
    """
    
    def __init__(
        self,
        workflow_step_service: Optional[WorkflowStepService] = None,
        execution_service: Optional[Any] = None,
        sqs_client: Optional[Any] = None,
        dispatch_service: Optional[StepDispatchService] = None,
    ):
        """
        Initialize handler.
        
        Args:
            workflow_step_service: Service for step operations
            execution_service: Service for execution operations
            sqs_client: SQS client for dispatching messages
            dispatch_service: Centralized dispatch service (created if not provided)
        """
        self._workflow_step_service = workflow_step_service
        self._execution_service = execution_service
        self._sqs_client = sqs_client
        self._dispatch_service = dispatch_service
    
    @property
    def sqs_client(self):
        """Lazy-loaded SQS client."""
        if self._sqs_client is None:
            self._sqs_client = boto3.client("sqs")
        return self._sqs_client
    
    @property
    def dispatch_service(self) -> StepDispatchService:
        """Lazy-loaded dispatch service with failure cascade."""
        if self._dispatch_service is None:
            self._dispatch_service = StepDispatchService(
                workflow_step_service=self._workflow_step_service,
                execution_service=self._execution_service,
                sqs_client=self.sqs_client,
                fail_execution_on_dispatch_error=True,
            )
        return self._dispatch_service
    
    @property
    def workflow_step_service(self) -> Optional[WorkflowStepService]:
        """Workflow step service."""
        return self._workflow_step_service
    
    def handle(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Handle SQS batch of step completion messages.
        
        Returns batch item failures for partial batch response.
        """
        records = event.get("Records", [])
        failed_message_ids: List[str] = []
        
        for record in records:
            # Use helper for case-insensitive field access (handles both moto and AWS)
            from geek_cafe_saas_sdk.utilities.sqs_helpers import get_sqs_field
            message_id = get_sqs_field(record, "messageId", "unknown")
            
            try:
                success = self._process_record(record)
                if not success:
                    failed_message_ids.append(message_id)
            except Exception as e:
                logger.exception(f"Error processing step completion {message_id}: {e}")
                failed_message_ids.append(message_id)
        
        return {
            "batchItemFailures": [
                {"itemIdentifier": msg_id} for msg_id in failed_message_ids
            ]
        }
    
    def _parse_message(self, record: Dict[str, Any]) -> StepCompletionMessage:
        """Parse SQS record into StepCompletionMessage."""
        from geek_cafe_saas_sdk.utilities.sqs_helpers import parse_sqs_message_body
        body = parse_sqs_message_body(record)
        return StepCompletionMessage.from_dict(body)
    
    def _process_record(self, record: Dict[str, Any]) -> bool:
        """
        Process a single step completion message.
        
        Returns True if processed successfully.
        """
        completion = self._parse_message(record)
        
        logger.info(
            f"Step completed: execution={completion.execution_id}, "
            f"step={completion.step_id}, status={completion.status}"
        )
        
        # Step 1: Update step status in database
        self._update_step_status(completion)
        
        # Step 2: Check if step failed
        if completion.status == "failed":
            self._handle_step_failure(completion)
            return True
        
        # Step 3: Find and dispatch next steps
        dispatch_results = self._dispatch_next_steps(completion)
        
        # Step 4: Check if execution is complete
        if self._check_execution_complete(completion.execution_id):
            self._handle_execution_complete(completion)
        
        return True
    
    def _update_step_status(self, completion: StepCompletionMessage) -> None:
        """Update step status in the database."""
        if not self.workflow_step_service:
            logger.warning("No workflow step service, skipping status update")
            return
        
        try:
            if completion.status == "completed":
                self.workflow_step_service.complete(
                    step_id=completion.step_id,
                    execution_id=completion.execution_id,
                    output_payload=completion.output_payload,
                )
            elif completion.status == "failed":
                self.workflow_step_service.fail(
                    step_id=completion.step_id,
                    execution_id=completion.execution_id,
                    error_message=completion.error or "Unknown error",
                    error_code=completion.error_code,
                    error_details=completion.error_details,
                )
            elif completion.status == "skipped":
                self.workflow_step_service.skip(
                    step_id=completion.step_id,
                    execution_id=completion.execution_id,
                )
        except Exception as e:
            logger.error(f"Failed to update step status: {e}")
    
    def _handle_step_failure(self, completion: StepCompletionMessage) -> None:
        """Handle a failed step."""
        logger.error(
            f"Step {completion.step_id} failed: {completion.error}"
        )
        
        # Call the abstract method for custom failure handling
        self.on_step_failed(completion)
    
    def _dispatch_next_steps(self, completion: StepCompletionMessage) -> List[DispatchResult]:
        """Find and dispatch steps that are now ready."""
        results = []
        
        if not self.workflow_step_service:
            return results
        
        try:
            dispatchable_result = self.workflow_step_service.get_dispatchable_steps(
                execution_id=completion.execution_id
            )
            
            if not dispatchable_result.success:
                logger.error(f"Failed to get dispatchable steps: {dispatchable_result.error_message}")
                return results
            
            for step in dispatchable_result.data or []:
                result = self._dispatch_step(step, completion)
                results.append(result)
                
        except Exception as e:
            logger.error(f"Failed to dispatch next steps: {e}")
        
        return results
    
    def _dispatch_step(
        self,
        step: WorkflowStep,
        completion: StepCompletionMessage,
    ) -> DispatchResult:
        """
        Dispatch a single step to its queue.
        
        Uses the centralized StepDispatchService which handles:
        - SQS send with retries
        - Step failure marking on dispatch errors
        - Execution failure cascade
        """
        # Get queue URL for this step type
        queue_url = step.queue_url or self.get_queue_url_for_step_type(step.step_type)
        
        # Merge output from previous step into input if needed
        input_payload = step.input_payload.copy() if step.input_payload else {}
        if completion.output_payload:
            input_payload["previous_step_output"] = completion.output_payload
        
        # Build message
        message = StepMessage(
            execution_id=step.execution_id,
            step_id=step.step_id,
            step_type=step.step_type,
            step_index=step.step_index,
            tenant_id=step.tenant_id or completion.tenant_id or "",
            user_id=step.owner_id or completion.user_id or "",
            input_payload=input_payload,
            depends_on=step.depends_on,
            callback_queue_url=self.get_completion_queue_url(),
            metadata=step.metadata or {},
        )
        
        # Use centralized dispatch service - handles failures and cascades
        result = self.dispatch_service.dispatch_step(
            message=message,
            queue_url=queue_url or "",
            mark_step_dispatched=True,
        )
        
        if result.success:
            logger.info(f"Dispatched step {step.step_id} ({step.step_type})")
        else:
            # Dispatch service already marked step and execution as failed
            logger.error(
                f"Failed to dispatch step {step.step_id}: {result.error}"
            )
        
        return result
    
    def _check_execution_complete(self, execution_id: str) -> bool:
        """Check if all steps in the execution are complete."""
        if not self.workflow_step_service:
            return False
        
        try:
            result = self.workflow_step_service.is_execution_complete(execution_id)
            return result.success and result.data is True
        except Exception as e:
            logger.error(f"Failed to check execution completion: {e}")
            return False
    
    def _handle_execution_complete(self, completion: StepCompletionMessage) -> None:
        """Handle execution completion."""
        logger.info(f"Execution {completion.execution_id} complete!")
        
        # Check if any steps failed
        has_failed = False
        if self.workflow_step_service:
            try:
                result = self.workflow_step_service.has_execution_failed(completion.execution_id)
                has_failed = result.success and result.data is True
            except Exception:
                pass
        
        if has_failed:
            self.on_execution_failed(completion)
        else:
            self.on_execution_complete(completion)
    
    # =========================================================================
    # Abstract methods - must be implemented by subclasses
    # =========================================================================
    
    @abstractmethod
    def get_queue_url_for_step_type(self, step_type: str) -> Optional[str]:
        """
        Get the SQS queue URL for a step type.
        
        Args:
            step_type: The type of step
            
        Returns:
            SQS queue URL or None if step type is not recognized
        """
        pass
    
    @abstractmethod
    def get_completion_queue_url(self) -> Optional[str]:
        """
        Get the SQS queue URL for step completion notifications.
        
        Returns:
            SQS queue URL for the completion queue
        """
        pass
    
    def on_step_failed(self, completion: StepCompletionMessage) -> None:
        """
        Called when a step fails.
        
        Override to implement custom failure handling (e.g., retry logic,
        notifications, etc.).
        
        Args:
            completion: The completion message for the failed step
        """
        pass
    
    def on_execution_complete(self, completion: StepCompletionMessage) -> None:
        """
        Called when all steps complete successfully.
        
        Override to implement completion handling (e.g., notifications,
        cleanup, etc.).
        
        Args:
            completion: The completion message for the last step
        """
        pass
    
    def on_execution_failed(self, completion: StepCompletionMessage) -> None:
        """
        Called when execution fails (one or more steps failed).
        
        Override to implement failure handling.
        
        Args:
            completion: The completion message for the last step
        """
        pass
