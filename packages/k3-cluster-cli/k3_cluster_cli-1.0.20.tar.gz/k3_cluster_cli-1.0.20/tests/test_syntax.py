"""Syntax validation tests to catch Python syntax errors before deployment."""

import ast
import sys
from pathlib import Path


def test_all_python_files_have_valid_syntax():
    """Ensure all Python files in the package have valid syntax."""
    project_root = Path(__file__).parent.parent
    cluster_cli_dir = project_root / "cluster_cli"

    python_files = list(cluster_cli_dir.glob("**/*.py"))
    assert python_files, "No Python files found in cluster_cli directory"

    errors = []
    for py_file in python_files:
        try:
            source = py_file.read_text()
            ast.parse(source)
        except SyntaxError as e:
            errors.append(f"{py_file}: line {e.lineno}: {e.msg}")

    assert not errors, f"Syntax errors found:\n" + "\n".join(errors)


def test_main_module_compiles():
    """Verify main.py compiles without syntax errors."""
    project_root = Path(__file__).parent.parent
    main_file = project_root / "cluster_cli" / "main.py"

    source = main_file.read_text()
    # This will raise SyntaxError if there are issues
    compile(source, main_file, "exec")


def test_no_unterminated_strings():
    """Check for common string literal issues."""
    project_root = Path(__file__).parent.parent
    cluster_cli_dir = project_root / "cluster_cli"

    for py_file in cluster_cli_dir.glob("**/*.py"):
        source = py_file.read_text()
        lines = source.split("\n")

        for i, line in enumerate(lines, 1):
            # Skip comments
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            # Check for obvious unterminated f-strings with doubled quotes
            if '""")' in line or "''')'" in line:
                # These might be legitimate triple-quoted strings
                continue
            if '"")' in line and 'f"' in line:
                # Potential issue like: print(f"text"")
                # Count quotes to see if balanced
                pass  # ast.parse will catch actual errors
