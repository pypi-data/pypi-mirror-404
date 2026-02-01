#!/usr/bin/env python3
"""
Generate Pydantic models from the Spotify OpenAPI schema.

This script uses datamodel-codegen to generate Pydantic v2 models from the
official Spotify Web API OpenAPI specification.
"""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Run datamodel-codegen to generate models."""
    root_dir = Path(__file__).parent.parent
    schema_path = root_dir / "schemas" / "spotify_openapi.yaml"
    output_path = root_dir / "src" / "spotipy_types" / "models.py"

    if not schema_path.exists():
        print(f"Error: Schema file not found at {schema_path}", file=sys.stderr)
        return 1

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "datamodel-codegen",
        "--input",
        str(schema_path),
        "--input-file-type",
        "openapi",
        "--output",
        str(output_path),
        "--output-model-type",
        "pydantic_v2.BaseModel",
        "--use-union-operator",
        "--use-standard-collections",
        "--use-default-kwarg",
        "--target-python-version",
        "3.11",
        "--use-field-description",
        "--wrap-string-literal",
        "--field-constraints",
        "--collapse-root-models",
        "--set-default-enum-member",
    ]

    print(f"Generating models from {schema_path}...")
    print(f"Output: {output_path}")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        # Add module docstring and __all__ export
        add_module_exports(output_path)

        print("✓ Models generated successfully!")
        return 0

    except subprocess.CalledProcessError as e:
        print(f"Error generating models: {e}", file=sys.stderr)
        print(e.stdout)
        print(e.stderr, file=sys.stderr)
        return 1
    except FileNotFoundError:
        print(
            "Error: datamodel-codegen not found. Install with: pip install datamodel-code-generator",
            file=sys.stderr,
        )
        return 1


def add_module_exports(output_path: Path) -> None:
    """Add module docstring and __all__ export to generated file."""
    content = output_path.read_text()

    # Add module docstring at the top
    docstring = '''"""Pydantic models for the Spotify Web API.

Auto-generated from the official Spotify OpenAPI schema.
Schema version: 2025.5.18
Source: https://github.com/sonallux/spotify-web-api
"""

'''

    # Find all model classes defined in the file
    import re

    model_pattern = r"^class (\w+)\("
    models = re.findall(model_pattern, content, re.MULTILINE)

    # Build __all__ list
    all_exports = "\n".join(f'    "{model}",' for model in sorted(models))

    all_section = f"""
__all__ = [
{all_exports}
]
"""

    # Insert after imports but before first class
    # Find the position after the last import
    lines = content.split("\n")
    import_end = 0
    for i, line in enumerate(lines):
        if line.startswith("from ") or line.startswith("import "):
            import_end = i + 1

    # Insert docstring at the very beginning
    new_content = docstring + "\n".join(lines[:import_end]) + "\n" + "\n".join(lines[import_end:])

    # Add __all__ at the end of the file (before if __name__ == "__main__" if present)
    if '\nif __name__ == "__main__":' in new_content:
        new_content = new_content.replace(
            '\nif __name__ == "__main__":', all_section + '\n\nif __name__ == "__main__":'
        )
    else:
        new_content = new_content + all_section

    output_path.write_text(new_content)
    print(f"✓ Added {len(models)} models to __all__")


if __name__ == "__main__":
    sys.exit(main())
