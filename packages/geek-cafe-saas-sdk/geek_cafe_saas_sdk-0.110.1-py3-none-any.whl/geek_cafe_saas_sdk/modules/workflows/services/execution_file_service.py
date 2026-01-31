"""
Execution file service for managing file associations with workflow executions.

This service provides operations for linking files to executions and querying
files by execution, type, role, or step. It implements the junction table pattern
for managing many-to-many relationships between executions and files.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import time
import uuid
from typing import Optional, List

from aws_lambda_powertools import Logger
from boto3_assist.dynamodb.dynamodb import DynamoDB

from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.request_context import RequestContext
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.core.service_errors import NotFoundError, ValidationError

from ..models.execution_file import ExecutionFile

logger = Logger()


class ExecutionFileService(DatabaseService[ExecutionFile]):
    """
    Service for managing execution-file relationships.
    
    This service provides a clean interface for:
    - Linking files to executions with type/role classification
    - Querying files by execution, type, role, or creating step
    - Reverse lookup: finding executions that use a specific file
    - Unlinking files from executions
    
    Example Usage:
        # Link a calculation result to an execution
        service.link_file(
            execution_id="exec-123",
            file_id="file-456",
            file_type="calculation",
            file_role="result",
            created_by_step="calculation",
            metadata={"profile_id": "subject_1"}
        )
        
        # Query all calculation files for an execution
        result = service.get_files_by_execution(
            execution_id="exec-123",
            file_type="calculation"
        )
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

    @service_method("create")
    def create(self, **kwargs) -> ServiceResult[ExecutionFile]:
        """
        Create a new execution-file link (abstract method implementation).
        
        This is an alias for link_file() to satisfy DatabaseService requirements.
        """
        return self.link_file(**kwargs)
    
    @service_method("link_file")
    def link_file(
        self,
        execution_id: str,
        file_id: str,
        file_type: str,
        file_role: str,
        created_by_step: str,
        step_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        **kwargs
    ) -> ServiceResult[ExecutionFile]:
        """
        Link a file to an execution.
        
        Creates a junction record that associates a file with an execution,
        including classification (type/role) and tracking information.
        
        Args:
            execution_id: ID of the execution
            file_id: ID of the file (from FileSystem)
            file_type: Type of file ("input", "profile", "calculation", "output", "package")
            file_role: Role of file ("source", "cleaned", "result", "listing", "summary")
            created_by_step: Name of the step that created this file
            step_id: Full step ID if available (execution_id:step_type:step_uuid)
            metadata: Additional step-specific metadata
            
        Returns:
            ServiceResult with created ExecutionFile
            
        Raises:
            ValidationError: If required fields are missing
        """
        if not execution_id:
            raise ValidationError("execution_id is required")
        if not file_id:
            raise ValidationError("file_id is required")
        if not file_type:
            raise ValidationError("file_type is required")
        if not file_role:
            raise ValidationError("file_role is required")
        if not created_by_step:
            raise ValidationError("created_by_step is required")
        
        exec_file = ExecutionFile()
        exec_file.id = f"{execution_id}:{file_id}"  # Composite ID for uniqueness
        exec_file.execution_id = execution_id
        exec_file.file_id = file_id
        exec_file.file_type = file_type
        exec_file.file_role = file_role
        exec_file.created_by_step = created_by_step
        exec_file.step_id = step_id
        exec_file.metadata = metadata or {}
        exec_file.linked_utc_ts = time.time()
        
        exec_file.prep_for_save()
        return self._save_model(exec_file)

    @service_method("get_link")
    def get_link(
        self,
        execution_id: str,
        file_id: str
    ) -> ServiceResult[ExecutionFile]:
        """
        Get a specific execution-file link.
        
        Args:
            execution_id: ID of the execution
            file_id: ID of the file
            
        Returns:
            ServiceResult with ExecutionFile
            
        Raises:
            NotFoundError: If link not found
        """
        # Build composite key for query
        temp_model = ExecutionFile()
        temp_model.execution_id = execution_id
        temp_model.file_id = file_id
        temp_model.prep_for_save()
        
        key = temp_model.get_key("primary").key()
        
        response = self.dynamodb.get(
            key=key,
            table_name=self.table_name
        )
        
        if not response or "Item" not in response:
            raise NotFoundError(
                f"ExecutionFile link not found: {execution_id} -> {file_id}"
            )
        
        exec_file = ExecutionFile()
        exec_file.map(response)
        return ServiceResult.success_result(exec_file)

    @service_method("unlink_file")
    def unlink_file(
        self,
        execution_id: str,
        file_id: str
    ) -> ServiceResult[bool]:
        """
        Unlink a file from an execution.
        
        Removes the junction record. Note: This does not delete the actual file
        from FileSystem, only the relationship.
        
        Args:
            execution_id: ID of the execution
            file_id: ID of the file
            
        Returns:
            ServiceResult with True if deleted
            
        Raises:
            NotFoundError: If link not found
        """
        # Build composite key for delete
        temp_model = ExecutionFile()
        temp_model.execution_id = execution_id
        temp_model.file_id = file_id
        temp_model.prep_for_save()
        
        key = temp_model.get_key("primary").key()
        
        # Verify it exists first
        response = self.dynamodb.get(
            key=key,
            table_name=self.table_name
        )
        
        if not response or "Item" not in response:
            raise NotFoundError(
                f"ExecutionFile link not found: {execution_id} -> {file_id}"
            )
        
        # Delete using the primary key
        self.dynamodb.delete(
            table_name=self.table_name,
            primary_key=key
        )
        
        return ServiceResult.success_result(True)

    @service_method("get_files_by_execution")
    def get_files_by_execution(
        self,
        execution_id: str,
        file_type: Optional[str] = None,
        file_role: Optional[str] = None,
        limit: Optional[int] = None,
        ascending: bool = True
    ) -> ServiceResult[List[ExecutionFile]]:
        """
        Get all files associated with an execution.
        
        Optionally filter by file_type and/or file_role.
        
        IMPORTANT: This method automatically handles pagination to fetch ALL results,
        not just the first page. For large result sets (e.g., 1000+ calculation files),
        this ensures no data is lost due to DynamoDB's 1MB page size limit.
        
        Args:
            execution_id: ID of the execution
            file_type: Optional filter by file type
            file_role: Optional filter by file role
            limit: Optional limit on TOTAL number of results (across all pages)
            ascending: Sort order (default: True for ascending/oldest first)
            
        Returns:
            ServiceResult with list of ALL ExecutionFile records (paginated automatically)
            
        Examples:
            # Get all files in ascending order (oldest first)
            service.get_files_by_execution("exec-123")
            
            # Get calculation files in descending order (newest first)
            service.get_files_by_execution("exec-123", file_type="calculation", ascending=False)
            
            # Get only calculation result files (all pages)
            service.get_files_by_execution(
                "exec-123",
                file_type="calculation",
                file_role="result"
            )
        """
        # Determine which index to use
        if file_type or file_role:
            index_name = "gsi1"
        else:
            index_name = "primary"
        
        # Fetch all pages
        all_files = []
        start_key = None
        page_count = 0
        total_fetched = 0
        
        while True:
            page_count += 1
            
            # Create fresh query model for each page
            query_model = ExecutionFile()
            query_model.execution_id = execution_id
            if file_type:
                query_model.file_type = file_type
            if file_role:
                query_model.file_role = file_role
            # Leave file_id empty for begins_with query
            
            # Calculate remaining items if user specified a limit
            page_limit = None
            if limit is not None:
                remaining = limit - total_fetched
                if remaining <= 0:
                    break  # Already have enough items
                page_limit = remaining
            
            # Query one page
            result = self._query_by_index(
                query_model,
                index_name,
                start_key=start_key,
                limit=page_limit,  # Pass limit to DynamoDB to reduce read requests
                ascending=ascending
            )
            
            if not result.success:
                # If first page fails, return the error
                if page_count == 1:
                    return result
                # If subsequent page fails, log warning but return what we have
                logger.warning(
                    f"Pagination failed on page {page_count} for execution {execution_id}. "
                    f"Returning {len(all_files)} files from {page_count - 1} pages.",
                    extra={
                        "execution_id": execution_id,
                        "page_count": page_count,
                        "total_fetched": len(all_files),
                        "error": result.message
                    }
                )
                break
            
            # Add this page's results
            page_files = result.data or []
            all_files.extend(page_files)
            total_fetched += len(page_files)
            
            logger.debug(
                f"Fetched page {page_count}: {len(page_files)} files (total: {total_fetched})",
                extra={
                    "execution_id": execution_id,
                    "page": page_count,
                    "page_size": len(page_files),
                    "total": total_fetched
                }
            )
            
            # Check if we've hit the user-specified limit
            if limit and total_fetched >= limit:
                all_files = all_files[:limit]  # Trim to exact limit
                logger.info(
                    f"Reached user-specified limit of {limit} files after {page_count} pages",
                    extra={
                        "execution_id": execution_id,
                        "limit": limit,
                        "pages": page_count
                    }
                )
                break
            
            # Check for more pages
            if result.metadata and "last_evaluated_key" in result.metadata:
                start_key = result.metadata["last_evaluated_key"]
            else:
                # No more pages
                break
        
        logger.info(
            f"Retrieved {len(all_files)} files for execution {execution_id} across {page_count} page(s)",
            extra={
                "execution_id": execution_id,
                "total_files": len(all_files),
                "pages_fetched": page_count,
                "file_type": file_type,
                "file_role": file_role
            }
        )
        
        return ServiceResult.success_result(all_files)

    @service_method("get_files_by_step")
    def get_files_by_step(
        self,
        execution_id: str,
        created_by_step: str,
        limit: Optional[int] = None
    ) -> ServiceResult[List[ExecutionFile]]:
        """
        Get all files created by a specific workflow step.
        
        Args:
            execution_id: ID of the execution
            created_by_step: Name of the step that created the files
            limit: Optional limit on number of results
            
        Returns:
            ServiceResult with list of ExecutionFile records
            
        Example:
            # Get all files created by profile_split step
            service.get_files_by_step("exec-123", "profile_split")
        """
        query_model = ExecutionFile()
        query_model.execution_id = execution_id
        query_model.created_by_step = created_by_step
        # Leave file_id empty for begins_with query
        
        return self._query_by_index(
            query_model,
            "gsi3",
            limit=limit
        )

    @service_method("get_executions_by_file")
    def get_executions_by_file(
        self,
        file_id: str,
        limit: Optional[int] = None
    ) -> ServiceResult[List[ExecutionFile]]:
        """
        Reverse lookup: Get all executions that use a specific file.
        
        This is useful for tracking file usage and dependencies.
        
        Args:
            file_id: ID of the file
            limit: Optional limit on number of results
            
        Returns:
            ServiceResult with list of ExecutionFile records
            
        Example:
            # Find all executions that used this input file
            service.get_executions_by_file("file-456")
        """
        query_model = ExecutionFile()
        query_model.file_id = file_id
        # Leave execution_id empty for begins_with query
        
        return self._query_by_index(
            query_model,
            "gsi2",
            limit=limit
        )

    @service_method("get_file_count")
    def get_file_count(
        self,
        execution_id: str,
        file_type: Optional[str] = None
    ) -> ServiceResult[int]:
        """
        Get count of files for an execution.
        
        Args:
            execution_id: ID of the execution
            file_type: Optional filter by file type
            
        Returns:
            ServiceResult with count of files
        """
        result = self.get_files_by_execution(
            execution_id=execution_id,
            file_type=file_type
        )
        
        if not result.success:
            return ServiceResult.failure_result(result.message)
        
        count = len(result.data or [])
        return ServiceResult.success_result(count)

    @service_method("delete_all_links_for_execution")
    def delete_all_links_for_execution(
        self,
        execution_id: str
    ) -> ServiceResult[int]:
        """
        Delete all file links for an execution.
        
        This is typically used during execution cleanup/deletion.
        Note: This does not delete the actual files from FileSystem.
        
        Args:
            execution_id: ID of the execution
            
        Returns:
            ServiceResult with count of deleted links
        """
        result = self.get_files_by_execution(execution_id)
        if not result.success:
            return ServiceResult.failure_result(result.message)
        
        exec_files = result.data or []
        deleted_count = 0
        
        for exec_file in exec_files:
            delete_result = self._delete_model(exec_file)
            if delete_result.success:
                deleted_count += 1
        
        return ServiceResult.success_result(deleted_count)

    # Abstract method implementations
    @service_method("get_by_id")
    def get_by_id(self, **kwargs) -> ServiceResult[ExecutionFile]:
        """Get execution file link by composite key (execution_id + file_id)."""
        execution_id = kwargs.get("execution_id")
        file_id = kwargs.get("file_id")
        
        if not execution_id or not file_id:
            raise ValidationError("execution_id and file_id are required")
        
        return self.get_link(execution_id=execution_id, file_id=file_id)

    @service_method("update")
    def update(self, **kwargs) -> ServiceResult[ExecutionFile]:
        """
        Update execution file link metadata.
        
        Only metadata can be updated. To change type/role/step, delete and recreate.
        """
        execution_id = kwargs.get("execution_id")
        file_id = kwargs.get("file_id")
        
        if not execution_id or not file_id:
            raise ValidationError("execution_id and file_id are required")
        
        # Get existing link
        link_result = self.get_link(execution_id=execution_id, file_id=file_id)
        if not link_result.success:
            raise NotFoundError(f"ExecutionFile link not found: {execution_id} -> {file_id}")
        
        exec_file = link_result.data
        
        # Only allow updating metadata
        if "metadata" in kwargs:
            exec_file.metadata = kwargs["metadata"]
        
        exec_file.prep_for_save()
        return self._save_model(exec_file)

    @service_method("delete")
    def delete(self, **kwargs) -> ServiceResult[bool]:
        """Delete execution file link by composite key."""
        execution_id = kwargs.get("execution_id")
        file_id = kwargs.get("file_id")
        
        if not execution_id or not file_id:
            raise ValidationError("execution_id and file_id are required")
        
        return self.unlink_file(execution_id=execution_id, file_id=file_id)
