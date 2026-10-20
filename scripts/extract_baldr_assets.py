#!/usr/bin/env python3
"""Extract source sprite rectangles; preserve source pixels and alpha."""
from PIL import Image, ImageDraw
from pathlib import Path
import hashlib, json
root=Path(__file__).resolve().parents[1]
source=root/'spriters-resource/Mobile - Fire Emblem_ Heroes - Map Characters_ Heroes - Baldr.png'
out=root/'examples/baldr/assets';out.mkdir(parents=True,exist_ok=True)
im=Image.open(source).convert('RGBA')
rects={
'head':(16,32,112,104),
'chest':(416,8,472,56),
'waist':(424,80,472,120),
'upper_arm':(16,144,48,192),
'forearm':(80,144,112,192),
'thigh':(272,144,304,200),
'shin':(336,144,368,192),
'hand':(16,240,48,280),
'shoulder':(232,288,272,344),
'wing':(320,216,352,320),
'wing_base':(416,280,512,328),
'cape':(528,0,664,96),
'halo':(264,384,376,508),
}
manifest={'source':str(source.relative_to(root)),'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'parts':{}}
for name,rect in rects.items():
    part=im.crop(rect);bounds=part.getchannel('A').getbbox()
    if not bounds:raise ValueError(name)
    part=part.crop(bounds);part.save(out/f'{name}.png')
    manifest['parts'][name]={'rectangle':list(rect),'alphaBounds':list(bounds),'size':list(part.size)}
for name in ['wing','wing_base']:
    Image.open(out/f'{name}.png').transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(out/f'{name}_mirrored.png')
    manifest['parts'][name+'_mirrored']={'derivedFrom':name,'operation':'horizontal flip'}
Image.new('RGBA',(1,1)).save(out/'root.png')
(out.parent/'asset-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
contact=Image.new('RGB',(800,800),'#242b3a');draw=ImageDraw.Draw(contact)
for i,name in enumerate(rects):
    part=Image.open(out/f'{name}.png');part.thumbnail((170,130))
    x=(i%4)*200;y=(i//4)*200
    contact.paste(part,(x+15,y+30),part);draw.text((x+12,y+10),name,fill='white')
contact.save(out.parent/'asset-catalog.png')
print(json.dumps(manifest['parts'],indent=2))
