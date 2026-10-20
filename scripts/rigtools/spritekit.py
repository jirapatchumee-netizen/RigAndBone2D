"""Pinned native renders -> immutable trimmed SpriteKit atlas package v1."""
import hashlib
import json
import math
import pathlib
import re
import tempfile
from PIL import Image


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def export_spritekit(client, source, config_path, output):
    source, output = pathlib.Path(source).resolve(), pathlib.Path(output).resolve()
    if output.exists():
        raise ValueError('Destination must be a new directory')
    config = json.loads(pathlib.Path(config_path).read_text())
    allowed = {'schemaVersion', 'id', 'licenseRecordID', 'renderScale', 'pixelsPerUnit', 'canvasPivot', 'maxAtlas', 'fps', 'clips'}
    if not isinstance(config, dict) or set(config) - allowed or type(config.get('schemaVersion')) is not int or config.get('schemaVersion') != 1:
        raise ValueError('Invalid SpriteKit config')
    for key in ('id', 'licenseRecordID'):
        if not isinstance(config.get(key), str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]{0,63}', config[key]):
            raise ValueError('Invalid ' + key)
    scale = config.get('renderScale', 0.5)
    density = config.get('pixelsPerUnit', 1)
    fps = config.get('fps', 15)
    limit = config.get('maxAtlas', 2048)
    pivot = config.get('canvasPivot', [192, 192])
    if not finite(scale) or not 0.25 <= scale <= 1 or abs(384*scale-round(384*scale)) > 1e-8:
        raise ValueError('renderScale must yield an integral canvas size in 96..384')
    if not finite(density) or not 0.5 <= density <= 4:
        raise ValueError('pixelsPerUnit must be 0.5..4')
    if type(fps) is not int or not 1 <= fps <= 30 or type(limit) is not int or limit not in (256,512,1024,2048):
        raise ValueError('Invalid fps or maxAtlas')
    if not isinstance(pivot, list) or len(pivot) != 2 or any(not finite(v) or not 0 <= v <= 384 for v in pivot):
        raise ValueError('Invalid canvasPivot')
    specs = config.get('clips')
    if not isinstance(specs, list) or not 1 <= len(specs) <= 32:
        raise ValueError('clips must contain 1..32 ranges')
    info = client.request('inspect', source)
    revision = info['revision']
    client.request('validate', source, expected_revision=revision)
    source_data = source.read_bytes()
    if hashlib.sha256(source_data).hexdigest() != revision:
        raise ValueError('Source revision changed')
    clips, names, total = [], set(), 0
    for spec in specs:
        if not isinstance(spec, dict) or set(spec) - {'name','start','end','loop','events'}:
            raise ValueError('Invalid clip fields')
        name, start, end = spec.get('name'), spec.get('start'), spec.get('end')
        if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,31}',name) or name in names:
            raise ValueError('Invalid/duplicate clip name')
        names.add(name)
        if not finite(start) or not finite(end) or not 0 <= start < end <= info['duration'] or type(spec.get('loop',False)) is not bool:
            raise ValueError('Invalid clip range/loop')
        count = round((end-start)*fps)
        if count < 1 or abs(count-(end-start)*fps) > 1e-7:
            raise ValueError('Clip length times fps must be an integer')
        total += count
        if total > 600:
            raise ValueError('Frame count budget exceeded')
        events = spec.get('events', [])
        if not isinstance(events, list) or any(not isinstance(e,dict) or set(e) != {'name','time'} or not isinstance(e['name'],str) or not e['name'] or not finite(e['time']) or not 0 <= e['time'] < end-start for e in events):
            raise ValueError('Invalid visual event')
        if len({e['name'] for e in events}) != len(events):
            raise ValueError('Duplicate visual event name')
        a = client.request('sample',source,time=start,expected_revision=revision)['angles']
        b = client.request('sample',source,time=end,expected_revision=revision)['angles']
        if spec.get('loop',False) and any(abs(x-y)>1e-6 for x,y in zip(a,b)):
            raise ValueError('Loop endpoints differ: '+name)
        clips.append({'name':name,'start':start,'length':end-start,'loop':spec.get('loop',False),
                      'frames':[], 'durations':[1/fps]*count, 'visualEvents':events})
    output.parent.mkdir(parents=True,exist_ok=True)
    # All renders and package writes stay in staging; failures never publish partial output.
    with tempfile.TemporaryDirectory(dir=output.parent,prefix='.spritekit-job-') as temporary:
        staging = pathlib.Path(temporary)
        frames, unique = [], {}
        for clip in clips:
            for i in range(len(clip['durations'])):
                raw = staging/'pose.png'
                t = clip['start'] + i/fps
                client.request('render',source,time=t,output=str(raw),expected_revision=revision)
                with Image.open(raw) as rendered:
                    image = rendered.convert('RGBA')
                box = image.getchannel('A').getbbox()
                if image.size != (384,384) or box is None:
                    raise ValueError('Unexpected/empty native frame')
                if box[0] <= 0 or box[1] <= 0 or box[2] >= 384 or box[3] >= 384:
                    raise ValueError('Native frame touches canvas edge; fix rig before export')
                size = round(384*scale)
                image = image.resize((size,size),Image.Resampling.LANCZOS)
                box = image.getchannel('A').getbbox()
                if box is None: raise ValueError('Empty downsampled frame')
                crop = image.crop(box)
                key = hashlib.sha256(str(crop.size).encode()+crop.tobytes()).hexdigest()
                unique.setdefault(key,crop)
                name = clip['name']+'-'+str(i).zfill(3)
                frames.append({'name':name,'key':key,'sourceTime':t,'originalSize':[size,size],
                               'trimOffset':list(box[:2]),'pivot':[v*scale for v in pivot]})
                clip['frames'].append(name)
        atlas_width = 256
        while True:
            x=y=row=0; regions={}
            for key,im in sorted(unique.items(),key=lambda item:(-item[1].height,item[0])):
                w,h=im.width+4,im.height+4
                if w > atlas_width: break
                if x+w > atlas_width: x=0;y+=row;row=0
                regions[key]=[x+2,y+2,im.width,im.height]
                x+=w;row=max(row,h)
            height=y+row
            if len(regions)==len(unique) and height <= limit: break
            atlas_width *= 2
            if atlas_width > limit: raise ValueError('Atlas budget exceeded')
        atlas=Image.new('RGBA',(atlas_width,height))
        for key,im in unique.items():
            x,y,w,h=regions[key];atlas.paste(im,(x,y))
            for d in (1,2):
                atlas.paste(im.crop((0,0,1,h)),(x-d,y))
                atlas.paste(im.crop((w-1,0,w,h)),(x+w-1+d,y))
                atlas.paste(atlas.crop((x-2,y,x+w+2,y+1)),(x-2,y-d))
                atlas.paste(atlas.crop((x-2,y+h-1,x+w+2,y+h)),(x-2,y+h-1+d))
        package=staging/'package';package.mkdir()
        atlas.save(package/'atlas.png',optimize=True)
        for frame in frames:
            frame['atlas']='atlas.png';frame['rect']=regions[frame.pop('key')]
        for clip in clips: clip.pop('start')
        atlas_bytes=(package/'atlas.png').read_bytes()
        manifest={'schemaVersion':1,'assetID':config['id'],'licenseRecordID':config['licenseRecordID'],
                  'sourceRevision':revision,'coordinateSystem':'pixels-top-left-y-down','pixelsPerUnit':density,
                  'atlasFiles':[{'file':'atlas.png','sha256':hashlib.sha256(atlas_bytes).hexdigest(),'size':[atlas_width,height]}],
                  'frames':frames,'clips':clips,'runtimeFiles':['atlas.png','manifest.json'],
                  'metrics':{'rgba8BaseBytes':atlas_width*height*4,'atlasPNGBytes':len(atlas_bytes),'uniqueRegions':len(unique),'frameCount':len(frames)},
                  'visualReviewRequired':True}
        (package/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        if hashlib.sha256(source.read_bytes()).hexdigest() != revision:
            raise ValueError('Source revision changed before publish')
        client.request('inspect',source,expected_revision=revision)
        if output.exists():
            raise ValueError('Destination was created by another writer')
        package.rename(output)
    return manifest
