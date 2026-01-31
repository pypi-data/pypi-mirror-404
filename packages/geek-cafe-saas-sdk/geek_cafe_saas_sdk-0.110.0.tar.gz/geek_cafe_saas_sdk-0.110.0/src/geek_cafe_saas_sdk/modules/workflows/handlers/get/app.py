"""
Get Execution Lambda Handler.

GET /executions/{execution-id}

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.modules.workflows.services import WorkflowService

handler_wrapper = create_handler(
    service_class=WorkflowService,
    require_body=False,
    convert_request_case=True
)


def lambda_handler(event: dict, context: Any, injected_service=None) -> dict:
    """Lambda entry point."""
    return handler_wrapper.execute(event, context, get_execution, injected_service=injected_service)


def get_execution(
    event: LambdaEvent,
    service: WorkflowService
) -> Any:
    """
    Get an execution by ID.
    
    Path parameters:
        execution-id or executionId: Execution ID
    """
    execution_id = event.path("execution-id", "executionId", "id")
    return service.get(execution_id=execution_id)
