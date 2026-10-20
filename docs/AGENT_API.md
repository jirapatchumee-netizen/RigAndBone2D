# Agent API v1

Executable: `dist/RigAndBone2D.app/Contents/MacOS/RigAndBone2D --agent`

Transport: UTF-8 JSONL on stdin / stdout. One request per line, one response per line. Keep the process alive for a sequence of operations, or use `python3 scripts/agent.py '<JSON>'` for one request. Paths may be relative to process cwd; use absolute paths for agent workflows. Native stderr is separate from protocol stdout.

## Request and response

```json
{"id":"task-001","command":"inspect","project":"/absolute/path/character.rig2d"}
```

```json
{"id":"task-001","ok":true,"result":{"version":1,"bones":[],"worldBones":[],"frames":[],"duration":2,"revision":"sha256-of-file"}}
```

The response above illustrates field names; actual arrays contain project data. Errors return `{"id":...,"ok":false,"error":"..."}`. Always check `ok`; a protocol error does not use the process exit code.

## Commands

| command | Additional arguments | Behavior |
| --- | --- | --- |
| `capabilities` | none; project not required | Protocol version, command list and supported features |
| `new` | `project`, optional `overwrite:true` | Create the demo rig; refuses existing project by default |
| `inspect` | `project` | Properties, frames, world origins/endpoints, SHA-256 revision; image byte counts instead of base64 |
| `validate` | `project` | Check schema version, hierarchy, finite values, dimensions and frame lengths |
| `set_bone` | `project`, `bone` index, `values` object | Patch selected properties; omitted properties remain unchanged |
| `add_bone` | `project`, `bone` parent index, optional `name` | Append child and extend existing keyframes |
| `import_image` | `project`, `bone`, `image` file path | Embed artwork; update width to image aspect ratio |
| `replace_image` | `project`, `bone`, `image` file path | Replace only the selected bone artwork; preserve dimensions, pivot, hierarchy, pose and keyframes |
| `keyframe` | `project`, `time`, optional `angles` array | Store current pose or provided angles; replace frame within 0.025 seconds |
| `set_duration` | `project`, `duration` | Change length (0–120 seconds, excluding zero); fails if any frame exceeds new duration |
| `sample` | `project`, `time` | Return interpolated angles without modifying file |
| `render` | `project`, `output` PNG path, optional `time` | Render current pose or interpolated pose, 384 × 384, transparent |
| `export_sheet` | `project`, `output` PNG path | Render 24 frames, 2304 × 1536, transparent; returns dimensions and duration |

`set_bone.values` supports: `name`, `parent` (index or null), `x`, `y`, `length`, `angle`, `width`, `layer`, `pivotX`, `pivotY`, `color` (three floats). Parent must be an earlier bone index. `set_bone` alters the current pose; store a keyframe afterward to change animation playback.

Use `replace_image` for a new outfit, hand, face or weapon on an existing rig. It accepts a stable bone ID or integer index and works in `batch`, with `dry_run` and `expected_revision`. Only the embedded image bytes change. The replacement fills the existing width and length, so prepare matching transparent canvas dimensions and joint positions to avoid stretching or visible alignment changes. `import_image` keeps its original aspect-fitting behavior. Neither operation stores alternate skins or changes animation tracks.

All commands reading an existing project optionally accept `expected_revision`, taken from the previous inspect response. A stale revision returns an error before editing. Inspect again after each saved change. One writer per project is required.

`render` and `export_sheet` replace their output path. Use a new output filename when preserving previous results. The GUI export writes a JSON sidecar; the agent export returns equivalent metadata in its result, which the agent can save separately.

## Working sequence

1. `capabilities` → discover available commands.
2. `new` or `inspect` → obtain bone indices, names, and properties.
3. `import_image` → attach transparent PNG pieces to their bones.
4. `set_bone` → set pivots, dimensions, layer, attachment and local angle.
5. `keyframe` → save pose at a chosen time; repeat for other poses.
6. `validate`, then `render` → verify structure and visually inspect output.
7. `export_sheet` → create sprite sheet for a game or downstream tool.

Example shell calls from the project folder:

```sh
python3 scripts/agent.py '{"command":"new","project":"scratch/my-character.rig2d"}'
python3 scripts/agent.py '{"command":"inspect","project":"scratch/my-character.rig2d"}'
python3 scripts/agent.py '{"command":"set_bone","project":"scratch/my-character.rig2d","bone":5,"values":{"angle":130}}'
python3 scripts/agent.py '{"command":"keyframe","project":"scratch/my-character.rig2d","time":0.5}'
python3 scripts/agent.py '{"command":"render","project":"scratch/my-character.rig2d","time":0.5,"output":"scratch/pose.png"}'
```

Parent output directories must already exist. Do not edit the same project concurrently in the GUI and API. Reopen in the GUI after an agent saves changes.

## เปิดผลลัพธ์ให้ผู้ใช้ดูในแอป

หลังบันทึกและตรวจโปรเจกต์แล้ว ใช้ GUI launch options:

```sh
open -n dist/RigAndBone2D.app --args --project /absolute/path/character.rig2d --play
```

`--project` โหลดไฟล์พร้อมตรวจ schema, `--play` เริ่มเล่นและซ่อนเส้นกระดูกสำหรับดูผลงาน ตัวแอปรองรับการเปิด `.rig2d` ผ่าน macOS open-file event ด้วย

## Version 0.2 additions (protocol v1 compatible)

New-work entry point: [AGENT_WORKFLOW.md](AGENT_WORKFLOW.md).

- `get_schema`: return authoritative recipe JSON Schema; no project required.
- `apply_recipe`: require `recipe` path, target `project`, optional `dry_run:true`. Existing targets require both `replace:true` and `expected_revision`. Compile the complete rig and frame list, then save once.
- `batch`: require `operations` array of 1–1024 mutation objects. Apply in memory and validate once. No intermediate saves. `dry_run:true` returns the proposed counts and existing revision without writing.
- `new` accepts `preset:"empty"`: one invisible root and no frames. Default remains the legacy demo preset.
- `delete_keyframe` requires `time`; `clear_keyframes` removes all frame data.
- `bone` selectors accept a stable ID or integer index. `set_bone.values.parent` additionally accepts a parent ID; `visible` is supported. IDs are immutable through patching.
- `add_bone` optionally accepts `bone_id`; otherwise a persistent UUID is generated. Its `bone` argument selects the parent.
- `keyframe` accepts sparse `pose` keyed by bone ID and optional `label`, as an alternative to the full `angles` array. Unspecified angles use the current project pose. Recipe frames instead use their declared rest pose.
- Mutation receipts include the saved `revision`, bone IDs, asset count, frame count, duration and dry-run status. Reuse the revision for the next edit; another full inspection is unnecessary.
- `inspect` includes IDs, optional project name and frame labels; `sample` returns both indexed `angles` and named `pose`.
- Errors retain the old `error` string and add stable `error_code` plus optional `context`. Codes include `invalid_json`, `invalid_request`, `invalid_schema`, `invalid_recipe`, `unknown_bone`, `duplicate_id`, `duplicate_time`, `hierarchy_cycle`, `asset_unreadable`, `validation_failed`, `replacement_required`, `already_exists`, `revision_conflict`, `write_failed`, `unknown_command`, and `io_error`.

The single-request `scripts/agent.py` bridge exits 1 for an API error. The persistent binary continues after individual request errors; check every response's `ok` field.

## Artwork placement and bone deletion

`set_bone.values` additionally supports `imageOffsetX` and `imageOffsetY`. Values are finite pixels along the bone's local axes, after its rotation. Missing or null values mean zero, so old projects retain their original appearance. Offsets move only embedded artwork. Bone origins, descendants, image dimensions, pivots and keyframes remain unchanged. Recipe bones accept the same optional fields. `inspect` exposes stored offsets and `capabilities.imageOffsets` reports support. Offsets are static rig properties and apply to every animation frame. Import and replacement retain offsets.

The editor exposes **Image X**, **Image Y**, **Move image** and **Reset image position**. In Move image mode, drag inside the selected image rectangle. The selected artwork takes priority over overlapping rectangles; otherwise the topmost visible image is selected. Transparent margins are part of the hit rectangle. Disable Move image to restore normal bone rotation and Shift-drag bone movement. Drag names in the left parts list to control which image covers a joint.

`delete_bone` accepts `bone` as a stable ID or index. By default it deletes only a leaf. If the bone has children, it returns `bone_has_children`; explicitly supply `include_descendants:true` to remove its full subtree. The flag must be a boolean. Deleting every bone is rejected. Remaining parent indices and every keyframe's angle array are remapped while IDs, artwork, poses, labels and times of surviving bones are preserved. The command supports revision checks, batch and dry run. The SDK pins its revision automatically. GUI deletion displays the affected descendant count and requires confirmation. Save persists the result. GUI deletion can be undone with Command-Z during the current editing session. API mutations do not participate in GUI history.

Run `tests/image_offsets.py` and `tests/bone_editing.py` with the Pillow Python for regression coverage. Native PNG/sprite-sheet rendering and both export bridges retain image placement.

## Layer list order

`reorder_layers` requires `order`, a front-to-back array containing every bone exactly once. Selectors accept stable bone IDs or integer indices. Include hidden/control bones; their placement does not make them visible. The command assigns distinct descending layer ranks and changes no bone array indices, hierarchy, transforms, artwork, offsets, or keyframes. Invalid or duplicate/missing selectors fail without saving. Batch, dry run and revision checks use the existing transaction path; the SDK pins revisions automatically. `capabilities.layerReordering` advertises support.

The editor has one flat parts list with the frontmost image at the top. Drag locally and drop between names. There is no layer/hierarchy mode switch and no numeric Layer field in the inspector. Bone parent indices remain independent of display order. Equal numeric layers render in original bone-index order, with later indices in front.

Run `tests/layer_ordering.py` with the Pillow Python for native pixel compositing, save/reopen, unchanged skeleton and animation, invalid-order rollback, dry run and stale-revision coverage.


## GUI undo history

Edit → Undo (Command-Z) and Redo (Command-Shift-Z) restore in-memory project snapshots, selection and time. The bounded 100-action history includes layer reorder, canvas gestures, committed properties, image reset/import/replacement, add/delete bones and keyframes. A complete mouse drag is one action. No-op edits do not consume history. New/Open clear history; Save preserves it. Undo does not revert the current file URL or revision receipt. While typing, the field editor handles text undo separately. Commit and focus the parts list/canvas for project undo.

`tests/undo_history.py` compiles the actual editor against a native AppKit history harness. `tests/undo_gui.mjs` runs via the Computer Use Node REPL against a separate app and fresh fixture directory. History is session-local and is not serialized into .rig2d files.

### Workspace camera and rig handles

The native workspace clips artwork and overlays to its bounds. Wheel scrolling over it zooms around the cursor, middle-button dragging pans, and Fit frames visible artwork in the current pose. Camera state is local to the editor session and does not change the shared export renderer or project schema.

With Bones visible and Move image disabled, the selected joint shows world X/Y translation arrows and a free-move center. Moving it converts the world delta into the parent coordinate space; descendants follow. This changes the rig attachment for all frames, since animation keyframes store angles only.

Numeric bone properties other than Parent have continuous sliders. Typed values outside the default slider range expand it. Each slider drag creates one project undo action. The inspector scrolls vertically to expose lower controls.
