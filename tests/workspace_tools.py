"""Run native viewport, clipping, rig-axis and slider behavior checks."""
import pathlib
import subprocess
import tempfile

root = pathlib.Path(__file__).resolve().parents[1]
sources = sorted(path for path in (root / 'Sources/RigAndBone2D').glob('*.swift') if path.name != 'main.swift')
with tempfile.TemporaryDirectory(prefix='rig-workspace-check-') as directory:
    binary = pathlib.Path(directory) / 'workspace-tools'
    subprocess.run(['swiftc', '-parse-as-library', *map(str, sources),
                    str(root / 'tests/workspace_tools.swift'), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
