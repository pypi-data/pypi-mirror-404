"""
Step Messages for Workflow Orchestration.

These dataclasses define the message formats used for communication between
the workflow orchestrator and step handlers via SQS queues.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional
import json

from geek_cafe_saas_sdk.utilities.sqs_helpers import parse_sqs_message_body


@dataclass
class StepMessage:
    """
    Standard message format for dispatching steps to queues.
    
    This is the message structure sent from the orchestrator to each
    step handler. Contains everything the handler needs to:
    1. Identify the execution and step
    2. Locate input files
    3. Know where to write output
    4. Get step-specific configuration
    5. Report completion back
    """
    
    # Identifiers
    execution_id: str
    """Root execution ID - links all steps together."""
    
    step_id: str
    """Unique identifier for this specific step."""
    
    tenant_id: str
    """Tenant ID for multi-tenancy."""
    
    user_id: str
    """User who initiated the execution."""
    
    # Step metadata
    step_type: str = ""
    """Type of step being executed (e.g., 'data_cleaning', 'calculation')."""
    
    step_index: int = 0
    """Order in the pipeline (for dependency tracking)."""
    
    # Input/Output locations
    input_dir: Optional[str] = None
    """URI for input files (e.g., s3://bucket/path/)."""
    
    output_dir: Optional[str] = None
    """URI for output files."""
    
    # Step-specific configuration
    input_payload: Dict[str, Any] = field(default_factory=dict)
    """Configuration specific to this step."""
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    """List of step_ids that must complete before this step can run."""
    
    # Callback info
    callback_queue_url: Optional[str] = None
    """SQS queue URL to notify on completion."""
    
    # Timestamps
    created_utc: Optional[str] = None
    """ISO timestamp when message was created."""
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata to pass through to the handler."""
    
    def __post_init__(self):
        """Set defaults after initialization."""
        if self.created_utc is None:
            self.created_utc = datetime.now(UTC).isoformat()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StepMessage":
        """Create from dictionary (e.g., parsed SQS message body)."""
        return cls(
            execution_id=data["execution_id"],
            step_id=data["step_id"],
            tenant_id=data["tenant_id"],
            user_id=data["user_id"],
            step_type=data.get("step_type", ""),
            step_index=data.get("step_index", 0),
            input_dir=data.get("input_dir"),
            output_dir=data.get("output_dir"),
            input_payload=data.get("input_payload", {}),
            depends_on=data.get("depends_on", []),
            callback_queue_url=data.get("callback_queue_url"),
            created_utc=data.get("created_utc"),
            metadata=data.get("metadata", {}),
        )
    
    @classmethod
    def from_sqs_record(cls, record: Dict[str, Any]) -> "StepMessage":
        """Create from SQS record."""
        body = parse_sqs_message_body(record)
        return cls.from_dict(body)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "execution_id": self.execution_id,
            "step_id": self.step_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "step_type": self.step_type,
            "step_index": self.step_index,
            "input_dir": self.input_dir,
            "output_dir": self.output_dir,
            "input_payload": self.input_payload,
            "depends_on": self.depends_on,
            "callback_queue_url": self.callback_queue_url,
            "created_utc": self.created_utc,
            "metadata": self.metadata,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string for SQS message body."""
        return json.dumps(self.to_dict())


@dataclass
class StepCompletionMessage:
    """
    Message sent when a step completes (success or failure).
    
    This is sent to the step completion queue for the workflow controller
    to track overall execution progress and dispatch next steps.
    """
    
    # Identifiers
    execution_id: str
    """Root execution ID."""
    
    step_id: str
    """The step that completed."""
    
    step_type: str = ""
    """Type of step that completed."""
    
    # Status
    status: str = ""
    """
    Completion status. One of:
    - completed: Step finished successfully
    - failed: Step failed with error
    - skipped: Step was skipped
    """
    
    # Results
    output_payload: Dict[str, Any] = field(default_factory=dict)
    """Output from the step (files created, metrics, etc.)."""
    
    error: Optional[str] = None
    """Error message if status is 'failed'."""
    
    error_code: Optional[str] = None
    """Error code if status is 'failed'."""
    
    error_details: Optional[Dict[str, Any]] = None
    """Additional error details (stack trace, etc.)."""
    
    # Timing
    started_utc: Optional[str] = None
    """ISO timestamp when step started."""
    
    completed_utc: Optional[str] = None
    """ISO timestamp when step completed."""
    
    duration_ms: Optional[int] = None
    """Duration in milliseconds."""
    
    # Context
    tenant_id: Optional[str] = None
    """Tenant ID for routing/filtering."""
    
    user_id: Optional[str] = None
    """User ID for routing/filtering."""
    
    def __post_init__(self):
        """Set defaults after initialization."""
        if self.completed_utc is None:
            self.completed_utc = datetime.now(UTC).isoformat()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StepCompletionMessage":
        """Create from dictionary."""
        return cls(
            execution_id=data["execution_id"],
            step_id=data["step_id"],
            step_type=data.get("step_type", ""),
            status=data.get("status", ""),
            output_payload=data.get("output_payload", {}),
            error=data.get("error"),
            error_code=data.get("error_code"),
            error_details=data.get("error_details"),
            started_utc=data.get("started_utc"),
            completed_utc=data.get("completed_utc"),
            duration_ms=data.get("duration_ms"),
            tenant_id=data.get("tenant_id"),
            user_id=data.get("user_id"),
        )
    
    @classmethod
    def from_sqs_record(cls, record: Dict[str, Any]) -> "StepCompletionMessage":
        """Create from SQS record."""
        body = parse_sqs_message_body(record)
        return cls.from_dict(body)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "execution_id": self.execution_id,
            "step_id": self.step_id,
            "step_type": self.step_type,
            "status": self.status,
            "output_payload": self.output_payload,
            "completed_utc": self.completed_utc,
        }
        
        if self.error:
            result["error"] = self.error
        if self.error_code:
            result["error_code"] = self.error_code
        if self.error_details:
            result["error_details"] = self.error_details
        if self.started_utc:
            result["started_utc"] = self.started_utc
        if self.duration_ms is not None:
            result["duration_ms"] = self.duration_ms
        if self.tenant_id:
            result["tenant_id"] = self.tenant_id
        if self.user_id:
            result["user_id"] = self.user_id
            
        return result
    
    def to_json(self) -> str:
        """Convert to JSON string for SQS message body."""
        return json.dumps(self.to_dict())
    
    @property
    def is_success(self) -> bool:
        """Check if step completed successfully."""
        return self.status == "completed"
    
    @property
    def is_failure(self) -> bool:
        """Check if step failed."""
        return self.status == "failed"
