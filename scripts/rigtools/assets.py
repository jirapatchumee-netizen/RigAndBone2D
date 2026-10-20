"""Deterministic sprite extraction from a versioned manifest; no source edits."""
import hashlib
import json
import os
import pathlib
import re
import tempfile
from collections import deque

def prepare_assets(spec_path, output, dry_run=False):
    from PIL import Image, ImageChops, ImageFilter
    spec_path = pathlib.Path(spec_path).resolve()
    spec = json.loads(spec_path.read_text())
    if set(spec) - {'schemaVersion', 'source', 'parts'} or spec.get('schemaVersion') != 1:
        raise ValueError('Unsupported asset manifest fields or version')
    source = (spec_path.parent / spec['source']).resolve()
    if source.suffix.lower() not in {'.png', '.jpg', '.jpeg'}:
        raise ValueError('Source must be an image')
    with Image.open(source) as image:
        original = image.convert('RGBA')
    parts, evidence = {}, {}
    def crop(image, rect):
        if not isinstance(rect, list) or len(rect) != 4 or any(type(v) is not int for v in rect):
            raise ValueError('rect must have four integer pixel coordinates')
        x0, y0, x1, y1 = rect
        if not (0 <= x0 < x1 <= image.width and 0 <= y0 < y1 <= image.height):
            raise ValueError(f'Crop outside image bounds: {rect}')
        return image.crop(rect)
    for item in spec['parts']:
        if set(item) - {'id', 'rect', 'derivedFrom', 'mirrorX', 'isolate', 'transparent'}:
            raise ValueError('Unknown part field')
        name = item['id']
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]{0,63}', name) or name in parts:
            raise ValueError(f'Invalid or duplicate part ID: {name}')
        if item.get('transparent'):
            part = Image.new('RGBA', (1, 1))
        else:
            if item.get('derivedFrom') not in (None, *parts.keys()):
                raise ValueError('derivedFrom must refer to an earlier part')
            part = parts.get(item.get('derivedFrom'), original).copy()
            if 'rect' in item:
                part = crop(part, item['rect'])
            isolate = item.get('isolate', 'alpha_bounds')
            if isolate not in {'alpha_bounds', 'largest_alpha', 'none'}:
                raise ValueError('isolate must be alpha_bounds, largest_alpha or none')
            if isolate == 'largest_alpha':
                w, h = part.size
                alpha = part.getchannel('A'); pixels = alpha.load()
                visited, groups = set(), []
                for y in range(h):
                    for x in range(w):
                        if (x, y) in visited or pixels[x, y] < 16:
                            continue
                        group, queue = [], deque([(x, y)])
                        visited.add((x, y))
                        while queue:
                            px, py = queue.popleft(); group.append((px, py))
                            for nx, ny in ((px-1, py), (px+1, py), (px, py-1), (px, py+1)):
                                if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited and pixels[nx, ny] >= 16:
                                    visited.add((nx, ny)); queue.append((nx, ny))
                        groups.append(group)
                if not groups:
                    raise ValueError(f'No opaque sprite in {name}')
                mask = Image.new('L', (w, h)); points = mask.load()
                for x, y in max(groups, key=len):
                    points[x, y] = 255
                part.putalpha(ImageChops.multiply(alpha, mask.filter(ImageFilter.MaxFilter(3))))
            bounds = part.getchannel('A').getbbox()
            if bounds is None:
                raise ValueError(f'Empty sprite {name}; use transparent:true for controls')
            if isolate != 'none':
                part = part.crop(bounds)
            if item.get('mirrorX'):
                part = part.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        parts[name] = part
        evidence[name] = {'spec': item, 'width': part.width, 'height': part.height}
    report = {'schemaVersion': 1, 'source': str(source), 'sourceSHA256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'partCount': len(parts), 'parts': evidence, 'dryRun': dry_run}
    if not dry_run:
        output = pathlib.Path(output).resolve()
        if output.exists():
            raise FileExistsError('Asset output already exists; choose a new job directory')
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output.parent, prefix='.rig-assets-') as temp:
            staged = pathlib.Path(temp)/'assets'; staged.mkdir()
            for name, part in parts.items():
                part.save(staged/f'{name}.png')
            (staged/'asset-report.json').write_text(json.dumps(report, indent=2)+'\n')
            os.rename(staged, output)
    return report
