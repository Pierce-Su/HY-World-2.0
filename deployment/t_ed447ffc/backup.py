"""Local bounded backup/index builder. Uses only canonical exact60649163 SSH.
No inference, retry, source deletion, lifecycle changes, or quality acceptance.
"""
from pathlib import Path
import subprocess,sys,hashlib,json,tarfile,shlex,shutil,html,collections,datetime
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parent
BASE=Path('/home/pierce/Documents/research/E3DQA/hypano-qwen-results')
REMOTE='/root/HY-World-2.0/deployment/t_ed447ffc'
CMD=['/home/pierce/vast-ssh-workflow/vast-ssh','--config','/home/pierce/.config/vast-ssh/config.json','--non-interactive','--id','60649163','--']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,x):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False))
def remote(args,timeout=180):
    r=subprocess.run(CMD+args,capture_output=True,timeout=timeout)
    if r.returncode:raise RuntimeError('Remote command failed rc='+str(r.returncode)+' '+r.stderr.decode(errors='replace')[-1000:])
    return r.stdout

def destination():
    p=W/'local_destination.json'
    if p.exists():dest=Path(read(p)['path'])
    else:
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');dest=BASE/('full-curated140-'+stamp)
        assert not dest.exists();dest.mkdir(parents=True);write(p,{'path':str(dest)})
    resolved=dest.resolve();vault=Path('/home/pierce/Hermes-Vault').resolve()
    assert resolved.is_relative_to(BASE.resolve()) and not resolved.is_relative_to(vault)
    assert shutil.disk_usage(dest).free>5*1024**3
    print('DURABLE_DESTINATION',resolved,flush=True);return dest

def fetch_batch(dest,cohort,batch):
    stem=cohort+'_'+str(batch);receipts=dest/'provenance/receipts';receipts.mkdir(parents=True,exist_ok=True)
    receipt=receipts/(stem+'.json')
    if receipt.exists():
        r=read(receipt)
        for e in r['files']:
            p=dest/e['path'];assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256']
        print('ALREADY_VERIFIED',stem,len(r['files']),flush=True);return
    info=json.loads(remote(['/root/HY-World-2.0/.venv-qwen-pano/bin/python',REMOTE+'/snapshot.py',cohort,str(batch)]))
    staging=dest/'provenance/staging'/stem;staging.mkdir(parents=True,exist_ok=True);archive=staging/'batch.tar'
    if not archive.exists() or archive.stat().st_size!=info['bytes'] or sha(archive)!=info['sha256']:
        partial=staging/'batch.partial.tar'
        with partial.open('wb') as f:
            p=subprocess.run(CMD+['/usr/bin/cat',info['archive']],stdout=f,stderr=subprocess.PIPE,timeout=180)
        assert p.returncode==0,('transfer failed',p.returncode,p.stderr.decode(errors='replace')[-1000:])
        assert partial.stat().st_size==info['bytes'] and sha(partial)==info['sha256'],'Archive hash mismatch'
        partial.replace(archive)
    with tarfile.open(archive) as t:
        for member in t.getmembers():assert member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
        t.extractall(staging/'files',filter='data')
    manifest=read(staging/'files/transfer'/(stem+'.json'))
    for e in manifest:
        src=staging/'files'/e['path'];assert src.stat().st_size==e['bytes'] and sha(src)==e['sha256']
        dst=dest/e['path'];dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists():assert dst.stat().st_size==e['bytes'] and sha(dst)==e['sha256'],'Collision '+str(dst)
        else:shutil.copy2(src,dst)
    for e in manifest:assert sha(dest/e['path'])==e['sha256']
    write(receipt,{'remote':info,'files':manifest,'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    print('TRANSFER_VERIFIED',stem,len(manifest),info['source_bytes'],flush=True)

def render_index(dest):
    inv=read(dest/'inventory.json');items=inv['items'];rows=[]
    previews=dest/'contact_sheets';previews.mkdir(exist_ok=True)
    for i in items:
        p=dest/'records'/(i['id']+'.json');r=read(p) if p.exists() else {'status':'pending'}
        row=dict(i,status=r['status'],kind=r.get('kind'),result=r.get('result'),visual_review_status='pending')
        if r['status']=='success':
            folder=dest/i['id'];assert sha(folder/'panorama.png')==r['output_sha256']
            with Image.open(folder/'panorama.png') as im:im.load();assert im.mode=='RGB' and im.size==(1920,960)
            q=folder/'panorama_spherical_check';m=read(q/'manifest.json')
            assert sha(q/'manifest.json')==r['qa']['manifest_sha256']
            assert m['config']['layout']=='eight' and m['config']['fov_horizontal_degrees']==m['config']['fov_vertical_degrees']==90
            for e in m['outputs']:
                p=q/e['path'];assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256']
                with Image.open(p) as im:im.load()
            assert sha(folder/'source.jpg')==i['sha256']
            assert sha(folder/'wrap_315_to_0.jpg')==r['qa']['wrap_315_to_0_sha256']
            for src,name in [(q/'source_vs_erp.jpg','comparison.jpg'),(q/'spherical_views.jpg','spherical_preview.jpg')]:
                if not (folder/name).exists():shutil.copy2(src,folder/name)
        rows.append(row)
    counts={'expected':140,'success':sum(r['status']=='success' for r in rows),'failed':sum(r['status']=='failed' for r in rows),'pending':sum(r['status']=='pending' for r in rows),'new':sum(r['status']=='success' and r['kind']=='new' for r in rows),'reused':sum(r['status']=='success' and r['kind']=='reused' for r in rows),'spherical_rendered':sum(r['status']=='success' for r in rows),'current_campaign_individual_visual_reviews':0,'visual_review_pending':sum(r['status']=='success' for r in rows)}
    def tile(row,w=600,h=270):
        canvas=Image.new('RGB',(w,h),'#20252c');d=ImageDraw.Draw(canvas)
        label=row['id']+' | '+row['variant_metadata']['style']+' | '+row['status']+' '+str(row['kind'] or '')
        d.text((10,8),label,fill='white');d.text((10,27),'source -> panorama (execution != quality acceptance)',fill='#b7c0cb')
        if row['status']=='success':
            for x,y,bw,bh,p in [(10,60,170,190,dest/row['id']/'source.jpg'),(190,60,400,200,dest/row['id']/'panorama.png')]:
                with Image.open(p) as im:
                    im=im.convert('RGB');im.thumbnail((bw,bh));canvas.paste(im,(x+(bw-im.width)//2,y+(bh-im.height)//2))
        return canvas
    links=[]
    for cohort in ['photorealistic','stylized']:
        group=[r for r in rows if r['cohort']==cohort]
        # 70 labelled tiles; page sheets remain readable without opening a giant image.
        full=Image.new('RGB',(3000,3780),'#101419')
        for j,r in enumerate(group):full.paste(tile(r),(j%5*600,j//5*270))
        full.save(dest/('contact_sheet_'+cohort+'.jpg'),quality=88)
        for b in range(7):
            sheet=Image.new('RGB',(1200,1350),'#101419')
            for j,r in enumerate(group[b*10:(b+1)*10]):sheet.paste(tile(r),(j%2*600,j//2*270))
            name=cohort+'_'+str(b+1).zfill(2)+'.jpg';sheet.save(previews/name,quality=92);links.append('<a href="contact_sheets/'+name+'">'+name+'</a>')
    cards=[]
    for row in rows:
        sid=row['id'];esc=html.escape
        if row['status']=='success':
            cards.append('<section id="'+sid+'"><h3>'+esc(sid+' | '+row['variant_metadata']['style']+' | '+row['kind'])+'</h3><a href="'+sid+'/panorama.png"><img loading="lazy" width="720" src="'+sid+'/panorama.png"></a><p>'+ ' | '.join('<a href="'+sid+'/'+p+'">'+label+'</a>' for p,label in [('source.jpg','原透視輸入'),('panorama.png','原始全景PNG'),('comparison.jpg','來源比較'),('spherical_preview.jpg','八方位＋兩極'),('wrap_315_to_0.jpg','315→0'),('panorama_spherical_check/manifest.json','球面manifest'),('config.json','執行設定'),('result.json','執行result')])+'</p><p>本campaign逐張目視：pending；不是品質或3D驗收。</p></section>')
        else:cards.append('<p>'+esc(sid+' '+row['status'])+'</p>')
    title='HY-Pano Qwen curated140 固定設定 baseline'
    (dest/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>'+title+'</title><style>body{font:16px system-ui;background:#101419;color:#e2e8f0;margin:28px}a{color:#80c8ff}section{border-top:1px solid #354052;margin:24px 0}img{max-width:100%;height:auto}</style><h1>'+title+'</h1><pre>'+html.escape(json.dumps(counts,ensure_ascii=False,indent=2))+'</pre><p>'+ ' | '.join(links)+'</p>'+''.join(cards))
    (dest/'README.md').write_text('# HY-Pano Qwen curated140 固定設定 baseline\n\n完整／持續備份位置：'+str(dest)+'\n\n先開 index.html，再看 contact_sheet_photorealistic.jpg／contact_sheet_stylized.jpg；contact_sheets/ 有每頁10條件。每條件資料夾有 source.jpg（原透視輸入）、panorama.png（byte-identical原生成PNG）、comparison.jpg、spherical_preview.jpg、wrap_315_to_0.jpg；panorama_spherical_check/ 保存八方位＋兩極PNG與hash manifest。config/result/log與 original_execution/ 保存原始執行出處。\n\n計數：'+json.dumps(counts,ensure_ascii=False)+'\n\n140 unique variant IDs；70寫實先跑、70風格化後跑；139 unique input-content hashes，重複bytes的不同條件保留。使用 nested variant 原prompt，不依top-level style猜測。重用5條件只有全部provenance匹配才匯入，其舊時間／log／路徑原樣保存；其餘預計135新生成；實際成功／失敗以counts為準，沒有為改善品質重跑、換seed或挑圖。\n\n固定：source df9988efb87bfc0f4947eb3889411cf957478b06；Qwen base d3968ef930e841f4c73640fb8afa3b306a78167e；LoRA d78a16c91c7a56488894a1c8de4f5c7cc28aa8b0；seed42每圖重置、1952×960、40 steps、bf16、trueCFG7.5、guidance1、blend32、crop0、無quant/offload；原PNG解碼RGB1920×960。每圖獨立cold process，時間／GPU取樣在result.json及gpu_samples.csv（取樣最大值非連續真實峰值）。\n\n球面工具v0.2.0：yaw0,45,90,135,180,225,270,315＋zenith/nadir；512平方，水平／垂直FoV皆90°；同光心重投影並非3D或WorldExplorer相機scaffold。所有自動投影／hash／decode均不等於agent或人工目視，個別新QA review.md維持pending，舊5張review僅在original_execution/作歷史證據。缺陷不自動刪除／篩掉；這是執行結果，不是品質接受。\n\n遠端：'+REMOTE+'；tmux hermes:hypano140-ted44；provenance/receipts/逐批原始檔SHA256及bytes驗證；transfer_receipt.json為去重總表。原始絕對路徑指向Vast，不代表本機也有該路徑。資料／權重不寫synced Vault，僅留下簡短指標。\n')
    write(dest/'counts.json',counts);write(dest/'sample_index.json',rows)
    unique={}
    for p in (dest/'provenance/receipts').glob('*.json'):
        for e in read(p)['files']:
            if e['path'] in unique:assert unique[e['path']]==e
            unique[e['path']]=e
    for e in unique.values():assert (dest/e['path']).stat().st_size==e['bytes'] and sha(dest/e['path'])==e['sha256']
    receipt={'verified_files':len(unique),'verified_bytes':sum(e['bytes'] for e in unique.values()),'files':sorted(unique.values(),key=lambda e:e['path']),'counts':counts,'destination_realpath':str(dest.resolve())}
    write(dest/'transfer_receipt.json',receipt);print('INDEX_AND_RECEIPT_VERIFIED',json.dumps(counts),len(unique),receipt['verified_bytes'],flush=True)

if __name__=='__main__':
    dest=destination()
    if len(sys.argv)==1:sys.exit(0)
    cohort=sys.argv[1]
    if cohort=='final':
        for c in ['photorealistic','stylized']:
            for b in range(7):fetch_batch(dest,c,b)
        for name in ['controller.log','controller.exit','progress.json','DONE.json','qa_tests.log']:
            # Small terminal state, fetched only after completion.
            data=remote(['/usr/bin/cat',REMOTE+'/'+name]);p=dest/'provenance/final'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        progress=read(dest/'provenance/final/progress.json');assert progress['pending']==0 and progress['status'] in ['DONE','DONE_WITH_FAILURES']
        render_index(dest)
    else:
        assert cohort in ['photorealistic','stylized']
        for b in range(7):fetch_batch(dest,cohort,b)
        render_index(dest)
