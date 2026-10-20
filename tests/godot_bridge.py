"""Native import, compact handoff, pose equivalence, and gameplay regression."""
import json
import math
import pathlib
import subprocess
import sys
import tempfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from rigtools.client import AgentClient, ROOT
from rigtools.godot import export_godot, run_godot

source=ROOT/'examples/rebuilt/Inquisitor-combat.rig2d'
config=ROOT/'recipes/inquisitor.godot.json'
with tempfile.TemporaryDirectory() as tmp, AgentClient() as client:
    tmp=pathlib.Path(tmp)
    report=export_godot(client,source,config,tmp/'character')
    assert set(p.name for p in (tmp/'character').iterdir())=={'atlas.png','visual.tscn','manifest.json'}
    assert report['metrics']['uniqueRegions']<report['metrics']['visibleSprites']
    assert report['metrics']['rgba8BaseBytes']<report['metrics']['sourcePartRGBA8Bytes']
    try:
        export_godot(client,source,config,tmp/'character')
        raise AssertionError('Existing destination overwritten')
    except ValueError: pass
    snapshots=[]
    inspected=client.request('inspect',source)
    bones=inspected['bones']
    for t in (0,0.35,0.7,0.95,1,1.1,1.3,1.5,1.85,2,2.6,3):
        angles=client.request('sample',source,time=t)['angles']
        world=[];expected={}
        for i,b in enumerate(bones):
            parent=b.get('parent')
            px,py,pa=world[parent] if parent is not None else (0,0,0)
            x=px+math.cos(pa)*b['x']-math.sin(pa)*b['y']
            y=py+math.sin(pa)*b['x']+math.cos(pa)*b['y']
            a=pa+math.radians(angles[i]);world.append((x,y,a))
            if b['id'] in report['boneIds']: expected[b['id']]=[x,y,a]
        snapshots.append({'time':t,'bones':expected})
    (tmp/'expected.json').write_text(json.dumps(snapshots))
    # Test the delivered scene at a different res:// location than the staging project.
    project=tmp/'game';project.mkdir()
    import shutil
    shutil.copytree(ROOT/'examples/godot-demo/gameplay',project/'gameplay')
    shutil.copy(ROOT/'examples/godot-demo/project.godot',project/'project.godot')
    destination=project/'generated/characters/inquisitor'
    shutil.copytree(tmp/'character',destination)
    run_godot('godot',project,'--editor','--import')
    output=run_godot('godot',project,'--script',str(ROOT/'tools/godot/test_handoff.gd'),'--',str(tmp/'expected.json'))
    print(output)
    assert '"ok":true' in output
    print('PASS: native relocation, shared atlas, 12 sampled world poses, hit once and out-of-range miss')
