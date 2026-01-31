"""
WorkflowHistory model for tracking execution state transitions over time.

Provides an append-only audit log of all state changes for an execution,
enabling debugging, compliance, and historical analysis.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import time
import uuid
from typing import Dict, Any, Optional
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


class WorkflowHistoryEventType:
    """Event type constants for execution history entries."""
    # Lifecycle events
    CREATED = "created"
    STARTED = "started"
    PROGRESS = "progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    RETRIED = "retried"
    
    # Step events
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    
    # Custom events
    CUSTOM = "custom"
    
    ALL = [
        CREATED, STARTED, PROGRESS, SUCCEEDED, FAILED, CANCELLED, TIMED_OUT, RETRIED,
        STEP_STARTED, STEP_COMPLETED, STEP_FAILED, CUSTOM
    ]


class WorkflowHistory(BaseTenantUserModel):
    """
    WorkflowHistory model for tracking execution state transitions.
    
    Each record represents a single event/state change in an execution's lifecycle.
    Records are append-only and immutable once created.
    
    Ordering:
    - Uses nanosecond timestamp + UUID suffix for guaranteed unique ordering
    - No sequence numbers to avoid read-before-write in distributed systems
    
    Access Patterns (DynamoDB Keys):
    - pk: EXECUTION#{execution_id}
    - sk: HISTORY#{timestamp_ns}#{uuid_suffix}
    - gsi1: History by owner + execution (for listing all history)
    - gsi2: History by owner + event_type (for filtering by event type)
    """

    def __init__(self):
        super().__init__()
        
        # Identity
        self._history_id: str | None = None
        self._execution_id: str | None = None
        
        # Ordering (nanosecond timestamp + uuid suffix for uniqueness)
        self._timestamp_ns: int | None = None
        self._uuid_suffix: str | None = None
        
        # Event classification
        self._event_type: str = WorkflowHistoryEventType.CUSTOM
        
        # State transition
        self._from_status: str | None = None
        self._to_status: str | None = None
        
        # Step tracking
        self._step_name: str | None = None
        self._step_index: int | None = None
        self._progress_percent: int | None = None
        
        # Human-readable message
        self._message: str | None = None
        
        # Duration in this state (milliseconds)
        self._duration_ms: int | None = None
        
        # Error details (for failed events)
        self._error_code: str | None = None
        self._error_message: str | None = None
        self._error_details: Dict[str, Any] | None = None
        
        # Flexible metadata for event-specific data
        self._metadata: Dict[str, Any] | None = None
        
        # Actor who triggered this event (user_id, system, lambda, etc.)
        self._actor: str | None = None
        self._actor_type: str | None = None  # "user", "system", "lambda", "step_function"
        
        # Model metadata
        self.model_name = "execution_history"
        self.model_name_plural = "execution_histories"
        
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for execution history queries."""
        
        # Primary index: History by execution_id + timestamp
        # Allows efficient range queries for all history of an execution
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("execution", self._execution_id)
        )
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(
            ("history", self._get_sort_key_value())
        )
        self.indexes.add_primary(primary)
        
        # GSI1: History by owner + execution (for listing with tenant isolation)
        self._setup_gsi1()
        
        # GSI2: History by owner + event_type (for filtering)
        self._setup_gsi2()
    
    def _setup_gsi1(self):
        """GSI1: History by owner + execution_id."""
        gsi = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = "gsi1_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("owner", self.owner_id)
        )
        gsi.sort_key.attribute_name = "gsi1_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("execution", self._execution_id),
            ("ts", self._timestamp_ns or 0)
        )
        self.indexes.add_secondary(gsi)
    
    def _setup_gsi2(self):
        """GSI2: History by owner + event_type."""
        gsi = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = "gsi2_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("owner", self.owner_id)
        )
        gsi.sort_key.attribute_name = "gsi2_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("event_type", self._event_type),
            ("ts", self._timestamp_ns or 0)
        )
        self.indexes.add_secondary(gsi)
    
    def _get_sort_key_value(self) -> str:
        """Generate sort key value from timestamp and uuid suffix.
        
        For queries (when timestamp_ns is None), returns empty string
        to enable begins_with queries on just the 'history#' prefix.
        """
        if self._timestamp_ns is None:
            return ""  # For query - will match all history# entries
        ts = self._timestamp_ns
        suffix = self._uuid_suffix
        return f"{ts:020d}#{suffix}"
    
    def generate_ordering_keys(self) -> None:
        """
        Generate timestamp and uuid suffix for ordering.
        
        Call this before saving a new history entry.
        Uses nanosecond precision + UUID suffix for guaranteed uniqueness.
        """
        self._timestamp_ns = time.time_ns()
        self._uuid_suffix = str(uuid.uuid4())[:8]  # Short suffix for uniqueness
        self._history_id = f"{self._timestamp_ns}#{self._uuid_suffix}"
    
    # Properties - Identity
    @property
    def history_id(self) -> str | None:
        """Unique history entry ID (timestamp#uuid_suffix)."""
        return self._history_id
    
    @history_id.setter
    def history_id(self, value: str | None):
        self._history_id = value
    
    @property
    def execution_id(self) -> str | None:
        """ID of the execution this history belongs to."""
        return self._execution_id
    
    @execution_id.setter
    def execution_id(self, value: str | None):
        self._execution_id = value
    
    # Properties - Ordering
    @property
    def timestamp_ns(self) -> int | None:
        """Nanosecond timestamp for ordering."""
        return self._timestamp_ns
    
    @timestamp_ns.setter
    def timestamp_ns(self, value: int | None):
        self._timestamp_ns = value
    
    @property
    def uuid_suffix(self) -> str | None:
        """UUID suffix for uniqueness."""
        return self._uuid_suffix
    
    @uuid_suffix.setter
    def uuid_suffix(self, value: str | None):
        self._uuid_suffix = value
    
    # Properties - Event classification
    @property
    def event_type(self) -> str:
        """Type of event (created, started, progress, succeeded, failed, etc.)."""
        return self._event_type
    
    @event_type.setter
    def event_type(self, value: str):
        self._event_type = value
    
    # Properties - State transition
    @property
    def from_status(self) -> str | None:
        """Previous status before this event."""
        return self._from_status
    
    @from_status.setter
    def from_status(self, value: str | None):
        self._from_status = value
    
    @property
    def to_status(self) -> str | None:
        """New status after this event."""
        return self._to_status
    
    @to_status.setter
    def to_status(self, value: str | None):
        self._to_status = value
    
    # Properties - Step tracking
    @property
    def step_name(self) -> str | None:
        """Name of the step (for step events)."""
        return self._step_name
    
    @step_name.setter
    def step_name(self, value: str | None):
        self._step_name = value
    
    @property
    def step_index(self) -> int | None:
        """Index of the step (0-based)."""
        return self._step_index
    
    @step_index.setter
    def step_index(self, value: int | None):
        self._step_index = value
    
    @property
    def progress_percent(self) -> int | None:
        """Progress percentage at time of event (0-100)."""
        return self._progress_percent
    
    @progress_percent.setter
    def progress_percent(self, value: int | None):
        if value is not None:
            value = max(0, min(100, value))
        self._progress_percent = value
    
    # Properties - Message
    @property
    def message(self) -> str | None:
        """Human-readable message describing the event."""
        return self._message
    
    @message.setter
    def message(self, value: str | None):
        self._message = value
    
    # Properties - Duration
    @property
    def duration_ms(self) -> int | None:
        """Duration in milliseconds (time spent in previous state)."""
        return self._duration_ms
    
    @duration_ms.setter
    def duration_ms(self, value: int | None):
        self._duration_ms = value
    
    # Properties - Error details
    @property
    def error_code(self) -> str | None:
        """Error code (for failed events)."""
        return self._error_code
    
    @error_code.setter
    def error_code(self, value: str | None):
        self._error_code = value
    
    @property
    def error_message(self) -> str | None:
        """Error message (for failed events)."""
        return self._error_message
    
    @error_message.setter
    def error_message(self, value: str | None):
        self._error_message = value
    
    @property
    def error_details(self) -> Dict[str, Any] | None:
        """Additional error details (for failed events)."""
        return self._error_details
    
    @error_details.setter
    def error_details(self, value: Dict[str, Any] | None):
        self._error_details = value
    
    # Properties - Metadata
    @property
    def metadata(self) -> Dict[str, Any] | None:
        """Flexible metadata for event-specific data."""
        return self._metadata
    
    @metadata.setter
    def metadata(self, value: Dict[str, Any] | None):
        self._metadata = value
    
    # Properties - Actor
    @property
    def actor(self) -> str | None:
        """ID of the actor who triggered this event."""
        return self._actor
    
    @actor.setter
    def actor(self, value: str | None):
        self._actor = value
    
    @property
    def actor_type(self) -> str | None:
        """Type of actor (user, system, lambda, step_function)."""
        return self._actor_type
    
    @actor_type.setter
    def actor_type(self, value: str | None):
        self._actor_type = value
    
    # Computed properties
    @property
    def is_error_event(self) -> bool:
        """Check if this is an error event."""
        return self._event_type in [
            WorkflowHistoryEventType.FAILED,
            WorkflowHistoryEventType.STEP_FAILED,
            WorkflowHistoryEventType.TIMED_OUT,
        ]
    
    @property
    def is_terminal_event(self) -> bool:
        """Check if this event represents a terminal state."""
        return self._event_type in [
            WorkflowHistoryEventType.SUCCEEDED,
            WorkflowHistoryEventType.FAILED,
            WorkflowHistoryEventType.CANCELLED,
            WorkflowHistoryEventType.TIMED_OUT,
        ]
