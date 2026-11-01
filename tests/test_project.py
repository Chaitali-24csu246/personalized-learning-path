import ast,contextlib,hashlib,io,json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'training'))
from engine import ACTIONS,Learner,choose,eligible,fresh,key,update_observation
CONTENT=json.loads((ROOT/'web/content.json').read_text())
class ContentTests(unittest.TestCase):
    def test_inventory_and_unique_ids(self):
        activities=CONTENT['activities'];self.assertEqual(len(CONTENT['topics']),20)
        self.assertEqual(sum(a['type']=='code' for a in activities),60)
        self.assertEqual(sum(a['type']=='mcq' for a in activities),240)
        self.assertEqual(len({a['id'] for a in activities}),len(activities))
    def test_prerequisite_graph_is_acyclic(self):
        seen=set()
        for topic in CONTENT['topics']:
            self.assertTrue(set(topic['prerequisites'])<=seen,topic['id']);seen.add(topic['id'])
    def test_all_reference_solutions(self):
        import copy
        for a in CONTENT['activities']:
            if a['type']!='code':continue
            ns={};exec(a['solution'],ns)
            for case in a['tests']:
                with self.subTest(activity=a['id'],args=case['args']):
                    self.assertEqual(ns['solve'](*copy.deepcopy(case['args'])),case['expected'])
    def test_trace_questions_execute_to_keyed_answer(self):
        for a in CONTENT['activities']:
            if a['type']!='mcq':continue
            self.assertEqual(len(a['options']),4);self.assertEqual(len(set(a['options'])),4)
            if 'code' not in a:continue
            tree=ast.parse(a['code']);last=tree.body.pop();ns={}
            exec(compile(tree,'question','exec'),ns)
            actual=eval(compile(ast.Expression(last.value),'question','eval'),ns)
            self.assertEqual(repr(actual),a['options'][a['answer']],a['id'])
    def test_lesson_examples_execute(self):
        for t in CONTENT['topics']:
            with self.subTest(topic=t['id']),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):exec(t['example'],{})
    def test_assessment_excluded_and_action_coverage(self):
        for t in CONTENT['topics']:
            for mode in ('mcq','code'):
                for level in (1,2,3):self.assertTrue(any(a['topic']==t['id'] and a['type']==mode and a['difficulty']==level and not a['assessment'] for a in CONTENT['activities']))
class LearningTests(unittest.TestCase):
    def test_lesson_does_not_raise_observed_mastery(self):
        s=fresh(1)[0];update_observation(s,0,1,0);self.assertEqual(s['mcq'],.15);self.assertEqual(s['code'],.15)
    def test_mcq_cannot_inflate_coding(self):
        s=fresh(1)[0]
        for i in range(20):update_observation(s,3,1,i)
        self.assertEqual(s['code'],.15);self.assertGreater(s['mcq'],.9)
    def test_easy_evidence_has_ceiling(self):
        s=fresh(1)[0]
        for i in range(20):update_observation(s,1,1,i)
        self.assertLessEqual(s['mcq'],.55)
    def test_prerequisites_block_advanced(self):
        s=fresh(20);self.assertEqual(eligible(s,CONTENT['topics']),[0]);s[0]['mcq']=.5;self.assertIn(1,eligible(s,CONTENT['topics']))
    def test_hidden_truth_not_in_state(self):
        e=Learner(CONTENT['topics'],4);before=key(e.states[0],0,45);e.true[0]=[.99,.99];self.assertEqual(key(e.states[0],0,45),before)
    def test_policy_has_learned_nonuniform_values(self):
        p=json.loads((ROOT/'web/policy.json').read_text());self.assertGreaterEqual(p['episodes'],1000);self.assertGreater(len(p['q']),50)
        self.assertTrue(any(max(row)-min(row)>.1 for row in p['q'].values()));self.assertEqual(p['content_sha256'],hashlib.sha256((ROOT/'web/content.json').read_bytes()).hexdigest())
    def test_seed_reproducibility(self):
        a=Learner(CONTENT['topics'],42);b=Learner(CONTENT['topics'],42)
        for i in range(10):self.assertEqual(a.apply(0,1),b.apply(0,1))
    def test_javascript_parity_fixture(self):
        s=fresh(1)[0];sequence=[(0,1),(1,1),(2,0),(4,.5),(6,1),(3,1)]
        for step,(a,score) in enumerate(sequence):update_observation(s,a,score,step)
        self.assertEqual(key(s,6,45),'2,2,0,0,0,0')
if __name__=='__main__':unittest.main()
