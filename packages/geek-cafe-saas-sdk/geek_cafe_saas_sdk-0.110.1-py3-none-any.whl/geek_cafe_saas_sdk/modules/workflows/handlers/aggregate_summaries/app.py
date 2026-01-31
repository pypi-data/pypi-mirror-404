"""
Lambda handler for aggregating execution metrics summaries.

This handler is triggered by EventBridge on a schedule (e.g., daily at 2 AM UTC)
to aggregate real-time execution metrics into period summaries.

Module-level handler instantiation for connection pooling across warm starts.
The DynamoDB connection is cached at cold start.


Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Any, Dict, Optional

from geek_cafe_saas_sdk.modules.workflows.handlers.aggregate_summaries.app import (
    AggregateSummariesHandler,
)

handler_wrapper = create_handler(
    service_class=AggregateSummariesHandler,
    require_body=True,
    convert_request_case=True
)


    
def lambda_handler(event: dict, context: Any, injected_service=None) -> dict:
    """Lambda entry point."""
    return handler_wrapper.execute(event, context, create_execution, injected_service=injected_service)

