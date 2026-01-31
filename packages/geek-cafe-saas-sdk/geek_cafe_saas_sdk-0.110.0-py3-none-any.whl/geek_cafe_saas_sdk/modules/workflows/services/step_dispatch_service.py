"""
Step Dispatch Service - Centralized SQS dispatch with failure handling.

This service provides a consistent interface for dispatching step messages
to SQS queues with proper error handling and failure cascade.

When a dispatch fails:
1. The step is marked as failed
2. The execution is marked as failed
3. Dependent steps are skipped

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import boto3
from aws_lambda_powertools import Logger
from botocore.exceptions import BotoCoreError, ClientError

from ..models.step_messages import StepMessage, StepCompletionMessage
from ..models.workflow_step import WorkflowStep, StepStatus

logger = Logger()


class DispatchError(Exception):
    """Exception raised when step dispatch fails."""
    
    def __init__(
        self,
        message: str,
        step_id: str,
        step_type: str,
        error_code: str = "DISPATCH_FAILED",
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.step_id = step_id
        self.step_type = step_type
        self.error_code = error_code
        self.original_error = original_error


@dataclass
class DispatchResult:
    """Result of a dispatch operation."""
    step_id: str
    step_type: str
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    dispatched_utc: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_type": self.step_type,
            "success": self.success,
            "message_id": self.message_id,
            "error": self.error,
            "error_code": self.error_code,
            "dispatched_utc": self.dispatched_utc,
        }


@dataclass
class BatchDispatchResult:
    """Result of dispatching multiple steps."""
    execution_id: str
    total_steps: int
    successful_count: int
    failed_count: int
    results: List[DispatchResult] = field(default_factory=list)
    
    @property
    def all_successful(self) -> bool:
        return self.failed_count == 0
    
    @property
    def has_failures(self) -> bool:
        return self.failed_count > 0
    
    def get_failed_results(self) -> List[DispatchResult]:
        return [r for r in self.results if not r.success]
    
    def get_successful_results(self) -> List[DispatchResult]:
        return [r for r in self.results if r.success]


class StepDispatchService:
    """
    Centralized service for dispatching step messages to SQS.
    
    Provides:
    - Consistent error handling across all step dispatches
    - Automatic step failure marking on dispatch errors
    - Execution failure cascade when steps fail
    - Retry support with configurable attempts
    - Detailed logging and error tracking
    
    Usage:
        dispatch_service = StepDispatchService(
            workflow_step_service=step_service,
            execution_service=exec_service,
        )
        
        result = dispatch_service.dispatch_step(
            message=step_message,
            queue_url=queue_url,
        )
        
        if not result.success:
            # Step and execution already marked as failed
            logger.error(f"Dispatch failed: {result.error}")
    """
    
    def __init__(
        self,
        workflow_step_service: Optional[Any] = None,
        execution_service: Optional[Any] = None,
        sqs_client: Optional[Any] = None,
        max_retries: int = 2,
        fail_execution_on_dispatch_error: bool = True,
    ):
        """
        Initialize the dispatch service.
        
        Args:
            workflow_step_service: Service for updating step status
            execution_service: Service for updating execution status
            sqs_client: SQS client (lazy-loaded if not provided)
            max_retries: Maximum retry attempts for transient failures
            fail_execution_on_dispatch_error: Whether to fail the execution when dispatch fails
        """
        self._workflow_step_service = workflow_step_service
        self._execution_service = execution_service
        self._sqs_client = sqs_client
        self.max_retries = max_retries
        self.fail_execution_on_dispatch_error = fail_execution_on_dispatch_error
    
    @property
    def sqs_client(self):
        """Lazy-loaded SQS client."""
        if self._sqs_client is None:
            self._sqs_client = boto3.client("sqs")
        return self._sqs_client
    
    def dispatch_step(
        self,
        message: StepMessage,
        queue_url: str,
        delay_seconds: int = 0,
        mark_step_dispatched: bool = True,
    ) -> DispatchResult:
        """
        Dispatch a single step message to SQS.
        
        On failure:
        - Marks the step as failed
        - Optionally marks the execution as failed
        
        Args:
            message: The step message to dispatch
            queue_url: Target SQS queue URL
            delay_seconds: Delay before message is available
            mark_step_dispatched: Whether to update step status to dispatched
            
        Returns:
            DispatchResult with success/failure details
        """
        if not queue_url:
            return self._handle_dispatch_failure(
                message=message,
                error_message=f"No queue URL provided for step {message.step_type}",
                error_code="QUEUE_URL_MISSING",
            )
        
        last_error: Optional[Exception] = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.sqs_client.send_message(
                    QueueUrl=queue_url,
                    MessageBody=message.to_json(),
                    DelaySeconds=delay_seconds,
                )
                
                message_id = response.get("MessageId")
                dispatched_utc = datetime.now(timezone.utc).isoformat()
                
                logger.info(
                    f"Dispatched step {message.step_id} ({message.step_type}) "
                    f"to queue, message_id={message_id}"
                )
                
                # Mark step as dispatched
                if mark_step_dispatched and self._workflow_step_service:
                    try:
                        self._workflow_step_service.dispatch(
                            step_id=message.step_id,
                            execution_id=message.execution_id,
                            message_id=message_id,
                        )
                    except Exception as e:
                        logger.warning(f"Failed to mark step as dispatched: {e}")
                
                return DispatchResult(
                    step_id=message.step_id,
                    step_type=message.step_type,
                    success=True,
                    message_id=message_id,
                    dispatched_utc=dispatched_utc,
                )
                
            except ClientError as e:
                last_error = e
                error_code = e.response.get("Error", {}).get("Code", "Unknown")
                
                # Non-retryable errors
                if error_code in [
                    "QueueDoesNotExist",
                    "InvalidParameterValue",
                    "AccessDenied",
                    "InvalidAddress",
                ]:
                    logger.error(
                        f"Non-retryable SQS error for step {message.step_id}: "
                        f"{error_code} - {e}"
                    )
                    break
                
                # Retryable errors - try again
                if attempt < self.max_retries:
                    logger.warning(
                        f"Retryable SQS error for step {message.step_id} "
                        f"(attempt {attempt + 1}/{self.max_retries + 1}): {e}"
                    )
                    continue
                    
            except BotoCoreError as e:
                last_error = e
                if attempt < self.max_retries:
                    logger.warning(
                        f"BotoCore error for step {message.step_id} "
                        f"(attempt {attempt + 1}/{self.max_retries + 1}): {e}"
                    )
                    continue
                    
            except Exception as e:
                last_error = e
                logger.exception(f"Unexpected error dispatching step {message.step_id}: {e}")
                break
        
        # All retries exhausted or non-retryable error
        error_code = "SQS_SEND_FAILED"
        if isinstance(last_error, ClientError):
            error_code = last_error.response.get("Error", {}).get("Code", "SQS_CLIENT_ERROR")
        
        return self._handle_dispatch_failure(
            message=message,
            error_message=str(last_error),
            error_code=error_code,
            original_error=last_error,
        )
    
    def dispatch_steps(
        self,
        messages: List[StepMessage],
        queue_url_resolver: callable,
        delay_seconds: int = 0,
        stop_on_first_failure: bool = False,
    ) -> BatchDispatchResult:
        """
        Dispatch multiple step messages.
        
        Args:
            messages: List of step messages to dispatch
            queue_url_resolver: Function that takes step_type and returns queue_url
            delay_seconds: Delay before messages are available
            stop_on_first_failure: Stop dispatching after first failure
            
        Returns:
            BatchDispatchResult with all results
        """
        if not messages:
            return BatchDispatchResult(
                execution_id="",
                total_steps=0,
                successful_count=0,
                failed_count=0,
            )
        
        execution_id = messages[0].execution_id
        results: List[DispatchResult] = []
        
        for message in messages:
            queue_url = queue_url_resolver(message.step_type)
            
            result = self.dispatch_step(
                message=message,
                queue_url=queue_url,
                delay_seconds=delay_seconds,
            )
            results.append(result)
            
            if not result.success and stop_on_first_failure:
                logger.warning(
                    f"Stopping batch dispatch after failure: {result.error}"
                )
                break
        
        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        
        return BatchDispatchResult(
            execution_id=execution_id,
            total_steps=len(messages),
            successful_count=successful,
            failed_count=failed,
            results=results,
        )
    
    def _handle_dispatch_failure(
        self,
        message: StepMessage,
        error_message: str,
        error_code: str,
        original_error: Optional[Exception] = None,
    ) -> DispatchResult:
        """
        Handle a dispatch failure by marking step and execution as failed.
        """
        logger.error(
            f"Dispatch failed for step {message.step_id} ({message.step_type}): "
            f"[{error_code}] {error_message}"
        )
        
        # Mark step as failed
        if self._workflow_step_service:
            try:
                self._workflow_step_service.fail(
                    step_id=message.step_id,
                    execution_id=message.execution_id,
                    error_message=f"Dispatch failed: {error_message}",
                    error_code=error_code,
                    error_details={
                        "dispatch_error": True,
                        "original_error": str(original_error) if original_error else None,
                    },
                )
                logger.info(f"Marked step {message.step_id} as failed")
            except Exception as e:
                logger.error(f"Failed to mark step as failed: {e}")
        
        # Mark execution as failed
        if self.fail_execution_on_dispatch_error and self._execution_service:
            try:
                self._execution_service.fail(
                    execution_id=message.execution_id,
                    error_message=f"Step {message.step_type} dispatch failed: {error_message}",
                    error_code=f"STEP_DISPATCH_{error_code}",
                )
                logger.info(f"Marked execution {message.execution_id} as failed")
            except Exception as e:
                logger.error(f"Failed to mark execution as failed: {e}")
        
        return DispatchResult(
            step_id=message.step_id,
            step_type=message.step_type,
            success=False,
            error=error_message,
            error_code=error_code,
        )
    
    def send_completion_notification(
        self,
        completion: StepCompletionMessage,
        queue_url: str,
    ) -> DispatchResult:
        """
        Send a step completion notification to the completion queue.
        
        This is used by step handlers to notify the workflow controller
        that a step has completed.
        
        Args:
            completion: The completion message
            queue_url: The step completion queue URL
            
        Returns:
            DispatchResult with success/failure details
        """
        if not queue_url:
            logger.error("No completion queue URL provided")
            return DispatchResult(
                step_id=completion.step_id,
                step_type=completion.step_type,
                success=False,
                error="No completion queue URL provided",
                error_code="QUEUE_URL_MISSING",
            )
        
        try:
            response = self.sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=completion.to_json(),
            )
            
            message_id = response.get("MessageId")
            
            logger.info(
                f"Sent completion notification for step {completion.step_id}, "
                f"status={completion.status}, message_id={message_id}"
            )
            
            return DispatchResult(
                step_id=completion.step_id,
                step_type=completion.step_type,
                success=True,
                message_id=message_id,
            )
            
        except (BotoCoreError, ClientError) as e:
            error_code = "SQS_SEND_FAILED"
            if isinstance(e, ClientError):
                error_code = e.response.get("Error", {}).get("Code", "SQS_CLIENT_ERROR")
            
            logger.error(
                f"Failed to send completion notification for step {completion.step_id}: {e}"
            )
            
            # For completion notifications, we don't cascade failures
            # The step already completed (or failed), we just couldn't notify
            return DispatchResult(
                step_id=completion.step_id,
                step_type=completion.step_type,
                success=False,
                error=str(e),
                error_code=error_code,
            )
