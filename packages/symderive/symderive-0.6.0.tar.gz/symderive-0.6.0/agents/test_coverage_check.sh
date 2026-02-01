#!/bin/bash
#
# Test Coverage Validator Hook
# Warns when source files are modified without corresponding test files.
#

set -e

# Read JSON from stdin
INPUT=$(cat)

# Extract values using Python (more portable than jq)
eval "$(echo "$INPUT" | python3 -c "
import json
import sys
data = json.load(sys.stdin)
print(f'TOOL_NAME=\"{data.get(\"tool_name\", \"\")}\"')
print(f'FILE_PATH=\"{data.get(\"tool_input\", {}).get(\"file_path\", \"\")}\"')
")"

# Only check source file modifications
if [[ ! "$FILE_PATH" =~ src/derive/.+\.py$ ]]; then
    exit 0
fi

if [[ "$TOOL_NAME" != "Write" && "$TOOL_NAME" != "Edit" ]]; then
    exit 0
fi

# Skip __init__.py files
if [[ "$FILE_PATH" =~ __init__\.py$ ]]; then
    exit 0
fi

# Extract module name from path
# e.g., src/derive/calculus/differentiation.py -> calculus
MODULE=$(echo "$FILE_PATH" | sed -E 's|.*/src/derive/([^/]+)/.*|\1|')

# Check for test file
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
TEST_FILE="$PROJECT_DIR/tests/test_${MODULE}.py"

if [[ ! -f "$TEST_FILE" ]]; then
    echo "WARNING: No test file found for module '$MODULE'" >&2
    echo "Expected: tests/test_${MODULE}.py" >&2
    echo "Consider adding tests for new functionality." >&2
fi

exit 0
