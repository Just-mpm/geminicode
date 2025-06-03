"""
Enhanced error handling utilities.
"""

import traceback
import logging
import functools
from typing import Any, Callable, Dict, Optional, Type, Union
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .error_humanizer import humanize_error


@dataclass
class ErrorContext:
    """Context information for error handling."""
    module: str
    function: str
    operation: str
    user_input: Optional[str] = None
    file_path: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None


class ErrorSeverity:
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GeminiCodeException(Exception):
    """Base exception for Gemini Code."""
    
    def __init__(self, message: str, severity: str = ErrorSeverity.MEDIUM, 
                 context: Optional[ErrorContext] = None, cause: Optional[Exception] = None):
        super().__init__(message)
        self.severity = severity
        self.context = context
        self.cause = cause
        self.timestamp = datetime.now()


class ValidationError(GeminiCodeException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(message, ErrorSeverity.MEDIUM)
        self.field = field
        self.value = value


class ConfigurationError(GeminiCodeException):
    """Exception for configuration errors."""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(message, ErrorSeverity.HIGH)
        self.config_key = config_key


class APIError(GeminiCodeException):
    """Exception for API-related errors."""
    
    def __init__(self, message: str, api_name: str = None, status_code: int = None):
        super().__init__(message, ErrorSeverity.HIGH)
        self.api_name = api_name
        self.status_code = status_code


class FileOperationError(GeminiCodeException):
    """Exception for file operation errors."""
    
    def __init__(self, message: str, file_path: str = None, operation: str = None):
        super().__init__(message, ErrorSeverity.MEDIUM)
        self.file_path = file_path
        self.operation = operation


class ErrorHandler:
    """Enhanced error handler with logging and recovery."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_counts = {}
        self.recovery_strategies = {}
        
    def register_recovery_strategy(self, exception_type: Type[Exception], 
                                  strategy: Callable[[Exception], Any]):
        """Register a recovery strategy for specific exception type."""
        self.recovery_strategies[exception_type] = strategy
    
    def handle_error(self, error: Exception, context: Optional[ErrorContext] = None,
                    user_friendly: bool = True, attempt_recovery: bool = True) -> Dict[str, Any]:
        """Handle error with logging, context, and optional recovery."""
        
        # Track error frequency
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Create error info
        error_info = {
            "type": error_type,
            "message": str(error),
            "timestamp": datetime.now().isoformat(),
            "context": context.__dict__ if context else None,
            "traceback": traceback.format_exc(),
            "frequency": self.error_counts[error_type]
        }
        
        # Log error
        self._log_error(error, error_info, context)
        
        # Attempt recovery if enabled
        recovery_result = None
        if attempt_recovery:
            recovery_result = self._attempt_recovery(error)
            if recovery_result:
                error_info["recovery_attempted"] = True
                error_info["recovery_result"] = recovery_result
        
        # Generate user-friendly message
        if user_friendly:
            if context:
                error_info["user_message"] = humanize_error(error, context.operation)
            else:
                error_info["user_message"] = humanize_error(error)
        
        return error_info
    
    def _log_error(self, error: Exception, error_info: Dict[str, Any], 
                  context: Optional[ErrorContext]):
        """Log error with appropriate level."""
        severity = getattr(error, 'severity', ErrorSeverity.MEDIUM)
        
        log_message = f"Error in {context.module if context else 'unknown'}: {str(error)}"
        
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, extra=error_info)
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(log_message, extra=error_info)
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message, extra=error_info)
        else:
            self.logger.info(log_message, extra=error_info)
    
    def _attempt_recovery(self, error: Exception) -> Optional[Any]:
        """Attempt to recover from error using registered strategies."""
        error_type = type(error)
        
        # Check for exact match first
        if error_type in self.recovery_strategies:
            try:
                return self.recovery_strategies[error_type](error)
            except Exception as recovery_error:
                self.logger.warning(f"Recovery strategy failed: {recovery_error}")
        
        # Check for parent class matches
        for registered_type, strategy in self.recovery_strategies.items():
            if isinstance(error, registered_type):
                try:
                    return strategy(error)
                except Exception as recovery_error:
                    self.logger.warning(f"Recovery strategy failed: {recovery_error}")
        
        return None
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics."""
        total_errors = sum(self.error_counts.values())
        
        return {
            "total_errors": total_errors,
            "error_types": len(self.error_counts),
            "most_common": max(self.error_counts.items(), key=lambda x: x[1]) if self.error_counts else None,
            "error_breakdown": self.error_counts.copy()
        }


def with_error_handling(operation: str = None, severity: str = ErrorSeverity.MEDIUM,
                       user_friendly: bool = True, attempt_recovery: bool = True):
    """Decorator for automatic error handling."""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Create context
                context = ErrorContext(
                    module=func.__module__,
                    function=func.__name__,
                    operation=operation or f"executing {func.__name__}"
                )
                
                # Handle error
                error_handler = ErrorHandler()
                error_info = error_handler.handle_error(
                    e, context, user_friendly, attempt_recovery
                )
                
                # Re-raise as GeminiCodeException with context
                raise GeminiCodeException(
                    error_info.get("user_message", str(e)),
                    severity=severity,
                    context=context,
                    cause=e
                )
        
        return wrapper
    
    return decorator


def with_async_error_handling(operation: str = None, severity: str = ErrorSeverity.MEDIUM,
                             user_friendly: bool = True, attempt_recovery: bool = True):
    """Decorator for automatic async error handling."""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Create context
                context = ErrorContext(
                    module=func.__module__,
                    function=func.__name__,
                    operation=operation or f"executing {func.__name__}"
                )
                
                # Handle error
                error_handler = ErrorHandler()
                error_info = error_handler.handle_error(
                    e, context, user_friendly, attempt_recovery
                )
                
                # Re-raise as GeminiCodeException with context
                raise GeminiCodeException(
                    error_info.get("user_message", str(e)),
                    severity=severity,
                    context=context,
                    cause=e
                )
        
        return wrapper
    
    return decorator


def validate_input(value: Any, validators: Dict[str, Callable[[Any], bool]], 
                  field_name: str = "input") -> None:
    """Validate input with custom validators."""
    
    for validator_name, validator_func in validators.items():
        try:
            if not validator_func(value):
                raise ValidationError(
                    f"Validation failed for {field_name}: {validator_name}",
                    field=field_name,
                    value=value
                )
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(
                f"Validation error for {field_name}: {str(e)}",
                field=field_name,
                value=value
            )


def validate_file_path(file_path: Union[str, Path], must_exist: bool = True,
                      must_be_file: bool = True) -> Path:
    """Validate file path."""
    
    try:
        path = Path(file_path)
        
        if must_exist and not path.exists():
            raise FileOperationError(f"File does not exist: {path}", str(path), "validation")
        
        if must_be_file and path.exists() and not path.is_file():
            raise FileOperationError(f"Path is not a file: {path}", str(path), "validation")
        
        return path
        
    except Exception as e:
        if isinstance(e, FileOperationError):
            raise
        raise FileOperationError(f"Invalid file path: {str(e)}", str(file_path), "validation")


def validate_api_response(response: Any, expected_fields: list = None) -> None:
    """Validate API response."""
    
    if response is None:
        raise APIError("API response is None")
    
    if expected_fields:
        if not isinstance(response, dict):
            raise APIError("API response is not a dictionary")
        
        missing_fields = [field for field in expected_fields if field not in response]
        if missing_fields:
            raise APIError(f"API response missing fields: {missing_fields}")


# Common recovery strategies
def retry_on_network_error(error: Exception) -> Optional[str]:
    """Recovery strategy for network errors."""
    if "network" in str(error).lower() or "connection" in str(error).lower():
        return "network_retry_suggested"
    return None


def fallback_on_api_error(error: Exception) -> Optional[str]:
    """Recovery strategy for API errors."""
    if isinstance(error, APIError) or "api" in str(error).lower():
        return "api_fallback_mode"
    return None


# Global error handler instance
global_error_handler = ErrorHandler()

# Register default recovery strategies
global_error_handler.register_recovery_strategy(ConnectionError, retry_on_network_error)
global_error_handler.register_recovery_strategy(APIError, fallback_on_api_error)