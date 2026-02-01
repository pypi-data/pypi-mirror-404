# Claude Code Agents

This directory contains enforcement agents (hooks) for Claude Code that automatically validate code against the project's coding standards defined in `CLAUDE.md`.

## Available Agents

### code_standards_enforcer.py

Validates Python code on every `Write` or `Edit` operation:

| Check | Description | Blocking |
|-------|-------------|----------|
| **Imports in functions** | Detects imports inside function bodies | Yes |
| **SymPy direct usage** | Flags `sympy.simplify()` etc. in `src/derive/` | Yes |
| **Nested for loops** | Suggests `itertools.product()` | Yes |
| **Special characters** | Rejects emojis and non-ASCII | Yes |
| **API naming** | Public functions must use CamelCase like `Symbol()` | Yes |
| **Test modifications** | Warns when test files are changed | No (warning) |

### test_coverage_check.sh

Warns when source files in `src/derive/` are modified without a corresponding test file in `tests/`.

## Setup

These agents are automatically configured via `.claude/settings.json`. When you open this project with Claude Code, the hooks are active.

### Manual Setup (for other projects)

1. Copy the agents to your project:
   ```bash
   mkdir -p your-project/agents
   cp code_standards_enforcer.py test_coverage_check.sh your-project/agents/
   chmod +x your-project/agents/*.py your-project/agents/*.sh
   ```

2. Create `.claude/settings.json`:
   ```json
   {
     "hooks": {
       "PostToolUse": [
         {
           "matcher": "Write|Edit",
           "hooks": [
             {
               "type": "command",
               "command": "\"$CLAUDE_PROJECT_DIR\"/agents/code_standards_enforcer.py",
               "timeout": 15000
             },
             {
               "type": "command",
               "command": "\"$CLAUDE_PROJECT_DIR\"/agents/test_coverage_check.sh",
               "timeout": 10000
             }
           ]
         }
       ]
     }
   }
   ```

3. Customize the checks in `code_standards_enforcer.py` for your project's conventions.

## How Hooks Work

Claude Code hooks receive JSON input via stdin with this structure:

```json
{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.py",
    "content": "..."
  }
}
```

Exit codes control behavior:
- **Exit 0**: Action proceeds
- **Exit 2**: Action blocked, stderr shown to Claude

## Customization

To add new checks, edit `code_standards_enforcer.py`:

1. Add a new check function following the pattern:
   ```python
   def check_something(content: str) -> list[str]:
       issues = []
       # Your logic here
       return issues
   ```

2. Call it in `main()`:
   ```python
   all_issues.extend(check_something(content))
   ```
