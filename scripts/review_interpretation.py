#!/usr/bin/env python3
"""Objective first-turn gates. Passing these checks is not a substitute for semantic review."""
import argparse,json,pathlib,collections
p=argparse.ArgumentParser();p.add_argument('report',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path);a=p.parse_args();r=json.loads(a.report.read_text());rows=[]
for t in r['trials']:
 issues=[];sid=t['scenario'].split('-')[0];p=t.get('proposal',{});inp=p.get('preview',{});cs=inp.get('components',[]);patterns=[c['pattern'] for c in cs];facts=p.get('facts',[])
 def need(condition,message):
  if not condition:issues.append(message)
 def values(key):return [f['value'] for f in facts if f['concept']==key and f['status']!='unknown']
 if t['state']!='succeeded':issues.append('Response rejected: '+t.get('error',{}).get('code','unknown'))
 else:
  need(bool(facts),'No facts extracted')
  need(not p.get('partial',False),'Full extraction still invalid after bounded correction')
  if sid=='S01':
   need(patterns==['direct'],'Expected one direct classifier');need(bool(cs) and cs[0]['location']=='local','Explicit local compute lost');need(bool(cs) and cs[0].get('rate')=='100','Peak rate must be 100/minute')
  if sid=='S02':
   need(patterns.count('retrieval')==1 and all(x in ['retrieval','other'] for x in patterns),'Expected one answer-serving retrieval assistant, optionally with specialist supporting work');need(bool(cs) and cs[0]['location']=='local' and cs[0]['retrieval']=='external','Compute/search scope incorrect');need(bool(cs) and cs[0].get('rate')=='40','Peak rate must be 40/minute');need(not inp.get('network',{}).get('initial_tb'),'External corpus is not initial data load');need(not any(c.get('storage_tb') for c in cs),'External corpus is not local retained storage')
  if sid=='S03':need(patterns==['agent'],'Expected agent');need(not any(c.get('calls') for c in cs),'Call envelope selected without confirmation');need('4' in values('calls_typical') and '12' in values('calls_upper'),'Lost typical or upper calls')
  if sid=='S04':need(not any(c.get('dedicated') for c in cs),'Exclusive batch window became dedicated capacity');need(patterns==['batch'],'Expected text batch');need(bool(cs) and cs[0].get('jobs')=='80000' and cs[0].get('window')=='8','Expected 80000 items in eight hours');need(not any(c['location']=='external' for c in cs),'Invented external placement')
  if sid=='S05':need('stream' in patterns and not any(x in patterns for x in ['direct','batch']),'Video must use specialist stream scope')
  if sid=='S06':need('generation' in patterns and not any(x in patterns for x in ['direct','batch','training']),'Images must not use text equations')
  if sid=='S07':need('adaptation' in patterns and 'training' not in patterns,'Adaptation must not become pretraining')
  if sid=='S08':need(patterns==['training'],'Expected training');need(bool(cs) and cs[0].get('tokens')=='90000000000' and cs[0].get('days')=='30','Training token/deadline mismatch')
  if sid=='S09':need('retrieval' in patterns and 'batch' in patterns,'Missing assistant or batch');need(inp.get('overlap')=='no','Lost separate operating windows');need(not any(c.get('users')=='18000' for c in cs),'Employees became active users')
  if sid=='S10':need('agent' in patterns,'Missing repair agent');need(any(f['concept']=='indexing_only' and f['value']=='yes' for f in facts),'Indexing supporting work omitted');need(inp.get('overlap')=='yes','Lost overlapping indexing')
  if sid=='S11':need('stream' in patterns and 'retrieval' in patterns,'Missing video or text service');need(patterns.count('retrieval')==1,'Duplicated answer serving');need(inp.get('overlap')=='yes','Lost overlap')
  if sid=='S12':need('agent' in patterns and 'generation' in patterns,'Missing agent or generation');need(any(c['pattern']=='generation' and c['relationship']=='conditional' for c in cs),'Conditional generation lost');need(inp.get('overlap')=='yes','Campaign overlap lost');need(inp.get('tenancy')=='single','Campaigns became tenants')
  if sid=='S13':need(bool(cs) and all(c['location']=='external' for c in cs),'External model scope not represented')
  if sid=='S14':need(not any(c['location'] in ['local','external'] for c in cs),'Hosted service acquired invented placement');need(sum(c['pattern']=='direct' for c in cs)<=2,'Overall service counted in addition to tiers');need(inp.get('tenancy')=='multi','Customer tenancy lost');need(not any(c.get('rate') or c.get('users') for c in cs),'Customer count became demand');need(any(f['concept']=='dedicated' and f['value']=='yes' for f in facts),'Dedicated tier missing')
  if sid=='S15':need(not cs,'Unknown architecture became confirmed');need(not values('active_users'),'Employee count became active users');need(any(q['concept']=='architecture' for q in p.get('questions',[])),'No architecture clarification')
  if sid=='S16':need(patterns==['other'],'Simulation not recognised');need(not any(q['concept'] in ['input_tokens','output_tokens','training_tokens'] for q in p.get('questions',[])),'Simulation asked for tokens')
 rows.append(dict(scenario=t['scenario'],trial=t['trial'],passed=not issues,issues=issues))
summary=dict(provider=r['provider'],model=r['model'],trials=len(rows),contract_valid=sum(t['state']=='succeeded' for t in r['trials']),objective_checks_passed=sum(x['passed'] for x in rows),threshold_met=bool(rows) and sum(x['passed'] for x in rows)/len(rows)>=.95,semantic_review_required=True,production_release_approved=False,checks=rows)
out=a.output or a.report.with_name(a.report.stem+'-checks.json');out.write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='checks'}))
