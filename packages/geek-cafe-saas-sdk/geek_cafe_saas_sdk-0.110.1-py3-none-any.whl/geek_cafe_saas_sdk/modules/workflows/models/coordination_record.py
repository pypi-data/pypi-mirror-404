"""
Coordination record model for tracking distributed processing completion.

This model uses atomic counters to track completion state without scanning
all items. Designed for high-scale workflows with millions of items.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from enum import Enum
from typing import Optional
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from geek_cafe_saas_sdk.core.models.base_model import BaseModel


class CoordinationStatus(str, Enum):
    """Status of coordination."""
    STREAMING = "streaming"  # Producer still creating items
    PROCESSING = "processing"  # All items created, waiting for completion
    COMPLETED = "completed"  # All items completed successfully
    FAILED = "failed"  # One or more items failed


class CoordinationRecord(BaseModel):
    """
    Tracks completion state for distributed processing using atomic counters.
    
    This model solves the scalability problem of checking if all items are
    complete by using DynamoDB's atomic ADD operation instead of scanning
    all items.
    
    Two-Phase Pattern:
    1. Streaming Phase: Producer creates items, consumers may start processing
       - total_expected = None (unknown)
       - is_finalized = False
       - Consumers increment completed_count/failed_count atomically
    
    2. Processing Phase: Producer finishes, total is known
       - total_expected = N (known)
       - is_finalized = True
       - Consumers continue incrementing counters
       - Check: (completed_count + failed_count) >= total_expected
    
    Access Patterns (DynamoDB Keys):
    - pk: coord#{execution_id}
    - sk: step#{step_type}
    - gsi1: Coordinations by execution_id (for cleanup/monitoring)
    
    Example:
        # Phase 1: Start streaming
        coord = CoordinationRecord()
        coord.execution_id = "exec-123"
        coord.step_type = "calculation"
        coord.total_expected = None  # Unknown yet
        coord.is_finalized = False
        coord.status = CoordinationStatus.STREAMING
        service.create(coord)
        
        # Consumers increment as they complete
        service.increment_completed("exec-123", "calculation")
        
        # Phase 2: Finalize when streaming done
        service.finalize("exec-123", "calculation", total_expected=1000000)
        
        # Check completion (O(1) lookup, not O(n) scan!)
        result = service.check_completion("exec-123", "calculation")
        if result.is_complete:
            # All done! Dispatch dependent steps
    """

    def __init__(self):
        super().__init__()
        
        self._execution_id: str | None = None
        self._step_type: str | None = None
        
        # Atomic counters - incremented by consumers
        self._total_expected: int | None = None  # Set when finalized
        self._completed_count: int = 0
        self._failed_count: int = 0
        
        # State
        self._is_finalized: bool = False
        self._status: str = CoordinationStatus.STREAMING.value
        
        # Timestamps
        self._created_utc_ts: float | None = None
        self._finalized_utc_ts: float | None = None
        self._completed_utc_ts: float | None = None
        
        # Metadata
        self._error_message: str | None = None
        self._metadata: dict | None = None
        
        self.model_name = "coordination_record"
        self.model_name_plural = "coordination_records"
        self._setup_indexes()

    def _setup_indexes(self):
        """Setup DynamoDB indexes."""
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("coord", self._execution_id)
        )
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(
            ("step", self._step_type)
        )
        self.indexes.add_primary(primary)
        self._setup_gsi1()

    def _setup_gsi1(self):
        """GSI1: Coordinations by execution_id for cleanup/monitoring."""
        gsi = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = "gsi1_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("execution", self._execution_id)
        )
        gsi.sort_key.attribute_name = "gsi1_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("model", "coordination_record"),
            ("step", self._step_type)
        )
        self.indexes.add_secondary(gsi)

    @property
    def execution_id(self) -> str | None:
        return self._execution_id

    @execution_id.setter
    def execution_id(self, value: str | None):
        self._execution_id = value

    @property
    def step_type(self) -> str | None:
        return self._step_type

    @step_type.setter
    def step_type(self, value: str | None):
        self._step_type = value

    @property
    def total_expected(self) -> int | None:
        return self._total_expected

    @total_expected.setter
    def total_expected(self, value: int | None):
        self._total_expected = int(value) if value is not None else None

    @property
    def completed_count(self) -> int:
        return self._completed_count

    @completed_count.setter
    def completed_count(self, value: int):
        self._completed_count = int(value) if value else 0

    @property
    def failed_count(self) -> int:
        return self._failed_count

    @failed_count.setter
    def failed_count(self, value: int):
        self._failed_count = int(value) if value else 0

    @property
    def is_finalized(self) -> bool:
        return self._is_finalized

    @is_finalized.setter
    def is_finalized(self, value: bool):
        self._is_finalized = bool(value) if value is not None else False

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str):
        if isinstance(value, CoordinationStatus):
            self._status = value.value
        else:
            self._status = value

    @property
    def created_utc_ts(self) -> float | None:
        return self._created_utc_ts

    @created_utc_ts.setter
    def created_utc_ts(self, value: float | None):
        self._created_utc_ts = self._safe_number_conversion(value)

    @property
    def finalized_utc_ts(self) -> float | None:
        return self._finalized_utc_ts

    @finalized_utc_ts.setter
    def finalized_utc_ts(self, value: float | None):
        self._finalized_utc_ts = self._safe_number_conversion(value)

    @property
    def completed_utc_ts(self) -> float | None:
        return self._completed_utc_ts

    @completed_utc_ts.setter
    def completed_utc_ts(self, value: float | None):
        self._completed_utc_ts = self._safe_number_conversion(value)

    @property
    def error_message(self) -> str | None:
        return self._error_message

    @error_message.setter
    def error_message(self, value: str | None):
        self._error_message = value

    @property
    def metadata(self) -> dict | None:
        return self._metadata

    @metadata.setter
    def metadata(self, value: dict | None):
        self._metadata = value

    @property
    def is_complete(self) -> bool:
        """
        Check if coordination is complete.
        
        Only returns True if:
        1. Finalized (total_expected is known)
        2. All items processed (completed + failed >= total)
        """
        if not self._is_finalized or self._total_expected is None:
            return False
        return (self._completed_count + self._failed_count) >= self._total_expected

    @is_complete.setter
    def is_complete(self, value: bool):
        """Read-only property, setter exists for serialization."""
        pass

    @property
    def has_failures(self) -> bool:
        """Check if any items failed."""
        return self._failed_count > 0

    @has_failures.setter
    def has_failures(self, value: bool):
        """Read-only property, setter exists for serialization."""
        pass

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if not self._is_finalized or not self._total_expected:
            return 0.0
        processed = self._completed_count + self._failed_count
        return (processed / self._total_expected) * 100.0

    @progress_percentage.setter
    def progress_percentage(self, value: float):
        """Read-only property, setter exists for serialization."""
        pass

    @property
    def pending_count(self) -> int:
        """Calculate pending items count."""
        if not self._is_finalized or not self._total_expected:
            return 0
        processed = self._completed_count + self._failed_count
        return max(0, self._total_expected - processed)

    @pending_count.setter
    def pending_count(self, value: int):
        """Read-only property, setter exists for serialization."""
        pass
