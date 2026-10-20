# Chibi asset and replacement work

- Ground: inspected source PNG, ProjectCommands, AgentAPI, Editor, Stage and shared asset workflow.
- Sketch: retain embedded per-bone artwork and add replace_image; reject a persistent skin library for this scoped delivery because it requires new project semantics and migrations.
- Agree: proceed within the requested feature scope.
- Implement: one writer owns replacement/API/UI/test files; primary owns character recipe, asset manifest and visual review.
- Scrap: no speculative framework or schema migration.

## Throughput checkpoint

- Blocking first steps: image alpha/crop inspection and repository instructions before extraction; DESIGN.md before native UI edit.
- Independent workstreams: character preparation and replacement implementation use separate paths.
- Shared mutable state: one rig writer; one release build; replacement batches use existing ProjectStore transaction and revision checks.
- Smallest safe decomposition: one feature owner and one character preparation owner. Existing renderer and sampler remain authoritative.

## Verification plan

Build app; run required smoke/workflow/orientation/reproducibility checks and replacement behavior test. Build recipe with shared pipeline; inspect rendered rest and animated poses, preview quality report and selective replacement evidence.
