"""Integration test of the actual shipping binary and project persistence."""
import json
import pathlib
import subprocess
import tempfile
root = pathlib.Path(__file__).resolve().parents[1]
binary = root / 'dist/RigAndBone2D.app/Contents/MacOS/RigAndBone2D'
with tempfile.TemporaryDirectory() as directory:
    project = str(pathlib.Path(directory) / 'test.rig2d')
    image = str(pathlib.Path(directory) / 'pose.png')
    sheet = str(pathlib.Path(directory) / 'sheet.png')
    process = subprocess.Popen([str(binary), '--agent'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    def request(command, **values):
        process.stdin.write(json.dumps(dict(command=command, project=project, **values)) + '\n')
        process.stdin.flush()
        return json.loads(process.stdout.readline())
    assert request('capabilities')['result']['protocolVersion'] == 1
    assert request('new')['ok']
    assert not request('new')['ok'], 'must protect existing files'
    inspected = request('inspect')['result']
    old_revision = inspected['revision']
    head = inspected['worldBones'][2]
    assert abs(head['origin'][0]) < 1e-8 and abs(head['origin'][1] + 85) < 1e-8
    assert abs(head['end'][1] + 143) < 1e-8, 'parent transform must keep child attached' 
    original = pathlib.Path(project).read_bytes()
    assert not request('set_bone', bone=1, values={'parent': 10})['ok']
    assert pathlib.Path(project).read_bytes() == original, 'invalid edit must not write'
    assert request('set_bone', bone=5, values={'angle': 80})['ok']
    assert not request('set_bone', bone=5, values={'angle': 10}, expected_revision=old_revision)['ok']
    assert not request('set_duration', duration=1)['ok'], 'must not truncate existing frames'
    assert request('keyframe', time=0.5)['ok']
    sample = request('sample', time=0.5)
    assert sample['result']['angles'][5] == 80
    assert request('add_bone', bone=6, name='Accessory')['ok']
    assert request('validate')['result']['bones'] == 13
    assert request('render', output=image, time=0.5)['ok']
    assert pathlib.Path(image).read_bytes().startswith(b'\x89PNG')
    assert request('import_image', bone=12, image=image)['ok']
    assert request('inspect')['result']['bones'][12]['imageBytes'] > 0
    assert request('export_sheet', output=sheet)['result']['frames'] == 24
    assert pathlib.Path(sheet).stat().st_size > 1000
    assert not request('keyframe', time=0.1, angles=[0])['ok']
    assert request('validate')['ok']
    process.stdin.close()
    assert process.wait(timeout=10) == 0
print('PASS: JSONL protocol, file protection, hierarchy validation, persisted edits, keyframes, image import, PNG render, sprite sheet, recovery after invalid input')
