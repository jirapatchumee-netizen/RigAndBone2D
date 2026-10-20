# Drag-first layer editing and undo

- Ground: current Layers view changes only draw ranks; GUI mutations are spread across editor and mouse gestures and currently have no history.
- Shape: one bounded native undo history stores project, selected bone and time. Document paths and revision receipts stay outside history.
- Blocking first steps: identify every GUI mutation and gesture boundary before registration.
- Independent workstreams: Swift implementation has one owner; primary owns UI behavior harness, evidence and docs.
- Shared mutable state: no edits to the user's running project; a separate test app uses its own fixture.
- Smallest safe decomposition: one history mechanism for discrete actions and begin/end gesture snapshots.

Verify real drag, Cmd+Z, Cmd+Shift+Z, saving without erasing history, one drag per undo, image movement, property commits and bone addition. Required existing API/render checks still apply.
