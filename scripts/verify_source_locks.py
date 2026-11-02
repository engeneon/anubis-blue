#!/usr/bin/env python3
import hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
lock=json.loads((root/'dependency-locks/local-profile.json').read_text())
for item in lock['vendored']:
 assert hashlib.sha256((root/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
assert json.loads((root/'package-lock.json').read_text())['packages']['node_modules/typescript']['version']=='5.7.3'
print('Vendored source and TypeScript locks verified')
