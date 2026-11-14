"""Task-scoped transport through the authorized exact-instance wrapper only."""
import subprocess,sys,shlex,base64
from pathlib import Path
WRAPPER=['/home/pierce/vast-ssh-workflow/vast-ssh','--config','/home/pierce/.config/vast-ssh/config.json','--non-interactive','--id','60649163','--']
mode,src,dst=sys.argv[1:]
if mode=='put':
    data=base64.b64encode(Path(src).read_bytes()).decode()
    command='set -e; test ! -e '+shlex.quote(dst)+'; printf %s '+shlex.quote(data)+' | base64 -d > '+shlex.quote(dst)
    subprocess.run(WRAPPER+['bash','-lc',command],check=True,timeout=90)
elif mode=='get':
    r=subprocess.run(WRAPPER+['base64','-w0',src],check=True,capture_output=True,timeout=180)
    # Welcome banner is stderr, stdout contains only base64 on this route.
    Path(dst).parent.mkdir(parents=True,exist_ok=True)
    Path(dst).write_bytes(base64.b64decode(r.stdout,validate=True))
    print('received',dst,Path(dst).stat().st_size)
else: raise ValueError(mode)
