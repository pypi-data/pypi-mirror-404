"""Retry configuration for database operations with throttling protection."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RetryConfig:
    """
    Configuration for retry behavior on database operations.
    
    Controls automatic retry logic for throttling exceptions with
    exponential backoff.
    
    Attributes:
        enabled: Whether retry logic is enabled (default: True)
        max_retries: Maximum number of retry attempts (default: 5)
        base_delay: Initial delay in seconds before first retry (default: 0.5)
        max_delay: Maximum delay between retries in seconds (default: 10.0)
        exponential_base: Base for exponential backoff calculation (default: 2.0)
        track_diagnostics: Whether to track retry attempts in ServiceResult.diagnostics (default: True)
    
    Example:
        # Default retry behavior (enabled with 5 retries)
        config = RetryConfig()
        
        # Disable retry
        config = RetryConfig(enabled=False)
        
        # Custom retry settings
        config = RetryConfig(
            max_retries=3,
            base_delay=1.0,
            exponential_base=3.0
        )
        
        # Aggressive retry for critical operations
        config = RetryConfig(
            max_retries=10,
            base_delay=0.1,
            max_delay=30.0
        )
    
    Retry Schedule (default settings):
        - Attempt 1: immediate
        - Attempt 2: wait 0.5s
        - Attempt 3: wait 1.0s
        - Attempt 4: wait 2.0s
        - Attempt 5: wait 4.0s
        - Attempt 6: wait 8.0s (final)
    """
    
    enabled: bool = True
    max_retries: int = 5
    base_delay: float = 0.5
    max_delay: float = 10.0
    exponential_base: float = 2.0
    track_diagnostics: bool = True
    
    def __post_init__(self):
        """Validate configuration values."""
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if self.base_delay < 0:
            raise ValueError("base_delay must be >= 0")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if self.exponential_base < 1:
            raise ValueError("exponential_base must be >= 1")
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given retry attempt.
        
        Args:
            attempt: The retry attempt number (0-indexed)
        
        Returns:
            Delay in seconds, capped at max_delay
        """
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)
    
    @classmethod
    def disabled(cls) -> "RetryConfig":
        """Create a RetryConfig with retry disabled."""
        return cls(enabled=False, max_retries=0)
    
    @classmethod
    def aggressive(cls) -> "RetryConfig":
        """
        Create a RetryConfig with aggressive retry settings.
        
        Useful for critical operations that must succeed.
        - 10 retry attempts
        - Faster initial retry (0.1s)
        - Longer max delay (30s)
        """
        return cls(
            max_retries=10,
            base_delay=0.1,
            max_delay=30.0
        )
    
    @classmethod
    def conservative(cls) -> "RetryConfig":
        """
        Create a RetryConfig with conservative retry settings.
        
        Useful for non-critical operations or when you want to fail fast.
        - 3 retry attempts
        - Slower initial retry (1.0s)
        - Standard max delay (10s)
        """
        return cls(
            max_retries=3,
            base_delay=1.0,
            max_delay=10.0
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "enabled": self.enabled,
            "max_retries": self.max_retries,
            "base_delay": self.base_delay,
            "max_delay": self.max_delay,
            "exponential_base": self.exponential_base,
            "track_diagnostics": self.track_diagnostics,
        }


# Default retry configuration
DEFAULT_RETRY_CONFIG = RetryConfig()
