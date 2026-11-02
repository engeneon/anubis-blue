import ts from 'typescript';
import fs from 'node:fs';
for(const path of ['ui/src/app.ts','ui/src/guided.ts','ui/src/help.ts','ui/src/discovery.ts']){
 const src=fs.readFileSync(path,'utf8'),ast=ts.createSourceFile(path,src,ts.ScriptTarget.Latest,true);let edits=[];
 function visit(n){if(ts.isStringLiteral(n)||ts.isNoSubstitutionTemplateLiteral(n)||[ts.SyntaxKind.TemplateHead,ts.SyntaxKind.TemplateMiddle,ts.SyntaxKind.TemplateTail].includes(n.kind)){
 const a=n.getStart(ast),b=n.end,raw=src.slice(a,b),updated=raw.replace(/; ([a-z])/g,(_,c)=>'. '+c.toUpperCase()).replaceAll('; ','. ');if(updated!==raw)edits.push([a,b,updated]);}ts.forEachChild(n,visit);}visit(ast);
 let out=src;for(const[a,b,v]of edits.sort((a,b)=>b[0]-a[0]))out=out.slice(0,a)+v+out.slice(b);fs.writeFileSync(path,out);
}
