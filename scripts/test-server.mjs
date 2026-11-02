import { fixtureProvider } from "../tests/copilot-fixture-server.mjs";
import { spawn } from "node:child_process";
import { mkdtempSync, rmSync, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
const directory = mkdtempSync(join(tmpdir(), "anubis-ui-"));
mkdirSync("test-results", { recursive: true });
const fixture = fixtureProvider();
await new Promise((resolve) => fixture.listen(0, "127.0.0.1", resolve));
const fixtureOrigin = "http://127.0.0.1:" + fixture.address().port;
// Fixed test-only origin discovery is served by the UI test launcher.
import { writeFileSync } from "node:fs";
writeFileSync("test-results/copilot-fixture-origin.txt", fixtureOrigin);
const child = spawn(
  "build/anubis",
  [
    "--root",
    process.cwd(),
    "--db",
    join(directory, "test.sqlite"),
    "--port",
    "8799",
  ],
  {
    stdio: "inherit",
    env: {
      ...process.env,
      ANUBIS_TOKEN: "ui-test-token-not-a-production-secret",
      ANUBIS_AI_ALLOWED_ORIGINS: JSON.stringify([fixtureOrigin]),
      ANUBIS_AI_KEY_UI_FIXTURE: "ui-fixture-key-not-real",
    },
  },
);
function stop() {
  child.kill("SIGTERM");
  fixture.close();
}
process.on("SIGTERM", stop);
process.on("SIGINT", stop);
child.on("exit", (code) => {
  fixture.close();
  rmSync(directory, { recursive: true, force: true });
  process.exit(code || 0);
});
