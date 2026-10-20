#!/usr/bin/env python3
"""Stable entry point for recipe builds, project checks, and rendered previews."""
import argparse
import json
import pathlib
import sys
import subprocess
from rigtools.client import AgentClient, RigAPIError
from rigtools.quality import check_project, render_preview

parser = argparse.ArgumentParser(description=__doc__)
sub = parser.add_subparsers(dest='action', required=True)
build = sub.add_parser('build', help='Compile a declarative recipe through the real app API')
build.add_argument('recipe', type=pathlib.Path)
build.add_argument('--project', type=pathlib.Path, required=True)
build.add_argument('--replace', action='store_true')
build.add_argument('--dry-run', action='store_true')
build.add_argument('--log', type=pathlib.Path)
check = sub.add_parser('check', help='Validate structure and loop endpoints')
check.add_argument('project', type=pathlib.Path)
check.add_argument('--strict', action='store_true')
preview = sub.add_parser('preview', help='Render, check frame boundaries, create GIF and sprite sheet')
preview.add_argument('project', type=pathlib.Path)
preview.add_argument('--output', type=pathlib.Path, required=True)
preview.add_argument('--fps', type=int, default=20)
preview.add_argument('--no-gif', action='store_true')
preview.add_argument('--no-sheet', action='store_true')
preview.add_argument('--strict', action='store_true')
prepare = sub.add_parser('prepare', help='Extract reusable assets from a declarative manifest')
prepare.add_argument('manifest', type=pathlib.Path)
prepare.add_argument('--output', type=pathlib.Path, required=True)
prepare.add_argument('--dry-run', action='store_true')
godot = sub.add_parser('godot-export', help='Export immutable optimized native Godot character package')
godot.add_argument('project', type=pathlib.Path)
godot.add_argument('--config', type=pathlib.Path, required=True)
godot.add_argument('--output', type=pathlib.Path, required=True)
godot.add_argument('--godot', default='godot')
spritekit = sub.add_parser('spritekit-export', help='Export immutable baked SpriteKit atlas package')
spritekit.add_argument('project', type=pathlib.Path)
spritekit.add_argument('--config', type=pathlib.Path, required=True)
spritekit.add_argument('--output', type=pathlib.Path, required=True)
schema = sub.add_parser('schema', help='Discover the versioned recipe JSON Schema from the app')
schema.add_argument('--output', type=pathlib.Path)
args = parser.parse_args()
try:
    if args.action == 'prepare':
        from rigtools.assets import prepare_assets
        result = prepare_assets(args.manifest, args.output, args.dry_run)
    else:
        with AgentClient() as client:
            if args.action == 'build':
                if not args.dry_run:
                    args.project.parent.mkdir(parents=True, exist_ok=True)
                result = client.request('apply_recipe', args.project, recipe=str(args.recipe.resolve()),
                                        replace=args.replace, dry_run=args.dry_run)
                if args.log:
                    client.save_transcript(args.log)
            elif args.action == 'spritekit-export':
                from rigtools.spritekit import export_spritekit
                result = export_spritekit(client, args.project, args.config, args.output)
            elif args.action == 'godot-export':
                from rigtools.godot import export_godot
                result = export_godot(client, args.project, args.config, args.output, args.godot)
            elif args.action == 'check':
                client.request('validate', args.project)
                result = check_project(client.request('inspect', args.project))
            elif args.action == 'preview':
                if not 1 <= args.fps <= 60:
                    raise ValueError('fps must be between 1 and 60')
                result = render_preview(client, args.project, args.output, args.fps,
                                        gif=not args.no_gif, sheet=not args.no_sheet)
            else:
                result = client.request('get_schema')
                if args.output:
                    args.output.write_text(json.dumps(result, indent=2)+'\n')
    passed = not (getattr(args, 'strict', False) and result.get('warnings'))
    print(json.dumps({'ok': passed, 'result': result}, indent=2))
    if not passed:
        sys.exit(2)
except RigAPIError as error:
    print(json.dumps(error.response, indent=2), file=sys.stderr)
    sys.exit(1)
except (ValueError, OSError, KeyError, ImportError, subprocess.SubprocessError) as error:
    print(json.dumps({'ok': False, 'error': str(error)}, indent=2), file=sys.stderr)
    sys.exit(1)
