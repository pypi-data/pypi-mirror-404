"""
Batch record model for tracking calculation batch status.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from enum import Enum
from typing import List, Dict, Any
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from geek_cafe_saas_sdk.core.models.base_model import BaseModel


class BatchStatus(str, Enum):
    """Status of a calculation batch."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BatchRecord(BaseModel):
    """
    Tracks individual batch status within an execution.
    
    Access Patterns (DynamoDB Keys):
    - pk: batch#{id}
    - sk: batch
    - gsi1: Batches by execution_id + batch_number
    - gsi2: Batches by execution_id + status
    """

    def __init__(self):
        super().__init__()
        
        self._execution_id: str | None = None
        self._batch_number: int = 0
        self._files: List[Dict[str, Any]] = []
        self._status: str = BatchStatus.PENDING.value
                
        self._started_utc_ts: float | None = None
        self._completed_utc_ts: float | None = None
        self._error_message: str | None = None
        self._error_code: str | None = None
        self._retry_count: int = 0
        self._items_succeeded: int = 0
        self._items_failed: int = 0
        
        self.model_name = "batch_record"
        self.model_name_plural = "batch_records"
        self._setup_indexes()

    def _setup_indexes(self):
        """Setup DynamoDB indexes."""
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("batch", self.id)
        )
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: "batch_record"
        self.indexes.add_primary(primary)
        self._setup_gsi1()
        self._setup_gsi2()

    def _setup_gsi1(self):
        """GSI1: Batches by execution_id + batch_number."""
        gsi = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = "gsi1_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("execution", self._execution_id)
        )
        gsi.sort_key.attribute_name = "gsi1_sk"
        # Sort key: model#batch_record#batch#NNNNNN
        # When batch_number is None, omit the batch part for begins_with queries
        gsi.sort_key.value = lambda: (
            DynamoDBKey.build_key(("model", "batch_record"))
            if self._batch_number is None
            else DynamoDBKey.build_key(
                ("model", "batch_record"),
                ("batch", f"{self._batch_number:06d}")
            )
        )
        self.indexes.add_secondary(gsi)

    def _setup_gsi2(self):
        """GSI2: Batches by execution_id + status."""
        gsi = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = "gsi2_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("execution", self._execution_id)
        )
        gsi.sort_key.attribute_name = "gsi2_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("model", "batch_record"),
            ("status", self._status)
        )
        self.indexes.add_secondary(gsi)

    @property
    def execution_id(self) -> str | None:
        return self._execution_id

    @execution_id.setter
    def execution_id(self, value: str | None):
        self._execution_id = value

    @property
    def batch_number(self) -> int:
        return self._batch_number

    @batch_number.setter
    def batch_number(self, value: int):
        self._batch_number = int(value) if value else 0

    @property
    def files(self) -> List[Dict[str, Any]]:
        return self._files

    @files.setter
    def files(self, value: List[Dict[str, Any]] | None):
        self._files = value or []

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str):
        if isinstance(value, BatchStatus):
            self._status = value.value
        else:
            self._status = value

    @property
    def started_utc_ts(self) -> float | None:
        return self._started_utc_ts

    @started_utc_ts.setter
    def started_utc_ts(self, value: float | None):
        self._started_utc_ts = self._safe_number_conversion(value)

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
    def error_code(self) -> str | None:
        return self._error_code

    @error_code.setter
    def error_code(self, value: str | None):
        self._error_code = value

    @property
    def retry_count(self) -> int:
        return self._retry_count

    @retry_count.setter
    def retry_count(self, value: int):
        self._retry_count = int(value) if value else 0

    @property
    def items_succeeded(self) -> int:
        return self._items_succeeded

    @items_succeeded.setter
    def items_succeeded(self, value: int):
        self._items_succeeded = int(value) if value else 0

    @property
    def items_failed(self) -> int:
        return self._items_failed

    @items_failed.setter
    def items_failed(self, value: int):
        self._items_failed = int(value) if value else 0

    @property
    def is_complete(self) -> bool:
        """Check if batch processing is complete."""
        return self._status in (BatchStatus.COMPLETED.value, BatchStatus.FAILED.value)

    @is_complete.setter
    def is_complete(self, value: bool):
        """Read-only property, setter exists for serialization."""
        pass

    @property
    def is_successful(self) -> bool:
        """Check if batch completed successfully."""
        return self._status == BatchStatus.COMPLETED.value

    @is_successful.setter
    def is_successful(self, value: bool):
        """Read-only property, setter exists for serialization."""
        pass

    @property
    def duration_ms(self) -> int | None:
        """Calculate processing duration in milliseconds."""
        if self._started_utc_ts and self._completed_utc_ts:
            return int((self._completed_utc_ts - self._started_utc_ts) * 1000)
        return None

    @duration_ms.setter
    def duration_ms(self, value: int | None):
        """Read-only property, setter exists for serialization."""
        pass
