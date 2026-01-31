"""
Execution metrics model for tracking real-time execution counts.

Tracks active, queued, and completed execution counts per user and tenant
for throttling decisions and usage monitoring.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Optional
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from boto3_assist.dynamodb.dynamodb_model_base import exclude_from_serialization
from geek_cafe_saas_sdk.core.models.base_tenant_model import BaseTenantModel


class WorkflowMetrics(BaseTenantModel):
    """
    Real-time workflow metrics for throttling and monitoring.
    
    Tracks counts of active, queued, and completed executions at both
    user and tenant levels. Uses atomic counters for thread-safe updates.
    
    Granularity:
    - Tenant-wide metrics: owner_id = "__tenant__" (sentinel value)
    - User-specific metrics: owner_id = actual user ID
    
    Access Patterns (DynamoDB Keys):
    - pk: execution_metrics#{id}
    - sk: metadata
    - gsi1: Metrics by tenant + metric_type (tenant-wide queries)
    - gsi2: Metrics by tenant + owner + metric_type (user-specific queries)
    """

    # Sentinel value for tenant-wide metrics (no specific user)
    TENANT_WIDE_OWNER = "__tenant__"

    def __init__(self):
        super().__init__()
        
        # Identity
        self._owner_id: str | None = None  # User ID or "__tenant__" for tenant-wide
        self._metric_type: str = "execution"  # e.g., "acme-workflow", "validation"
        
        # Real-time counters (updated atomically)
        self._active_count: int = 0      # Currently running executions
        self._queued_count: int = 0      # In queue waiting to start
        self._throttled_count: int = 0   # In throttle/delay queue
        
        # Cumulative counters (for rate limiting windows)
        self._total_submitted: int = 0   # All-time submitted
        self._total_completed: int = 0   # All-time completed successfully
        self._total_failed: int = 0      # All-time failed
        self._total_profiles: int = 0    # Cumulative profiles processed
        
        # Rate limiting
        self._last_submission_ts: float | None = None  # Last submission timestamp
        self._submissions_this_hour: int = 0  # Rolling hour counter
        self._submissions_this_day: int = 0   # Rolling day counter
        self._hour_window_start_ts: float | None = None  # Start of current hour window
        self._day_window_start_ts: float | None = None   # Start of current day window
        
        # Model metadata
        self.model_name = "execution_metrics"
        self.model_name_plural = "execution_metrics"
        
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()

    def _setup_indexes(self):
        """Setup DynamoDB indexes for execution metrics queries."""
        
        # Primary index: Metrics by ID
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("execution_metrics", self.id)
        )
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: "metrics"
        self.indexes.add_primary(primary)
        
        # GSI1: Metrics by tenant + metric_type (for tenant-wide queries)
        self._setup_gsi1()
        
        # GSI2: Metrics by tenant + owner + metric_type (for user-specific queries)
        self._setup_gsi2()

    def _setup_gsi1(self):
        """GSI1: Metrics by tenant + metric_type."""
        gsi = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = "gsi1_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id)
        )
        gsi.sort_key.attribute_name = "gsi1_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("model", "execution_metrics"),
            ("metric_type", self._metric_type)
        )
        self.indexes.add_secondary(gsi)

    def _setup_gsi2(self):
        """GSI2: Metrics by tenant + owner + metric_type."""
        gsi = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = "gsi2_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("owner", self._owner_id)
        )
        gsi.sort_key.attribute_name = "gsi2_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("model", "execution_metrics"),
            ("metric_type", self._metric_type)
        )
        self.indexes.add_secondary(gsi)

    # Properties - Identity
    @property
    def owner_id(self) -> str | None:
        """Owner user ID, or '__tenant__' for tenant-wide metrics."""
        return self._owner_id

    @owner_id.setter
    def owner_id(self, value: str | None):
        self._owner_id = value

    @property
    def metric_type(self) -> str:
        """Type of execution being tracked (e.g., 'nca_analysis', 'validation')."""
        return self._metric_type

    @metric_type.setter
    def metric_type(self, value: str):
        self._metric_type = value

    # Properties - Real-time counters
    @property
    def active_count(self) -> int:
        """Number of currently running executions."""
        return self._active_count

    @active_count.setter
    def active_count(self, value: int):
        self._active_count = max(0, int(value) if value else 0)

    @property
    def queued_count(self) -> int:
        """Number of executions in queue waiting to start."""
        return self._queued_count

    @queued_count.setter
    def queued_count(self, value: int):
        self._queued_count = max(0, int(value) if value else 0)

    @property
    def throttled_count(self) -> int:
        """Number of executions in throttle/delay queue."""
        return self._throttled_count

    @throttled_count.setter
    def throttled_count(self, value: int):
        self._throttled_count = max(0, int(value) if value else 0)

    # Properties - Cumulative counters
    @property
    def total_submitted(self) -> int:
        """Total number of executions ever submitted."""
        return self._total_submitted

    @total_submitted.setter
    def total_submitted(self, value: int):
        self._total_submitted = int(value) if value else 0

    @property
    def total_completed(self) -> int:
        """Total number of executions completed successfully."""
        return self._total_completed

    @total_completed.setter
    def total_completed(self, value: int):
        self._total_completed = int(value) if value else 0

    @property
    def total_failed(self) -> int:
        """Total number of executions that failed."""
        return self._total_failed

    @total_failed.setter
    def total_failed(self, value: int):
        self._total_failed = int(value) if value else 0

    @property
    def total_profiles(self) -> int:
        """Total number of profiles processed across all executions."""
        return self._total_profiles

    @total_profiles.setter
    def total_profiles(self, value: int):
        self._total_profiles = int(value) if value else 0

    # Properties - Rate limiting
    @property
    def last_submission_ts(self) -> float | None:
        """Timestamp of the last submission."""
        return self._last_submission_ts

    @last_submission_ts.setter
    def last_submission_ts(self, value: float | None):
        self._last_submission_ts = self._safe_number_conversion(value)

    @property
    def submissions_this_hour(self) -> int:
        """Number of submissions in the current hour window."""
        return self._submissions_this_hour

    @submissions_this_hour.setter
    def submissions_this_hour(self, value: int):
        self._submissions_this_hour = int(value) if value else 0

    @property
    def submissions_this_day(self) -> int:
        """Number of submissions in the current day window."""
        return self._submissions_this_day

    @submissions_this_day.setter
    def submissions_this_day(self, value: int):
        self._submissions_this_day = int(value) if value else 0

    @property
    def hour_window_start_ts(self) -> float | None:
        """Start timestamp of the current hour window."""
        return self._hour_window_start_ts

    @hour_window_start_ts.setter
    def hour_window_start_ts(self, value: float | None):
        self._hour_window_start_ts = self._safe_number_conversion(value)

    @property
    def day_window_start_ts(self) -> float | None:
        """Start timestamp of the current day window."""
        return self._day_window_start_ts

    @day_window_start_ts.setter
    def day_window_start_ts(self, value: float | None):
        self._day_window_start_ts = self._safe_number_conversion(value)

    # Computed properties
    @property
    @exclude_from_serialization
    def is_tenant_wide(self) -> bool:
        """Check if this is a tenant-wide metric (not user-specific)."""
        return self._owner_id == self.TENANT_WIDE_OWNER

    @property
    @exclude_from_serialization
    def total_in_flight(self) -> int:
        """Total executions currently in flight (active + queued + throttled)."""
        return self._active_count + self._queued_count + self._throttled_count
