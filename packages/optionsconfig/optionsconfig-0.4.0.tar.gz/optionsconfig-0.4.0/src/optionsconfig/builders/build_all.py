#!/usr/bin/env python3
"""
Master build script to update all generated documentation files

This script is meant to be used by projects that consume this library.
It should NOT be run in the optionsconfig repository itself.

For users of optionsconfig:
- Copy this file to your project root or scripts directory
- Ensure your OPTIONS_SCHEMA is configured in pyproject.toml
- Run it to generate .env.example and update README.md

This script:
1. Generates .env.example from OPTIONS_SCHEMA
2. Generates and updates README.md with option documentation
"""

import sys
from pathlib import Path

# Add parent directories to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root / "src"))

from optionsconfig.schema import get_schema
from optionsconfig.builders import EnvBuilder, ReadmeBuilder


def main() -> bool:
    """Run all documentation builders."""
    
    print("Building all documentation from OPTIONS_SCHEMA...")
    print("=" * 60)
    
    try:
        # Add repo root to path so src.options_schema can be imported
        sys.path.insert(0, str(repo_root))
        
        # Get schema
        schema = get_schema()
        print(f"Loaded schema with {len(schema)} options")
        print()
        
        # Build .env.example
        print("Building .env.example...")
        env_builder = EnvBuilder(schema=schema)
        if not env_builder.build():
            print("ERROR: EnvBuilder failed")
            return False
        print()
        
        # Build README.md
        print("Building README.md...")
        readme_builder = ReadmeBuilder(schema=schema)
        if not readme_builder.build():
            print("ERROR: ReadmeBuilder failed")
            return False
        print()
        
        # Summary
        print("=" * 60)
        print("SUCCESS: All documentation built!")
        print("\nGenerated/Updated Files:")
        print(f"   {env_builder.env_example_file} - Environment configuration template")
        print(f"   {readme_builder.readme_file} - Updated with current option documentation")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
