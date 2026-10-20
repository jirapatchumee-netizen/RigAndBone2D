# Workspace controls verification

Release build and ad hoc signing passed using scripts/build-app.sh.

Passed native behavior checks via tests/workspace_tools.py for cursor-anchored zoom, scale limits, Fit, translation through a rotated parent with descendants, gizmo hit testing, slider action grouping with Undo/Redo, expanded ranges and actual Stage.draw clipping. The clipping check renders onto a larger bitmap and verifies every pixel outside the stage stays white.

Passed agent_smoke.py, agent_workflow.py (15 cases), render_orientation.py, demo_reproducibility.py and undo_history.py. Reproduced demo poses and sprite images remain unchanged.

Live GUI on a copy of Chibi confirmed wheel zoom, Fit, clipping, X-axis dragging and Command-Z. The torso X value changed from 0 to 16.69 and returned to 0. Slider track click changed Angle from 0 to 63.33 and Command-Z returned to 0.

Sky knob drag did not move either the new property slider or the existing native timeline slider. Therefore native continuous-action Undo grouping is covered by the native harness; physical knob dragging is not confirmed by GUI automation. Native NSSlider tracking is retained.

fit.jpg and wheel-zoom.jpg capture the live workspace. Original Chibi file SHA256 remains af0962772e68cbc4c85fa8c306a4aa0426623b8f48b2c4067bfec0f01554572c.

No original project or existing user app session was modified. Camera changes apply only to the editor session. Rig translation affects all animation frames; keyframes remain angle-only. Fit covers the current pose, not the motion envelope.
