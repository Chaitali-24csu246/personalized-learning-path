"""Candidate-scoring Double DQN. No production user data or network calls."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import argparse,collections,hashlib,json,pathlib,random
import numpy as np
from engine import Learner,ACTIONS,values
ROOT=pathlib.Path(__file__).resolve().parents[1]
def train(episodes=4000,seed=42,struggle=True,output=None):
    content=json.loads((ROOT/'web/content.json').read_text());rng=np.random.default_rng(seed);random.seed(seed);width=32;dim=28;gamma=.9
    w1=rng.normal(0,.15,(dim,width)).astype('float32');b1=np.zeros(width,dtype='float32');w2=rng.normal(0,.1,width).astype('float32');b2=np.float32(0)
    target=[w1.copy(),b1.copy(),w2.copy(),b2];memory=collections.deque(maxlen=3000);trace=[];updates=0;stepcount=0
    for ep in range(episodes):
        env=Learner(content,seed*100000+ep,struggle=struggle);total=0;rows=env.choices()
        for step in range(30):
            x=np.asarray([r[3] for r in rows],dtype='float32');v=np.maximum(0,x@w1+b1)@w2+b2;epsilon=max(.08,.8*(1-ep/(episodes*.8)))
            index=int(rng.integers(len(rows))) if rng.random()<epsilon else int(np.argmax(v+rng.uniform(0,1e-7,len(v))))
            reward=env.apply(rows[index]);total+=reward;nextrows=env.choices();nx=np.asarray([r[3] for r in nextrows],dtype='float32');terminal=step==29
            memory.append((x[index],reward,nx,terminal));rows=nextrows;stepcount+=1
            if len(memory)>=64 and stepcount%8==0:
                batch=random.sample(list(memory),32);bx=np.stack([b[0] for b in batch]);allnext=np.concatenate([b[2] for b in batch]);online=np.maximum(0,allnext@w1+b1)@w2+b2
                tw1,tb1,tw2,tb2=target;tv=np.maximum(0,allnext@tw1+tb1)@tw2+tb2;targets=[];offset=0
                for _,r,n,done in batch:
                    best=offset+int(np.argmax(online[offset:offset+len(n)]));targets.append(r+(0 if done else gamma*tv[best]));offset+=len(n)
                h=np.maximum(0,bx@w1+b1);pred=h@w2+b2;err=np.clip(pred-np.array(targets),-1,1)/len(batch);grad=(err[:,None]*w2)*(h>0);lr=.006
                w1-=lr*(bx.T@grad+.0001*w1);b1-=lr*grad.sum(axis=0);w2-=lr*(h.T@err+.0001*w2);b2-=lr*err.sum();updates+=1
                if updates%100==0:target=[w1.copy(),b1.copy(),w2.copy(),b2]
        if ep%200==0:
            trace.append(dict(episode=ep,return_=round(total,4)));print(ep,round(total,3),flush=True)
    model=dict(format='candidate-dqn-v3',algorithm='Double DQN candidate scorer',seed=seed,episodes=episodes,budget=30,gamma=gamma,hidden_units=width,productive_struggle=struggle,w1=w1.tolist(),b1=b1.tolist(),w2=w2.tolist(),b2=float(b2),actions=ACTIONS,training_trace=trace,content_sha256=hashlib.sha256((ROOT/'web/content.json').read_bytes()).hexdigest(),limitations='Synthetic training; learning benefits and fatigue/load proxy are not validated on real learners. No online weight updates. Map rollouts assume 75% independent success.')
    path=pathlib.Path(output) if output else ROOT/'web/policy.json';path.write_text(json.dumps(model,separators=(',',':')));return model
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--episodes',type=int,default=4000);p.add_argument('--seed',type=int,default=42);p.add_argument('--no-struggle',action='store_true');p.add_argument('--output');a=p.parse_args();train(a.episodes,a.seed,not a.no_struggle,a.output)
