"""
Batch record service for tracking calculation batch status.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import time
import uuid
from typing import Optional, Dict, Any, List

from aws_lambda_powertools import Logger
from boto3_assist.dynamodb.dynamodb import DynamoDB

from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.request_context import RequestContext
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.core.service_errors import NotFoundError

from ..models.batch_record import BatchRecord, BatchStatus

logger = Logger()


class BatchRecordService(DatabaseService[BatchRecord]):
    """
    Service for managing batch records.
    
    Provides operations for creating, updating, and querying batch records
    used in streaming calculation workflows.
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

    @service_method("create_batch")
    def create(
        self,
        execution_id: str,
        batch_number: int,
        files: List[Dict[str, Any]],  
        **kwargs
    ) -> ServiceResult[BatchRecord]:
        """
        Create a new batch record.
        
        Args:
            execution_id: Parent execution ID
            batch_number: Batch number (1-indexed)
            file_id: Profile batch file ID
            profile_ids: List of profile IDs in this batch
            bucket: S3 bucket
            input_key: S3 key for input file
            
        Returns:
            ServiceResult with created BatchRecord
        """
        batch = BatchRecord()        
        batch.execution_id = execution_id
        batch.batch_number = batch_number
        batch.files = files
        batch.status = BatchStatus.PENDING
        
        batch.prep_for_save()
        return self._save_model(batch)

    @service_method("get_batch")
    def get(self, batch_id: str) -> ServiceResult[BatchRecord]:
        """Get batch record by ID."""
        batch = self._get_by_id(batch_id, BatchRecord)
        if not batch:
            raise NotFoundError(f"BatchRecord {batch_id} not found")
        return ServiceResult.success_result(batch)

    @service_method("get_by_id")
    def get_by_id(self, **kwargs) -> ServiceResult[BatchRecord]:
        """Get batch record by ID (abstract method implementation)."""
        batch_id = kwargs.get("batch_id") or kwargs.get("id")
        return self.get(batch_id)

    @service_method("update_batch")
    def update(self, **kwargs) -> ServiceResult[BatchRecord]:
        """Update batch record (abstract method implementation)."""
        batch_id = kwargs.get("batch_id") or kwargs.get("id")
        batch = self._get_by_id(batch_id, BatchRecord)
        if not batch:
            raise NotFoundError(f"BatchRecord {batch_id} not found")
        
        for field in ["status", "output_key", "error_message", "error_code",
                      "profiles_succeeded", "profiles_failed", "retry_count"]:
            if field in kwargs:
                setattr(batch, field, kwargs[field])
        
        batch.prep_for_save()
        return self._save_model(batch)

    @service_method("delete_batch")
    def delete(self, **kwargs) -> ServiceResult[bool]:
        """Delete batch record (abstract method implementation)."""
        batch_id = kwargs.get("batch_id") or kwargs.get("id")
        batch = self._get_by_id(batch_id, BatchRecord)
        if not batch:
            raise NotFoundError(f"BatchRecord {batch_id} not found")
        return self._delete_model(batch)

    @service_method("start_processing")
    def start_processing(
        self,
        batch_id: str,
        file_id: str,
    ) -> ServiceResult[BatchRecord]:
        """
        Mark batch as processing with file_id verification.
        
        Args:
            batch_id: Batch record ID
            file_id: File ID for verification (must match)
            
        Returns:
            ServiceResult with updated BatchRecord
            
        Raises:
            NotFoundError: If batch not found
            ValueError: If file_id doesn't match (safety check)
        """
        batch = self._get_by_id(batch_id, BatchRecord)
        if not batch:
            raise NotFoundError(f"BatchRecord {batch_id} not found")
        
        # Verify file_id is in the batch's files list
        file_ids = [f.get("id") for f in batch.files]
        if file_id not in file_ids:
            raise ValueError(
                f"File ID mismatch: {file_id} not found in batch files {file_ids}"
            )
        
        batch.status = BatchStatus.PROCESSING
        batch.started_utc_ts = time.time()
        batch.prep_for_save()
        return self._save_model(batch)

    @service_method("complete_batch")
    def complete_batch(
        self,
        batch_id: str,
        file_id: str,
        output_key: str,
        items_succeeded: int = 0,
        items_failed: int = 0,
    ) -> ServiceResult[BatchRecord]:
        """
        Mark batch as completed with file_id verification.
        
        Args:
            batch_id: Batch record ID
            file_id: File ID for verification (must match)
            output_key: S3 key for output results
            items_succeeded: Number of successful items
            items_failed: Number of failed items
            
        Returns:
            ServiceResult with updated BatchRecord
        """
        batch = self._get_by_id(batch_id, BatchRecord)
        if not batch:
            raise NotFoundError(f"BatchRecord {batch_id} not found")
        
        # Verify file_id is in the batch's files list
        file_ids = [f.get("id") for f in batch.files]
        if file_id not in file_ids:
            raise ValueError(
                f"File ID mismatch: {file_id} not found in batch files {file_ids}"
            )
        
        batch.status = BatchStatus.COMPLETED
        batch.completed_utc_ts = time.time()
        batch.output_key = output_key
        batch.items_succeeded = items_succeeded
        batch.items_failed = items_failed
        batch.prep_for_save()
        return self._save_model(batch)

    @service_method("fail_batch")
    def fail_batch(
        self,
        batch_id: str,
        file_id: str,
        error_message: str,
        error_code: str = "BATCH_FAILED",
    ) -> ServiceResult[BatchRecord]:
        """
        Mark batch as failed with file_id verification.
        
        Args:
            batch_id: Batch record ID
            file_id: File ID for verification (must match)
            error_message: Error description
            error_code: Error code
            
        Returns:
            ServiceResult with updated BatchRecord
        """
        batch = self._get_by_id(batch_id, BatchRecord)
        if not batch:
            raise NotFoundError(f"BatchRecord {batch_id} not found")
        
        # Verify file_id is in the batch's files list
        file_ids = [f.get("id") for f in batch.files]
        if file_id not in file_ids:
            raise ValueError(
                f"File ID mismatch: {file_id} not found in batch files {file_ids}"
            )
        
        batch.status = BatchStatus.FAILED
        batch.completed_utc_ts = time.time()
        batch.error_message = error_message
        batch.error_code = error_code
        batch.prep_for_save()
        return self._save_model(batch)

    @service_method("get_batches_by_execution")
    def get_batches_by_execution(
        self,
        execution_id: str,
    ) -> ServiceResult[List[BatchRecord]]:
        """
        Get all batch records for an execution.
        
        Args:
            execution_id: Parent execution ID
            
        Returns:
            ServiceResult with list of BatchRecords
        """
        query_model = BatchRecord()
        query_model.execution_id = execution_id
        query_model._batch_number = None  # None triggers prefix-only sort key for begins_with
        
        return self._query_by_index(query_model, "gsi1")

    @service_method("get_execution_status")
    def get_execution_status(
        self,
        execution_id: str,
    ) -> ServiceResult[Dict[str, Any]]:
        """
        Get aggregated status for all batches in an execution.
        
        Args:
            execution_id: Parent execution ID
            
        Returns:
            ServiceResult with status summary:
            - total_batches: Total number of batches
            - pending: Count of pending batches
            - processing: Count of processing batches
            - completed: Count of completed batches
            - failed: Count of failed batches
            - all_complete: True if all batches are done
            - all_successful: True if all completed successfully
            - total_profiles: Sum of all profile counts
            - profiles_succeeded: Sum of successful profiles
            - profiles_failed: Sum of failed profiles
        """
        result = self.get_batches_by_execution(execution_id)
        if not result.success:
            return result
        
        batches = result.data or []
        
        status_counts = {
            BatchStatus.PENDING.value: 0,
            BatchStatus.PROCESSING.value: 0,
            BatchStatus.COMPLETED.value: 0,
            BatchStatus.FAILED.value: 0,
        }
        
        total_files = 0
        items_succeeded = 0
        items_failed = 0
        
        for batch in batches:
            status_counts[batch.status] = status_counts.get(batch.status, 0) + 1
            total_files += len(batch.files)
            items_succeeded += batch.items_succeeded
            items_failed += batch.items_failed
        
        total_batches = len(batches)
        completed_count = status_counts[BatchStatus.COMPLETED.value]
        failed_count = status_counts[BatchStatus.FAILED.value]
        
        summary = {
            "total_batches": total_batches,
            "pending": status_counts[BatchStatus.PENDING.value],
            "processing": status_counts[BatchStatus.PROCESSING.value],
            "completed": completed_count,
            "failed": failed_count,
            "all_complete": (completed_count + failed_count) == total_batches and total_batches > 0,
            "all_successful": completed_count == total_batches and total_batches > 0,
            "total_files": total_files,
            "items_succeeded": items_succeeded,
            "items_failed": items_failed,
        }
        
        return ServiceResult.success_result(summary)

    @service_method("are_all_batches_complete")
    def are_all_batches_complete(
        self,
        execution_id: str,
    ) -> ServiceResult[bool]:
        """
        Check if all batches for an execution are complete.
        
        Args:
            execution_id: Parent execution ID
            
        Returns:
            ServiceResult with True if all batches are complete
        """
        result = self.get_execution_status(execution_id)
        if not result.success:
            return ServiceResult.error_result(result.message)
        
        return ServiceResult.success_result(result.data["all_complete"])
