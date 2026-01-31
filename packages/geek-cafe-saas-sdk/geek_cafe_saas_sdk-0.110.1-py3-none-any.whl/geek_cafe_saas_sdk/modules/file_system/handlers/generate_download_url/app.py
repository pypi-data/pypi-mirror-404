"""
Generic Lambda handler for generating presigned download URLs.

Copyright 2024-2025 Geek Cafe, LLC
MIT License. See Project Root for the license information.

Configuration:
    Consumers can inject configuration values through handler_wrapper.config:
    
    Example:
        from geek_cafe_saas_sdk.modules.file_system.handlers.generate_download_url.app import handler_wrapper
        
        # Set config before invoking handler
        handler_wrapper.config["download_bucket"] = "my-downloads-bucket"
        
    Available config parameters:
        - download_bucket: S3 bucket for file downloads (fallback if file metadata doesn't specify)
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.modules.file_system.services import FileSystemService
from geek_cafe_saas_sdk.core.service_result import ServiceResult


# Create handler wrapper (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=FileSystemService,
    require_body=False,  # GET request - body is optional
    convert_request_case=True  # Converts camelCase → snake_case
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Generate presigned URL for file download.
    
    Ultra-thin handler - validation, file lookup, and URL generation
    all happen in the FileSystemService layer.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional FileSystemService for testing
    
    Expected body (camelCase → auto-converted to snake_case):
    {
        // Option 1: Provide file_id (handler looks up bucket/key)
        "fileId": "file-abc-123",
        
        // Option 2: Provide explicit bucket and key
        "bucket": "my-bucket",
        "key": "tenants/tenant-123/users/user-456/uploads/file.pdf",
        
        // Optional fields for both:
        "fileName": "data.xlsx",  // For Content-Disposition header
        "expiresIn": 300          // Defaults to 300 seconds
    }
    
    Returns:
        200 with presigned download URL or error response
    """
    return handler_wrapper.execute(event, context, generate_download_url_logic, injected_service)


def generate_download_url_logic(
    event: LambdaEvent,
    service: FileSystemService
) -> ServiceResult:
    """
    Ultra-thin business logic - pass payload to service.
    
    Service handles:
    - Field validation (file_id vs bucket/key)
    - File lookup by file_id (gets bucket/key from FileSystemService)
    - Access control validation (tenant isolation)
    - Presigned URL generation via S3FileService
    - Response formatting
    
    Returns:
        ServiceResult from service.generate_download_url()
    """

    # Check body, path params, and query params (for GET requests)
    file_id = event.body_get("fileId") or event.path("fileId") or event.query("fileId")

    payload = {
        "file_id": file_id,
        "bucket": event.body_get("bucket") or event.path("bucket") or event.query("bucket"),
        "key": event.body_get("key") or event.path("key") or event.query("key"),
        "file_name": event.body_get("fileName") or event.path("fileName") or event.query("fileName"),
        "expires_in": event.body_get("expiresIn") or event.path("expiresIn") or event.query("expiresIn")
    }
    return service.generate_download_url(**payload)
