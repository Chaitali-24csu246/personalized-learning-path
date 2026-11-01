import argparse,json,pathlib,random,statistics,hashlib
from engine import Learner,choose,pairs,ACTIONS
ROOT=pathlib.Path(__file__).resolve().parents[1]
def train(episodes=8000,seed=42):
    content=json.loads((ROOT/'web/content.json').read_text());topics=content['topics'];q={};visits={};rng=random.Random(seed);budget=45;trace=[]
    for ep in range(episodes):
        env=Learner(topics,rng.randrange(10**9));total=0
        for step in range(budget):
            i,a,k=choose(q,env.states,topics,step,budget,rng,max(.08,.8*(1-ep/episodes)))
            reward=env.apply(i,a)
            if step==budget-1:reward+=8*env.gain()
            row=q.setdefault(k,[0.]*7);visits.setdefault(k,[0]*7)[a]+=1
            future=0 if step==budget-1 else max(q.get(nk,[0.]*7)[na] for ni,na,nk in pairs(env.states,topics,step+1,budget))
            row[a]+=.12*(reward+.93*future-row[a]);total+=reward
        if ep%200==0:trace.append({'episode':ep,'return':round(total,4)})
    output={'algorithm':'shared-feature tabular Q-learning','seed':seed,'episodes':episodes,'budget':budget,'gamma':.93,'alpha':.12,'actions':ACTIONS,'state_fields':['mcq_bin','code_bin','repeated_fail','review_due','session_phase','lesson_seen'],'q':q,'visits':visits,'training_trace':trace,'content_sha256':hashlib.sha256((ROOT/'web/content.json').read_bytes()).hexdigest(),'limitations':'Trained on synthetic learners, not validated educational efficacy. Aggregated observations alias histories. Topic prerequisites and item selection are deterministic constraints. Completion of a lesson does not increase observed mastery.'}
    (ROOT/'web/policy.json').write_text(json.dumps(output,separators=(',',':')))
    print(f'Trained {episodes} episodes; {len(q)} state rows')
    return q
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--episodes',type=int,default=8000);p.add_argument('--seed',type=int,default=42);args=p.parse_args();train(args.episodes,args.seed)
