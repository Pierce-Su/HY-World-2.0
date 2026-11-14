import json,time,hashlib
from pathlib import Path
from huggingface_hub import snapshot_download,hf_hub_download
root=Path('/root/HY-World-2.0/deployment/t_1e9a7907')
inv=json.loads((root/'hf-inventory.json').read_text())
out={}
for repo,entry in inv.items():
    print('DOWNLOAD_START',repo,entry['sha'],time.time(),flush=True)
    patterns=['model_index.json','processor/*','scheduler/*','text_encoder/*','tokenizer/*','transformer/*','vae/*'] if repo.startswith('Qwen/') else ['HY-Pano-2.0/pytorch_lora_weights.safetensors']
    path=snapshot_download(repo_id=repo,revision=entry['sha'],allow_patterns=patterns,max_workers=8)
    print('DOWNLOAD_DONE',repo,path,time.time(),flush=True)
    checked=[]
    for f in entry['files']:
        if not f['lfs']: continue
        p=Path(path)/f['path']
        assert p.stat().st_size==f['size'],p
        h=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
        assert h==f['lfs']['sha256'],(p,h)
        checked.append({'path':str(p),'size':p.stat().st_size,'sha256':h})
        print('SHA256_OK',p,h,flush=True)
    out[repo]={'revision':entry['sha'],'snapshot':path,'verified_lfs':checked}
(root/'models.json').write_text(json.dumps(out,indent=2))
print('ALL_MODELS_VERIFIED',flush=True)
