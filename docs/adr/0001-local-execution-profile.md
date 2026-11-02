# ADR 0001 — Initial local execution profile

Status: implemented development decision; independent architecture review pending.

The implementation uses C++20, nlohmann JSON 3.11.3, cpp-httplib 0.18.3, OpenSSL and SQLite. JSON provides strict parsing and sorted object serialization; HTTP provides the loopback server; OpenSSL supplies SHA256, secure random identifiers and constant-time token comparison. TypeScript 5.7.3 compiles the browser interface without a runtime framework. Playwright 1.64.1 is a development-only browser driver.

Quantities use normalized checked rational int64 pairs, with int128 intermediates. Inputs are decimal strings, never binary floating-point quantities. Overflow rejects the operation. Output exact numerators/denominators remain strings. Canonical unit normalization currently requires a terminating decimal within twelve places; unsupported normalization is an explicit error. Semantic hashes cover normalized workload, locked evidence, engine identity and result. This is an Anubis canonical JSON profile, not a claim of RFC 8785 compliance for arbitrary JSON numbers.

The local service uses one exclusive database owner and a serialized application transaction boundary. Its worker computes outside the transaction and publishes only if its persisted attempt remains current. Restart recovers unfinished compiler jobs. An experimental PostgreSQL backend now serializes application mutations with a database transaction advisory lock and fences worker publication by persisted owner, attempt and a five-minute lease. Separate processes pass optimistic-conflict and idempotency tests. Object-store persistence and production shared-deployment qualification remain outstanding.

For this first implementation, JSON artifacts are stored inline in SQLite transactions rather than in the architecture's proposed external blob directory. This avoids a manifest/blob two-phase publication problem, at the cost of larger database snapshots. The records preserve content digests and history. This is a deliberate local implementation deviation; it does not satisfy the planned shared object-store package.

Knowledge dependencies reference exact SHA256 contents. Equal-identity conflicting evidence is rejected; silently ordered overriding is not supported. New evidence requires a new identity. Every activation retains the resolved contents and dependency lock. Production activation requires a qualified channel, independent approval and a passing preregistered qualification report. Administrative labels and uploaded reports do not themselves prove empirical truth; source review remains an independent gate.

The solver presently implements within-node serving replicas, exact measured training configurations and dedicated stage reservations across explicitly declared scenarios. It does not infer temporal correlation, sharing efficiency, cross-node serving placement or prices. Unknowns remain visible. Core calculations contain no HTTP, database, clock, random or LLM dependencies.

The initial UI stores descriptive text without interpreting it. Registered component descriptors drive quantity controls; cycles fail validation. Edges represent ordering and stage demand is explicit. New evaluators are reviewed code changes, not executable uploads.
