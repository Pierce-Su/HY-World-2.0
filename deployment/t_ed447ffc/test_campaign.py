import copy,json,unittest,collections
from pathlib import Path
import controller as c

class CampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inv=c.read(c.RUN/'inventory.json');cls.items=cls.inv['items'];cls.models=c.read(c.RUN/'models.json');cls.const=c.constants()
    def test_full_inventory_and_nested_styles(self):
        self.assertEqual(len(self.items),140)
        self.assertEqual(len({i['id'] for i in self.items}),140)
        self.assertEqual(collections.Counter(i['cohort'] for i in self.items),{'photorealistic':70,'stylized':70})
        x=next(i for i in self.items if i['id']=='stylized_0005')
        self.assertEqual(x['variant_metadata']['style'],'ukiyo-e')
        self.assertEqual(x['record']['style'],'photorealistic')
    def test_all_five_reuse_original_matches(self):
        reused=[i for i in self.items if 'reuse' in i];self.assertEqual(len(reused),5)
        for i in reused:c.matching(Path(i['reuse']['origin']),i,self.models,self.const)
    def test_changed_prompt_reuse_rejected(self):
        i=copy.deepcopy(next(i for i in self.items if 'reuse' in i));i['variant_metadata']['prompt']+=' changed'
        with self.assertRaises(AssertionError):c.matching(Path(i['reuse']['origin']),i,self.models,self.const)
    def test_changed_source_reuse_rejected(self):
        i=copy.deepcopy(next(i for i in self.items if 'reuse' in i));i['sha256']='0'*64
        with self.assertRaises(AssertionError):c.matching(Path(i['reuse']['origin']),i,self.models,self.const)
    def test_frozen_input_hashes(self):
        for i in self.items:self.assertEqual(c.sha(i['source']),i['sha256'])
    def test_worker_template_preserves_seed_and_cold_load(self):
        text=(c.RUN/'proven_worker_template.py').read_text()
        self.assertIn('seed=42',text);self.assertIn('HunyuanPanoPipeline.from_pretrained',text)
        self.assertEqual(text.count('image=pipe(source,**settings)'),1)

if __name__=='__main__':
    unittest.main(exit=False)
    groups=collections.defaultdict(list)
    for i in c.read(c.RUN/'inventory.json')['items']:groups[i['sha256']].append(i['id'])
    print('Duplicate content groups (variants retained):',json.dumps([g for g in groups.values() if len(g)>1]))
