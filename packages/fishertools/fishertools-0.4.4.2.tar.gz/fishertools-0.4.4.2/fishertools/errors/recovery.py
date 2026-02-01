"""
Error recovery manager for graceful degradation and error handling.
"""

import logging
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
from dataclasses import dataclass
from .exceptions import FishertoolsError


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types."""
    RETRY = "retry"
    FALLBACK = "fallback"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    FAIL_FAST = "fail_fast"
    IGNORE = "ignore"


@dataclass
class ErrorContext:
    """Context information for an error."""
    component: str
    operation: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    metadata: Dict[str, Any]


@dataclass
class RecoveryAction:
    """Action to take for error recovery."""
    strategy: RecoveryStrategy
    fallback_function: Optional[Callable] = None
    retry_count: int = 0
    max_retries: int = 3
    message: str = ""
    should_log: bool = True


class ErrorRecoveryManager:
    """
    Manages error recovery strategies and graceful degradation.
    
    Provides centralized error handling with configurable recovery
    strategies for different types of errors and components.
    """
    
    def __init__(self):
        """Initialize the error recovery manager."""
        self._recovery_strategies: Dict[str, RecoveryAction] = {}
        self._error_handlers: Dict[str, Callable] = {}
        self._fallback_functions: Dict[str, Callable] = {}
        self._error_counts: Dict[str, int] = {}
        
        # Set up default recovery strategies
        self._setup_default_strategies()
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
    
    def _setup_default_strategies(self) -> None:
        """Set up default recovery strategies for common error types."""
        
        # Configuration errors - use defaults and continue
        self._recovery_strategies['config_error'] = RecoveryAction(
            strategy=RecoveryStrategy.FALLBACK,
            message="Configuration error detected, using default settings",
            should_log=True
        )
        
        # Learning content errors - graceful degradation
        self._recovery_strategies['content_error'] = RecoveryAction(
            strategy=RecoveryStrategy.GRACEFUL_DEGRADATION,
            message="Learning content unavailable, providing basic functionality",
            should_log=True
        )
        
        # Documentation generation errors - retry then fallback
        self._recovery_strategies['documentation_error'] = RecoveryAction(
            strategy=RecoveryStrategy.RETRY,
            max_retries=2,
            message="Documentation generation failed, retrying",
            should_log=True
        )
        
        # Interactive session errors - graceful degradation
        self._recovery_strategies['session_error'] = RecoveryAction(
            strategy=RecoveryStrategy.GRACEFUL_DEGRADATION,
            message="Interactive session error, continuing with limited functionality",
            should_log=True
        )
        
        # Visual documentation errors - ignore and continue
        self._recovery_strategies['visual_error'] = RecoveryAction(
            strategy=RecoveryStrategy.IGNORE,
            message="Visual documentation unavailable, continuing without visuals",
            should_log=True
        )
        
        # Critical system errors - fail fast
        self._recovery_strategies['system_error'] = RecoveryAction(
            strategy=RecoveryStrategy.FAIL_FAST,
            message="Critical system error detected",
            should_log=True
        )
    
    def handle_error(self, error_context: ErrorContext) -> RecoveryAction:
        """
        Handle an error using the appropriate recovery strategy.
        
        Args:
            error_context: Context information about the error
            
        Returns:
            RecoveryAction: Action taken for recovery
        """
        error_key = f"{error_context.component}_{error_context.error_type}"
        
        # Track error frequency
        self._error_counts[error_key] = self._error_counts.get(error_key, 0) + 1
        
        # Get recovery strategy
        strategy = self._get_recovery_strategy(error_context)
        
        # Log the error if required
        if strategy.should_log:
            self._log_error(error_context, strategy)
        
        # Execute recovery action
        return self._execute_recovery(error_context, strategy)
    
    def register_fallback(self, component: str, operation: str, fallback_function: Callable) -> None:
        """
        Register a fallback function for a specific component and operation.
        
        Args:
            component: Component name
            operation: Operation name
            fallback_function: Function to call as fallback
        """
        key = f"{component}_{operation}"
        self._fallback_functions[key] = fallback_function
    
    def register_error_handler(self, error_type: str, handler: Callable) -> None:
        """
        Register a custom error handler for a specific error type.
        
        Args:
            error_type: Type of error to handle
            handler: Handler function
        """
        self._error_handlers[error_type] = handler
    
    def set_recovery_strategy(self, error_type: str, strategy: RecoveryAction) -> None:
        """
        Set a custom recovery strategy for an error type.
        
        Args:
            error_type: Type of error
            strategy: Recovery strategy to use
        """
        self._recovery_strategies[error_type] = strategy
    
    def handle_config_error(self, error: Exception, component: str = "config") -> RecoveryAction:
        """
        Handle configuration-related errors.
        
        Args:
            error: Configuration error
            component: Component that had the error
            
        Returns:
            RecoveryAction: Recovery action taken
        """
        error_context = ErrorContext(
            component=component,
            operation="load_config",
            error_type="config_error",
            error_message=str(error),
            severity=ErrorSeverity.MEDIUM,
            metadata={"error_class": error.__class__.__name__}
        )
        
        return self.handle_error(error_context)
    
    def handle_content_error(self, error: Exception, component: str = "learning") -> RecoveryAction:
        """
        Handle learning content-related errors.
        
        Args:
            error: Content error
            component: Component that had the error
            
        Returns:
            RecoveryAction: Recovery action taken
        """
        error_context = ErrorContext(
            component=component,
            operation="load_content",
            error_type="content_error",
            error_message=str(error),
            severity=ErrorSeverity.LOW,
            metadata={"error_class": error.__class__.__name__}
        )
        
        return self.handle_error(error_context)
    
    def handle_documentation_error(self, error: Exception, component: str = "documentation") -> RecoveryAction:
        """
        Handle documentation generation errors.
        
        Args:
            error: Documentation error
            component: Component that had the error
            
        Returns:
            RecoveryAction: Recovery action taken
        """
        error_context = ErrorContext(
            component=component,
            operation="generate_docs",
            error_type="documentation_error",
            error_message=str(error),
            severity=ErrorSeverity.MEDIUM,
            metadata={"error_class": error.__class__.__name__}
        )
        
        return self.handle_error(error_context)
    
    def handle_session_error(self, error: Exception, component: str = "session") -> RecoveryAction:
        """
        Handle interactive session errors.
        
        Args:
            error: Session error
            component: Component that had the error
            
        Returns:
            RecoveryAction: Recovery action taken
        """
        error_context = ErrorContext(
            component=component,
            operation="manage_session",
            error_type="session_error",
            error_message=str(error),
            severity=ErrorSeverity.LOW,
            metadata={"error_class": error.__class__.__name__}
        )
        
        return self.handle_error(error_context)
    
    def handle_visual_error(self, error: Exception, component: str = "visual") -> RecoveryAction:
        """
        Handle visual documentation errors.
        
        Args:
            error: Visual documentation error
            component: Component that had the error
            
        Returns:
            RecoveryAction: Recovery action taken
        """
        error_context = ErrorContext(
            component=component,
            operation="create_visual",
            error_type="visual_error",
            error_message=str(error),
            severity=ErrorSeverity.LOW,
            metadata={"error_class": error.__class__.__name__}
        )
        
        return self.handle_error(error_context)
    
    def _get_recovery_strategy(self, error_context: ErrorContext) -> RecoveryAction:
        """Get the appropriate recovery strategy for an error."""
        # Check for specific component + error type strategy
        specific_key = f"{error_context.component}_{error_context.error_type}"
        if specific_key in self._recovery_strategies:
            return self._recovery_strategies[specific_key]
        
        # Check for general error type strategy
        if error_context.error_type in self._recovery_strategies:
            return self._recovery_strategies[error_context.error_type]
        
        # Default strategy based on severity
        if error_context.severity == ErrorSeverity.CRITICAL:
            return RecoveryAction(
                strategy=RecoveryStrategy.FAIL_FAST,
                message="Critical error - stopping execution"
            )
        elif error_context.severity == ErrorSeverity.HIGH:
            return RecoveryAction(
                strategy=RecoveryStrategy.RETRY,
                max_retries=1,
                message="High severity error - attempting recovery"
            )
        else:
            return RecoveryAction(
                strategy=RecoveryStrategy.GRACEFUL_DEGRADATION,
                message="Error detected - continuing with reduced functionality"
            )
    
    def _execute_recovery(self, error_context: ErrorContext, strategy: RecoveryAction) -> RecoveryAction:
        """Execute the recovery strategy."""
        error_key = f"{error_context.component}_{error_context.error_type}"
        
        if strategy.strategy == RecoveryStrategy.RETRY:
            # Check if we've exceeded retry limit
            if self._error_counts.get(error_key, 0) > strategy.max_retries:
                # Switch to fallback strategy
                strategy.strategy = RecoveryStrategy.GRACEFUL_DEGRADATION
                strategy.message = f"Max retries exceeded, switching to graceful degradation"
        
        elif strategy.strategy == RecoveryStrategy.FALLBACK:
            # Try to find and execute fallback function
            fallback_key = f"{error_context.component}_{error_context.operation}"
            if fallback_key in self._fallback_functions:
                try:
                    strategy.fallback_function = self._fallback_functions[fallback_key]
                except Exception as e:
                    self.logger.warning(f"Fallback function failed: {e}")
                    strategy.strategy = RecoveryStrategy.GRACEFUL_DEGRADATION
        
        elif strategy.strategy == RecoveryStrategy.FAIL_FAST:
            # For critical errors, raise the original error
            raise FishertoolsError(f"Critical error in {error_context.component}: {error_context.error_message}")
        
        return strategy
    
    def _log_error(self, error_context: ErrorContext, strategy: RecoveryAction) -> None:
        """Log error information."""
        log_level = self._get_log_level(error_context.severity)
        
        message = (
            f"Error in {error_context.component}.{error_context.operation}: "
            f"{error_context.error_message}. "
            f"Recovery: {strategy.strategy.value}. "
            f"{strategy.message}"
        )
        
        self.logger.log(log_level, message, extra={
            'component': error_context.component,
            'operation': error_context.operation,
            'error_type': error_context.error_type,
            'severity': error_context.severity.value,
            'recovery_strategy': strategy.strategy.value
        })
    
    def _get_log_level(self, severity: ErrorSeverity) -> int:
        """Get appropriate log level for error severity."""
        severity_to_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }
        return severity_to_level.get(severity, logging.WARNING)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about errors and recovery actions.
        
        Returns:
            Dict[str, Any]: Error statistics
        """
        total_errors = sum(self._error_counts.values())
        
        return {
            'total_errors': total_errors,
            'error_counts_by_type': dict(self._error_counts),
            'registered_fallbacks': len(self._fallback_functions),
            'registered_handlers': len(self._error_handlers),
            'recovery_strategies': len(self._recovery_strategies)
        }
    
    def reset_error_counts(self) -> None:
        """Reset error count statistics."""
        self._error_counts.clear()


# Global error recovery manager instance
_recovery_manager: Optional[ErrorRecoveryManager] = None


def get_recovery_manager() -> ErrorRecoveryManager:
    """
    Get or create the global error recovery manager.
    
    Returns:
        ErrorRecoveryManager: The global recovery manager instance
    """
    global _recovery_manager
    
    if _recovery_manager is None:
        _recovery_manager = ErrorRecoveryManager()
    
    return _recovery_manager


def handle_error_with_recovery(error: Exception, component: str, operation: str, error_type: str = "general") -> RecoveryAction:
    """
    Convenience function to handle errors with recovery.
    
    Args:
        error: The exception that occurred
        component: Component where error occurred
        operation: Operation that failed
        error_type: Type of error for recovery strategy selection
        
    Returns:
        RecoveryAction: Recovery action taken
    """
    recovery_manager = get_recovery_manager()
    
    error_context = ErrorContext(
        component=component,
        operation=operation,
        error_type=error_type,
        error_message=str(error),
        severity=ErrorSeverity.MEDIUM,
        metadata={"error_class": error.__class__.__name__}
    )
    
    return recovery_manager.handle_error(error_context)


def with_error_recovery(component: str, operation: str, error_type: str = "general"):
    """
    Decorator to add error recovery to functions.
    
    Args:
        component: Component name
        operation: Operation name
        error_type: Error type for recovery strategy
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                recovery_action = handle_error_with_recovery(e, component, operation, error_type)
                
                if recovery_action.fallback_function:
                    try:
                        return recovery_action.fallback_function(*args, **kwargs)
                    except Exception as fallback_error:
                        logging.warning(f"Fallback function failed: {fallback_error}")
                
                if recovery_action.strategy == RecoveryStrategy.FAIL_FAST:
                    raise
                
                # For other strategies, return None or appropriate default
                return None
        
        return wrapper
    return decorator