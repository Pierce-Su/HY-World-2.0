# Vast 60649163：HY-Pano 2.0 Qwen 單圖部署驗證

2026-11-14，task t_1e9a7907。只驗證 Qwen image→panorama，沒有跑 bulk dataset 或其他 World2 階段。

## 實測結果

- A100-SXM4-80GB；driver 595.91.07。cgroup memory.max=730298580992 bytes，不把 host 的 2Ti RAM 當成配額。
- 上游與既有 Pierce-Su fork HEAD 均為 `df9988efb87bfc0f4947eb3889411cf957478b06`，沒有修改 upstream tracked code。
- torch 2.7.1+cu128、torchvision 0.22.1+cu128 保留原模板；Python 3.11；diffusers 0.36.0、transformers 4.57.1、peft 0.18.1、accelerate 1.15.0、huggingface_hub 0.36.2、numpy 2.2.0、tokenizers 0.22.0、safetensors 0.7.0、Pillow 11.0.0。pip check 無衝突。
- 基模 Qwen/Qwen-Image-Edit-2509 revision `d3968ef930e841f4c73640fb8afa3b306a78167e`；LoRA tencent/HY-World-2.0 revision `d78a16c91c7a56488894a1c8de4f5c7cc28aa8b0`，只取 `HY-Pano-2.0/pytorch_lora_weights.safetensors`。全部所需 LFS 檔案按 HF SHA256 驗證；未下載 HunyuanImage3 shards。
- 輸入：既有 `curated_set/photorealistic/0000.jpg`（咖啡館、1080×740），SHA256 `34e268fa5e3b7ce4b348a9847142d9edadc6f08b0201c69410663c107b50ab68`。用其原 metadata prompt，未上傳本機 bulk assets。
- seed42；40 steps、1952×960、bf16、true CFG7.5、guidance1.0、blend32、crop0，均為上游預設。未啟用量化、offload、縮圖、cache 或 flashinfer。
- 成功保存 RGB PNG 1920×960（左右 blend 後裁去32px）；SHA256 `e37115e00b30ccfb564e64b6725f588320c8e873e25ab324c23f32056ea0d714`。終態 `pilot.exit=0`。
- load 14.6925s；inference（含條件編碼／採樣／VAE decode）136.5568s；load→保存及解碼核對 152.0519s，不含下載／安裝／事後 QA。log 的40步採樣約132s，不混稱 cold-start。
- torch peak allocated=66596313088 bytes、reserved=67872227328 bytes（含 load+inference）；nvidia-smi 每約1秒取樣146次，total device memory.used sampled max=65249 MiB、util sampled max=100%。取樣最大值不是連續真實峰值。
- spherical-check v0.2.0 在此 venv 跑13 tests通過；產生10張512²、90°×90° pinhole views（八方位＋兩極），14個影像輸出全部解碼及 SHA256 檢核。agent 視覺檢查完成，manifest=reviewed_2d、visual_verdict=review。
- 不是黑圖／壞圖，咖啡館風格、整圈和前景可辨識，180 wrap和315→0未見巨大硬接縫。細節重繪、重複瓶罐／桌椅、局部形變與模糊仍在；不是人工品質批准或3D正確性驗證。見 visual_review.md。

## 精確遠端位置

Project `/root/HY-World-2.0`
Activate `source /root/HY-World-2.0/.venv-qwen-pano/bin/activate`
Evidence root `/root/HY-World-2.0/deployment/t_1e9a7907`
Input `/root/HY-World-2.0/curated_set/photorealistic/0000.jpg`
Output `/root/HY-World-2.0/deployment/t_1e9a7907/pilot_0000/panorama.png`
QA `/root/HY-World-2.0/deployment/t_1e9a7907/pilot_0000/panorama_spherical_check`
Base `/root/.cache/huggingface/hub/models--Qwen--Qwen-Image-Edit-2509/snapshots/d3968ef930e841f4c73640fb8afa3b306a78167e`
LoRA root `/root/.cache/huggingface/hub/models--tencent--HY-World-2.0/snapshots/d78a16c91c7a56488894a1c8de4f5c7cc28aa8b0`
Logs `setup.log`, `download.log`, `pilot.log` 與各自 `.exit`；`pip-freeze.txt`、`pip-check.txt`、`hf-inventory.json`、`models.json`。
Pilot `config.json`、`result.json`、`gpu_samples.csv` 位於 pilot_0000，包含完整有效 prompt、輸入 provenance、HF revision和GPU量測。

遠端工作使用 hermes session 的 hypano-setup / hypano-download / hypano-pilot 專用 windows；各 phase 結束後 window 自動關閉，完成狀態與 log 留在上列路徑。handoff 提供 hermes:hypano-evidence 工作目錄 shell。登入後 `tmux attach -t hermes`，選 hypano-evidence；原 ssh_tmux 沒有被注入指令。

## 檢查／接續

唯一遠端入口（下列 READ_COMMAND 換成讀取指令，不要把整串 command 當成 executable）：

    /home/pierce/vast-ssh-workflow/vast-ssh --config /home/pierce/.config/vast-ssh/config.json --non-interactive --id 60649163 -- bash -lc 'READ_COMMAND'

先看 pilot.exit、pilot_0000/result.json、GPU process，再決定接續；完成不需要重跑。download.py 固定 HF revision 且可使用 cache 接續，不能因 waiter timeout 就重開下載。setup.sh / download.sh / pilot.sh / pilot.py 是這個 task 的 archival execution record，硬編碼上述專用路徑，不宣稱泛用部署器。pilot.py 拒絕既有 pilot_0000，以防覆寫；finalize_qa.py 同樣只允許 pending→reviewed 一次，不要當成可重複 controller。

如另外獲准再跑一張，在 dedicated tmux window 使用下列已驗證 API 相同的官方 CLI；換全新 --save，不動原輸出（此文件的命令本身未另外執行，避免第二次未要求推論）：

    source /root/HY-World-2.0/.venv-qwen-pano/bin/activate
    cd /root/HY-World-2.0/hyworld2/panogen
    HF_HUB_OFFLINE=1 python pipeline_with_qwen_image.py \
      --pretrained-model-name-or-path /root/.cache/huggingface/hub/models--Qwen--Qwen-Image-Edit-2509/snapshots/d3968ef930e841f4c73640fb8afa3b306a78167e \
      --lora-path /root/.cache/huggingface/hub/models--tencent--HY-World-2.0/snapshots/d78a16c91c7a56488894a1c8de4f5c7cc28aa8b0 \
      --lora-subfolder HY-Pano-2.0 \
      --image /root/HY-World-2.0/curated_set/photorealistic/0000.jpg \
      --prompt 'In the Cozy Café, a warm ambiance envelops the bar counter and dining tables topped with inviting chairs.' \
      --seed 42 --height 960 --width 1952 --num-inference-steps 40 \
      --guidance-scale 1.0 --true-cfg-scale 7.5 --blend-width 32 --crop-border 0 \
      --save /root/HY-World-2.0/deployment/t_1e9a7907/NEW_AUTHORIZED_RUN/panorama.png

固定 generator seed42，不保證不同機器／版本 bit-identical。`--reproduce` 沒有在本次使用，不要偷偷加入改設定。上游 warning：guidance_scale1.0 對非 guidance-distilled 模型被忽略（true CFG7.5仍生效）；torch_dtype deprecated warning 不阻止 load。沒有 source patch。

## 安裝與保存限制

此輪已實際安裝和執行，但不是 clean-room rebuild 測試。setup.sh 保留 torch/CUDA並僅裝 Qwen 路徑所需依賴，不裝 root requirements.txt 的 reconstruction stack。完整 pip-freeze 包含繼承模板套件，只是環境證據，不是建議全套重裝檔。

本機沒有 gh、沒有已設定 HTTPS credential helper；GitHub SSH read attempt 因 host-key verification failed，未改 trust／複製憑證。程式與證據會作 task archive／Git bundle 保存；若本輪不能推送，需 PM 用既有授權 GitHub 連線發佈，不能把本機 commit 當成已 push。此限制不影響已完成遠端推論，仍需 PM 獨立讀回 artifact。無 lifecycle／driver／service 變更，未刪除 user assets。
