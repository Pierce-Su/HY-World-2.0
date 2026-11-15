"""Read-only independent audit of completed curated140 backup; no remote inference."""
from pathlib import Path
import json, hashlib, collections, datetime
from PIL import Image
W=Path(__file__).resolve().parent
D=Path(json.loads((W/'local_destination.json').read_text())['path'])
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
inv=read(D/'inventory.json')['items']; assert len(inv)==140 and len({i['id'] for i in inv})==140
assert collections.Counter(i['cohort'] for i in inv)=={'photorealistic':70,'stylized':70}
receipt=read(D/'transfer_receipt.json'); entries=receipt['files']; assert len({e['path'] for e in entries})==len(entries)
for e in entries:
 p=D/e['path']; assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],e['path']
assert (D/'provenance/final/controller.exit').read_text().strip()=='0'
progress=read(D/'provenance/final/progress.json'); assert progress['status']=='DONE' and progress['success']==140 and progress['failed']==progress['pending']==0
expected_views=[(f'{n:02d}_yaw_{yaw:03d}',yaw,0) for n,yaw in enumerate(range(0,360,45))]+[('08_zenith',0,90),('09_nadir',0,-90)]
counts=collections.Counter(); samples=[]; elapsed=[]; actual_paths=set()
for i in inv:
 sid=i['id']; f=D/sid; r=read(D/'records'/(sid+'.json')); c=read(f/'config.json'); q=read(f/'panorama_spherical_check/manifest.json')
 assert r['status']=='success' and r['id']==sid
 assert sha(f/'source.jpg')==i['sha256']==r['input_sha256']==c['input_sha256']
 assert sha(f/'panorama.png')==r['output_sha256']==q['input']['sha256']
 assert q['source']['sha256']==i['sha256'] and q['version']=='0.2.0' and q['projection_status']=='rendered'
 assert [(v['name'],v['yaw'],v['pitch']) for v in q['views']]==expected_views
 assert q['config']['view_size']==512 and q['config']['layout']=='eight' and q['config']['fov_horizontal_degrees']==q['config']['fov_vertical_degrees']==90
 assert q['review_status']=='pending_manual_review' and r['visual_review_status']=='pending'
 assert len(list((f/'panorama_spherical_check').glob('*.png')))==10
 for name,_,_ in expected_views:
  p=f/'panorama_spherical_check'/(name+'.png')
  with Image.open(p) as im: im.load(); assert im.mode=='RGB' and im.size==(512,512)
 with Image.open(f/'panorama.png') as im: im.load(); assert im.mode=='RGB' and im.size==(1920,960)
 s=c['settings']; assert {k:s[k] for k in ['seed','height','width','num_inference_steps','guidance_scale','true_cfg_scale','blend_width','crop_border']}==dict(seed=42,height=960,width=1952,num_inference_steps=40,guidance_scale=1.0,true_cfg_scale=7.5,blend_width=32,crop_border=0.0)
 assert s['prompt']==i['variant_metadata']['prompt']
 assert c['positive_prompt']=='Create a **ERP** panoramic expansion of the provided image. Preserve the original style, lighting, and fine details seamlessly throughout the extended areas, extend according to: '+s['prompt']+' 8k UHD, masterpiece, razor-sharp details.'
 assert c['source_revision']=='df9988efb87bfc0f4947eb3889411cf957478b06'
 assert c['models']['Qwen/Qwen-Image-Edit-2509']['revision']=='d3968ef930e841f4c73640fb8afa3b306a78167e'
 assert c['models']['tencent/HY-World-2.0']['revision']=='d78a16c91c7a56488894a1c8de4f5c7cc28aa8b0'
 counts[r['kind']]+=1; counts[i['cohort']]+=1
 if r['kind']=='new':
  assert (D/(sid+'.exit')).read_text().strip()=='0'
  assert (f/'gpu_samples.csv').stat().st_size>0
  elapsed.append(r['result']['end_to_end_seconds'])
 else:
  assert r['original_execution'] and (f/'original_execution/execution.exit').read_text().strip()=='0'
 assert (D/(sid+'.qa.exit')).read_text().strip()=='0'
 actual_paths.update(str(p.relative_to(D)) for p in f.rglob('*') if p.is_file() and p.name not in ['comparison.jpg','spherical_preview.jpg'])
 samples.append({'id':sid,'kind':r['kind'],'status':'success','pngs':10})
assert counts['new']==135 and counts['reused']==5
covered={e['path'] for e in entries}; assert actual_paths<=covered,actual_paths-covered
report={'audit_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'destination':str(D.resolve()),'expected':140,'success':140,'failed':0,'pending':0,'counts':dict(counts),'verified_files':len(entries),'verified_bytes':sum(e['bytes'] for e in entries),'decoded_original_panoramas':140,'decoded_512square_spherical_pngs':1400,'individual_visual_reviewed':0,'visual_review_pending':140,'new_end_to_end_seconds_sum':sum(elapsed),'new_end_to_end_seconds_min':min(elapsed),'new_end_to_end_seconds_max':max(elapsed),'samples':samples}
p=D/'final_audit.json'; assert not p.exists();p.write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2))
