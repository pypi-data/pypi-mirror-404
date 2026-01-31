"""
Throttle configuration service for managing execution rate limits.

Provides CRUD operations for throttle configurations at tenant and user levels.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import uuid
from typing import Optional, Dict, Any, List

from aws_lambda_powertools import Logger
from boto3_assist.dynamodb.dynamodb import DynamoDB

from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
from geek_cafe_saas_sdk.core.request_context import RequestContext
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.core.service_errors import NotFoundError

from ..models.throttle_config import ThrottleConfig

logger = Logger()


class ThrottleConfigService(DatabaseService[ThrottleConfig]):
    """
    Service for managing throttle configurations.
    
    Provides CRUD operations and lookup methods for throttle configs
    at both tenant and user levels.
    """

    def __init__(
        self,
        *,
        dynamodb: Optional[DynamoDB] = None,
        table_name: Optional[str] = None,
        request_context: Optional[RequestContext] = None,        
        **kwargs
    ):
        super().__init__(
            dynamodb=dynamodb,
            table_name=table_name,
            request_context=request_context,
            **kwargs
        )

    # =========================================================================
    # Core CRUD Operations
    # =========================================================================

    @service_method("create_config")
    def create(
        self,
        config_type: str = "execution",
        owner_id: Optional[str] = None,
        **kwargs
    ) -> ServiceResult[ThrottleConfig]:
        """
        Create a new throttle configuration.
        
        Args:
            config_type: Type of execution this config applies to
            owner_id: User ID for user-specific override, None for tenant default
            **kwargs: Additional config fields to set
            
        Returns:
            ServiceResult with created ThrottleConfig
        """
        config = ThrottleConfig()
        config.map(kwargs)
        # set primary values that we control
        config.id = str(uuid.uuid4())
        config.tenant_id = self.request_context.authenticated_tenant_id
        config.config_type = config_type
        config.owner_id = owner_id
        config.is_active = True
                        
        config.prep_for_save()
        return self._save_model(config)

    @service_method("get_config")
    def get(self, config_id: str) -> ServiceResult[ThrottleConfig]:
        """Get throttle config by ID."""
        config = self._get_by_id(config_id, ThrottleConfig)
        if not config:
            raise NotFoundError(f"ThrottleConfig {config_id} not found")
        return ServiceResult.success_result(config)

    @service_method("get_by_id")
    def get_by_id(self, **kwargs) -> ServiceResult[ThrottleConfig]:
        """Get throttle config by ID (abstract method implementation)."""
        config_id = kwargs.get("config_id") or kwargs.get("id")
        return self.get(config_id)

    @service_method("update_config")
    def update(self, **kwargs) -> ServiceResult[ThrottleConfig]:
        """
        Update throttle configuration.
        
        Args:
            config_id or id: ID of the config to update
            **kwargs: Fields to update
            
        Returns:
            ServiceResult with updated ThrottleConfig
        """
        config_id = kwargs.get("config_id") or kwargs.get("id")
        config = self._get_by_id(config_id, ThrottleConfig)
        if not config:
            raise NotFoundError(f"ThrottleConfig {config_id} not found")
        
        temp_model = ThrottleConfig()
        temp_model.id = config_id
        old_config = self._fetch_model_raw(temp_model)
        
        # Update allowed fields
        updatable_fields = [
            "config_type", "is_active",
            "max_concurrent_per_user", "max_concurrent_per_tenant",
            "max_queued_per_user", "max_queued_per_tenant",
            "max_profiles_per_submission", "max_profiles_per_hour", "max_profiles_per_day",
            "min_submission_interval_seconds", "max_submissions_per_hour", "max_submissions_per_day",
            "throttle_delay_seconds", "max_throttle_queue_depth", "reject_when_throttle_full",
            "throttling_enabled", "profile_limit_enabled", "rate_limit_enabled",
        ]
        
        for field in updatable_fields:
            if field in kwargs:
                setattr(config, field, kwargs[field])
        
        config.prep_for_save()
        return self._save_model(config, old_model=old_config)

    @service_method("delete_config")
    def delete(self, **kwargs) -> ServiceResult[bool]:
        """Delete throttle configuration."""
        config_id = kwargs.get("config_id") or kwargs.get("id")
        config = self._get_by_id(config_id, ThrottleConfig)
        if not config:
            raise NotFoundError(f"ThrottleConfig {config_id} not found")
        return self._delete_model(config)

    # =========================================================================
    # Config Lookup Operations
    # =========================================================================

    @service_method("get_tenant_config")
    def get_tenant_config(
        self,
        config_type: str = "execution",
    ) -> ServiceResult[ThrottleConfig]:
        """
        Get tenant's default throttle configuration.
        
        Args:
            config_type: Type of execution
            
        Returns:
            ServiceResult with ThrottleConfig or None
        """
        tenant_id = self.request_context.authenticated_tenant_id
        
        query_model = ThrottleConfig()
        query_model.tenant_id = tenant_id
        query_model.owner_id = None  # Will use "__default__" in GSI
        query_model.config_type = config_type
        
        result = self._query_by_index(query_model, "gsi2", limit=1)
        if result.success and result.data:
            # Filter for active configs
            for config in result.data:
                if config.is_active and config.owner_id is None:
                    return ServiceResult.success_result(config)
        return ServiceResult.success_result(None)

    @service_method("get_user_config")
    def get_user_config(
        self,
        user_id: str,
        config_type: str = "execution",
    ) -> ServiceResult[ThrottleConfig]:
        """
        Get user-specific throttle configuration override.
        
        Args:
            user_id: User ID
            config_type: Type of execution
            
        Returns:
            ServiceResult with ThrottleConfig or None
        """
        tenant_id = self.request_context.authenticated_tenant_id
        
        query_model = ThrottleConfig()
        query_model.tenant_id = tenant_id
        query_model.owner_id = user_id
        query_model.config_type = config_type
        
        result = self._query_by_index(query_model, "gsi2", limit=1)
        if result.success and result.data:
            # Filter for active configs
            for config in result.data:
                if config.is_active:
                    return ServiceResult.success_result(config)
        return ServiceResult.success_result(None)

    @service_method("get_effective_config")
    def get_effective_config(
        self,
        user_id: str,
        config_type: str = "execution",
    ) -> ServiceResult[ThrottleConfig]:
        """
        Get the effective throttle configuration for a user.
        
        Checks for user-specific override first, then falls back to tenant default,
        then falls back to system defaults.
        
        Args:
            user_id: User ID
            config_type: Type of execution
            
        Returns:
            ServiceResult with effective ThrottleConfig (never None)
        """
        # Try user-specific override first
        user_result = self.get_user_config(user_id, config_type)
        if user_result.success and user_result.data:
            return user_result
        
        # Fall back to tenant default
        tenant_result = self.get_tenant_config(config_type)
        if tenant_result.success and tenant_result.data:
            return tenant_result
        
        # Fall back to system defaults
        default_config = ThrottleConfig.create_default(
            tenant_id=self.request_context.authenticated_tenant_id,
            config_type=config_type
        )
        return ServiceResult.success_result(default_config)

    @service_method("get_or_create_tenant_config")
    def get_or_create_tenant_config(
        self,
        config_type: str = "execution",
    ) -> ServiceResult[ThrottleConfig]:
        """
        Get or create tenant's default throttle configuration.
        
        Args:
            config_type: Type of execution
            
        Returns:
            ServiceResult with ThrottleConfig
        """
        # Try to find existing
        result = self.get_tenant_config(config_type)
        if result.success and result.data:
            return result
        
        # Create new with defaults
        return self.create(config_type=config_type, owner_id=None)

    # =========================================================================
    # List Operations
    # =========================================================================

    @service_method("list_tenant_configs")
    def list_tenant_configs(
        self,
        limit: int = 50,
    ) -> ServiceResult[List[ThrottleConfig]]:
        """
        List all throttle configurations for the tenant.
        
        Args:
            limit: Maximum results
            
        Returns:
            ServiceResult with list of ThrottleConfigs
        """
        tenant_id = self.request_context.authenticated_tenant_id
        
        query_model = ThrottleConfig()
        query_model.tenant_id = tenant_id
        
        return self._query_by_index(query_model, "gsi1", limit=limit)
