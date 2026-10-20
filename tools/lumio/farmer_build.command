#!/bin/zsh
# Double-click on the Mac: builds the Farmer rig with the native RigAndBone2D app, checks it, renders a preview,
# and exports the SpriteKit atlas into a NEW versioned folder. Stops at the first error. Output: Exports/iOS/char_farmer/vNNN
set -eu
cd "$(dirname "$0")/../.."
RIG_PYTHON="${RIG_PYTHON:-/Users/macminim4pro/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3}"
[[ -x "$RIG_PYTHON" ]] || RIG_PYTHON=python3
python3 scripts/lumio/build_farmer_recipe.py
N=1; while [[ -e "rigs/lumio/farmer/v$(printf %03d $N)" ]]; do N=$((N+1)); done
V="v$(printf %03d $N)"; JOB="rigs/lumio/farmer/$V"; mkdir -p "$JOB"
python3 scripts/rig_pipeline.py build recipes/lumio/farmer.rigrecipe.json --project "$JOB/Farmer.rig2d" --dry-run
python3 scripts/rig_pipeline.py build recipes/lumio/farmer.rigrecipe.json --project "$JOB/Farmer.rig2d" --log "$JOB/build-session.json"
python3 scripts/rig_pipeline.py check "$JOB/Farmer.rig2d" --strict
"$RIG_PYTHON" scripts/rig_pipeline.py preview "$JOB/Farmer.rig2d" --output "$JOB/preview" --fps 15 --strict
"$RIG_PYTHON" scripts/rig_pipeline.py spritekit-export "$JOB/Farmer.rig2d" --config recipes/lumio/farmer.spritekit.json --output "Exports/iOS/char_farmer/$V"
echo "DONE: $JOB  and  Exports/iOS/char_farmer/$V"
echo "Look at $JOB/preview (GIF + sheet) and tell Claude what looks wrong."
