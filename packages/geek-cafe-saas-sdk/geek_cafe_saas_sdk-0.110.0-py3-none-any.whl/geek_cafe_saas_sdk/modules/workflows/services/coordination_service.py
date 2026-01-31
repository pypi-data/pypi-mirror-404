"""
Coordination service for tracking distributed processing completion.

This service uses atomic counters to efficiently track completion state
without scanning all items. Designed for high-scale workflows.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import time
import uuid
from typing import Optional, Dict, Any

from aws_lambda_powertools import Logger
from boto3_assist.dynamodb.dynamodb import DynamoDB
from decimal import Decimal

from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.request_context import RequestContext
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.core.service_errors import NotFoundError

from ..models.coordination_record import CoordinationRecord, CoordinationStatus

logger = Logger()


class CoordinationService(DatabaseService[CoordinationRecord]):
    """
    Service for managing coordination records with atomic counters.
    
    This service provides O(1) completion checking for distributed
    processing workflows using DynamoDB's atomic ADD operation.
    
    Example:
        # Phase 1: Start coordination (streaming)
        service.create(execution_id="exec-123", step_type="calculation")
        
        # Consumers increment atomically (no race conditions)
        service.increment_completed("exec-123", "calculation")
        service.increment_failed("exec-123", "calculation")
        
        # Phase 2: Finalize when total known
        service.finalize("exec-123", "calculation", total_expected=1000000)
        
        # Check completion (O(1) lookup!)
        result = service.get_status("exec-123", "calculation")
        if result.data["is_complete"]:
            # All done!
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

    @service_method("create_coordination")
    def create(
        self,
        execution_id: str,
        step_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ServiceResult[CoordinationRecord]:
        """
        Create a new coordination record (streaming phase).
        
        Args:
            execution_id: Parent execution ID
            step_type: Type of step being coordinated (e.g., "calculation")
            metadata: Optional metadata
            
        Returns:
            ServiceResult with created CoordinationRecord
        """
        coord = CoordinationRecord()
        coord.id = str(uuid.uuid4())
        coord.execution_id = execution_id
        coord.step_type = step_type
        coord.total_expected = None  # Unknown during streaming
        coord.completed_count = 0
        coord.failed_count = 0
        coord.is_finalized = False
        coord.status = CoordinationStatus.STREAMING
        coord.created_utc_ts = Decimal(str(time.time()))
        coord.metadata = metadata or {}
        
        coord.prep_for_save()
        return self._save_model(coord)

    @service_method("get_coordination")
    def get(
        self,
        execution_id: str,
        step_type: str
    ) -> ServiceResult[CoordinationRecord]:
        """
        Get coordination record by execution_id and step_type.
        
        Args:
            execution_id: Execution ID
            step_type: Step type
            
        Returns:
            ServiceResult with CoordinationRecord
        """
        # Use model to build key
        query_model = CoordinationRecord()
        query_model.execution_id = execution_id
        query_model.step_type = step_type
        
        key = query_model.get_key("primary").key()
        
        response = self.dynamodb.get(
            table_name=self.table_name,
            key=key,
            strongly_consistent=True  # Strong consistency for accurate counts
        )
        
        if not response.get("Item"):
            raise NotFoundError(
                f"CoordinationRecord not found for execution {execution_id}, step {step_type}"
            )
        
        coord = CoordinationRecord()
        coord.map(response["Item"])
        return ServiceResult.success_result(coord)

    @service_method("finalize_coordination")
    def finalize(
        self,
        execution_id: str,
        step_type: str,
        total_expected: int,
        metadata: dict | None = None
    ) -> ServiceResult[bool]:
        """
        Finalize coordination record with known total (processing phase).
        
        This transitions from streaming to processing phase. After this,
        completion can be checked.
        
        Args:
            execution_id: Execution ID
            step_type: Step type
            total_expected: Total number of items to process
            metadata: Optional metadata to merge with existing metadata (e.g., fan-out config)
            
        Returns:
            ServiceResult with True if successful
        """
        # Use model to build key
        query_model = CoordinationRecord()
        query_model.execution_id = execution_id
        query_model.step_type = step_type
        key = query_model.get_key("primary").key()
        
        # Build update expression based on whether metadata is provided
        if metadata:
            update_expression = """
                SET total_expected = :total,
                    is_finalized = :true,
                    #status = :processing,
                    finalized_utc_ts = :ts
            """
            expression_attribute_names = {
                "#status": "status",
                "#metadata": "metadata"
            }
            expression_attribute_values = {
                ":total": total_expected,
                ":true": True,
                ":processing": CoordinationStatus.PROCESSING.value,
                ":ts": Decimal(str(time.time()))
            }
            
            # Add metadata fields dynamically
            # DynamoDB will automatically create the metadata map if it doesn't exist
            # when setting nested properties
            for key_name, value in metadata.items():
                safe_key = key_name.replace(".", "_")
                update_expression += f", #metadata.#meta_{safe_key} = :meta_{safe_key}"
                expression_attribute_names[f"#meta_{safe_key}"] = safe_key
                expression_attribute_values[f":meta_{safe_key}"] = value
        else:
            update_expression = """
                SET total_expected = :total,
                    is_finalized = :true,
                    #status = :processing,
                    finalized_utc_ts = :ts
            """
            expression_attribute_names = {"#status": "status"}
            expression_attribute_values = {
                ":total": total_expected,
                ":true": True,
                ":processing": CoordinationStatus.PROCESSING.value,
                ":ts": Decimal(str(time.time()))
            }
        
        # Atomic update to set total and finalize
        try:
            self.dynamodb.update_item(
            table_name=self.table_name,
            key=key,
            update_expression=update_expression,
            expression_attribute_names=expression_attribute_names,
            expression_attribute_values=expression_attribute_values
        )
        except Exception as e:
            logger.exception(
                f"Failed to finalize coordination for {execution_id}/{step_type}: {e}"
            )
            raise        
        logger.info(
            f"Finalized coordination for {execution_id}/{step_type} "
            f"with total_expected={total_expected}"
        )
        
        return ServiceResult.success_result(True)

    @service_method("increment_completed")
    def increment_completed(
        self,
        execution_id: str,
        step_type: str,
        increment: int = 1
    ) -> ServiceResult[bool]:
        """
        Atomically increment completed count.
        
        This operation is thread-safe and works correctly even with
        hundreds of concurrent Lambda executions.
        
        Args:
            execution_id: Execution ID
            step_type: Step type
            increment: Amount to increment (default 1)
            
        Returns:
            ServiceResult with True if successful
        """
        # Use model to build key
        query_model = CoordinationRecord()
        query_model.execution_id = execution_id
        query_model.step_type = step_type
        key = query_model.get_key("primary").key()
        
        # Atomic increment - DynamoDB guarantees correctness
        from datetime import datetime, timezone
        self.dynamodb.update_item(
            table_name=self.table_name,
            key=key,
            update_expression="ADD completed_count :inc SET updated_utc_ts = :ts, modified_utc = :modified_utc",
            expression_attribute_values={
                ":inc": increment,
                ":ts": Decimal(str(time.time())),
                ":modified_utc": str(datetime.now(timezone.utc))
            }
        )
        
        return ServiceResult.success_result(True)

    @service_method("increment_failed")
    def increment_failed(
        self,
        execution_id: str,
        step_type: str,
        increment: int = 1,
        error_message: Optional[str] = None
    ) -> ServiceResult[bool]:
        """
        Atomically increment failed count and mark as failed.
        
        Args:
            execution_id: Execution ID
            step_type: Step type
            increment: Amount to increment (default 1)
            error_message: Optional error message
            
        Returns:
            ServiceResult with True if successful
        """
        # Use model to build key
        query_model = CoordinationRecord()
        query_model.execution_id = execution_id
        query_model.step_type = step_type
        key = query_model.get_key("primary").key()
        
        # Build update expression
        update_expr = "ADD failed_count :inc SET #status = :failed, updated_utc_ts = :ts"
        attr_values = {
            ":inc": increment,
            ":failed": CoordinationStatus.FAILED.value,
            ":ts": Decimal(str(time.time()))
        }
        
        if error_message:
            update_expr += ", error_message = :error"
            attr_values[":error"] = error_message
        
        # Atomic increment
        self.dynamodb.update_item(
            table_name=self.table_name,
            key=key,
            update_expression=update_expr,
            expression_attribute_names={"#status": "status"},
            expression_attribute_values=attr_values
        )
        
        return ServiceResult.success_result(True)

    @service_method("get_status")
    def get_status(
        self,
        execution_id: str,
        step_type: str
    ) -> ServiceResult[Dict[str, Any]]:
        """
        Get coordination status summary.
        
        This is an O(1) operation that returns completion state without
        scanning all items.
        
        Args:
            execution_id: Execution ID
            step_type: Step type
            
        Returns:
            ServiceResult with status summary:
            - is_complete: True if all items processed
            - is_finalized: True if total is known
            - has_failures: True if any items failed
            - completed: Count of completed items
            - failed: Count of failed items
            - total: Total expected items (None if not finalized)
            - pending: Count of pending items
            - progress_percentage: Progress percentage
            - status: Current status
        """
        result = self.get(execution_id, step_type)
        if not result.success:
            return result
        
        coord = result.data
        
        # Check if coordination has been explicitly marked as failed
        # This happens when a critical error occurs (e.g., CSV parsing error)
        # In this case, treat it as complete even if not all items processed
        is_explicitly_failed = coord.status == CoordinationStatus.FAILED.value
        
        # Compute actual status based on completion state
        # The database status field may be stale (e.g., "processing" when actually complete)
        # Note: is_complete means "done processing" (could be succeeded or failed)
        computed_status = coord.status
        is_coordination_complete = coord.is_complete or is_explicitly_failed
        
        if is_coordination_complete:
            # Done processing - check if succeeded or failed
            if coord.has_failures or is_explicitly_failed:
                computed_status = CoordinationStatus.FAILED.value  # Completed with failures
            else:
                computed_status = CoordinationStatus.COMPLETED.value  # Completed successfully
        elif coord.is_finalized:
            # Total is known but not all items processed yet
            computed_status = CoordinationStatus.PROCESSING.value
        else:
            # Still creating items (total not yet known)
            computed_status = CoordinationStatus.STREAMING.value
        
        summary = {
            "is_complete": is_coordination_complete,
            "is_finalized": coord.is_finalized,
            "has_failures": coord.has_failures or is_explicitly_failed,
            "completed": coord.completed_count,
            "failed": coord.failed_count,
            "total": coord.total_expected,
            "pending": coord.pending_count,
            "progress_percentage": coord.progress_percentage,
            "status": computed_status,
            "error_message": coord.error_message,
        }
        
        return ServiceResult.success_result(summary)

    @service_method("mark_complete")
    def mark_complete(
        self,
        execution_id: str,
        step_type: str
    ) -> ServiceResult[bool]:
        """
        Mark coordination as completed.
        
        Args:
            execution_id: Execution ID
            step_type: Step type
            
        Returns:
            ServiceResult with True if successful
        """
        # Use model to build key
        query_model = CoordinationRecord()
        query_model.execution_id = execution_id
        query_model.step_type = step_type
        key = query_model.get_key("primary").key()
        
        self.dynamodb.update_item(
            table_name=self.table_name,
            key=key,
            update_expression="SET #status = :completed, completed_utc_ts = :ts",
            expression_attribute_names={"#status": "status"},
            expression_attribute_values={
                ":completed": CoordinationStatus.COMPLETED.value,
                ":ts": Decimal(str(time.time()))
            }
        )
        
        return ServiceResult.success_result(True)

    @service_method("get_by_id")
    def get_by_id(self, **kwargs) -> ServiceResult[CoordinationRecord]:
        """Get coordination record by ID (abstract method implementation)."""
        execution_id = kwargs.get("execution_id")
        step_type = kwargs.get("step_type")
        return self.get(execution_id, step_type)

    @service_method("update")
    def update(self, **kwargs) -> ServiceResult[CoordinationRecord]:
        """Update coordination record (abstract method implementation)."""
        # Not typically used - use atomic operations instead
        raise NotImplementedError(
            "Use atomic operations (increment_completed, increment_failed, finalize) instead"
        )

    @service_method("delete")
    def delete(self, **kwargs) -> ServiceResult[bool]:
        """Delete coordination record (abstract method implementation)."""
        execution_id = kwargs.get("execution_id")
        step_type = kwargs.get("step_type")
        
        query_model = CoordinationRecord()
        query_model.execution_id = execution_id
        query_model.step_type = step_type
        
        return self._delete_model(query_model)
