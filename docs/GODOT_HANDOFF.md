# Godot handoff v1

Use `scripts/rig_pipeline.py godot-export PROJECT --config CONFIG --output NEW_DIRECTORY` with Pillow and Godot on PATH. The native project is validated and sampled through the shared app API with its revision pinned. A source change aborts the job. The destination must not exist; generated packages are immutable. Copy one selected package version into the game's `generated/characters/<id>/`; keep revision archives outside the game resource directory.

Example (repository root):

```sh
RIG_PYTHON=/Users/macminim4pro/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
"$RIG_PYTHON" scripts/rig_pipeline.py godot-export examples/rebuilt/Inquisitor-combat.rig2d --config recipes/inquisitor.godot.json --output scratch/handoff-001/inquisitor
"$RIG_PYTHON" tests/godot_bridge.py
godot --path examples/godot-demo
```

## Ownership and contract

The animation author owns the `.rig2d`, recipes and handoff configuration. The bridge owns the atlas and native visual scene. The game agent owns wrapper scenes, collision rules, movement and damage in `gameplay/`. Do not edit generated scenes manually. Godot scene dependencies use relative atlas paths so the package can move between projects. No Python, RigAndBone executable, source sprite sheet or rig JSON is needed at game runtime.

The versioned manifest identifies the source revision, tested Godot version, bone IDs, sockets, named clips, clip-relative event times, runtime filenames and measured sizes. `visual.tscn` is a Node2D hierarchy with Sprite2D artwork and an AnimationPlayer. Its `sockets` metadata maps semantic names to NodePaths. Units are pixels, positive Y down; source degrees become Godot radians. Parent transforms, pivots and absolute draw ordering are preserved. Rigid cutouts only; no mesh deformation or simulated chain physics.

Config v1 fields: `schemaVersion`, `id`, `exclude` (bone IDs and descendants), `hidden` (art only), `density` (1..4 image pixels per displayed unit, default 2), `maxAtlas` (256/512/1024/2048/4096), `sockets` (name to kept bone ID), and `clips`. Each clip has unique `name`, `start`, `end`, boolean `loop`, and optional unique `{name,time}` events relative to the clip. Boundary poses are sampled by the shared native sampler. Loop endpoints must match. Events become Animation markers; these are metadata, not automatically emitted damage signals. The game consumes them explicitly.

## Optimization policy

- Trim transparent borders while preserving the artwork offset and original pivot.
- Downsample only when source resolution exceeds the configured display density. Never upscale. Density 2 targets the current displayed size and up to roughly 2x visual enlargement; larger use requires another density and visual review.
- Deduplicate exact RGBA images and exact horizontal mirrors after resizing. Mirror sprites share the same atlas region. No approximate matching.
- Pack only visible, included artwork into one lossless PNG atlas with two extruded edge pixels and clipped region filtering. Reject atlas budget overflow; never silently sacrifice fidelity to fit.
- Export linear angle keys at authored times, not a rendered frame sequence. Constant tracks have one reset key so changing clips cannot inherit stale rotations. Do not use angular wrap interpolation: the source sampler uses direct angle interpolation.
- Godot resource loading shares the atlas between instances; the integration test checks actual resource identity. Animation node processing still has a cost for each actor. One atlas does not guarantee one draw call, especially with layering and other render states.
- Ship `atlas.png` and `visual.tscn`; keep manifest as development metadata unless the game explicitly consumes it. No GIF/video/previews, original sheets, embedded `.rig2d` or archived revisions in runtime directories. Export the selected gameplay scene and its dependencies, not every file. Inspect actual exported artifacts when an export preset and target are added.

`rgba8BaseBytes` estimates one uncompressed RGBA8 base level only, excluding mipmaps, driver allocation, engine objects and compression choices. PNG bytes measure source disk payload, not exported game size or GPU usage. FPS, peak memory and draw calls require a target workload benchmark; this bridge does not claim a capacity measurement. Avoid enabling lossy compression without reviewing outlines and transparency.

## Current playable proof

`examples/godot-demo/project.godot`: Left/Right move, Space attacks a separate training target. Idle is a held guard pose; no walk animation is authored yet. Attack includes recovery in its 3-second non-looping clip. The weapon-tip socket drives an Area2D; only overlaps during markers `hit_start` .. `hit_end` deal damage, at most once per attack. Chain movement is authored, not physics. This is a gameplay integration proof, not a finished combat system.

`tests/godot_bridge.py` builds in a fresh temporary directory, imports into a differently located Godot project, verifies 12 sampled world poses against native API samples, shared atlas identity between two instances, exclusion of the baked training dummy, one damage application and an out-of-range miss. Original source project is untouched. Visual review remains required after changing art/density/pivots. Run it alongside the repository's normal tests.

## Render benchmark evidence

`tools/godot/benchmark_handoff.gd` runs a small visible render workload (960×540, 0.3-scale actors, 30 warmup + 120 sampled frames, VSync disabled) on the installed Godot compatibility renderer. Latest machine-specific results are in `reports/godot-render-benchmark.json`. The benchmark animates the cutout hierarchy but excludes gameplay AI and physics; it is a short measurement, not a sustained capacity guarantee. `textureMemoryBytes` is the engine-wide monitor, not character-only allocation. Re-run on the actual shipping renderer, screen size and gameplay workload before setting performance budgets.
