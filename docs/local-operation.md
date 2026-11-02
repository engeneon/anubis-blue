# Local development operation

Build prerequisites: CMake >=3.24, C++20 compiler with int128, OpenSSL development libraries, SQLite development libraries, Node/npm and Python 3. Dependencies observed in this workspace are recorded in `dependency-locks/local-profile.json`. The local runtime has been tested on macOS arm64, with development PostgreSQL parity and concurrency checks also run in a Linux arm64 container. These checks do not qualify a production shared deployment.

```sh
cmake --preset local
cmake --build --preset local -j4
npm ci
npm run build
python3 deploy/local/run.py
```

Open http://127.0.0.1:8787 and use the token in `.anubis/identities.json`. That file is created with private permissions and excluded from Git. Use separate identities for curator and approver when evaluating production activation. The identity file can also declare architect, consultant, viewer and agent roles. Restart the service after changing identity configuration. There is no default public password.

The application binds only to loopback. Do not expose this development profile through a network proxy. It does not implement shared-deployment identity federation, session expiry, rate limiting or multi-host isolation. Browser sessions are HttpOnly/SameSiteStrict; all case reads enforce membership. A role called admin does not bypass case membership.

Start from Meridian, Harbor or Aster to explore deliberately incomplete customer inputs. Unknown is different from zero. Add known observations with units and sources; explicitly accept assumptions. Freeze creates an immutable workload revision. Choose a knowledge activation explicitly before compiling; otherwise only demand arithmetic is available. Synthetic fixture evidence is for software verification, not hardware procurement.

The CLI also runs without a service:

```sh
build/anubis compile tests/fixtures/aster.json
build/anubis compile tests/fixtures/synthetic.json knowledge/synthetic.json
```

All application operations are documented in `contracts/openapi.json`, served through authenticated `GET /api/v1/openapi`. `contracts/operations.json` records authorization scopes. `If-Match` protects draft/case edits; `Idempotency-Key` protects retried document mutations; the administrative backup operation is not covered by that mechanism. A job in `succeeded` state can contain an infeasible or unresolved engineering result.

## Backup and recovery

`POST /api/v1/admin/backup` writes a consistent snapshot to the database's sibling `backups` directory. It accepts no client filesystem path. For a portable verified backup and digest manifest:

```sh
python3 scripts/backup.py backup .anubis/anubis.sqlite /absolute/new/backup.sqlite
python3 scripts/backup.py verify /absolute/new/backup.sqlite
python3 scripts/backup.py restore /absolute/new/backup.sqlite /absolute/new/restored.sqlite
```

Restore refuses to overwrite an existing database and verifies the backup digest and database integrity. Stop the service before switching its database. Restart using `--db /absolute/new/restored.sqlite`. Preserve the identity file separately with appropriate permissions; tokens are not part of the database backup. Recovered in-flight compiler jobs replay their frozen input. A second service cannot acquire the same local database lock.

Schema version 1 is the only implemented database profile. No migration or rollback qualification exists for a later schema. To evaluate a newer binary, first take a verified snapshot; retain the prior binary and restore into a separate path if rollback is needed. Never run a destructive schema downgrade.

## Optional agent connection

Run `node mcp/server.mjs` with `ANUBIS_AGENT_TOKEN` set to a dedicated agent identity and `ANUBIS_URL` pointing to this loopback service. Case owners must add that identity to case membership and set `agent_compile_limit` (default zero). The limit is a persisted per-identity, per-case count of submitted jobs. Existing tools can read, compare and compile frozen revisions. The observation-proposal tool additionally requires a positive `agent_proposal_limit` (default zero). Proposals preserve agent provenance and remain unaccepted assumptions until a human reviews individual rows against the original draft version. Review appears in the final intake phase; a changed draft requires a new proposal. Agents cannot apply their own proposals, approve knowledge, finalize a recommendation or submit to downstream design tool. No paid external model calls occur. Disabling the adapter leaves the entire ordinary journey functional.

## Design handoff

Anubis describes the destination as your downstream AI Factory design tool or process. The installed adapter still targets its existing contract; this wording does not add automatic compatibility with arbitrary design tools. API route names, environment variables, identifiers and JSON filenames are retained for backward compatibility. Manual exports and the companion brief can inform other tools or human design processes.

Generate a projection only from a nonfailed candidate with a resolved GPU count. Explicitly approve B300/GB300 modelling substitutions. The exported payload contains existing downstream design tool intake fields only. Keep the companion specification, independent intended platform and omitted storage tiers. The local API probe in `tests/neon-live/probe.py` runs an existing downstream design tool binary with an isolated temporary runtime. Its observations are not a production target qualification.

The actual probe returned 576 HGX B300 GPUs and 1,152 GB300 GPUs for a 56-GPU request. These are the tested target's reference scale points, not Anubis requirements. Returned storage planning defaults and engineering authority restrictions must remain visible. Live submission is disabled by default. An administrator can explicitly configure an experimental local stateless target; returned JSON can also be imported for review. Architecture field matching does not establish workload feasibility.


To enable the tested experimental transport, create a private target JSON file and set `ANUBIS_NEON_TARGET` to its absolute path before starting Anubis:

```json
{
  "id": "reviewed-local-neon",
  "base_url": "http://127.0.0.1:8080",
  "api_version": "1.1.0",
  "mode": "stateless_local_experimental",
  "contract_evidence_sha256": "REPLACE_WITH_SHA256_OF_REVIEWED_COMPATIBILITY_REPORT"
}
```

Use `ANUBIS_NEON_TOKEN` if the target requires bearer authentication. Credentials never enter the frozen job. The connector checks target API version, sends only the projected payload, and retains the returned authority. `POST /api/v1/neon-submissions` requires `confirm_experimental_submission: true` and a projection ID. Poll the returned job, then read its assessment. A lost response or service restart after dispatch yields `outcome_unknown`, never automatic resubmission. `POST /api/v1/jobs/{id}/reconcile` accepts the inspected external response and a source reference. Cancellation after dispatch cannot retract a remote request; any received result is retained. Remote project mutation, remote version-conflict handling and production target certification remain unimplemented.
