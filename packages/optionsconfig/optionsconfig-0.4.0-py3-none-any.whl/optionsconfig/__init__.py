"""
OptionsConfig - Schema-driven configuration management for Python applications
"""

from .schema import get_schema
from .argument_writer import ArgumentWriter
from .options import Options, init_options, setup_logging
from .builders.env_builder import EnvBuilder
from .builders.readme_builder import ReadmeBuilder
from loguru import logger

__version__ = "1.0.0"
__all__ = [
    "get_schema",
    "ArgumentWriter",
    "Options",
    "init_options",
    "setup_logging",
    "EnvBuilder",
    "ReadmeBuilder",
    "logger",
]