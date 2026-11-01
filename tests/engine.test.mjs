import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {ACTIONS,freshState,stateKey,updateObservation,status,recommend} from '../web/engine.mjs';
const content=JSON.parse(fs.readFileSync(new URL('../web/content.json',import.meta.url))),policy=JSON.parse(fs.readFileSync(new URL('../web/policy.json',import.meta.url)));
const profile=()=>({states:Object.fromEntries(content.topics.map(t=>[t.id,freshState()])),step:0,credited:[]});
test('MCQ success cannot mark an untested coder secure',()=>{let s=freshState();for(let i=0;i<10;i++)updateObservation(s,ACTIONS[3],1,i);assert.notEqual(status(s).color,'green');assert.equal(s.code,.15);});
test('lesson is not mastery evidence',()=>{let s=freshState();updateObservation(s,ACTIONS[0],1,0);assert.equal(status(s).color,'gray');});
test('state transitions match Python fixture',()=>{let s=freshState();[[0,1],[1,1],[2,0],[4,.5],[6,1],[3,1]].forEach(([a,r],i)=>updateObservation(s,ACTIONS[a],r,i));assert.equal(stateKey(s,6),'2,2,0,0,0,0');});
test('recommendations respect prerequisite graph and available items',()=>{let p=profile();for(let i=0;i<120;i++){let r=recommend(content,policy,p);assert.ok(r.topic.prerequisites.every(id=>p.states[id].mcq>=.4));if(r.activity){assert.equal(r.activity.assessment,false);assert.ok(!p.credited.includes(r.activity.family));p.credited.push(r.activity.family);}updateObservation(p.states[r.topic.id],r.action,1,p.step);p.step++;}});
test('changing learned values changes selected activity',()=>{let p=profile(),k=stateKey(p.states.basics,0);let q={q:{[k]:[1,0,0,0,0,0,0]}};assert.equal(recommend(content,q,p).action.type,'lesson');q.q[k]=[0,0,0,0,5,0,0];assert.equal(recommend(content,q,p).action.type,'code');});
test('missing policy state has explicit fallback',()=>{let r=recommend(content,{q:{}},profile());assert.equal(r.source,'fallback');assert.ok(r.activity);});
test('unknown mastery is gray, not a failure label',()=>assert.equal(status(freshState()).color,'gray'));

test('first easy success is developing rather than a failure label',()=>{let s=freshState();updateObservation(s,ACTIONS[4],1,0);assert.equal(status(s).color,'yellow');});
