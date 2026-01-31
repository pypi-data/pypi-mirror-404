import json
import threading
from pathlib import Path
from typing import Any, Dict, Optional
from aws_lambda_powertools import Logger as PowerToolsLogger
from geek_cafe_saas_sdk.utilities.environment_variables import (
    EnvironmentVariables,
)


LOG_LEVEL = EnvironmentVariables.get_logging_level()


class LoggingUtility:
    """
    Thread-safe singleton logger for centralized logging across all services.
    
    Features:
    - Singleton pattern ensures one logger instance across all services
    - Thread-safe initialization
    - Optional file logging for event-based testing
    - Supports all log levels (debug, info, warning, error, critical, exception)
    - Efficient file writing with buffering
    
    Usage:
        from geek_cafe_saas_sdk.utilities.logging_utility import Logger
        
        # Basic logging
        Logger.info("Processing started")
        Logger.error("Failed to process", extra={"error_code": "E001"})
        
        # Enable file logging for testing
        Logger.set_output_file("/tmp/test_logs.txt")
        Logger.info("This goes to CloudWatch AND file")
        
        # Disable file logging
        Logger.set_output_file(None)
    """
    
    _instance: Optional['LoggingUtility'] = None
    _lock = threading.Lock()
    
    def __new__(cls, service: Optional[str] = None):
        """Thread-safe singleton implementation."""
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, service: Optional[str] = None) -> None:
        """Initialize the logger (only runs once due to singleton)."""
        # Prevent re-initialization
        if self._initialized:
            return
            
        self.logger: PowerToolsLogger = PowerToolsLogger(service=service)
        self.logger.setLevel(LOG_LEVEL)
        self._output_file: Optional[str] = None
        self._file_lock = threading.Lock()
        self._initialized = True
    
    def set_output_file(self, file_path: Optional[str]) -> None:
        """
        Set the output file for logging (in addition to CloudWatch).
        
        Automatically creates the directory path if it doesn't exist.
        
        Args:
            file_path: Path to log file, or None to disable file logging
        
        Raises:
            ValueError: If file_path is invalid or cannot be created
        
        Example:
            Logger.set_output_file("/tmp/test_logs.txt")
            Logger.info("This goes to file and CloudWatch")
            Logger.set_output_file(None)  # Disable file logging
        """
        with self._file_lock:
            if file_path is None:
                self._output_file = None
                return
            
            try:
                # Convert to Path object and resolve
                log_path = Path(file_path).resolve()
                
                # Create parent directory if it doesn't exist
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Verify we can write to the location by touching the file
                log_path.touch(exist_ok=True)
                
                self._output_file = str(log_path)
            except Exception as e:
                error_msg = f"Failed to set output file '{file_path}': {str(e)}"
                self.logger.error(error_msg)
                raise ValueError(error_msg) from e
    
    def _write_to_file(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Write log message to file if file logging is enabled."""
        if not self._output_file:
            return
        
        try:
            with self._file_lock:
                if self._output_file:  # Double-check after acquiring lock
                    # Ensure directory exists (defensive check)
                    log_path = Path(self._output_file)
                    log_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(self._output_file, "a", buffering=8192) as f:
                        # Format: [LEVEL] message {extra}
                        log_line = f"[{level}] {message}"
                        if extra:
                            log_line += f" {json.dumps(extra)}"
                        f.write(log_line + "\n")
        except Exception as e:
            # Don't let file logging errors break the application
            self.logger.warning(f"Failed to write to log file: {str(e)}")
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, **kwargs)
        self._write_to_file("DEBUG", message, kwargs.get("extra"))
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, **kwargs)
        self._write_to_file("INFO", message, kwargs.get("extra"))
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, **kwargs)
        self._write_to_file("WARNING", message, kwargs.get("extra"))
    
    def warn(self, message: str, **kwargs) -> None:
        """Alias for warning()."""
        self.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.logger.error(message, **kwargs)
        self._write_to_file("ERROR", message, kwargs.get("extra"))
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(message, **kwargs)
        self._write_to_file("CRITICAL", message, kwargs.get("extra"))
    
    def exception(self, message: str, **kwargs) -> None:
        """Log exception with traceback."""
        self.logger.exception(message, **kwargs)
        self._write_to_file("EXCEPTION", message, kwargs.get("extra"))
    
    def setLevel(self, level: int) -> None:
        """Set the logging level."""
        self.logger.setLevel(level)

    @staticmethod
    def get_logger(
        service: str | None = None, level: str | None | int = None
    ) -> PowerToolsLogger:
        
        level = level or LOG_LEVEL
        logger = PowerToolsLogger(service=service)
        logger.setLevel(level)
        return logger

    @staticmethod
    def build_message(
        source: str,
        action: str,
        message: str | None = None,
        metric_filter: str | None = None,
    ) -> dict:
        """
        Build a formatted message for logging
        Args:
            source (str): _description_
            action (str): _description_
            message (str, optional): _description_. Defaults to None.
            metric_filter (str, optional): _description_. Defaults to None.

        Returns:
            dict: _description_
        """
        response = {
            "source": source,
            "action": action,
            "details": message,
            "metric_filter": metric_filter,
        }
        return response
    
    @staticmethod
    def sanitize_event_for_logging(event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize a Lambda event dictionary by masking sensitive fields.
        
        This removes or masks sensitive information like:
        - Authorization headers
        - API keys
        - Passwords
        - Tokens
        - SSNs, credit cards, etc.
        
        Args:
            event: The Lambda event dictionary to sanitize
            
        Returns:
            A sanitized copy of the event safe for logging
        """
        if not isinstance(event, dict):
            return event
        
        # Fields that should be completely removed
        REMOVE_FIELDS = {
            'password', 'passwd', 'pwd',
            'secret', 'api_key', 'apikey',
            'token', 'access_token', 'refresh_token',
            'private_key', 'privatekey',
            'ssn', 'credit_card', 'creditcard',
            'cvv', 'pin'
        }
        
        # Fields that should be masked (show first few chars)
        MASK_FIELDS = {
            'authorization', 'x_api_key',
            'cookie', 'session'
        }
        
        def sanitize_value(key: str, value: Any) -> Any:
            """Recursively sanitize values."""
            try:
                key_lower = key.lower().replace('-', '_').replace(' ', '_')
                
                # Remove sensitive fields entirely (exact match)
                if key_lower in REMOVE_FIELDS:
                    return '[REDACTED]'
                
                # Mask partially visible fields (exact match)
                if key_lower in MASK_FIELDS:
                    if isinstance(value, str) and len(value) > 20:
                        return f"{value[:4]}...{value[-4:]}"
                    return '[MASKED]'
                
                # Recursively handle nested structures
                if isinstance(value, dict):
                    return {k: sanitize_value(k, v) for k, v in value.items()}
                elif isinstance(value, list):
                    return [sanitize_value(key, item) if isinstance(item, dict) else item 
                            for item in value]
                
                return value
            except Exception:
                # If we can't safely process the value, redact it
                return '[SANITIZATION_ERROR]'
        
        # Create a deep copy and sanitize
        try:
            sanitized = {k: sanitize_value(k, v) for k, v in event.items()}
            # Validate that the result is JSON-serializable
            import json
            json.dumps(sanitized)
            return sanitized
        except Exception as e:
            # If sanitization fails, return safe fallback
            return {"error": "Failed to sanitize event"}


class LogLevels:
    def __init__(self) -> None:
        pass

    CRITICAL = 50
    FATAL = CRITICAL
    ERROR = 40
    WARNING = 30
    WARN = WARNING
    INFO = 20
    DEBUG = 10
    NOTSET = 0


# Module-level singleton instance for easy import
# Usage: from geek_cafe_saas_sdk.utilities.logging_utility import Logger
Logger = LoggingUtility()
