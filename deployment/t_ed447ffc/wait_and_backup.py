"""Bounded event-driven completion observer, then verified local backup.
Only the private waiter's command_timeout differs from canonical config.
No polling and never replays inference when monitoring fails.
"""
import subprocess,json,os,sys,datetime
from pathlib import Path
W=Path(__file__).resolve().parent
cfg=json.loads(Path('/home/pierce/.config/vast-ssh/config.json').read_text())
private=dict(cfg,command_timeout=28800)
assert {k:v for k,v in private.items() if k!='command_timeout'}=={k:v for k,v in cfg.items() if k!='command_timeout'}
p=W/'wait-only-config.json';p.write_text(json.dumps(private,indent=2));p.chmod(0o600)
waiter=['/home/pierce/vast-ssh-workflow/vast-ssh','--config',str(p),'--non-interactive','--id','60649163','--','tmux','wait-for','curated140-t_ed447ffc']
print('WAITING_FOR_DURABLE_REMOTE_EVENT',datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
r=subprocess.run(waiter,timeout=28860)
if r.returncode:
    print('MONITOR_FAILURE original remote work not restarted; inspect original PID/log/progress',flush=True);sys.exit(r.returncode)
# Event means terminal, not successful: independently read exact progress before backup.
canonical=['/home/pierce/vast-ssh-workflow/vast-ssh','--config','/home/pierce/.config/vast-ssh/config.json','--non-interactive','--id','60649163','--']
r=subprocess.run(canonical+['/usr/bin/cat','/root/HY-World-2.0/deployment/t_ed447ffc/progress.json'],capture_output=True,check=True,timeout=180)
progress=json.loads(r.stdout);print('REMOTE_TERMINAL_READBACK',json.dumps(progress),flush=True)
(W/'completion_progress.json').write_text(json.dumps(progress,indent=2))
if progress['status'] not in ['DONE','DONE_WITH_FAILURES'] or progress['pending']!=0:
    print('REMOTE_PAUSED: evidence preserved; no automated inference retry',flush=True);sys.exit(2)
print('BACKUP_START',flush=True)
subprocess.run([sys.executable,str(W/'backup.py'),'final'],check=True,timeout=7200,cwd=W)
print('DONE_REMOTE_GENERATION_QA_AND_LOCAL_HASH_BACKUP_NEEDS_AGENT_INDEPENDENT_REVIEW',datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
