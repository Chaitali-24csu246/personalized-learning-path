"""Held-out simulator evaluation; no claims of real educational benefit."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import argparse,json,pathlib,random,statistics
import numpy as np
from engine import Learner,values
ROOT=pathlib.Path(__file__).resolve().parents[1]
def cf_training(content):
    # Neighbour recommender: training learners' initial profiles and observed per-topic/action gains.
    vectors=[];ratings=[]
    for seed in range(120000,120160):
        env=Learner(content,seed);vectors.append([s[m] for s in env.states for m in ('mcq','code')]);r=np.full((len(env.topics),7),np.nan)
        sums={};counts={}
        for _ in range(45):
            rows=env.choices();row=env.rng.choice(rows);i,a,_,_=row;before=env.states[i]['mcq']+env.states[i]['code'];env.apply(row);gain=env.states[i]['mcq']+env.states[i]['code']-before
            sums[i,a]=sums.get((i,a),0)+gain;counts[i,a]=counts.get((i,a),0)+1
        for (i,a),v in sums.items():r[i,a]=v/counts[i,a]
        ratings.append(r)
    return np.array(vectors),np.array(ratings)
def evaluate(count=100,policy_path=None):
    content=json.loads((ROOT/'web/content.json').read_text());model=json.loads(pathlib.Path(policy_path or ROOT/'web/policy.json').read_text());vectors,ratings=cf_training(content);results=[]
    for shift in (1.,1.5):
        for method in ('rl','random','rules','fixed','collaborative_filtering','zero_weights'):
            gains=[];ret=[];loads=[];hist={str(a):0 for a in range(7)}
            for seed in range(900000,900000+count):
                env=Learner(content,seed,shift);rng=random.Random(seed)
                for step in range(30):
                    rows=env.choices()
                    if method=='rl':idx=int(np.argmax(values(model,[r[3] for r in rows])))
                    elif method=='random':idx=rng.randrange(len(rows))
                    elif method=='zero_weights':idx=0 # deliberate policy ablation, fixed candidate order
                    elif method=='fixed':idx=next((j for j,r in enumerate(rows) if r[0]==min(len(env.topics)-1,step//7) and r[1]==step%7),0)
                    elif method=='rules':
                        def heuristic(row):
                            i,a,_,_=row;s=env.states[i];m='code' if a>=4 else 'mcq';skill=s[m];desired=1 if skill<.4 or env.load>.65 else 2 if skill<.7 else 3
                            return (1-skill)+(1 if a and (a-1)%3+1==desired else 0)-(.5 if a==0 else 0)
                        idx=max(range(len(rows)),key=lambda j:heuristic(rows[j]))
                    else:
                        vec=np.array([s[m] for s in env.states for m in ('mcq','code')]);nn=np.argsort(((vectors-vec)**2).mean(axis=1))[:12];rr=ratings[nn];valid=np.isfinite(rr);sums=np.nansum(rr,axis=0);counts=valid.sum(axis=0);scores=np.divide(sums,counts,out=np.zeros_like(sums),where=counts>0);idx=max(range(len(rows)),key=lambda j:scores[rows[j][0],rows[j][1]])
                    hist[str(rows[idx][1])]+=1;env.apply(rows[idx])
                gains.append(env.gain());ret.append(env.retention());loads.append(env.load)
            results.append(dict(setting=shift,method=method,n=count,mean_hidden_mastery_gain=statistics.mean(gains),sd_gain=statistics.stdev(gains) if count>1 else 0,mean_simulated_retention=statistics.mean(ret),mean_load_proxy=statistics.mean(loads),actions=hist))
    out=dict(note='Synthetic results only. Same held-out seeds and budgets; actions alter random draw streams. CF uses training seeds 120000–120159 only. Load is a design proxy, not measured fatigue. zero_weights tests dependence on learned scores.',policy=model['format'],results=results)
    (ROOT/'training/evaluation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2));return out
def evaluate_ablation(count,other_path):
    content=json.loads((ROOT/'web/content.json').read_text());models=[('productive_struggle',json.loads((ROOT/'web/policy.json').read_text())),('learning_gain_only',json.loads(pathlib.Path(other_path).read_text()))];rows=[]
    for shift in (1.,1.5):
        for label,model in models:
            gains=[];ret=[];loads=[]
            for seed in range(900000,900000+count):
                env=Learner(content,seed,shift)
                for step in range(30):
                    choices=env.choices();idx=int(np.argmax(values(model,[r[3] for r in choices])));env.apply(choices[idx])
                gains.append(env.gain());ret.append(env.retention());loads.append(env.load)
            rows.append(dict(setting=shift,policy=label,n=count,mean_hidden_mastery_gain=statistics.mean(gains),sd_gain=statistics.stdev(gains),mean_simulated_retention=statistics.mean(ret),mean_load_proxy=statistics.mean(loads)))
    result=dict(note='Reward ablation: same architecture, seed 42, 8000 episodes and training environment; only explicit reward shaping disabled for learning_gain_only. Both environments retain challenge-dependent learning and load assumptions. Synthetic outcomes, not real efficacy.',results=rows)
    (ROOT/'training/reward_ablation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--learners',type=int,default=100);p.add_argument('--policy');p.add_argument('--ablation');a=p.parse_args()
    if a.ablation:evaluate_ablation(a.learners,a.ablation)
    else:evaluate(a.learners,a.policy)
