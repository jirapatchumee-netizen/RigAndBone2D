#!/usr/bin/env python3
"""Extract original sprite components, excluding detached captions."""
from PIL import Image,ImageDraw,ImageFilter
from pathlib import Path
from collections import deque
import json,hashlib
root=Path(__file__).resolve().parents[1];out=root/'examples/inquisitor/assets';out.mkdir(parents=True,exist_ok=True)
source=root/'spriters-resource/825256925_1638955110962641_9009267157229036913_n.png'
im=Image.open(source).convert('RGBA')
rects={
'head_determined':(1450,56,1896,400),'head_shouting':(495,56,945,400),
'body':(60,442,440,718),'coat':(477,440,920,734),
'shoulder_left':(959,425,1197,687),'shoulder_right':(1230,425,1468,690),
'arm_left':(85,745,318,973),'legs':(500,759,808,973),
'boot_left':(951,777,1158,982),'boot_right':(1163,777,1369,982),
'hand_fist':(1565,782,1717,963),'hand_grasp':(1735,744,1883,964),
'mace_head':(22,996,282,1280),'chain':(590,1090,866,1236),'handle':(888,1063,1380,1280),
}
manifest={'source':str(source.relative_to(root)),'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'parts':{}}
for name,rect in rects.items():
    part=im.crop(rect);w,h=part.size;alpha=part.getchannel('A');pixels=alpha.load();visited=set();groups=[]
    for y in range(h):
        for x in range(w):
            if (x,y) in visited or pixels[x,y]<16:continue
            group=[];queue=deque([(x,y)]);visited.add((x,y))
            while queue:
                px,py=queue.popleft();group.append((px,py))
                for nx,ny in [(px-1,py),(px+1,py),(px,py-1),(px,py+1)]:
                    if 0<=nx<w and 0<=ny<h and (nx,ny) not in visited and pixels[nx,ny]>=16:
                        visited.add((nx,ny));queue.append((nx,ny))
            groups.append(group)
    main=max(groups,key=len);mask=Image.new('L',(w,h));mp=mask.load()
    for x,y in main:mp[x,y]=255
    mask=mask.filter(ImageFilter.MaxFilter(3))
    from PIL import ImageChops
    part.putalpha(ImageChops.multiply(alpha,mask));bounds=part.getchannel('A').getbbox();part=part.crop(bounds);part.save(out/f'{name}.png')
    manifest['parts'][name]={'rectangle':list(rect),'alphaBounds':list(bounds),'size':list(part.size),'extraction':'largest connected alpha component'}
legs=Image.open(out/'legs.png')
for name,rect in [('leg_left',(0,0,legs.width//2,legs.height)),('leg_right',(legs.width//2,0,legs.width,legs.height))]:
    legs.crop(rect).save(out/f'{name}.png');manifest['parts'][name]={'derivedFrom':'legs','rectangle':list(rect)}
for name in ['handle','mace_head']:
    Image.open(out/f'{name}.png').transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(out/f'{name}_mirrored.png')
    manifest['parts'][name+'_mirrored']={'derivedFrom':name,'operation':'horizontal flip'}
Image.open(out/'arm_left.png').transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(out/'arm_right.png')
manifest['parts']['arm_right']={'derivedFrom':'arm_left','operation':'horizontal flip'}
Image.new('RGBA',(1,1)).save(out/'root.png')
(out.parent/'asset-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
contact=Image.new('RGB',(1000,800),'#192331');draw=ImageDraw.Draw(contact)
for i,name in enumerate(rects):
    part=Image.open(out/f'{name}.png');part.thumbnail((220,200));x=i%4*250;y=i//4*200
    contact.paste(part,(x+12,y+25),part);draw.text((x+12,y+6),name,fill='white')
contact.save(out.parent/'asset-catalog.png')
print({name:p.get('size') for name,p in manifest['parts'].items()})
