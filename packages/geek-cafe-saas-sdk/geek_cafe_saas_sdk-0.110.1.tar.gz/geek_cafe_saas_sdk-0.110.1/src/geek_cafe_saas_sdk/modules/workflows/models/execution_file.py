"""
Execution file model for tracking files associated with workflow executions.

This is a junction table model that creates a many-to-many relationship between
executions and files, allowing efficient queries for:
- All files associated with an execution
- All executions that use a specific file
- Files filtered by type (input, profile, calculation, output, etc.)
- Files filtered by role (source, cleaned, result, listing, summary, etc.)

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from geek_cafe_saas_sdk.core.models.base_model import BaseModel


class ExecutionFile(BaseModel):
    """
    Junction model tracking files associated with workflow executions.
    
    This model follows the Single Responsibility Principle by only tracking
    the relationship between executions and files, without duplicating data
    from either the Execution or File models.
    
    Access Patterns (DynamoDB Keys):
    - pk: execution#{execution_id}
    - sk: file#{file_id}
    - gsi1: execution_id + file_type (query all files of a type for an execution)
    - gsi2: file_id (reverse lookup: which executions use this file)
    - gsi3: execution_id + created_by_step (query files created by a specific step)
    
    Example Usage:
        # Link a calculation result file to an execution
        exec_file = ExecutionFile()
        exec_file.execution_id = "exec-123"
        exec_file.file_id = "file-456"
        exec_file.file_type = "calculation"
        exec_file.file_role = "result"
        exec_file.created_by_step = "calculation"
        exec_file.metadata = {"profile_id": "subject_1"}
        
        # Query all calculation files for an execution
        query_model = ExecutionFile()
        query_model.execution_id = "exec-123"
        query_model.file_type = "calculation"
        # Use service to query by gsi1
    """

    def __init__(self):
        super().__init__()
        
        # Core relationship fields
        self._execution_id: str | None = None
        self._file_id: str | None = None
        
        # Classification fields
        self._file_type: str | None = None  # "input", "profile", "calculation", "output", "package"
        self._file_role: str | None = None  # "source", "cleaned", "result", "listing", "summary", etc.
        
        # Tracking fields
        self._created_by_step: str | None = None  # Which workflow step created this file
        self._step_id: str | None = None  # Full step ID if available
        
        # Metadata for step-specific information
        self._metadata: Dict[str, Any] = {}
        
        # Timestamps
        self._linked_utc_ts: float | None = None  # When the file was linked to execution
        
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for efficient queries."""
        
        # Primary index: execution_id + file_id (composite key)
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("execution", self._execution_id)
        )
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(
            ("file", self._file_id)
        )
        self.indexes.add_primary(primary)
        
        # GSI1: Query files by execution + file_type
        # Use case: Get all calculation files for an execution
        gsi1 = DynamoDBIndex()
        gsi1.name = "gsi1"
        gsi1.partition_key.attribute_name = f"{gsi1.name}_pk"
        gsi1.partition_key.value = lambda: DynamoDBKey.build_key(
            ("execution", self._execution_id)
        )
        gsi1.sort_key.attribute_name = f"{gsi1.name}_sk"
        gsi1.sort_key.value = lambda: DynamoDBKey.build_key(
            ("type", self._file_type),
            ("role", self._file_role),
            ("file", self._file_id)
        )
        self.indexes.add_secondary(gsi1)
        
        # GSI2: Reverse lookup - which executions use this file
        # Use case: Find all executions that used a specific input file
        gsi2 = DynamoDBIndex()
        gsi2.name = "gsi2"
        gsi2.partition_key.attribute_name = f"{gsi2.name}_pk"
        gsi2.partition_key.value = lambda: DynamoDBKey.build_key(
            ("file", self._file_id)
        )
        gsi2.sort_key.attribute_name = f"{gsi2.name}_sk"
        gsi2.sort_key.value = lambda: DynamoDBKey.build_key(
            ("execution", self._execution_id)
        )
        self.indexes.add_secondary(gsi2)
        
        # GSI3: Query files by execution + step that created them
        # Use case: Get all files created by the profile_split step
        gsi3 = DynamoDBIndex()
        gsi3.name = "gsi3"
        gsi3.partition_key.attribute_name = f"{gsi3.name}_pk"
        gsi3.partition_key.value = lambda: DynamoDBKey.build_key(
            ("execution", self._execution_id)
        )
        gsi3.sort_key.attribute_name = f"{gsi3.name}_sk"
        gsi3.sort_key.value = lambda: DynamoDBKey.build_key(
            ("step", self._created_by_step),
            ("file", self._file_id)
        )
        self.indexes.add_secondary(gsi3)
    
    # Properties
    @property
    def execution_id(self) -> str | None:
        """ID of the execution this file is associated with."""
        return self._execution_id
    
    @execution_id.setter
    def execution_id(self, value: str | None):
        self._execution_id = value
    
    @property
    def file_id(self) -> str | None:
        """ID of the file (from FileSystem)."""
        return self._file_id
    
    @file_id.setter
    def file_id(self, value: str | None):
        self._file_id = value
    
    @property
    def file_type(self) -> str | None:
        """
        Type of file in the workflow.
        
        Common values:
        - "input": Original input file
        - "profile": Split profile file
        - "calculation": Calculation result file
        - "output": Final output file (results, listings, summaries)
        - "package": Packaged/zipped output
        """
        return self._file_type
    
    @file_type.setter
    def file_type(self, value: str | None):
        self._file_type = value
    
    @property
    def file_role(self) -> str | None:
        """
        Role/purpose of the file within its type.
        
        Common values:
        - "source": Original source file
        - "cleaned": Cleaned/validated version
        - "split": Split/partitioned file
        - "result": Calculation result
        - "listing": Detailed listing output
        - "summary": Summary output
        - "report": Report file
        """
        return self._file_role
    
    @file_role.setter
    def file_role(self, value: str | None):
        self._file_role = value
    
    @property
    def created_by_step(self) -> str | None:
        """Name of the workflow step that created this file."""
        return self._created_by_step
    
    @created_by_step.setter
    def created_by_step(self, value: str | None):
        self._created_by_step = value
    
    @property
    def step_id(self) -> str | None:
        """Full step ID if available (execution_id:step_type:step_uuid)."""
        return self._step_id
    
    @step_id.setter
    def step_id(self, value: str | None):
        self._step_id = value
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Step-specific metadata about the file.
        
        Examples:
        - {"profile_id": "subject_1", "batch_number": 1}
        - {"input_file_id": "file-123", "calculation_success": true}
        - {"output_format": "csv", "row_count": 100}
        """
        return self._metadata
    
    @metadata.setter
    def metadata(self, value: Dict[str, Any]):
        self._metadata = value if value is not None else {}
    
    @property
    def linked_utc_ts(self) -> float | None:
        """Timestamp when the file was linked to the execution."""
        return self._linked_utc_ts
    
    @linked_utc_ts.setter
    def linked_utc_ts(self, value: float | None):
        self._linked_utc_ts = value
