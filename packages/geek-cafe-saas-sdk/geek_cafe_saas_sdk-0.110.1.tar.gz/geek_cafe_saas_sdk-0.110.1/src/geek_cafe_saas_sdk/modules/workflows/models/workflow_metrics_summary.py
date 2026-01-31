"""
Execution metrics summary model for aggregated execution statistics.

Stores periodic summaries (weekly, monthly, yearly) of execution metrics
for reporting and analytics.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from geek_cafe_saas_sdk.core.models.base_tenant_model import BaseTenantModel


class PeriodType:
    """Period type constants for summary aggregation."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    
    ALL = [DAILY, WEEKLY, MONTHLY, YEARLY]


class WorkflowMetricsSummary(BaseTenantModel):
    """
    Aggregated workflow metrics summary for reporting.
    
    Stores periodic summaries of execution counts, success/failure rates,
    and resource usage. Aggregated by scheduled jobs (e.g., EventBridge).
    
    Granularity:
    - Tenant-wide summaries: owner_id = "__tenant__"
    - User-specific summaries: owner_id = actual user ID
    
    Access Patterns (DynamoDB Keys):
    - pk: execution_metrics_summary#{id}
    - sk: metadata
    - gsi1: By tenant + period_type + period_start_ts
    - gsi2: By tenant + owner + period_type + period_start_ts
    - gsi3: By tenant + metric_type + period_type + period_start_ts
    """

    # Sentinel value for tenant-wide summaries
    TENANT_WIDE_OWNER = "__tenant__"

    def __init__(self):
        super().__init__()
        
        # Identity
        self._owner_id: str | None = None  # User ID or "__tenant__"
        self._metric_type: str = "execution"  # e.g., "acme-workflow", "validation"
        
        # Period definition
        self._period_type: str = PeriodType.WEEKLY  # daily, weekly, monthly, yearly
        self._period_start_ts: float | None = None  # Start of aggregation period
        self._period_end_ts: float | None = None    # End of aggregation period
        
        # Execution counts
        self._submission_count: int = 0   # Total submissions in period
        self._success_count: int = 0      # Successful completions
        self._failure_count: int = 0      # Failed executions
        self._cancelled_count: int = 0    # Cancelled executions
        self._timeout_count: int = 0      # Timed out executions
        
        # Resource usage
        self._total_profiles: int = 0     # Total profiles processed
        self._total_duration_ms: int = 0  # Total execution time
        self._avg_duration_ms: float = 0  # Average execution time
        self._max_duration_ms: int = 0    # Longest execution
        self._min_duration_ms: int = 0    # Shortest execution
        
        # Throttling stats
        self._throttled_count: int = 0    # Times throttled
        self._rejected_count: int = 0     # Times rejected (hard limit)
        
        # Flexible metrics storage
        self._metrics: Dict[str, Any] = {}
        
        # Model metadata
        self.model_name = "execution_metrics_summary"
        self.model_name_plural = "execution_metrics_summaries"
        
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()

    def _setup_indexes(self):
        """Setup DynamoDB indexes for summary queries."""
        
        # Primary index: Summary by ID
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("execution_metrics_summary", self.id)
        )
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: "metrics"
        self.indexes.add_primary(primary)
        
        # GSI1: By tenant + period_type + period_start_ts
        self._setup_gsi1()
        
        # GSI2: By tenant + owner + period_type + period_start_ts
        self._setup_gsi2()
        
        # GSI3: By tenant + metric_type + period_type + period_start_ts
        self._setup_gsi3()

    def _setup_gsi1(self):
        """GSI1: Summaries by tenant + period_type sorted by period start."""
        gsi = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = "gsi1_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id)
        )
        gsi.sort_key.attribute_name = "gsi1_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("model", "execution_metrics_summary"),
            ("period_type", self._period_type),
            ("period_start", self._period_start_ts or 0)
        )
        self.indexes.add_secondary(gsi)

    def _setup_gsi2(self):
        """GSI2: Summaries by tenant + owner + period_type sorted by period start."""
        gsi = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = "gsi2_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("owner", self._owner_id)
        )
        gsi.sort_key.attribute_name = "gsi2_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("model", "execution_metrics_summary"),
            ("period_type", self._period_type),
            ("period_start", self._period_start_ts or 0)
        )
        self.indexes.add_secondary(gsi)

    def _setup_gsi3(self):
        """GSI3: Summaries by tenant + metric_type + period_type sorted by period start."""
        gsi = DynamoDBIndex()
        gsi.name = "gsi3"
        gsi.partition_key.attribute_name = "gsi3_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("metric_type", self._metric_type)
        )
        gsi.sort_key.attribute_name = "gsi3_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("model", "execution_metrics_summary"),
            ("period_type", self._period_type),
            ("period_start", self._period_start_ts or 0)
        )
        self.indexes.add_secondary(gsi)

    # Properties - Identity
    @property
    def owner_id(self) -> str | None:
        """Owner user ID, or '__tenant__' for tenant-wide summaries."""
        return self._owner_id

    @owner_id.setter
    def owner_id(self, value: str | None):
        self._owner_id = value

    @property
    def metric_type(self) -> str:
        """Type of execution being summarized."""
        return self._metric_type

    @metric_type.setter
    def metric_type(self, value: str):
        self._metric_type = value

    # Properties - Period
    @property
    def period_type(self) -> str:
        """Period type (daily, weekly, monthly, yearly)."""
        return self._period_type

    @period_type.setter
    def period_type(self, value: str):
        self._period_type = value

    @property
    def period_start_ts(self) -> float | None:
        """Start timestamp of the aggregation period."""
        return self._period_start_ts

    @period_start_ts.setter
    def period_start_ts(self, value: float | None):
        self._period_start_ts = self._safe_number_conversion(value)

    @property
    def period_end_ts(self) -> float | None:
        """End timestamp of the aggregation period."""
        return self._period_end_ts

    @period_end_ts.setter
    def period_end_ts(self, value: float | None):
        self._period_end_ts = self._safe_number_conversion(value)

    # Properties - Execution counts
    @property
    def submission_count(self) -> int:
        """Total submissions in this period."""
        return self._submission_count

    @submission_count.setter
    def submission_count(self, value: int):
        self._submission_count = int(value) if value else 0

    @property
    def success_count(self) -> int:
        """Number of successful completions."""
        return self._success_count

    @success_count.setter
    def success_count(self, value: int):
        self._success_count = int(value) if value else 0

    @property
    def failure_count(self) -> int:
        """Number of failed executions."""
        return self._failure_count

    @failure_count.setter
    def failure_count(self, value: int):
        self._failure_count = int(value) if value else 0

    @property
    def cancelled_count(self) -> int:
        """Number of cancelled executions."""
        return self._cancelled_count

    @cancelled_count.setter
    def cancelled_count(self, value: int):
        self._cancelled_count = int(value) if value else 0

    @property
    def timeout_count(self) -> int:
        """Number of timed out executions."""
        return self._timeout_count

    @timeout_count.setter
    def timeout_count(self, value: int):
        self._timeout_count = int(value) if value else 0

    # Properties - Resource usage
    @property
    def total_profiles(self) -> int:
        """Total profiles processed in this period."""
        return self._total_profiles

    @total_profiles.setter
    def total_profiles(self, value: int):
        self._total_profiles = int(value) if value else 0

    @property
    def total_duration_ms(self) -> int:
        """Total execution duration in milliseconds."""
        return self._total_duration_ms

    @total_duration_ms.setter
    def total_duration_ms(self, value: int):
        self._total_duration_ms = int(value) if value else 0

    @property
    def avg_duration_ms(self) -> float:
        """Average execution duration in milliseconds."""
        return self._avg_duration_ms

    @avg_duration_ms.setter
    def avg_duration_ms(self, value: float):
        self._avg_duration_ms = float(value) if value else 0.0

    @property
    def max_duration_ms(self) -> int:
        """Maximum execution duration in milliseconds."""
        return self._max_duration_ms

    @max_duration_ms.setter
    def max_duration_ms(self, value: int):
        self._max_duration_ms = int(value) if value else 0

    @property
    def min_duration_ms(self) -> int:
        """Minimum execution duration in milliseconds."""
        return self._min_duration_ms

    @min_duration_ms.setter
    def min_duration_ms(self, value: int):
        self._min_duration_ms = int(value) if value else 0

    # Properties - Throttling stats
    @property
    def throttled_count(self) -> int:
        """Number of times executions were throttled."""
        return self._throttled_count

    @throttled_count.setter
    def throttled_count(self, value: int):
        self._throttled_count = int(value) if value else 0

    @property
    def rejected_count(self) -> int:
        """Number of times executions were rejected (hard limit)."""
        return self._rejected_count

    @rejected_count.setter
    def rejected_count(self, value: int):
        self._rejected_count = int(value) if value else 0

    # Properties - Flexible metrics
    @property
    def metrics(self) -> Dict[str, Any]:
        """Additional flexible metrics storage."""
        return self._metrics

    @metrics.setter
    def metrics(self, value: Dict[str, Any]):
        self._metrics = value if value is not None else {}

    # Computed properties
    @property
    def is_tenant_wide(self) -> bool:
        """Check if this is a tenant-wide summary."""
        return self._owner_id == self.TENANT_WIDE_OWNER

    @property
    def success_rate(self) -> float:
        """Calculate success rate as a percentage."""
        total = self._success_count + self._failure_count + self._cancelled_count + self._timeout_count
        if total == 0:
            return 0.0
        return (self._success_count / total) * 100

    @property
    def completion_count(self) -> int:
        """Total completed executions (success + failure + cancelled + timeout)."""
        return self._success_count + self._failure_count + self._cancelled_count + self._timeout_count

    # Helper methods
    def get_metric(self, key: str, default: Any = None) -> Any:
        """Get a specific metric value."""
        return self._metrics.get(key, default)

    def set_metric(self, key: str, value: Any) -> None:
        """Set a specific metric value."""
        self._metrics[key] = value
