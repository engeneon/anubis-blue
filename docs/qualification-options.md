# Qualification options

Software verification, empirical sizing qualification and deployed downstream design tool compatibility are independent gates.

Selected on 2026-10-24: hybrid public evidence plus local downstream design tool. Private evidence, staging qualification and targeted hardware measurements are deferred until nearer release.

| Path | Evidence | downstream design tool route | Establishes | Remaining limits |
|---|---|---|---|---|
| Hybrid (recommended) | Published artifacts, then targeted measurements for important gaps | Isolated local API first; staging later | Reproducible software and expanding applicability coverage | No universal extrapolation; paid/partner GPU testing needs a separate arrangement |
| Public/manual | Published artifacts with exact execution fingerprints | Export/import of existing-field payloads | Deterministic sizing where source applicability holds; manual design workflow | No deployed authentication, reconciliation or remote project concurrency qualification |
| Private/staging | Reviewed internal/customer/partner measurements with reuse rights | Named staging API and test identities | Customer-relevant performance plus operational integration tests | Data quality and coverage still require independent review; no automatic production approval |

Primary starting points: [MLPerf submission requirements](https://github.com/mlcommons/inference/blob/master/Submission_Guidelines.md) and [TensorRT-LLM reproducible benchmarking](https://nvidia.github.io/TensorRT-LLM/performance/perf-benchmarking.html). Retrieved 2026-10-24. These references are discovery sources, not activated Anubis evidence packs. Import an immutable release/commit and exact artifacts; do not resolve a floating `main` branch during compilation.

Each measurement record should identify model/tokenizer revision, runtime/build, hardware SKU and topology, precision, parallelism, workload distribution, offered/admitted load, batch policy, cache state, latency boundaries and percentiles, throughput, quality checks, duration, sample coverage, repetition/variation, source digest and reuse rights. Training additionally needs optimizer, execution-state memory, checkpoint/evaluation overhead and completed useful work. Storage/network measurements must name the measured configuration and endpoint/protocol scope.

Before held-out evaluation, freeze the applicability domain, calibration configuration IDs, minimum samples, relative-error tolerance and false-feasible tolerance. Retain individual rows, failures and residuals. The software evaluation report is an input to independent engineering review, not a replacement for it.

The original three stories intentionally omit performance-critical inputs. A benchmark cannot supply the customer's missing SLO, prompt distribution, operating policy or acceptable degradation. Consultative intake and evidence collection are separate responsibilities.

The local downstream design tool probe is against a named binary digest and source checkout with isolated state. It observed successful stateless compilation for B300 and GB300 and preserved returned warnings and authority. Production compatibility still needs the deployed build, authentication method, actual target contract, representative payload suite and failure/recovery testing. A successful HTTP status is insufficient for engineering approval.
