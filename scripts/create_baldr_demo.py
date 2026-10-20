#!/usr/bin/env python3
"""Build a real sprite rig using only the app's public agent commands."""
import json, pathlib, subprocess
root=pathlib.Path(__file__).resolve().parents[1]
out=root/'examples/baldr';out.mkdir(parents=True,exist_ok=True)
project=out/'Baldr.rig2d'
binary=root/'dist/RigAndBone2D.app/Contents/MacOS/RigAndBone2D'
process=subprocess.Popen([str(binary),'--agent'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
log=[];revision=None

def call(command,**values):
    global revision
    request={'id':f'baldr-{len(log)+1:03}','command':command,'project':str(project),**values}
    if revision and command not in ['capabilities','new']:request['expected_revision']=revision
    process.stdin.write(json.dumps(request)+'\n');process.stdin.flush()
    response=json.loads(process.stdout.readline());log.append({'request':request,'response':response})
    if not response['ok']:raise RuntimeError(response)
    if command=='inspect':revision=response['result']['revision']
    elif command in ['new','set_bone','add_bone','import_image','keyframe','set_duration']:revision=None
    return response['result']

call('capabilities')
call('new',overwrite=True)
call('inspect')
# Append bones via API to preserve schema and keyframe lengths.
for name,parent in [('Waist',1),('Cape',1),('Back wing R',1),('Back hand',4),('Front hand',6),('Back shoulder',3),('Front shoulder',5),('Back wing base L',1),('Back wing base R',1),('Halo',1)]:call('add_bone',bone=parent,name=name)
# Index, name, parent, attachment x/y, image, display height, rotation, layer, pivot x/y.
parts=[
(0,'Root',None,0,0,'root',1,0,-100,.5,.5),
(1,'Chest',0,0,-38,'chest',36,0,5,.5,.18),
(2,'Head',1,0,-3,'head',66,0,20,.5,.95),
(3,'Back upper arm',1,-19,6,'upper_arm',26,20,3,.5,.12),
(4,'Back forearm',3,0,21,'forearm',23,-12,4,.5,.15),
(5,'Front upper arm',1,19,6,'upper_arm',26,-20,8,.5,.12),
(6,'Front forearm',5,0,21,'forearm',23,12,9,.5,.15),
(7,'Back wing L',1,-32,0,'wing',86,-23,0,.5,.95),
(8,'Back thigh',0,-10,18,'thigh',35,7,2,.5,.08),
(9,'Back shin',8,0,28,'shin',28,-4,3,.5,.08),
(10,'Front thigh',0,10,18,'thigh',35,-7,4,.5,.08),
(11,'Front shin',10,0,28,'shin',28,4,5,.5,.08),
(12,'Waist',1,0,29,'waist',35,0,7,.5,.07),
(13,'Cape',1,0,2,'cape',78,0,-2,.5,.08),
(14,'Back wing R',1,32,0,'wing_mirrored',86,23,0,.5,.95),
(15,'Back hand',4,0,18,'hand',15,0,5,.5,.25),
(16,'Front hand',6,0,18,'hand',15,0,10,.5,.25),
(17,'Back shoulder armor',3,0,0,'shoulder',29,-8,6,.5,.1),
(18,'Front shoulder armor',5,0,0,'shoulder',29,8,11,.5,.1),
(19,'Back wing base L',1,-26,14,'wing_base',30,0,1,.85,.65),
(20,'Back wing base R',1,26,14,'wing_base_mirrored',30,0,1,.15,.65),
(21,'Halo',1,0,-56,'halo',52,0,1,.5,.5),
]
for i,name,parent,x,y,image,height,angle,layer,px,py in parts:
    call('inspect')
    call('set_bone',bone=i,values={'name':name,'parent':parent,'x':x,'y':y,'length':height,'angle':angle,'layer':layer,'pivotX':px,'pivotY':py})
    call('inspect')
    call('import_image',bone=i,image=str(out/'assets'/f'{image}.png'))
base=[part[7] for part in parts]
# Gentle idle + wing movement, then a front arm salute and return.
poses=[(0,{}),(.5,{1:-1.5,2:2,7:-29,14:29,13:3}), (1,{1:0,2:-2,7:-18,14:18,13:-3}), (1.5,{5:-55,6:-40,16:12,2:-5,7:-25,14:25}), (2,{5:-85,6:-55,16:15,2:-7,7:-30,14:30}), (2.5,{5:-55,6:-40,2:-4,13:3}), (3,{})]
call('set_duration',duration=3)
for time,changes in poses:
    angles=list(base)
    for i,v in changes.items():angles[i]=v
    call('inspect');call('keyframe',time=time,angles=angles)
call('validate')
call('render',output=str(out/'Baldr-preview.png'),time=0)
call('render',output=str(out/'Baldr-salute.png'),time=2)
call('inspect')
(out/'agent-session.json').write_text(json.dumps(log,indent=2)+'\n')
process.stdin.close();assert process.wait(timeout=10)==0
print(f'Created {project}: {len(parts)} bones, {len(poses)} poses, {len(log)} successful API requests')
