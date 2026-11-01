"""Shared-feature tabular Q-learning for a partially observed multi-topic learner.
Q values rank (eligible topic, activity) pairs. State abstraction aliases global
histories; it is not a full Markov model of a real student. No hidden knowledge
is used in the policy state. Hidden knowledge is used only for simulated rewards.
"""
import math, random
ACTIONS=[{'type':'lesson','difficulty':0}]+[{'type':typ,'difficulty':d} for typ in ('mcq','code') for d in (1,2,3)]
def fresh(n):
    return [dict(mcq=.15,code=.15,fail=0,last=-10,lesson=False,attempts=0) for _ in range(n)]
def key(s,step,budget):
    return ','.join(map(str,[min(3,int(s['mcq']*4)),min(3,int(s['code']*4)),int(s['fail']>=2),int(step-s['last']>=8 and s['attempts']>0),min(2,int(step/max(1,budget)*3)),int(s['lesson'])]))
def eligible(states,topics):
    idx={t['id']:i for i,t in enumerate(topics)}
    return [i for i,t in enumerate(topics) if all(states[idx[p]]['mcq']>=.4 for p in t['prerequisites'])]
def pairs(states,topics,step,budget):
    result=[]
    for i in eligible(states,topics):
        s=states[i]
        if min(s['mcq'],s['code'])>=.85 and step-s['last']<8: continue
        for a in range(7):
            if a==0 and s['lesson']: continue
            result.append((i,a,key(s,step,budget)))
    return result or [(0,1,key(states[0],step,budget))]
def choose(q,states,topics,step,budget,rng,epsilon=0):
    choices=pairs(states,topics,step,budget)
    if rng.random()<epsilon:return rng.choice(choices)
    # Seeded random tie-breaking during training. UI uses stable order on ties.
    best=max(q.get(k,[0.]*7)[a] for i,a,k in choices)
    return rng.choice([x for x in choices if q.get(x[2],[0.]*7)[x[1]]==best])
def update_observation(s,a,score,step):
    action=ACTIONS[a]
    if a==0:
        s['lesson']=True
        return
    mode=action['type']; target=[.55,.8,1.][action['difficulty']-1]*score
    rate=.55 if mode=='code' else .4
    s[mode]=max(.02,min(.98,s[mode]+rate*(target-s[mode])))
    s['fail']=s['fail']+1 if score<.5 else 0
    s['attempts']+=1;s['last']=step;s['lesson']=False
class Learner:
    def __init__(self,topics,seed,shift=1.):
        self.rng=random.Random(seed); self.topics=topics;self.states=fresh(len(topics));self.step=0
        r=self.rng
        # Vary start, learning rate, forgetting, slip and guessing independently.
        self.true=[[r.uniform(.03,.4),r.uniform(.02,.25)] for _ in topics]
        self.initial=[x[:] for x in self.true]
        self.rate=r.uniform(.045,.15)*shift;self.forget=r.uniform(.0001,.002)*shift
        self.slip=r.uniform(.02,.15);self.guess=r.uniform(.1,.25)
    def apply(self,i,a):
        r=self.rng;act=ACTIONS[a];before=sum(map(sum,self.true));s=self.states[i]
        for j in range(len(self.true)):
            for m in range(2):self.true[j][m]*=(1-self.forget)
        m=0 if act['type']!='code' else 1
        skill=self.true[i][m];d=act['difficulty'];difficulty=[.15,.25,.55,.8][d]
        challenge=math.exp(-((skill-difficulty)/.38)**2)
        support=1.35 if s['lesson'] else 1.
        gain=self.rate*(1-skill)*(0.7 if a==0 else .25+challenge)*support
        self.true[i][m]=min(.99,skill+gain)
        if a==0:self.true[i][1]=min(.99,self.true[i][1]+gain*.12)
        elif m==1:self.true[i][0]=min(.99,self.true[i][0]+gain*.25)
        p=1/(1+math.exp(-6*(self.true[i][m]-difficulty)))
        p=(self.guess if m==0 and a!=0 else .01)+(1-self.slip-(self.guess if m==0 and a!=0 else .01))*p
        score=float(r.random()<p)
        if m==1: score=sum(r.random()<p for _ in range(4))/4
        update_observation(s,a,score,self.step);self.step+=1
        reward=12*(sum(map(sum,self.true))-before)-.035
        return reward
    def gain(self):return sum(sum(a)-sum(b) for a,b in zip(self.true,self.initial))/(2*len(self.true))
    def retention(self):return sum(map(sum,self.true))*(1-self.forget)**30/(2*len(self.true))
