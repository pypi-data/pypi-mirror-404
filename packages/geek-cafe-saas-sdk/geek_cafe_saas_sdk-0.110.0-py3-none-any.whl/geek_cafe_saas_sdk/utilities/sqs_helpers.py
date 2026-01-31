"""
SQS Helper Utilities - Common utilities for working with SQS messages.

Provides case-insensitive field access and message parsing to handle differences
between moto (test mocks) and real AWS Lambda SQS events.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import json
from typing import Any, Dict, Optional


def get_sqs_field(record: Dict[str, Any], field_name: str, default: Any = None) -> Any:
    """
    Get field from SQS record with case-insensitive lookup.
    
    Handles both PascalCase (moto/test mocks) and camelCase (real AWS Lambda).
    
    Args:
        record: SQS record
        field_name: Field name in camelCase (e.g., "body", "messageId")
        default: Default value if field not found
        
    Returns:
        Field value or default
        
    Examples:
        get_sqs_field(record, "body") -> handles both "Body" and "body"
        get_sqs_field(record, "messageId") -> handles both "MessageId" and "messageId"
    """
    # Try PascalCase first (moto format)
    pascal_case = field_name[0].upper() + field_name[1:] if field_name else field_name
    value = record.get(pascal_case)
    
    if value is not None:
        return value
        
    # Try original camelCase (AWS format)
    return record.get(field_name, default)


def parse_sqs_message_body(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse SQS message body from record with case-insensitive field access.
    
    Handles both "Body" (moto/test mocks) and "body" (real AWS Lambda).
    
    Args:
        record: SQS record
        
    Returns:
        Parsed message body as dict
        
    Example:
        body = parse_sqs_message_body(record)
        message = MyMessage.from_dict(body)
    """
    # Use helper to handle both "Body" (moto) and "body" (real AWS)
    body_str = get_sqs_field(record, "body", "{}")
    
    # Handle case where body is already parsed
    if isinstance(body_str, dict):
        return body_str
        
    return json.loads(body_str)
