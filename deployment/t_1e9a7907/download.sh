#!/bin/bash
set -Eeuo pipefail
RUN=/root/HY-World-2.0/deployment/t_1e9a7907
exec > >(tee -a "$RUN/download.log") 2>&1
trap 'rc=$?; date -Is; echo "$rc" > "$RUN/download.exit"; echo "DOWNLOAD_FINISHED rc=$rc"; tmux wait-for -S hypano-download-t_1e9a7907' EXIT
date -Is
source /root/HY-World-2.0/.venv-qwen-pano/bin/activate
python -u "$RUN/download.py"
