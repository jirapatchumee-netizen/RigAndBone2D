# Layer dragging

Keep the stored bone array and parent graph unchanged. A Layers view projects the shared draw order in reverse, placing the frontmost artwork at the top. A Bones view retains the hierarchy. Dragging in Layers supplies the full order to one mutation that changes layer ranks only.

- Blocking first steps: read selection, rendering and hierarchy mappings before changing table rows.
- Independent workstreams: one implementation owner edits Swift and DESIGN; primary owns SDK, behavior tests and documentation.
- Shared mutable state: single source/build writer and one GUI test project writer.
- Smallest safe decomposition: one implementation owner for table mapping, drag operation and shared command; no new project schema.

Verify local drag upward and downward on the real table, native render compositing, saved/reopened order and unchanged skeleton/animation. API rejection and rollback checks cover stale revisions and malformed permutations.
