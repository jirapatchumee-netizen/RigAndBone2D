#!/usr/bin/env python3
"""Cut the approved F1 hero into rigid limbs, preserving its pixels and single cuffs.

Only hidden shoulder overlap is extended with sampled sleeve texture. No mirroring,
repainting of visible features, or modification of immutable input assets.
Outputs must be new. Metadata keeps the original hero coordinate system for pivots.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from extract_sheet import label

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'Assets/Source/chr_f1_farmer/v001/parts'
SCALE = .36


def clean(im):
    a = np.array(im.convert('RGBA'))
    # Keep only the character, excluding the neighbouring heads left in F1 crops.
    labs, n = label(a[::4, ::4, 3] > 64, 0)
    counts = np.bincount(labs.ravel()); counts[0] = 0
    mask = Image.fromarray((labs == counts.argmax()).astype('uint8') * 255)
    mask = mask.resize(im.size, Image.Resampling.NEAREST).filter(ImageFilter.MaxFilter(17))
    alpha = np.clip((a[..., 3].astype(float) - 48) / (253 - 48), 0, 1) * 255
    a[..., 3] = np.where(np.array(mask) > 0, alpha, 0).astype('uint8')
    return Image.fromarray(a)


def polygon(im, points):
    mask = Image.new('L', im.size); ImageDraw.Draw(mask).polygon(points, fill=255)
    a = np.array(im); a[..., 3] = np.minimum(a[..., 3], np.array(mask))
    return Image.fromarray(a)


def main_component(im):
    a = np.array(im)
    labs, _ = label(a[::2, ::2, 3] > 32, 0)
    counts = np.bincount(labs.ravel()); counts[0] = 0
    mask = Image.fromarray((labs == counts.argmax()).astype('uint8') * 255)
    mask = mask.resize(im.size,Image.Resampling.NEAREST).filter(ImageFilter.MaxFilter(5))
    a[...,3] = np.minimum(a[...,3],np.array(mask))
    return Image.fromarray(a)


def sleeve_overlap(part, hero, pivot, right):
    # The cap is behind the bib at rest, and remains behind it at +/-30 degrees.
    px, py = pivot
    mask = Image.new('L', hero.size)
    ImageDraw.Draw(mask).ellipse((px-34, py-34, px+34, py+34), fill=255)
    src = np.array(hero)
    yy, xx = np.indices(src.shape[:2])
    sx = np.clip(xx, 229, 258) if right else np.clip(xx, 465, 485)
    sy = np.clip(yy, 476, 503)
    cap = src[sy, sx].copy(); cap[..., 3] = np.array(mask)
    base = Image.fromarray(cap); base.alpha_composite(part)
    return base


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); args = ap.parse_args()
    out = Path(args.out).resolve()
    if out.exists(): raise SystemExit('output must be new; immutable assets are never overwritten')
    (out / 'parts').mkdir(parents=True)
    hero = clean(Image.open(SOURCE / 'char_farmer_hero_v01.png'))
    cuts = {
        'hat': ([(0,0),(636,0),(636,270),(549,325),(529,307),(530,264),
                 (537,226),(529,190),(519,167),(505,145),(480,130),(445,122),
                 (408,124),(370,130),(321,143),(283,159),(244,177),(210,197),
                 (179,221),(154,245),(130,271),(111,300),(99,333),(96,369),
                 (92,382),(0,400)], (350,170), 'head', 50),
        'torso': ([(301,453),(319,445),(401,433),(429,443),(439,469),
                   (447,507),(452,563),(463,600),(466,653),(444,677),
                   (367,688),(339,688),(255,676),(246,652),(252,610),
                   (254,576),(284,556),(299,526),(292,475)], (355,630), 'pelvis', 20),
        'pelvis': ([(255,603),(458,603),(476,662),(462,690),(388,694),
                    (354,681),(326,704),(249,695),(238,675)], (355,641), 'root', 18),
        'arm_r': ([(100,430),(266,445),(281,468),(292,500),(298,532),
                   (282,560),(264,578),(247,578),(239,610),(226,625),
                   (228,710),(100,710)], (265,488), 'torso', 17),
        'arm_l': ([(431,433),(448,443),(466,467),(480,477),(495,490),
                   (507,515),(505,533),(535,575),(575,609),(580,680),
                   (482,680),(485,615),(461,586),(456,559),(444,530),
                   (432,477)], (451,485), 'torso', 19),
        'leg_r': ([(263,612),(329,617),(371,639),(359,675),(331,737),
                   (315,770),(319,900),(145,900),(145,779),(187,758),
                   (203,707),(228,667),(245,628)], (298,642), 'pelvis', 9),
        'leg_l': ([(369,619),(447,616),(478,669),(500,783),(563,799),
                   (576,879),(362,879),(359,776),(350,714),(355,672)],
                  (410,639), 'pelvis', 10),
    }
    meta = {'schemaVersion': 1, 'scale': SCALE, 'origin': [350,440], 'parts': {}}
    def save(name, im, pivot, parent, layer, origin=(0,0), factor=1):
        bbox = im.getchannel('A').getbbox(); cropped = im.crop(bbox)
        file = f'char_farmer_part_{name}_v01.png'
        cropped.save(out / 'parts' / file)
        bx, by = origin[0]+bbox[0]*factor, origin[1]+bbox[1]*factor
        w, h = cropped.width*factor, cropped.height*factor
        meta['parts'][name] = {'file': file, 'height': h*SCALE,
             'pivotX': (pivot[0]-bx)/w, 'pivotY': (pivot[1]-by)/h,
             'worldX': (pivot[0]-350)*SCALE, 'worldY': (pivot[1]-440)*SCALE,
             'parent': parent, 'layer': layer, 'sourceBox': list(bbox)}
    for name, (points, pivot, parent, layer) in cuts.items():
        part = polygon(hero, points)
        if name.startswith('arm_'): part = sleeve_overlap(part,hero,pivot,name=='arm_r')
        part = main_component(part)
        save(name,part,pivot,parent,layer)
    # The four approved expression images share one canvas and one transform.
    for face in ('happy','blink','talk','surprised'):
        im = clean(Image.open(SOURCE / f'char_farmer_head_{face}_v01.png'))
        common = Image.new('RGBA',(420,394)); common.alpha_composite(im,((420-im.width)//2,394-im.height))
        pivot = (350,422); origin = (114,27); factor = 1.03
        common.save(out/'parts'/f'char_farmer_head_{face}_v01.png')
        if face=='happy':
            meta['parts']['head'] = {'file': f'char_farmer_head_{face}_v01.png',
                'height': 394*factor*SCALE, 'pivotX': (pivot[0]-origin[0])/(420*factor),
                'pivotY': (pivot[1]-origin[1])/(394*factor),
                'worldX': (pivot[0]-350)*SCALE, 'worldY': (pivot[1]-440)*SCALE,
                'parent':'torso','layer':40}
    (out/'rig-parts.json').write_text(json.dumps(meta,indent=2)+'\n')
    sources = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCE.glob('*.png')}
    (out/'provenance.json').write_text(json.dumps({'task':'RIG-FARMER-FIX-001',
       'method':'approved F1 pixel masks; sampled hidden shoulder overlap; single rigid limbs; largest-component alpha cleanup',
       'sourceSHA256':sources,'script':'scripts/lumio/prepare_farmer_fix.py'},indent=2)+'\n')
    print('Prepared',out,'with',len(meta['parts']),'visible bones and 4 equal-size expressions')


if __name__=='__main__': main()
