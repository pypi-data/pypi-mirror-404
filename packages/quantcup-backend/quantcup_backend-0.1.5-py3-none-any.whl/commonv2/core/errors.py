"""
Standardized error handling for QuantCup CLI commands.

Provides consistent error types and exit codes across all modules
in the QuantCup ecosystem.
"""

from typing import Optional


class NFLfastRError(Exception):
    """
    User-facing CLI error for QuantCup commands.
    
    This exception should be used for errors that are the result of user input
    or configuration issues, not internal system errors. When caught by CLI
    commands, the message should be displayed to the user and the process
    should exit with code 2.
    
    Examples:
        - Invalid command line arguments
        - Missing required configuration
        - Invalid season expressions
        - Data validation failures due to user input
    """
    
    def __init__(self, message: str, exit_code: int = 2):
        """
        Initialize NFLfastR error.
        
        Args:
            message: User-friendly error message
            exit_code: Exit code to use (default: 2 for CLI errors)
        """
        super().__init__(message)
        self.exit_code = exit_code


class ConfigurationError(NFLfastRError):
    """Error related to configuration issues."""
    
    def __init__(self, message: str):
        super().__init__(f"Configuration error: {message}", exit_code=4)


class DataValidationError(NFLfastRError):
    """Error related to data validation failures."""
    
    def __init__(self, message: str):
        super().__init__(f"Data validation error: {message}", exit_code=3)


class NetworkError(NFLfastRError):
    """Error related to network or API issues."""
    
    def __init__(self, message: str):
        super().__init__(f"Network error: {message}", exit_code=5)


class SeasonError(NFLfastRError):
    """Error related to invalid season expressions or ranges."""
    
    def __init__(self, message: str):
        super().__init__(f"Season error: {message}", exit_code=2)


def handle_cli_error(error: Exception, verbose: bool = False) -> int:
    """
    Handle CLI errors consistently across all commands.
    
    Args:
        error: Exception that was raised
        verbose: Whether to show detailed error information
        
    Returns:
        Exit code to use
    """
    from .cli import echo_error, echo_warning
    
    if isinstance(error, NFLfastRError):
        # User-facing error - show clean message
        echo_error(str(error))
        if verbose:
            import traceback
            echo_warning("Detailed error information:")
            traceback.print_exc()
        return error.exit_code
    
    else:
        # Unexpected error - show generic message
        echo_error(f"An unexpected error occurred: {type(error).__name__}")
        if verbose:
            echo_error(str(error))
            import traceback
            traceback.print_exc()
        else:
            echo_warning("Use --verbose for detailed error information")
        return 1


def validate_required_config(config_dict: dict, required_keys: list, context: str = "") -> None:
    """
    Validate that required configuration keys are present.
    
    Args:
        config_dict: Configuration dictionary to validate
        required_keys: List of required keys
        context: Context string for error messages
        
    Raises:
        ConfigurationError: If any required keys are missing
    """
    missing_keys = [key for key in required_keys if key not in config_dict or config_dict[key] is None]
    
    if missing_keys:
        context_str = f" for {context}" if context else ""
        raise ConfigurationError(
            f"Missing required configuration{context_str}: {', '.join(missing_keys)}"
        )


def validate_file_exists(file_path: str, description: str = "File") -> None:
    """
    Validate that a file exists.
    
    Args:
        file_path: Path to file to check
        description: Description of the file for error messages
        
    Raises:
        NFLfastRError: If file does not exist
    """
    import os
    
    if not os.path.exists(file_path):
        raise NFLfastRError(f"{description} not found: {file_path}")
    
    if not os.path.isfile(file_path):
        raise NFLfastRError(f"{description} is not a file: {file_path}")


def validate_directory_exists(dir_path: str, description: str = "Directory") -> None:
    """
    Validate that a directory exists.
    
    Args:
        dir_path: Path to directory to check
        description: Description of the directory for error messages
        
    Raises:
        NFLfastRError: If directory does not exist
    """
    import os
    
    if not os.path.exists(dir_path):
        raise NFLfastRError(f"{description} not found: {dir_path}")
    
    if not os.path.isdir(dir_path):
        raise NFLfastRError(f"{description} is not a directory: {dir_path}")


def safe_int_conversion(value: str, field_name: str, min_value: Optional[int] = None, max_value: Optional[int] = None) -> int:
    """
    Safely convert a string to integer with validation.
    
    Args:
        value: String value to convert
        field_name: Name of the field for error messages
        min_value: Minimum allowed value (optional)
        max_value: Maximum allowed value (optional)
        
    Returns:
        Converted integer value
        
    Raises:
        NFLfastRError: If conversion fails or value is out of range
    """
    try:
        int_value = int(value)
    except ValueError:
        raise NFLfastRError(f"Invalid {field_name}: '{value}' is not a valid integer")
    
    if min_value is not None and int_value < min_value:
        raise NFLfastRError(f"Invalid {field_name}: {int_value} is less than minimum {min_value}")
    
    if max_value is not None and int_value > max_value:
        raise NFLfastRError(f"Invalid {field_name}: {int_value} is greater than maximum {max_value}")
    
    return int_value
