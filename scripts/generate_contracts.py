#!/usr/bin/env python3
"""Versioned language-neutral API inventory; runtime remains authoritative for cross-field rules."""
import json,pathlib
root=pathlib.Path(__file__).resolve().parents[1];out=root/'contracts';out.mkdir(exist_ok=True)
def write(name,value): (out/name).write_text(json.dumps(value,indent=2)+'\n')
obs={'type':'object','additionalProperties':False,'required':['state'],'properties':{'state':{'enum':['known','estimated','assumed','unknown']},'value':{'type':'string','pattern':r'^-?[0-9]+(\.[0-9]+)?$'},'unit':{'type':'string'},'origin':{'enum':['customer','measurement','template','agent']},'source':{'type':'string','minLength':1},'accepted':{'type':'boolean'},'active':{'type':'boolean'},'reason':{'type':'string'}},'allOf':[{'if':{'properties':{'state':{'const':'unknown'}}},'then':{'not':{'required':['value']}},'else':{'required':['value','unit','origin','source']}}]}
write('observation.schema.json',{'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:anubis:observation:1.0',**obs})
workload={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:anubis:workload:1.0','type':'object','additionalProperties':False,'required':['schema_version','name','stages','scenarios'],'properties':{'schema_version':{'const':'1.0'},'name':{'type':'string','minLength':1},'notes':{'type':'string'},'tenancy':{'enum':['single','multi']},'objective':{'const':'gpu_count'},'candidate_limit':{'type':'integer','minimum':0,'maximum':4096},'stages':{'type':'array','maxItems':128,'items':{'type':'object','required':['id','type','observations'],'properties':{'id':{'type':'string','minLength':1,'maxLength':80},'name':{'type':'string'},'type':{'type':'string'},'observations':{'type':'object','additionalProperties':obs}}}},'scenarios':{'type':'array','minItems':1,'maxItems':32,'items':{'type':'object','required':['id'],'properties':{'id':{'type':'string'},'name':{'type':'string'},'active_stages':{'type':'array','items':{'type':'string'},'uniqueItems':True},'multiplier':{'type':'string'},'failed_nodes':{'type':'integer','minimum':0,'maximum':64},'cache_state':{'type':'string'},'notes':{'type':'string'}}}},'edges':{'type':'array','items':{'type':'object','additionalProperties':False,'required':['from','to'],'properties':{'from':{'type':'string'},'to':{'type':'string'}}}}}}
planning_example=json.loads((root/'tests/fixtures/meridian-planning.json').read_text())
def planning_schema(example):
 props={k:{'type':'boolean' if isinstance(v,bool) else 'integer' if isinstance(v,int) else 'string'} for k,v in example.items()}
 return {'type':'object','additionalProperties':False,'properties':props,'required':list(props)}
workload['properties']['planning']=planning_schema(planning_example['planning'])
workload['properties']['stages']['items']['properties']['planning']=planning_schema(planning_example['stages'][0]['planning'])
workload['properties']['characterization']={'type':'object'}
write('workload.schema.json',workload)
rows=[]
def route(method,path,scope,description,body=None,status=200):rows.append(dict(method=method,path=path,scope=scope,description=description,body=body,status=status))
for path,desc in [('capabilities','Declared support and bounds'),('component-descriptors','Registered intake controls'),('me','Effective identity'),('stories','Fictional reference workloads'),('openapi','Versioned API inventory'),('integration-capabilities','Configured integration scope')]:route('GET',path,'authenticated',desc)
route('POST','session','authenticated','Set local HttpOnly session',{},200);route('POST','logout','authenticated','Clear session',{},200)
route('GET','cases','member','List authorized engagements');route('POST','cases','writer','Create engagement',{'name':{'type':'string'}},201)
route('GET','cases/{id}','member','Read engagement');route('PATCH','cases/{id}','writer; owner for membership/budget','Optimistic update (If-Match required)',{'name':{'type':'string'},'archived':{'type':'boolean'},'members':{'type':'array','items':{'type':'string'}},'agent_compile_limit':{'type':'integer','minimum':0,'maximum':100},'agent_proposal_limit':{'type':'integer','minimum':0,'maximum':100}})
for suffix in ['drafts','runs','audit','proposals','completions','saved-projections']:route('GET','cases/{id}/'+suffix,'member','List case '+suffix)
route('GET','cases/trash','member','List recoverably deleted engagements')
for op in ['delete','restore']:route('POST','cases/{id}/'+op,'owner','Move engagement to Trash or restore. If-Match and explicit confirmation required.',{'confirm':{'type':'boolean'}})
route('GET','cases/{id}/closure-review','member','Assess current limitations and preview a deterministic final status report without closing')
route('POST','cases/{id}/close-with-report','writer, not agent','Conclude without a design handoff and preserve a final status report. If-Match and matching review digest required.',{'review_digest':{'type':'string'},'notes':{'type':'string'},'confirm':{'type':'boolean'}},201)
route('POST','cases/{id}/complete','writer, not agent','Confirm requirements delivered and preserve selected result/projection snapshots. If-Match required.',{'result_id':{'type':'string'},'projection_id':{'type':'string'},'notes':{'type':'string'},'confirm_delivery':{'type':'boolean'},'acknowledge_stale':{'type':'boolean'},'executive_summary':{'type':'string'},'narrative_version':{'type':'string'}},201)
route('POST','cases/{id}/reopen','writer, not agent','Reopen for revisions without changing completed snapshots. If-Match required.',{'notes':{'type':'string'}})
route('POST','cases/{id}/drafts','writer','Create structured draft',{'$ref':'workload.schema.json'},201)
route('GET','drafts/{id}','member','Read editable draft');route('PATCH','drafts/{id}','writer','Replace draft with If-Match version',{'$ref':'workload.schema.json'})
for op in ['validate','freeze']:route('POST','drafts/{id}/'+op,'writer',op+' effective workload; freeze requires If-Match',{},201 if op=='freeze' else 200)
for path in ['packs','activations','qualification-protocols','qualification-reports']:route('GET',path,'authenticated','List '+path);route('GET',path+'/{id}','authenticated','Read '+path)
route('POST','packs','curator/admin','Import immutable version; executable extensions forbidden',None,201)
route('POST','packs/{id}/activate','approver/admin','Resolve exact dependency lock; production requires independent qualification',{'channel':{'enum':['demonstration','production']},'qualification_report_id':{'type':'string'}},201)
route('POST','activations/{id}/withdraw','approver/admin','Withdraw for future jobs; retain history',{})
route('GET','activations/{id}/impact','member','List authorized dependent runs')
route('POST','qualification-protocols','curator/admin','Freeze thresholds and calibration split',None,201)
route('POST','qualification-runs','curator/admin','Evaluate dataset against predeclared protocol',{'protocol_id':{'type':'string'},'dataset':{'type':'object'}},201)
route('POST','observation-proposals','writer/agent with proposal budget','Store unaccepted assumed agent observations; no draft mutation',{'draft_id':{'type':'string'},'rows':{'type':'array','maxItems':100}},201)
route('POST','proposal-reviews','human writer','Review explicit rows and apply against the original draft version',{'proposal_id':{'type':'string'},'accept_rows':{'type':'array','items':{'type':'integer'}},'rationale':{'type':'string'}},201)
route('POST','import-previews','writer','Validate typed rows with per-row rejection reasons',{'draft_id':{'type':'string'},'rows':{'type':'array','maxItems':2000,'items':{'type':'object'}}},201)
route('POST','import-commits','writer','Commit reviewed rows only against original draft version',{'preview_id':{'type':'string'},'accept_partial':{'type':'boolean'}})
route('POST','compilations','writer/agent with case budget','Freeze job inputs and enqueue',{'revision_id':{'type':'string'},'activation_id':{'type':'string'}},202)
route('GET','jobs/{id}','member','Poll job; job success is separate from engineering feasibility');route('POST','jobs/{id}/cancel','writer','Cancellation fenced against committed publication',{})
for path in ['results','revisions','projections','reports','assessments','decisions']:route('GET',path+'/{id}','member','Read immutable scoped '+path)
route('POST','reports','writer','Create frozen dossier manifest',{'result_id':{'type':'string'}},201)
route('POST','recommendation-decisions','writer; architect/admin for finalization','Record selection without changing engineering status',{'result_id':{'type':'string'},'candidate_id':{'type':'string'},'state':{'enum':['selected','finalized']},'rationale':{'type':'string'}},201)
route('POST','comparisons','member/agent','Compare immutable results',{'left_id':{'type':'string'},'right_id':{'type':'string'}})
route('POST','neon-projections','writer','Create allowlisted manual handoff and separate mapping ledger',{'result_id':{'type':'string'},'mapping':{'type':'object'}},201)
route('POST','external-result-imports','writer','Retain downstream design tool authority; unresolved semantics stay unverifiable',{'projection_id':{'type':'string'},'external_result':{'type':'object'}},201)
route('POST','neon-submissions','writer; configured local target','Experimental stateless submission; 409 when target unconfigured',{'projection_id':{'type':'string'},'confirm_experimental_submission':{'type':'boolean'}},202)
route('POST','jobs/{id}/reconcile','writer','Import evidence to reconcile uncertain external outcome',{'external_result':{'type':'object'},'source':{'type':'string'}})
route('POST','admin/backup','admin','Consistent SQLite snapshot to server-controlled backup directory',{},201)
route('GET','planning-catalog','member','Read versioned planning hardware, model assumptions and supported downstream design tool anchors')
route('GET','guided-catalog','member','Read versioned application patterns and accepted-default profiles')
route('POST','guided-readiness','authenticated','Return deterministic minimum GPU input requirements without persistence',None)
route('POST','copilot-explanations','writer','Save a deterministic explanation or queue a read-only model explanation',{'result_id':{'type':'string'},'projection_id':{'type':'string'},'profile_id':{'type':'string'},'classification':{'type':'string','enum':['public','corporate']}},201)
route('GET','copilot-explanations/{id}','member','Read a saved explanation and exact result provenance')
route('GET','copilot-explanations/{result_id}/history','member','List explanations for an exact saved result')
route('POST','guided-workloads','writer','Transform architecture-led intake into a validated workload without persistence',{'name':{'type':'string'},'components':{'type':'array','minItems':1,'maxItems':16,'items':{'type':'object'}},'accepted':{'type':'boolean'},'overlap':{'enum':['yes','no','unknown']},'tenancy':{'enum':['single','multi']},'architecture':{'type':'string'},'sensitivity':{'type':'string'},'notes':{'type':'string'}})
# Optional copilot API. Runtime owns field-level and source validation.
route('POST','assisted-compatibility','writer','Inspect lossless assisted compatibility and preview a separate assisted copy without changing the supplied workload')
route('GET','copilot-capabilities','authenticated','Copilot bounds, versioned fact schema, architecture cards and disabled status')
route('GET','copilot-profiles','authenticated','List configured model and MCP connections without credentials')
route('POST','copilot-profiles','admin','Create an endpoint-policy-checked profile using backend secret references',None,201)
for op in ['test','disable']:route('POST','copilot-profiles/{id}/'+op,'admin','Test capability or disable connection',{},202 if op=='test' else 200)
route('POST','copilot-sessions','writer','Create a case-scoped assistant session',{'case_id':{'type':'string'},'draft_id':{'type':'string'},'classification':{'enum':['public','corporate']}},201)
route('GET','copilot-sessions/{id}','member','Read accepted session state')
route('GET','copilot-sessions/{id}/history','member','Read scoped sources, proposals and job outcomes')
for op,status in [('sources',201),('proposals',201),('turns',202),('mcp-import',202),('fork',201)]:route('POST','copilot-sessions/{id}/'+op,'writer; proposals also budgeted agent','Controlled assistant '+op,None,status)
route('GET','copilot-proposals/{id}','member','Read immutable proposed values and review status')
route('POST','copilot-proposals/{id}/apply','human writer','Apply reviewed fields with revision checks. Fact proposals are accepted atomically with their fact ledger',{'selected':{'type':'array','items':{'type':'integer'}},'accept_assumptions':{'const':True}},201)
route('POST','copilot-proposals/{id}/reject','human writer','Reject pending proposal',{})
route('GET','copilot-context/{id}','member','Read case-scoped sessions and approved catalogue context')
route('GET','copilot-facts/{id}','member','Read engine-owned facts from an immutable result')
paths={}
for r in rows:
 op={'operationId':r['method'].lower()+'_'+r['path'].replace('/','_').replace('{id}','by_id').replace('-','_'),'summary':r['description'],'x-authorization':r['scope'],'security':[{'bearerAuth':[]}], 'responses':{str(r['status']):{'description':r['description']},'401':{'description':'Authentication required'},'403':{'description':'Access denied'},'409':{'description':'Conflict or target unavailable'},'422':{'description':'Contract/engineering input validation error'},'428':{'description':'If-Match required'}},'parameters':[]}
 if '{id}' in r['path']:op['parameters'].append({'name':'id','in':'path','required':True,'schema':{'type':'string'}})
 if r['method']!='GET':
  body=r['body'];schema=body if body and '$ref' in body else {'type':'object',**({'properties':body} if body is not None else {})}
  op['requestBody']={'required':True,'content':{'application/json':{'schema':schema}}}
  op['parameters'].append({'name':'Idempotency-Key','in':'header','schema':{'type':'string'}})
 if r['method']=='PATCH' or r['path'].endswith('/freeze'):op['parameters'].append({'name':'If-Match','in':'header','required':True,'schema':{'type':'string','pattern':'^[1-9][0-9]*$'}})
 paths.setdefault('/api/v1/'+r['path'],{})[r['method'].lower()]=op
write('openapi.json',{'openapi':'3.1.0','info':{'title':'Anubis local development API','version':'0.1.0','description':'Runtime validates detailed cross-field semantics. Local deployment only; external integration remains unqualified.'},'servers':[{'url':'http://127.0.0.1:8787'}],'paths':paths,'components':{'securitySchemes':{'bearerAuth':{'type':'http','scheme':'bearer'}}}})
write('operations.json',rows)
