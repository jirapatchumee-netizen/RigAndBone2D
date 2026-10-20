#!/usr/bin/env python3
"""Cut thin bridges between touching objects in a generated master sheet.
usage: split_touching.py MASTER.png OUT.png --seed y,x --seed y,x [...]   (full-res seed points, one inside each object)
Seeds grow over the eroded alpha mask; pixels where two objects meet get alpha=0 (a 3px cut). Non-destructive: writes OUT."""
import argparse, sys
from collections import deque
import numpy as np
from PIL import Image

def erode(a, r):
    o = a.copy()
    for _ in range(r):
        p = np.pad(o, 1); o = p[1:-1,1:-1] & p[:-2,1:-1] & p[2:,1:-1] & p[1:-1,:-2] & p[1:-1,2:]
    return o

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("master"); ap.add_argument("out")
    ap.add_argument("--seed", action="append", required=True)
    ap.add_argument("--erode", type=int, default=2)
    ap.add_argument("--floor", type=int, default=48)
    a = ap.parse_args()
    im = np.array(Image.open(a.master).convert("RGBA")).copy()
    H, W = im.shape[:2]
    mask = im[...,3] > a.floor
    small = erode((im[::4, ::4, 3] > 110), a.erode)
    lab = np.zeros((H, W), np.int16)
    q = deque()
    for i, sd in enumerate(a.seed, 1):
        y, x = map(int, sd.split(","))
        sy, sx = y // 4, x // 4
        if not small[sy, sx]: sys.exit(f"seed {sd} not inside an eroded object")
        comp = deque([(sy, sx)]); seen = {(sy, sx)}
        while comp:
            cy, cx = comp.popleft()
            lab[cy*4:cy*4+4, cx*4:cx*4+4] = i
            for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
                n = (cy+dy, cx+dx)
                if 0 <= n[0] < small.shape[0] and 0 <= n[1] < small.shape[1] and small[n] and n not in seen:
                    seen.add(n); comp.append(n)
    lab[~mask] = 0
    for y, x in zip(*np.nonzero(lab)): q.append((y, x))
    while q:
        cy, cx = q.popleft()
        for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
            ny, nx = cy+dy, cx+dx
            if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and lab[ny, nx] == 0:
                lab[ny, nx] = lab[cy, cx]; q.append((ny, nx))
    cut = np.zeros((H, W), bool)
    P = np.pad(lab, 1)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0: continue
            nb = P[1+dy:1+dy+H, 1+dx:1+dx+W]
            cut |= (lab > 0) & (nb > 0) & (nb != lab)
    # thicken cut by 1px
    p = np.pad(cut, 1); cut = p[1:-1,1:-1] | p[:-2,1:-1] | p[2:,1:-1] | p[1:-1,:-2] | p[1:-1,2:]
    n = int((cut & mask).sum())
    im[cut, 3] = 0
    Image.fromarray(im).save(a.out)
    print(f"cut {n} px; wrote {a.out}")
main()
