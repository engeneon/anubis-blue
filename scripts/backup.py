#!/usr/bin/env python3
"""Offline/online SQLite-consistent local backup and offline restore into a new path."""
import argparse, hashlib, json, os, pathlib, sqlite3
p=argparse.ArgumentParser();p.add_argument('operation',choices=['backup','verify','restore']);p.add_argument('source',type=pathlib.Path);p.add_argument('destination',type=pathlib.Path,nargs='?');a=p.parse_args()
os.umask(0o077)
def verify(path):
 with sqlite3.connect(f'file:{path}?mode=ro',uri=True) as c:
  assert c.execute('pragma integrity_check').fetchall()==[('ok',)],'Integrity check failed'
  for body, in c.execute('select body from documents'):json.loads(body)
if a.operation=='verify':verify(a.source);print('Database integrity verified')
else:
 assert a.destination is not None and not a.destination.exists(),'Destination must be a new path'
 if a.operation=='restore':
  manifest=json.loads(a.source.with_suffix(a.source.suffix+'.manifest.json').read_text())
  assert hashlib.sha256(a.source.read_bytes()).hexdigest()==manifest['sha256'],'Backup digest mismatch'
 verify(a.source);a.destination.parent.mkdir(parents=True,exist_ok=True)
 with sqlite3.connect(f'file:{a.source}?mode=ro',uri=True) as source,sqlite3.connect(a.destination) as target:source.backup(target)
 verify(a.destination)
 manifest={'schema_version':1,'sha256':hashlib.sha256(a.destination.read_bytes()).hexdigest(),'profile':'sqlite-local-v1','external_blobs':False}
 a.destination.with_suffix(a.destination.suffix+'.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(f'{a.operation} verified: {a.destination}')
