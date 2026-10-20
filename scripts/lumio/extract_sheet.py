#!/usr/bin/env python3
"""Extract objects from ONE generated transparent master sheet (Lumio pipeline, step E1).

Usage: extract_sheet.py MASTER.png LAYOUT.json OUT_DIR [--alpha-floor 48] [--gap 6]

LAYOUT.json: {"schemaVersion":1,"objects":[{"id":"crop_carrot_plot","region":[x0,y0,x1,y1]}, ...]}
  region = percent of sheet (0-100) where the prompt told the generator to put that object.

Does: threshold alpha -> label connected blobs (merging pieces closer than --gap px at 1/4 scale)
      -> assign blobs to regions by centroid -> crop -> remove the faint glow halo (alpha floor + remap)
      -> write OUT_DIR/<id>.png and OUT_DIR/extraction-report.json. Needs Pillow + numpy only.
Exit code 2 when any object is missing or stray blobs are not assigned to a region (report says which).
Border-touching is only a warning: real generators drift from the percent layout (measured: a stone placed
for x5-40% actually spanned x0-49%), so assignment is by blob centroid, not by hard crop rectangles.
"""
import argparse, json, hashlib, sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image

STEP = 4  # labeling done on a 1/4-scale grid for speed


def label(mask, gap):
    h, w = mask.shape
    # grow by `gap` cells so nearby petals/leaves join their parent object
    grown = mask.copy()
    for _ in range(gap):
        g = grown.copy()
        g[1:, :] |= grown[:-1, :]; g[:-1, :] |= grown[1:, :]
        g[:, 1:] |= grown[:, :-1]; g[:, :-1] |= grown[:, 1:]
        grown = g
    lab = np.zeros((h, w), np.int32); n = 0
    for y, x in zip(*np.nonzero(grown)):
        if lab[y, x]:
            continue
        n += 1; lab[y, x] = n; q = deque([(y, x)])
        while q:
            cy, cx = q.popleft()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and grown[ny, nx] and not lab[ny, nx]:
                        lab[ny, nx] = n; q.append((ny, nx))
    return lab * mask, n  # labels only where the real mask is set


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('master'); ap.add_argument('layout'); ap.add_argument('out')
    ap.add_argument('--alpha-floor', type=int, default=48)
    ap.add_argument('--gap', type=int, default=2)
    ap.add_argument('--pad', type=int, default=8)
    a = ap.parse_args()
    src = Path(a.master); out = Path(a.out)
    if out.exists() and any(out.iterdir()):
        sys.exit('output directory must be new/empty (immutable outputs)')
    out.mkdir(parents=True, exist_ok=True)
    layout = json.loads(Path(a.layout).read_text())
    img = Image.open(src).convert('RGBA'); W, H = img.size
    arr = np.array(img); alpha = arr[..., 3]
    small = alpha[::STEP, ::STEP] >= a.alpha_floor
    lab, n = label(small, a.gap)
    blobs = {}
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if len(ys) < 40:  # ignore specks
            continue
        blobs[i] = dict(area=len(ys), cx=xs.mean() * STEP / W * 100, cy=ys.mean() * STEP / H * 100,
                        box=[xs.min() * STEP, ys.min() * STEP, (xs.max() + 1) * STEP, (ys.max() + 1) * STEP])
    report = {'schemaVersion': 1, 'source': str(src), 'sourceSHA256': hashlib.sha256(src.read_bytes()).hexdigest(),
              'sheetSize': [W, H], 'alphaFloor': a.alpha_floor, 'objects': {}, 'unassignedBlobs': [], 'ok': True}
    used = set()
    for obj in layout['objects']:
        x0, y0, x1, y1 = obj['region']
        mine = [i for i, b in blobs.items() if x0 <= b['cx'] <= x1 and y0 <= b['cy'] <= y1]
        entry = {'region': obj['region'], 'blobCount': len(mine)}
        if not mine:
            entry['error'] = 'missing: no artwork inside region'; report['ok'] = False
        else:
            used.update(mine)
            bx = [min(blobs[i]['box'][0] for i in mine), min(blobs[i]['box'][1] for i in mine),
                  max(blobs[i]['box'][2] for i in mine), max(blobs[i]['box'][3] for i in mine)]
            pad = a.pad
            cb = [max(0, bx[0] - pad), max(0, bx[1] - pad), min(W, bx[2] + pad), min(H, bx[3] + pad)]
            crop = arr[cb[1]:cb[0 + 3], cb[0]:cb[2]].copy()
            al = crop[..., 3].astype(np.float32)
            before = float(((al > 0) & (al <= 80)).sum()) / max(1, (al > 0).sum())
            # keep only pixels belonging to this object's blobs (drop neighbours' glow), then remove halo
            keep = np.zeros(al.shape, bool)
            for i in mine:
                bb = blobs[i]['box']
                keep[max(0, bb[1] - cb[1] - 2 * STEP):bb[3] - cb[1] + 2 * STEP, max(0, bb[0] - cb[0] - 2 * STEP):bb[2] - cb[0] + 2 * STEP] = True
            al = np.where(keep, al, 0)
            al = np.clip((al - a.alpha_floor) / (255.0 - a.alpha_floor), 0, 1) * 255
            crop[..., 3] = al.astype(np.uint8)
            nz = crop[..., 3] > 0
            ys, xs = np.nonzero(nz)
            crop = crop[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            after = float(((crop[..., 3] > 0) & (crop[..., 3] <= 80)).sum()) / max(1, (crop[..., 3] > 0).sum())
            Image.fromarray(crop).save(out / f"{obj['id']}.png")
            rw, rh = (x1 - x0) / 100 * W, (y1 - y0) / 100 * H
            touches = bx[0] <= x0 / 100 * W + 4 or bx[1] <= y0 / 100 * H + 4 or bx[2] >= x1 / 100 * W - 4 or bx[3] >= y1 / 100 * H - 4
            entry.update(size=[crop.shape[1], crop.shape[0]], faintAlphaRatioBefore=round(before, 4),
                         faintAlphaRatioAfter=round(after, 4), touchesRegionBorder=bool(touches))
            if touches:
                entry['warning'] = 'artwork reaches region border (generator ignored layout slightly; centroid assignment still used)'
        report['objects'][obj['id']] = entry
    report['unassignedBlobs'] = [dict(b, id=i) for i, b in blobs.items() if i not in used]
    if report['unassignedBlobs']:
        report['ok'] = False
    (out / 'extraction-report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({k: (v if k != 'objects' else {o: {kk: vv for kk, vv in e.items() if kk in ('size', 'faintAlphaRatioBefore', 'faintAlphaRatioAfter', 'error', 'warning')} for o, e in v.items()}) for k, v in report.items() if k != 'source'}, indent=1))
    sys.exit(0 if report['ok'] else 2)


if __name__ == '__main__':
    main()
