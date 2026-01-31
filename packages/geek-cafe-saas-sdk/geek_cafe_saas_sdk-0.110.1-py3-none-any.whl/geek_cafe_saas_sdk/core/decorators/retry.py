"""Retry decorators for handling transient failures like DynamoDB throttling."""

import time
import functools
from typing import Callable, TypeVar, Any, Dict, Optional, Tuple
from aws_lambda_powertools import Logger

logger = Logger()

T = TypeVar('T')


class RetryDiagnostics:
    """
    Diagnostics information about retry attempts.
    
    Tracks retry behavior for observability and debugging.
    """
    
    def __init__(self):
        self.retry_attempted: bool = False
        self.retry_count: int = 0
        self.total_delay: float = 0.0
        self.throttling_errors: list = []
        self.final_attempt: int = 0
        self.succeeded_on_retry: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for ServiceResult.diagnostics."""
        return {
            "retry_attempted": self.retry_attempted,
            "retry_count": self.retry_count,
            "total_delay_seconds": round(self.total_delay, 2),
            "throttling_errors": self.throttling_errors,
            "final_attempt": self.final_attempt,
            "succeeded_on_retry": self.succeeded_on_retry,
        }


def with_throttling_retry(
    max_retries: int = 5,
    base_delay: float = 0.5,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    track_diagnostics: bool = False
):
    """
    Decorator to retry operations that fail due to DynamoDB throttling.
    
    Uses exponential backoff with configurable parameters. Retries only
    throttling-related exceptions, fails fast on other errors.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 5)
        base_delay: Initial delay in seconds (default: 0.5)
        max_delay: Maximum delay between retries in seconds (default: 10.0)
        exponential_base: Base for exponential backoff calculation (default: 2.0)
        track_diagnostics: If True, return (result, diagnostics) tuple (default: False)
    
    Returns:
        If track_diagnostics=False: Returns function result directly
        If track_diagnostics=True: Returns (result, RetryDiagnostics) tuple
    
    Example:
        @with_throttling_retry(max_retries=3, base_delay=1.0)
        def save_to_db(item):
            return db.save(item)
        
        # With diagnostics tracking
        @with_throttling_retry(max_retries=3, track_diagnostics=True)
        def save_with_tracking(item):
            return db.save(item)
        
        result, diagnostics = save_with_tracking(item)
        print(f"Retries: {diagnostics.retry_count}")
    
    Retry Schedule (default):
        - Attempt 1: immediate
        - Attempt 2: wait 0.5s
        - Attempt 3: wait 1.0s
        - Attempt 4: wait 2.0s
        - Attempt 5: wait 4.0s
        - Attempt 6: wait 8.0s (final)
    """
    def decorator(func: Callable[..., T]) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            diagnostics = RetryDiagnostics() if track_diagnostics else None
            last_exception = None
            
            for attempt in range(max_retries + 1):  # +1 for initial attempt
                try:
                    result = func(*args, **kwargs)
                    
                    # Track success
                    if diagnostics:
                        diagnostics.final_attempt = attempt + 1
                        diagnostics.succeeded_on_retry = attempt > 0
                    
                    # Return based on tracking mode
                    if track_diagnostics:
                        return result, diagnostics
                    return result
                
                except Exception as e:
                    # Check if this is a throttling exception
                    error_str = str(e)
                    is_throttled = (
                        "ThrottlingException" in error_str or
                        "ProvisionedThroughputExceededException" in error_str or
                        "RequestLimitExceeded" in error_str
                    )
                    
                    if not is_throttled:
                        # Not a throttling error, fail immediately
                        raise
                    
                    last_exception = e
                    
                    # Track throttling error
                    if diagnostics:
                        diagnostics.retry_attempted = True
                        diagnostics.throttling_errors.append({
                            "attempt": attempt + 1,
                            "error": error_str[:200]  # Truncate long errors
                        })
                    
                    if attempt < max_retries:
                        # Calculate delay with exponential backoff
                        delay = min(
                            base_delay * (exponential_base ** attempt),
                            max_delay
                        )
                        
                        # Track delay
                        if diagnostics:
                            diagnostics.retry_count += 1
                            diagnostics.total_delay += delay
                        
                        logger.warning(
                            f"Throttling detected in {func.__name__}, "
                            f"retry {attempt + 1}/{max_retries} after {delay:.2f}s: {error_str}"
                        )
                        time.sleep(delay)
                    else:
                        # Max retries reached
                        if diagnostics:
                            diagnostics.final_attempt = attempt + 1
                        
                        logger.error(
                            f"Max retries ({max_retries}) reached for {func.__name__}: {error_str}"
                        )
                        raise
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


def is_throttling_error(exception: Exception) -> bool:
    """
    Check if an exception is a DynamoDB throttling error.
    
    Args:
        exception: The exception to check
    
    Returns:
        True if the exception is throttling-related, False otherwise
    """
    error_str = str(exception)
    return (
        "ThrottlingException" in error_str or
        "ProvisionedThroughputExceededException" in error_str or
        "RequestLimitExceeded" in error_str
    )
