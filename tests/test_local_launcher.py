"""Launcher regression checks without opening ports or touching customer data."""
import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class LocalLauncherTests(unittest.TestCase):
    def test_backend_owns_address_and_receives_port_options(self):
        for options in ([], ["--port", "8791"]):
            with self.subTest(options=options), tempfile.TemporaryDirectory() as folder:
                root = Path(folder).resolve()
                launcher = root / "deploy/local/run.py"
                launcher.parent.mkdir(parents=True)
                shutil.copyfile(ROOT / "deploy/local/run.py", launcher)
                output = io.StringIO()
                previous_umask = os.umask(0o077)
                try:
                    with patch.dict(os.environ, {}, clear=True), patch.object(
                        sys, "argv", [str(launcher), *options]
                    ), patch("os.execve") as execute, contextlib.redirect_stdout(output):
                        runpy.run_path(str(launcher), run_name="__main__")
                finally:
                    os.umask(previous_umask)
                execute.assert_called_once()
                executable, arguments, environment = execute.call_args.args
                self.assertEqual(executable, str(root / "build/anubis"))
                self.assertEqual(arguments, [executable, "--root", str(root),
                                            "--db", str(root / ".anubis/anubis.sqlite"), *options])
                identity = root / ".anubis/identities.json"
                self.assertEqual(environment["ANUBIS_IDENTITIES"], str(identity))
                token = json.loads(identity.read_text())[0]["token"]
                self.assertIn(str(identity), output.getvalue())
                self.assertNotIn(token, output.getvalue())
                # Only the backend may announce an address, using its parsed port.
                self.assertNotIn("http://", output.getvalue())
                self.assertNotIn("8787", output.getvalue())


if __name__ == "__main__":
    unittest.main()
