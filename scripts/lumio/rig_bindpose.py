#!/usr/bin/env python3
"""Approximate Pillow renderer for RigAndBone2D recipe-v1 (forward kinematics), for checking rigs on machines
without the native app. NOT the source of truth: the native renderer is. Semantics (validated on the Inquisitor demo):
child pivot = parent pivot + R(parentWorldAngle)*(x,y); image height = length, width = aspect*length (or `width`);
angle in degrees, positive = clockwise on screen (y down); canvas 384x384 with origin at centre.
usage: rig_bindpose.py RECIPE.json OUT.png [--frame INDEX|--pose '{"bone":deg}'] [--scale 2] [--bg checker|white]"""
import argparse, json, math, os
from PIL import Image

def render(recipe_path, pose=None, scale=2, canvas=384, bg="checker"):
    r = json.load(open(recipe_path)); base = os.path.dirname(os.path.abspath(recipe_path))
    bones = {b["id"]: b for b in r["bones"]}
    order, seen = [], set()
    def visit(i):
        if i in seen: return
        p = bones[i].get("parent")
        if p: visit(p)
        seen.add(i); order.append(i)
    for i in bones: visit(i)
    world = {}
    for i in order:
        b = bones[i]; p = b.get("parent")
        ang = (b.get("angle") or 0) + (pose or {}).get(i, 0) if False else (pose or {}).get(i, b.get("angle") or 0)
        x, y = b.get("x") or 0, b.get("y") or 0
        if p:
            (px, py), pa = world[p]
            c, s = math.cos(math.radians(pa)), math.sin(math.radians(pa))
            pos = (px + c*x - s*y, py + s*x + c*y); wa = pa + ang
        else:
            pos = (x, y); wa = ang
        world[i] = (pos, wa)
    S = scale; size = canvas*S
    img = Image.new("RGBA", (size, size), (255,255,255,255) if bg != "none" else (0,0,0,0))
    if bg == "checker":
        for yy in range(0, size, 16*S//2*1):
            for xx in range(0, size, 16*S//2*1):
                if (xx//(8*S) + yy//(8*S)) % 2: img.paste((225,225,225,255), (xx, yy, xx+8*S, yy+8*S))
    for i in sorted(order, key=lambda k: (bones[k].get("layer") or 0)):
        b = bones[i]
        if b.get("visible") is False or not b.get("image"): continue
        src = Image.open(os.path.join(base, b["image"])).convert("RGBA")
        h = (b.get("length") or src.height) ; w = b.get("width") or src.width * h / src.height
        src = src.resize((max(1, round(w*S)), max(1, round(h*S))), Image.LANCZOS)
        (px, py), wa = world[i]
        pvx, pvy = b.get("pivotX", .5), b.get("pivotY", .5)
        # rotate about pivot: paste on a big transparent square centred on the pivot
        pad = int(max(src.size)*2)
        tile = Image.new("RGBA", (pad*2, pad*2), (0,0,0,0))
        tile.paste(src, (pad - round(pvx*src.width), pad - round(pvy*src.height)))
        tile = tile.rotate(-wa, resample=Image.BICUBIC, center=(pad, pad))   # PIL rotates CCW; we want CW positive
        cx, cy = (canvas/2 + px)*S, (canvas/2 + py)*S
        img.alpha_composite(tile, (round(cx - pad), round(cy - pad))) if (cx-pad) >= 0 and (cy-pad) >= 0 else \
            img.paste(tile, (round(cx - pad), round(cy - pad)), tile)
    return img

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("recipe"); ap.add_argument("out")
    ap.add_argument("--frame", type=int); ap.add_argument("--pose"); ap.add_argument("--scale", type=int, default=2)
    a = ap.parse_args(); pose = None
    if a.frame is not None: pose = json.load(open(a.recipe))["frames"][a.frame]["pose"]
    if a.pose: pose = json.loads(a.pose)
    render(a.recipe, pose, a.scale).save(a.out); print("wrote", a.out)
