"""
Execution metrics service for tracking real-time execution counts.

Provides atomic counter operations for tracking active, queued, and completed
executions at both user and tenant levels.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import time
import uuid
from datetime import datetime, UTC
from typing import Optional, Dict, Any, List

from aws_lambda_powertools import Logger
from boto3_assist.dynamodb.dynamodb import DynamoDB

from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
from geek_cafe_saas_sdk.core.request_context import RequestContext
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.core.service_errors import NotFoundError

from ..models.workflow_metrics import WorkflowMetrics

logger = Logger()


class WorkflowMetricsService(DatabaseService[WorkflowMetrics]):
    """
    Service for managing workflow metrics.
    
    Provides atomic counter operations for real-time tracking of executions.
    Supports both user-level and tenant-level metrics.
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
    # Core CRUD Operations
    # =========================================================================

    @service_method("create_metrics")
    def create(
        self,
        metric_type: str = "execution",
        owner_id: Optional[str] = None,
        **kwargs
    ) -> ServiceResult[WorkflowMetrics]:
        """
        Create a new execution metrics record.
        
        Args:
            metric_type: Type of execution (e.g., "acme_workflow")
            owner_id: User ID for user-specific metrics, None for tenant-wide
            
        Returns:
            ServiceResult with created WorkflowMetrics
        """
        metrics = WorkflowMetrics()
        metrics.id = str(uuid.uuid4())
        metrics.tenant_id = self.request_context.authenticated_tenant_id
        metrics.owner_id = owner_id or WorkflowMetrics.TENANT_WIDE_OWNER
        metrics.metric_type = metric_type
        
        metrics.prep_for_save()
        return self._save_model(metrics)

    @service_method("get_metrics")
    def get(self, metrics_id: str) -> ServiceResult[WorkflowMetrics]:
        """Get execution metrics by ID."""
        metrics = self._get_by_id(metrics_id, WorkflowMetrics)
        if not metrics:
            raise NotFoundError(f"WorkflowMetrics {metrics_id} not found")
        return ServiceResult.success_result(metrics)

    @service_method("get_by_id")
    def get_by_id(self, **kwargs) -> ServiceResult[WorkflowMetrics]:
        """Get execution metrics by ID (abstract method implementation)."""
        metrics_id = kwargs.get("metrics_id") or kwargs.get("id")
        return self.get(metrics_id)

    @service_method("update_metrics")
    def update(self, **kwargs) -> ServiceResult[WorkflowMetrics]:
        """Update execution metrics (abstract method implementation)."""
        metrics_id = kwargs.get("metrics_id") or kwargs.get("id")
        metrics = self._get_by_id(metrics_id, WorkflowMetrics)
        if not metrics:
            raise NotFoundError(f"WorkflowMetrics {metrics_id} not found")
        
        # Update allowed fields
        for field in ["metric_type"]:
            if field in kwargs:
                setattr(metrics, field, kwargs[field])
        
        metrics.prep_for_save()
        return self._save_model(metrics)

    @service_method("delete_metrics")
    def delete(self, **kwargs) -> ServiceResult[bool]:
        """Delete execution metrics (abstract method implementation)."""
        metrics_id = kwargs.get("metrics_id") or kwargs.get("id")
        metrics = self._get_by_id(metrics_id, WorkflowMetrics)
        if not metrics:
            raise NotFoundError(f"WorkflowMetrics {metrics_id} not found")
        return self._delete_model(metrics)

    # =========================================================================
    # Metrics Lookup Operations
    # =========================================================================

    @service_method("get_or_create_user_metrics")
    def get_or_create_user_metrics(
        self,
        user_id: str,
        metric_type: str = "execution",
    ) -> ServiceResult[WorkflowMetrics]:
        """
        Get or create user-specific metrics record.
        
        Args:
            user_id: User ID
            metric_type: Type of execution
            
        Returns:
            ServiceResult with WorkflowMetrics
        """
        # Try to find existing
        result = self.get_user_metrics(user_id, metric_type)
        if result.success and result.data:
            return result
        
        # Create new
        return self.create(metric_type=metric_type, owner_id=user_id)

    @service_method("get_or_create_tenant_metrics")
    def get_or_create_tenant_metrics(
        self,
        metric_type: str = "execution",
    ) -> ServiceResult[WorkflowMetrics]:
        """
        Get or create tenant-wide metrics record.
        
        Args:
            metric_type: Type of execution
            
        Returns:
            ServiceResult with WorkflowMetrics
        """
        # Try to find existing
        result = self.get_tenant_metrics(metric_type)
        if result.success and result.data:
            return result
        
        # Create new
        return self.create(metric_type=metric_type, owner_id=WorkflowMetrics.TENANT_WIDE_OWNER)

    @service_method("get_user_metrics")
    def get_user_metrics(
        self,
        user_id: str,
        metric_type: str = "execution",
    ) -> ServiceResult[WorkflowMetrics]:
        """
        Get user-specific metrics.
        
        Args:
            user_id: User ID
            metric_type: Type of execution
            
        Returns:
            ServiceResult with WorkflowMetrics or None
        """
        tenant_id = self.request_context.authenticated_tenant_id
        
        query_model = WorkflowMetrics()
        query_model.tenant_id = tenant_id
        query_model.owner_id = user_id
        query_model.metric_type = metric_type
        
        result = self._query_by_index(query_model, "gsi2", limit=1)
        if result.success and result.data:
            return ServiceResult.success_result(result.data[0])
        return ServiceResult.success_result(None)

    @service_method("get_tenant_metrics")
    def get_tenant_metrics(
        self,
        metric_type: str = "execution",
    ) -> ServiceResult[WorkflowMetrics]:
        """
        Get tenant-wide metrics.
        
        Args:
            metric_type: Type of execution
            
        Returns:
            ServiceResult with WorkflowMetrics or None
        """
        tenant_id = self.request_context.authenticated_tenant_id
        
        query_model = WorkflowMetrics()
        query_model.tenant_id = tenant_id
        query_model.owner_id = WorkflowMetrics.TENANT_WIDE_OWNER
        query_model.metric_type = metric_type
        
        result = self._query_by_index(query_model, "gsi2", limit=1)
        if result.success and result.data:
            return ServiceResult.success_result(result.data[0])
        return ServiceResult.success_result(None)

    @service_method("get_current_counts")
    def get_current_counts(
        self,
        user_id: str,
        metric_type: str = "execution",
    ) -> ServiceResult[Dict[str, Any]]:
        """
        Get current execution counts for throttle decisions.
        
        Returns both user-level and tenant-level counts.
        
        Args:
            user_id: User ID
            metric_type: Type of execution
            
        Returns:
            ServiceResult with dict containing:
            - user_active: User's active count
            - user_queued: User's queued count
            - user_throttled: User's throttled count
            - tenant_active: Tenant's active count
            - tenant_queued: Tenant's queued count
            - tenant_throttled: Tenant's throttled count
        """
        user_result = self.get_user_metrics(user_id, metric_type)
        tenant_result = self.get_tenant_metrics(metric_type)
        
        user_metrics = user_result.data if user_result.success else None
        tenant_metrics = tenant_result.data if tenant_result.success else None
        
        counts = {
            "user_active": user_metrics.active_count if user_metrics else 0,
            "user_queued": user_metrics.queued_count if user_metrics else 0,
            "user_throttled": user_metrics.throttled_count if user_metrics else 0,
            "user_total_in_flight": user_metrics.total_in_flight if user_metrics else 0,
            "user_last_submission_ts": user_metrics.last_submission_ts if user_metrics else None,
            "user_submissions_this_hour": user_metrics.submissions_this_hour if user_metrics else 0,
            "user_submissions_this_day": user_metrics.submissions_this_day if user_metrics else 0,
            "tenant_active": tenant_metrics.active_count if tenant_metrics else 0,
            "tenant_queued": tenant_metrics.queued_count if tenant_metrics else 0,
            "tenant_throttled": tenant_metrics.throttled_count if tenant_metrics else 0,
            "tenant_total_in_flight": tenant_metrics.total_in_flight if tenant_metrics else 0,
        }
        
        return ServiceResult.success_result(counts)

    # =========================================================================
    # Atomic Counter Operations
    # =========================================================================

    @service_method("increment_queued")
    def increment_queued(
        self,
        user_id: str,
        metric_type: str = "execution",
    ) -> ServiceResult[bool]:
        """
        Increment queued count for both user and tenant.
        Also updates submission tracking for rate limiting.
        
        Args:
            user_id: User ID
            metric_type: Type of execution
            
        Returns:
            ServiceResult with success boolean
        """
        now = time.time()
        
        # Update user metrics
        user_result = self.get_or_create_user_metrics(user_id, metric_type)
        if user_result.success and user_result.data:
            metrics = user_result.data
            metrics.queued_count += 1
            metrics.total_submitted += 1
            metrics.last_submission_ts = now
            self._update_rate_windows(metrics, now)
            metrics.prep_for_save()
            self._save_model(metrics)
        
        # Update tenant metrics
        tenant_result = self.get_or_create_tenant_metrics(metric_type)
        if tenant_result.success and tenant_result.data:
            metrics = tenant_result.data
            metrics.queued_count += 1
            metrics.total_submitted += 1
            metrics.prep_for_save()
            self._save_model(metrics)
        
        return ServiceResult.success_result(True)

    @service_method("increment_throttled")
    def increment_throttled(
        self,
        user_id: str,
        metric_type: str = "execution",
    ) -> ServiceResult[bool]:
        """
        Increment throttled count for both user and tenant.
        
        Args:
            user_id: User ID
            metric_type: Type of execution
            
        Returns:
            ServiceResult with success boolean
        """
        now = time.time()
        
        # Update user metrics
        user_result = self.get_or_create_user_metrics(user_id, metric_type)
        if user_result.success and user_result.data:
            metrics = user_result.data
            metrics.throttled_count += 1
            metrics.total_submitted += 1
            metrics.last_submission_ts = now
            self._update_rate_windows(metrics, now)
            metrics.prep_for_save()
            self._save_model(metrics)
        
        # Update tenant metrics
        tenant_result = self.get_or_create_tenant_metrics(metric_type)
        if tenant_result.success and tenant_result.data:
            metrics = tenant_result.data
            metrics.throttled_count += 1
            metrics.total_submitted += 1
            metrics.prep_for_save()
            self._save_model(metrics)
        
        return ServiceResult.success_result(True)

    @service_method("start_execution")
    def start_execution(
        self,
        user_id: str,
        metric_type: str = "execution",
        from_throttled: bool = False,
    ) -> ServiceResult[bool]:
        """
        Record execution start: decrement queued/throttled, increment active.
        
        Args:
            user_id: User ID
            metric_type: Type of execution
            from_throttled: Whether this was from the throttle queue
            
        Returns:
            ServiceResult with success boolean
        """
        # Update user metrics
        user_result = self.get_or_create_user_metrics(user_id, metric_type)
        if user_result.success and user_result.data:
            metrics = user_result.data
            if from_throttled:
                metrics.throttled_count = max(0, metrics.throttled_count - 1)
            else:
                metrics.queued_count = max(0, metrics.queued_count - 1)
            metrics.active_count += 1
            metrics.prep_for_save()
            self._save_model(metrics)
        
        # Update tenant metrics
        tenant_result = self.get_or_create_tenant_metrics(metric_type)
        if tenant_result.success and tenant_result.data:
            metrics = tenant_result.data
            if from_throttled:
                metrics.throttled_count = max(0, metrics.throttled_count - 1)
            else:
                metrics.queued_count = max(0, metrics.queued_count - 1)
            metrics.active_count += 1
            metrics.prep_for_save()
            self._save_model(metrics)
        
        return ServiceResult.success_result(True)

    @service_method("complete_execution")
    def complete_execution(
        self,
        user_id: str,
        metric_type: str = "execution",
        success: bool = True,
        profile_count: int = 0,
        duration_ms: int = 0,
    ) -> ServiceResult[bool]:
        """
        Record execution completion: decrement active, update totals.
        
        Args:
            user_id: User ID
            metric_type: Type of execution
            success: Whether execution succeeded
            profile_count: Number of profiles processed
            duration_ms: Execution duration in milliseconds
            
        Returns:
            ServiceResult with success boolean
        """
        # Update user metrics
        user_result = self.get_or_create_user_metrics(user_id, metric_type)
        if user_result.success and user_result.data:
            metrics = user_result.data
            metrics.active_count = max(0, metrics.active_count - 1)
            if success:
                metrics.total_completed += 1
            else:
                metrics.total_failed += 1
            metrics.total_profiles += profile_count
            metrics.prep_for_save()
            self._save_model(metrics)
        
        # Update tenant metrics
        tenant_result = self.get_or_create_tenant_metrics(metric_type)
        if tenant_result.success and tenant_result.data:
            metrics = tenant_result.data
            metrics.active_count = max(0, metrics.active_count - 1)
            if success:
                metrics.total_completed += 1
            else:
                metrics.total_failed += 1
            metrics.total_profiles += profile_count
            metrics.prep_for_save()
            self._save_model(metrics)
        
        return ServiceResult.success_result(True)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _update_rate_windows(self, metrics: WorkflowMetrics, now: float) -> None:
        """Update rolling rate limit windows."""
        hour_seconds = 3600
        day_seconds = 86400
        
        # Check if hour window needs reset
        if metrics.hour_window_start_ts is None or (now - metrics.hour_window_start_ts) >= hour_seconds:
            metrics.hour_window_start_ts = now
            metrics.submissions_this_hour = 1
        else:
            metrics.submissions_this_hour += 1
        
        # Check if day window needs reset
        if metrics.day_window_start_ts is None or (now - metrics.day_window_start_ts) >= day_seconds:
            metrics.day_window_start_ts = now
            metrics.submissions_this_day = 1
        else:
            metrics.submissions_this_day += 1
