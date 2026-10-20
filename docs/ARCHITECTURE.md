# Architecture — 0.2

Character data is declarative. Both the native editor and agent transport share the same project model, validation, animation sampler, renderer and persistence layer.

```text
Sprite sheet + asset manifest → shared asset preparation → PNG parts
Recipe (IDs, parents, pivots, poses) → RecipeCompiler → Project
Human → Editor ──────────────────────────────────────────┐
Agent → JSONL AgentAPI → ProjectCommands / RecipeCompiler ├→ ProjectCore
                                                        └→ ProjectStore
ProjectCore → Stage renderer → transparent PNG → shared quality checks / preview
ProjectStore → writer lock + revision check + atomic .rig2d replacement
```

| Module | Responsibility |
| --- | --- |
| `Project.swift` | Version 1 model; optional persistent IDs, visibility, character name and phase labels |
| `ProjectCore.swift` | Validation, animation sampling and offscreen rendering |
| `ProjectStore.swift` | Legacy ID normalization, SHA-256 revisions, writer locks and atomic persistence |
| `ProjectCommands.swift` | Named/indexed selectors and model mutations; independent of transport |
| `RecipeCompiler.swift` | Authoritative recipe schema, strict fields, topology sorting, image binding and fresh timeline compilation |
| `RigError.swift` | Machine-readable error code, message and context |
| `Stage.swift` | Forward kinematics, artwork draw order, interactive selection and drag |
| `Editor.swift` | Mac UI; remembers loaded revision to detect stale saves |
| `AgentAPI.swift` | JSONL routing, transactional batches and structured receipts |
| `scripts/rigtools/client.py` | Provider-independent local SDK, revision cache, timeout and transcripts |
| `scripts/rigtools/assets.py` | Versioned sprite extraction manifest and staged asset output |
| `scripts/rigtools/quality.py` | Loop checks, rendered frame checks and common preview packaging |
| `scripts/rig_pipeline.py` | Shared prepare / build / check / preview / schema entry point |
| `recipes/` | Character-specific asset and rig data; no executable instructions |

## Persistence contract

All 0.2 app/API writers use a common hidden `.<project-name>.lock` sidecar. A write holds an exclusive OS lock while comparing the expected revision and atomically replacing the file. API edits always compare against the revision they loaded, even when a caller omits its own expected revision. The GUI compares with the revision it loaded when saving back to that file. A competing writer causes a conflict, not a stale overwrite. Sidecars remain present; deleting them while a writer is active could create independent locks.

This coordination covers participating writers using ProjectStore. Manual JSON editors, old application versions, and other programs do not follow that lock contract. The GUI does not automatically reload external edits; reopen to see agent changes. A Save As to a different file uses the user's file panel overwrite choice.

## Compatibility and versions

JSONL protocol and stored project schema remain version 1; new features are additive. Existing integer-based commands and old demo projects pass integration tests. Legacy bones receive IDs `bone-0`, `bone-1`, etc. on load; IDs persist on the next save. Recipe-authored IDs remain independent of declaration order and display-name edits. Internally, parent references and frame angles still use compact ordered arrays.

Recipe schema version 1 is separate from the runtime project format. Future changes to clip tracks, asset storage or mesh data must declare their own migration and version contract. The schema returned by the running app is authoritative; the committed JSON copy is tested against it.

## Boundaries

Artwork is embedded in each project for portability. For larger libraries, a future schema can reference content-addressed assets with explicit packing and migration. The current model supports rigid sprites and angle keyframes. It has no mesh deformation, physics engine, collision simulation, multiple clip tracks, or built-in MCP server. These features should extend the shared core; adapters should call the existing API rather than duplicate its authoring rules.
