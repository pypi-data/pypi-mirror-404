#!/usr/bin/env python3
"""
Code Standards Enforcement Hook for Deriver Project.

Enforces:
- No imports inside functions
- Self-reference derive API (not raw SymPy)
- No nested for loops (use itertools.product)
- No special characters/emojis
- CamelCase naming for public API functions
- Test file modification warnings
"""
import ast
import json
import re
import sys


def check_imports_in_functions(file_path: str, content: str) -> list[str]:
    """Check for imports inside function definitions using AST.

    Exempts example notebooks (marimo requires imports inside cells).
    """
    issues = []

    # Skip examples directory - marimo notebooks require imports inside cells
    if "/examples/" in file_path or file_path.startswith("examples/"):
        return issues

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return issues

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(node):
                if isinstance(child, (ast.Import, ast.ImportFrom)):
                    issues.append(
                        f"Line {child.lineno}: Import inside function "
                        f"'{node.name}' - move to module top-level"
                    )
    return issues


def check_sympy_direct_usage(file_path: str, content: str) -> list[str]:
    """Check for direct SymPy usage instead of derive API."""
    issues = []

    # Skip test files and __init__ files
    if "test" in file_path or "__init__" in file_path:
        return issues

    # Only check src/derive files
    if "src/derive" not in file_path:
        return issues

    patterns = [
        (r"sympy\.symbols\(", "Use derive.Symbol() instead of sympy.symbols()"),
        (r"sympy\.simplify\(", "Use derive.Simplify() instead of sympy.simplify()"),
        (r"sympy\.expand\(", "Use derive.Expand() instead of sympy.expand()"),
        (r"sympy\.diff\(", "Use derive.D() instead of sympy.diff()"),
        (r"sympy\.integrate\(", "Use derive.Integrate() instead of sympy.integrate()"),
        (r"sympy\.solve\(", "Use derive.Solve() instead of sympy.solve()"),
        (r"sympy\.limit\(", "Use derive.Limit() instead of sympy.limit()"),
        (r"sympy\.series\(", "Use derive.Series() instead of sympy.series()"),
    ]

    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        # Skip comments
        if line.strip().startswith("#"):
            continue
        for pattern, message in patterns:
            if re.search(pattern, line):
                issues.append(f"Line {i}: {message}")

    return issues


def check_nested_loops(content: str) -> list[str]:
    """Check for nested for loops using AST."""
    issues = []
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return issues

    def find_nested_loops(node, depth=0):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.For):
                if depth > 0:
                    issues.append(
                        f"Line {child.lineno}: Nested for loop - "
                        "consider itertools.product() or comprehensions"
                    )
                find_nested_loops(child, depth + 1)
            else:
                find_nested_loops(child, depth)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            find_nested_loops(node)

    return issues


def check_special_characters(content: str) -> list[str]:
    """Check for emojis and special unicode characters."""
    issues = []

    # Emoji unicode ranges
    emoji_pattern = re.compile(
        "["
        "\U0001F300-\U0001F9FF"  # Misc symbols, emoticons, etc.
        "\U0001FA00-\U0001FA6F"  # Chess, extended-A
        "\U0001FA70-\U0001FAFF"  # Symbols extended-A
        "\u2600-\u27BF"  # Misc symbols
        "\u2300-\u23FF"  # Misc technical
        "]"
    )

    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        # Skip comments that might contain documentation examples
        if line.strip().startswith("#"):
            continue
        matches = emoji_pattern.findall(line)
        if matches:
            issues.append(
                f"Line {i}: Special character/emoji found ({matches[0]!r}) - use ASCII only"
            )

    return issues


def check_test_modification(file_path: str) -> list[str]:
    """Warn when test files are being modified."""
    issues = []
    if "/tests/" in file_path and file_path.endswith(".py"):
        issues.append(
            f"WARNING: Modifying test file ({file_path}). "
            "Ensure you are fixing code, not modifying tests to pass."
        )
    return issues


def check_api_naming(file_path: str, content: str) -> list[str]:
    """Check that public API functions use CamelCase naming."""
    issues = []

    # Only check src/derive files, skip internals
    if "src/derive" not in file_path:
        return issues

    # Skip test files and private modules
    if "test" in file_path or "/_" in file_path:
        return issues

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return issues

    for node in ast.iter_child_nodes(tree):
        # Only check module-level function definitions (public API)
        if isinstance(node, ast.FunctionDef):
            name = node.name

            # Skip private/internal functions
            if name.startswith("_"):
                continue

            # Skip dunder methods
            if name.startswith("__") and name.endswith("__"):
                continue

            # Check if it's CamelCase (starts with uppercase)
            if name[0].islower():
                # Allow common lowercase helpers that aren't part of public API
                allowed_lowercase = {"main", "setup", "teardown"}
                if name not in allowed_lowercase:
                    issues.append(
                        f"Line {node.lineno}: Public function '{name}' should use "
                        f"CamelCase (e.g., '{name.title().replace('_', '')}') "
                        "to match derive API style"
                    )

    return issues


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Only check Write/Edit on Python files
    if tool_name not in ("Write", "Edit") or not file_path.endswith(".py"):
        sys.exit(0)

    # Get the content being written/edited
    if tool_name == "Write":
        content = tool_input.get("content", "")
    else:  # Edit
        new_string = tool_input.get("new_string", "")
        # For Edit, we only have the new_string, not full file
        # Run limited checks on the snippet
        content = new_string

    if not content:
        sys.exit(0)

    all_issues = []

    # Run all checks
    all_issues.extend(check_imports_in_functions(file_path, content))
    all_issues.extend(check_sympy_direct_usage(file_path, content))
    all_issues.extend(check_nested_loops(content))
    all_issues.extend(check_special_characters(content))
    all_issues.extend(check_api_naming(file_path, content))

    # Test modification warning (non-blocking)
    test_warnings = check_test_modification(file_path)

    if all_issues:
        output_lines = ["Code Standards Violations Found:"]
        output_lines.extend(f"  - {issue}" for issue in all_issues)
        print("\n".join(output_lines), file=sys.stderr)
        sys.exit(2)  # Block the action

    if test_warnings:
        # Warn but don't block
        print(test_warnings[0], file=sys.stderr)
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
