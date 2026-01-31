"""
Get Execution Status Lambda Handler.

GET /executions/{execution-id}/status

Returns the execution with all child steps and an aggregated summary.

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
    return handler_wrapper.execute(event, context, get_execution_status, injected_service=injected_service)


def get_execution_status(
    event: LambdaEvent,
    service: WorkflowService
) -> Any:
    """
    Get execution status with all steps and summary.
    
    Path parameters:
        execution-id or executionId: Execution ID
        
    Query parameters:
        include_steps: Include child steps (default: true)
        exclude_fields: Comma-separated list of fields to exclude (default: input_payload)
                       Use 'none' to include all fields
        
    Returns:
        {
            "execution": { ... root execution (with excluded fields removed) ... },
            "steps": [ ... child executions (with excluded fields removed) ... ],
            "summary": {
                "total_steps": 5,
                "completed": 2,
                "running": 1,
                "pending": 2,
                "failed": 0,
                "progress_percent": 40,
                "duration_seconds": 925,
                "duration_human": "0:15:25",
                "status_counts": { ... },
                "steps": [ ... step breakdown with durations ... ]
            }
        }
        
    Examples:
        # Default (excludes input_payload)
        GET /executions/{id}/status
        
        # Include all fields
        GET /executions/{id}/status?exclude_fields=none
        
        # Exclude multiple fields
        GET /executions/{id}/status?exclude_fields=input_payload,output_payload,metadata
    """
    execution_id = event.path("executionId", "id")
    include_steps = event.query_bool("includeSteps", default=True)
    
    # Parse exclude_fields parameter
    exclude_fields_param = event.query("excludeFields", "input_payload")
    exclude_fields = None
    
    if exclude_fields_param:
        if exclude_fields_param.lower() == "none":
            # Explicitly include all fields
            exclude_fields = []
        else:
            # Parse comma-separated list
            exclude_fields = [f.strip() for f in exclude_fields_param.split(",") if f.strip()]
    # If not specified, use default (None = service default)
    
    return service.get_status(
        execution_id=execution_id,
        include_steps=include_steps,
        exclude_fields=exclude_fields,
    )
