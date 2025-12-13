"""Retry handler for Bedrock API calls with exponential backoff.

This module provides error handling and retry logic for transient
Bedrock API failures, implementing exponential backoff strategy.
"""

import asyncio
import logging
import time
from typing import Callable, Any, TypeVar, Optional
from functools import wraps

logger = logging.getLogger(__name__)

# Type variable for generic return types
T = TypeVar('T')


class BedrockRetryHandler:
    """Handles transient Bedrock API failures with exponential backoff.
    
    This handler implements a retry strategy for API calls that may fail
    due to transient issues like throttling or temporary service unavailability.
    
    The exponential backoff formula is: delay = base_delay * (2 ^ attempt)
    
    Attributes:
        max_attempts: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds for exponential backoff (default: 1.0)
    
    Example:
        >>> handler = BedrockRetryHandler(max_attempts=3, base_delay=1.0)
        >>> result = handler.execute_with_retry(lambda: bedrock_api_call())
        
        Retry delays: 1s, 2s, 4s (for attempts 0, 1, 2)
    """
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0):
        """Initialize the retry handler.
        
        Args:
            max_attempts: Maximum number of retry attempts. Must be >= 1.
            base_delay: Base delay in seconds for exponential backoff. Must be > 0.
        
        Raises:
            ValueError: If max_attempts < 1 or base_delay <= 0
        """
        if max_attempts < 1:
            raise ValueError(f"max_attempts must be >= 1, got {max_attempts}")
        if base_delay <= 0:
            raise ValueError(f"base_delay must be > 0, got {base_delay}")
        
        self.max_attempts = max_attempts
        self.base_delay = base_delay
    
    def execute_with_retry(self, func: Callable[[], T]) -> T:
        """Execute a function with retry logic and exponential backoff.
        
        This method attempts to execute the provided function up to max_attempts times.
        If the function raises a retryable exception, it waits with exponential backoff
        before retrying.
        
        Retryable exceptions include:
        - Throttling errors
        - Service unavailable errors
        - Connection errors
        - Timeout errors
        
        Args:
            func: The function to execute. Should take no arguments.
        
        Returns:
            The result of the function call
        
        Raises:
            Exception: The last exception encountered if all retry attempts fail
        
        Example:
            >>> handler = BedrockRetryHandler(max_attempts=3)
            >>> result = handler.execute_with_retry(lambda: api_call())
        """
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                logger.debug(f"Attempt {attempt + 1}/{self.max_attempts}")
                result = func()
                
                if attempt > 0:
                    logger.info(f"Succeeded on attempt {attempt + 1}")
                
                return result
            
            except Exception as e:
                last_exception = e
                exception_name = type(e).__name__
                
                # Check if this is a retryable error
                if not self._is_retryable_error(e):
                    logger.error(f"Non-retryable error: {exception_name}: {str(e)}")
                    raise
                
                # If this was the last attempt, raise the exception
                if attempt == self.max_attempts - 1:
                    logger.error(
                        f"All {self.max_attempts} retry attempts failed. "
                        f"Last error: {exception_name}: {str(e)}"
                    )
                    raise
                
                # Calculate delay using exponential backoff: delay = base * 2^attempt
                delay = self.base_delay * (2 ** attempt)
                
                logger.warning(
                    f"Attempt {attempt + 1} failed with {exception_name}: {str(e)}. "
                    f"Retrying in {delay}s..."
                )
                
                # Wait before retrying
                time.sleep(delay)
        
        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError("Unexpected error in retry logic")
    
    async def execute_with_retry_async(self, func: Callable[[], T]) -> T:
        """Execute an async function with retry logic and exponential backoff.
        
        This is the async version of execute_with_retry for use with async functions.
        
        Args:
            func: The async function to execute. Should take no arguments.
        
        Returns:
            The result of the function call
        
        Raises:
            Exception: The last exception encountered if all retry attempts fail
        
        Example:
            >>> handler = BedrockRetryHandler(max_attempts=3)
            >>> result = await handler.execute_with_retry_async(async_api_call)
        """
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                logger.debug(f"Attempt {attempt + 1}/{self.max_attempts}")
                result = await func()
                
                if attempt > 0:
                    logger.info(f"Succeeded on attempt {attempt + 1}")
                
                return result
            
            except Exception as e:
                last_exception = e
                exception_name = type(e).__name__
                
                # Check if this is a retryable error
                if not self._is_retryable_error(e):
                    logger.error(f"Non-retryable error: {exception_name}: {str(e)}")
                    raise
                
                # If this was the last attempt, raise the exception
                if attempt == self.max_attempts - 1:
                    logger.error(
                        f"All {self.max_attempts} retry attempts failed. "
                        f"Last error: {exception_name}: {str(e)}"
                    )
                    raise
                
                # Calculate delay using exponential backoff: delay = base * 2^attempt
                delay = self.base_delay * (2 ** attempt)
                
                logger.warning(
                    f"Attempt {attempt + 1} failed with {exception_name}: {str(e)}. "
                    f"Retrying in {delay}s..."
                )
                
                # Wait before retrying (async)
                await asyncio.sleep(delay)
        
        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError("Unexpected error in retry logic")
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Determine if an error is retryable.
        
        Args:
            error: The exception to check
        
        Returns:
            True if the error is retryable, False otherwise
        """
        error_name = type(error).__name__
        error_message = str(error).lower()
        
        # Common retryable error patterns (check both type name and message)
        retryable_patterns = [
            "throttl",
            "rate limit",
            "too many requests",
            "service unavailable",
            "serviceunavailable",
            "timeout",
            "connection",
            "temporarily unavailable",
            "internal server error",
            "internalserver",
        ]
        
        # Check exception type name
        error_name_lower = error_name.lower()
        for pattern in retryable_patterns:
            if pattern in error_name_lower:
                return True
        
        # Check error message for common patterns
        for pattern in retryable_patterns:
            if pattern in error_message:
                return True
        
        return False


def with_retry(max_attempts: int = 3, base_delay: float = 1.0):
    """Decorator to add retry logic to a function.
    
    This decorator wraps a function with retry logic using BedrockRetryHandler.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
    
    Returns:
        Decorated function with retry logic
    
    Example:
        >>> @with_retry(max_attempts=3, base_delay=1.0)
        ... def api_call():
        ...     return bedrock.invoke_model(...)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        handler = BedrockRetryHandler(max_attempts=max_attempts, base_delay=base_delay)
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            return handler.execute_with_retry(lambda: func(*args, **kwargs))
        
        return wrapper
    
    return decorator


def with_retry_async(max_attempts: int = 3, base_delay: float = 1.0):
    """Decorator to add retry logic to an async function.
    
    This decorator wraps an async function with retry logic using BedrockRetryHandler.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
    
    Returns:
        Decorated async function with retry logic
    
    Example:
        >>> @with_retry_async(max_attempts=3, base_delay=1.0)
        ... async def api_call():
        ...     return await bedrock.invoke_model_async(...)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        handler = BedrockRetryHandler(max_attempts=max_attempts, base_delay=base_delay)
        
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await handler.execute_with_retry_async(lambda: func(*args, **kwargs))
        
        return wrapper
    
    return decorator
