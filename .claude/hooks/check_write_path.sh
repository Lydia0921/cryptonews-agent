#!/bin/bash
python3 -c "
import json, sys, os

PROJECT_DIR = '/Users/lydiak/Projects/small_project'

try:
    data = json.load(sys.stdin)
    file_path = data.get('tool_input', {}).get('file_path', '')
except Exception:
    sys.exit(0)

if not file_path:
    sys.exit(0)

real_path = os.path.realpath(file_path)
real_project = os.path.realpath(PROJECT_DIR)

if not (real_path == real_project or real_path.startswith(real_project + os.sep)):
    print(f'⚠️ BLOCKED: Attempt to write outside project directory: {file_path}', file=sys.stderr)
    sys.exit(2)

sys.exit(0)
"
