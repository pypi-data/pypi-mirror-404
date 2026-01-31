"""
SQS Lambda handler for batch message processing.

Provides a handler specifically designed for SQS-triggered Lambda functions
that need to return batchItemFailures for partial batch failure reporting.
"""

from typing import Dict, Any, Callable, Optional, List, Type, TypeVar
from aws_lambda_powertools import Logger

from .service_pool import ServicePool
from .lambda_event import LambdaEvent

logger = Logger()

T = TypeVar('T')  # Service type


class SqsLambdaHandler:
    """
    Handler for SQS-triggered Lambda functions with batch failure reporting.
    
    Unlike API Gateway handlers, SQS handlers:
    - Process batches of messages from SQS
    - Return batchItemFailures for partial batch failure reporting
    - Don't wrap responses in API Gateway format
    - Don't require requestContext or authentication headers
    
    IMPORTANT - Return Value Behavior:
    - SQS ONLY uses the "batchItemFailures" key to determine retry behavior
    - Additional keys like "statusCode" and "message" are included for testing/debugging
    - These additional keys DO NOT affect SQS behavior in any way
    - They are useful for integration tests to understand step outcomes
    - If batchItemFailures is empty, SQS considers the entire batch successful
    - If batchItemFailures has items, SQS will retry those specific messages
    
    Example:
        handler = SqsLambdaHandler(
            service_class=DataCleaningHandler,
        )
        
        def lambda_handler(event, context):
            return handler.execute(event, context, process_messages)
        
        def process_messages(event: LambdaEvent, service: DataCleaningHandler) -> Dict:
            # service.handle() should return {"batchItemFailures": [...]}
            return service.handle(event.raw, context=None)
    """
    
    def __init__(
        self,
        service_class: Optional[Type[T]] = None,
        service_kwargs: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize SQS handler.
        
        Args:
            service_class: Service class to instantiate for processing
            service_kwargs: Additional kwargs for service instantiation
            config: Optional configuration dict passed to LambdaEvent
        """
        self.service_class = service_class
        self.service_kwargs = service_kwargs or {}
        self.config = config or {}
        
        # Initialize service pool if a class is provided
        self._service_pool = ServicePool(service_class, **self.service_kwargs) if service_class else None

    def _get_service(self, injected_service: Optional[T] = None) -> Optional[T]:
        """
        Get service instance (injected or from pool).
        
        Args:
            injected_service: Injected service for testing
            
        Returns:
            Service instance
        """
        if injected_service:
            return injected_service
        
        if self._service_pool:
            return self._service_pool.get()
        
        if self.service_class:
            return self.service_class(**self.service_kwargs)

        return None

    def execute(
        self,
        event: Dict[str, Any],
        context: Any,
        business_logic: Callable,
        injected_service: Optional[T] = None
    ) -> Dict[str, Any]:
        """
        Execute the SQS Lambda handler with the given business logic.
        
        Args:
            event: Lambda event dictionary containing SQS Records
            context: Lambda context object
            business_logic: Callable(event: LambdaEvent, service) that returns 
                           {"batchItemFailures": [...]} or similar dict
            injected_service: Optional service instance for testing
            
        Returns:
            Dict with:
            - batchItemFailures: List of failed message IDs (used by SQS for retries)
            - statusCode: HTTP-style status code (for testing/debugging only)
            - message: Human-readable message (for testing/debugging only)
            
            NOTE: SQS ONLY uses batchItemFailures. The statusCode and message are
            included for testing and debugging purposes but do not affect SQS behavior.
        """
        records = event.get("Records", [])
        logger.info(f"Processing SQS batch with {len(records)} records")
        logger.info(event)
        try:
            # Get service instance
            service = self._get_service(injected_service)
            
            # Wrap event in LambdaEvent for convenient access
            lambda_event = LambdaEvent(event, config=self.config)
            
            # Execute business logic - expects dict with batchItemFailures
            result = business_logic(lambda_event, service)
            
            # Validate result format
            if not isinstance(result, dict):
                logger.error(f"Business logic returned {type(result)}, expected dict")
                # Return all messages as failures
                return {
                    "batchItemFailures": [
                        {"itemIdentifier": r.get("messageId", f"unknown-{i}")}
                        for i, r in enumerate(records)
                    ],
                    "statusCode": 500,
                    "message": f"Business logic returned {type(result)}, expected dict"
                }
            
            # Log results and enhance return dict with status info
            failures = result.get("batchItemFailures", [])
            if failures:
                logger.warning(f"Batch processing completed with {len(failures)} failures")
                # Add status info if not already present (for testing/debugging)
                if "statusCode" not in result:
                    result["statusCode"] = 207  # Multi-Status (partial success)
                if "message" not in result:
                    result["message"] = f"Batch processing completed with {len(failures)}/{len(records)} failures"
            else:
                logger.info(f"Batch processing completed successfully ({len(records)} messages)")
                # Add success status info if not already present
                if "statusCode" not in result:
                    result["statusCode"] = 200
                if "message" not in result and result["statusCode"] == 200:
                    result["message"] = f"Batch processing completed successfully ({len(records)} messages)"
            
            return result
            
        except Exception as e:
            logger.exception(f"SQS handler execution error: {e}")
            # Return all messages as failures so they can be retried
            return {
                "batchItemFailures": [
                    {"itemIdentifier": r.get("messageId", f"unknown-{i}")}
                    for i, r in enumerate(records)
                ],
                "statusCode": 500,
                "message": f"SQS handler execution error: {str(e)}"
            }


def create_sqs_handler(
    service_class: Optional[Type[T]] = None,
    **kwargs
) -> SqsLambdaHandler:
    """
    Convenience function for creating SQS handlers.
    
    Example:
        from geek_cafe_saas_sdk.lambda_handlers import create_sqs_handler
        
        handler = create_sqs_handler(
            service_class=DataCleaningHandler,
        )
        
        def lambda_handler(event, context):
            return handler.execute(event, context, process_batch)
    """
    return SqsLambdaHandler(service_class=service_class, **kwargs)
