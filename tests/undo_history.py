"""Compile the real editor with a native AppKit history behavior harness."""
import pathlib
import subprocess
import tempfile

root = pathlib.Path(__file__).resolve().parents[1]
sources = sorted(path for path in (root / 'Sources/RigAndBone2D').glob('*.swift') if path.name != 'main.swift')
with tempfile.TemporaryDirectory(prefix='rig-undo-check-') as directory:
    binary = pathlib.Path(directory) / 'undo-history'
    subprocess.run(['swiftc', '-parse-as-library', *map(str, sources),
                    str(root / 'tests/undo_history.swift'), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
