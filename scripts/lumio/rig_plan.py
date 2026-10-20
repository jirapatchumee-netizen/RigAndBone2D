#!/usr/bin/env python3
"""Rig planner: compute joints, part sizes and the generation-sheet layout BEFORE any art is generated.
Input: a rigspec JSON measured on the APPROVED assembled reference image (pixel coordinates of that image):
  {"id","pack","ref_image","units_per_px","origin_ref":[x,y],"oy":N,
   "parts":[{"id","parent","bbox":[l,t,r,b],"expand":[l,t,r,b],"pivot":[x,y],"layer":N,"note":""}]}
  bbox   = where the part sits in the reference; expand = extra px painted beyond bbox (overlap hidden under the neighbour at joints)
  pivot  = the joint point in reference pixels (where the part rotates)
Output (in Assets/Inbox/<pack>/): layout.json (percent cells, packed, >=gutter), PLAN.md (numbers for humans), rig_rows.json (recipe table rows),
and PROMPT_PARTS.txt (the per-piece lines to paste into the pack prompt).  usage: rig_plan.py SPEC.json [--gutter 0.06] [--sheet 1536 1024]"""
import argparse, json, os, sys
ap = argparse.ArgumentParser(); ap.add_argument("spec"); ap.add_argument("--gutter", type=float, default=.06)
ap.add_argument("--sheet", nargs=2, type=int, default=[1536, 1024]); a = ap.parse_args()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
S = json.load(open(a.spec)); W, H = a.sheet; gut = a.gutter
parts = []
for p in S["parts"]:
    l, t, r, b = p["bbox"]; el, et, er, eb = p.get("expand", [0, 0, 0, 0])
    box = [l - el, t - et, r + er, b + eb]
    parts.append({**p, "box": box, "w": box[2] - box[0], "h": box[3] - box[1]})
def pack(scale):
    """shelf packing with gutters; returns placements or None"""
    gx, gy = int(W * gut), int(H * gut); x = gx; y = gy; shelf = 0; out = {}
    for p in sorted(parts, key=lambda q: -q["h"]):
        w, h = round(p["w"] * scale), round(p["h"] * scale)
        if x + w + gx > W: x = gx; y += shelf + gy; shelf = 0
        if y + h + gy > H or w + 2 * gx > W: return None
        out[p["id"]] = [x, y, x + w, y + h]; x += w + gx; shelf = max(shelf, h)
    return out
lo, hi = .2, 3.0
for _ in range(40):
    mid = (lo + hi) / 2
    if pack(mid): lo = mid
    else: hi = mid
scale = round(lo - .005, 3); place = pack(scale)
if not place: sys.exit("cannot pack even at small scale; split into two sheets")
pack_dir = os.path.join(ROOT, "Assets", "Inbox", S["pack"]); os.makedirs(pack_dir, exist_ok=True)
objects = []
for p in parts:
    x0, y0, x1, y1 = place[p["id"]]
    # region = cell with half-gutter slack, in percent of the sheet
    sx, sy = gut * W / 2, gut * H / 2
    objects.append({"id": f"{S['id']}_part_{p['id']}_v01", "region": [round(max(0, x0 - sx) / W * 100, 1), round(max(0, y0 - sy) / H * 100, 1), round(min(W, x1 + sx) / W * 100, 1), round(min(H, y1 + sy) / H * 100, 1)], "size_px": [x1 - x0, y1 - y0]})
json.dump({"schemaVersion": 1, "pack": S["pack"], "sheetSize": [W, H], "objects": [{k: v for k, v in o.items() if k != "size_px"} for o in objects]}, open(os.path.join(pack_dir, "layout.json"), "w"), indent=1)
k = S["units_per_px"]; ox, oy_ref = S["origin_ref"]; OY = S.get("oy", 0); rows = []
for p in parts:
    px, py = p["pivot"]; bx0, by0, bx1, by1 = p["box"]
    rows.append({"id": p["id"], "parent": p["parent"], "height_units": round(p["h"] * k, 2), "pivotX": round((px - bx0) / p["w"], 4), "pivotY": round((py - by0) / p["h"], 4),
                 "world": [round((px - ox) * k, 2), round((py - oy_ref) * k + OY, 2)], "layer": p["layer"]})
json.dump(rows, open(os.path.join(pack_dir, "rig_rows.json"), "w"), indent=1)
lines = []
for p, o in zip(parts, objects):
    x0, y0, x1, y1 = place[p["id"]]
    lines.append(f" - {p['id'].upper()}: cell x {o['region'][0]}-{o['region'][2]}% y {o['region'][1]}-{o['region'][3]}%; draw it about {x1-x0}x{y1-y0} px ({round((x1-x0)/W*100)}% x {round((y1-y0)/H*100)}% of the sheet). {p.get('note','')}")
open(os.path.join(pack_dir, "PROMPT_PARTS.txt"), "w").write("\n".join(lines) + "\n")
md = [f"# Rig plan: {S['id']} (pack {S['pack']})", f"reference: `{S['ref_image']}`; units_per_px {k}; generation scale vs reference = **{scale}x** (bigger = sharper parts); sheet {W}x{H}, gutter {int(gut*100)}%", "",
      "| part | parent | reference bbox | painted box (with overlap) | draw size px | pivot (ref px) | height units | layer |", "|---|---|---|---|---|---|---|---|"]
for p, r in zip(parts, rows):
    md.append(f"| {p['id']} | {p['parent']} | {p['bbox']} | {[round(v) for v in p['box']]} | {round(p['w']*scale)}x{round(p['h']*scale)} | {p['pivot']} | {r['height_units']} | {p['layer']} |")
md += ["", f"Sprites to generate: **{len(parts)}** (+ heads/expressions reused from the approved pack if listed in the spec).", "Nothing here is generated; Codex draws exactly these pieces in ONE edit of the approved reference."]
open(os.path.join(pack_dir, "PLAN.md"), "w").write("\n".join(md) + "\n")
print("\n".join(md))
