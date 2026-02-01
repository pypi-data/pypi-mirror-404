#!/usr/bin/env python3
"""
Build script to generate .env.example from OPTIONS_SCHEMA

This script creates a new .env.example file based on the option schema,
ensuring documentation stays in sync with the actual option definitions.
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path to allow importing from src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from optionsconfig.schema import get_schema

class EnvBuilder:
    """Class to build .env.example from OPTIONS_SCHEMA."""

    def __init__(self, schema: dict | None = None, env_example_path: str | Path | None = None):
        """
        Initialize EnvBuilder.
        
        Args:
            schema: The OPTIONS_SCHEMA dictionary. If None, loads from pyproject.toml configuration.
            env_example_path: Optional path to .env.example file.
                             If None, will check pyproject.toml or use default.
        """
        self.env_example_file = self._get_env_example_path(env_example_path)
        self.schema = get_schema(schema)

    def build(self) -> bool:
        """Build the .env.example file."""

        if not self._update_env_example():
            return False

        if not self._validate_generated_file():
            return False

        return True

    def _get_env_example_path(self, env_example_path: str | Path | None = None) -> Path:
        """
        Get the path to the .env.example file.
        
        Priority order:
        1. Direct path parameter
        2. Configuration file (pyproject.toml)
        3. Default location (repository root)
        
        Args:
            env_example_path: Optional direct path to .env.example file
            
        Returns:
            Path to .env.example file
        """
        # 1. Direct path parameter
        if env_example_path is not None:
            return Path(env_example_path)
        
        # 2. Configuration file (pyproject.toml)
        config_path = self._load_path_from_config()
        if config_path:
            return config_path
        
        # 3. Default location
        return Path(__file__).parent.parent.parent.parent / ".env.example"
    
    def _load_path_from_config(self) -> Path | None:
        """Load env example file path from pyproject.toml."""
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
            
            env_path = config.get('tool', {}).get('optionsconfig', {}).get('env_example_path')
            if env_path:
                return Path(env_path)
        except Exception:
            # If any error occurs reading config, return None
            pass
        
        return None

    def _generate_env_example(self) -> str:
        """Generate .env.example content from schema."""
        # Header
        header = [
            "# Use forward slashes \"/\" in paths for compatibility across platforms",
        ]
        
        lines = header + [""]  # Add blank line after header
        
        def process_option(details: Dict[str, Any]) -> None:
            """Process a single option and add it to the lines."""
            env_var = details["env"]
            help_text = details.get("help", "")
            example = details.get("example", None)
            default = details.get("default", None)
            depends_on = details.get("depends_on", [])

            # Convert default value to string representation for .env file
            def _str_repr(value: Any) -> str:
                """Convert a value to its string representation for .env file."""
                if value is None:
                    return ""
                elif isinstance(value, bool):
                    return "True" if value else "False"
                elif isinstance(value, Path):
                    return str(value) if value else ""
                else:
                    return str(value)
            default_str = _str_repr(default)
            example_str = _str_repr(example)

            # Add comment with help text
            if help_text:
                # Wrap long help text
                if len(help_text) > 80:
                    # Simple word wrapping
                    words = help_text.split()
                    current_line = "# "
                    for word in words:
                        if len(current_line + word) > 80:
                            lines.append(current_line.rstrip())
                            current_line = "# " + word + " "
                        else:
                            current_line += word + " "
                    if current_line.strip() != "#":
                        lines.append(current_line.rstrip())
                else:
                    lines.append(f"# {help_text}")
            
            # Add dependency information if present
            if depends_on:
                dep_str = " or ".join(depends_on)
                lines.append(f"# Required when {dep_str} is True")
            
            # Add the environment variable with default value
            if example_str:
                lines.append(f'# Example: {example_str}')
            lines.append(f'{env_var}="{default_str}"')
            lines.append("")  # Blank line after each option
        
        # Group options by section while preserving order
        sections_data = {}
        section_order = []
        
        for option_name, details in self.schema.items():
            section = details.get("section", "Other")
            if section not in sections_data:
                sections_data[section] = []
                section_order.append(section)
            sections_data[section].append((option_name, details))
        
        # Process options by section
        for i, section in enumerate(section_order):
            # Add extra blank line between sections (except before first section)
            if i > 0:
                lines.append("")
            
            lines.append(f"# {section}")
            
            # Process all options in this section
            for _, details in sections_data[section]:
                process_option(details)
        
        return "\n".join(lines)


    def _update_env_example(self) -> bool:
        """Update the .env.example file with generated content."""
        
        try:
            # Generate new content
            new_content = self._generate_env_example()
            
            # Write to .env.example
            with open(self.env_example_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            print(f"Successfully updated {self.env_example_file}")
            print(f"Generated {len(new_content.splitlines())} lines")
            
            # Show summary of options
            option_count = len(self.schema)
            
            # Count dependent options (options with depends_on field)
            dependent_count = sum(
                1 for details in self.schema.values()
                if "depends_on" in details
            )
            
            print(f"Processed {option_count} options ({option_count - dependent_count} root + {dependent_count} dependent)")
            
        except Exception as e:
            print(f"Error updating env example: {e}")
            return False
        
        return True


    def _validate_generated_file(self) -> bool:
        """Validate that the generated .env.example file is properly formatted."""
        
        if not self.env_example_file.exists():
            print(f"Generated file {self.env_example_file} does not exist")
            return False
        
        try:
            with open(self.env_example_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # Basic validation checks
            has_header = any("Use forward slashes" in line for line in lines[:5])
            has_env_vars = any("=" in line and not line.strip().startswith("#") for line in lines)
            
            if not has_header:
                print("Warning: Generated file missing expected header")
                return False
            
            if not has_env_vars:
                print("Warning: Generated file contains no environment variables")
                return False
            
            print(f"Generated file validation passed ({len(lines)} lines)")
            return True
            
        except Exception as e:
            print(f"Error validating generated file: {e}")
            return False