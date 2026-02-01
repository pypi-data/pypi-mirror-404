"""
Options class for managing application configuration
"""

from dotenv import load_dotenv
import os
import sys
from argparse import Namespace
from typing import Literal, get_origin, get_args
from pathlib import Path
from loguru import logger

from .schema import get_schema

def setup_logging(log_file: str | Path | None = None, log_level: str = "DEBUG", delete_existing: bool = False) -> Path:
    """
    Setup loguru logging to the specified log file.
    
    Args:
        log_file: Path to log file. If None, uses default location.
        log_level: Logging level (default: DEBUG)
        delete_existing: Whether to delete existing loggers (default: False)
        
    Returns:
        Path to the log file being used
    """
    # Determine log file path
    if log_file is not None:
        log_path = Path(log_file)
    else:
        # Try to load from config
        config_path = _load_log_file_from_config()
        if config_path:
            log_path = config_path
        else:
            # Default location
            default_dir = Path(__file__).parent / 'logs'
            log_path = default_dir / 'default.log'
    
    # Ensure parent directory exists
    os.makedirs(log_path.parent, exist_ok=True)
    
    # Delete existing loggers if requested
    if delete_existing:
        logger.remove()
        # Clear the log file when deleting existing loggers
        with open(log_path, 'w') as f:
            pass
    
    # Check existing handlers and merge instead of replace
    existing_handlers = logger._core.handlers
    file_handler_exists = any(str(log_path) in str(handler) for handler in existing_handlers.values())
    stdout_handler_exists = any("stdout" in str(handler) or "sys.stdout" in str(handler) for handler in existing_handlers.values())
    
    # Add or update handlers
    format_with_color = "<level>{level}</level> | <cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    
    if not file_handler_exists:
        # Add new file handler with append mode (don't clear file)
        logger.add(str(log_path), level=log_level, rotation="30 MB", retention="10 days", enqueue=True, format=format_with_color, mode="a")
    else:
        # Remove existing file handler and add new one with updated level
        for handler_id, handler in existing_handlers.items():
            if str(log_path) in str(handler):
                logger.remove(handler_id)
                break
        logger.add(str(log_path), level=log_level, rotation="30 MB", retention="10 days", enqueue=True, format=format_with_color, mode="a")
    
    if not stdout_handler_exists:
        # Add new stdout handler
        logger.add(sys.stdout, level=log_level, format=format_with_color)
    else:
        # Remove existing stdout handler and add new one with updated level
        for handler_id, handler in existing_handlers.items():
            if "stdout" in str(handler) or "sys.stdout" in str(handler):
                logger.remove(handler_id)
                break
        logger.add(sys.stdout, level=log_level, format=format_with_color)
    
    logger.debug(f"Logging initialized to: {log_path} and stdout")
    
    return log_path


def _load_log_file_from_config() -> Path | None:
    """Load log file path from pyproject.toml."""
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            # Python < 3.11 and tomli not installed, skip this method
            return None
    
    config_file = Path('pyproject.toml')
    if not config_file.exists():
        return None
    
    try:
        with open(config_file, 'rb') as f:
            config = tomllib.load(f)
        
        log_file_path = config.get('tool', {}).get('optionsconfig', {}).get('log_file')
        if log_file_path:
            return Path(log_file_path)
    except Exception:
        # If any error occurs reading config, return None
        pass
    
    return None


class Options:
    """
    A class to hold options for the application.
    """
    def __init__(self, args: Namespace | None = None, schema: dict | None = None, log_file: str | Path | None = None, setup_logger: bool = True):
        # Load .env from current working directory (user's project root)
        # This must be called here (not at module level) to ensure it loads from the
        # user's project directory, not from where OptionsConfig is installed
        cwd = Path.cwd()
        env_file = cwd / ".env"
        
        # Explicitly load .env file if it exists
        if env_file.exists():
            load_dotenv(dotenv_path=env_file, override=True)
            logger.debug(f"Loaded .env from: {env_file}")
        else:
            logger.debug(f".env not found at: {env_file}")
        
        self.schema = get_schema(schema=schema)
        
        # Setup logging if requested
        if setup_logger:
            self.log_file = setup_logging(log_file=log_file, log_level=getattr(self, 'log_level', 'DEBUG'), delete_existing=True)
        else:
            self.log_file = Path(log_file) if log_file else None

        # Initialize all options in the following preference
        # 1. Direct args (if provided)
        # 2. Environment variables (if set)
        # 3. Defaults from OPTIONS_SCHEMA

        # If args is provided, it should be a Namespace from argparse
        if args is not None:
            args_dict = vars(args)
        else:
            args_dict = {}

        # Identify root options (options that other options depend on)
        self.root_options = []
        for option_name, details in self.schema.items():
            # An option is a root option if other options depend on it
            is_root = any(
                option_name in self.schema[other_option]["depends_on"]
                for other_option in self.schema
            )
            if is_root:
                self.root_options.append(option_name)

        # Process the schema to set all attributes
        options = self._process_schema(self.schema, args_dict)

        # Set attributes dynamically using lowercase underscore format
        for key, value in options.items():
            # Convert schema key (UPPER_CASE) to attribute name (lower_case)
            details = self.schema[key]
            var_name = details["var"]
            setattr(self, var_name, value)
            logger.debug(f"Set option {var_name} to value: {value if not details['sensitive'] else '***HIDDEN***'}")

        # Set log level
        if setup_logger and getattr(self, 'log_file', None) is not None:
            setup_logging(log_file=self.log_file, log_level=self.log_level)

        self.validate()
        
        self.log()

    def _process_schema(self, schema: dict, args_dict: dict) -> dict:
        """Process the option schema, env options, and args to get the combined options."""

        options = {}

        # Process all options in the schema
        for option_name, details in schema.items():
            # Convert arg name to attribute name (remove -- and convert - to _)
            var_name = details["var"]
            
            # Get value in order of priority: args -> env -> default
            value = None

            logger.debug(f"Processing option: {option_name} (var: {var_name})")

            # 1. Check args first
            if var_name in args_dict and args_dict[var_name] is not None:
                value = args_dict[var_name]
                logger.debug(f"Argument {var_name} found in args with value: {value if not details['sensitive'] else '***HIDDEN***'}")
            # 2. Check environment variable
            elif details["env"] in os.environ:
                env_value = os.environ[details["env"]]
                logger.debug(f"Environment variable {details['env']} found with value: {env_value if not details['sensitive'] else '***HIDDEN***'}")
                # Convert environment string to proper type
                if details["type"] == bool:
                    value = is_truthy(env_value)
                elif details["type"] == Path:
                    value = Path(env_value) if env_value else None
                elif get_origin(details["type"]) is Literal:
                    # For Literal types, use the string value directly if it's valid
                    valid_choices = get_args(details["type"])
                    value = env_value if env_value in valid_choices else details["default"]
                else:
                    value = details["type"](env_value) if env_value else details["default"]
            # 3. Use default
            else:
                value = details["default"]
            
            # Store
            options[option_name] = value

        # If none of the root options have been explicitly set (from args or env), default all to true for ease of use
        # Check if any root option was explicitly provided (not just defaulted from schema)
        explicitly_set_root_options = []
        for root_option in self.root_options:
            var_name = self.schema[root_option]["var"]
            # Check if it was in args or environment
            if (var_name in args_dict and args_dict[var_name] is not None) or \
               self.schema[root_option]["env"] in os.environ:
                explicitly_set_root_options.append(root_option)
        
        if not explicitly_set_root_options:
            # No root options were explicitly set, default all to True
            for root_option in self.root_options:
                options[root_option] = True
            logger.debug("No root options explicitly set, defaulting all to True")

        return options
    
    def validate(self) -> None:
        # Validate that options with dependencies have their requirements met
        options_as_dict = {k.upper(): v for k, v in self.__dict__.items() if k != 'root_options'}
        
        # Check each option that has dependencies
        for option_name, details in self.schema.items():
            depends_on_list = details["depends_on"]
            if not depends_on_list:
                continue
            
            # Check if ANY of the dependencies are True
            any_dependency_true = any(
                options_as_dict[dep_option] is True
                for dep_option in depends_on_list
            )
            
            if any_dependency_true:
                value = options_as_dict.get(option_name)
                if value is None:
                    # Build a helpful error message
                    active_dependencies = [
                        dep for dep in depends_on_list
                        if options_as_dict[dep] is True
                    ]
                    raise ValueError(
                        f"{option_name} is required when any of the following are true: "
                        f"{', '.join(depends_on_list)}. Currently active: {', '.join(active_dependencies)}"
                    )
                logger.debug(f"Dependent option {option_name} is set to {value if not details['sensitive'] else '***HIDDEN***'}")
        
    def log(self):
        """
        Logs the options.
        """
        # Dynamically log all attributes that were set from the schema
        log_lines = ["Options initialized with:"]
        
        for option_name, details in self.schema.items():
            var_name = details["var"]
            if hasattr(self, var_name):
                value = getattr(self, var_name)
                # Don't log sensitive information
                if details["sensitive"]:
                    value = "***HIDDEN***"
                log_lines.append(f"{option_name}: {value}")
        
        logger.info("\n".join(log_lines))


# Helper to initialize OPTIONS with direct args if available
def init_options(args: Namespace | None = None, schema: dict | None = None, log_file: str | Path | None = None, setup_logger: bool = True) -> Options:
    global OPTIONS
    OPTIONS = Options(args=args, schema=schema, log_file=log_file, setup_logger=setup_logger)
    return OPTIONS


def is_truthy(string):
    TRUE_THO = [
        True,
        'true',
        'True',
        'TRUE',
        't',
        'T',
        1,
    ]
    return string in TRUE_THO
