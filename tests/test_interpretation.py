"""Deterministic fact-contract, measurement, architecture and multi-turn regression."""
import json,unittest,copy
from test_copilot import Copilot

def fact(concept,value='',unit='',period='',period_unit='',activity='Service',status='reported'):
 return dict(activity=activity,concept=concept,value=value,unit=unit,period_value=period,period_unit=period_unit,status=status,source_id='',quote='')
class Interpretation(Copilot):
 # Keep this suite focused, while reusing the fixture and authenticated API helpers.
 def propose_facts(self,s,rows):
  statement='Consultant measurements and choices: '+json.dumps(rows)
  source=self.source(s,statement)
  rows=copy.deepcopy(rows)
  for f in rows:f.update(source_id=source['id'],quote=statement)
  return self.good('copilot-sessions/'+s['id']+'/proposals','POST',{'facts':rows})
 def direct(self):return [fact('text_model','yes'),fact('search','no'),fact('actions','no'),fact('compute_location','local')]
 def test_f01_hourly_units(self):
  _,s=self.setup_case();p=self.propose_facts(s,self.direct()+[fact('demand_basis','measured_peak'),fact('requests','2400','request','1','hour')]);self.assertEqual(p['data']['preview']['components'][0]['rate'],'40');self.assertEqual(p['data']['trace'][-1]['unit'],'request/min')
  p2=self.propose_facts(s,self.direct()+[fact('demand_basis','measured_peak'),fact('requests','40','request','1','min')]);self.assertEqual(p2['data']['preview']['components'][0]['rate'],'40')
 def test_f02_daily_is_not_peak(self):
  _,s=self.setup_case();p=self.propose_facts(s,self.direct()+[fact('demand_basis','average'),fact('requests','900000','request','1','day')]);self.assertNotIn('rate',p['data']['preview']['components'][0]);self.assertEqual(p['data']['questions'][0]['concept'],'demand_basis')
 def test_f03_architecture_rules(self):
  for rows,expected in [([fact('search','yes')],'retrieval'),([fact('actions','yes')],'agent'),([fact('media','image_generation'),fact('schedule','batch')],'generation'),([fact('media','video_analysis')],'stream'),([fact('training_method','peft')],'adaptation'),([fact('training_method','pretraining')],'training'),([fact('simulation','yes')],'other')]:
   _,s=self.setup_case();p=self.propose_facts(s,rows);self.assertEqual(p['data']['preview']['components'][0]['pattern'],expected)
 def test_f04_population_and_unknowns(self):
  _,s=self.setup_case();p=self.propose_facts(s,[fact('population','5000','person'),fact('text_model',status='unknown')]);self.assertEqual(p['data']['preview']['components'],[]);self.assertEqual(p['data']['questions'][0]['concept'],'architecture');code,r=self.apply(p);self.assertEqual(code,201,r);self.assertEqual(r['session']['data']['draft_id'],'');self.assertEqual(len(r['session']['data']['facts']),2)
 def test_f05_users_route(self):
  _,s=self.setup_case();p=self.propose_facts(s,self.direct()+[fact('demand_basis','users'),fact('population','5000','person'),fact('active_users','100','person'),fact('requests_per_user','2','request','1','min')]);c=p['data']['preview']['components'][0];self.assertEqual(c['users'],'100');self.assertEqual(c['interval'],'30');self.assertNotIn('rate',c)
 def test_f06_agent_envelope(self):
  _,s=self.setup_case();rows=[fact('actions','yes'),fact('calls_typical','4','call'),fact('calls_upper','12','call')];p=self.propose_facts(s,rows);self.assertNotIn('calls',p['data']['preview']['components'][0]);p=self.propose_facts(s,rows+[fact('call_envelope','upper')]);self.assertEqual(p['data']['preview']['components'][0]['calls'],'12')
 def test_f07_scope_and_storage(self):
  _,s=self.setup_case();p=self.propose_facts(s,[fact('search','yes'),fact('compute_location','local'),fact('search_location','external'),fact('data_location','external'),fact('storage','4','TB')]);c=p['data']['preview']['components'][0];self.assertEqual(c['location'],'local');self.assertEqual(c['retrieval'],'external');self.assertNotIn('storage_tb',c)
 def test_f08_relationship_tenancy(self):
  _,s=self.setup_case();p=self.propose_facts(s,[fact('actions','yes'),fact('media','image_generation',activity='Assets'),fact('relationship','conditional',activity='Assets'),fact('overlap','yes',activity='Factory')]);cs=p['data']['preview']['components'];self.assertEqual(next(c for c in cs if c['name']=='Assets')['relationship'],'conditional');self.assertEqual(p['data']['preview']['tenancy'],'single');self.assertEqual(p['data']['preview']['overlap'],'yes')
 def test_f09_conflict_and_stale(self):
  _,s=self.setup_case();p=self.propose_facts(s,self.direct());code,r=self.apply(p);self.assertEqual(code,201,r);s=r['session'];p=self.propose_facts(s,[fact('compute_location','external')]);self.assertEqual(len(p['data']['conflicts']),1);self.assertEqual(p['data']['questions'][0]['concept'],'conflict');self.assertEqual(self.good('copilot-sessions/'+s['id'])['data']['input']['components'][0]['location'],'local');self.assertEqual(self.apply(p)[0],201)
 def test_f10_multi_turn_to_sizing_and_handoff(self):
  _,s=self.setup_case();p=self.propose_facts(s,self.direct());code,r=self.apply(p);self.assertEqual(code,201,r)
  rows=[fact('demand_basis','measured_peak'),fact('requests','2400','request','1','hour'),fact('model','dense8b'),fact('input_tokens','2000','token'),fact('output_tokens','500','token')]
  p=self.propose_facts(r['session'],rows);self.assertTrue(p['data']['ready_for_estimate']);code,r=self.apply(p);self.assertEqual(code,201,r);d=r['draft'];rev=self.good('drafts/'+d['id']+'/freeze','POST',{},extra={'If-Match':str(d['version'])});j=self.wait(self.good('compilations','POST',{'revision_id':rev['id']}));self.assertEqual(j['data']['state'],'succeeded');facts=self.good('copilot-facts/'+j['data']['result_id']);self.assertEqual(len(facts['planning']['hardware_comparison']),3)
  manual=self.good('guided-workloads','POST',r['session']['data']['input']);self.assertEqual(manual,d['data'])
  pr=self.good('neon-projections','POST',{'result_id':j['data']['result_id'],'mapping':{'candidate_id':'planning:factory','platform':'HGX_B300','network_fabric':'Spectrum-X'}});self.assertGreater(pr['data']['payload']['requirements']['target_gpu_count'],0)
 def test_f11_specialist_no_tokens(self):
  _,s=self.setup_case();p=self.propose_facts(s,[fact('simulation','yes'),fact('compute_location','local')]);self.assertEqual(p['data']['preview']['components'][0]['pattern'],'other');self.assertFalse(p['data']['ready_for_estimate']);self.assertNotIn('input_tokens',[q['concept'] for q in p['data']['questions']]);self.assertIn('requirements brief',p['data']['question'])
 def test_f12_network_conversion(self):
  _,s=self.setup_case();p=self.propose_facts(s,[fact('initial_data','1000','GB',activity='Factory'),fact('load_window','1','day',activity='Factory'),fact('storage_read','2','GB/s',activity='Factory')]);n=p['data']['preview']['network'];self.assertEqual(n['initial_tb'],'1');self.assertEqual(n['load_hours'],'24');self.assertEqual(n['storage_read_gbps'],'16')
 def test_f13_schema_sources_and_partial_apply(self):
  _,s=self.setup_case();p=self.propose_facts(s,self.direct()+[fact('overlap','yes',activity='Factory')]);self.assertEqual(self.apply(p,[0])[0],422)
  f=fact('requests','40','request','1','min');source=self.source(s,'2400 requests in an hour');f.update(source_id=source['id'],quote='2400 requests in an hour');self.assertEqual(self.req('copilot-sessions/'+s['id']+'/proposals','POST',{'facts':[f]})[0],422)
 def test_f14_cards_complete(self):
  caps=self.good('copilot-capabilities');self.assertEqual(len(caps['architecture_library']['cards']),9)
  for c in caps['architecture_library']['cards']:
   for key in ['diagram','description','counterexample','decision_rule','measurement_points']:self.assertTrue(c[key])
 def test_f15_peak_average_and_clock(self):
  _,s=self.setup_case();p=self.propose_facts(s,self.direct()+[fact('requests_average','45000','request','1','day'),fact('requests_peak','6000','request','1','hour')]);self.assertEqual(p['data']['preview']['components'][0]['rate'],'100')
  _,s=self.setup_case();p=self.propose_facts(s,self.direct()+[fact('schedule','batch'),fact('jobs','80000','item'),fact('window_start','22:00'),fact('window_end','06:00')]);self.assertEqual(p['data']['preview']['components'][0]['window'],'8')
 def test_f16_service_target_not_network(self):
  _,s=self.setup_case();p=self.propose_facts(s,self.direct()+[fact('service_target','5','s')]);self.assertEqual(p['data']['preview']['components'][0]['service_seconds'],'5');self.assertNotIn('latency_ms',p['data']['preview']['network'])
 def test_f17_preserve_manual_engagement(self):
  _,s=self.setup_case(True);p=self.propose_facts(s,[fact('population','5000','person',activity='Customer service')]);c=p['data']['preview']['components'][0];self.assertEqual(c['location'],'local');self.assertEqual(c['rate'],'100');self.assertEqual(c['pattern'],'direct')
 def test_f18_route_switch_does_not_double_count(self):
  _,s=self.setup_case();p=self.propose_facts(s,self.direct()+[fact('requests_peak','6000','request','1','hour')]);_,r=self.apply(p)
  p=self.propose_facts(r['session'],[fact('demand_basis','users'),fact('active_users','20','person'),fact('requests_per_user','2','request','1','min')]);c=p['data']['preview']['components'][0];self.assertNotIn('rate',c);self.assertEqual(c['users'],'20')
 def test_f19_raw_unit_guard_and_external_corpus(self):
  _,s=self.setup_case();src=self.source(s,'The external search corpus is 4 TB and the busiest hour has 2400 requests.')
  for f in [fact('initial_data','4','TB'),fact('requests_peak','2400','request','1','min')]:
   f.update(source_id=src['id'],quote=src['data']['text']);self.assertEqual(self.req('copilot-sessions/'+s['id']+'/proposals','POST',{'facts':[f]})[0],422)
 def test_f20_partial_recovery_is_explicit(self):
  _,s=self.setup_case();profile=self.profile(model='partial');self.qualify(profile);self.source(s,'A text classifier has no search or tools.')
  before=len(__import__('test_copilot').Provider.calls);job=self.wait(self.good('copilot-sessions/'+s['id']+'/turns','POST',{'profile_id':profile['id']}));self.assertEqual(job['data']['state'],'succeeded',job)
  self.assertEqual(len(__import__('test_copilot').Provider.calls)-before,2)
  p=self.good('copilot-proposals/'+job['data']['proposal_id']);self.assertTrue(p['data']['partial']);self.assertFalse(p['data']['ready_for_estimate']);self.assertEqual(len(p['data']['rejected_facts']),1);self.assertEqual(self.good('copilot-sessions/'+s['id'])['data']['revision'],1)
 def test_f21_reasoning_profile(self):
  p=self.good('copilot-profiles','POST',dict(name='Reasoning fixture',provider='deepseek',origin=self.origin,path='/v1/chat/completions',model='fixture',secret_env='ANUBIS_AI_KEY_FIXTURE',enabled=True,max_turns=10,max_output_tokens=8192,data_policy='public',reasoning_effort='low'));self.qualify(p)
  body=__import__('test_copilot').Provider.calls[-1][1];self.assertEqual(body['thinking']['type'],'enabled');self.assertEqual(body['reasoning_effort'],'low')
 def test_f22_unit_aliases(self):
  _,s=self.setup_case();p=self.propose_facts(s,self.direct()+[fact('requests_peak','6000','requests','60','minutes')]);self.assertEqual(p['data']['preview']['components'][0]['rate'],'100');f=next(f for f in p['data']['facts'] if f['concept']=='requests_peak');self.assertEqual(f['source_period_unit'],'minutes');self.assertEqual(f['period_unit'],'min')
 def test_f23_adaptation_category_with_unknown_method(self):
  _,s=self.setup_case();p=self.propose_facts(s,[fact('text_model','yes'),fact('lifecycle','adaptation'),fact('training_method',status='unknown')]);self.assertEqual(p['data']['preview']['components'][0]['pattern'],'adaptation')
  p=self.propose_facts(s,[fact('text_model','yes'),fact('training_method',status='unknown')]);self.assertEqual(p['data']['preview']['components'],[])
 def test_f24_factory_scope_and_campaigns(self):
  _,s=self.setup_case();source=self.source(s,'Several customer campaigns can be in different phases at once.')
  f=fact('tenancy','multi',activity='Factory');f.update(source_id=source['id'],quote=source['data']['text']);self.assertEqual(self.req('copilot-sessions/'+s['id']+'/proposals','POST',{'facts':[f]})[0],422)
 def test_f25_alongside_derives_overlap(self):
  _,s=self.setup_case();p=self.propose_facts(s,[fact('actions','yes'),fact('indexing_only','yes',activity='Index'),fact('relationship','alongside',activity='Index')]);self.assertEqual(p['data']['preview']['overlap'],'yes');self.assertEqual(p['data']['preview']['tenancy'],'single')
 def test_f26_hosting_not_placement_or_dedication(self):
  _,s=self.setup_case();src=self.source(s,'We host text endpoints. No interactive work runs during the batch window.')
  for kind,value in [('compute_location','external'),('compute_location','local'),('dedicated','yes')]:
   f=fact(kind,value);f.update(source_id=src['id'],quote=src['data']['text']);self.assertEqual(self.req('copilot-sessions/'+s['id']+'/proposals','POST',{'facts':[f]})[0],422)
 def test_f27_aggregate_is_not_a_third_workload(self):
  _,s=self.setup_case();rows=[fact('text_model','yes',activity='Service'),fact('activity_role','context',activity='Service'),fact('text_model','yes',activity='Premium'),fact('dedicated','yes',activity='Premium'),fact('text_model','yes',activity='Standard'),fact('dedicated','no',activity='Standard')];p=self.propose_facts(s,rows);self.assertEqual(len(p['data']['preview']['components']),2)
  rows=[f for f in rows if f['concept']!='activity_role'];p=self.propose_facts(s,rows);self.assertEqual(sum(c['pattern']=='direct' for c in p['data']['preview']['components']),2);self.assertIn('scope',p['data']['trace'][0]['rule'])
 def test_f28_sole_workload_cannot_be_context(self):
  _,s=self.setup_case();src=self.source(s,'The assistant serves engineers locally.')
  rows=[fact('text_model','yes'),fact('activity_role','context')]
  for f in rows:f.update(source_id=src['id'],quote=src['data']['text'])
  code,result=self.req('copilot-sessions/'+s['id']+'/proposals','POST',{'facts':rows});self.assertEqual(code,422);self.assertEqual(result['error']['code'],'fact_scope')
 def test_f29_compatibility_and_legacy_flag(self):
  c,s=self.setup_case(True);d=self.good('drafts/'+s['data']['draft_id']);w=d['data'];w['characterization']['advanced_modified']=True
  self.assertTrue(self.good('assisted-compatibility','POST',w)['compatible'])
  w['name']='Renamed safely';d=self.good('drafts/'+d['id'],'PATCH',w,extra={'If-Match':str(d['version'])});self.assertFalse(d['data']['characterization'].get('advanced_modified',False));self.assertEqual(d['data']['characterization']['guided_input']['name'],'Renamed safely')
  self.good('copilot-sessions','POST',{'case_id':c['id'],'draft_id':d['id']})
 def test_f30_advanced_preserved_and_conflicts_blocked(self):
  from test_copilot import change
  c,s=self.setup_case(True);d=self.good('drafts/'+s['data']['draft_id']);w=d['data'];w['planning']['compute_efficiency']='0.42';w['stages'][0]['name']='Custom serving stage'
  review=self.good('assisted-compatibility','POST',w);self.assertFalse(review['compatible']);self.assertTrue(review['can_copy']);self.assertTrue(any(x['path']=='/planning/compute_efficiency' for x in review['differences']))
  d=self.good('drafts/'+d['id'],'PATCH',w,extra={'If-Match':str(d['version'])});self.assertTrue(d['data']['characterization']['advanced_modified'])
  s=self.good('copilot-sessions','POST',{'case_id':c['id'],'draft_id':d['id']});p=self.proposal(s,[change('notes','A safe explanation')]);code,r=self.apply(p);self.assertEqual(code,201,r);self.assertEqual(r['draft']['data']['planning']['compute_efficiency'],'0.42');self.assertEqual(r['draft']['data']['notes'],'A safe explanation')
  p=self.proposal(r['session'],[change('sensitivity','20')]);code,r=self.apply(p);self.assertEqual(code,201,r);self.assertEqual(r['draft']['data']['planning']['compute_efficiency'],'0.42');self.assertEqual(r['draft']['data']['stages'][0]['name'],'Custom serving stage')
  before=self.good('drafts/'+d['id']);p=self.proposal(r['session'],[change('components.0.rate','777')]);code,error=self.apply(p);self.assertEqual(code,422);self.assertEqual(error['error']['code'],'assisted_conflict');self.assertIn('/stages/0/name',error['error']['message']);self.assertEqual(before,self.good('drafts/'+d['id']))
 def test_f31_no_guided_description_is_non_destructive(self):
  _,s=self.setup_case(True);w=self.good('drafts/'+s['data']['draft_id'])['data'];del w['characterization'];review=self.good('assisted-compatibility','POST',w);self.assertFalse(review['compatible']);self.assertFalse(review['can_copy'])
 def test_f32_complete_retrieve_and_reopen(self):
  c,s=self.setup_case(True);d=self.good('drafts/'+s['data']['draft_id']);rev=self.good('drafts/'+d['id']+'/freeze','POST',{},extra={'If-Match':str(d['version'])});job=self.wait(self.good('compilations','POST',{'revision_id':rev['id']}));rid=job['data']['result_id'];pr=self.good('neon-projections','POST',{'result_id':rid,'mapping':{'candidate_id':'planning:factory','platform':'HGX_B300','network_fabric':'Spectrum-X'}})
  workflow=lambda:next(x['workflow'] for x in self.good('cases') if x['id']==c['id'])
  self.assertEqual(workflow()['label'],'Handoff prepared · delivery pending')
  body={'result_id':rid,'projection_id':pr['id'],'confirm_delivery':True,'notes':'Delivered for design review','executive_summary':'Saved narrative','narrative_version':'test'}
  current=self.good('cases/'+c['id']);extra={'If-Match':str(current['version'])}
  self.assertEqual(self.req('cases/'+c['id']+'/complete','POST',{**body,'confirm_delivery':False},extra=extra)[0],422)
  other=self.good('cases','POST',{'name':'Other'});self.assertEqual(self.req('cases/'+other['id']+'/complete','POST',body,extra={'If-Match':str(other['version'])})[0],422)
  edited=copy.deepcopy(d['data']);edited['notes']='New edits';self.good('drafts/'+d['id'],'PATCH',edited,extra={'If-Match':str(d['version'])})
  self.assertTrue(workflow()['stale_result']);self.assertEqual(workflow()['phase'],3)
  code,error=self.req('cases/'+c['id']+'/complete','POST',body,extra=extra);self.assertEqual(code,422);self.assertEqual(error['error']['code'],'stale_completion')
  saved=self.good('cases/'+c['id']+'/complete','POST',{**body,'acknowledge_stale':True},extra=extra);snapshot=saved['completion'];self.assertEqual(saved['case']['data']['status'],'completed');self.assertTrue(snapshot['data']['earlier_calculation_acknowledged']);self.assertEqual(snapshot['data']['projection_snapshot'],pr['data'])
  self.assertEqual(workflow()['phase'],5)
  self.assertEqual(self.good('cases/'+c['id']+'/completions'),[snapshot]);self.assertEqual(self.good('cases/'+c['id']+'/saved-projections')[0]['id'],pr['id']);self.assertEqual(self.req('cases/'+c['id']+'/completions',actor='bob')[0],403)
  self.assertEqual(self.req('cases/'+c['id']+'/reopen','POST',{},extra=extra)[0],422)
  reopened=self.good('cases/'+c['id']+'/reopen','POST',{'notes':'New revision'},extra={'If-Match':str(saved['case']['version'])});self.assertEqual(reopened['data']['status'],'active');self.assertEqual(self.good('cases/'+c['id']+'/completions'),[snapshot])
  from test_copilot import change
  resumed=self.good('copilot-sessions/'+reopened['data']['copilot_resume_session_id']);self.assertEqual(resumed['data']['turns'],0);self.assertEqual(resumed['data']['draft_version'],self.good('drafts/'+d['id'])['version']);proposal=self.proposal(resumed,[change('notes','Reopened revision')]);self.assertEqual(self.apply(proposal)[0],201);self.assertEqual(self.good('cases/'+c['id']+'/completions'),[snapshot])
  second=self.good('cases/'+c['id']+'/complete','POST',{**body,'acknowledge_stale':True,'notes':'Second delivery'},extra={'If-Match':str(reopened['version'])});self.assertEqual(second['completion']['data']['previous_completion_id'],snapshot['id']);self.assertIn(snapshot,self.good('cases/'+c['id']+'/completions'))
 def test_f33_delete_restore_and_scope(self):
  c,s=self.setup_case(True);path='cases/'+c['id'];extra={'If-Match':str(c['version'])}
  self.assertEqual(self.req(path+'/delete','POST',{'confirm':False},extra=extra)[0],422)
  self.assertEqual(self.req(path+'/delete','POST',{'confirm':True},extra=extra,actor='bob')[0],403)
  deleted=self.good(path+'/delete','POST',{'confirm':True},extra=extra);self.assertNotIn(c['id'],[x['id'] for x in self.good('cases')]);self.assertIn(c['id'],[x['id'] for x in self.good('cases/trash')]);self.assertEqual(self.req('copilot-sessions','POST',{'case_id':c['id']})[1]['error']['code'],'deleted_engagement')
  self.assertEqual(self.req(path+'/restore','POST',{'confirm':True},extra=extra)[0],422)
  self.good(path+'/restore','POST',{'confirm':True},extra={'If-Match':str(deleted['version'])});self.assertIn(c['id'],[x['id'] for x in self.good('cases')]);self.assertEqual(self.good('copilot-sessions/'+s['id'])['id'],s['id'])
 def test_f34_specialist_closure_without_result(self):
  c,s=self.setup_case();p=self.propose_facts(s,[fact('simulation','yes'),fact('workload_note','Solver and mesh measurements are needed')]);review=self.good('cases/'+c['id']+'/closure-review');self.assertEqual(review['state'],'specialist_required');self.assertIn('unaccepted',review['basis']);self.assertTrue(review['offer_status_closure'])
  body={'review_digest':review['review_digest'],'notes':'Specialist solver measurements unavailable. Refer for benchmarking.','confirm':True};extra={'If-Match':str(c['version'])}
  self.assertEqual(self.req('cases/'+c['id']+'/close-with-report','POST',{**body,'confirm':False},extra=extra)[0],422)
  self.source(s,'More information arrived after the preview.')
  code,error=self.req('cases/'+c['id']+'/close-with-report','POST',body,extra=extra);self.assertEqual(code,422);self.assertEqual(error['error']['code'],'stale_closure_review')
  review=self.good('cases/'+c['id']+'/closure-review');body['review_digest']=review['review_digest'];saved=self.good('cases/'+c['id']+'/close-with-report','POST',body,extra=extra);snapshot=saved['completion'];self.assertEqual(saved['case']['data']['completion_outcome'],'concluded_without_handoff');self.assertIsNone(snapshot['data']['assessment']['snapshot']['result']);self.assertIn('No GPU count is inferred',snapshot['data']['report_text']);self.assertIn('No accepted fact ledger',snapshot['data']['report_text']);self.assertNotIn('projection_snapshot',snapshot['data']);self.assertEqual(snapshot['data']['assessment']['snapshot']['proposals'][0]['data']['state'],'proposed')
  self.assertEqual(next(x for x in self.good('cases') if x['id']==c['id'])['workflow']['label'],'Closed · final status report');self.assertEqual(self.good('cases/'+c['id']+'/completions'),[snapshot]);self.assertEqual(self.req('cases/'+c['id']+'/closure-review',actor='bob')[0],403)
  self.good('cases/'+c['id']+'/reopen','POST',{},extra={'If-Match':str(saved['case']['version'])});self.assertEqual(self.good('cases/'+c['id']+'/completions'),[snapshot])
 def test_f35_specialist_case_phase(self):
  c,s=self.setup_case();p=self.propose_facts(s,[fact('simulation','yes')]);self.assertEqual(self.apply(p)[0],201)
  row=next(x for x in self.good('cases') if x['id']==c['id']);self.assertIn('Specialist scope',row['workflow']['label']);self.assertIn('status report',row['workflow']['next_action'])
# Do not duplicate the parent test suite in this module.
for name in list(Copilot.__dict__):
 if name.startswith('test_'):setattr(Interpretation,name,None)
if __name__=='__main__':unittest.main(verbosity=2)
