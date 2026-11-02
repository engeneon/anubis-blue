#!/usr/bin/env python3
"""Start the local profile with a persistent private identity file."""
import json,os,pathlib,secrets,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[2];state=root/'.anubis';os.umask(0o077);state.mkdir(exist_ok=True)
identity=state/'identities.json'
if not identity.exists():identity.write_text(json.dumps([{'id':'local-owner','role':'admin','token':secrets.token_urlsafe(32)}],indent=2)+'\n')
# Read only provider credentials from the private local file. Never evaluate shell code.
provider_aliases={'OPENAI_API_KEY':'ANUBIS_AI_KEY_OPENAI','ANTHROPIC_API_KEY':'ANUBIS_AI_KEY_ANTHROPIC','DEEPSEEK_API_KEY':'ANUBIS_AI_KEY_DEEPSEEK','XAI_API_KEY':'ANUBIS_AI_KEY_XAI'}
if (root/'.env').exists():
 for line in (root/'.env').read_text().splitlines():
  line=line.strip()
  if line.startswith('export '):line=line[7:]
  if '=' not in line or line.startswith('#'):continue
  name,value=line.split('=',1);name=name.strip();value=value.strip().strip('"').strip("'")
  if name in provider_aliases:os.environ.setdefault(provider_aliases[name],value)
  elif name.startswith('ANUBIS_AI_KEY_'):os.environ.setdefault(name,value)
print('Anubis: http://127.0.0.1:8787',flush=True)
print(f'Your private access token is in {identity}. It is not printed or included in exports.',flush=True)
if (state/'neon-target.json').exists():os.environ.setdefault('ANUBIS_NEON_TARGET',str(state/'neon-target.json'))
os.execve(str(root/'build/anubis'),[str(root/'build/anubis'),'--root',str(root),'--db',str(state/'anubis.sqlite'),*sys.argv[1:]],{**os.environ,'ANUBIS_IDENTITIES':str(identity)})
