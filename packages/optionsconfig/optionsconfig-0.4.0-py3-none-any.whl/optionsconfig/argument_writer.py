"""
ArgumentWriter class for generating command line arguments from OPTIONS_SCHEMA
"""

from argparse import ArgumentParser, ArgumentTypeError
from typing import Literal, get_origin, get_args
from pathlib import Path
from loguru import logger

from .schema import get_schema

class ArgumentWriter:
    """
    Helper class to write command line arguments based on OPTIONS_SCHEMA
    """

    def __init__(self, schema: dict | None = None):
        self.schema = get_schema(schema=schema)

    @staticmethod
    def str2bool(v: str) -> bool:
        """Convert string to boolean for argparse."""
        if isinstance(v, bool):
            return v
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise ArgumentTypeError('Boolean value expected.')

    def add_arguments(self, parser: ArgumentParser):
        for option_name, details in self.schema.items():
            arg_name = details["arg"]
            arg_type = details["type"]
            default = details["default"]
            help_text = details.get("help", "") + f" (default: {default})"
            
            if arg_type == bool: # ensure Boolean Arguments section in SCHEMA.md is updated
                parser.add_argument(arg_name, type=self.str2bool, nargs='?', const=True, default=None, help=help_text)
                logger.debug(f"Added boolean argument {arg_name} with str2bool, const=True and default None")
            elif get_origin(arg_type) is Literal:
                # Handle Literal types by extracting the choices
                choices = list(get_args(arg_type))
                parser.add_argument(arg_name, choices=choices, default=None, help=help_text)
                logger.debug(f"Added choice argument {arg_name} with choices {choices} and default None")
            elif arg_type == Path:
                # Handle Path types
                parser.add_argument(arg_name, type=str, default=None, help=help_text)
                logger.debug(f"Added path argument {arg_name} with default None")
            else:
                parser.add_argument(arg_name, type=arg_type, default=None, help=help_text)
                logger.debug(f"Added argument {arg_name} with type {arg_type} and default None")
        logger.debug(f"All arguments added to parser. Actual defaults will be set when the schema, args, and env are processed together.")
