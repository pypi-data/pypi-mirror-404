"""
Service Factory for centralized service creation with connection pooling.

Provides a factory pattern for creating services with shared boto3 connections
and proper request context injection. Recommended for Lambda functions to
minimize connection overhead.

Copyright 2024-2025 Geek Cafe, LLC
All Rights Reserved.
"""

from typing import Type, TypeVar, Optional, Dict, Any
import os
from aws_lambda_powertools import Logger

from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3_assist.s3.s3 import S3
from boto3_assist.sqs import SQSConnection

from .request_context import RequestContext
from .services.database_service import DatabaseService

T = TypeVar('T', bound=DatabaseService)

logger = Logger()


class ServiceFactory:
    """
    Factory for creating services with shared connections and request context.
    
    This factory manages boto3 connections using connection pooling for optimal
    Lambda performance. Connections are reused across service instances within
    the same factory, while request context is always passed fresh per request.
    
    Pattern:
        - Module-level factory: Reused in Lambda warm containers
        - Per-request context: Created fresh for each invocation
        - Shared connections: DynamoDB, S3, SQS clients cached
    
    Example (Lambda Handler):
        >>> # Module-level factory (reused in warm container)
        >>> _service_factory = ServiceFactory()
        >>> 
        >>> def lambda_handler(event, context):
        >>>     # Fresh context per request
        >>>     request_context = SystemRequestContext(
        >>>         tenant_id=event["tenant_id"],
        >>>         user_id=event["user_id"],
        >>>         source="lambda"
        >>>     )
        >>>     
        >>>     # Create service with shared connection + fresh context
        >>>     user_service = _service_factory.create_service(
        >>>         UserService,
        >>>         request_context=request_context
        >>>     )
        >>>     
        >>>     return user_service.get_by_id(event["user_id"])
    
    Example (Testing):
        >>> factory = ServiceFactory()
        >>> context = AnonymousContextFactory.create_test_context(
        >>>     tenant_id="test-tenant",
        >>>     user_id="test-user"
        >>> )
        >>> service = factory.create_service(UserService, context)
        >>> result = service.create(user_data)
    """
    
    def __init__(
        self,
        *,
        use_connection_pool: bool = True,
        aws_profile: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_endpoint_url: Optional[str] = None,
    ):
        """
        Initialize ServiceFactory with optional connection parameters.
        
        Args:
            use_connection_pool: Use boto3-assist connection pooling (default: True)
            aws_profile: AWS profile name (optional, for local development)
            aws_region: AWS region (optional, defaults to environment)
            aws_endpoint_url: Custom endpoint URL (optional, for moto/LocalStack)
        
        Note:
            For Lambda functions, leave all AWS parameters as None to use
            the Lambda execution role and environment configuration.
        """
        self._use_connection_pool = use_connection_pool
        self._aws_profile = aws_profile
        self._aws_region = aws_region
        self._aws_endpoint_url = aws_endpoint_url
        
        # Lazy-initialized shared connections
        self._dynamodb: Optional[DynamoDB] = None
        self._s3: Optional[S3] = None
        self._sqs: Optional[SQSConnection] = None
        
        # Track connection creation for debugging
        self._connection_stats = {
            "dynamodb_created": False,
            "s3_created": False,
            "sqs_created": False,
        }
    
    @property
    def dynamodb(self) -> DynamoDB:
        """
        Get shared DynamoDB connection.
        
        Lazy-loads on first access and reuses for all subsequent calls.
        Uses connection pooling by default for Lambda performance.
        
        Returns:
            DynamoDB instance configured with connection pooling
        """
        if self._dynamodb is None:
            logger.debug("Creating shared DynamoDB connection", extra={
                "use_pool": self._use_connection_pool,
                "endpoint": self._aws_endpoint_url
            })
            
            if self._use_connection_pool:
                self._dynamodb = DynamoDB.from_pool(
                    aws_profile=self._aws_profile,
                    aws_region=self._aws_region,
                    aws_end_point_url=self._aws_endpoint_url,
                )
            else:
                self._dynamodb = DynamoDB(
                    aws_profile=self._aws_profile,
                    aws_region=self._aws_region,
                    aws_end_point_url=self._aws_endpoint_url,
                )
            
            self._connection_stats["dynamodb_created"] = True
        
        return self._dynamodb
    
    @property
    def s3(self) -> S3:
        """
        Get shared S3 connection.
        
        Lazy-loads on first access and reuses for all subsequent calls.
        Uses connection pooling by default for Lambda performance.
        
        Returns:
            S3 instance configured with connection pooling
        """
        if self._s3 is None:
            logger.debug("Creating shared S3 connection", extra={
                "use_pool": self._use_connection_pool,
                "endpoint": self._aws_endpoint_url
            })
            
            if self._use_connection_pool:
                self._s3 = S3.from_pool(
                    aws_profile=self._aws_profile,
                    aws_region=self._aws_region,
                    aws_end_point_url=self._aws_endpoint_url,
                )
            else:
                self._s3 = S3(
                    aws_profile=self._aws_profile,
                    aws_region=self._aws_region,
                    aws_end_point_url=self._aws_endpoint_url,
                )
            
            self._connection_stats["s3_created"] = True
        
        return self._s3
    
    @property
    def sqs(self) -> SQSConnection:
        """
        Get shared SQS connection.
        
        Lazy-loads on first access and reuses for all subsequent calls.
        Uses connection pooling by default for Lambda performance.
        
        Returns:
            SQSConnection instance configured with connection pooling
        """
        if self._sqs is None:
            logger.debug("Creating shared SQS connection", extra={
                "use_pool": self._use_connection_pool,
                "endpoint": self._aws_endpoint_url
            })
            
            if self._use_connection_pool:
                self._sqs = SQSConnection.from_pool(
                    aws_profile=self._aws_profile,
                    aws_region=self._aws_region,
                    aws_end_point_url=self._aws_endpoint_url,
                )
            else:
                self._sqs = SQSConnection(
                    aws_profile=self._aws_profile,
                    aws_region=self._aws_region,
                    aws_end_point_url=self._aws_endpoint_url,
                )
            
            self._connection_stats["sqs_created"] = True
        
        return self._sqs
    
    def create_service(
        self,
        service_class: Type[T],
        request_context: RequestContext,
        **kwargs
    ) -> T:
        """
        Create service instance with injected connections and context.
        
        This is the primary method for creating services. It automatically
        injects the shared DynamoDB connection and table name, while ensuring
        the request context is passed fresh.
        
        Args:
            service_class: Service class to instantiate (must extend DatabaseService)
            request_context: Fresh request context for this invocation
            **kwargs: Additional service-specific parameters
        
        Returns:
            Service instance with injected dependencies
        
        Example:
            >>> factory = ServiceFactory()
            >>> context = SystemRequestContext(tenant_id="t1", user_id="u1")
            >>> user_service = factory.create_service(UserService, context)
            >>> result = user_service.get_by_id("user-123")
        
        Note:
            The request_context should NEVER be cached at module level.
            Always create it fresh per Lambda invocation to avoid cross-request
            contamination.
        """
        # Get table name from environment or kwargs
        table_name = kwargs.pop("table_name", None) or os.getenv("DYNAMODB_TABLE_NAME")
        
        if not table_name:
            raise ValueError(
                f"Table name is required for {service_class.__name__}. "
                "Provide via table_name parameter or DYNAMODB_TABLE_NAME environment variable."
            )
        
        logger.debug(f"Creating service: {service_class.__name__}", extra={
            "table_name": table_name,
            "tenant_id": request_context.tenant_id if hasattr(request_context, 'tenant_id') else None,
            "user_id": request_context.user_id if hasattr(request_context, 'user_id') else None,
        })
        
        # Create service with injected dependencies
        return service_class(
            dynamodb=self.dynamodb,
            table_name=table_name,
            request_context=request_context,
            **kwargs
        )
    
    def reset_connections(self):
        """
        Reset all cached connections.
        
        This clears all lazy-loaded connections, forcing them to be recreated
        on next access. Useful for testing scenarios where you need to reset
        state between tests.
        
        Warning:
            This should only be used in testing. In production Lambda functions,
            connections should persist across invocations for performance.
        
        Example:
            >>> factory = ServiceFactory()
            >>> # ... use factory ...
            >>> factory.reset_connections()  # Clear for next test
        """
        logger.debug("Resetting all connections")
        self._dynamodb = None
        self._s3 = None
        self._sqs = None
        self._connection_stats = {
            "dynamodb_created": False,
            "s3_created": False,
            "sqs_created": False,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about connection usage.
        
        Returns:
            Dict with connection creation stats and configuration
        
        Example:
            >>> factory = ServiceFactory()
            >>> service = factory.create_service(UserService, context)
            >>> stats = factory.get_stats()
            >>> print(stats)
            {
                'use_connection_pool': True,
                'connections_created': {'dynamodb': True, 's3': False, 'sqs': False},
                'total_connections': 1
            }
        """
        return {
            "use_connection_pool": self._use_connection_pool,
            "connections_created": self._connection_stats.copy(),
            "total_connections": sum(1 for v in self._connection_stats.values() if v),
            "aws_profile": self._aws_profile,
            "aws_region": self._aws_region,
            "aws_endpoint_url": self._aws_endpoint_url,
        }
