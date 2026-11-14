#!/bin/bash
set -Eeuo pipefail
RUN=/root/HY-World-2.0/deployment/t_ed447ffc
cd /root/HY-World-2.0
export HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false
exec >> "$RUN/controller.log" 2>&1
printf 'CAMPAIGN_START '; date -Is
exec /root/HY-World-2.0/.venv-qwen-pano/bin/python -u "$RUN/controller.py" run
