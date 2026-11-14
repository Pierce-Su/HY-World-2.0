#!/bin/bash
set -Eeuo pipefail
ROOT=/root/HY-World-2.0
RUN=$ROOT/deployment/t_1e9a7907
exec > >(tee -a "$RUN/setup.log") 2>&1
trap 'rc=$?; date -Is; printf "%s\n" "$rc" > "$RUN/setup.exit"; echo "SETUP_FINISHED rc=$rc"; tmux wait-for -S hypano-setup-t_1e9a7907' EXIT
date -Is
cd "$ROOT"
python -m venv --system-site-packages .venv-qwen-pano
. .venv-qwen-pano/bin/activate
python -m pip install 'einops==0.8.1' 'numpy==2.2.0' pillow 'diffusers==0.36.0' 'safetensors==0.7.0' 'tokenizers==0.22.0' 'transformers==4.57.1' 'huggingface_hub<1.0' 'accelerate' 'peft==0.18.1' 'loguru>=0.7.3' tiktoken
python -m pip freeze > "$RUN/pip-freeze.txt"
python -m pip check > "$RUN/pip-check.txt" || true
python -c 'import torch,transformers,diffusers,peft; print(torch.__version__,torch.version.cuda,transformers.__version__,diffusers.__version__,peft.__version__); import sys;sys.path.insert(0,"hyworld2/panogen");from pipeline_with_qwen_image import HunyuanPanoPipeline; print("IMPORT_OK")'
