#!/usr/bin/env python3
"""Export combat poses through the application, package a smooth 20-fps preview."""
import json,pathlib,subprocess
from PIL import Image
root=pathlib.Path(__file__).resolve().parents[1];out=root/'examples/inquisitor';project=out/'Inquisitor-combat.rig2d'
binary=root/'dist/RigAndBone2D.app/Contents/MacOS/RigAndBone2D'
process=subprocess.Popen([str(binary),'--agent'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True);log=[]
def call(command,**values):
    request={'id':f'combat-export-{len(log)+1:03}','command':command,'project':str(project),**values}
    process.stdin.write(json.dumps(request)+'\n');process.stdin.flush();response=json.loads(process.stdout.readline());log.append({'request':request,'response':response});assert response['ok'],response
    return response['result']
project_info=call('inspect');assert len(project_info['frames'])==13 and project_info['duration']==3
call('validate');sheet_result=call('export_sheet',output=str(out/'Inquisitor-sheet.png'))
(out/'Inquisitor-sheet.json').write_text(json.dumps(sheet_result,indent=2)+'\n')
frames=[];directory=out/'frames';directory.mkdir(exist_ok=True);bounds=[]
for i in range(60):
    path=directory/f'{i:03}.png';call('render',time=i/20,output=str(path))
    frame=Image.open(path).convert('RGBA');box=frame.getchannel('A').getbbox();bounds.append(box)
    assert box and box[0]>0 and box[1]>0 and box[2]<384 and box[3]<384,('clipped',i,box)
    background=Image.new('RGBA',(384,384),'#101827');background.alpha_composite(frame)
    frames.append(background.convert('RGB').resize((576,576),Image.Resampling.LANCZOS))
frames[0].save(out/'Inquisitor-combat.gif',save_all=True,append_images=frames[1:],duration=50,loop=0,optimize=False)
process.stdin.close();assert process.wait(timeout=10)==0
(out/'export-session.json').write_text(json.dumps(log,indent=2)+'\n')
(out/'preview-metadata.json').write_text(json.dumps({'frameCount':60,'fps':20,'duration':3,'alphaBoundsPerFrame':bounds,'validation':'All frames within 384 × 384 canvas'},indent=2)+'\n')
# Review key moments on one image, using the actual rendered PNGs.
review=Image.new('RGB',(1536,384),'#101827')
for i,name in enumerate(['guard','windup','impact','followthrough']):
    part=Image.open(out/f'Inquisitor-{name}.png').convert('RGBA');review.paste(part,(i*384,0),part)
review.save(out/'combat-contact-sheet.png')
print('PASS: 13 authored keyframes, 60 rendered frames within bounds; 24-frame sheet and 20-fps GIF exported')
