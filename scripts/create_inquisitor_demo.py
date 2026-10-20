#!/usr/bin/env python3
"""Author combat through RigAndBone2D's real JSONL API."""
import json,pathlib,subprocess
root=pathlib.Path(__file__).resolve().parents[1];out=root/'examples/inquisitor';project=out/'Inquisitor-combat.rig2d'
binary=root/'dist/RigAndBone2D.app/Contents/MacOS/RigAndBone2D'
process=subprocess.Popen([str(binary),'--agent'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
log=[];revision=None

def call(command,**values):
    global revision
    request={'id':f'combat-{len(log)+1:03}','command':command,'project':str(project),**values}
    if revision and command not in ['new','capabilities']:request['expected_revision']=revision
    process.stdin.write(json.dumps(request)+'\n');process.stdin.flush();response=json.loads(process.stdout.readline())
    log.append({'request':request,'response':response})
    if not response['ok']:raise RuntimeError(response)
    if command=='inspect':revision=response['result']['revision']
    elif command in ['new','add_bone','set_bone','import_image','keyframe','set_duration']:revision=None
    return response['result']
call('capabilities');call('new',overwrite=True);call('inspect')
for name,parent in [('Chain',7),('Morning Star',12),('Coat tails',1),('Back shoulder',3),('Front shoulder',5),('Training stand',0),('Training body',17),('Training head',18),('Training arms',18),('Training base',17)]:
    call('add_bone',bone=parent,name=name)
# Original pixels are attached to local bones; no raster pose generation.
parts=[
(0,'Root',None,-25,10,'root',1,0,-100,.5,.5),
(1,'Torso',0,0,-30,'body',56,0,6,.5,.18),
(2,'Determined head',1,0,-9,'head_determined',84,0,20,.5,.92),
(3,'Back arm',1,-23,10,'arm_left',48,10,4,.8,.15),
(4,'Guard fist',3,-24,32,'hand_fist',23,0,10,.5,.75),
(5,'Weapon arm',1,23,10,'arm_right',48,-45,9,.2,.15),
(6,'Gripping hand',5,24,32,'hand_grasp',24,35,13,.5,.68),
(7,'Morning Star handle',6,0,-7,'handle_mirrored',40,-5,11,.21,.35),
(8,'Back thigh',0,-12,10,'leg_left',35,9,2,.5,.04),
(9,'Back boot',8,0,27,'boot_left',31,-9,5,.5,.08),
(10,'Front thigh',0,12,10,'leg_right',35,-9,3,.5,.04),
(11,'Front boot',10,0,27,'boot_right',31,9,7,.5,.08),
(12,'Chain',7,71,-1,'chain',17,0,12,.08,.85),
(13,'Morning Star head',12,30,-11,'mace_head_mirrored',39,0,12,.1,.52),
(14,'Coat tails',1,0,29,'coat',47,0,1,.5,.12),
(15,'Back shoulder armor',3,0,0,'shoulder_left',36,-5,8,.75,.2),
(16,'Front shoulder armor',5,0,0,'shoulder_right',36,5,14,.25,.2),
(17,'Training dummy stand',None,144,69,None,60,180,0,.5,.0),
(18,'Training dummy body',17,0,42,None,32,0,1,.5,.0),
(19,'Training dummy head',18,0,40,None,20,0,2,.5,.0),
(20,'Training dummy crossbar',18,23,20,None,46,90,0,.5,.0),
(21,'Training dummy base',17,23,0,None,46,90,0,.5,.0),
]
for i,name,parent,x,y,image,height,angle,layer,px,py in parts:
    call('inspect');call('set_bone',bone=i,values={'name':name,'parent':parent,'x':x,'y':y,'length':height,'angle':angle,'layer':layer,'pivotX':px,'pivotY':py})
    if image:
        call('inspect');call('import_image',bone=i,image=str(out/'assets'/f'{image}.png'))
    else:
        call('inspect');call('set_bone',bone=i,values={'width':32 if i==18 else 24 if i==19 else 8,'color':[.72,.29,.22] if i==18 else [.65,.47,.28]})
base=[p[7] for p in parts]
# Anticipation -> quick swing -> follow-through -> recovery -> guard.
poses=[
(0,'guard',{}),
(.35,'guard breathe',{1:-2,2:2,14:3,12:-6}),
(.7,'wind-up',{1:-7,2:5,3:28,5:-115,6:30,7:12,12:22,13:-18,8:16,9:-16,10:-18,11:18,14:10}),
(.95,'weapon raised',{1:-9,2:6,3:35,5:-145,6:20,7:25,12:10,13:-8,8:18,9:-18,10:-22,11:22,14:14}),
(1,'release',{1:-5,2:3,3:26,5:-130,6:18,7:18,12:-10,13:-16,8:10,9:-10,10:-22,11:22,14:8}),
(1.1,'strike start',{1:4,2:-5,3:12,5:-95,6:15,7:5,12:-35,13:-25,8:0,9:0,10:-22,11:22,14:-4}),
(1.3,'impact',{1:9,2:-7,3:-20,5:-20,6:12,7:7,12:0,13:10,18:8,8:-10,9:10,10:-22,11:22,14:-12}),
(1.5,'follow-through',{1:12,2:-8,3:-30,5:20,6:-15,7:-15,12:28,13:22,18:18,8:-12,9:12,10:-18,11:18,14:-16}),
(1.85,'recoil',{1:4,2:-3,3:0,5:-10,6:20,7:-10,12:32,13:-15,18:-6,14:-6}),
(2,'recover start',{1:0,2:0,5:-30,6:28,7:-5,12:10,13:0,18:-3,14:0}),
(2.2,'recover',{1:-3,2:3,5:-55,6:40,7:0,12:-20,13:10,18:4,14:8}),
(2.6,'guard settle',{1:1,2:-1,12:6,13:-5,14:-3}),
(3,'guard',{}),
]
call('set_duration',duration=3)
for time,name,changes in poses:
    angles=list(base)
    for i,v in changes.items():angles[i]=v
    call('inspect');call('keyframe',time=time,angles=angles)
call('validate')
for time,name in [(0,'guard'),(.95,'windup'),(1.3,'impact'),(1.5,'followthrough')]:
    call('render',time=time,output=str(out/f'Inquisitor-{name}.png'))
call('inspect');process.stdin.close();assert process.wait(timeout=10)==0
(out/'agent-session.json').write_text(json.dumps(log,indent=2)+'\n')
(out/'combat-timeline.json').write_text(json.dumps([{'time':t,'phase':n,'angleOverrides':c} for t,n,c in poses],indent=2)+'\n')
print(f'Created combat project: {len(parts)} bones, {len(poses)} keyframes, {len(log)} successful API requests')
