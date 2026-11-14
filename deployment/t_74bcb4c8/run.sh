#!/bin/bash
set -Eeuo pipefail
RUN=/root/HY-World-2.0/deployment/t_74bcb4c8
exec > >(tee -a "$RUN/controller.log") 2>&1
trap 'rc=$?; date -Is; printf "%s\n" "$rc" > "$RUN/controller.exit"; echo "FOUR_FINISHED rc=$rc"; tmux wait-for -S four-t_74bcb4c8' EXIT
date -Is
source /root/HY-World-2.0/.venv-qwen-pano/bin/activate
cd /root/HY-World-2.0
export HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false
python -m unittest discover -s /root/HY-World-2.0/deployment/t_1e9a7907/qa -p test_spherical_check.py -v
echo START_photorealistic_0106
set +e
timeout --signal=TERM 1200 python -u "$RUN/photorealistic_0106.py" > "$RUN/photorealistic_0106.log" 2>&1
rc=$?
set -e
printf "%s\n" "$rc" > "$RUN/photorealistic_0106.exit"
test "$rc" -eq 0
cp -- "/root/HY-World-2.0/curated_set/photorealistic/0106.jpg" "$RUN/photorealistic_0106/source.jpg"
python /root/HY-World-2.0/deployment/t_1e9a7907/qa/spherical_check.py --image "$RUN/photorealistic_0106/panorama.png" --source "$RUN/photorealistic_0106/source.jpg"
echo DONE_photorealistic_0106
echo START_photorealistic_0501
set +e
timeout --signal=TERM 1200 python -u "$RUN/photorealistic_0501.py" > "$RUN/photorealistic_0501.log" 2>&1
rc=$?
set -e
printf "%s\n" "$rc" > "$RUN/photorealistic_0501.exit"
test "$rc" -eq 0
cp -- "/root/HY-World-2.0/curated_set/photorealistic/0501.jpg" "$RUN/photorealistic_0501/source.jpg"
python /root/HY-World-2.0/deployment/t_1e9a7907/qa/spherical_check.py --image "$RUN/photorealistic_0501/panorama.png" --source "$RUN/photorealistic_0501/source.jpg"
echo DONE_photorealistic_0501
echo START_stylized_0005
set +e
timeout --signal=TERM 1200 python -u "$RUN/stylized_0005.py" > "$RUN/stylized_0005.log" 2>&1
rc=$?
set -e
printf "%s\n" "$rc" > "$RUN/stylized_0005.exit"
test "$rc" -eq 0
cp -- "/root/HY-World-2.0/curated_set/stylized/0005.jpg" "$RUN/stylized_0005/source.jpg"
python /root/HY-World-2.0/deployment/t_1e9a7907/qa/spherical_check.py --image "$RUN/stylized_0005/panorama.png" --source "$RUN/stylized_0005/source.jpg"
echo DONE_stylized_0005
echo START_stylized_0084
set +e
timeout --signal=TERM 1200 python -u "$RUN/stylized_0084.py" > "$RUN/stylized_0084.log" 2>&1
rc=$?
set -e
printf "%s\n" "$rc" > "$RUN/stylized_0084.exit"
test "$rc" -eq 0
cp -- "/root/HY-World-2.0/curated_set/stylized/0084.jpg" "$RUN/stylized_0084/source.jpg"
python /root/HY-World-2.0/deployment/t_1e9a7907/qa/spherical_check.py --image "$RUN/stylized_0084/panorama.png" --source "$RUN/stylized_0084/source.jpg"
echo DONE_stylized_0084
