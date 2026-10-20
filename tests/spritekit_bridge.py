"""Native-render parity, immutable publishing and rejection coverage for SpriteKit v1."""
import hashlib
import json
import pathlib
import shutil
import sys
import tempfile
from PIL import Image
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from rigtools.client import AgentClient
from rigtools.spritekit import export_spritekit

with tempfile.TemporaryDirectory() as tmp:
    root=pathlib.Path(tmp);project=root/'fixture.rig2d';recipe=root/'recipe.json';config=root/'config.json'
    # Explicit source orientation marker and non-central anchor.
    marker=Image.new('RGBA',(40,60),'red')
    for y in range(30,60):
        for x in range(40): marker.putpixel((x,y),(0,0,255,255))
    marker.save(root/'marker.png')
    recipe.write_text(json.dumps({'schemaVersion':1,'name':'parity','duration':1,'bones':[{'id':'root','visible':False,'length':1},{'id':'marker','parent':'root','image':'marker.png','length':100,'width':65,'x':-25,'y':10,'pivotX':.3,'pivotY':.8,'imageOffsetX':11,'imageOffsetY':-9}], 'frames':[{'time':0,'pose':{}},{'time':.5,'pose':{'marker':12}},{'time':1,'pose':{}}]}))
    cfg={'schemaVersion':1,'id':'fixture','licenseRecordID':'fixture-original','renderScale':.5,'canvasPivot':[120,245],'fps':4,'maxAtlas':256,'clips':[{'name':'idle','start':0,'end':1,'loop':True,'events':[{'name':'blink','time':.25}]}]}
    def write_config(value): config.write_text(json.dumps(value))
    def rejected(client, value, name):
        write_config(value);dest=root/name
        try: export_spritekit(client,project,config,dest)
        except (ValueError,RuntimeError): pass
        else: raise AssertionError('Expected rejection: '+name)
        assert not dest.exists(), name
    with AgentClient() as client:
        client.request('apply_recipe',project,recipe=str(recipe))
        write_config(cfg);dest=root/'package'
        manifest=export_spritekit(client,project,config,dest)
        assert set(p.name for p in dest.iterdir())=={'atlas.png','manifest.json'}
        atlas=Image.open(dest/'atlas.png').convert('RGBA')
        assert manifest['sourceRevision']==hashlib.sha256(project.read_bytes()).hexdigest()
        assert manifest['metrics']['rgba8BaseBytes']==atlas.width*atlas.height*4
        for frame in manifest['frames']:
            native=root/'native.png'
            client.request('render',project,time=frame['sourceTime'],output=str(native),expected_revision=manifest['sourceRevision'])
            expected=Image.open(native).convert('RGBA').resize(tuple(frame['originalSize']),Image.Resampling.LANCZOS)
            x,y,w,h=frame['rect'];crop=atlas.crop((x,y,x+w,y+h))
            restored=Image.new('RGBA',expected.size);restored.paste(crop,tuple(frame['trimOffset']))
            assert restored.tobytes()==expected.tobytes(), frame['name']
            assert frame['pivot']==[60,122.5]
            assert atlas.getpixel((x-1,y))==atlas.getpixel((x,y))
            assert atlas.getpixel((x,y-2))==atlas.getpixel((x,y))
        assert len(manifest['frames'])==4
        moved=root/'elsewhere';shutil.copytree(dest,moved)
        assert hashlib.sha256((moved/'atlas.png').read_bytes()).hexdigest()==manifest['atlasFiles'][0]['sha256']
        before=(dest/'manifest.json').read_bytes()
        try: export_spritekit(client,project,config,dest)
        except ValueError: pass
        else: raise AssertionError('Overwrite allowed')
        assert (dest/'manifest.json').read_bytes()==before
        rejected(client,{**cfg,'fps':True},'bad-fps')
        rejected(client,{**cfg,'renderScale':2},'upscale')
        rejected(client,{**cfg,'clips':[{'name':'bad','start':0,'end':.3,'loop':False}]},'fractional-frames')
        rejected(client,{**cfg,'clips':[{'name':'bad','start':0,'end':.5,'loop':True}]},'bad-loop')
        rejected(client,{**cfg,'canvasPivot':[float('nan'),0]},'nan-pivot')
        rejected(client,{**cfg,'clips':[{'name':'bad','start':0,'end':1,'events':[{'name':'x','time':1}]}]},'end-event')
        # Force overflow using a larger source crop and full-size frames.
        rev=client.request('inspect',project)['revision']
        client.request('set_bone',project,bone='marker',values={'width':280,'length':280,'pivotX':.5,'pivotY':.5,'x':0,'y':0},expected_revision=rev)
        rejected(client,{**cfg,'renderScale':1},'overflow')
        rev=client.request('inspect',project)['revision']
        client.request('set_bone',project,bone='marker',values={'length':600},expected_revision=rev)
        rejected(client,cfg,'clipped')
    # Simulate a source edit immediately after the last frame rendered.
    with AgentClient() as native:
        native.request('set_bone',project,bone='marker',values={'length':100,'width':65,'x':-25,'y':10,'pivotX':.3,'pivotY':.8})
        class RacingClient:
            def __init__(self): self.renders=0
            def request(self,command,source,**values):
                result=native.request(command,source,**values)
                if command=='render':
                    self.renders+=1
                    if self.renders==4: native.request('set_bone',source,bone='marker',values={'angle':1})
                return result
        write_config(cfg)
        try: export_spritekit(RacingClient(),project,config,root/'racing')
        except ValueError: pass
        else: raise AssertionError('Mid-job changed source accepted')
        assert not (root/'racing').exists()
    # A racing edit must fail even if the API transport did not notice it yet.
    class ChangedClient:
        def request(self,command,source,**values):
            if command=='inspect': return {'revision':'0'*64,'duration':1}
            return {}
    write_config(cfg)
    try: export_spritekit(ChangedClient(),project,config,root/'changed')
    except ValueError: pass
    else: raise AssertionError('Changed revision accepted')
    assert not (root/'changed').exists()
print('PASS: 4 native frame parity checks, pivot, Y orientation, extrusion, relocation, immutability and rejection gates')
