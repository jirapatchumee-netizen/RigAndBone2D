import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';

export async function verifyCharacterUndo(sky, {app, directory}) {
    async function state() {return await sky.get_app_state({app,disableDiff:true});}
    function control(text, pattern) {
        const match=text.match(pattern);
        assert(match,'Missing UI control '+pattern);
        return Number(match[1]);
    }
    function names(text) {
        return [...text.matchAll(/^\s*\d+ text (hand-front|head|forearm-front|upper-arm-front|neck|upper-arm-back|torso|foot-front|pelvis|shin-front|foot-back|thigh-front|shin-back|hand-back|thigh-back|forearm-back|root \[hidden\])$/gm)].map(m=>m[1]);
    }
    async function save(name) {
        let s=await state();
        await sky.click({app,element_index:control(s.text,/^\s*(\d+) button Save…$/m)});
        s=await state();
        await sky.set_value({app,element_index:control(s.text,/^\s*(\d+) text field .*ID: saveAsNameTextField/m),value:name+'.rig2d'});
        await sky.press_key({app,key:'super+shift+g'});
        s=await state();
        await sky.set_value({app,element_index:control(s.text,/^\s*(\d+) text field .*ID: PathTextField/m),value:directory+'/'});
        await sky.press_key({app,key:'Return'});
        s=await state();
        await sky.click({app,element_index:control(s.text,/^\s*(\d+) button Save,/m)});
        await state();
        return JSON.parse(await fs.readFile(path.join(directory,name+'.rig2d'),'utf8'));
    }
    async function capture(name) {
        const s=await state();
        await fs.copyFile(fileURLToPath(s.screenshot.url),path.join(directory,name+'.jpg'));
        return s;
    }
    const before=await state();
    assert(before.text.includes('PARTS'));
    assert(!before.text.includes('radio button Description: Layers'));
    assert(!before.text.includes('radio button Description: Bones'));
    assert(!before.text.includes('ID: Layer'));
    const originalNames=names(before.text);
    assert.equal(originalNames.indexOf('upper-arm-back'),15);
    await sky.perform_secondary_action({app,element_index:control(before.text,/^(\d+) standard window/m),action:'Raise'});
    await sky.click({app,x:100,y:610});
    await state();
    await sky.drag({app,from_x:100,from_y:610,to_x:100,to_y:310});
    const moved=await capture('dragged');
    const movedNames=names(moved.text);
    assert.equal(movedNames.indexOf('upper-arm-back'),5);
    const front=await save('gui-front');
    await sky.press_key({app,key:'super+z'});
    const undone=await capture('gui-undone');
    assert.deepEqual(names(undone.text),originalNames);
    const undo=await save('gui-undo');
    const original=JSON.parse(await fs.readFile(path.join(directory,'Chibi-preview.rig2d'),'utf8'));
    assert.deepEqual(undo,original);
    await sky.press_key({app,key:'super+shift+z'});
    const redone=await capture('gui-redone');
    assert.deepEqual(names(redone.text),movedNames);
    const redo=await save('gui-redo');
    assert.deepEqual(redo,front);
    for(const project of [front,original])for(const bone of project.bones)delete bone.layer;
    assert.deepEqual(front,original);
    await sky.press_key({app,key:'super+z'});
    await state();
    const result={ok:true,singleList:true,noNumericLayer:true,dragNameMovesArmInFrontOfTorso:true,
        commandZRestoresExactProject:true,commandShiftZRestoresExactProject:true,savePreservesHistory:true,
        onlyLayerValuesChanged:true,originalNames,movedNames};
    await fs.writeFile(path.join(directory,'gui-proof.json'),JSON.stringify(result,null,2)+'\n');
    return result;
}
