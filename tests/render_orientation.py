"""Regression: offscreen PNG must preserve top/bottom orientation and alpha."""
import json,pathlib,subprocess,tempfile
from PIL import Image
root=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as directory:
    directory=pathlib.Path(directory);project=directory/'orientation.rig2d'
    marker=Image.new('RGBA',(4,4),'red')
    for y in (2,3):
        for x in range(4):marker.putpixel((x,y),(0,0,255,255))
    marker.save(directory/'marker.png');Image.new('RGBA',(1,1)).save(directory/'clear.png')
    binary=root/'dist/RigAndBone2D.app/Contents/MacOS/RigAndBone2D'
    process=subprocess.Popen([str(binary),'--agent'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
    def call(command,**values):
        process.stdin.write(json.dumps({'command':command,'project':str(project),**values})+'\n');process.stdin.flush()
        response=json.loads(process.stdout.readline());assert response['ok'],response
        return response['result']
    call('new');call('inspect')
    for i in range(12):call('import_image',bone=i,image=str(directory/('marker.png' if i==0 else 'clear.png')))
    call('set_bone',bone=0,values={'length':40,'width':40,'angle':0,'pivotX':.5,'pivotY':.5,'layer':100})
    call('render',output=str(directory/'render.png'))
    rendered=Image.open(directory/'render.png').convert('RGBA')
    assert rendered.getpixel((192,176)) == (255,0,0,255), rendered.getpixel((192,176))
    assert rendered.getpixel((192,208)) == (0,0,255,255), rendered.getpixel((192,208))
    assert rendered.getpixel((0,0))[3] == 0
    process.stdin.close();assert process.wait(timeout=10)==0
print('PASS: PNG source orientation, pivot placement and transparent background')
