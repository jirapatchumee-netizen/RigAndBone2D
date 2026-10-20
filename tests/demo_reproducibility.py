"""Both original demos must rebuild from data and render identically."""
import hashlib
import json
import pathlib
import sys
import tempfile
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from rigtools.client import AgentClient
from rigtools.assets import prepare_assets
from rigtools.quality import render_preview

results=[]
with tempfile.TemporaryDirectory() as temp:
    temp=pathlib.Path(temp)
    with AgentClient() as schema_client:
        schema=schema_client.request('get_schema')
    assert schema==json.loads((ROOT/'schemas/recipe-v1.schema.json').read_text())
    for label,folder,file in [('baldr','baldr','Baldr.rig2d'),('inquisitor-combat','inquisitor','Inquisitor-combat.rig2d')]:
        job=temp/label;job.mkdir()
        assets=job/'assets'
        source_manifest=ROOT/'recipes'/f'{folder}.assets.json'
        prepared=prepare_assets(source_manifest,assets)
        for png in assets.glob('*.png'):
            with Image.open(png) as rebuilt,Image.open(ROOT/'examples'/folder/'assets'/png.name) as original:
                assert rebuilt.convert('RGBA').tobytes()==original.convert('RGBA').tobytes(),png.name
        recipe=json.loads((ROOT/'recipes'/f'{label}.rigrecipe.json').read_text())
        for bone in recipe['bones']:
            if 'image' in bone:bone['image']='assets/'+pathlib.Path(bone['image']).name
        recipe_path=job/'recipe.json';recipe_path.write_text(json.dumps(recipe))
        rebuilt=job/file;original=ROOT/'examples'/folder/file
        original_hash=hashlib.sha256(original.read_bytes()).hexdigest()
        with AgentClient() as client:
            result=client.request('apply_recipe',rebuilt,recipe=str(recipe_path))
            assert len(client.transcript)==1,'Creation should require one request'
            original_info=client.request('inspect',original)
            rebuilt_info=client.request('inspect',rebuilt)
            assert [{k:v for k,v in f.items() if k != 'label'} for f in rebuilt_info['frames']]==original_info['frames']
            assert all(f.get('label') for f in rebuilt_info['frames'])
            assert len(rebuilt_info['bones'])==len(original_info['bones'])
            for index,time in enumerate([0,.35,.7,.95,1,1.1,1.3,1.5,2,2.2,2.6,3]):
                a,b=job/f'original-{index}.png',job/f'rebuilt-{index}.png'
                client.request('render',original,time=time,output=str(a))
                client.request('render',rebuilt,time=time,output=str(b))
                with Image.open(a) as before,Image.open(b) as after:
                    assert before.convert('RGBA').tobytes()==after.convert('RGBA').tobytes(),(label,time)
            report=render_preview(client,rebuilt,job/'preview',fps=20)
            assert report['seamlessLoop'] and not report['warnings'] and not report['clippedFrames']
            assert report['frameCount']==60
            assert hashlib.sha256(original.read_bytes()).hexdigest()==original_hash
            results.append({'demo':label,'boneCount':result['bones'],'keyframeCount':result['keyframes'],
                            'creationRequests':1,'matchingSampledPoses':12,'checkedPreviewFrames':60,
                            'assetCount':prepared['partCount'],'originalProjectUnchanged':True})
report_path=ROOT/'reports/demo-reproducibility.json'
report_path.parent.mkdir(exist_ok=True)
report_path.write_text(json.dumps(results,indent=2)+'\n')
print('PASS: both demos rebuilt through one-request recipes; all extracted assets and 24 sampled pose images match originals; 120 preview frames pass bounds and loop checks')
