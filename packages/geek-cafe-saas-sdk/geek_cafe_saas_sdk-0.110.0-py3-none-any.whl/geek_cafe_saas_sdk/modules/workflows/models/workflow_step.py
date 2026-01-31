"""
WorkflowStep model for tracking individual steps within an execution.

Represents a single step in a multi-step workflow with dependency tracking.
Steps are linked to a parent Execution and can depend on other steps.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any, Optional, List
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


class StepStatus:
    """Step status constants."""
    PENDING = "pending"          # Waiting for dependencies
    DISPATCHED = "dispatched"    # Sent to queue, waiting to start
    RUNNING = "running"          # Currently executing
    COMPLETED = "completed"      # Finished successfully
    FAILED = "failed"            # Finished with error
    SKIPPED = "skipped"          # Skipped (not needed or disabled)
    CANCELLED = "cancelled"      # Manually cancelled
    TIMED_OUT = "timed_out"      # Exceeded time limit
    
    ALL = [PENDING, DISPATCHED, RUNNING, COMPLETED, FAILED, SKIPPED, CANCELLED, TIMED_OUT]
    
    # Terminal states (step is complete)
    TERMINAL = [COMPLETED, FAILED, SKIPPED, CANCELLED, TIMED_OUT]
    
    # Success states (for dependency resolution)
    SUCCESS = [COMPLETED, SKIPPED]
    
    # Valid transitions
    TRANSITIONS = {
        PENDING: [DISPATCHED, RUNNING, SKIPPED, CANCELLED],
        DISPATCHED: [RUNNING, FAILED, CANCELLED, TIMED_OUT],
        RUNNING: [COMPLETED, FAILED, CANCELLED, TIMED_OUT],
        COMPLETED: [],  # Terminal
        FAILED: [PENDING],  # Allow retry
        SKIPPED: [],  # Terminal
        CANCELLED: [],  # Terminal
        TIMED_OUT: [PENDING],  # Allow retry
    }
    
    @classmethod
    def can_transition(cls, from_status: str, to_status: str) -> bool:
        """Check if a status transition is valid."""
        return to_status in cls.TRANSITIONS.get(from_status, [])
    
    @classmethod
    def is_terminal(cls, status: str) -> bool:
        """Check if status is a terminal state."""
        return status in cls.TERMINAL
    
    @classmethod
    def is_success(cls, status: str) -> bool:
        """Check if status is a success state (for dependency resolution)."""
        return status in cls.SUCCESS


class WorkflowStep(BaseTenantUserModel):
    """
    WorkflowStep model for tracking steps within an execution.
    
    Represents a single step in a multi-step workflow. Steps can have
    dependencies on other steps and are tracked independently.
    
    Multi-Tenancy:
    - tenant_id: Organization/company
    - owner_id: User who owns the parent execution
    
    Hierarchy:
    - execution_id: The parent execution this step belongs to
    - depends_on: List of step_ids this step depends on
    
    Access Patterns (DynamoDB Keys):
    - pk: EXECUTION#{execution_id}
    - sk: STEP#{step_id}
    - gsi1: Steps by execution + status (for finding dispatchable steps)
    - gsi2: Steps by execution + step_type (for type-based queries)
    """

    def __init__(self):
        super().__init__()
        
        # Identity
        self._step_id: str | None = None
        self._execution_id: str | None = None
        
        # Step classification
        self._step_type: str | None = None        # e.g., "data_cleaning", "calculation"
        self._step_name: str | None = None        # Human-readable name
        self._step_index: int| None = None                 # Order in the workflow
        
        # Dependencies
        self._depends_on: List[str] | None = None  # List of step_ids this depends on
        
        # Queue/Dispatch info
        self._queue_name: str | None = None       # Queue this step runs on
        self._queue_url: str | None = None        # SQS queue URL
        self._message_id: str | None = None       # SQS message ID when dispatched
        
        # Status
        self._status: str = StepStatus.PENDING
        
        # Timestamps
        self._dispatched_utc: str | None = None    # When sent to queue
        self._started_utc: str | None = None       # When processing started
        self._completed_utc: str | None = None     # When processing finished
        self._dispatched_utc_ts: float | None = None
        self._started_utc_ts: float | None = None
        self._completed_utc_ts: float | None = None
        self._duration_ms: int | None = None      # Processing duration
        
        # Input/Output
        self._input_payload: Dict[str, Any] | None = None
        self._output_payload: Dict[str, Any] | None = None
        
        # Error handling
        self._error_code: str | None = None
        self._error_message: str | None = None
        self._error_details: Dict[str, Any] | None = None
        self._retry_count: int = 0
        self._max_retries: int = 3
        
        # Timeout
        self._timeout_seconds: int | None = None
        
        # Flexible metadata
        self._metadata: Dict[str, Any] | None = None
        
        # Model metadata
        self.model_name = "workflow_step"
        self.model_name_plural = "workflow_steps"
        
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for step queries."""
        
        # Primary index: Step within execution
        # pk: EXECUTION#{execution_id}, sk: STEP#{step_id}
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("execution", self._execution_id)
        )
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(
            ("step", self.id)
        )
        self.indexes.add_primary(primary)
        
        # GSI1: Steps by execution + status (for finding dispatchable steps)
        self._setup_gsi1()
        
        # GSI2: Steps by execution + step_type
        self._setup_gsi2()
    
    def _setup_gsi1(self):
        """GSI1: Steps by execution + status."""
        gsi = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = "gsi1_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("execution", self._execution_id)
        )
        gsi.sort_key.attribute_name = "gsi1_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("status", self._status),
            ("index", self.__get_sk_index_filler())
        )
        self.indexes.add_secondary(gsi)
    
    def _setup_gsi2(self):
        """GSI2: Steps by execution + step_type."""
        gsi = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = "gsi2_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("execution", self._execution_id)
        )
        gsi.sort_key.attribute_name = "gsi2_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("type", self._step_type),
            ("index", self.__get_sk_index_filler())
        )
        self.indexes.add_secondary(gsi)
    
    def __get_sk_index_filler(self)-> str:
        if self._step_index is None:
            return ""
        return str(self._step_index).zfill(6)

    # Properties - Identity
    @property
    def step_id(self) -> str | None:
        """Unique step ID."""
        return self._step_id or self.id
    
    @step_id.setter
    def step_id(self, value: str | None):
        self._step_id = value
        if value:
            self.id = value
    
    @property
    def execution_id(self) -> str | None:
        """Parent execution ID."""
        return self._execution_id
    
    @execution_id.setter
    def execution_id(self, value: str | None):
        self._execution_id = value
    
    # Properties - Classification
    @property
    def step_type(self) -> str | None:
        """Type of step (e.g., 'data_cleaning', 'calculation')."""
        return self._step_type
    
    @step_type.setter
    def step_type(self, value: str | None):
        self._step_type = value
    
    @property
    def step_name(self) -> str | None:
        """Human-readable step name."""
        return self._step_name
    
    @step_name.setter
    def step_name(self, value: str | None):
        self._step_name = value
    
    @property
    def step_index(self) -> int:
        """Order in the workflow (0-based)."""
        return self._step_index
    
    @step_index.setter
    def step_index(self, value: int):
        self._step_index = value
    
    # Properties - Dependencies
    @property
    def depends_on(self) -> List[str]:
        """List of step_ids this step depends on."""
        if self._depends_on is None:
            self._depends_on = []
        return self._depends_on
    
    @depends_on.setter
    def depends_on(self, value: List[str] | None):
        self._depends_on = value if value is not None else []
    
    # Properties - Queue/Dispatch
    @property
    def queue_name(self) -> str | None:
        """Queue name this step runs on."""
        return self._queue_name
    
    @queue_name.setter
    def queue_name(self, value: str | None):
        self._queue_name = value
    
    @property
    def queue_url(self) -> str | None:
        """SQS queue URL."""
        return self._queue_url
    
    @queue_url.setter
    def queue_url(self, value: str | None):
        self._queue_url = value
    
    @property
    def message_id(self) -> str | None:
        """SQS message ID when dispatched."""
        return self._message_id
    
    @message_id.setter
    def message_id(self, value: str | None):
        self._message_id = value
    
    # Properties - Status
    @property
    def status(self) -> str:
        """Current step status."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        self._status = value
    
    # Properties - Timestamps
    @property
    def dispatched_utc(self) -> str | None:
        """ISO datetime when step was dispatched to queue."""
        return self._dispatched_utc
    
    @dispatched_utc.setter
    def dispatched_utc(self, value: str | None):
        self._dispatched_utc = value
    
    @property
    def started_utc(self) -> str | None:
        """ISO datetime when step started processing."""
        return self._started_utc
    
    @started_utc.setter
    def started_utc(self, value: str | None):
        self._started_utc = value
    
    @property
    def completed_utc(self) -> str | None:
        """ISO datetime when step completed."""
        return self._completed_utc
    
    @completed_utc.setter
    def completed_utc(self, value: str | None):
        self._completed_utc = value
    
    @property
    def dispatched_utc_ts(self) -> float | None:
        """Timestamp when dispatched (for sorting)."""
        return self._dispatched_utc_ts
    
    @dispatched_utc_ts.setter
    def dispatched_utc_ts(self, value: float | None):
        self._dispatched_utc_ts = value
    
    @property
    def started_utc_ts(self) -> float | None:
        """Timestamp when started (for sorting)."""
        return self._started_utc_ts
    
    @started_utc_ts.setter
    def started_utc_ts(self, value: float | None):
        self._started_utc_ts = value
    
    @property
    def completed_utc_ts(self) -> float | None:
        """Timestamp when completed (for sorting)."""
        return self._completed_utc_ts
    
    @completed_utc_ts.setter
    def completed_utc_ts(self, value: float | None):
        self._completed_utc_ts = value
    
    @property
    def duration_ms(self) -> int | None:
        """Processing duration in milliseconds."""
        return self._duration_ms
    
    @duration_ms.setter
    def duration_ms(self, value: int | None):
        self._duration_ms = value
    
    # Properties - Input/Output
    @property
    def input_payload(self) -> Dict[str, Any] | None:
        """Input payload for this step."""
        return self._input_payload
    
    @input_payload.setter
    def input_payload(self, value: Dict[str, Any] | None):
        self._input_payload = value
    
    @property
    def output_payload(self) -> Dict[str, Any] | None:
        """Output payload from this step."""
        return self._output_payload
    
    @output_payload.setter
    def output_payload(self, value: Dict[str, Any] | None):
        self._output_payload = value
    
    # Properties - Error handling
    @property
    def error_code(self) -> str | None:
        """Error code if step failed."""
        return self._error_code
    
    @error_code.setter
    def error_code(self, value: str | None):
        self._error_code = value
    
    @property
    def error_message(self) -> str | None:
        """Error message if step failed."""
        return self._error_message
    
    @error_message.setter
    def error_message(self, value: str | None):
        self._error_message = value
    
    @property
    def error_details(self) -> Dict[str, Any] | None:
        """Additional error details."""
        return self._error_details
    
    @error_details.setter
    def error_details(self, value: Dict[str, Any] | None):
        self._error_details = value
    
    @property
    def retry_count(self) -> int:
        """Number of retry attempts."""
        return self._retry_count
    
    @retry_count.setter
    def retry_count(self, value: int):
        self._retry_count = value
    
    @property
    def max_retries(self) -> int:
        """Maximum retry attempts allowed."""
        return self._max_retries
    
    @max_retries.setter
    def max_retries(self, value: int):
        self._max_retries = value
    
    # Properties - Timeout
    @property
    def timeout_seconds(self) -> int | None:
        """Timeout in seconds for this step."""
        return self._timeout_seconds
    
    @timeout_seconds.setter
    def timeout_seconds(self, value: int | None):
        self._timeout_seconds = value
    
    # Properties - Metadata
    @property
    def metadata(self) -> Dict[str, Any] | None:
        """Flexible metadata."""
        return self._metadata
    
    @metadata.setter
    def metadata(self, value: Dict[str, Any] | None):
        self._metadata = value
    
    # Computed properties
    def is_terminal(self) -> bool:
        """Check if step is in a terminal state."""
        return StepStatus.is_terminal(self._status)
    
    def is_success(self) -> bool:
        """Check if step completed successfully."""
        return StepStatus.is_success(self._status)
    
    def is_dispatchable(self) -> bool:
        """Check if step can be dispatched (pending with no unmet dependencies)."""
        return self._status == StepStatus.PENDING
    
    def can_retry(self) -> bool:
        """Check if step can be retried."""
        return (
            self._status in [StepStatus.FAILED, StepStatus.TIMED_OUT]
            and self._retry_count < self._max_retries
        )
    
    # Helper methods for setting timestamps
    def set_dispatched_time(self, utc_datetime: Optional[str] = None) -> None:
        """
        Set dispatched timestamp (both UTC and timestamp fields).
        
        Args:
            utc_datetime: ISO datetime string (if None, uses current time)
        """
        from datetime import datetime, UTC
        
        if utc_datetime:
            dt = datetime.fromisoformat(utc_datetime.replace('Z', '+00:00'))
        else:
            dt = datetime.now(UTC)
        
        self._dispatched_utc = dt.isoformat()
        self._dispatched_utc_ts = dt.timestamp()
    
    def set_started_time(self, utc_datetime: Optional[str] = None) -> None:
        """
        Set started timestamp (both UTC and timestamp fields).
        
        Args:
            utc_datetime: ISO datetime string (if None, uses current time)
        """
        from datetime import datetime, UTC
        
        if utc_datetime:
            dt = datetime.fromisoformat(utc_datetime.replace('Z', '+00:00'))
        else:
            dt = datetime.now(UTC)
        
        self._started_utc = dt.isoformat()
        self._started_utc_ts = dt.timestamp()
    
    def set_completed_time(self, utc_datetime: Optional[str] = None) -> None:
        """
        Set completed timestamp (both UTC and timestamp fields).
        Automatically calculates duration_ms if started_utc_ts is set.
        
        Args:
            utc_datetime: ISO datetime string (if None, uses current time)
        """
        from datetime import datetime, UTC
        
        if utc_datetime:
            dt = datetime.fromisoformat(utc_datetime.replace('Z', '+00:00'))
        else:
            dt = datetime.now(UTC)
        
        self._completed_utc = dt.isoformat()
        self._completed_utc_ts = dt.timestamp()
        
        # Calculate duration if started time is set
        if self._started_utc_ts:
            self._duration_ms = int((dt.timestamp() - self._started_utc_ts) * 1000)
