# curated140 Qwen panorama baseline — campaign archive

Task t_ed447ffc，授權 exact Vast60649163，2026-11-14 啟動。

這是已執行campaign的程式／控制記錄，不是可跨機器直接跑的泛用套件。不要對舊路徑盲目重新執行。

- 遠端 `/root/HY-World-2.0/deployment/t_ed447ffc`；tmux `hermes:hypano140-ted44`。
- `controller.py prepare`：從實際metadata與檔案凍結140 variant IDs，70photo先、70stylized後；139 unique image-content hashes，保留不同variant條件。
- 預檢5個舊baseline的source path/hash、nested原prompt、有效prompt、settings、source/model revisions與原PNG decode/hash，全部匹配才reuse；本輪5個符合，135個預計新生成。
- 生成沿用已實測的cold-process worker，每圖seed42、1952×960、40steps、bf16、trueCFG7.5、guidance1、blend32、crop0、無quant/offload。輸出RGB1920×960。
- `controller.py run`：逐張log/config/result/exit/GPU CSV；1200s/sample、10GiB disk reserve；兩次連續環境/CUDA error暫停；失敗與不完整attempt保留，沒有自動重試／換seed／品質篩選。共享GPU flock，先檢查原工作後才能resume。
- 完成的新/舊PNG均新跑 spherical-check v0.2.0 八yaw＋兩極、512²、水平垂直FoV90；verify所有decoded image／hash，另存315→0比較。QA review維持pending，自動投影不代表目視或品質通過。
- `snapshot.py`凍結10條件的不可變transfer tar與逐檔manifest；`backup.py`使用canonical wrapper傳回，驗tar與每個原檔bytes/SHA256，再產生繁中README、index及cohort/page sheets。原始execution時間／路徑／log保留在reuse imports。
- `wait_and_backup.py`：等待tmux完成事件後重新讀progress，再決定是否備份；通知代表完成，不代表成功。僅私有waiter config延長command_timeout至28800，其餘identity/trust欄位與canonical完全相同；所有其他命令使用原config。waiter timeout不重播GPU工作。

完整來源/HF revisions、模型檔案SHA、input metadata、設定、log與輸出不提交GitHub；它們在獨立本機結果資料夾與遠端campaign中。

本機目的地：`/home/pierce/Documents/research/E3DQA/hypano-qwen-results/full-curated140-20261114T142156Z/`（realpath已確認不在Vault）。

已實測：actual遠端Python3.11 venv的6個controller測試、13個spherical-check測試通過；首個新樣本0003已完成生成／QA，load14.347s、inference136.442s，原PNG hash 4a4bd0c38660bb44920306367e95e604a64a1a5ad0dec7c6f20922b3aa011b5c。此記錄不宣稱全批已完成；終態依最終progress、transfer receipt與PM review為準。

沒有重建venv、改driver/services、生命週期操作、其他World2階段或刪除研究資產。

## 最終保存稽核（2026-11-15）

原controller於2026-11-14T20:18:38Z DONE、exit0，140成功／0失敗／0待生成；新135、沿用5，兩cohort各70。先前SSH observer255造成備份中斷，並非推論失敗；解鎖既有dedicated key後只恢復備份，沒有重跑生成。

`audit_final.py`為本次在原workspace實際執行的唯讀獨立稽核存檔，保留絕對local destination規則，依`local_destination.json`讀取既有資料，且拒絕覆蓋既有final_audit.json。與backup.py產生的4092個去重原檔、1028947566 bytes逐檔大小/SHA256一致；140張原始RGB1920×960與1400張RGB512²球面圖解碼通過，逐variant原prompt、有效prompt、seed42及固定settings／revisions、exit/timing/GPU取樣、沿用出處均核驗。五個終態檔另以遠端／本機sha256sum比對一致。

本機index.html、兩cohort大圖／14張10條件分頁、逐樣本source→ERP／spherical／315→0均已產生。Agent實看兩頁共20條件來源→ERP縮圖，線索見本機AUDIT_NOTES_zh.md；沒有聲稱完整個別球面目視，140個review仍pending。兩個monitor已讀回paused。交PM review／原Discord thread統一交付，不代表品質或3D驗收。
