#!/usr/bin/env python3
"""
Build script to generate README option documentation from OPTIONS_SCHEMA

This script creates markdown documentation for all options that can be
included in the README.md file, ensuring documentation stays in sync.
"""

import sys
import re
import os
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path to allow importing from src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from optionsconfig.schema import get_schema

class ReadmeBuilder:
    """Class to build README option documentation from OPTIONS_SCHEMA."""

    def __init__(self, schema: dict | None = None, readme_path: str | Path | None = None):
        """
        Initialize ReadmeBuilder.
        
        Args:
            schema: The OPTIONS_SCHEMA dictionary. If None, loads from pyproject.toml configuration.
            readme_path: Optional path to README.md file.
                        If None, will check pyproject.toml or use default.
        """
        self.readme_file = self._get_readme_path(readme_path)
        self.schema = get_schema(schema)

    def build(self) -> bool:
        """Build and update the README.md file with option documentation."""
        
        # Generate the option documentation
        options_content = self._generate_readme_options()
        
        # Update README.md with the generated content
        if not self._update_readme(options_content):
            return False
        
        print(f"Generated file validation passed ({len(options_content.splitlines())} lines)")
        return True

    def _get_readme_path(self, readme_path: str | Path | None = None) -> Path:
        """
        Get the path to the README.md file.
        
        Priority order:
        1. Direct path parameter
        2. Configuration file (pyproject.toml)
        3. Default location (repository root)
        
        Args:
            readme_path: Optional direct path to README.md file
            
        Returns:
            Path to README.md file
        """
        # 1. Direct path parameter
        if readme_path is not None:
            return Path(readme_path)
        
        # 2. Configuration file (pyproject.toml)
        config_path = self._load_path_from_config()
        if config_path:
            return config_path
        
        # 3. Default location
        return Path(__file__).parent.parent.parent.parent / "README.md"
    
    def _load_path_from_config(self) -> Path | None:
        """Load README path from pyproject.toml."""
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
            
            readme_path = config.get('tool', {}).get('optionsconfig', {}).get('readme_path')
            if readme_path:
                return Path(readme_path)
        except Exception:
            # If any error occurs reading config, return None
            pass
        
        return None

    def _generate_readme_options(self) -> str:
        """Generate option documentation organized by sections from schema."""
        
        lines = []
        
        # Group options by section
        sections_data = {}
        for option_name, details in self.schema.items():
            section = details.get("section", "Other")
            if section not in sections_data:
                sections_data[section] = []
            
            # Determine if this is a dependent option (has depends_on field)
            is_dependent = "depends_on" in details
            sections_data[section].append((option_name, details, is_dependent))
        
        # Generate documentation for each section
        for section, options in sections_data.items():
            lines.extend([
                f"#### {section}",
                "",
            ])
            for option_name, details, is_dependent in options:
                self._add_option_doc_to_lines(lines, option_name, details, is_dependent)
            lines.append("")
        
        return "\n".join(lines)

    def _add_option_doc_to_lines(self, lines: list, option_name: str, details: Dict[str, Any], is_dependent: bool = False, indent_level: int = 0) -> None:
        """Add documentation for a single option to the lines list."""
        env_var = details["env"]
        help_text = details.get("help", "")
        default = details.get("default", "")
        arg_name = details["arg"]
        depends_on = details.get("depends_on", [])
        example = details.get("example", None)
        
        # Convert default value to readable string
        if default is None:
            if depends_on:
                # Build dependency string
                dep_str = " or ".join(depends_on)
                default_str = f"None - required when {dep_str} is True"
            else:
                default_str = "None"
        elif isinstance(default, bool):
            default_str = f'`"{str(default).lower()}"`'
        elif isinstance(default, str):
            if default == "":
                default_str = '`""` (empty)'
            else:
                default_str = f'`"{default}"`'
        else:
            default_str = f'`"{default}"`'

        # Convert example value to readable string
        example_str = None
        if example is not None:
            if isinstance(example, bool):
                example_str = f'`"{str(example).lower()}"`'
            elif isinstance(example, Path):
                # Convert Path to string using forward slashes
                example_str = f'`"{str(example).replace(os.sep, "/")}"`'
            else:
                example_str = f'`"{example}"`'
        
        # Create the option entry
        indent = "  " * indent_level if is_dependent else ""
        bullet = "-" if not is_dependent else "*"
        
        lines.append(f"{indent}{bullet} **{env_var}** - {help_text}")
        if example_str:
            lines.append(f"{indent}  - Example: {example_str}")
        lines.append(f"{indent}  - Default: {default_str}")
        lines.append(f"{indent}  - Command line: `{arg_name}`")
        
        # Add dependency information if present
        if depends_on:
            dep_list = ", ".join(f"`{dep}`" for dep in depends_on)
            lines.append(f"{indent}  - Depends on: {dep_list}")
        
        # Add links if present
        if "links" in details:
            for link_name, link_url in details["links"].items():
                lines.append(f"{indent}  - [{link_name}]({link_url})")
        
        # Add extended help if present
        if "help_extended" in details:
            lines.append(f"{indent}  - {details['help_extended']}")
        
        lines.append("")  # Blank line after each option

    def _update_readme(self, options_content: str) -> bool:
        """Update README.md content between markers."""
        
        if not self.readme_file.exists():
            print(f"README.md not found at {self.readme_file}")
            return False
        
        try:
            # Read README
            with open(self.readme_file, "r", encoding="utf-8") as f:
                readme_content = f.read()
            
            # Define markers
            start_marker = "<!-- BEGIN_GENERATED_OPTIONS -->"
            end_marker = "<!-- END_GENERATED_OPTIONS -->"
            
            # Check if markers exist
            if start_marker not in readme_content or end_marker not in readme_content:
                raise ValueError(
                    f"Markers not found in {self.readme_file}\n"
                    f"Add these markers where you want the option docs:\n"
                    f"    {start_marker}\n"
                    f"    {end_marker}"
                )
            
            # Replace content between markers
            start_pos = readme_content.find(start_marker)
            end_pos = readme_content.find(end_marker)
            
            if start_pos == -1 or end_pos == -1:
                raise ValueError(
                    f"Markers not found in {self.readme_file}\n"
                    f"Add these markers where you want the option docs:\n"
                    f"    {start_marker}\n"
                    f"    {end_marker}"
                )
            
            # Get content before start marker and after end marker
            before_content = readme_content[:start_pos]
            after_content = readme_content[end_pos + len(end_marker):]
            
            # Combine with new content
            new_readme_content = f"{before_content}{start_marker}\n{options_content}\n{end_marker}{after_content}"
            
            # Write updated README
            with open(self.readme_file, "w", encoding="utf-8") as f:
                f.write(new_readme_content)
            
            print(f"Successfully updated {self.readme_file}")
            
            # Show summary of options
            option_count = len(self.schema)
            
            # Count dependent options (options with depends_on field)
            dependent_count = sum(
                1 for details in self.schema.values()
                if "depends_on" in details
            )
            
            print(f"Processed {option_count} options ({option_count - dependent_count} root + {dependent_count} dependent)")
            
        except ValueError:
            # Re-raise ValueError (e.g., markers not found)
            raise
        except Exception as e:
            print(f"Error updating README: {e}")
            return False
        
        return True
