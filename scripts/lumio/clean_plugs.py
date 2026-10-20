#!/usr/bin/env python3
"""Erase skin-coloured joint 'plugs' from the end bands of exploded parts (the generator paints them at joints).
Deterministic post-process of immutable sources -> writes NEW files to OUT_DIR. usage: clean_plugs.py SRC_PARTS_DIR OUT_DIR"""
import colorsys, os, sys
import numpy as np
from PIL import Image
# part -> list of (end, fraction of height, col_lo, col_hi as fractions of width). Neck of torso is kept on purpose.
JOBS = {"pelvis": [("bottom", .40, 0, 1), ("top", .30, 0, 1)], "thigh_r": [("bottom", .30, 0, 1)], "thigh_l": [("bottom", .30, 0, 1)],
        "shin_r": [("top", .25, 0, 1)], "shin_l": [("top", .25, 0, 1)],
        "torso": [("bottom", .22, 0, 1), ("top", .50, 0, .30), ("top", .50, .70, 1)],
        "upper_arm_r": [("top", .28, 0, 1)], "upper_arm_l": [("top", .28, 0, 1)]}
def main(src, out):
    os.makedirs(out, exist_ok=True)
    for name, jobs in JOBS.items():
        im = Image.open(os.path.join(src, f"char_farmer_part_{name}_v01.png")).convert("RGBA"); a = np.array(im); W = a.shape[1]; total = 0
        for (end, frac, c0, c1) in jobs:
            H = a.shape[0]; rows = slice(int(H*(1-frac)), H) if end == "bottom" else slice(0, int(H*frac)); cols = slice(int(W*c0), int(W*c1))
            sub = a[rows, cols]; rgb = sub[..., :3].astype(float)/255
            hsv = np.array([[colorsys.rgb_to_hsv(*px) for px in row] for row in rgb])
            skin = (hsv[...,0]*360 >= 8) & (hsv[...,0]*360 <= 42) & (hsv[...,1] >= .16) & (hsv[...,1] <= .62) & (hsv[...,2] >= .72)
            total += int((skin & (sub[...,3] > 0)).sum()); sub[...,3][skin] = 0
        Image.fromarray(a).save(os.path.join(out, f"char_farmer_part_{name}_v01.png")); print(f"{name}: erased {total} px")
main(sys.argv[1], sys.argv[2])
