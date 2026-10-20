# Agent workflow — version 0.2

Use this workflow for new characters. Keep character-specific data in JSON recipes; use the shared tools for extraction, compilation, verification and export. The old per-character scripts remain for historical demo reproduction.

## Start here

1. Discover `capabilities` and `get_schema` through `scripts/agent.py` or `rigtools.client.AgentClient`.
2. Inspect the supplied sheet and declare crop rectangles in an asset manifest. Crop selection and pivot placement still require visual judgment.
3. Prepare an immutable asset directory with `rig_pipeline.py prepare`.
4. Describe the skeleton and animation in a recipe with named bone IDs.
5. Dry-run the recipe before writing; then build a `.rig2d` project.
6. Run structural and loop checks, then render the whole clip.
7. Read the quality report and visually inspect key poses before delivery. Exported images are evidence; structural validation cannot judge whether an attack looks convincing.

The API and build/check commands need only Python's standard library. Asset preparation and preview packaging need Pillow. On this machine it is bundled at:

```sh
RIG_PYTHON=/Users/macminim4pro/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
```

## Rebuild an existing demo using the shared workflow

Run from the repository root; choose a new job directory:

```sh
python3 scripts/rig_pipeline.py build recipes/inquisitor-combat.rigrecipe.json --project scratch/job-003/Inquisitor.rig2d --dry-run
python3 scripts/rig_pipeline.py build recipes/inquisitor-combat.rigrecipe.json --project scratch/job-003/Inquisitor.rig2d --log scratch/job-003/build-session.json
python3 scripts/rig_pipeline.py check scratch/job-003/Inquisitor.rig2d --strict
"$RIG_PYTHON" scripts/rig_pipeline.py preview scratch/job-003/Inquisitor.rig2d --output scratch/job-003/preview --fps 20 --strict
```

The demo recipes reference existing extracted PNGs relative to the recipe file. To test the reusable extraction stage without replacing them:

```sh
"$RIG_PYTHON" scripts/rig_pipeline.py prepare recipes/inquisitor.assets.json --output scratch/job-003/assets
```

For a new character, point its recipe images at its own generated asset directory. `prepare` refuses an existing destination; `preview` refuses a nonempty destination, so frames from different jobs do not get mixed. Build refuses to replace an existing project unless `--replace` is supplied. Replacement uses the revision from inspection; no hidden retry overwrites somebody else's edit.

`--strict` makes `check`/`preview` exit 2 when their report has warnings. API or I/O errors exit 1. Successful commands exit 0. Structural checks can also be run without `--strict` for intentionally non-looping clips.

## Recipe format

Authoritative JSON Schema: `get_schema`. A generated copy is committed at `schemas/recipe-v1.schema.json`. Version fields are required. Unknown fields are rejected so `angel` cannot silently become an unrotated arm.

```json
{
  "schemaVersion": 1,
  "name": "Example character",
  "duration": 2,
  "bones": [
    {"id":"root","visible":false,"length":1},
    {"id":"torso","parent":"root","length":50,"width":30,"angle":0},
    {"id":"weapon-arm","parent":"torso","x":18,"y":8,"length":30,"angle":20}
  ],
  "frames": [
    {"time":0,"label":"guard","pose":{}},
    {"time":1,"label":"strike","pose":{"weapon-arm":-80}},
    {"time":2,"label":"guard","pose":{}}
  ]
}
```

- IDs are unique and immutable through patch commands. Parent and pose keys refer to IDs, not indices. Renaming display text does not change identity.
- Bone declaration order may be arbitrary. The compiler sorts parent before child and rejects cycles or missing parents.
- ID syntax: letter followed by up to 63 letters, digits, dots, underscores or hyphens.
- `image` is relative to the recipe file, or an absolute path. `length` sets displayed image height; width defaults to its aspect ratio. Explicit `width` overrides that fit.
- `pivotX`/`pivotY` are normalized 0–1. Position is local to parent, Y down, angle in degrees.
- `visible:false` hides artwork while retaining the bone and its children. Control bones do not need a transparent placeholder PNG.
- Each recipe frame starts from the recipe's rest angles, then applies the sparse `pose` overrides. It does not inherit the preceding keyframe.
- The recipe replaces the entire rig and frame list. No hidden demo frames are added. Duplicate times fail validation.
- Project name and frame labels are preserved as optional metadata in the `.rig2d` file.
- Layer ties retain compiled array order. Give overlapping artwork distinct layers when order matters.

## Safe incremental edits

Use the SDK from `scripts/` or add that directory to your Python import path:

```python
from rigtools.client import AgentClient

with AgentClient() as agent:
    result = agent.request("batch", "my-character.rig2d", operations=[
        {"command":"set_bone", "bone":"weapon-arm", "values":{"angle":-60}},
        {"command":"keyframe", "time":1, "label":"strike", "pose":{"weapon-arm":-60}}
    ])
    print(result["revision"])
```

The SDK inspects an existing project before its first mutation, reuses returned revision receipts, correlates response IDs, applies a response timeout, and raises structured errors. Use one SDK instance per thread. Revision conflicts are reported; they are not automatically retried.

`batch` mutates a copy in memory, validates the complete resulting project, and writes once. A failed operation or final validation leaves the file byte-for-byte unchanged. Nested transactions and render/export commands are not allowed in a batch. `dry_run:true` validates without saving.

## Asset manifest format

```json
{
  "schemaVersion":1,
  "source":"../inputs/character-sheet.png",
  "parts":[
    {"id":"head","rect":[16,32,112,104],"isolate":"alpha_bounds"},
    {"id":"arm","rect":[16,144,48,192],"isolate":"largest_alpha"},
    {"id":"arm-other","derivedFrom":"arm","mirrorX":true,"isolate":"none"}
  ]
}
```

`rect` is `[left,top,right,bottom]`; derived rectangles are relative to the earlier extracted part. `largest_alpha` keeps the largest connected alpha component and neighboring antialias pixels to exclude detached captions. `alpha_bounds` trims transparent borders; `none` preserves dimensions. This is deterministic pixel extraction, not automatic character recognition or background removal. Opaque source backgrounds remain opaque. Output includes the original source hash and extraction report; source images are never overwritten.

## Verification evidence

`quality-report.json` includes endpoint coverage, loop pose equality, frame count, source revision, empty frames, per-frame alpha bounds and possible clipping at edges. It also states `visualReviewRequired:true`. The sprite sheet remains 24 frames at 384 × 384; the preview samples independently at the selected fps. A 3-second 24-frame sheet uses 8 fps, while a 20-fps preview has 60 frames.

## Development checks

```sh
./scripts/build-app.sh
python3 tests/agent_smoke.py
python3 tests/agent_workflow.py
"$RIG_PYTHON" tests/render_orientation.py
"$RIG_PYTHON" tests/demo_reproducibility.py
```

The last test rebuilds extracted assets and both demos in temporary job directories, compares actual rendered pixels at 12 times per demo, checks 120 preview frames, and verifies that original demo projects remain unchanged. Its report is `reports/demo-reproducibility.json`.

## Send to Godot

Read [GODOT_HANDOFF.md](GODOT_HANDOFF.md). Use `godot-export` with a versioned handoff config and a new output directory. Review the manifest's memory/disk metrics and the actual Godot render. Keep authoring data and preview artifacts outside the game's runtime asset folders. Game agents modify wrapper scenes, not generated character scenes.

## Send to SpriteKit

Read [SPRITEKIT_HANDOFF.md](SPRITEKIT_HANDOFF.md). Use `spritekit-export` with a named-clip config and a new destination. Native render/sample calls pin expected_revision. Review authored key poses before export and the actual imported game scene afterward. Runtime consumes only atlas.png and manifest.json; keep parts, recipes, .rig2d, previews and transcripts outside the app bundle. Run `tests/spritekit_bridge.py` with the Pillow Python after changing this bridge.
