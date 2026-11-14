#!/bin/bash
set -Eeuo pipefail
RUN=/root/HY-World-2.0/deployment/t_1e9a7907
exec > >(tee -a "$RUN/pilot.log") 2>&1
trap 'rc=$?; date -Is; echo "$rc" > "$RUN/pilot.exit"; echo "PILOT_FINISHED rc=$rc"; tmux wait-for -S hypano-pilot-t_1e9a7907' EXIT
date -Is
source /root/HY-World-2.0/.venv-qwen-pano/bin/activate
cd /root/HY-World-2.0
export HF_HUB_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
# Bound single-image job; no dataset loop or retries.
timeout --signal=TERM 3600 python -u "$RUN/pilot.py"
python -m unittest discover -s "$RUN/qa" -p test_spherical_check.py -v
python "$RUN/qa/spherical_check.py" --image "$RUN/pilot_0000/panorama.png" --source /root/HY-World-2.0/curated_set/photorealistic/0000.jpg
