import ast,contextlib,hashlib,io,json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'training'))
from engine import ACTIONS,Learner,eligible,fresh,features,update_observation,values
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
    def test_lesson_not_mastery(self):
        s=fresh(1)[0];update_observation(s,0,1,0);self.assertEqual(s['mcq'],.15)
    def test_mcq_not_coding(self):
        s=fresh(1)[0];update_observation(s,3,1,0);self.assertEqual(s['code'],.15)
    def test_easy_success_preserves_prior_stronger_evidence(self):
        s=fresh(1)[0];s['mcq']=.85;update_observation(s,1,1,0);self.assertEqual(s['mcq'],.85)
    def test_seed_reproducibility(self):
        a=Learner(CONTENT,42);b=Learner(CONTENT,42)
        for _ in range(10):self.assertEqual(a.apply(a.choices()[0]),b.apply(b.choices()[0]))
    def test_truth_not_in_features(self):
        e=Learner(CONTENT,42);before=features(e.states,0,0,0,1);e.true[0]=[.99,.99];self.assertEqual(before,features(e.states,0,0,0,1))
    def test_saved_policy_and_content_identity(self):
        p=json.loads((ROOT/'web/policy.json').read_text());self.assertEqual(p['format'],'candidate-dqn-v3');self.assertGreaterEqual(p['episodes'],1000);self.assertEqual(len(p['w1']),28);self.assertEqual(p['content_sha256'],hashlib.sha256((ROOT/'web/content.json').read_bytes()).hexdigest());self.assertTrue(any(abs(v)>.01 for v in p['w2']))
    def test_simulation_choices_have_real_items_and_prerequisites(self):
        e=Learner(CONTENT,42)
        for i,a,item,x in e.choices():
            self.assertIn(i,eligible(e.states,e.topics));self.assertEqual(len(x),28)
            if a:self.assertFalse(item['assessment']);self.assertEqual(item['difficulty'],ACTIONS[a]['difficulty'])
    def test_reward_ablation_changes_reward_not_observations(self):
        a=Learner(CONTENT,42,struggle=True);b=Learner(CONTENT,42,struggle=False);ra=a.apply(next(r for r in a.choices() if r[1]==3));rb=b.apply(next(r for r in b.choices() if r[1]==3));self.assertNotEqual(ra,rb);self.assertEqual(a.states,b.states)
if __name__=='__main__':unittest.main()
