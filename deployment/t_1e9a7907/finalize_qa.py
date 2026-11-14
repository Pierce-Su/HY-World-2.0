import json,hashlib,shutil,sys
from pathlib import Path
from PIL import Image
ROOT=Path('/root/HY-World-2.0/deployment/t_1e9a7907')
qa=ROOT/'pilot_0000/panorama_spherical_check'
m=json.loads((qa/'manifest.json').read_text())
assert m['config']['layout']=='eight'
assert m['config']['fov_horizontal_degrees']==m['config']['fov_vertical_degrees']==90
assert [x['yaw'] for x in m['views'][:8]]==[0,45,90,135,180,225,270,315]
assert len(m['views'])==10
for entry in [m['input'],m['source']]:
    assert hashlib.file_digest(Path(entry['path']).open('rb'),'sha256').hexdigest()==entry['sha256']
for entry in m['outputs']:
    p=qa/entry['path']; assert p.stat().st_size==entry['bytes']; assert hashlib.file_digest(p.open('rb'),'sha256').hexdigest()==entry['sha256']
    with Image.open(p) as im: im.load(); assert list(im.size)==entry['size']
assert len(list(qa.glob('*.png')))==10
review=(qa/'review.md');assert m['review_status']=='pending_manual_review'
shutil.copy2(review,qa/'review.pending.md')
review.write_bytes((ROOT/'visual_review.md').read_bytes())
m.update(review_status='reviewed_2d',reviewer='Hermes Developer agent',visual_verdict='review',review_sha256=hashlib.sha256(review.read_bytes()).hexdigest())
(qa/'manifest.json').write_text(json.dumps(m,indent=2))
print('QA_IMAGES_VERIFIED',len(m['outputs']),'PNG_VIEWS',len(m['views']),'REVIEW_SHA256',m['review_sha256'])
