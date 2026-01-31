"""
Handler logic for aggregating execution metrics summaries.

This handler processes ExecutionMetrics records and creates/updates
WorkflowMetricsSummary records for various time periods.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import os
from aws_lambda_powertools import Logger
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal

from boto3_assist.dynamodb.dynamodb import DynamoDB

from geek_cafe_saas_sdk.core.system_request_context import SystemRequestContext
from geek_cafe_saas_sdk.modules.workflows.models.workflow_metrics import (
    WorkflowMetrics,
)
from geek_cafe_saas_sdk.modules.workflows.models.workflow_metrics_summary import (
    WorkflowMetricsSummary,
    PeriodType,
)

logger = Logger(__name__)


class AggregateSummariesHandler:
    """
    Handler for aggregating execution metrics into period summaries.
    
    Aggregation Strategy:
    - Daily: Runs every day, captures previous day's metrics
    - Weekly: Runs on Mondays, aggregates previous week (Mon-Sun)
    - Monthly: Runs on 1st of month, aggregates previous month
    - Yearly: Runs on Jan 1st, aggregates previous year
    
    The handler is idempotent - running multiple times for the same period
    will update (not duplicate) the summary records.
    """
        
    def __init__(
        self,
        injected_services: Optional[Dict[str, Any]] = None,
    ):
        """Initialize handler with optional injected services."""
        self._injected_services = injected_services or {}
        self._dynamodb: Optional[DynamoDB] = None
        self._table_name = os.getenv("DYNAMODB_TABLE_NAME")
    
    @property
    def dynamodb(self) -> DynamoDB:
        """Lazy-loaded DynamoDB instance."""
        if self._dynamodb is None:
            self._dynamodb = self._injected_services.get("dynamodb") or DynamoDB()
        return self._dynamodb
    
    def handle(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Handle the aggregation job.
        
        Args:
            event: EventBridge event (contains time, detail-type, etc.)
            context: Lambda context
            
        Returns:
            Summary of aggregation results
        """
        try:
            now = datetime.now(timezone.utc)
            
            # Determine which periods to aggregate based on current time
            periods_to_aggregate = self._determine_periods_to_aggregate(now)
            
            logger.info(f"Aggregating periods: {periods_to_aggregate}")
            
            # Get all unique tenant/user combinations from metrics
            metrics_records = self._scan_all_metrics()
            
            if not metrics_records:
                logger.info("No metrics records found to aggregate")
                return self._success_response({
                    "message": "No metrics to aggregate",
                    "periods": [],
                    "summaries_created": 0,
                })
            
            # Group by tenant/owner
            grouped_metrics = self._group_metrics(metrics_records)
            
            summaries_created = 0
            summaries_updated = 0
            errors: List[str] = []
            
            # Process each tenant/owner combination
            for (tenant_id, owner_id, metric_type), metrics in grouped_metrics.items():
                for period_type in periods_to_aggregate:
                    try:
                        result = self._aggregate_period(
                            tenant_id=tenant_id,
                            owner_id=owner_id,
                            metric_type=metric_type,
                            period_type=period_type,
                            metrics=metrics,
                            reference_time=now,
                        )
                        if result.get("created"):
                            summaries_created += 1
                        else:
                            summaries_updated += 1
                    except Exception as e:
                        error_msg = f"Error aggregating {period_type} for {tenant_id}/{owner_id}: {e}"
                        logger.exception(error_msg)
                        errors.append(error_msg)
            
            return self._success_response({
                "message": "Aggregation complete",
                "periods": periods_to_aggregate,
                "metrics_processed": len(metrics_records),
                "summaries_created": summaries_created,
                "summaries_updated": summaries_updated,
                "errors": errors if errors else None,
            })
            
        except Exception as e:
            logger.exception(f"Aggregation job failed: {e}")
            return self._error_response(str(e))
    
    def _determine_periods_to_aggregate(self, now: datetime) -> List[PeriodType]:
        """
        Determine which periods need aggregation based on current time.
        
        Always aggregates daily. Additionally:
        - Weekly on Mondays (for previous week)
        - Monthly on 1st of month (for previous month)
        - Yearly on Jan 1st (for previous year)
        """
        periods = [PeriodType.DAILY]
        
        # Monday = 0 in Python's weekday()
        if now.weekday() == 0:
            periods.append(PeriodType.WEEKLY)
        
        if now.day == 1:
            periods.append(PeriodType.MONTHLY)
            
            if now.month == 1:
                periods.append(PeriodType.YEARLY)
        
        return periods
    
    def _scan_all_metrics(self) -> List[WorkflowMetrics]:
        """
        Scan all WorkflowMetrics records from DynamoDB.
        
        Note: For large datasets, consider using GSI queries by tenant
        or implementing pagination with continuation tokens.
        """
        try:
            table = self.dynamodb.resource.Table(self._table_name)
            
            # Scan for all execution_metrics records
            # Using filter on pk prefix for single-table design
            response = table.scan(
                FilterExpression="begins_with(pk, :prefix)",
                ExpressionAttributeValues={
                    ":prefix": "execution_metrics#",
                },
            )
            
            items = response.get("Items", [])
            
            # Handle pagination
            while "LastEvaluatedKey" in response:
                response = table.scan(
                    FilterExpression="begins_with(pk, :prefix)",
                    ExpressionAttributeValues={
                        ":prefix": "execution_metrics#",
                    },
                    ExclusiveStartKey=response["LastEvaluatedKey"],
                )
                items.extend(response.get("Items", []))
            
            # Convert to model objects
            metrics_list = []
            for item in items:
                metrics = WorkflowMetrics()
                metrics.map(item)
                metrics_list.append(metrics)
            
            return metrics_list
            
        except Exception as e:
            logger.exception(f"Error scanning metrics: {e}")
            return []
    
    def _group_metrics(
        self,
        metrics_records: List[WorkflowMetrics],
    ) -> Dict[Tuple[str, str, str], List[WorkflowMetrics]]:
        """Group metrics by (tenant_id, owner_id, metric_type)."""
        grouped: Dict[Tuple[str, str, str], List[WorkflowMetrics]] = {}
        
        for metrics in metrics_records:
            key = (metrics.tenant_id, metrics.owner_id, metrics.metric_type)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(metrics)
        
        return grouped
    
    def _aggregate_period(
        self,
        tenant_id: str,
        owner_id: str,
        metric_type: str,
        period_type: PeriodType,
        metrics: List[WorkflowMetrics],
        reference_time: datetime,
    ) -> Dict[str, Any]:
        """
        Aggregate metrics for a specific period.
        
        Args:
            tenant_id: Tenant ID
            owner_id: Owner ID (user or __tenant__)
            metric_type: Type of metric (e.g., nca_analysis)
            period_type: Period to aggregate (daily, weekly, etc.)
            metrics: List of metrics records for this tenant/owner
            reference_time: Current time for calculating period boundaries
            
        Returns:
            Dict with 'created' (bool) indicating if new or updated
        """
        # Calculate period boundaries
        period_start, period_end = self._calculate_period_boundaries(
            period_type, reference_time
        )
        
        # Create system context for database operations
        request_context = SystemRequestContext(
            tenant_id=tenant_id,
            user_id="system-aggregator",
            source="metrics-aggregation-job",
        )
        
        # Aggregate the metrics
        aggregated = self._calculate_aggregates(metrics, period_start, period_end)
        
        # Check if summary already exists
        existing_summary = self._find_existing_summary(
            tenant_id=tenant_id,
            owner_id=owner_id,
            metric_type=metric_type,
            period_type=period_type,
            period_start=period_start,
        )
        
        if existing_summary:
            # Update existing
            self._update_summary(existing_summary, aggregated)
            return {"created": False, "id": existing_summary.id}
        else:
            # Create new
            summary = self._create_summary(
                tenant_id=tenant_id,
                owner_id=owner_id,
                metric_type=metric_type,
                period_type=period_type,
                period_start=period_start,
                period_end=period_end,
                aggregated=aggregated,
            )
            return {"created": True, "id": summary.id}
    
    def _calculate_period_boundaries(
        self,
        period_type: PeriodType,
        reference_time: datetime,
    ) -> Tuple[datetime, datetime]:
        """
        Calculate start and end timestamps for the period to aggregate.
        
        We aggregate the PREVIOUS period (e.g., yesterday, last week).
        """
        # Start of today (midnight UTC)
        today_start = reference_time.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        
        if period_type == PeriodType.DAILY:
            # Previous day
            period_end = today_start
            period_start = period_end - timedelta(days=1)
            
        elif period_type == PeriodType.WEEKLY:
            # Previous week (Mon-Sun)
            # Find start of current week (Monday)
            days_since_monday = reference_time.weekday()
            current_week_start = today_start - timedelta(days=days_since_monday)
            period_end = current_week_start
            period_start = period_end - timedelta(days=7)
            
        elif period_type == PeriodType.MONTHLY:
            # Previous month
            first_of_month = today_start.replace(day=1)
            period_end = first_of_month
            # Go back to first of previous month
            if first_of_month.month == 1:
                period_start = first_of_month.replace(year=first_of_month.year - 1, month=12)
            else:
                period_start = first_of_month.replace(month=first_of_month.month - 1)
                
        elif period_type == PeriodType.YEARLY:
            # Previous year
            first_of_year = today_start.replace(month=1, day=1)
            period_end = first_of_year
            period_start = first_of_year.replace(year=first_of_year.year - 1)
            
        else:
            raise ValueError(f"Unknown period type: {period_type}")
        
        return period_start, period_end
    
    def _calculate_aggregates(
        self,
        metrics: List[WorkflowMetrics],
        period_start: datetime,
        period_end: datetime,
    ) -> Dict[str, Any]:
        """
        Calculate aggregate values from metrics.
        
        Note: Current implementation uses snapshot values from metrics.
        For accurate period-based aggregation, you'd need to track
        individual execution events with timestamps.
        """
        # Sum up totals from all metrics records
        total_submitted = sum(m.total_submitted for m in metrics)
        total_completed = sum(m.total_completed for m in metrics)
        total_failed = sum(m.total_failed for m in metrics)
        total_profiles = sum(m.total_profiles for m in metrics)
        
        # For now, we use the totals as the period values
        # In a production system, you'd track deltas or use execution history
        return {
            "submission_count": total_submitted,
            "success_count": total_completed,
            "failure_count": total_failed,
            "cancelled_count": 0,  # Would need execution history
            "timeout_count": 0,  # Would need execution history
            "total_profiles": total_profiles,
            # Duration stats would require execution history with timestamps
            "avg_duration_ms": None,
            "max_duration_ms": None,
            "min_duration_ms": None,
            "total_duration_ms": None,
        }
    
    def _find_existing_summary(
        self,
        tenant_id: str,
        owner_id: str,
        metric_type: str,
        period_type: PeriodType,
        period_start: datetime,
    ) -> Optional[WorkflowMetricsSummary]:
        """Find existing summary for the given period."""
        try:
            table = self.dynamodb.resource.Table(self._table_name)
            
            # Build the expected pk/sk for this summary
            period_start_ts = period_start.timestamp()
            pk = f"execution_metrics_summary#{tenant_id}#{owner_id}"
            sk = f"execution_metrics_summary#{metric_type}#{period_type}#{int(period_start_ts)}"
            
            response = table.get_item(Key={"pk": pk, "sk": sk})
            
            if "Item" in response:
                summary = WorkflowMetricsSummary()
                summary.map(response["Item"])
                return summary
            
            return None
            
        except Exception as e:
            logger.warning(f"Error finding existing summary: {e}")
            return None
    
    def _create_summary(
        self,
        tenant_id: str,
        owner_id: str,
        metric_type: str,
        period_type: PeriodType,
        period_start: datetime,
        period_end: datetime,
        aggregated: Dict[str, Any],
    ) -> WorkflowMetricsSummary:
        """Create a new summary record."""
        summary = WorkflowMetricsSummary()
        summary.tenant_id = tenant_id
        summary.owner_id = owner_id
        summary.metric_type = metric_type
        summary.period_type = period_type
        summary.period_start_ts = period_start.timestamp()
        summary.period_end_ts = period_end.timestamp()
        
        # Set aggregated values
        summary.submission_count = aggregated.get("submission_count", 0)
        summary.success_count = aggregated.get("success_count", 0)
        summary.failure_count = aggregated.get("failure_count", 0)
        summary.cancelled_count = aggregated.get("cancelled_count", 0)
        summary.timeout_count = aggregated.get("timeout_count", 0)
        summary.total_profiles = aggregated.get("total_profiles", 0)
        
        if aggregated.get("avg_duration_ms") is not None:
            summary.avg_duration_ms = aggregated["avg_duration_ms"]
        if aggregated.get("max_duration_ms") is not None:
            summary.max_duration_ms = aggregated["max_duration_ms"]
        if aggregated.get("min_duration_ms") is not None:
            summary.min_duration_ms = aggregated["min_duration_ms"]
        
        # Save to DynamoDB
        summary.prep_for_save()
        table = self.dynamodb.resource.Table(self._table_name)
        table.put_item(Item=summary.to_dict())
        
        logger.info(f"Created summary: {summary.id} for {period_type} {period_start}")
        return summary
    
    def _update_summary(
        self,
        summary: WorkflowMetricsSummary,
        aggregated: Dict[str, Any],
    ) -> None:
        """Update an existing summary record."""
        summary.submission_count = aggregated.get("submission_count", 0)
        summary.success_count = aggregated.get("success_count", 0)
        summary.failure_count = aggregated.get("failure_count", 0)
        summary.cancelled_count = aggregated.get("cancelled_count", 0)
        summary.timeout_count = aggregated.get("timeout_count", 0)
        summary.total_profiles = aggregated.get("total_profiles", 0)
        
        if aggregated.get("avg_duration_ms") is not None:
            summary.avg_duration_ms = aggregated["avg_duration_ms"]
        if aggregated.get("max_duration_ms") is not None:
            summary.max_duration_ms = aggregated["max_duration_ms"]
        if aggregated.get("min_duration_ms") is not None:
            summary.min_duration_ms = aggregated["min_duration_ms"]
        
        # Save to DynamoDB
        summary.prep_for_save()
        table = self.dynamodb.resource.Table(self._table_name)
        table.put_item(Item=summary.to_dict())
        
        logger.info(f"Updated summary: {summary.id}")
    
    def _success_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build success response."""
        return {
            "statusCode": 200,
            "body": data,
        }
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """Build error response."""
        return {
            "statusCode": 500,
            "body": {"error": message},
        }
