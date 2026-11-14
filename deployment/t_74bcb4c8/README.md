# HY-Pano 2.0 Qwen：四張混合風格探索預覽

本輪只在 Vast 60649163 新生成四張，不重用舊0000、不加跑、不修圖、不挑種子。全部執行／RGB1920×960解碼通過；四張agent視覺結論均為「review／研究品質待審」，不是使用者批准，也未驗證3D。

## 先看這些

1. contact_sheet.jpg：依左上、右上、左下、右下為0106、0501、0005、0084。每格上方為原透視圖，下方為全景縮圖，非配準比較。
2. 各sample/comparison.jpg：更大的原圖→ERP對照；panorama.png才是原尺寸、未重新編碼的生成全景，source.jpg是原資料集透視圖。
3. 各sample/spherical_preview.jpg：第一排yaw0/45/90/135、第二排180/225/270/315、第三排天極／地極。皆512²、水平／垂直FoV90°；yaw180對應左右wrap，亦檢查315→0。
4. panorama_spherical_check/內有10張完整PNG投影、manifest、review.md；provenance/放config、結果、GPU取樣和log。原source FoV未知，不能做像素保真或真實3D推論。

## 選樣與固定設定

- photorealistic_0106：室內客廳，補足舊咖啡館以外房間類型。
- photorealistic_0501：室外山湖木屋，觀察山、天空、水面反射。
- stylized_0005：nested stylized variant驗證為ukiyo-e；其record頂層style反而是photorealistic，不能誤用頂層。
- stylized_0084：nested style為chinese_ink_painting，保留指定歷史挑戰案例。

這是可逆的探索預覽，不是正式dataset設計或失敗率估計。四個來源hash不同；原caption完整保留在各自provenance/config.json，沒有另加藝術風格提示詞。

seed42；1952×960、40steps、bf16、true CFG7.5、guidance1.0、blend32、crop0；官方blend後1920×960。未量化、offload、reproduce旗標或其他World2階段。有效正／負prompt、原metadata與固定HF snapshot均記在config。為沿用已測路徑，每張獨立cold-process載入，沒有宣稱warm-model吞吐。

## 實測時間與缺陷

| sample | load秒 | inference秒 | load→保存解碼秒 | nvidia-smi sampled max MiB |
|---|---:|---:|---:|---:|
| photorealistic_0106 | 14.70 | 136.81 | 152.19 | 59055 |
| photorealistic_0501 | 14.62 | 136.59 | 151.98 | 65253 |
| stylized_0005 | 14.25 | 137.33 | 152.42 | 65285 |
| stylized_0084 | 14.58 | 137.31 | 152.29 | 59063 |

inference含條件編碼、採樣及VAE decode；不等同整個campaign的wall time。每張GPU約1秒取樣146/147筆；sampled max不是連續真峰值，可能漏掉暫態配置。torch peak包含load及inference，精確allocated/reserved bytes在result.json。controller 13:45:13→13:56:01 UTC（詳log），含process啟動、四次load和QA。

### photorealistic_0106
前景原圖的綠灰牆、米色沙發、矮桌與書架仍可辨識，寫實光色保持；但它們縮成遠端一組，另新增巨大的花瓶／咖啡桌、側面沙發與重複窗格，不是原房間的可靠幾何延伸。0/45度可見物件重複，杯盤、花材與家具邊緣有重繪／形變。180度及315→0未見明顯整條硬接縫；天花板／吊燈可辨，地板與毯子仍有局部形狀不自然。

### photorealistic_0501
原圖的湖面、山群、木屋與森林保留，寫實風格及整體照明連貫；木屋被縮小／重繪，新增樹島、環湖森林與對岸山脊，不能當作真實周圍景觀。135/180/225/270度的山脈和反射呈重複／過度對稱感，反射細節偏軟。180度與315→0未見巨大硬接縫；天空平滑且上極無明顯爆裂，下極主要為單調青綠水面，空間合理性仍待研究審查。

### stylized_0005
原圖兩名坐客、書架、吊燈與暖黃／紅色平塗插畫核心仍可辨，但擴展的窗戶／櫃台採更強透視和光影，原本紙感／平面筆觸變弱，風格並非全圈完全一致。新增／重複坐客與椅子，0/45/135/180/315度可見不自然的人體、桌椅接合、腿腳與細節形變。180與315→0未見明顯硬切；天花板與地板／影子大致連續，但桌椅和影子的空間關係不可靠。

### stylized_0084
原圖灶台、鍋與L形廚櫃尚可辨，黑灰淡墨與米白基調多數延續；右側新增冰箱、酒櫃、瓶罐和橘色燈光，細節較寫實／數位化。135→180→225度大量空白牆面，225→270度孤立黑色高櫃／冰箱樣體與門框缺乏清楚連接，房間佈局的可信度弱。180 wrap與315→0沒有顯著色塊硬縫，但無縫不等於連貫；天／地極幾乎純米白、地板線條消失，資訊不足，不以通過解碼推論品質合格。

## 可核對位置與重現邊界

本機：`/home/pierce/Documents/research/E3DQA/hypano-qwen-results/four-representative-20261114T134425Z`；realpath已核對，不在同步Vault。
遠端：`/root/HY-World-2.0/deployment/t_74bcb4c8`。
啟用：`source /root/HY-World-2.0/.venv-qwen-pano/bin/activate`。
實際啟動：`tmux new-window -d -t hermes -n hypano-four-t74 "bash /root/HY-World-2.0/deployment/t_74bcb4c8/run.sh"`。
run.sh在專用tmux window依序執行四個固定script；完成後window正常關閉，沒有動原ssh_tmux。不要重跑同一目錄；script拒絕既有sample，以防覆寫。
所有遠端命令唯一入口：`/home/pierce/vast-ssh-workflow/vast-ssh --config /home/pierce/.config/vast-ssh/config.json --non-interactive --id 60649163 -- COMMAND`。
日誌：遠端root下controller.log及各sample_id.log；controller.exit與四個sample.exit均0。本機同名檔在root/provenance/。
上游source：df9988efb87bfc0f4947eb3889411cf957478b06；未修改上游原碼。Python3.11、torch2.7.1+cu128、diffusers0.36.0、transformers4.57.1，沿用前次驗證venv與模型。
Qwen snapshot：d3968ef930e841f4c73640fb8afa3b306a78167e；LoRA snapshot：d78a16c91c7a56488894a1c8de4f5c7cc28aa8b0／HY-Pano-2.0。
checker v0.2.0 hash：5ccd3ec25de2f1f0c58344b1e780fe0770cfcf47ecfbe80d1192724d7597ad6f；同遠端interpreter重跑13 tests通過。

provenance/remote_transfer_manifest.json列凍結遠端119檔、30,373,285 bytes；transfer_receipt.json逐一對照遠端→本機路徑、bytes、SHA256，全部核對成功。移到provenance的config/log內容不變；QA manifest內absolute path刻意保留遠端原始provenance，閱覽時使用本機對應資料夾。
本地completion waiter曾遭工具420秒上限中斷，之後只讀原工作狀態，未重開推論；原四張正常完成。

## 全景原檔SHA256

- photorealistic_0106/panorama.png：e942c4711d4d24ac43269f4043076db992bb366a21c936443c7d06a3c03deac8
- photorealistic_0501/panorama.png：e85acd677877a39632ec88a3f60f2d7b340a1ac1dc2c26145fe937cd7ba19f44
- stylized_0005/panorama.png：1196cb42cef4c7fbe8e6725c7037551735351ee648e0d470aeb1381cfb5a9492
- stylized_0084/panorama.png：0224804de3881554eb633a942c41e1f43fdfdc84c446f7e4fff74d2a36a29a0c

這些為已執行的一次性campaign腳本，固定遠端路徑，並非泛用／可自動resume的batch controller；finalize.py只能從pending轉換一次，拒絕覆寫review。資料／原圖／輸出／權重未提交Git。
