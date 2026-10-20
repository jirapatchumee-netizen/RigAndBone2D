"""Immutable native Godot handoff: one atlas, shared textures, sparse angle tracks."""
import base64
import hashlib
import io
import json
import math
import pathlib
import shutil
import subprocess
import tempfile
from PIL import Image, ImageOps
from .client import ROOT


def run_godot(binary, project, *args):
    result = subprocess.run([binary, '--headless', '--path', str(project), *args],
                            capture_output=True, text=True, timeout=120)
    if result.returncode or 'SCRIPT ERROR:' in result.stderr or 'ERROR:' in result.stderr:
        raise ValueError(result.stdout + result.stderr)
    return result.stdout


def export_godot(client, source, config_path, output, binary='godot'):
    source, output = pathlib.Path(source).resolve(), pathlib.Path(output).resolve()
    if output.exists():
        raise ValueError('Destination must be a new directory')
    config = json.loads(pathlib.Path(config_path).read_text())
    if config.get('schemaVersion') != 1 or set(config) - {'schemaVersion', 'id', 'exclude', 'hidden', 'density', 'maxAtlas', 'clips', 'sockets'}:
        raise ValueError('Invalid Godot handoff config')
    density = config.get('density', 2)
    limit = config.get('maxAtlas', 2048)
    if not isinstance(density, (float, int)) or not math.isfinite(density) or not 1 <= density <= 4:
        raise ValueError('density must be 1..4')
    if limit not in (256, 512, 1024, 2048, 4096):
        raise ValueError('Unsupported atlas limit')
    snapshot = client.request('inspect', source)
    client.request('validate', source, expected_revision=snapshot['revision'])
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() != snapshot['revision']:
        raise ValueError('Source revision changed')
    project = json.loads(data)
    bones = project['bones']
    ids = [b.get('id', 'bone-'+str(i)) for i,b in enumerate(bones)]
    excluded = set(config.get('exclude', []))
    hidden = set(config.get('hidden', []))
    if (excluded | hidden) - set(ids):
        raise ValueError('Unknown exclude/hidden bone ID')
    kept, parts, unique = [], [], {}
    source_pixels = 0
    for i,b in enumerate(bones):
        parent = b.get('parent')
        if ids[i] in excluded or (parent is not None and ids[parent] in excluded):
            excluded.add(ids[i]); continue
        bone = dict(b); bone.pop('image', None)
        bone['id'] = ids[i]; bone['parent'] = ids[parent] if parent is not None else None
        bone['sourceIndex'] = i
        if b.get('visible', True) and ids[i] not in hidden:
            if not b.get('image'):
                raise ValueError('Visible primitive needs artwork or exclusion: '+ids[i])
            image = Image.open(io.BytesIO(base64.b64decode(b['image']))).convert('RGBA')
            source_pixels += image.width * image.height
            bbox = image.getchannel('A').getbbox()
            if bbox:
                sx,sy = b['width']/image.width,b['length']/image.height
                crop = image.crop(bbox)
                size = (max(1,min(crop.width,math.ceil(crop.width*sx*density))), max(1,min(crop.height,math.ceil(crop.height*sy*density))))
                crop = crop.resize(size, Image.Resampling.LANCZOS)
                flipped = ImageOps.mirror(crop)
                digest = hashlib.sha256(crop.tobytes()+str(size).encode()).hexdigest()
                mirror_digest = hashlib.sha256(flipped.tobytes()+str(size).encode()).hexdigest()
                mirrored = digest not in unique and mirror_digest in unique
                key = mirror_digest if mirrored else digest
                unique.setdefault(key, crop)
                bone['art'] = {'key':key, 'mirror':mirrored,
                    'size':[(bbox[2]-bbox[0])*sx,(bbox[3]-bbox[1])*sy],
                    'offset':[bbox[0]*sx-b['width']*b['pivotX']+(b.get('imageOffsetX') or 0),
                              bbox[1]*sy-b['length']*b['pivotY']+(b.get('imageOffsetY') or 0)]}
                parts.append(bone['art'])
        kept.append(bone)
    if not unique:
        raise ValueError('No visible artwork')
    # Deterministic shelf packing; two extruded pixels prevent filtering bleed.
    atlas_width = 256
    while True:
        x=y=row=0; regions={}
        for key,image in sorted(unique.items(), key=lambda kv:(-kv[1].height,kv[0])):
            w,h=image.width+4,image.height+4
            if w>atlas_width: break
            if x+w>atlas_width: x=0;y+=row;row=0
            regions[key]=[x+2,y+2,image.width,image.height]
            x+=w;row=max(row,h)
        height=y+row
        if len(regions)==len(unique) and height<=limit: break
        atlas_width*=2
        if atlas_width>limit: raise ValueError('Atlas budget exceeded; lower density or split character')
    for rank,bone in enumerate(sorted(kept,key=lambda b:(b['layer'],b['sourceIndex']))):
        bone['drawOrder'] = rank
    atlas=Image.new('RGBA',(atlas_width,height))
    for key,image in unique.items():
        x,y,w,h=regions[key]
        atlas.paste(image,(x,y))
        for d in (1,2):
            atlas.paste(image.crop((0,0,1,h)).resize((1,h)),(x-d,y))
            atlas.paste(image.crop((w-1,0,w,h)),(x+w-1+d,y))
            atlas.paste(atlas.crop((x-2,y,x+w+2,y+1)),(x-2,y-d))
            atlas.paste(atlas.crop((x-2,y+h-1,x+w+2,y+h)),(x-2,y+h-1+d))
    for part in parts: part['region']=regions[part.pop('key')]
    clips=[]; names=set()
    for spec in config['clips']:
        if set(spec)-{'name','start','end','loop','events'} or spec['name'] in names:
            raise ValueError('Invalid/duplicate clip')
        names.add(spec['name'])
        start,end=spec['start'],spec['end']
        if not 0<=start<end<=project['duration']: raise ValueError('Invalid clip range')
        times=sorted({start,end}|{f['time'] for f in project['frames'] if start<f['time']<end})
        poses=[client.request('sample',source,time=t,expected_revision=snapshot['revision'])['angles'] for t in times]
        if not isinstance(spec.get('loop',False), bool): raise ValueError('loop must be boolean')
        if spec.get('loop',False) and any(abs(poses[0][b['sourceIndex']]-poses[-1][b['sourceIndex']])>1e-6 for b in kept):
            raise ValueError('Loop endpoints differ: '+spec['name'])
        events=spec.get('events',[])
        if any(set(e)!={'name','time'} or not isinstance(e['name'],str) or not 0<=e['time']<=end-start for e in events):
            raise ValueError('Invalid clip event')
        if len({e['name'] for e in events}) != len(events): raise ValueError('Duplicate event name')
        clips.append({'name':spec['name'],'length':end-start,'loop':spec.get('loop',False),'events':events,
                      'times':[t-start for t in times],'poses':[[p[b['sourceIndex']] for b in kept] for p in poses]})
    sockets=config.get('sockets',{})
    if set(sockets.values())-set(b['id'] for b in kept): raise ValueError('Unknown socket bone')
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent,prefix='.godot-build-') as temporary:
        staging=pathlib.Path(temporary)
        package=staging/'character';package.mkdir()
        atlas.save(package/'atlas.png',optimize=True)
        (staging/'project.godot').write_text('[application]\nconfig/name="Rig handoff"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\ntextures/default_filters/use_nearest_mipmap_filter=false\n')
        payload={'bones':kept,'clips':clips,'sockets':sockets}
        (staging/'payload.json').write_text(json.dumps(payload))
        shutil.copy(ROOT/'tools/godot/export_scene.gd',staging/'export_scene.gd')
        run_godot(binary,staging,'--editor','--import')
        run_godot(binary,staging,'--script','export_scene.gd')
        scene_path = package/'visual.tscn'
        scene_path.write_text(scene_path.read_text().replace('res://character/atlas.png', 'atlas.png'))
        report={'schemaVersion':1,'id':config['id'],'sourceRevision':snapshot['revision'],
            'godotVersion':subprocess.check_output([binary,'--version'],text=True).strip(),
            'scene':'visual.tscn','atlas':'atlas.png','coordinates':'pixels, Y down, radians in Godot',
            'boneIds':[b['id'] for b in kept],'sockets':sockets,
            'clips':[{k:c[k] for k in ('name','length','loop','events')} for c in clips],
            'metrics':{'visibleSprites':len(parts),'uniqueRegions':len(unique),'atlasSize':list(atlas.size),
                'rgba8BaseBytes':atlas.width*atlas.height*4,'sourcePartRGBA8Bytes':source_pixels*4,
                'atlasPNGBytes':(package/'atlas.png').stat().st_size,
                'sceneBytes':(package/'visual.tscn').stat().st_size},
            'visualReviewRequired':True,'runtimeFiles':['atlas.png','visual.tscn']}
        (package/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
        # Publish only runtime resources + handoff metadata, never sources or previews.
        shutil.copytree(package,output,ignore=shutil.ignore_patterns('*.import','*.uid'))
    return report
