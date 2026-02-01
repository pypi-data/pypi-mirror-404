"""
Generic decorators for logging and retry logic.
"""

import time
import functools
from functools import wraps
from typing import Callable
from commonv2 import get_logger

logger = get_logger(__name__)

def log_execution_time(func: Callable) -> Callable:
    """
    Decorator to log function execution time.
    
    Args:
        func: Function to decorate
    
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"Starting {func.__name__}...")
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"✓ {func.__name__} completed in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"✗ {func.__name__} failed after {execution_time:.2f} seconds: {str(e)}")
            raise
    
    return wrapper

def retry_with_backoff(max_retries=3, base_delay=1.0, max_delay=60.0):
    """Decorator for retry logic with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, TimeoutError) as e:
                    if attempt == max_retries - 1:
                        raise
                    
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(
                        f"⚠️  Attempt {attempt+1} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
