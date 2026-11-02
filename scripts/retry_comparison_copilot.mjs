import {chromium} from '/Users/trai/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import {readFileSync,writeFileSync,existsSync,mkdirSync} from 'node:fs';
import assert from 'node:assert/strict';
const out='deliverables/manual-copilot-comparison-2026-11-03';mkdirSync(out,{recursive:true});
const token=JSON.parse(readFileSync('.anubis/identities.json','utf8')).find(x=>x.id==='local-owner').token;
const base='http://127.0.0.1:8787';const headers={Authorization:'Bearer '+token};
const get=async path=>{const r=await fetch(base+'/api/v1/'+path,{headers});if(!r.ok)throw Error(path+' '+r.status);return r.json();};
const profiles=await get('copilot-profiles');const profile=profiles.find(x=>x.data.enabled&&x.data.provider==='deepseek'&&x.data.name.includes('low reasoning'));assert(profile);
const evidence={date:'2026-11-03',url:base,provider:profile.data.provider,model:profile.data.model,profile_name:profile.data.name,errors:[],steps:[],started:new Date().toISOString()};
const story='Cedar Engineering operates a document assistant named Engineering answers for one organisation. The answer model runs inside this AI Factory and retrieves passages from an existing search and indexing service outside this AI Factory. The outside service indexes a 4 TB document corpus. That corpus stays outside this AI Factory. No local corpus copy and no initial corpus transfer are requested. The busiest hour has 2,400 questions. Use the busiest-hour rate for planning. Explicitly assume dense8b, one model call per question, 2,000 input tokens and 500 output tokens per call. This is one activity, operating under the overlapping-demand planning option, without reserved dedicated capacity. No response-time target, local retained-data quantity, data-growth quantity, bulk-transfer rates, storage throughput or east-west payload measurement has been supplied. Keep unspecified quantities unknown. Retain the existing B300 Spectrum-X Enterprise deployment profile and 30 percent sensitivity envelope. Do not infer GPU counts in the interpretation. Use the deterministic sizing calculation after fact review.';
writeFileSync(out+'/scenario.txt',story+'\n');
const browser=await chromium.launch({headless:true,executablePath:'/Users/trai/Library/Caches/ms-playwright/chromium-1248/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'});
const page=await browser.newPage({viewport:{width:1440,height:1080}});page.setDefaultTimeout(20000);page.on('pageerror',e=>evidence.errors.push(e.message));
const click=async name=>page.getByRole('button',{name,exact:true}).click();const fill=async(name,v)=>page.getByLabel(name,{exact:true}).fill(v);
const shot=async file=>page.screenshot({path:out+'/'+file+'.png',fullPage:true});
const download=async(name,file)=>{const [d]=await Promise.all([page.waitForEvent('download'),click(name)]);await d.saveAs(out+'/'+file);return JSON.parse(readFileSync(out+'/'+file,'utf8'));};
const finish=async mode=>{
 await page.getByRole('heading',{name:'Workload analysis',exact:true}).waitFor();
 const r=await download('Export result',mode+'-result.json');await shot(mode+'-results');
 await click('Continue to Design handoff');await click('Prepare projection');await page.getByRole('heading',{name:'AI Factory design executive summary',exact:true}).waitFor();
 await download('Download design intake',mode+'-intake.json');await download('Download companion specification',mode+'-projection.json');await shot(mode+'-handoff');
 await fill('Completion notes','Manual versus live Copilot comparison. Fictional Cedar workload. Requirements preserved for comparison.');await page.getByLabel('I confirm that these selected requirements are delivered.',{exact:true}).check();await click('Complete engagement');await page.getByRole('button',{name:'Download complete engagement record',exact:true}).waitFor();
 const completion=await download('Download complete engagement record',mode+'-completion.json');assert.deepEqual(completion.data.result_snapshot.result,r);
 evidence[mode]={case_id:completion.case_id,result_id:completion.data.result_id,projection_id:completion.data.projection_id,completed:true};evidence.steps.push(mode+' completed');console.log(mode+' calculated, projected and completed.');
};
try{
 await page.goto(base);await fill('Access token',token);await click('Open workspace');
 const manual=JSON.parse(readFileSync(out+'/manual-completion.json','utf8'));evidence.manual={case_id:manual.case_id,result_id:manual.data.result_id,projection_id:manual.data.projection_id,completed:true};
 await page.locator('.engagement-row').filter({hasText:'Cedar comparison 03 Nov — assisted'}).last().getByRole('button',{name:'View engagement',exact:true}).click();await click('Consultant Copilot');
 const session={id:'copilot_session_87b43360ddf9e3ac0b3c37416fa4f104'};evidence.session_id=session.id;
 evidence.previous_attempt={job_id:'job_43e3f3616615a709d3b2bee225db1aad',state:'failed',code:'provider_unavailable'};
 await page.getByLabel('Model connection',{exact:true}).selectOption(profile.id);await fill('What should we know about the workload?',story);const askStart=Date.now();const started=page.waitForResponse(r=>r.url().endsWith('/turns')&&r.request().method()==='POST');await click('Ask copilot');const job=await (await started).json();evidence.live_job_id=job.id;console.log('Live DeepSeek interpretation requested.');
 for(let i=0;i<180;i++){const j=await get('jobs/'+job.id);if(j.data.state==='failed')throw Error(JSON.stringify(j.data.error));if(j.data.state==='succeeded')break;await new Promise(r=>setTimeout(r,1000));} await page.getByRole('heading',{name:'Input proposal — proposed',exact:true}).waitFor({timeout:15000});evidence.live_turn_seconds=(Date.now()-askStart)/1000;
 const history=await get('copilot-sessions/'+session.id+'/history');writeFileSync(out+'/live-proposal.json',JSON.stringify({sources:history.sources,proposals:history.proposals,jobs:history.jobs.map(j=>({id:j.id,state:j.data.state,error:j.data.error,attempts:j.data.attempts}))},null,2));await shot('assisted-proposal');writeFileSync(out+'/proposal-screen.txt',await page.locator('main').innerText());console.log('Proposal saved. Awaiting factual review before acceptance.');
 for(let i=0;!existsSync(out+'/review-approved.json');i++){if(i>900)throw Error('Factual review not completed');await new Promise(r=>setTimeout(r,1000));}
 evidence.review=JSON.parse(readFileSync(out+'/review-approved.json','utf8'));
 await page.getByLabel('I reviewed the selected values and accept the planning assumptions.',{exact:true}).check();await click('Apply selected');await click('Review and calculate GPU estimate');await shot('assisted-review');await page.getByLabel('Use these planning assumptions',{exact:true}).check();await click('Calculate estimate');await finish('assisted');
 evidence.passed=true;
}catch(e){evidence.passed=false;evidence.error=String(e);await shot('failure');writeFileSync(out+'/failure-screen.txt',await page.locator('main').innerText().catch(()=>''));throw e;}finally{evidence.finished=new Date().toISOString();writeFileSync(out+'/execution-retry.json',JSON.stringify(evidence,null,2));await browser.close();}
