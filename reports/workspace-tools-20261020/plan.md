# Workspace controls

## Shape

Keep camera state separate from rig data. One viewport transform must serve drawing, hit testing, wheel zoom and dragging. Explicitly clip the Stage draw context to its own bounds. Bone axis handles transform world movement into parent-local coordinates; they do not change artwork offsets. Slider changes use existing undo snapshots, with one action per complete drag.

## Throughput checkpoint

- Blocking first steps: inspect Stage drawing and pointer transforms, snapshot lifecycle and inspector constraints before edits.
- Independent workstreams: one Swift implementation owner; primary writes native behavior tests, UI verification and documentation.
- Shared mutable state: only one release build writer. Use a new Chibi copy for GUI verification and preserve open user sessions.
- Smallest safe decomposition: Stage camera/gizmo and Editor sliders share the same owner because they share gesture/undo boundaries.

## Verification

Native camera anchor and roundtrip checks; Fit transformed art bounds; bitmap inspection outside Stage; parent-rotation axis movement; slider undo grouping; real wheel/gizmo/slider interaction on Chibi; unchanged export orientation/pixels and existing agent workflows.
