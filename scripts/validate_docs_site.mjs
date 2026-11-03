import {chromium} from 'playwright';
import {createServer} from 'node:http';
import {readFileSync,existsSync,readdirSync,mkdirSync,writeFileSync,statSync} from 'node:fs';
import {resolve,extname} from 'node:path';
import assert from 'node:assert/strict';
const root=resolve('_site'),qa=resolve('test-results/docs-site');mkdirSync(qa,{recursive:true});
const mime={'.html':'text/html','.css':'text/css','.png':'image/png','.pdf':'application/pdf','.docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document'};
const server=createServer((req,res)=>{const p=resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));const file=p===root?resolve(root,'index.html'):p;if(!file.startsWith(root+'/')||!existsSync(file)||!statSync(file).isFile()){res.writeHead(404);res.end();return;}res.setHeader('Content-Type',mime[extname(file)]||'text/plain');res.end(readFileSync(file));});
await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
const browser=await chromium.launch({headless:true,executablePath:process.env.ANUBIS_CHROMIUM_PATH||chromium.executablePath()});const checks=[];
try{for(const width of [390,1440]){const page=await browser.newPage({viewport:{width,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 for(const name of readdirSync(root).filter(n=>n.endsWith('.html'))){await page.goto(base+'/'+name);await page.getByRole('heading',{level:1}).waitFor();assert.equal(await page.locator('h1').count(),1);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Horizontal page overflow: '+width+' '+name);await page.evaluate(async()=>{for(const img of document.images){img.loading='eager';await img.decode();}});assert.equal(errors.length,0,errors.join('\n'));checks.push({page:name,width,status:'passed'});
  if(['index.html','getting-started.html','s13.html'].includes(name)){if(name==='s13.html'){await page.locator('#manual').scrollIntoViewIfNeeded();}await page.screenshot({path:qa+'/'+width+'-'+name+'.png'});}
 }
 await page.close();}
 for(const file of readdirSync(resolve(root,'downloads')).filter(f=>/\.(pdf|docx)$/.test(f))){const r=await fetch(base+'/downloads/'+file);assert.equal(r.status,200);const bytes=Buffer.from(await r.arrayBuffer());assert(bytes.subarray(0,file.endsWith('.pdf')?4:2).toString()=== (file.endsWith('.pdf')?'%PDF':'PK'));checks.push({download:file,status:'passed',content_type:r.headers.get('content-type')});}
 writeFileSync(resolve(qa,'validation.json'),JSON.stringify({checks,passed:true},null,2)+'\n');console.log('PASS:',checks.length,'page-layout and document-download checks');
}finally{await browser.close();await new Promise(r=>server.close(r));}
