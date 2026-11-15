"""Check local index links and observed terminal hashes, no network or generation."""
from pathlib import Path
from html.parser import HTMLParser
import json,hashlib
D=Path(json.loads((Path(__file__).resolve().parent/'local_destination.json').read_text())['path'])
class Links(HTMLParser):
 def __init__(self): super().__init__(); self.paths=[]
 def handle_starttag(self,tag,attrs): self.paths += [v for k,v in attrs if k in ('href','src')]
p=Links();p.feed((D/'index.html').read_text())
assert all((D/x).is_file() for x in p.paths)
assert len(list((D/'contact_sheets').glob('*.jpg')))==14
# Independently observed via canonical exact60649163 remote sha256sum at closeout.
remote_hashes={'controller.log':'c28a6689b613e43678a0ecb93caf16e5b64f9f6fd15e5dcd21b18b4cef1f49b1','controller.exit':'9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa','progress.json':'c927b9a16754bac40de2135e2c8e450053f3cbbf91c10f0683cf0030a557e82f','DONE.json':'c927b9a16754bac40de2135e2c8e450053f3cbbf91c10f0683cf0030a557e82f','qa_tests.log':'3897bcc3d6948ad6c80de1ba7dbcd8d45d410cf61772a0675bcbd58e1d62c320'}
for f,h in remote_hashes.items(): assert hashlib.sha256((D/'provenance/final'/f).read_bytes()).hexdigest()==h
report={'remote_terminal_hashes_observed_via_canonical_ssh':remote_hashes,'local_terminal_hashes_match':True,'index_local_link_occurrences_verified':len(p.paths),'contact_sheet_pages':14,'individual_visual_reviews':0,'overview_samples_viewed':20,'remote_controller_tests':{'passed':6,'interpreter':'/root/HY-World-2.0/.venv-qwen-pano/bin/python'},'local_test_limitation':'Archived campaign tests are remote-absolute-path fixtures; local Python3.14 run hit /root path permission; rerun on original remote venv passed all6.'}
f=D/'provenance/final/closeout_verification.json'; assert not f.exists(); f.write_text(json.dumps(report,indent=2)); print(json.dumps(report,indent=2))
