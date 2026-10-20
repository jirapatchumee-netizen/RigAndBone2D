"""Shared checks that report evidence, not inferred animation quality."""
import json
import pathlib

def check_project(info):
    frames = sorted(info['frames'], key=lambda frame: frame['time'])
    warnings = []
    if not frames:
        warnings.append('No keyframes; preview is static.')
    endpoint_coverage = bool(frames and frames[0]['time'] == 0 and frames[-1]['time'] == info['duration'])
    if not endpoint_coverage:
        warnings.append('Animation does not have keys at both loop endpoints.')
    seamless = endpoint_coverage and frames[0]['angles'] == frames[-1]['angles']
    if endpoint_coverage and not seamless:
        warnings.append('Loop endpoint poses differ; a visible jump is possible.')
    return {'boneCount': len(info['bones']), 'keyframeCount': len(frames), 'duration': info['duration'],
            'revision': info['revision'], 'phases': [{'time': f['time'], 'label': f.get('label')} for f in frames], 'endpointCoverage': endpoint_coverage,
            'seamlessLoop': seamless, 'warnings': warnings}

def render_preview(client, project, directory, fps=20, gif=True, sheet=True):
    from PIL import Image
    directory = pathlib.Path(directory)
    if directory.exists() and any(directory.iterdir()):
        raise FileExistsError("Preview output is not empty; choose a new job directory")
    directory.mkdir(parents=True, exist_ok=True)
    frames_dir = directory / 'frames'
    frames_dir.mkdir(exist_ok=True)
    info = client.request('inspect', project)
    report = check_project(info)
    exact_count = info['duration'] * fps
    count = round(exact_count)
    if count < 1 or count > 2400 or abs(exact_count-count) > 1e-8:
        raise ValueError('duration × fps must be an integer between 1 and 2400')
    frames, clipped, bounds = [], [], []
    for i in range(count):
        path = frames_dir / f'{i:04}.png'
        client.request('render', project, time=i/fps, output=str(path), expected_revision=info['revision'])
        with Image.open(path) as source:
            image = source.convert('RGBA')
        box = image.getchannel('A').getbbox()
        bounds.append(box)
        if box and (box[0] == 0 or box[1] == 0 or box[2] == image.width or box[3] == image.height):
            clipped.append(i)
        if gif:
            background = Image.new('RGBA', image.size, '#101827')
            background.alpha_composite(image)
            frames.append(background.convert('RGB'))
    report.update(frameCount=count, fps=fps, clippedFrames=clipped, alphaBounds=bounds,
                  emptyFrames=[i for i, box in enumerate(bounds) if box is None], visualReviewRequired=True)
    if clipped:
        report['warnings'].append('Nontransparent pixels touch frame edges; clipping is possible.')
    if report["emptyFrames"]:
        report["warnings"].append("Some frames contain no visible artwork.")
    if gif:
        # GIF timing is quantized to 10ms; distribute rounding over cumulative timestamps.
        durations = [(round((i+1)*100/fps)-round(i*100/fps))*10 for i in range(count)]
        if min(durations) < 10:
            raise ValueError('GIF preview supports at most 100 fps')
        frames[0].save(directory/'preview.gif', save_all=True, append_images=frames[1:],
                       duration=durations, loop=0, optimize=False)
    if sheet:
        metadata = client.request('export_sheet', project, output=str(directory/'sheet.png'), expected_revision=info['revision'])
        (directory/'sheet.json').write_text(json.dumps(metadata, indent=2)+'\n')
    (directory/'quality-report.json').write_text(json.dumps(report, indent=2)+'\n')
    client.save_transcript(directory/'agent-session.json')
    return report
