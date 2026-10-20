#!/usr/bin/env python3
"""Generates recipes/lumio/farmer.rigrecipe.json from a joint table (world positions in canvas units, y down, origin = canvas centre).
Edit the TABLE, rerun, then look at it with rig_bindpose.py (approximate) and the native app (source of truth).
usage: build_farmer_recipe.py [OUT.json]"""
import json, math, os, sys
from PIL import Image
P = "../../Assets/Source/chr_f2b_farmer_parts/v001/parts/char_farmer_part_{}_v01.png"
D = P  # F2b has no joint plugs, so no cleaned derivatives are needed (old: "../../rigs/lumio/farmer/assets/char_farmer_part_{}_v01.png")   # plug-cleaned derivatives (scripts/lumio/clean_plugs.py)
H = "../../Assets/Source/chr_f1_farmer/v001/parts/char_farmer_head_{}_v01.png"
HERE = os.path.dirname(os.path.abspath(__file__)); RECIPES = os.path.join(HERE, "..", "..", "recipes", "lumio")

# id, parent, image, height(units), pivotX, pivotY, worldX, worldY (of the pivot), restAngle(deg), layer
OY = 14   # shifts the whole figure down so hat and boots both fit the 384 canvas (root stays at 0)
TABLE = [
 ("root",        None,       None,                 1,   .5, .5,   0,    0,   0, -100),
 ("pelvis",      "root",     D.format("pelvis"),   58,  .5, .5,   0,    4,   0,   18),
 ("torso",       "pelvis",   D.format("torso"),    74,  .5, .90,  0,  -24,   0,   20),
 ("head",        "torso",    H.format("happy"),    110, .5, .86,  0,  -84,   0,   40),
 ("hat",         "head",     P.format("hat"),      66,  .5, .70,  0, -136,   0,   50),
]
def limb(name, parent, wx, wy, layer):
    b = json.load(open(os.path.join(HERE, "..", "..", "rigs", "lumio", "farmer", "assets", "baked.json")))[name]
    return (name, parent, b["image"], b["height"], b["pivotX"], b["pivotY"], wx, wy, 0, layer)
TABLE += [limb("arm_r", "torso", -44, -72, 17), limb("arm_l", "torso", 44, -72, 27),
          limb("leg_r", "pelvis", -20, 22, 9), limb("leg_l", "pelvis", 20, 22, 10)]   # baked 2-segment limbs (scripts/lumio/bake_limbs.py)

# RIG-FARMER-FIX-001: hero-derived rigid limbs preserve one sleeve/cuff per limb.
# All pivots and scales come from one source coordinate system, eliminating the
# inconsistent sizes and doubled cuffs of the separately generated parts.
FIX = os.path.join(HERE, "..", "..", "Assets", "Source", "chr_farmer_rigfix", "v001")
if os.path.isfile(os.path.join(FIX, "rig-parts.json")):
    data = json.load(open(os.path.join(FIX, "rig-parts.json")))
    OY = 0
    TABLE = [("root", None, None, 1, .5, .5, 0, 0, 0, -100)]
    for name in ("pelvis", "torso", "head", "hat", "arm_r", "arm_l", "leg_r", "leg_l"):
        b = data["parts"][name]
        img = os.path.relpath(os.path.join(FIX, "parts", b["file"]), RECIPES)
        TABLE.append((name, b["parent"], img, b["height"], b["pivotX"], b["pivotY"],
                      b["worldX"], b["worldY"], 0, b["layer"]))

def main(out):
    clips = json.load(open(os.path.join(RECIPES, "farmer.clips.json")))
    FRAMES = clips["frames"]
    duration = max(f["time"] for f in FRAMES)
    world = {}; bones = []
    for (i, parent, img, h, pvx, pvy, wx, wy, rest, layer) in TABLE:
        wy = wy + (OY if parent is not None else 0)
        if parent is None: lx, ly = wx, wy; wa = rest
        else:
            (px, py), pa = world[parent]; dx, dy = wx - px, wy - py
            c, s = math.cos(math.radians(-pa)), math.sin(math.radians(-pa))
            lx, ly = c*dx - s*dy, s*dx + c*dy; wa = pa + rest
        world[i] = ((wx, wy), wa)   # NOTE: wy already includes OY below
        b = {"id": i, "name": i, "parent": parent, "x": round(lx, 2), "y": round(ly, 2), "length": h, "angle": rest,
             "layer": layer, "pivotX": pvx, "pivotY": pvy}
        if img: b["image"] = img
        else: b["visible"] = False
        bones.append(b)
    r = {"schemaVersion": 1, "name": "lumio-farmer", "duration": duration, "bones": bones, "frames": FRAMES}
    json.dump(r, open(out, "w"), indent=1); print("wrote", out, len(bones), "bones,", len(FRAMES), "keyframes")
    sk = {"schemaVersion": 1, "id": "char_farmer", "licenseRecordID": "lumio-codex-generated-review-before-public-release",
          "renderScale": clips.get("renderScale", 0.75), "pixelsPerUnit": 1, "fps": clips.get("fps", 15), "maxAtlas": 2048, "clips": clips["clips"]}
    json.dump(sk, open(os.path.join(RECIPES, "farmer.spritekit.json"), "w"), indent=1); print("wrote farmer.spritekit.json with", len(clips["clips"]), "clips")
if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RECIPES, "farmer.rigrecipe.json"))
