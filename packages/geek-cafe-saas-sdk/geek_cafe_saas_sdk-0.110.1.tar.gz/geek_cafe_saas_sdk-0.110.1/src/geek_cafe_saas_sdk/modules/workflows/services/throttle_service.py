"""
Throttle service for evaluating execution rate limits.

Evaluates current metrics against throttle configuration to determine
whether to allow, throttle, or reject execution requests.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import os
import time
from dataclasses import dataclass
from datetime import datetime, UTC, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List

from aws_lambda_powertools import Logger

from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.request_context import RequestContext
from geek_cafe_saas_sdk.core.error_codes import ErrorCode

from ..models.throttle_config import ThrottleConfig
from .workflow_metrics_service import WorkflowMetricsService
from .throttle_config_service import ThrottleConfigService

logger = Logger()


class ThrottleDecision(Enum):
    """Throttle evaluation decision."""
    ALLOW = "allow"          # Proceed to primary queue
    THROTTLE = "throttle"    # Send to throttle/delay queue
    REJECT = "reject"        # Hard reject (429)


@dataclass
class ThrottleResult:
    """Result of throttle evaluation."""
    decision: ThrottleDecision
    reason: str
    delay_seconds: int = 0
    details: Optional[Dict[str, Any]] = None
    
    @property
    def is_allowed(self) -> bool:
        """Check if execution is allowed."""
        return self.decision == ThrottleDecision.ALLOW
    
    @property
    def is_throttled(self) -> bool:
        """Check if execution should be throttled."""
        return self.decision == ThrottleDecision.THROTTLE
    
    @property
    def is_rejected(self) -> bool:
        """Check if execution should be rejected."""
        return self.decision == ThrottleDecision.REJECT


class ThrottleService:
    """
    Service for evaluating throttle decisions.
    
    Evaluates current execution metrics against throttle configuration
    to determine whether to allow, throttle, or reject new executions.
    
    This service does NOT extend DatabaseService as it doesn't directly
    manage database records - it uses WorkflowMetricsService and
    ThrottleConfigService for data access.
    """

    def __init__(
        self,
        metrics_service: WorkflowMetricsService,
        config_service: ThrottleConfigService,
        request_context: Optional[RequestContext] = None,
    ):
        """
        Initialize throttle service.
        
        Args:
            metrics_service: Service for accessing execution metrics
            config_service: Service for accessing throttle configs
            request_context: Security context
        """
        self._metrics_service = metrics_service
        self._config_service = config_service
        self._request_context = request_context

    @property
    def request_context(self) -> RequestContext:
        """Get the request context."""
        return self._request_context

    @request_context.setter
    def request_context(self, value: RequestContext):
        """Set the request context."""
        self._request_context = value

    def evaluate(
        self,
        user_id: str,
        metric_type: str = "execution",
        estimated_profiles: Optional[int] = None,
        reconcile: bool = True,
    ) -> ServiceResult[ThrottleResult]:
        """
        Evaluate whether a new execution should be allowed, throttled, or rejected.
        
        Checks in order:
        1. Throttling enabled check
        2. Metrics reconciliation (if enabled) - cleans up stale workflows
        3. Rate limit check (min interval between submissions)
        4. Hourly/daily submission limits
        5. User concurrent/queued limits
        6. Tenant concurrent/queued limits
        7. Profile count limits (if estimated_profiles provided)
        8. Throttle queue depth check
        
        Args:
            user_id: User ID submitting the execution
            metric_type: Type of execution
            estimated_profiles: Optional estimated profile count for pre-check
            reconcile: If True, reconcile metrics from actual workflows (default: True)
            
        Returns:
            ServiceResult with ThrottleResult
        """
        try:
            # Get effective config
            config_result = self._config_service.get_effective_config(user_id, metric_type)
            if not config_result.success:
                # If we can't get config, allow by default (fail open)
                logger.warning("Could not get throttle config, allowing by default")
                return ServiceResult.success_result(ThrottleResult(
                    decision=ThrottleDecision.ALLOW,
                    reason="Config unavailable, allowing by default"
                ))
            
            config = config_result.data
            
            # Reconcile metrics if enabled (cleans up stale workflows)
            if reconcile:
                self._reconcile_metrics(user_id, metric_type)
            
            # Check if throttling is enabled
            if not config.throttling_enabled:
                return ServiceResult.success_result(ThrottleResult(
                    decision=ThrottleDecision.ALLOW,
                    reason="Throttling disabled"
                ))
            
            # Get current metrics
            counts_result = self._metrics_service.get_current_counts(user_id, metric_type)
            if not counts_result.success:
                # If we can't get metrics, allow by default (fail open)
                logger.warning("Could not get metrics, allowing by default")
                return ServiceResult.success_result(ThrottleResult(
                    decision=ThrottleDecision.ALLOW,
                    reason="Metrics unavailable, allowing by default"
                ))
            
            counts = counts_result.data
            now = time.time()
            
            # Build details for debugging
            details = {
                "config_type": config.config_type,
                "user_id": user_id,
                "counts": counts,
                "estimated_profiles": estimated_profiles,
            }
            
            # Check 1: Rate limit (min interval between submissions)
            if config.rate_limit_enabled:
                last_submission = counts.get("user_last_submission_ts")
                if last_submission:
                    elapsed = now - last_submission
                    if elapsed < config.min_submission_interval_seconds:
                        return ServiceResult.success_result(ThrottleResult(
                            decision=ThrottleDecision.THROTTLE,
                            reason=f"Rate limit: {elapsed:.1f}s since last submission, minimum is {config.min_submission_interval_seconds}s",
                            delay_seconds=config.throttle_delay_seconds,
                            details=details
                        ))
            
            # Check 2: Hourly submission limit
            if config.rate_limit_enabled:
                submissions_this_hour = counts.get("user_submissions_this_hour", 0)
                if submissions_this_hour >= config.max_submissions_per_hour:
                    return ServiceResult.success_result(ThrottleResult(
                        decision=ThrottleDecision.THROTTLE,
                        reason=f"Hourly limit reached: {submissions_this_hour}/{config.max_submissions_per_hour}",
                        delay_seconds=config.throttle_delay_seconds,
                        details=details
                    ))
            
            # Check 3: Daily submission limit
            if config.rate_limit_enabled:
                submissions_this_day = counts.get("user_submissions_this_day", 0)
                if submissions_this_day >= config.max_submissions_per_day:
                    return ServiceResult.success_result(ThrottleResult(
                        decision=ThrottleDecision.REJECT,
                        reason=f"Daily limit reached: {submissions_this_day}/{config.max_submissions_per_day}",
                        details=details
                    ))
            
            # Check 4: User concurrent limit
            user_active = counts.get("user_active", 0)
            if user_active >= config.max_concurrent_per_user:
                return ServiceResult.success_result(ThrottleResult(
                    decision=ThrottleDecision.THROTTLE,
                    reason=f"User concurrent limit: Active={user_active}, Max={config.max_concurrent_per_user}",
                    delay_seconds=config.throttle_delay_seconds,
                    details=details
                ))
            
            # Check 5: User queued limit
            user_queued = counts.get("user_queued", 0)
            user_throttled = counts.get("user_throttled", 0)
            user_total_queued = user_queued + user_throttled
            if user_total_queued >= config.max_queued_per_user:
                if config.reject_when_throttle_full:
                    return ServiceResult.success_result(ThrottleResult(
                        decision=ThrottleDecision.REJECT,
                        reason=f"User queue full: {user_total_queued}/{config.max_queued_per_user}",
                        details=details
                    ))
                else:
                    return ServiceResult.success_result(ThrottleResult(
                        decision=ThrottleDecision.THROTTLE,
                        reason=f"User queue limit: {user_total_queued}/{config.max_queued_per_user}",
                        delay_seconds=config.throttle_delay_seconds,
                        details=details
                    ))
            
            # Check 6: Tenant concurrent limit
            tenant_active = counts.get("tenant_active", 0)
            if tenant_active >= config.max_concurrent_per_tenant:
                return ServiceResult.success_result(ThrottleResult(
                    decision=ThrottleDecision.THROTTLE,
                    reason=f"Tenant concurrent limit: Active={tenant_active}, Max={config.max_concurrent_per_tenant}",
                    delay_seconds=config.throttle_delay_seconds,
                    details=details
                ))
            
            # Check 7: Tenant queued limit
            tenant_queued = counts.get("tenant_queued", 0)
            tenant_throttled = counts.get("tenant_throttled", 0)
            tenant_total_queued = tenant_queued + tenant_throttled
            if tenant_total_queued >= config.max_queued_per_tenant:
                if config.reject_when_throttle_full:
                    return ServiceResult.success_result(ThrottleResult(
                        decision=ThrottleDecision.REJECT,
                        reason=f"Tenant queue full: {tenant_total_queued}/{config.max_queued_per_tenant}",
                        details=details
                    ))
                else:
                    return ServiceResult.success_result(ThrottleResult(
                        decision=ThrottleDecision.THROTTLE,
                        reason=f"Tenant queue limit: Active={tenant_total_queued}, Max={config.max_queued_per_tenant}",
                        delay_seconds=config.throttle_delay_seconds,
                        details=details
                    ))
            
            # Check 8: Profile count limit (if provided and enabled)
            if config.profile_limit_enabled and estimated_profiles:
                if estimated_profiles > config.max_profiles_per_submission:
                    return ServiceResult.success_result(ThrottleResult(
                        decision=ThrottleDecision.REJECT,
                        reason=f"Profile limit exceeded: Active={estimated_profiles}, Max={config.max_profiles_per_submission}",
                        details=details
                    ))
            
            # All checks passed - allow
            return ServiceResult.success_result(ThrottleResult(
                decision=ThrottleDecision.ALLOW,
                reason="All checks passed",
                details=details
            ))
            
        except Exception as e:
            logger.exception(f"Error evaluating throttle: {e}")
            # Fail open - allow on error
            return ServiceResult.success_result(ThrottleResult(
                decision=ThrottleDecision.ALLOW,
                reason=f"Error during evaluation, allowing by default: {str(e)}"
            ))

    def evaluate_profile_count(
        self,
        user_id: str,
        actual_profiles: int,
        metric_type: str = "execution",
    ) -> ServiceResult[ThrottleResult]:
        """
        Secondary evaluation after profile count is known.
        
        Called after profile splitting to check if actual profile count
        exceeds limits. Can trigger re-queue to throttle queue.
        
        Args:
            user_id: User ID
            actual_profiles: Actual profile count from profile split
            metric_type: Type of execution
            
        Returns:
            ServiceResult with ThrottleResult
        """
        try:
            # Get effective config
            config_result = self._config_service.get_effective_config(user_id, metric_type)
            if not config_result.success or not config_result.data:
                return ServiceResult.success_result(ThrottleResult(
                    decision=ThrottleDecision.ALLOW,
                    reason="Config unavailable"
                ))
            
            config = config_result.data
            
            if not config.profile_limit_enabled:
                return ServiceResult.success_result(ThrottleResult(
                    decision=ThrottleDecision.ALLOW,
                    reason="Profile limits disabled"
                ))
            
            # Check profile count
            if actual_profiles > config.max_profiles_per_submission:
                return ServiceResult.success_result(ThrottleResult(
                    decision=ThrottleDecision.REJECT,
                    reason=f"Profile limit exceeded: Active={actual_profiles}, Max={config.max_profiles_per_submission}",
                    details={"actual_profiles": actual_profiles}
                ))
            
            return ServiceResult.success_result(ThrottleResult(
                decision=ThrottleDecision.ALLOW,
                reason="Profile count within limits",
                details={"actual_profiles": actual_profiles}
            ))
            
        except Exception as e:
            logger.exception(f"Error evaluating profile count: {e}")
            return ServiceResult.success_result(ThrottleResult(
                decision=ThrottleDecision.ALLOW,
                reason=f"Error during evaluation: {str(e)}"
            ))

    def _reconcile_metrics(
        self,
        user_id: str,
        metric_type: str,
    ) -> None:
        """
        Reconcile metrics by counting ACTUALLY running workflows.
        
        This method:
        1. Queries all workflows for the user (all statuses)
        2. Filters to only non-terminal statuses (pending, running, queued)
        3. Identifies stale workflows (running > timeout threshold)
        4. Auto-fails stale workflows (only if in non-terminal state)
        5. Updates metrics to match actual running count
        
        This ensures metrics are accurate even if previous updates failed,
        and prevents permanent throttle states from stuck workflows.
        
        Args:
            user_id: User ID to reconcile metrics for
            metric_type: Type of execution
        """
        try:
            # Get timeout threshold from environment (default 2 hours)
            timeout_hours = int(os.getenv("WORKFLOW_TIMEOUT_HOURS", "2"))
            timeout_threshold = timedelta(hours=timeout_hours)
            
            # Import here to avoid circular dependency
            from .workflow_service import WorkflowService
            
            # Create workflow service with same context
            workflow_svc = WorkflowService(
                dynamodb=self._metrics_service.dynamodb,
                table_name=self._metrics_service.table_name,
                request_context=self._request_context,
            )
            
            # Get ALL workflows for this user (not filtered by status)
            # We'll filter in memory to avoid multiple queries
            from ..models import Workflow
            
            query_model = Workflow()
            query_model.tenant_id = self._request_context.authenticated_tenant_id
            query_model.owner_id = user_id
            
            # Query for all user workflows
            result = workflow_svc._query_by_index(
                query_model,
                "gsi1",  # Assuming GSI1 is tenant_id + owner_id
                limit=100
            )
            
            if not result.success:
                logger.warning(f"Failed to query workflows for reconciliation: {result.message}")
                return
            
            all_workflows = result.data or []
            
            # Terminal states that should NOT be counted or failed
            TERMINAL_STATES = {'succeeded', 'failed', 'cancelled'}
            # Non-terminal states that count toward metrics
            NON_TERMINAL_STATES = {'pending', 'running', 'queued'}
            
            # Filter to only non-terminal workflows
            active_workflows = [
                w for w in all_workflows 
                if w.status and w.status.lower() in NON_TERMINAL_STATES
            ]
            
            # Identify stale workflows (any non-terminal workflow > timeout threshold)
            now = datetime.now(UTC)
            actual_running = 0
            stale_workflows = []
            
            for workflow in active_workflows:
                # Determine timestamp to check based on status
                timestamp_to_check = None
                status_lower = workflow.status.lower() if workflow.status else 'unknown'
                
                if status_lower == 'running':
                    # Running workflows: check started_utc (or started_utc_ts)
                    timestamp_to_check = workflow.started_utc_ts or workflow.started_utc
                elif status_lower in ('pending', 'queued'):
                    # Pending/queued workflows: check created_utc (or created_utc_ts)
                    timestamp_to_check = workflow.created_utc_ts or workflow.created_utc
                
                # If no timestamp, treat as stale
                if not timestamp_to_check:
                    stale_workflows.append(workflow)
                    logger.warning(
                        f"Stale workflow detected: {workflow.id}, "
                        f"status={status_lower}, no timestamp"
                    )
                    continue
                
                # Parse timestamp and check age
                try:
                    # Handle both Unix timestamp (float) and ISO string
                    if isinstance(timestamp_to_check, (int, float)):
                        # Unix timestamp
                        workflow_time = datetime.fromtimestamp(timestamp_to_check, tz=UTC)
                    elif isinstance(timestamp_to_check, str):
                        # ISO string
                        workflow_time = datetime.fromisoformat(timestamp_to_check.replace('Z', '+00:00'))
                    else:
                        # Unknown type - treat as stale
                        logger.warning(
                            f"Unknown timestamp type for {workflow.id}: {type(timestamp_to_check)}"
                        )
                        stale_workflows.append(workflow)
                        continue
                    
                    age = now - workflow_time
                    
                    if age > timeout_threshold:
                        # Stale - should have completed
                        stale_workflows.append(workflow)
                        logger.warning(
                            f"Stale workflow detected: {workflow.id}, "
                            f"status={status_lower}, age={age.total_seconds()/3600:.1f}h"
                        )
                    else:
                        # Still active and within timeout
                        actual_running += 1
                except (ValueError, AttributeError, TypeError) as e:
                    logger.warning(f"Error parsing workflow timestamp for {workflow.id}: {e}")
                    # Treat as stale if we can't parse timestamp
                    stale_workflows.append(workflow)
            
            # Auto-fail stale workflows (only if still in non-terminal state)
            for workflow in stale_workflows:
                try:
                    # Double-check status before attempting to fail
                    if workflow.status and workflow.status.lower() in TERMINAL_STATES:
                        logger.debug(f"Skipping workflow {workflow.id} - already in terminal state: {workflow.status}")
                        continue
                    
                    logger.info(f"Auto-failing stale workflow: {workflow.id}")
                    workflow_svc.fail(
                        workflow.id,
                        error_message=f"Workflow timed out after {timeout_hours} hours (auto-cleanup)",
                        error_code=ErrorCode.STALE_WORKFLOW_TIMEOUT
                    )
                except Exception as e:
                    logger.error(f"Failed to auto-fail stale workflow {workflow.id}: {e}")
            
            # Update metrics to match reality
            metrics_result = self._metrics_service.get_user_metrics(user_id, metric_type)
            if metrics_result.success and metrics_result.data:
                metrics = metrics_result.data
                
                if metrics.active_count != actual_running:
                    logger.warning(
                        f"Metrics drift corrected for user {user_id}: "
                        f"{metrics.active_count} → {actual_running} "
                        f"({len(stale_workflows)} stale workflows auto-failed)"
                    )
                    metrics.active_count = actual_running
                    self._metrics_service._save_model(metrics)
                else:
                    logger.debug(f"Metrics accurate for user {user_id}: {actual_running} active")
            
        except Exception as e:
            # Don't fail throttle evaluation if reconciliation fails
            logger.exception(f"Error during metrics reconciliation: {e}")
