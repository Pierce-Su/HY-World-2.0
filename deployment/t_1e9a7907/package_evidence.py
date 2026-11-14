from pathlib import Path
import zipfile,hashlib,json
root=Path('/root/HY-World-2.0/deployment/t_1e9a7907')
paths=sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.zip')
output=root/'hypano-qwen-t_1e9a7907-evidence.zip'
assert not output.exists()
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
    for p in paths: z.write(p,str(p.relative_to(root)))
    z.write('/root/HY-World-2.0/curated_set/photorealistic/0000.jpg','input/0000.jpg')
print(json.dumps({'archive':str(output),'bytes':output.stat().st_size,'sha256':hashlib.file_digest(output.open('rb'),'sha256').hexdigest(),'files':len(paths)+1}))
