"""Read-only campaign snapshot; never launches/retries generation."""
from pathlib import Path
import json,shutil,subprocess,os
R=Path('/root/HY-World-2.0/deployment/t_ed447ffc')
p=json.loads((R/'progress.json').read_text())
rows=[json.loads(f.read_text()) for f in (R/'records').glob('*.json')]
success=[r for r in rows if r['status']=='success']
p['records_success']=len(success)
p['qa_complete']=sum(r.get('qa',{}).get('png_count')==10 for r in success)
p['visual_reviewed']=sum(r.get('visual_review_status') not in [None,'pending'] for r in success)
p['free_bytes']=shutil.disk_usage(R).free
pid=int((R/'controller.pid').read_text());p['controller_pid']=pid
try: os.kill(pid,0);p['controller_alive']=True
except ProcessLookupError:p['controller_alive']=False
r=subprocess.run(['nvidia-smi','--query-gpu=utilization.gpu,memory.used,memory.total','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=15)
p['gpu']=r.stdout.strip() if r.returncode==0 else 'unavailable'
print(json.dumps(p))
