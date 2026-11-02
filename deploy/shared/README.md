# Experimental shared-repository checks

This is an isolated development test profile, not a deployable production service.

```sh
npm run build
docker compose -p anubis-development-check -f deploy/shared/compose.yaml up --build --abort-on-container-exit --exit-code-from checks
docker compose -p anubis-development-check -f deploy/shared/compose.yaml down -v
```

The PostgreSQL image is pinned by digest. The Debian compiler image installs distribution toolchain dependencies at build time, so it is not yet a fully reproducible release build. Database contents are temporary. No database/API ports are published. The test password is a fixture credential for this disposable network, never a deployment credential. Build-context allowlisting excludes identity files, local databases and customer artifacts.

The backend uses parameterized SQL and a transaction advisory lock for serialized mutations. Draft versions protect optimistic concurrency; idempotency lookups occur inside the same transaction as their mutation. Worker ownership, attempt and a five-minute lease fence result publication. Expired compiler work can be reclaimed; uncertain Neon dispatch is not automatically repeated. This profile does not promise completion of jobs longer than the lease duration.

The check starts two PostgreSQL API processes and a SQLite API process. It compares exact semantic results, competing draft edits, shared record visibility and duplicate mutation reuse. All artifacts currently remain inline in the database; S3/object-store parity, retention, multi-tenant identity federation, disaster recovery and production load qualification remain separate work.

To build the repository backend outside this container, enable `-DANUBIS_WITH_POSTGRES=ON` with libpq development files available. Set `ANUBIS_DATABASE_URL` in the service environment; do not put real credentials in project files. The API still binds to loopback and the local security/deployment restrictions still apply. PostgreSQL snapshots require PostgreSQL backup tooling; the SQLite backup API rejects this profile explicitly.
