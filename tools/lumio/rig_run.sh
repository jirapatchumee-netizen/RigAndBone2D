#!/bin/zsh
# usage: zsh tools/lumio/rig_run.sh farmer
# Regenerates recipe from joints table + clips file, builds/checks/previews with the native app, exports SpriteKit atlas to NEW versioned folders.
set -eu
cd "$(dirname "$0")/../.."
CH="${1:?character name, e.g. farmer}"
RIG_PYTHON="${RIG_PYTHON:-/Users/macminim4pro/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3}"
[[ -x "$RIG_PYTHON" ]] || RIG_PYTHON=python3
python3 "scripts/lumio/build_${CH}_recipe.py"
N=1; while [[ -e "rigs/lumio/$CH/v$(printf %03d $N)" || -e "Exports/iOS/char_$CH/v$(printf %03d $N)" ]]; do N=$((N+1)); done
V="v$(printf %03d $N)"; JOB="rigs/lumio/$CH/$V"; mkdir -p "$JOB"
python3 scripts/rig_pipeline.py build "recipes/lumio/$CH.rigrecipe.json" --project "$JOB/${CH}.rig2d" --log "$JOB/build-session.json" >/dev/null
python3 scripts/rig_pipeline.py check "$JOB/${CH}.rig2d" --strict >/dev/null
"$RIG_PYTHON" scripts/rig_pipeline.py preview "$JOB/${CH}.rig2d" --output "$JOB/preview" --fps 15 --strict >/dev/null
"$RIG_PYTHON" scripts/rig_pipeline.py spritekit-export "$JOB/${CH}.rig2d" --config "recipes/lumio/$CH.spritekit.json" --output "Exports/iOS/char_$CH/$V" >/dev/null
echo "OK $V  preview: $JOB/preview/preview.gif  sheet: $JOB/preview/sheet.png  export: Exports/iOS/char_$CH/$V"
