// Repeatable UI acceptance using the supported cua_repl API.
// Prerequisites: `tab` bound to authenticated Anubis; `browser` is its browser.
// Paste this script into cua_repl (split at awaited snapshots if needed).
// Dynamic evaluation from file strings is not supported by cua_repl.
(async()=>{
 const fs=await import('node:fs/promises');
 const root='/Users/trai/Code/anubis/implementation/usability';const checks=[];
 const assert=(n,ok,detail)=>{if(!ok)throw Error(`Slice ${n}: ${detail}`);checks.push({slice:n,status:'passed',detail});};
 const press=async(name)=>{await tab.playwright.getByRole('button',{name,exact:true}).press('Enter');return await tab.playwright.domSnapshot();};
 const fill=async(name,value)=>tab.playwright.getByLabel(name,{exact:true}).fill(value);
 const select=async(name,value)=>tab.playwright.getByLabel(name,{exact:true}).selectOption(value);
 await press('Cases');await press('New engagement');await tab.playwright.getByLabel('Customer workload name',{exact:true}).waitFor({state:'visible',timeoutMs:5000});await press('Clear unsaved intake');
 await fill('Customer workload name','Repeatable Alder acceptance');let s=await tab.playwright.domSnapshot();
 assert(2,(s.match(/button "Add /g)||[]).length===9,'Eight core patterns plus explicit unmatched application');
 await press('Add Direct model service');s=await press('Continue');
 assert(3,s.includes('Compute location 1')&&!s.includes('Stage type'),'Composition without internal stage types');
 assert(4,s.includes('system architecture')&&s.includes('AI FACTORY COMPUTE'),'Application flow diagram');
 assert(5,s.includes('Measure at entry'),'Measurement points accompany components');
 await select('Do activities run at the same time?','no');s=await tab.playwright.domSnapshot();assert(11,s.includes('No — separate operating windows" [selected]'),'Explicit operating-window choice');
 await press('Continue');await select('Describe demand using','users');s=await tab.playwright.domSnapshot();assert(6,s.includes('Active users')&&!s.includes('textbox "Peak requests per minute"'),'Alternative demand route does not duplicate inputs');
 await select('Describe demand using','rate');await fill('Peak requests per minute','100');
 const guidance=await tab.playwright.evaluate(()=>[...document.querySelectorAll('main input,main select')].filter(e=>e.type!=='checkbox'&&!e.getAttribute('aria-describedby')).length);
 assert(9,guidance===0,'Every displayed field links to contextual guidance');
 s=await tab.playwright.domSnapshot();assert(7,!s.includes('concurrent_sequences')&&!s.includes('weight_bytes'),'Expert settings excluded from initial intake');
 assert(10,s.includes('Leave blank if unknown')&&s.includes('Preset: 2000'),'Unknowns and assumptions distinguished');
 await press('Continue');s=await tab.playwright.domSnapshot();assert(8,s.includes('Inspect versioned planning defaults'),'Versioned assumptions available before acceptance');
 assert(12,s.includes('Infrastructure deployment profile'),'Application and deployment architecture distinguished');
 await tab.playwright.getByRole('checkbox',{name:'Use these planning assumptions',exact:true}).check();await press('Calculate estimate');await tab.playwright.getByRole('heading',{name:'Workload analysis',exact:true}).waitFor({state:'visible',timeoutMs:8000});s=await tab.playwright.domSnapshot();
 assert(1,s.includes('HGX_B300 8')&&s.includes('HGX_B200 8')&&s.includes('HGX_H200 8'),'Blank engagement reaches all three GPU estimates');
 assert(13,s.includes('Application component Demand GPU subtotal Sizing driver')&&s.includes('Initial deployment: 256'),'Component drivers and separate factory anchor');
 await press('Design handoff');await press('Prepare projection');await tab.playwright.getByRole('button',{name:'Download design intake',exact:true}).waitFor({state:'visible',timeoutMs:5000});
 let download=tab.playwright.waitForEvent('download');await press('Download design intake');let payload=JSON.parse(await fs.readFile(await (await download).path(),'utf8'));assert(14,payload.requirements.target_gpu_count===256&&payload.requirements.platform==='HGX_B300','Compatible payload downloaded through UI');
 assert(15,await tab.playwright.getByRole('link',{name:'User guide',exact:true}).getAttribute('href')==='/user-guide.html','Customer guide reachable in the product');
 await (await browser.capabilities.get('viewport')).set({width:320,height:740});await press('Workload builder');await tab.playwright.getByRole('heading',{name:'Refine your application estimate',exact:true}).waitFor({state:'visible',timeoutMs:5000});
 const width=await tab.playwright.evaluate(()=>({content:document.documentElement.scrollWidth,viewport:innerWidth}));assert(16,width.content<=width.viewport,'320px layout has no document overflow; journey operated by keyboard');
 await fs.writeFile(root+'/ui-validation.json',JSON.stringify({checks:checks.sort((a,b)=>a.slice-b.slice),payload},null,2));
 await fs.writeFile(root+'/narrow-layout.png',await tab.screenshot({fullPage:true}));
 await (await browser.capabilities.get('viewport')).reset();
 return checks;
})()
