"""Paired held-out seeds, two simulator settings, no superiority assertion."""
import json,pathlib,random,statistics,argparse
from engine import Learner,choose,pairs
ROOT=pathlib.Path(__file__).resolve().parents[1]
def evaluate(count=100):
    topics=json.loads((ROOT/'web/content.json').read_text())['topics'];model=json.loads((ROOT/'web/policy.json').read_text());results=[]
    for shift in (1.,1.5):
        for method in ('rl','random','rules','fixed'):
            gains=[];ret=[]
            for seed in range(900000,900000+count):
                env=Learner(topics,seed,shift);rng=random.Random(seed)
                for step in range(45):
                    choices=pairs(env.states,topics,step,45)
                    if method=='rl':i,a,k=choose(model['q'],env.states,topics,step,45,rng)
                    elif method=='random':i,a,k=rng.choice(choices)
                    elif method=='fixed':i=min(len(topics)-1,step//7);a=step%7
                    else:
                        i=min({v[0] for v in choices},key=lambda j:min(env.states[j]['mcq'],env.states[j]['code']))
                        s=env.states[i];a=0 if s['fail']>=2 and not s['lesson'] else (1 if s['mcq']<.4 else 2 if s['mcq']<.65 else 4 if s['code']<.4 else 5 if s['code']<.65 else 6)
                    # Every comparison is constrained to the same eligible action pool.
                    if not any(v[0]==i and v[1]==a for v in choices):i,a,k=choices[0]
                    env.apply(i,a)
                gains.append(env.gain());ret.append(env.retention())
            results.append(dict(setting=shift,method=method,n=count,mean_hidden_mastery_gain=statistics.mean(gains),sd_gain=statistics.stdev(gains) if count>1 else 0,mean_simulated_retention=statistics.mean(ret)))
    report={'note':'Synthetic hidden-mastery metrics; not real student learning gains. Same seeds and budgets; policy actions alter random draw paths. Shift changes learning/forgetting assumptions. Fixed schedule is prerequisite-constrained. No automatic claim that RL wins.','results':results}
    (ROOT/'training/evaluation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--learners',type=int,default=100);evaluate(p.parse_args().learners)
