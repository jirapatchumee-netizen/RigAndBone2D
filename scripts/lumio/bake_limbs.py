#!/usr/bin/env python3
"""Bake two-segment limbs (upper+lower) into ONE rigid image each, so the rig has no elbow/knee joints to misalign.
Uses rig_bindpose.render (same FK semantics). Writes rigs/lumio/farmer/assets/baked_<limb>.png and baked.json
(height in units + pivot fractions of the shoulder/hip) which build_farmer_recipe.py reads.   usage: bake_limbs.py"""
import json, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, HERE)
import rig_bindpose as R
from PIL import Image
P = os.path.join(ROOT, "Assets/Source/chr_f2b_farmer_parts/v001/parts/char_farmer_part_{}_v01.png")
OUT = os.path.join(ROOT, "rigs/lumio/farmer/assets"); os.makedirs(OUT, exist_ok=True)
S = 6; CANVAS = 240                      # render scale and canvas (units); limb root pivot at canvas centre
# name: (upper part, upper height, upper pivotY, upper layer, lower part, lower height, lower pivotY, lower layer, offset of lower pivot below upper pivot)
LIMBS = {
 "arm_r": ("upper_arm_r", 50, .12, 17, "forearm_r", 60, .10, 16, 44),
 "arm_l": ("upper_arm_l", 50, .12, 27, "forearm_l", 60, .10, 26, 44),
 "leg_r": ("thigh_r", 44, .08, 9, "shin_r", 66, .10, 6, 31),
 "leg_l": ("thigh_l", 44, .08, 10, "shin_l", 66, .10, 7, 31),
}
info = {}
for name, (up, uh, upy, ul, lo, lh, lpy, ll, off) in LIMBS.items():
    rec = {"schemaVersion": 1, "duration": 1, "frames": [], "bones": [
        {"id": "u", "x": 0, "y": 0, "length": uh, "pivotX": .5, "pivotY": upy, "layer": ul, "image": P.format(up)},
        {"id": "l", "parent": "u", "x": 0, "y": off, "length": lh, "pivotX": .5, "pivotY": lpy, "layer": ll, "image": P.format(lo)}]}
    tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False); json.dump(rec, tmp); tmp.close()
    img = R.render(tmp.name, {}, S, CANVAS, bg="none"); os.unlink(tmp.name)
    bbox = img.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    crop = img.crop(bbox); cx = CANVAS/2*S; cy = CANVAS/2*S
    crop.save(os.path.join(OUT, f"baked_{name}.png"))
    info[name] = {"image": f"../../rigs/lumio/farmer/assets/baked_{name}.png", "height": round(crop.height/S, 2),
                  "pivotX": round((cx - bbox[0])/crop.width, 4), "pivotY": round((cy - bbox[1])/crop.height, 4)}
    print(name, crop.size, info[name])
json.dump(info, open(os.path.join(OUT, "baked.json"), "w"), indent=1)
