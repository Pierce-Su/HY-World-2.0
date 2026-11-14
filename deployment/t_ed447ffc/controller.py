"""Exact60649163 fixed baseline controller. No quality retries, no asset deletion.
prepare freezes actual nested variants; run resumes only verified successes.
An interrupted incomplete GPU attempt is a hard pause requiring inspection.
"""
import collections,fcntl,hashlib,json,os,shutil,subprocess,sys,time,traceback
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('/root/HY-World-2.0')
RUN=ROOT/'deployment/t_ed447ffc'
PY=ROOT/'.venv-qwen-pano/bin/python'
QA=ROOT/'deployment/t_1e9a7907/qa/spherical_check.py'
REV='df9988efb87bfc0f4947eb3889411cf957478b06'
EVENT='curated140-t_ed447ffc'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())
def write(p,obj):
    p=Path(p);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2));tmp.replace(p)
def now(): return datetime.now(timezone.utc).isoformat()
def settings(prompt): return dict(prompt=prompt,negative_prompt='',seed=42,height=960,width=1952,num_inference_steps=40,guidance_scale=1.0,true_cfg_scale=7.5,blend_width=32,crop_border=0.0)
def constants():
    # Parse only literal assignments; preflight never loads torch/model.
    import ast
    tree=ast.parse((ROOT/'hyworld2/panogen/pipeline_with_qwen_image.py').read_text());out={}
    for node in tree.body:
        if isinstance(node,ast.Assign):
            for target in node.targets:
                if isinstance(target,ast.Name) and target.id.startswith('GENERAL_'):out[target.id]=ast.literal_eval(node.value)
    return out

def verify_png(p,expected=None):
    from PIL import Image
    with Image.open(p) as im: im.load();assert im.mode=='RGB' and im.size==(1920,960),(p,im.mode,im.size)
    h=sha(p)
    if expected: assert h==expected,(p,'changed output hash')
    return h

def matching(old,item,models,c):
    cfg=read(old/'config.json');result=read(old/'result.json')
    checks={'source_revision':cfg['source_revision']==REV,'source_hash':cfg['input_sha256']==item['sha256'],
      'source_path':cfg['input']==item['source'],'prompt_settings':cfg['settings']==settings(item['variant_metadata']['prompt']),
      'effective_positive':cfg['positive_prompt']==(c['GENERAL_POSITIVE_PREFIX']+item['variant_metadata']['prompt']+c['GENERAL_POSITIVE_SUFFIX']).strip(),
      'effective_negative':cfg['negative_prompt']==c['GENERAL_NEGATIVE_PROMPT'].strip(),
      'models':cfg['models']==models,'result_success':result['status']=='success'}
    # Legacy first pilot has no dtype/offload fields: verify its executed source is identical
    # to archived worker's proven load/call path, whose defaults are bf16/no offload.
    if 'dtype' in cfg: checks['dtype']=cfg['dtype']=='bfloat16'
    if 'offload' in cfg: checks['offload']=cfg['offload'] is False
    if 'quantization' in cfg: checks['quantization']=cfg['quantization'] is False
    checks['decoded_output']=verify_png(old/'panorama.png',result['sha256'])==result['sha256']
    assert all(checks.values()),checks
    return checks

def prepare():
    assert not (RUN/'inventory.json').exists(),'inventory is immutable'
    assert subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()==REV
    models=read(ROOT/'deployment/t_74bcb4c8/models.json');c=constants()
    metadata=read(ROOT/'curated_set/metadata.json');records=metadata['samples']
    assert len({r['index'] for r in records})==len(records)
    byid={r['index']:r for r in records};items=[]
    from PIL import Image
    for cohort in ['photorealistic','stylized']:
        files=sorted((ROOT/'curated_set'/cohort).glob('*.jpg'))
        expected={r[cohort]['filename'] for r in records if cohort in r}
        assert {p.name for p in files}==expected,(cohort,'metadata/file disagreement')
        assert len(files)==70,(cohort,len(files))
        for src in files:
            rec=byid[int(src.stem)];variant=rec[cohort]
            assert variant['filename']==src.name and variant['prompt'].strip()
            assert (variant['style']=='photorealistic')==(cohort=='photorealistic')
            with Image.open(src) as im:im.load();size=list(im.size);mode=im.mode
            items.append(dict(id=cohort+'_'+src.stem,cohort=cohort,source=str(src),sha256=sha(src),size=size,mode=mode,record=rec,variant_metadata=variant))
    assert len(items)==140 and len({i['id'] for i in items})==140
    reuse={
      'photorealistic_0000':ROOT/'deployment/t_1e9a7907/pilot_0000',
      **{i:ROOT/'deployment/t_74bcb4c8'/i for i in ['photorealistic_0106','photorealistic_0501','stylized_0005','stylized_0084']}}
    for i in items:
        if i['id'] in reuse:
            try:
                checks=matching(reuse[i['id']],i,models,c)
                i['reuse']={'origin':str(reuse[i['id']]),'checks':checks,'output_sha256':sha(reuse[i['id']]/'panorama.png')}
            except Exception as e:i['reuse_rejected']=repr(e)
    RUN.mkdir(exist_ok=True)
    shutil.copy2(ROOT/'curated_set/metadata.json',RUN/'original_metadata.json')
    shutil.copy2(ROOT/'deployment/t_74bcb4c8/models.json',RUN/'models.json')
    shutil.copy2(ROOT/'deployment/t_1e9a7907/pilot.py',RUN/'proven_worker_template.py')
    shutil.copy2(ROOT/'hyworld2/panogen/pipeline_with_qwen_image.py',RUN/'pipeline_source.py')
    shutil.copy2(QA,RUN/'spherical_check_v0_2_0.py')
    write(RUN/'inventory.json',dict(created_utc=now(),source_revision=REV,metadata_sha256=sha(RUN/'original_metadata.json'),models_sha256=sha(RUN/'models.json'),worker_sha256=sha(RUN/'proven_worker_template.py'),pipeline_sha256=sha(RUN/'pipeline_source.py'),qa_sha256=sha(QA),items=items))
    counts={'expected':len(items),'reused_planned':sum('reuse' in i for i in items),'new_planned':sum('reuse' not in i for i in items),'cohorts':dict(collections.Counter(i['cohort'] for i in items)), 'unique_source_hashes':len({i['sha256'] for i in items})}
    write(RUN/'preflight.json',counts);print(json.dumps(counts),flush=True)

def state(item):return RUN/'records'/(item['id']+'.json')
def summarize(status='RUNNING',active=None,reason=None):
    items=read(RUN/'inventory.json')['items'];rows=[read(state(i)) for i in items if state(i).exists()]
    success=[r for r in rows if r['status']=='success'];failed=[r for r in rows if r['status']=='failed']
    obj=dict(updated_utc=now(),status=status,active=active,reason=reason,expected=len(items),success=len(success),failed=len(failed),pending=len(items)-len(success)-len(failed),reused=sum(r.get('kind')=='reused' for r in success),new=sum(r.get('kind')=='new' for r in success),visual_review_pending=len(success),cohorts={c:dict(success=sum(r['cohort']==c for r in success),failed=sum(r['cohort']==c for r in failed),expected=70) for c in ['photorealistic','stylized']})
    write(RUN/'progress.json',obj);print(json.dumps(obj),flush=True)
    return obj

def check_qa(out):
    from PIL import Image
    manifest=read(out/'manifest.json');pngs=sorted(out.glob('*.png'))
    assert len(pngs)==10
    names=['%02d_yaw_%03d.png'%(k,k*45) for k in range(8)]+['08_zenith.png','09_nadir.png']
    assert [p.name for p in pngs]==names
    for p in pngs:
        with Image.open(p) as im: im.load();assert im.size==(512,512)
    assert manifest['projection_status']=='rendered' and manifest['version']=='0.2.0'
    assert manifest['input']['sha256']==sha(out.parent/'panorama.png')
    assert manifest['source']['sha256']==sha(out.parent/'source.jpg')
    cfg=manifest['config'];assert cfg['layout']=='eight' and cfg['view_size']==512
    assert cfg['fov_horizontal_degrees']==cfg['fov_vertical_degrees']==90
    assert [v['yaw'] for v in manifest['views'][:8]]==list(range(0,360,45))
    for entry in manifest['outputs']:
        p=out/entry['path'];assert p.stat().st_size==entry['bytes'] and sha(p)==entry['sha256']
        with Image.open(p) as im:im.load();assert list(im.size)==entry['size']
    # Explicit adjacent 315->0 view, supplementing the checker montage (no review claim).
    preview=out.parent/'wrap_315_to_0.jpg'
    if not preview.exists():
        from PIL import ImageDraw
        tile=Image.new('RGB',(1024,548),'white');draw=ImageDraw.Draw(tile)
        for x,name,label in [(0,'07_yaw_315.png','yaw315 ->'),(512,'00_yaw_000.png','yaw0 (continuity check)')]:
            with Image.open(out/name) as im:tile.paste(im,(x,36))
            draw.text((x+12,12),label,fill='black')
        tile.save(preview,quality=92)
    return {'manifest_sha256':sha(out/'manifest.json'),'png_count':10,'image_hashes':{p.name:sha(p) for p in out.iterdir() if p.suffix in ['.png','.jpg']},'wrap_315_to_0_sha256':sha(preview),'review_status':'pending'}

def worker(item):
    template=(RUN/'proven_worker_template.py').read_text()
    start=template.index('source=');end=template.index('settings=')
    block="source=Path("+repr(item['source'])+")\nrecord="+repr(item['record'])+"\nprompt="+repr(item['variant_metadata']['prompt'])+"\nout=RUN/"+repr(item['id'])+";out.mkdir(exist_ok=False)\n"
    template=template[:start]+block+template[end:]
    template=template.replace("RUN=ROOT/'deployment/t_1e9a7907'","RUN=ROOT/'deployment/t_ed447ffc'")
    p=RUN/'workers'/(item['id']+'.py');p.parent.mkdir(exist_ok=True);p.write_text(template);return p

def process(item):
    sid=item['id'];out=RUN/sid
    assert sha(item['source'])==item['sha256'],'source changed'
    if state(item).exists():
        r=read(state(item))
        if r['status']=='success':
            verify_png(out/'panorama.png',r['output_sha256']);assert sha(out/'panorama_spherical_check/manifest.json')==r['qa']['manifest_sha256']
        return r
    # An existing successful panorama can finish QA without replaying GPU inference.
    if out.exists() and not (out/'result.json').exists():raise RuntimeError('Interrupted incomplete attempt: inspect original process before any retry '+sid)
    kind='reused' if 'reuse' in item else 'new'
    if not out.exists():
        if kind=='reused':
            old=Path(item['reuse']['origin']);matching(old,item,read(RUN/'models.json'),constants())
            out.mkdir();origin=out/'original_execution';origin.mkdir()
            for name in ['config.json','result.json','gpu_samples.csv']:shutil.copy2(old/name,origin/name)
            shutil.copy2(old/'panorama.png',out/'panorama.png')
            # Result/config retain original paths/times: explicitly imports, not fresh execution.
            for name in ['config.json','result.json']:shutil.copy2(old/name,out/name)
            write(out/'import_receipt.json',dict(kind='reused',imported_utc=now(),**item['reuse']))
        else:
            marker=RUN/(sid+'.attempt.json')
            if marker.exists():raise RuntimeError('Unfinished attempt requires inspection '+sid)
            write(marker,dict(started_utc=now(),kind='new',input_sha256=item['sha256']))
            p=worker(item)
            with (RUN/(sid+'.log')).open('w') as log:
                try:rc=subprocess.run([str(PY),'-u',str(p)],stdout=log,stderr=subprocess.STDOUT,timeout=1200).returncode
                except subprocess.TimeoutExpired:rc=124
            (RUN/(sid+'.exit')).write_text(str(rc)+'\n')
            if rc!=0:
                text=(RUN/(sid+'.log')).read_text()[-12000:]
                r=dict(id=sid,cohort=item['cohort'],status='failed',kind=kind,exit=rc,error=text[-3000:],environment_error=any(k in text for k in ['CUDA','ModuleNotFoundError','ImportError','out of memory','No space left']),finished_utc=now())
                write(state(item),r);return r
    result=read(out/'result.json');assert result['status']=='success'
    h=verify_png(out/'panorama.png',result['sha256'])
    if not (out/'source.jpg').exists():shutil.copy2(item['source'],out/'source.jpg')
    qadir=out/'panorama_spherical_check'
    if not qadir.exists():
        with (RUN/(sid+'.qa.log')).open('w') as log:
            rc=subprocess.run([str(PY),str(QA),'--image',str(out/'panorama.png'),'--source',str(out/'source.jpg'),'--layout','eight','--size','512','--fov','90'],stdout=log,stderr=subprocess.STDOUT,timeout=180).returncode
        (RUN/(sid+'.qa.exit')).write_text(str(rc)+'\n');assert rc==0,'QA failed '+sid
    qa=check_qa(qadir)
    r=dict(id=sid,cohort=item['cohort'],status='success',kind=kind,finished_utc=now(),output_sha256=h,input_sha256=item['sha256'],qa=qa,visual_review_status='pending',original_execution=item.get('reuse',{}).get('origin'),result=result)
    write(state(item),r);return r

def run():
    lock=(ROOT/'deployment/.qwen-gpu.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    (RUN/'controller.pid').write_text(str(os.getpid()))
    inv=read(RUN/'inventory.json');assert sha(QA)==inv['qa_sha256'];assert sha(ROOT/'hyworld2/panogen/pipeline_with_qwen_image.py')==inv['pipeline_sha256']
    os.environ.update(HF_HUB_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
    (RUN/'records').mkdir(exist_ok=True)
    with (RUN/'qa_tests.log').open('w') as log:subprocess.run([str(PY),'-m','unittest','discover','-s',str(QA.parent),'-p','test_spherical_check.py','-v'],stdout=log,stderr=subprocess.STDOUT,check=True)
    errors=0
    for item in inv['items']:
        if shutil.disk_usage(ROOT).free<10*1024**3:raise RuntimeError('Disk reserve below10GiB')
        summarize(active=item['id']);r=process(item)
        errors=errors+1 if r.get('environment_error') else 0
        summarize()
        if errors>=2:raise RuntimeError('Two consecutive environment/CUDA failures; paused without retry')
    p=summarize('DONE' if not any(read(state(i))['status']=='failed' for i in inv['items']) else 'DONE_WITH_FAILURES')
    (RUN/'controller.exit').write_text('0\n');write(RUN/'DONE.json',p)

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    else:
        try:run()
        except BaseException as e:
            traceback.print_exc();summarize('PAUSED',reason=repr(e));(RUN/'controller.exit').write_text('1\n');raise
        finally:subprocess.run(['tmux','wait-for','-S',EVENT])
