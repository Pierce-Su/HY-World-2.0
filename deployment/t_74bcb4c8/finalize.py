from pathlib import Path
import json,hashlib,csv,shutil,zipfile
from datetime import datetime,timezone
from PIL import Image,ImageDraw
R=Path('/root/HY-World-2.0/deployment/t_74bcb4c8')
reviews={'photorealistic_0106': '前景原圖的綠灰牆、米色沙發、矮桌與書架仍可辨識，寫實光色保持；但它們縮成遠端一組，另新增巨大的花瓶／咖啡桌、側面沙發與重複窗格，不是原房間的可靠幾何延伸。0/45度可見物件重複，杯盤、花材與家具邊緣有重繪／形變。180度及315→0未見明顯整條硬接縫；天花板／吊燈可辨，地板與毯子仍有局部形狀不自然。', 'photorealistic_0501': '原圖的湖面、山群、木屋與森林保留，寫實風格及整體照明連貫；木屋被縮小／重繪，新增樹島、環湖森林與對岸山脊，不能當作真實周圍景觀。135/180/225/270度的山脈和反射呈重複／過度對稱感，反射細節偏軟。180度與315→0未見巨大硬接縫；天空平滑且上極無明顯爆裂，下極主要為單調青綠水面，空間合理性仍待研究審查。', 'stylized_0005': '原圖兩名坐客、書架、吊燈與暖黃／紅色平塗插畫核心仍可辨，但擴展的窗戶／櫃台採更強透視和光影，原本紙感／平面筆觸變弱，風格並非全圈完全一致。新增／重複坐客與椅子，0/45/135/180/315度可見不自然的人體、桌椅接合、腿腳與細節形變。180與315→0未見明顯硬切；天花板與地板／影子大致連續，但桌椅和影子的空間關係不可靠。', 'stylized_0084': '原圖灶台、鍋與L形廚櫃尚可辨，黑灰淡墨與米白基調多數延續；右側新增冰箱、酒櫃、瓶罐和橘色燈光，細節較寫實／數位化。135→180→225度大量空白牆面，225→270度孤立黑色高櫃／冰箱樣體與門框缺乏清楚連接，房間佈局的可信度弱。180 wrap與315→0沒有顯著色塊硬縫，但無縫不等於連貫；天／地極幾乎純米白、地板線條消失，資訊不足，不以通過解碼推論品質合格。'}
selection=json.loads((R/'selection.json').read_text()); assert len(selection)==4
assert (R/'controller.exit').read_text().strip()=='0'
records=[]
for s in selection:
 sid=s['id']; d=R/sid; q=d/'panorama_spherical_check'; m=json.loads((q/'manifest.json').read_text()); cfg=json.loads((d/'config.json').read_text()); result=json.loads((d/'result.json').read_text())
 assert (R/f'{sid}.exit').read_text().strip()=='0' and result['status']=='success'
 assert cfg['settings']==dict(prompt=s['record'][s['variant']]['prompt'],negative_prompt='',seed=42,height=960,width=1952,num_inference_steps=40,guidance_scale=1.0,true_cfg_scale=7.5,blend_width=32,crop_border=0.0)
 assert cfg['dtype']=='bfloat16' and cfg['offload']==False and cfg['quantization']==False
 assert hashlib.sha256((d/'source.jpg').read_bytes()).hexdigest()==s['input_sha256']==cfg['input_sha256']==m['source']['sha256']
 assert hashlib.sha256(Path(s['input']).read_bytes()).hexdigest()==s['input_sha256']
 assert hashlib.sha256((d/'panorama.png').read_bytes()).hexdigest()==result['sha256']==m['input']['sha256']
 with Image.open(d/'panorama.png') as im: im.load(); assert im.mode=='RGB' and im.size==(1920,960)
 assert [v['yaw'] for v in m['views'][:8]]==list(range(0,360,45))
 assert [v['pitch'] for v in m['views'][-2:]]==[90,-90]
 assert m['config']['fov_horizontal_degrees']==m['config']['fov_vertical_degrees']==90 and m['config']['layout']=='eight'
 assert len(m['outputs'])==14 and len(list(q.glob('*.png')))==10
 for o in m['outputs']:
  p=q/o['path']; assert p.stat().st_size==o['bytes']; assert hashlib.sha256(p.read_bytes()).hexdigest()==o['sha256']
  with Image.open(p) as im: im.load(); assert list(im.size)==o['size']
 rows=list(csv.DictReader((d/'gpu_samples.csv').open())); assert len(rows)==result['nvidia_smi_sample_count']; assert max(float(x['memory_used_MiB']) for x in rows)==result['nvidia_smi_sampled_max_MiB']
 assert m['review_status']=='pending_manual_review'
 shutil.copy2(q/'manifest.json',q/'manifest.pending.json');shutil.copy2(q/'review.md',q/'review.pending.md')
 text=f"# {sid}：agent 2D 視覺檢查\n\n審查者：Developer agent；不是使用者品質批准。\n\n{reviews[sid]}\n\n結論：review（保留缺陷、研究品質待審）；執行／RGB解碼通過。已查看原圖對照ERP和八個yaw＋兩極montage。未像素配準；未知原圖FoV；同中心重投影不證明3D幾何、真實場景或下游可用性。\n"
 (q/'review.md').write_text(text); m.update(review_status='reviewed_2d',reviewer='Developer agent',visual_verdict='review',review_sha256=hashlib.sha256(text.encode()).hexdigest(),reviewed_utc=datetime.now(timezone.utc).isoformat());(q/'manifest.json').write_text(json.dumps(m,indent=2,ensure_ascii=False))
 shutil.copy2(q/'source_vs_erp.jpg',d/'comparison.jpg');shutil.copy2(q/'spherical_views.jpg',d/'spherical_preview.jpg')
 records.append(dict(id=sid,style=s['style'],result=result,review=reviews[sid],visual_verdict='review'))
canvas=Image.new('RGB',(1200,1080),'#202020');draw=ImageDraw.Draw(canvas)
for n,s in enumerate(selection):
 x=(n%2)*600;y=(n//2)*540;draw.text((x+10,y+8),f"{n+1}. {s['id']} | {s['style']}",fill='white')
 with Image.open(R/s['id']/'comparison.jpg') as im: im.thumbnail((600,500));canvas.paste(im,(x,y+35))
canvas.save(R/'contact_sheet.jpg',quality=94)
(R/'results.json').write_text(json.dumps(dict(task='t_74bcb4c8',target='60649163',new_generated=4,reused=0,source_revision=records and cfg['source_revision'],cold_process_per_sample=True,records=records),indent=2,ensure_ascii=False))
# Freeze transfer inventory after all writes; archive excludes itself and inventory.
files=sorted(p for p in R.rglob('*') if p.is_file() and p.name not in ('transfer_manifest.json','evidence.zip'))
manifest=[dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]
(R/'transfer_manifest.json').write_text(json.dumps(manifest,indent=2))
with zipfile.ZipFile(R/'evidence.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
 for p in files: z.write(p,p.relative_to(R))
 z.write(R/'transfer_manifest.json','transfer_manifest.json')
print(json.dumps(dict(files=len(files),bytes=sum(x['bytes'] for x in manifest),archive_bytes=(R/'evidence.zip').stat().st_size,archive_sha256=hashlib.sha256((R/'evidence.zip').read_bytes()).hexdigest(),records=records),indent=2,ensure_ascii=False))
