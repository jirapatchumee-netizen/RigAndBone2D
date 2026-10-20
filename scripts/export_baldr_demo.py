#!/usr/bin/env python3
"""Export through the real API, then package its rendered frames for preview."""
import json,pathlib,subprocess
from PIL import Image
root=pathlib.Path(__file__).resolve().parents[1];out=root/'examples/baldr';project=out/'Baldr.rig2d'
binary=root/'dist/RigAndBone2D.app/Contents/MacOS/RigAndBone2D'
request={'id':'baldr-export','command':'export_sheet','project':str(project),'output':str(out/'Baldr-sheet.png')}
r=subprocess.run([str(binary),'--agent'],input=json.dumps(request)+'\n',text=True,capture_output=True,check=True)
response=json.loads(r.stdout);assert response['ok'],response
(out/'export-session.json').write_text(json.dumps({'request':request,'response':response},indent=2)+'\n')
(out/'Baldr-sheet.json').write_text(json.dumps(response['result'],indent=2)+'\n')
sheet=Image.open(out/'Baldr-sheet.png').convert('RGBA');frames=[];directory=out/'frames';directory.mkdir(exist_ok=True)
for i in range(24):
    x=i%6*384;y=i//6*384;frame=sheet.crop((x,y,x+384,y+384));frame.save(directory/f'{i:03}.png')
    background=Image.new('RGBA',(384,384),'#101827');background.alpha_composite(frame)
    frames.append(background.convert('RGB').resize((576,576),Image.Resampling.LANCZOS))
frames[0].save(out/'Baldr-demo.gif',save_all=True,append_images=frames[1:],duration=125,loop=0,optimize=False)
print(f'Exported 24 transparent frames, sprite sheet, metadata and 3-second GIF: {out}')
