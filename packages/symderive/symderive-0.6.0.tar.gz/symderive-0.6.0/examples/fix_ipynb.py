#!/usr/bin/env python3
"""Fix marimo-exported ipynb files for Jupyter compatibility."""

import json
import re
from pathlib import Path


def fix_notebook(notebook_path: Path) -> None:
    """Fix a notebook for Jupyter compatibility."""
    with open(notebook_path) as f:
        nb = json.load(f)

    first_code_cell = True

    for cell in nb['cells']:
        if cell['cell_type'] != 'code':
            continue

        source = cell.get('source', [])
        if not source:
            continue
        if isinstance(source, str):
            source = [source]

        # Join source
        source_str = ''.join(source)

        # Remove marimo imports
        if 'import marimo as mo' in source_str:
            lines = source_str.split('\n')
            lines = [l for l in lines if 'import marimo as mo' not in l]
            source_str = '\n'.join(lines)

        # Handle mo.md() calls - remove them entirely and just keep the computations
        # The mo.md() with f-strings doesn't work in Jupyter
        if 'mo.md(' in source_str:
            # Find and remove the mo.md(...) block
            # Pattern matches mo.md(f"""...""") or mo.md(r"""...""") etc
            pattern = r'mo\.md\((?:f|r)?(?:"""|\'\'\').*?(?:"""|\'\'\')(?:\s*\))'
            source_str = re.sub(pattern, '', source_str, flags=re.DOTALL)
            # Clean up any trailing whitespace/newlines
            source_str = source_str.rstrip()

        # Add matplotlib inline to first code cell
        if first_code_cell:
            if '%matplotlib inline' not in source_str:
                source_str = '%matplotlib inline\nfrom IPython.display import display\n' + source_str
            first_code_cell = False

        # Fix tuple returns at end of cell - convert to display()
        lines = source_str.rstrip().split('\n')
        if lines:
            last_line = lines[-1].strip()
            # Check if last line is a bare tuple
            if (last_line.startswith('(') and last_line.endswith(')') and
                '=' not in last_line and
                not any(last_line.startswith(f) for f in ['print(', 'display(', 'return('])):
                inner = last_line[1:-1]
                lines[-1] = f'display({inner})'
                source_str = '\n'.join(lines)

        # Convert back to list format
        lines = source_str.split('\n')
        cell['source'] = [l + '\n' for l in lines[:-1]] + [lines[-1]] if lines else []

    with open(notebook_path, 'w') as f:
        json.dump(nb, f, indent=1)

    print(f"  Fixed: {notebook_path.name}")


def main():
    rendered = Path('examples/rendered')
    for nb_path in sorted(rendered.glob('*.ipynb')):
        fix_notebook(nb_path)


if __name__ == '__main__':
    main()
