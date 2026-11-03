"""V3 observable candidate state, finite activity bank, synthetic learning only."""
import copy, math, random
import numpy as np
ACTIONS=[{'type':'lesson','difficulty':0}]+[{'type':m,'difficulty':d} for m in ('mcq','code') for d in (1,2,3)]
def clamp(x,a=0,b=1):return max(a,min(b,x))
def fresh(n):return [dict(mcq=.15,code=.15,fail=0,last=-10,lesson=False,attempts=0,mcqCount=0,codeCount=0,recent=[]) for _ in range(n)]
def update_observation(s,a,score,step,weight=1):
    act=ACTIONS[a] if isinstance(a,int) else a
    if act['type']=='lesson':s['lesson']=True;return
    m=act['type'];rate=(.48 if m=='code' else .38)*weight
    target=[.5,.8,1][act['difficulty']-1]*score
    if score==1:target=max(s[m],target)
    s[m]=clamp(s[m]+rate*(target-s[m]),.02,.98)
    s['fail']=s['fail']+1 if score<.5 else 0;s['attempts']+=1;s['last']=step;s['lesson']=False
    if weight>=.5:s[m+'Count']+=1

def eligible(states,topics):
    ix={t['id']:i for i,t in enumerate(topics)}
    return [i for i,t in enumerate(topics) if (states[i]['mcq']>=.65 and states[i]['mcqCount']>=2) or all(states[ix[k]]['mcq']>=.4 for k in t['prerequisites'])]
def features(states,step,load,i,a,repeat=False):
    s=states[i];act=ACTIONS[a];m='code' if act['type']=='code' else 'mcq';skill=s[m];other=s['mcq' if m=='code' else 'code'];d=act['difficulty']/3
    due=clamp((step-s['last'])/12) if s['attempts'] else 0;last=s['recent'][-1] if s['recent'] else {};mean=sum((x['mcq']+x['code'])/2 for x in states)/len(states)
    return [float(j==a) for j in range(7)]+[s['mcq'],s['code'],skill,other-skill,d,d*d,skill*d,(skill-d)**2,due,min(1,s[m+'Count']/4),float(s['lesson']),clamp(s['fail']/3),load,load*d,float(repeat),last.get('score',.5),clamp(last.get('seconds',0)/(600 if m=='code' else 120)),mean,skill-mean,min(1,s['attempts']/8),float(s['attempts']>0)]
class Learner:
    def __init__(self,content,seed,shift=1.,struggle=True):
        self.content=content;self.topics=content['topics'];self.rng=random.Random(seed);r=self.rng;self.states=fresh(len(self.topics));self.step=0;self.load=0.;self.struggle=struggle;self.used={};self.history=[]
        self.rate=r.uniform(.06,.18)*shift;self.forget=r.uniform(.0002,.0015)*shift;self.slip=r.uniform(.02,.12)
        level=r.choice([.12,.35,.65,.85]);self.true=[[clamp(r.gauss(level,.24),.03,.97),clamp(r.gauss(level+r.choice([-.3,0,.1]),.23),.03,.97)] for _ in self.topics]
        # Noisy diagnostic observations; hidden values never enter the feature vector.
        if r.random()<.85:
            for i,s in enumerate(self.states):
                for m in ('mcq','code'):
                    s[m]=clamp(self.true[i][m=='code']+r.gauss(0,.13),.03,.95);s[m+'Count']=r.choice([1,2,3]);s['attempts']+=s[m+'Count']
        self.initial=copy.deepcopy(self.true)
        self.bank={}
        for i,t in enumerate(self.topics):
            for a,act in enumerate(ACTIONS):self.bank[i,a]=[x for x in content['activities'] if x['topic']==t['id'] and x['type']==act['type'] and x['difficulty']==act['difficulty'] and not x['assessment']]
    def choices(self):
        rows=[]
        for i in eligible(self.states,self.topics):
            s=self.states[i]
            for a,act in enumerate(ACTIONS):
                if a==0:
                    if s['lesson'] or s['mcq']>=.7:continue
                    item=None
                else:
                    items=[x for x in self.bank[i,a] if x['family'] not in self.used or self.step-self.used[x['family']]['step']>=8]
                    if not items:continue
                    item=min(items,key=lambda x:self.used.get(x['family'],{}).get('step',-10000))
                rep=item is not None and item['family'] in self.used
                rows.append((i,a,item,features(self.states,self.step,self.load,i,a,rep)))
        return rows
    def apply(self,row):
        i,a,item,_=row;r=self.rng;s=self.states[i];act=ACTIONS[a];m=int(act['type']=='code');skill=self.true[i][m];difficulty=[.15,.2,.5,.8][act['difficulty']];before=sum(map(sum,self.true));oldload=self.load
        for vals in self.true:
            for j in range(2):vals[j]*=1-self.forget
        repeat=bool(item and item['family'] in self.used);due=clamp((self.step-s['last'])/12) if s['attempts'] else 0
        challenge=math.exp(-((skill-difficulty+.12)/.3)**2)
        gain=self.rate*(1-skill)*(.65 if a==0 else .2+challenge)*(1.25 if s['lesson'] else 1)*(1-.65*self.load)
        if repeat:gain*=.15+.35*due
        self.true[i][m]=clamp(skill+gain,.01,.99)
        if a==0:self.true[i][1]=clamp(self.true[i][1]+gain*.15)
        if a==0:
            self.load=clamp(self.load-.3);s['lesson']=True;score=0
        else:
            probability=clamp(1/(1+math.exp(-7*(self.true[i][m]-difficulty)))*(1-self.slip-self.load*.12)+(.1 if m==0 else 0))
            score=sum(r.random()<probability for _ in range(4))/4 if m else float(r.random()<probability)
            prev=self.used.get(item['family']);gap=self.step-prev['step'] if prev else 999
            weight=1 if not prev else .2 if gap>=8 else .3 if score>prev['best'] else 0
            if weight:update_observation(s,a,score,self.step,weight)
            elif score<.5:s['fail']+=1;s['last']=self.step
            seconds=r.uniform(.5,1.5)*(100 if m==0 else 420)*(1+.5*self.load)
            s['recent'].append(dict(type=act['type'],score=score,difficulty=act['difficulty'],seconds=seconds));s['recent']=s['recent'][-12:]
            self.used[item['family']]=dict(step=self.step,best=max(score,prev['best'] if prev else 0))
            self.load=clamp(self.load+[0,.02,.08,.16][act['difficulty']]+(.18 if score<.5 else 0)-(.2 if act['difficulty']==1 else 0))
        reward=18*(sum(map(sum,self.true))-before)-.025
        # Explicit small challenge/load terms; learning remains the dominant objective.
        if self.struggle and a:
            reward+=.06*(challenge-.5)-.08*max(0,self.load-.6)-(.08 if repeat and due<.5 else 0)
        self.step+=1;self.history.append(dict(topic=i,action=a,score=score,load=self.load,reward=reward));return reward
    def gain(self):return sum(sum(a)-sum(b) for a,b in zip(self.true,self.initial))/(2*len(self.true))
    def retention(self):return sum(map(sum,self.true))*(1-self.forget)**30/(2*len(self.true))

def values(model,x):
    x=np.asarray(x,dtype=np.float32);return np.maximum(0,x@np.asarray(model['w1'])+np.asarray(model['b1']))@np.asarray(model['w2'])+model['b2']
