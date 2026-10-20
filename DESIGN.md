# RigAndBone2D native editor

The editor uses native macOS AppKit controls. Preserve existing layout and system typography.

- Stage background RGB 0.055, 0.075, 0.12; grid white at 0.04 alpha.
- Bone overlays use system teal; selected bone and joint dots use system yellow.
- Inspector width 280 points, horizontal inset 14 points, label width 65 points.
- Use system fonts, secondaryLabelColor for help, and rounded NSButton controls.
- Keep asset replacement beside the selected bone properties. Import fits aspect ratio; replacement retains geometry and pivots. Tell users to align new artwork on the same normalized canvas.
- Image X/Y edit artwork offsets in local bone pixels. Move image enables dragging artwork while joints stay fixed; show a yellow artwork rectangle in that mode. Reset image position clears both offsets.
- Add child bone and Delete bone live beside artwork controls. Deletion asks for confirmation naming the bone and descendant count; keep at least one bone.
- Put the inspector in a vertical scroll view so all properties remain reachable at the minimum window size.
- Use the existing NSOpenPanel and NSAlert patterns. Save continues through ProjectStore.

Design discovery on 2026-10-20: `designmd search "dark animation editor"` returned `No kits found.` These specifications are taken from the existing Editor.swift and Stage.swift.

- The left sidebar has one flat front-to-back PARTS list with the hint "Drag up = front · Drag down = back". Drag a row between rows to change only draw order. Keep selection bound to the bone when reordering. Hidden bones remain listed and tagged. Bone parenting stays unchanged by reordering.

- Draw order is edited directly by dragging names in the left list. Do not add Layers/Bones modes or expose an editable numeric Layer inspector field.
- Edit menu uses native Command-Z undo and Command-Shift-Z redo. Project history retains at most 100 complete editing actions in memory. A canvas drag forms one action; clicks, scrubbing, playback and unchanged values do not form actions.
- History covers layer reorder, committed inspector values, artwork import/replacement/reset, bone addition/deletion and keyframe addition/deletion. Undo stops playback and restores the action's selected bone and timeline position. New/Open clear project history; Save preserves it. File path and persistence revision are never rewound.
- Inspector text editing retains native text undo in a separate field-editor history. While typing, Command-Z edits the text. Press Return or leave the field to commit, then click the canvas or the parts list to use project undo. The field text history resets for each editing session.

- Stage drawing clips to its own rectangle, including bone overlays and axis handles. Export rendering retains its existing independent cell clip.
- Wheel zoom anchors to the cursor at 0.1× to 12×. Middle-button drag pans; Fit frames visible artwork with padding. Camera changes do not enter project history or saved rigs.
- Selected bones show red screen-X and green screen-Y arrows, plus a square for free movement. Dragging a handle moves its attachment and descendants. Hide these handles in Move image mode or when Bones is hidden.
- Numeric rig properties have a slider below their editable number. Name and Parent remain text inputs. Slider ranges expand to include valid typed values; a complete slider drag creates one undo action.
