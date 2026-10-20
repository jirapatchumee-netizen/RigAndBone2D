# SpriteKit baked handoff v1

Export via `scripts/rig_pipeline.py spritekit-export PROJECT --config CONFIG --output NEW_DIRECTORY` using Python with Pillow. This adapter calls the shared native validator, sampler and renderer with a pinned SHA-256 revision. No rig data is modified. Source revision is checked again before publishing. Empty frames, clipping at the native 384px canvas boundary, invalid loops, atlas overflow and an existing destination fail the job without publishing a partial package.

## Config v1
Required: schemaVersion=1, id, licenseRecordID, clips. Optional: renderScale=0.5 (0.25..1 and integral 384*scale), pixelsPerUnit=1 (0.5..4), canvasPivot=[192,192] (native 384px coordinates), maxAtlas=2048 (256/512/1024/2048), fps=15 (integer 1..30).
Each clip: name, start, end, loop=false, events=[]; each event: name, time relative to clip. Events must lie in [0,length), unique names per clip. Ranges must satisfy 0<=start<end<=project duration; length*fps is integral. At most 600 sampled frames across 32 clips. Loop endpoints use the native sampled angles and must match. Non-looping clips omit the exact end frame and play until length; author recovery before that boundary.

## Manifest v1 / runtime files
Only atlas.png and manifest.json belong in runtime packages. Manifest: schemaVersion, assetID, licenseRecordID, sourceRevision, coordinateSystem="pixels-top-left-y-down", pixelsPerUnit, atlasFiles (file, SHA-256, [width,height]), frames, clips, runtimeFiles, metrics and visualReviewRequired.
Frame: name, atlas, rect=[x,y,width,height], originalSize=[width,height], trimOffset=[left,top], pivot=[x,y] relative to untrimmed canvas, sourceTime in original animation. All positions are pixels, Y down. Pivot is scaled along with the native canvas and is not recomputed from the trim. Clip: name, length, loop, ordered frames, durations and visualEvents.

## SpriteKit mapping
For atlas W,H and rect x,y,w,h, normalized SKTexture region is [x/W,1-(y+h)/H,w/W,h/H]. SKSpriteNode anchorPoint=(0,0), size=(w/density,h/density). Its bottom-left offset from the actor root is ((trimX-pivotX)/density,(pivotY-trimY-h)/density). This preserves the same original-canvas anchor across variable trims. Example: atlas 256x256, rect [20,30,40,50], trim [7,11], pivot [90,130], density=2 => UV [0.078125,0.6875,0.15625,0.1953125], offset [-41.5,34.5]. Do not mirror UVs to fix orientation; the formula already converts Y.

The consumer validates manifest dimensions, paths, frame/clip references and durations, atlas hash and decoded dimensions before creating textures. One package instance owns shared atlas textures and frame subtextures; actor nodes retain that package instead of loading duplicates. Preload before attaching final art. Actor animation consumes elapsed presentation time; pause must stop advancing it. Visual events are exposed for effects only, never damage.

## Optimization and limitations
Frames are native-rendered rigid cutouts, downsampled without upscaling, trimmed, exact-pixel deduplicated and shelf-packed with two extruded pixels around every region. One atlas only; budget overflow rejects the package. This is a lossless PNG source payload, not a GPU compression choice. rgba8BaseBytes=width*height*4 estimates one base RGBA8 level, not measured GPU/process memory. atlasPNGBytes is measured disk size. Frame swaps can consume more texture memory than a cutout hierarchy; benchmark before producing a roster.
No runtime skeleton, sockets, mesh deformation, lighting changes or pose blending are exported in v1. The native renderer remains 384x384. Higher-detail authoring requires a separately versioned renderer extension. Shadow should be rendered separately by the game.

## Tests
Run build-app.sh, tests/agent_smoke.py, tests/agent_workflow.py, tests/render_orientation.py, tests/demo_reproducibility.py and tests/spritekit_bridge.py (last three with Pillow Python). The bridge test reconstructs every trimmed frame and compares exact pixels to independently rendered native poses, checks extrusion, relocation, immutable destinations, malformed ranges, overflow, clipping and changed source revision. The game consumer has coordinate/time/texture-sharing/checksum tests in its Swift package. Review native key poses and the actual iPhone scene as a separate visual gate.
