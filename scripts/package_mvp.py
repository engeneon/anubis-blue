"""Package the local MVP without credentials, customer databases or build caches."""
import hashlib,json,pathlib,zipfile
root=pathlib.Path(__file__).resolve().parents[1]
out=root/'deliverables/anubis-mvp-1.0';out.mkdir(parents=True,exist_ok=True)
files=[]
for directory in ['src','third_party','ui/src','ui/dist','ui/assets','contracts','knowledge','deploy','docs','tests','scripts','dependency-locks','mcp','implementation/mvp-1.0']:
 for p in (root/directory).rglob('*'):
  if p.is_file() and not p.is_symlink() and not any(part.startswith('.') or part in ['__pycache__','node_modules','video-build'] for part in p.relative_to(root).parts) and p.suffix not in ['.pyc','.sqlite','.db','.log']:
   files.append(p)
for name in ['CMakeLists.txt','CMakePresets.json','README.md','package.json','package-lock.json','playwright.config.ts','ui/tsconfig.json','build/anubis','implementation/copilot/random-scenario.json']:
 files.append(root/name)
files=sorted(set(files))
manifest={'release':'Anubis MVP 1.0','profile':'local macOS arm64 binary plus buildable source','qualification':'Analytical planning. No empirical hardware or live provider qualification claimed.','files':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
manifest_text=json.dumps(manifest,indent=2)+'\n'
(out/'manifest.json').write_text(manifest_text)
archive=out/'Anubis_MVP_1.0.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,'anubis-mvp-1.0/'+str(p.relative_to(root)))
 z.writestr('anubis-mvp-1.0/RELEASE-MANIFEST.json',manifest_text)
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for name,digest in manifest['files'].items():assert hashlib.sha256(z.read('anubis-mvp-1.0/'+name)).hexdigest()==digest
 assert not any('/.env' in n or '/.anubis/' in n or '/.git/' in n or n.endswith('.sqlite') for n in z.namelist())
checksum=hashlib.sha256(archive.read_bytes()).hexdigest()
(out/'SHA256SUMS.txt').write_text(checksum+'  '+archive.name+'\n')
print(json.dumps({'archive':str(archive),'files':len(files),'bytes':archive.stat().st_size,'sha256':checksum}))
