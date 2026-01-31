# Database Service

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Dict, Any, List, Optional, TYPE_CHECKING
from boto3_assist.dynamodb.dynamodb import DynamoDB, DynamoDBIndex
from ..service_result import ServiceResult
from ..service_errors import ValidationError, AccessDeniedError, NotFoundError
from ..error_codes import ErrorCode
from ..request_context import RequestContext
from ..retry_config import RetryConfig, DEFAULT_RETRY_CONFIG
from ..decorators import with_throttling_retry, is_throttling_error, RetryDiagnostics
import os
import time
from aws_lambda_powertools import Logger

# Import audit logging infrastructure
from ..audit import AuditEvent, AuditAction, AuditLoggerFactory
# Import access control infrastructure
from ..access import AccessChecker, AccessLevel, AccessResult, IShareChecker, NoOpShareChecker
if TYPE_CHECKING:
    from ..audit import IAuditLogger

T = TypeVar("T")

logger = Logger()


class DatabaseService(ABC, Generic[T]):
    """Base service class for database operations with AUTOMATIC security and audit logging.
    
    SECURITY (Job Zero - Always On):
        All CRUD operations automatically enforce access control:
        - READ: Checks owner, admin, or resource share (VIEW permission)
        - UPDATE: Checks owner, admin, or resource share (EDIT permission)
        - DELETE: Checks owner or admin only (no share-based delete)
        
        Access is granted if ANY of these conditions are met:
        1. User is platform_admin (full access everywhere)
        2. User is tenant_admin (full access within their tenant)
        3. User is the resource owner (owner_id or created_by_id matches)
        4. User has a valid ResourceShare for this resource
        
        Security CANNOT be disabled. The only escape hatch is `skip_access_check=True`
        for rare internal operations where access was already verified.
    
    Audit Logging:
        When configured via environment variables, all CRUD operations are
        automatically logged to the configured audit destination (DynamoDB, S3, or both).
        
        Environment Variables:
            AUDIT_LOG_ENABLED: "true" to enable audit logging
            AUDIT_LOG_DESTINATION: "dynamodb", "s3", or "both"
            AUDIT_LOG_TABLE_NAME: DynamoDB table for audit logs
            AUDIT_LOG_BUCKET_NAME: S3 bucket for audit logs
        
        Audit events capture:
            - Who: user_id, tenant_id, user_email
            - What: action (CREATE/UPDATE/DELETE), resource_type, resource_id
            - When: timestamp
            - Changes: old_values, new_values, changed_fields
    """

    def __init__(
        self,
        *,
        dynamodb: Optional[DynamoDB] = None,
        table_name: Optional[str] = None,
        request_context: RequestContext,
        audit_logger: Optional["IAuditLogger"] = None,
        retry_config: Optional[RetryConfig] = None
    ):
        """
        Initialize DatabaseService with AUTOMATIC security.
        
        Args:
            dynamodb: DynamoDB client instance (auto-created with connection pooling if not provided)
            table_name: DynamoDB table name (falls back to DYNAMODB_TABLE_NAME env var)
            request_context: **REQUIRED** Security context with JWT token
            audit_logger: Optional audit logger (auto-configured from environment if not provided)
            retry_config: Optional retry configuration (defaults to enabled with 5 retries)
            
        Raises:
            ValueError: If table_name cannot be determined
            AccessDeniedError: If request_context is not provided
            
        Security:
            Access control is AUTOMATIC and ALWAYS ON. The share checker is
            automatically initialized to check ResourceShare records in the
            same table. Security cannot be disabled.
        
        Connection Pooling:
            If dynamodb is not provided, a pooled connection is automatically created
            using DynamoDB.from_pool() for optimal Lambda performance.
        
        Retry Configuration:
            By default, retry is ENABLED with 5 attempts and exponential backoff.
            To disable retry: retry_config=RetryConfig.disabled()
            For aggressive retry: retry_config=RetryConfig.aggressive()
            For conservative retry: retry_config=RetryConfig.conservative()
        """
        if request_context is None:
            raise AccessDeniedError("request_context is required for all database operations. All services must have security context.")
        
        # Store retry configuration (default to enabled)
        self._retry_config = retry_config or DEFAULT_RETRY_CONFIG
        
        # Auto-inject dynamodb with connection pooling if not provided
        if dynamodb is None:
            from boto3_assist.dynamodb.dynamodb import DynamoDB
            aws_region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
            aws_endpoint_url = (
                os.getenv("AWS_ENDPOINT_URL")
                or os.getenv("AWS_DYNAMODB_ENDPOINT_URL")
                or os.getenv("DYNAMODB_ENDPOINT_URL")
            )
            dynamodb = DynamoDB.from_pool(
                aws_profile=os.getenv("AWS_PROFILE"),
                aws_region=aws_region,
                aws_end_point_url=aws_endpoint_url,
            )
        
        # Auto-inject table_name from environment if not provided
        if not table_name:
            table_name = os.getenv("DYNAMODB_TABLE_NAME") or os.getenv("TABLE_NAME")
            if not table_name:
                raise ValueError(
                    "table_name parameter is required. Provide it directly or set DYNAMODB_TABLE_NAME environment variable."
                )
        
        self.dynamodb = dynamodb
        self.table_name = table_name

        self.LOG_DYNAMO_DB_QUERY = os.getenv("LOG_DYNAMO_DB_QUERY", False)
        self._request_context = request_context
        
        # Initialize audit logger (auto-configured from environment if not provided)
        self._audit_logger = audit_logger or AuditLoggerFactory.create_from_environment(
            dynamodb=self.dynamodb
        )
        
        # Throttle "audit logging disabled" warnings
        # Set to -1 for unlimited warnings, 0 to disable, or positive number for max count
        self._audit_disabled_warning_limit = int(os.getenv("AUDIT_DISABLED_WARNING_LIMIT", "5"))
        self._audit_disabled_warning_count = 0
        
        # AUTOMATIC share checker - always enabled, uses same table for ResourceShare records
        # This is NOT optional - security is Job Zero
        # NOTE: Pass a lambda to get current context - this ensures checkers always use
        # the latest context even if _request_context is refreshed (e.g., handler injection)
        from ..access import ResourceShareChecker
        self._share_checker: IShareChecker = ResourceShareChecker(
            dynamodb=self.dynamodb,
            table_name=self.table_name,
            request_context=lambda: self._request_context
        )
        
        # Initialize access checker with share support - ALWAYS ON
        # Pass lambda to ensure it always uses current _request_context
        self._access_checker = AccessChecker(
            request_context=lambda: self._request_context,
            share_checker=self._share_checker
        )

        if not self._request_context:
            raise AccessDeniedError("Request context is required for all database operations")
    
    @property
    def request_context(self) -> RequestContext:
        """Get the request context (security token)."""
        if self._request_context is None:
            raise AccessDeniedError("No security context set for this service")
        return self._request_context
    
    @request_context.setter
    def request_context(self, value: RequestContext):
        """Set the request context (security token)."""
        self._request_context = value
    
    @property
    def audit_logger(self) -> "IAuditLogger":
        """Get the audit logger."""
        return self._audit_logger
    
    @audit_logger.setter
    def audit_logger(self, value: "IAuditLogger"):
        """Set the audit logger."""
        self._audit_logger = value
    
    @property
    def access_checker(self) -> AccessChecker:
        """Get the access checker (read-only - security cannot be modified)."""
        return self._access_checker

    @abstractmethod
    def create(self, tenant_id: str, user_id: str, **kwargs) -> ServiceResult[T]:
        """Create a new resource."""
        pass

    @abstractmethod
    def get_by_id(
        self, resource_id: str, tenant_id: str, user_id: str
    ) -> ServiceResult[T]:
        """Get resource by ID with access control."""
        pass

    @abstractmethod
    def update(
        self, resource_id: str, tenant_id: str, user_id: str, updates: Dict[str, Any]
    ) -> ServiceResult[T]:
        """Update resource with access control."""
        pass

    @abstractmethod
    def delete(
        self, resource_id: str, tenant_id: str, user_id: str
    ) -> ServiceResult[bool]:
        """Delete resource with access control."""
        pass

    def _is_system_context(self) -> bool:
        """
        Check if the current request context is a system context.
        
        System contexts are used for internal operations (background jobs,
        authorization lookups, etc.) and bypass normal security checks.
        
        Returns:
            True if this is a system context
        """
        if not self._request_context:
            return False
        # Check for system role or system user ID
        return (
            'system' in getattr(self._request_context, 'roles', []) or
            getattr(self._request_context, 'authenticated_user_id', None) == 'system'
        )

    def _validate_required_fields(
        self, data: Dict[str, Any], required_fields: List[str]
    ) -> None:
        """Validate required fields are present."""
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            if len(missing_fields) == 1:
                raise ValidationError(f"Field '{missing_fields[0]}' is required", missing_fields[0])
            else:
                field_list = "', '".join(missing_fields)
                raise ValidationError(f"Fields '{field_list}' are required", missing_fields)
    
    def _validate_owner_field(
        self, payload: Dict[str, Any], authenticated_user_id: str, field_name: str = "owner_id"
    ) -> str:
        """
        Validate and resolve owner field following Rule #3.
        
        Pattern:
        - Missing owner_id: Default to authenticated user (self-service)
        - Present owner_id with value: Use specified owner (admin-on-behalf)
        - Present owner_id but empty/null: ERROR (explicit but invalid)
        
        Args:
            payload: Request payload
            authenticated_user_id: User ID from JWT
            field_name: Name of owner field (default: "owner_id")
            
        Returns:
            Resolved owner user ID
            
        Raises:
            ValidationError: If owner_id is explicitly provided but empty/null
        """
        # Check if field is explicitly provided in payload
        if field_name in payload:
            owner_id = payload[field_name]
            # Explicit but empty/null = error (fail fast)
            if not owner_id:
                raise ValidationError(
                    f"{field_name} cannot be empty when explicitly provided",
                    field_name
                )
            return owner_id
        
        # Field not provided = default to authenticated user (self-service)
        return authenticated_user_id

    def _save_model(
        self,
        model: T,
        *,
        old_model: Optional[T] = None,
        preserve_timestamps: bool = False,
        skip_access_check: bool = False
    ) -> ServiceResult[T]:
        """Save model to database with **AUTOMATIC** security validation and audit trail.
        
        Args:
            model: Model to save
            old_model: Optional previous state of model (for UPDATE audit logging)
                      If provided, enables detailed change tracking in audit log.
            preserve_timestamps: If True, don't update modified_utc_ts.
                               Useful for migrations and data imports where
                               you want to preserve the original timestamps.
            skip_access_check: If True, skip access validation (use with caution -
                              only for internal operations where access was already verified)
        
        Returns:
            ServiceResult with saved model or error
            
        Security:
            - **AUTOMATIC** access validation for UPDATES (owner, admin, or edit share)
            - **ALWAYS** validates tenant access
            - **ALWAYS** auto-populates audit fields (created_by, updated_by)
            - **ALWAYS** prevents cross-tenant resource creation
            - request_context is required (enforced in __init__)
            
        Audit Logging:
            - Automatically logs CREATE or UPDATE events when audit logging is enabled
            - Captures old_values and new_values for change tracking
            - Fail-safe: audit failures don't break business operations
        """
        try:
            # MANDATORY security validation - always validate tenant access
            # EXCEPTION: SYSTEM tenant can provision new tenants (signup flow), sqs messages, etc
            from geek_cafe_saas_sdk.core.anonymous_context import AnonymousContextFactory
            is_system_tenant = (self._request_context.authenticated_tenant_id == 
                               AnonymousContextFactory.SYSTEM_TENANT_ID)
            
            if hasattr(model, 'tenant_id') and model.tenant_id:
                # SYSTEM tenant can create resources in any tenant (provisioning)
                if not is_system_tenant:
                    if not self._request_context.validate_tenant_access(model.tenant_id):
                        return ServiceResult.error_result(
                            ErrorCode.ACCESS_DENIED,
                            "Cannot save resources in other tenants"
                            f"Target Tenant ID: {model.tenant_id}, User Tenant ID: {self._request_context.authenticated_tenant_id}"
                        )
            
            if not old_model:
                try:
                    old_model = self._fetch_model_raw(model)
                except Exception as e:
                    logger.error(f"Failed to get old model: {e}")
                    pass
            # Determine if this is a CREATE or UPDATE
            # SIMPLE RULE: If old_model is provided, it's an UPDATE. Otherwise, it's a CREATE.
            # 
            # For proper UPDATE behavior (access check + audit logging with change tracking),
            # services SHOULD pass old_model when updating existing records:
            #   temp_model = ModelClass()
            #   temp_model.id = resource_id  # or set composite key fields
            #   old_model = self._fetch_model_raw(temp_model)
            #   # ... modify model ...
            #   return self._save_model(model, old_model=old_model)
            #
            # If old_model is not provided, we treat it as a CREATE (no access check needed
            # since the user is creating their own resource).
            is_create = old_model is None
            
            # AUTOMATIC access check for UPDATES (not creates)
            # For updates, user must have EDIT permission
            if not is_create and not skip_access_check and not is_system_tenant:
                access_result = self._access_checker.check_model_access(
                    model=model,
                    required_permission=AccessLevel.EDIT
                )
                
                if not access_result.granted:
                    return ServiceResult.error_result(
                        ErrorCode.ACCESS_DENIED,
                        f"You do not have permission to modify this resource. Reason: {access_result.reason}"
                    )
            
            # MANDATORY audit trail - always populate audit fields
            # Set created_by_id if this is a new resource
            if hasattr(model, 'created_by_id') and not model.created_by_id:
                model.created_by_id = self._request_context.authenticated_user_id
            
            # Always update updated_by_id
            if hasattr(model, 'updated_by_id'):
                model.updated_by_id = self._request_context.authenticated_user_id
            
            # Prepare model for save (sets id, timestamps, computes keys)
            # This is idempotent and safe to call multiple times
            if hasattr(model, 'prep_for_save') and callable(model.prep_for_save):
                model.prep_for_save(preserve_timestamps=preserve_timestamps)
            
            # Save with automatic retry on throttling
            # The boto3_assist library handles all GSI key population automatically.
            retry_diagnostics = self._save_with_retry(model)
            
            # Log audit event (fail-safe - doesn't break business operations)
            self._log_audit_event(
                action=AuditAction.CREATE if is_create else AuditAction.UPDATE,
                model=model,
                old_model=old_model,
                success=True
            )
            http_status = 201 if is_create else 200
            result = ServiceResult.success_result(model, http_status=http_status)
            
            # Add retry diagnostics if available
            if retry_diagnostics:
                result.diagnostics["retry"] = retry_diagnostics.to_dict()
            
            return result
        except Exception as e:
            # Log failed audit event
            self._log_audit_event(
                action=AuditAction.CREATE if old_model is None else AuditAction.UPDATE,
                model=model,
                old_model=old_model,
                success=False,
                error_message=str(e)
            )
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.DATABASE_SAVE_FAILED,
                context=f"Failed to save model to table {self.table_name}",
            )

    def _save_with_retry(self, model: T) -> Optional[RetryDiagnostics]:
        """
        Save a single model with configurable retry on throttling.
        
        This method wraps the DynamoDB save operation with exponential backoff
        retry logic to handle throttling exceptions automatically.
        
        Uses the retry_config from __init__ to determine retry behavior.
        
        Args:
            model: The model to save (already prepped with prep_for_save)
        
        Returns:
            RetryDiagnostics if retry_config.track_diagnostics=True, else None
        
        Raises:
            Exception: Re-raises non-throttling exceptions immediately
        """
        if not self._retry_config.enabled:
            # Retry disabled - save directly
            self.dynamodb.save(table_name=self.table_name, item=model)
            return None
        
        # Create decorator with config settings
        retry_decorator = with_throttling_retry(
            max_retries=self._retry_config.max_retries,
            base_delay=self._retry_config.base_delay,
            max_delay=self._retry_config.max_delay,
            exponential_base=self._retry_config.exponential_base,
            track_diagnostics=self._retry_config.track_diagnostics
        )
        
        # Wrap the save operation
        @retry_decorator
        def _do_save():
            self.dynamodb.save(table_name=self.table_name, item=model)
        
        # Execute with retry
        result = _do_save()
        
        # Extract diagnostics if tracking enabled
        if self._retry_config.track_diagnostics:
            _, diagnostics = result
            return diagnostics
        
        return None
    
    def _batch_save_models(
        self,
        models: List[T],
        *,
        old_models: Optional[List[Optional[T]]] = None,
        preserve_timestamps: bool = False,
        skip_access_check: bool = False
    ) -> ServiceResult[List[T]]:
        """
        Save multiple models in batch with automatic throttling retry.
        
        Uses DynamoDB batch_write_item for efficient bulk operations.
        Automatically handles:
        - Access validation for each model
        - Audit field population
        - Throttling retry with exponential backoff
        - Audit logging for all operations
        
        Args:
            models: List of models to save
            old_models: Optional list of previous states (for UPDATE audit logging)
            preserve_timestamps: If True, don't update modified_utc_ts
            skip_access_check: If True, skip access validation
        
        Returns:
            ServiceResult with list of saved models or error
        
        Example:
            # Create multiple file records
            files = [File(...), File(...), File(...)]
            result = self._batch_save_models(files)
            if result.success:
                print(f"Saved {len(result.data)} files")
        
        Note:
            - Maximum 25 items per batch (automatically chunked)
            - Unprocessed items are automatically retried
            - All models must pass access checks or entire batch fails
        """
        try:
            if not models:
                return ServiceResult.success_result([])
            
            # Validate and prepare all models
            prepared_models = []
            for idx, model in enumerate(models):
                old_model = old_models[idx] if old_models and idx < len(old_models) else None
                
                # Security validation (same as _save_model)
                from geek_cafe_saas_sdk.core.anonymous_context import AnonymousContextFactory
                is_system_tenant = (self._request_context.authenticated_tenant_id == 
                                   AnonymousContextFactory.SYSTEM_TENANT_ID)
                
                if hasattr(model, 'tenant_id') and model.tenant_id:
                    if not is_system_tenant:
                        if not self._request_context.validate_tenant_access(model.tenant_id):
                            return ServiceResult.error_result(
                                ErrorCode.ACCESS_DENIED,
                                f"Cannot save resources in other tenants (model {idx})"
                            )
                
                # Access check for updates
                is_create = old_model is None
                if not is_create and not skip_access_check and not is_system_tenant:
                    access_result = self._access_checker.check_model_access(
                        model=model,
                        required_permission=AccessLevel.EDIT
                    )
                    if not access_result.granted:
                        return ServiceResult.error_result(
                            ErrorCode.ACCESS_DENIED,
                            f"No permission to modify model {idx}: {access_result.reason}"
                        )
                
                # Populate audit fields
                if hasattr(model, 'created_by_id') and not model.created_by_id:
                    model.created_by_id = self._request_context.authenticated_user_id
                if hasattr(model, 'updated_by_id'):
                    model.updated_by_id = self._request_context.authenticated_user_id
                
                # Prepare model
                if hasattr(model, 'prep_for_save') and callable(model.prep_for_save):
                    model.prep_for_save(preserve_timestamps=preserve_timestamps)
                
                prepared_models.append(model)
            
            # Convert models to DynamoDB items
            items = [model.to_resource_dictionary() for model in prepared_models]
            
            # Batch write with automatic retry (boto3-assist handles this)
            response = self.dynamodb.batch_write_item(
                items=items,
                table_name=self.table_name,
                operation="put"
            )
            
            # Check for unprocessed items
            if response.get('UnprocessedCount', 0) > 0:
                unprocessed_count = response['UnprocessedCount']
                logger.error(
                    f"Batch save had {unprocessed_count} unprocessed items after retries"
                )
                return ServiceResult.error_result(
                    ErrorCode.DATABASE_SAVE_FAILED,
                    f"Failed to save {unprocessed_count} items after retries"
                )
            
            # Log audit events for all models
            for idx, model in enumerate(prepared_models):
                old_model = old_models[idx] if old_models and idx < len(old_models) else None
                is_create = old_model is None
                self._log_audit_event(
                    action=AuditAction.CREATE if is_create else AuditAction.UPDATE,
                    model=model,
                    old_model=old_model,
                    success=True
                )
            
            result = ServiceResult.success_result(prepared_models, http_status=201)
            
            # Add batch operation diagnostics
            if self._retry_config.track_diagnostics:
                result.diagnostics["batch_operation"] = {
                    "total_items": len(models),
                    "processed_items": response.get('ProcessedCount', len(models)),
                    "unprocessed_items": response.get('UnprocessedCount', 0),
                    "retry_enabled": self._retry_config.enabled,
                    "batch_size_limit": 25,
                    "chunks_processed": (len(models) + 24) // 25  # Ceiling division
                }
            
            return result
            
        except Exception as e:
            logger.exception(f"Batch save failed: {str(e)}")
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.DATABASE_SAVE_FAILED,
                context=f"Failed to batch save {len(models)} models to table {self.table_name}",
            )

    def _fetch_model_raw(self, model: T) -> Optional[T]:
        """
        Raw database fetch - NO security checks.
        
        INTERNAL USE ONLY. This method bypasses all security checks.
        Use _get_by_id() for normal operations.
        
        Works with both single-ID and composite-key models by using the
        model's actual primary key structure.
        
        Args:
            model: Model instance with key fields populated (e.g., id, or execution_id+file_id)
        
        Returns:
            Fetched model instance or None if not found
        
        Only use this for:
        - Building composite operations where you'll check access separately
        - Fetching old_model for audit logging comparison
        - System operations that have already verified access
        """
        key : Any = None
        try:
            # Use the model's actual key structure (works for single or composite keys)
            # Don't call prep_for_save() - we only need the key, not full validation
            key = model.get_key("primary").key()

            result = self.dynamodb.get(key=key, table_name=self.table_name)
            if not result or "Item" not in result:
                return None

            fetched_model = model.__class__()
            fetched_model.map(result["Item"])
            return fetched_model
        except Exception as e:
            logger.exception(
                {
                    "message": "Failed to fetch model (raw)",
                    "table_name": self.table_name,
                    "key": key,
                    "error": e
                },
            )
            return None

    def _get_by_id(
        self,
        resource_id: str,
        model_class,
        *,
        skip_security_check: bool = False,
        required_permission: AccessLevel = AccessLevel.VIEW,
        include_deleted: bool = True # getting by ID should always include deleted records
    ) -> Optional[T]:
        """
        Get model by ID - THE primary method for fetching resources.
        
        Security is ON by default. This method automatically:
        1. Requires authentication
        2. Fetches the resource from DynamoDB
        3. Validates access (owner, admin, tenant settings, shares)
        4. Returns None if access denied (prevents enumeration)
        
        Args:
            resource_id: The resource ID to fetch
            model_class: The model class to instantiate
            skip_security_check: Set True ONLY for system records without tenant data
                                or when access was already verified upstream.
                                Default: False (security ON)
            required_permission: Required permission level (VIEW, DOWNLOAD, EDIT)
            include_deleted: If True, returns soft-deleted items
            
        Returns:
            The model if found AND access granted, None otherwise
            
        Example:
            # Normal usage - security is automatic
            file = self._get_by_id(file_id, File)
            
            # System record without tenant - skip security
            config = self._get_by_id(config_id, SystemConfig, skip_security_check=True)
        """
        # Require authentication unless skipping security
        if not skip_security_check:
            self.request_context.require_authentication()
        
        # Fetch raw model - create temp instance with ID for single-key models
        temp_model = model_class()
        temp_model.id = resource_id
        model = self._fetch_model_raw(temp_model)
        if not model:
            return None
        
        # Filter deleted if requested
        if not include_deleted:
            if hasattr(model, 'is_deleted') and callable(model.is_deleted):
                if model.is_deleted():
                    return None
            elif hasattr(model, 'status') and model.status == 'deleted':
                return None
        
        # Skip security checks if requested (for system records)
        if skip_security_check:
            return model
        
        # CENTRALIZED SECURITY CHECK via AccessChecker
        access_result = self._access_checker.check_model_access(
            model=model,
            required_permission=required_permission
        )
        
        if access_result.granted:
            return model
        
        # Access denied - log the real reason for audit/troubleshooting, return None to hide existence
        logger.warning(
            f"Access denied for resource {resource_id}",
            extra={
                "resource_id": resource_id,
                "user_id": self._request_context.authenticated_user_id,
                "resource_tenant_id": getattr(model, 'tenant_id', None),
                "user_tenant_id": self._request_context.authenticated_tenant_id,
                "required_permission": required_permission.value,
                "denial_reason": access_result.reason,
                "action": "ACCESS_DENIED_MASKED_AS_NOT_FOUND"
            }
        )

        # Raise access denied error
        raise AccessDeniedError("Access denied for resource " + resource_id)

    def _delete_model(self, model: T, *, skip_access_check: bool = False) -> ServiceResult[bool]:
        """Delete model from database with **AUTOMATIC** access validation and audit logging.
        
        Args:
            model: Model to delete
            skip_access_check: If True, skip access validation (use with caution - 
                              only for internal operations where access was already verified)
            
        Returns:
            ServiceResult[bool] - True if successful
            
        Security:
            - **AUTOMATIC** access validation - only owner or admin can delete
            - Returns ACCESS_DENIED error if user lacks permission
            
        Audit Logging:
            - Logs DELETE event with full model state as old_values
            - Fail-safe: audit failures don't break business operations
        """
        try:
            # AUTOMATIC access check - only owner/admin can delete
            if not skip_access_check:
                resource_owner_id = getattr(model, 'owner_id', None) or getattr(model, 'created_by_id', None)
                resource_tenant_id = getattr(model, 'tenant_id', None)
                
                access_result = self._access_checker.check_access(
                    resource_id=model.id,
                    resource_owner_id=resource_owner_id,
                    resource_tenant_id=resource_tenant_id,
                    required_permission=AccessLevel.OWNER,  # Delete requires owner-level access
                    allow_tenant_access=False
                )
                
                # Only owner or admin can delete
                if not access_result.granted or access_result.level not in (AccessLevel.OWNER, AccessLevel.ADMIN):
                    return ServiceResult.error_result(
                        ErrorCode.ACCESS_DENIED,
                        "Only the owner or an admin can delete this resource"
                    )
            
            primary_key = model.get_key("primary").key()
            self.dynamodb.delete(table_name=self.table_name, primary_key=primary_key)
            
            # Log audit event for delete
            self._log_audit_event(
                action=AuditAction.DELETE,
                model=model,
                old_model=model,  # For DELETE, old_model is the deleted state
                success=True
            )
            
            return ServiceResult.success_result(True)
        except Exception as e:
            # Log failed audit event
            self._log_audit_event(
                action=AuditAction.DELETE,
                model=model,
                old_model=model,
                success=False,
                error_message=str(e)
            )
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.DATABASE_DELETE_FAILED,
                context=f"Failed to delete model from table {self.table_name}",
            )

    def _query_by_index(
        self,
        model: T,
        index_name: str,
        *,
        ascending: bool = False,
        strongly_consistent: bool = False,
        projection_expression: Optional[str] = None,
        expression_attribute_names: Optional[dict] = None,
        start_key: Optional[dict] = None,
        limit: Optional[int] = None,
        skip_security_check: bool = False,
        required_permission: AccessLevel = AccessLevel.VIEW,
        query_condition: str="begins_with",
        low_value: Optional[Any] = None,
        high_value: Optional[Any] = None
    ) -> ServiceResult[List[T]]:
        """
        Generic query method for GSI queries with **AUTOMATIC** security filtering.

        Security:
            - Requires authentication (unless skip_security_check=True)
            - Filters results to only include items the user has access to
            - Silently removes inaccessible items (prevents enumeration attacks)
            - Logs audit events for access denial attempts

        Args:
            model: The pre-configured model instance to use for the query
            index_name: The name of the GSI index to query
            ascending: Sort order (default: descending)
            strongly_consistent: Use strongly consistent reads
            projection_expression: DynamoDB projection expression
            expression_attribute_names: Expression attribute names
            start_key: Pagination start key
            limit: Maximum number of items to return
            skip_security_check: If True, skip access filtering (use with caution)
            required_permission: Required permission level for access check
            query_condition: Query condition type ("begins_with", "between", "eq", "gt", "gte", "lt")
            low_value: Low value for "between" condition (e.g., start timestamp)
            high_value: High value for "between" condition (e.g., end timestamp)

        Returns:
            ServiceResult containing a list of accessible model instances.
            Pagination info is included in error_details as 'last_evaluated_key' if more results exist.
        """
        try:
            # Require authentication unless skipping security
            if not skip_security_check:
                self.request_context.require_authentication()
            
            # Get the key for the specified index from the provided model
            if index_name == "primary":
                key = model.get_key("primary").key(
                    query_key=True, 
                    condition=query_condition,
                    low_value=low_value,
                    high_value=high_value
                )
            else:
                key = model.get_key(index_name).key(
                    condition=query_condition,
                    low_value=low_value,
                    high_value=high_value
                )

            
            self._log_dynamo_db_query(key=key, index_name=index_name)

            # Execute the query
            response = self.dynamodb.query(
                table_name=self.table_name,
                key=key,
                index_name=index_name,
                ascending=ascending,
                strongly_consistent=strongly_consistent,
                projection_expression=projection_expression,
                expression_attribute_names=expression_attribute_names,
                start_key=start_key,
                limit=limit,
            )

            # Extract items from response
            data = response.get("Items", [])

            # Map each item to a model instance
            model_class = type(model)
            all_items = [model_class().map(item) for item in data]

            # SECURITY FILTERING: Filter items by access
            if skip_security_check:
                accessible_items = all_items
            else:
                accessible_items = []
                denied_count = 0
                
                for item in all_items:
                    access_result = self._access_checker.check_model_access(
                        model=item,
                        required_permission=required_permission
                    )
                    
                    if access_result.granted:
                        accessible_items.append(item)
                    else:
                        denied_count += 1
                        # Log access denial for audit (silent filtering)
                        logger.debug(
                            f"List query filtered item due to access denial",
                            extra={
                                "resource_id": getattr(item, 'id', 'unknown'),
                                "resource_type": type(item).__name__,
                                "user_id": self._request_context.authenticated_user_id,
                                "denial_reason": access_result.reason,
                                "action": "LIST_ITEM_FILTERED"
                            }
                        )
                
                # Log audit event if any items were filtered
                if denied_count > 0:
                    self._log_list_access_denial(
                        index_name=index_name,
                        total_found=len(all_items),
                        denied_count=denied_count,
                        model_class=model_class
                    )

            # Include pagination info if present
            result = ServiceResult.success_result(accessible_items)
            if "LastEvaluatedKey" in response:
                result.metadata = {"last_evaluated_key": response["LastEvaluatedKey"]}

            return result

        except Exception as e:
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.DATABASE_QUERY_FAILED,
                context=f"Failed to query index {index_name} on table {self.table_name}",
            )
    
    def _log_dynamo_db_query(self, key: Any, index_name: str) -> None:
        """Log DynamoDB query for debugging."""

        query: dict = {}
        try:
            if hasattr(DynamoDBIndex, 'extract_key_values'):
                query = DynamoDBIndex.extract_key_values(key)
                
            else:
                try:
                    query = {
                        'pk': key._values[0]._values[1],
                        'sk': key._values[1]._values[1],
                        'operator': key._values[1].expression_operator,
                        'format': key._values[1].expression_format,
                        'index_name': index_name
                    }            
                except Exception as e:
                    logger.error(f"Failed to extract key values: {e}")
        except Exception as e:
            logger.error(f"Failed to extract key values: str{e}")

        message = {
            "index_name": index_name,
            "query": query
        }
        if self.LOG_DYNAMO_DB_QUERY:
            logger.info(message)
        else:
            logger.debug(message)

    def _log_list_access_denial(
        self,
        index_name: str,
        total_found: int,
        denied_count: int,
        model_class: type
    ) -> None:
        """
        Log an audit event when list query results are filtered due to access denial.
        
        This helps detect potential unauthorized access attempts or misconfigured permissions.
        """
        try:
            if not self._audit_logger or not self._audit_logger.is_enabled:
                return
            
            event = AuditEvent()
            
            # Actor
            event.actor_tenant_id = self._request_context.authenticated_tenant_id
            event.actor_user_id = self._request_context.authenticated_user_id
            event.actor_email = getattr(self._request_context, 'authenticated_email', '') or ''
            
            # Resource owner - same as actor for list queries
            event.tenant_id = self._request_context.authenticated_tenant_id
            event.user_id = self._request_context.authenticated_user_id
            
            # What
            event.action = "LIST_ACCESS_FILTERED"
            event.resource_type = model_class.__name__
            event.resource_id = f"query:{index_name}"
            event.service_name = self.__class__.__name__
            event.source_table_name = self.table_name
            event.success = True  # The query succeeded, items were just filtered
            event.new_values = {
                "index_name": index_name,
                "total_found": total_found,
                "denied_count": denied_count,
                "accessible_count": total_found - denied_count
            }
            
            self._audit_logger.log(event)
            
        except Exception as e:
            logger.warning(f"Failed to log list access denial audit event: {e}")

    def _delete_by_composite_key(
        self,
        pk: str,
        sk: str,
    ) -> ServiceResult[bool]:
        """
        Delete an item by composite key (pk + sk).
        
        Useful for adjacent record patterns where items use composite keys
        instead of a single id field.
        
        Args:
            pk: Partition key value
            sk: Sort key value
            
        Returns:
            ServiceResult[bool] - True if successful
            
        Example:
            # Delete a specific member from a channel
            result = self._delete_by_composite_key(
                pk="channel#channel_123",
                sk="member#user_456"
            )
        """
        try:
            # Use boto3 resource (simpler API that handles typing)
            key = {"pk": pk, "sk": sk}
            self.dynamodb.delete(table_name=self.table_name, primary_key=key)
            return ServiceResult.success_result(True)
            
        except Exception as e:
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.DATABASE_DELETE_FAILED,
                context=f"Failed to delete item by composite key from table {self.table_name}",
            )

    def _handle_service_exception(
        self, e: Exception, operation: str, **context
    ) -> ServiceResult[T]:
        """
        Common exception handler for service operations.
        
        Maps exception types to standardized error codes and formats error details.
        Always includes operation name in error details for debugging.
        
        Args:
            e: The exception that was raised
            operation: Name of the operation that failed (for logging/debugging)
            **context: Additional context information (resource_id, tenant_id, etc.)
        
        Returns:
            ServiceResult with appropriate error information
        """
        # Build base error details with operation
        error_details = {"operation": operation, **context}
        
        # Validation errors (4xx equivalent)
        if isinstance(e, ValidationError):
            field_info = getattr(e, "field", None)
            # Handle both single field and list of fields
            if isinstance(field_info, list):
                error_details["fields"] = field_info
            elif field_info:
                error_details["field"] = field_info
            
            return ServiceResult.error_result(
                message=f"Validation failed: {str(e)}",
                error_code=ErrorCode.VALIDATION_ERROR,
                error_details=error_details,
            )
        
        # Authorization errors (403 equivalent)
        elif isinstance(e, AccessDeniedError):
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.ACCESS_DENIED,
                error_details=error_details
            )
        
        # Resource not found (404 equivalent)
        elif isinstance(e, NotFoundError):
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.NOT_FOUND,
                error_details=error_details
            )
        
        # Unexpected errors (500 equivalent)
        else:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context=f"Operation '{operation}' failed: {str(e)}"
            )

    # ========== Audit Logging Methods ==========
    
    def _log_audit_disabled_warning(self) -> None:
        """
        Log a throttled warning when audit logging is disabled.
        
        Controlled by AUDIT_DISABLED_WARNING_LIMIT environment variable:
        - Positive number (default 5): Log warning up to N times, then silence
        - 0: Never log the warning
        - -1: Always log the warning (unlimited)
        
        Examples:
            AUDIT_DISABLED_WARNING_LIMIT=5   # Log first 5 times, then silence
            AUDIT_DISABLED_WARNING_LIMIT=0   # Never log
            AUDIT_DISABLED_WARNING_LIMIT=-1  # Always log (no limit)
        """
        # Check if warnings are disabled
        if self._audit_disabled_warning_limit == 0:
            return
        
        # Check if we've hit the limit (but not if unlimited)
        if self._audit_disabled_warning_limit > 0 and self._audit_disabled_warning_count >= self._audit_disabled_warning_limit:
            return
        
        # Increment counter
        self._audit_disabled_warning_count += 1
        
        # Build warning message
        if self._audit_disabled_warning_limit == -1:
            # Unlimited warnings
            message = f"Audit logging is disabled (warning #{self._audit_disabled_warning_count})"
        elif self._audit_disabled_warning_count < self._audit_disabled_warning_limit:
            # Not at limit yet
            remaining = self._audit_disabled_warning_limit - self._audit_disabled_warning_count
            message = (
                f"Audit logging is disabled "
                f"(warning {self._audit_disabled_warning_count}/{self._audit_disabled_warning_limit}, "
                f"{remaining} more will be shown)"
            )
        else:
            # Final warning
            message = (
                f"Audit logging is disabled "
                f"(warning {self._audit_disabled_warning_count}/{self._audit_disabled_warning_limit}, "
                f"this message will now be silenced. Set AUDIT_DISABLED_WARNING_LIMIT=-1 for unlimited warnings)"
            )
        
        logger.warning(message)
    
    def _log_audit_event(
        self,
        action: str,
        model: T,
        *,
        old_model: Optional[T] = None,
        success: bool = True,
        error_message: str = ""
    ) -> None:
        """
        Log an audit event for a database operation.
        
        This method is fail-safe - audit logging failures will not break
        business operations. Errors are logged but not raised.
        
        Args:
            action: The action performed (CREATE, UPDATE, DELETE, etc.)
            model: The model being operated on (current/new state)
            old_model: Previous state of model (for UPDATE/DELETE operations)
            success: Whether the operation succeeded
            error_message: Error message if operation failed
        """
        try:
            # Skip if audit logging is disabled
            if not self._audit_logger or not self._audit_logger.is_enabled:
                self._log_audit_disabled_warning()
                return
            
            # Extract model information
            resource_type = self._get_model_resource_type(model)
            resource_id = getattr(model, 'id', '') or ''
            resource_name = self._get_model_resource_name(model)
            tenant_id = getattr(model, 'tenant_id', '') or self._request_context.authenticated_tenant_id
            
            # Build old/new values for change tracking
            old_values = {}
            new_values = {}
            
            if old_model is not None:
                old_values = self._model_to_audit_dict(old_model)
            
            if action != AuditAction.DELETE:
                new_values = self._model_to_audit_dict(model)
            
            # Get resource owner user_id if available
            resource_owner_id = getattr(model, 'owner_id', '') or getattr(model, 'user_id', '') or ''
            
            # Create audit event (AuditEvent is now an alias for AuditLog model)
            event = AuditEvent()
            
            # Actor (who performed the action)
            event.actor_tenant_id = self._request_context.authenticated_tenant_id
            event.actor_user_id = self._request_context.authenticated_user_id
            event.actor_email = getattr(self._request_context, 'authenticated_email', '') or ''
            
            # Resource owner (whose data is being modified)
            event.tenant_id = tenant_id
            event.user_id = resource_owner_id
            
            # What
            event.action = action
            event.resource_type = resource_type
            event.resource_id = resource_id
            event.resource_name = resource_name
            event.old_values = old_values
            event.new_values = new_values
            event.service_name = self.__class__.__name__
            event.source_table_name = self.table_name
            event.success = success
            event.error_message = error_message
            event.resource_class_name = self._get_model_class_name(model)
            # Compute changed fields
            event.compute_changed_fields()
            
            # Log the event (fail-safe)
            self._audit_logger.log(event)
            
        except Exception as e:
            # Audit logging should never break business operations
            logger.warning(
                f"Failed to log audit event: {e}",
                extra={
                    "action": action,
                    "model_type": type(model).__name__ if model else "unknown",
                    "error": str(e)
                }
            )
    
    def _get_model_class_name(self, model: T) -> str:
        """
        Get the resource type name from a model (the class name).
        
        Args:
            model: The model instance
            
        Returns:
            Resource type string (e.g., "file", "directory", "user")
        """
        if hasattr(model, 'class_name'):
            return model.class_name()
        
        # Fallback: convert class name to snake_case
        class_name = type(model).__name__
        # Simple snake_case conversion
        return class_name

    def _get_model_resource_type(self, model: T) -> str:
        """
        Get the resource type name from a model (the class name).
        
        Args:
            model: The model instance
            
        Returns:
            Resource type string (e.g., "file", "directory", "user")
        """
        if hasattr(model, 'model_name') and model.model_name:
            return str(model.model_name)
        return 'unknown'
    
    def _get_model_resource_name(self, model: T) -> str:
        """
        Get a human-readable name for the resource (the model name).
        
        Args:
            model: The model instance
            
        Returns:
            Resource name or empty string if not found
        """
        if hasattr(model, 'model_name') and model.model_name:
            return str(model.model_name)
        return 'unknown'
    
    def _model_to_audit_dict(self, model: T) -> Dict[str, Any]:
        """
        Convert a model to a dictionary for audit logging.
        
        Excludes internal fields (starting with _) and large binary data.
        
        Args:
            model: The model instance
            
        Returns:
            Dictionary of model fields suitable for audit logging
        """
        try:
            # Use model's to_dictionary if available
            if hasattr(model, 'to_dictionary') and callable(model.to_dictionary):
                data = model.to_dictionary()
            else:
                # Fallback: extract public attributes
                data = {
                    k: v for k, v in model.__dict__.items()
                    if not k.startswith('_')
                }
            
            # Filter out large values and sensitive data
            filtered = {}
            for key, value in data.items():
                # Skip internal keys
                if key.startswith('_'):
                    continue
                # Skip index-related keys (pk, sk, gsi*_pk, gsi*_sk)
                if key in ('pk', 'sk') or key.startswith('gsi'):
                    continue
                # Skip large binary data
                if isinstance(value, bytes) and len(value) > 1000:
                    filtered[key] = f"<binary data: {len(value)} bytes>"
                    continue
                # Skip large strings (likely file content)
                if isinstance(value, str) and len(value) > 10000:
                    filtered[key] = f"<large string: {len(value)} chars>"
                    continue
                filtered[key] = value
            
            return filtered
            
        except Exception as e:
            logger.warning(f"Failed to convert model to audit dict: {e}")
            return {"error": f"Failed to serialize: {str(e)}"}
    
    def log_custom_audit_event(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        *,
        resource_name: str = "",
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: str = ""
    ) -> None:
        """
        Log a custom audit event for operations not covered by standard CRUD.
        
        Use this for custom actions like:
        - SHARE / UNSHARE
        - APPROVE / REJECT
        - DOWNLOAD / UPLOAD
        - LOGIN / LOGOUT
        
        Args:
            action: Custom action name (e.g., "SHARE", "APPROVE")
            resource_type: Type of resource (e.g., "file", "workflow")
            resource_id: ID of the resource
            resource_name: Human-readable name (optional)
            old_values: State before the action (optional)
            new_values: State after the action (optional)
            metadata: Additional context (optional)
            success: Whether the operation succeeded
            error_message: Error message if failed
            
        Example:
            self.log_custom_audit_event(
                action="SHARE",
                resource_type="file",
                resource_id="file_123",
                resource_name="report.pdf",
                new_values={"shared_with": "user_456", "permission": "read"},
                metadata={"share_type": "direct"}
            )
        """
        try:
            if not self._audit_logger or not self._audit_logger.is_enabled:
                return
            
            # Create audit event (AuditEvent is now an alias for AuditLog model)
            event = AuditEvent()
            
            # Actor (who performed the action)
            event.actor_tenant_id = self._request_context.authenticated_tenant_id
            event.actor_user_id = self._request_context.authenticated_user_id
            event.actor_email = getattr(self._request_context, 'authenticated_email', '') or ''
            
            # Resource owner - defaults to actor for custom events
            event.tenant_id = self._request_context.authenticated_tenant_id
            event.user_id = self._request_context.authenticated_user_id
            
            # What
            event.action = action
            event.resource_type = resource_type
            event.resource_id = resource_id
            event.resource_name = resource_name
            event.old_values = old_values or {}
            event.new_values = new_values or {}
            event.audit_metadata = metadata or {}
            event.service_name = self.__class__.__name__
            event.source_table_name = self.table_name
            event.success = success
            event.error_message = error_message
            
            event.compute_changed_fields()
            self._audit_logger.log(event)
            
        except Exception as e:
            logger.warning(f"Failed to log custom audit event: {e}")
