#!/usr/bin/env python3
"""Thin JSON bridge: stdin JSONL or a single JSON request argument."""
import json
import pathlib
import subprocess
import sys
root = pathlib.Path(__file__).resolve().parents[1]
binary = root / 'dist/RigAndBone2D.app/Contents/MacOS/RigAndBone2D'
if not binary.exists():
    sys.exit('Build first: ./scripts/build-app.sh')
if len(sys.argv) == 2:
    result = subprocess.run([str(binary), '--agent'], input=sys.argv[1] + '\n', text=True, capture_output=True)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    try:
        success = json.loads(result.stdout).get("ok", False)
    except ValueError:
        success = False
    sys.exit(result.returncode if result.returncode else (0 if success else 1))
sys.exit(subprocess.call([str(binary), '--agent']))
