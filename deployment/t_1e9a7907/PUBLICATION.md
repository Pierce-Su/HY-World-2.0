# Publication follow-up / 發佈補記

本輪 HTTPS Git push 已實際成功，不是 publication blocker。雖然 gh 未安裝、credential.helper 查無設定、SSH host-key check 不通，這些都不等於 HTTPS Git 沒有現成授權。直接使用既有 origin 的非互動 HTTPS git push 成功；沒有提取、搬移或顯示任何 credential，也沒有改 SSH trust。

GitHub branch：
https://github.com/Pierce-Su/HY-World-2.0/tree/deploy/qwen-pano-t_1e9a7907

部署 code / docs 首次 commit：2f126833895d6d9c45e415208cbae92ec15727e0；已透過 git ls-remote 獨立讀回相同 SHA。後續補記 commit 只補本說明。main 保持 df9988efb87bfc0f4947eb3889411cf957478b06，沒有 merge、PR或 CI 通過聲明。

發佈僅有 explicit allowlist 的 setup/download/pilot/QA scripts、HF inventory、版本 snapshot及繁中 handoff／review；不含 credentials、input/output images、GPU logs、weights、venv、curated dataset。遠端 upstream source 沒有 patch；這些是新增的 archival deployment records。

本檔補足早期 HANDOFF.md 末段「如不能推送則交 PM」的條件式提醒；本次已推送，所以不需要 PM 補推。

本機 evidence zip：hypano-qwen-t_1e9a7907-evidence.zip，6542921 bytes，SHA256 e9fffdd5790b4773fcd24dc5aff5a968bbb20865de76c701826e5ddc6a278019；遠端和本機 byte/hash一致，zip integrity test全數通過。原 zip 是推送前的 execution snapshot，保留不重寫。此補記獨立保存。
