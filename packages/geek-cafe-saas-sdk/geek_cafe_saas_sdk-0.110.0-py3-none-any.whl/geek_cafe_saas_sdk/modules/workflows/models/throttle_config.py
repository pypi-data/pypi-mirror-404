"""
Throttle configuration model for execution rate limiting.

Stores configurable guardrails for controlling execution submission rates
at both user and tenant levels.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any, Optional
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from geek_cafe_saas_sdk.core.models.base_tenant_model import BaseTenantModel


class ThrottleConfig(BaseTenantModel):
    """
    Throttle configuration for execution rate limiting.
    
    Defines limits for concurrent executions, queue depth, submission rates,
    and resource consumption. Can be configured per tenant with optional
    per-user overrides.
    
    Access Patterns (DynamoDB Keys):
    - pk: throttle_config#{id}
    - sk: metadata
    - gsi1: By tenant + config_type (for looking up active config)
    - gsi2: By tenant + owner (for user-specific overrides)
    """

    # Default configuration values
    DEFAULT_MAX_CONCURRENT_PER_USER = 5
    DEFAULT_MAX_CONCURRENT_PER_TENANT = 50
    DEFAULT_MAX_QUEUED_PER_USER = 10
    DEFAULT_MAX_QUEUED_PER_TENANT = 100
    DEFAULT_MAX_PROFILES_PER_SUBMISSION = 10000
    DEFAULT_MIN_SUBMISSION_INTERVAL_SECONDS = 5
    DEFAULT_MAX_SUBMISSIONS_PER_HOUR = 100
    DEFAULT_MAX_SUBMISSIONS_PER_DAY = 500

    def __init__(self):
        super().__init__()
        
        # Identity
        self._config_type: str = "execution"  # e.g., "acme-workflow", "validation"
        self._owner_id: str | None = None  # None = tenant default, set = user override
        self._is_active: bool = True  # Whether this config is active
        
        # Concurrency limits
        self._max_concurrent_per_user: int = self.DEFAULT_MAX_CONCURRENT_PER_USER
        self._max_concurrent_per_tenant: int = self.DEFAULT_MAX_CONCURRENT_PER_TENANT
        
        # Queue depth limits
        self._max_queued_per_user: int = self.DEFAULT_MAX_QUEUED_PER_USER
        self._max_queued_per_tenant: int = self.DEFAULT_MAX_QUEUED_PER_TENANT
        
        # Resource limits
        self._max_profiles_per_submission: int = self.DEFAULT_MAX_PROFILES_PER_SUBMISSION
        self._max_profiles_per_hour: int | None = None  # None = unlimited
        self._max_profiles_per_day: int | None = None   # None = unlimited
        
        # Rate limiting
        self._min_submission_interval_seconds: int = self.DEFAULT_MIN_SUBMISSION_INTERVAL_SECONDS
        self._max_submissions_per_hour: int = self.DEFAULT_MAX_SUBMISSIONS_PER_HOUR
        self._max_submissions_per_day: int = self.DEFAULT_MAX_SUBMISSIONS_PER_DAY
        
        # Throttle behavior
        self._throttle_delay_seconds: int = 60  # Delay for throttled requests
        self._max_throttle_queue_depth: int = 50  # Max items in throttle queue
        self._reject_when_throttle_full: bool = True  # Reject if throttle queue full
        
        # Feature flags
        self._throttling_enabled: bool = True
        self._profile_limit_enabled: bool = True
        self._rate_limit_enabled: bool = True
        
        # Flexible configuration storage
        self._config: Dict[str, Any] = {}
        
        # Model metadata
        self.model_name = "throttle_config"
        self.model_name_plural = "throttle_configs"
        
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()

    def _setup_indexes(self):
        """Setup DynamoDB indexes for throttle config queries."""
        
        # Primary index: Config by ID
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("throttle_config", self.id)
        )
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: "throttle_config"
        self.indexes.add_primary(primary)
        
        # GSI1: By tenant + config_type (for looking up active config)
        self._setup_gsi1()
        
        # GSI2: By tenant + owner (for user-specific overrides)
        self._setup_gsi2()

    def _setup_gsi1(self):
        """GSI1: Config by tenant + config_type."""
        gsi = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = "gsi1_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id)
        )
        gsi.sort_key.attribute_name = "gsi1_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("model", "throttle_config"),
            ("config_type", self._config_type)
        )
        self.indexes.add_secondary(gsi)

    def _setup_gsi2(self):
        """GSI2: Config by tenant + owner (for user overrides)."""
        gsi = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = "gsi2_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("owner", self._owner_id)
        )
        gsi.sort_key.attribute_name = "gsi2_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("model", "throttle_config"),
            ("config_type", self._config_type)
        )
        self.indexes.add_secondary(gsi)

    # Properties - Identity
    @property
    def config_type(self) -> str:
        """Type of execution this config applies to."""
        return self._config_type

    @config_type.setter
    def config_type(self, value: str):
        self._config_type = value

    @property
    def owner_id(self) -> str | None:
        """Owner user ID for user-specific override, None for tenant default."""
        return self._owner_id

    @owner_id.setter
    def owner_id(self, value: str | None):
        self._owner_id = value

    @property
    def is_active(self) -> bool:
        """Whether this configuration is active."""
        return self._is_active

    @is_active.setter
    def is_active(self, value: bool):
        self._is_active = bool(value)

    # Properties - Concurrency limits
    @property
    def max_concurrent_per_user(self) -> int:
        """Maximum concurrent executions per user."""
        return self._max_concurrent_per_user

    @max_concurrent_per_user.setter
    def max_concurrent_per_user(self, value: int):
        self._max_concurrent_per_user = int(value) if value else self.DEFAULT_MAX_CONCURRENT_PER_USER

    @property
    def max_concurrent_per_tenant(self) -> int:
        """Maximum concurrent executions per tenant."""
        return self._max_concurrent_per_tenant

    @max_concurrent_per_tenant.setter
    def max_concurrent_per_tenant(self, value: int):
        self._max_concurrent_per_tenant = int(value) if value else self.DEFAULT_MAX_CONCURRENT_PER_TENANT

    # Properties - Queue depth limits
    @property
    def max_queued_per_user(self) -> int:
        """Maximum queued executions per user."""
        return self._max_queued_per_user

    @max_queued_per_user.setter
    def max_queued_per_user(self, value: int):
        self._max_queued_per_user = int(value) if value else self.DEFAULT_MAX_QUEUED_PER_USER

    @property
    def max_queued_per_tenant(self) -> int:
        """Maximum queued executions per tenant."""
        return self._max_queued_per_tenant

    @max_queued_per_tenant.setter
    def max_queued_per_tenant(self, value: int):
        self._max_queued_per_tenant = int(value) if value else self.DEFAULT_MAX_QUEUED_PER_TENANT

    # Properties - Resource limits
    @property
    def max_profiles_per_submission(self) -> int:
        """Maximum profiles allowed per single submission."""
        return self._max_profiles_per_submission

    @max_profiles_per_submission.setter
    def max_profiles_per_submission(self, value: int):
        self._max_profiles_per_submission = int(value) if value else self.DEFAULT_MAX_PROFILES_PER_SUBMISSION

    @property
    def max_profiles_per_hour(self) -> int | None:
        """Maximum profiles per hour (None = unlimited)."""
        return self._max_profiles_per_hour

    @max_profiles_per_hour.setter
    def max_profiles_per_hour(self, value: int | None):
        self._max_profiles_per_hour = int(value) if value else None

    @property
    def max_profiles_per_day(self) -> int | None:
        """Maximum profiles per day (None = unlimited)."""
        return self._max_profiles_per_day

    @max_profiles_per_day.setter
    def max_profiles_per_day(self, value: int | None):
        self._max_profiles_per_day = int(value) if value else None

    # Properties - Rate limiting
    @property
    def min_submission_interval_seconds(self) -> int:
        """Minimum seconds between submissions."""
        return self._min_submission_interval_seconds

    @min_submission_interval_seconds.setter
    def min_submission_interval_seconds(self, value: int):
        self._min_submission_interval_seconds = int(value) if value else self.DEFAULT_MIN_SUBMISSION_INTERVAL_SECONDS

    @property
    def max_submissions_per_hour(self) -> int:
        """Maximum submissions per hour."""
        return self._max_submissions_per_hour

    @max_submissions_per_hour.setter
    def max_submissions_per_hour(self, value: int):
        self._max_submissions_per_hour = int(value) if value else self.DEFAULT_MAX_SUBMISSIONS_PER_HOUR

    @property
    def max_submissions_per_day(self) -> int:
        """Maximum submissions per day."""
        return self._max_submissions_per_day

    @max_submissions_per_day.setter
    def max_submissions_per_day(self, value: int):
        self._max_submissions_per_day = int(value) if value else self.DEFAULT_MAX_SUBMISSIONS_PER_DAY

    # Properties - Throttle behavior
    @property
    def throttle_delay_seconds(self) -> int:
        """Delay in seconds for throttled requests."""
        return self._throttle_delay_seconds

    @throttle_delay_seconds.setter
    def throttle_delay_seconds(self, value: int):
        self._throttle_delay_seconds = int(value) if value else 60

    @property
    def max_throttle_queue_depth(self) -> int:
        """Maximum items allowed in throttle queue."""
        return self._max_throttle_queue_depth

    @max_throttle_queue_depth.setter
    def max_throttle_queue_depth(self, value: int):
        self._max_throttle_queue_depth = int(value) if value else 50

    @property
    def reject_when_throttle_full(self) -> bool:
        """Whether to reject requests when throttle queue is full."""
        return self._reject_when_throttle_full

    @reject_when_throttle_full.setter
    def reject_when_throttle_full(self, value: bool):
        self._reject_when_throttle_full = bool(value)

    # Properties - Feature flags
    @property
    def throttling_enabled(self) -> bool:
        """Whether throttling is enabled."""
        return self._throttling_enabled

    @throttling_enabled.setter
    def throttling_enabled(self, value: bool):
        self._throttling_enabled = bool(value)

    @property
    def profile_limit_enabled(self) -> bool:
        """Whether profile limits are enforced."""
        return self._profile_limit_enabled

    @profile_limit_enabled.setter
    def profile_limit_enabled(self, value: bool):
        self._profile_limit_enabled = bool(value)

    @property
    def rate_limit_enabled(self) -> bool:
        """Whether rate limiting is enabled."""
        return self._rate_limit_enabled

    @rate_limit_enabled.setter
    def rate_limit_enabled(self, value: bool):
        self._rate_limit_enabled = bool(value)

    # Properties - Flexible config
    @property
    def config(self) -> Dict[str, Any]:
        """Additional flexible configuration storage."""
        return self._config

    @config.setter
    def config(self, value: Dict[str, Any]):
        self._config = value if value is not None else {}

    # Computed properties
    @property
    def is_user_override(self) -> bool:
        """Check if this is a user-specific override."""
        return self._owner_id is not None

    # Helper methods
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a specific config value."""
        return self._config.get(key, default)

    def set_config_value(self, key: str, value: Any) -> None:
        """Set a specific config value."""
        self._config[key] = value

    @classmethod
    def create_default(cls, tenant_id: str, config_type: str = "execution") -> "ThrottleConfig":
        """Create a default throttle config for a tenant."""
        config = cls()
        config.tenant_id = tenant_id
        config.config_type = config_type
        config.is_active = True
        return config
