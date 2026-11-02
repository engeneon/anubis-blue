"""Repeatable local build and regression gate; browser acceptance is separate."""
import pathlib, subprocess, sys
root = pathlib.Path(__file__).resolve().parents[1]
out = root / 'implementation/usability'
out.mkdir(parents=True, exist_ok=True)
checks = [
 ('ui-build', ['npm', 'run', 'build']),
 ('system-diagram', ['node', 'tests/test_system_diagram.mjs']),
 ('cpp-build', ['cmake', '--build', 'build', '-j4']),
 ('network-tests', [sys.executable, 'tests/test_network_planning.py']),
 ('engine-tests', [sys.executable, 'tests/test_usability.py']),
 ('api-tests', [sys.executable, 'tests/test_usability_api.py']),
 ('planning-regression', [sys.executable, 'tests/test_planning.py']),
 ('system-regression', [sys.executable, 'tests/test_system.py']),
 ('core-regression', ['ctest', '--test-dir', 'build', '--output-on-failure']),
]
for name, command in checks:
 result = subprocess.run(command, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
 (out / (name + '.log')).write_text(result.stdout)
 print(name + ': ' + ('PASS' if result.returncode == 0 else 'FAIL'), flush=True)
 if result.returncode:
  print(result.stdout)
  raise SystemExit(result.returncode)
print('Run tests/ui/usability.cua.js in the authenticated GUI for browser acceptance.')
