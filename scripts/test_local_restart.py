#!/usr/bin/env python3
"""Check launcher token bootstrap and saved case/draft persistence in isolation."""
import datetime, json, os, pathlib, shutil, socket, subprocess, tempfile, time, urllib.request
ROOT = pathlib.Path(__file__).resolve().parents[1]

def main():
    with tempfile.TemporaryDirectory(prefix='anubis-restart-') as folder:
        root = pathlib.Path(folder)
        (root/'deploy/local').mkdir(parents=True)
        shutil.copy2(ROOT/'deploy/local/run.py', root/'deploy/local/run.py')
        for name in ['build', 'ui', 'contracts', 'knowledge', 'tests', 'docs']:
            (root/name).symlink_to(ROOT/name, target_is_directory=True)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        base = f'http://127.0.0.1:{port}'
        def start():
            proc = subprocess.Popen(['python3', str(root/'deploy/local/run.py'), '--port', str(port)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for _ in range(100):
                try:
                    urllib.request.urlopen(base+'/health', timeout=1).close()
                    return proc
                except OSError:
                    if proc.poll() is not None:
                        raise RuntimeError('Isolated launcher failed')
                    time.sleep(.1)
            proc.terminate()
            proc.wait(timeout=10)
            raise RuntimeError('Startup timed out')
        proc = start()
        try:
            identity = root/'.anubis/identities.json'
            initial = identity.read_bytes()
            token = json.loads(initial)[0]['token']
            assert token and identity.stat().st_mode & 0o777 == 0o600
            def request(path, data=None):
                req = urllib.request.Request(base+'/api/v1/'+path, data=None if data is None else json.dumps(data).encode(), headers={'Authorization': 'Bearer '+token, 'Content-Type':'application/json'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    return json.load(response)
            case = request('cases', {'name':'Isolated restart validation'})
            draft = request('cases/'+case['id']+'/drafts', json.loads((ROOT/'tests/fixtures/meridian.json').read_text()))
            before = {p:request(p) for p in ['cases', 'cases/'+case['id'], 'drafts/'+draft['id']]}
            proc.terminate()
            proc.wait(timeout=10)
            proc = start()
            assert identity.read_bytes() == initial
            for path, expected in before.items():
                assert request(path) == expected, path
            report = {'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'passed':True, 'checks':['first-launch private token bootstrap', 'identity unchanged after restart', 'same token authenticates after restart', 'case list unchanged', 'saved case unchanged', 'saved workload draft unchanged'], 'scope':'Isolated launcher and database on existing macOS toolchain. Normal process restart. Not crash, power-loss or pristine OS qualification.'}
            out = ROOT/'testing-evidence/macos-installation/restart-persistence.json'
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(report, indent=2)+'\n')
            print(json.dumps(report, indent=2))
        finally:
            proc.terminate()
            proc.wait(timeout=10)

if __name__ == '__main__':
    main()
