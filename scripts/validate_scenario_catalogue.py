#!/usr/bin/env python3
"""Release gate: every demonstration must produce GPU comparisons and a handoff.
Original incomplete stories remain separate boundary fixtures.
"""
import pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[1]
raise SystemExit(subprocess.call([sys.executable,str(root/'tests/test_gpu_readiness.py')],cwd=root))
