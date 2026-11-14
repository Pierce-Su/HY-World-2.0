"""Freeze bounded immutable completed-sample batches for exact local backup."""
from pathlib import Path
import json,hashlib,tarfile,sys,shutil
RUN=Path('/root/HY-World-2.0/deployment/t_ed447ffc')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cohort,batch=sys.argv[1],int(sys.argv[2]);assert cohort in ['photorealistic','stylized']
items=[i for i in json.loads((RUN/'inventory.json').read_text())['items'] if i['cohort']==cohort][batch*10:(batch+1)*10]
assert items and len(items)==10
records={i['id']:json.loads((RUN/'records'/(i['id']+'.json')).read_text()) for i in items}
assert all(r['status'] in ['success','failed'] for r in records.values())
# Preserve legacy actual execution receipts, not manufactured current exits/logs.
for i in items:
    if 'reuse' in i and records[i['id']]['status']=='success':
        old=Path(i['reuse']['origin']);target=RUN/i['id']/'original_execution'
        origin=old.parent
        pairs=[(origin/'pilot.log','execution.log'),(origin/'pilot.exit','execution.exit'),(origin/'pilot.py','worker.py')] if old.name=='pilot_0000' else [(origin/(i['id']+'.log'),'execution.log'),(origin/(i['id']+'.exit'),'execution.exit'),(origin/(i['id']+'.py'),'worker.py')]
        for src,name in pairs:
            if src.exists() and not (target/name).exists():shutil.copy2(src,target/name)
        qa=old/'panorama_spherical_check'
        for name in ['manifest.json','review.md']:
            dest=target/('legacy_qa_'+name)
            if (qa/name).exists() and not dest.exists():shutil.copy2(qa/name,dest)
paths=[]
for i in items:
    sid=i['id'];folder=RUN/sid
    if folder.exists():paths.extend(p for p in folder.rglob('*') if p.is_file())
    paths.append(RUN/'records'/(sid+'.json'))
    for suffix in ['.log','.exit','.qa.log','.qa.exit','.attempt.json']:
        p=RUN/(sid+suffix)
        if p.exists():paths.append(p)
    p=RUN/'workers'/(sid+'.py')
    if p.exists():paths.append(p)
for name in ['inventory.json','original_metadata.json','preflight.json','models.json','proven_worker_template.py','pipeline_source.py','spherical_check_v0_2_0.py','controller.py','campaign.py','test_campaign.py','run.sh','qa_tests.log']:
    paths.append(RUN/name)
paths=sorted(set(paths));manifest=[dict(path=str(p.relative_to(RUN)),bytes=p.stat().st_size,sha256=sha(p)) for p in paths]
folder=RUN/'transfer';folder.mkdir(exist_ok=True);stem=cohort+'_'+str(batch)
mp=folder/(stem+'.json');archive=folder/(stem+'.tar')
if mp.exists():assert json.loads(mp.read_text())==manifest,'Frozen batch changed; do not overwrite'
else:mp.write_text(json.dumps(manifest,indent=2))
if not archive.exists():
    with tarfile.open(archive,'w') as t:
        for p in paths:t.add(p,arcname=str(p.relative_to(RUN)),recursive=False)
        t.add(mp,arcname='transfer/'+mp.name)
receipt=dict(archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),files=len(manifest),source_bytes=sum(e['bytes'] for e in manifest),ids=list(records))
print(json.dumps(receipt))
