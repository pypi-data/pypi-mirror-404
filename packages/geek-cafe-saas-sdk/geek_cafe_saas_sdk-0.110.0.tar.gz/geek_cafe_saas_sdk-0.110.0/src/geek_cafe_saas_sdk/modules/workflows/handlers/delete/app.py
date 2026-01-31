"""
Update Execution Lambda Handler.

PATCH /executions/{execution-id}

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.modules.workflows.services import WorkflowService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.error_codes import ErrorCode

handler_wrapper = create_handler(
    service_class=WorkflowService,
    require_body=True,
    convert_request_case=True
)


def lambda_handler(event: dict, context: Any, injected_service=None) -> dict:
    """Lambda entry point."""
    return handler_wrapper.execute(event, context, delete_execution, injected_service=injected_service)


def delete_execution(
    event: LambdaEvent,
    service: WorkflowService
) -> Any:
    """
    Delete an execution.
    
    Path parameters:
        execution-id or executionId: Execution ID
        
    Request body:
        None
    """
    execution_id = event.path("execution-id", "executionId", "id")
    body = event.body
    
    return service.delete(execution_id=execution_id)
    
