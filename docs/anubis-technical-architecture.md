# Anubis AI Factory Workload Sizing Engine

## Deterministic technical solution architecture

Version 1.0 | 27 September 2026 | Implementation baseline

## 1 Purpose and governing decisions

Anubis is a standalone, API-first engineering application that turns incomplete customer workload descriptions into concrete AI factory configuration recommendations. It implements the companion Anubis AI Factory Workload Sizing Framework, version 1.0. This document defines the implementation boundaries, components, data contracts, compilation behavior, integration, security and verification strategy. It is an architecture specification; described components and performance targets are not claims of a completed implementation.

The baseline adopts a modular monolith with a pure deterministic compiler library and separately controlled external adapters. All user and administrative operations are exposed through the application API. The GUI and optional MCP server use that API. An LLM is optional for elicitation, explanation and orchestration and is not required to execute or replay a sizing run.

downstream design tool's intake is a fixed external contract. Anubis adds no fields to downstream design tool, requires no new downstream design tool sizing logic, and remains able to size hardware or server configurations that downstream design tool does not yet support. Intended configurations and downstream design tool modelling configurations are separate records. Explicit user-selected substitutions and external physical specifications are first-class outcomes.

The leading customer artifact is a recommended configuration with workload character, GPU and server resources, memory tiers, storage, fabrics, connectivity and tenancy. Evidence and uncertainty support that recommendation. The API also exposes every intermediate artifact needed to review or reproduce it.

### 1.1 Normative conventions

MUST, SHOULD and MAY in this document express Anubis implementation requirements, preferred practices and optional capabilities. They do not imply that a cited standard mandates the same choice. Baseline changes require an architecture decision record and corresponding contract and test updates.

### 1.2 Core invariants

| ID | Invariant | Verification |
| --- | --- | --- |
| INV01 | Every GUI operation has an API operation | API parity journey tests |
| INV02 | Identical frozen semantic inputs produce identical semantic results | Replay and digest tests |
| INV03 | Intended hardware remains independent of downstream design tool support | Unsupported-platform sizing fixture |
| INV04 | downstream design tool payloads contain only allowlisted existing fields | Projection contract tests |
| INV05 | No substitution silently changes the intended design | Mapping-ledger regression |
| INV06 | No missing evidence becomes a passing result | Unknown-propagation tests |
| INV07 | Agents cannot introduce authoritative arithmetic or policies | API authorization and provenance tests |
| INV08 | Historical runs and decisions remain immutable | Persistence and revision tests |
| INV09 | All material recommendations trace to inputs, rules and evidence | Derivation completeness tests |
| INV10 | Finalization does not imply all design domains are verified | Lifecycle and report tests |

## 2 System context and ownership

The application serves consultants, workload owners, architects, evidence curators and reviewers. It can operate locally for a single consultant or as a shared service. Customer-facing workload tenancy is distinct from Anubis application tenancy: recommending a single-tenant factory does not imply a single-user Anubis installation.

The logical flow is customer and consultant, optional agent, Anubis API and compiler, architect selection, downstream design tool adapter, downstream design tool API and architecture results, then assessment and customer review. The same flow is possible without agents and without a live downstream design tool connection. A disconnected case still produces a configuration dossier and an existing-field intake worksheet.

Anubis owns demand, sizing, evidence qualification, configuration recommendation and assessment of requirements. downstream design tool owns the compiled architecture and its own authority statuses. Anubis MUST preserve those statuses when displaying imported results. An Anubis recommendation is not a procurement authorization, and customer acceptance does not rewrite engineering verification.

## 3 Logical architecture

### 3.1 Deployment structure

Use a C++20 compiler core, a C++ application service and a TypeScript web client. The core is a library with typed inputs and outputs and no direct network, clock, database or UI dependencies. The API host supplies authentication, persistence, job execution and adapters. JSON contracts and schema validation form the language-neutral boundary. CMake and a dependency lock manifest pin the build. The exact HTTP and schema libraries are implementation selections to be recorded before coding; no library is assumed to be required by the methodology.

A separate worker process MAY execute long runs and quarantined prediction adapters from the same release package. This is a process-isolation boundary, not a requirement for independently deployed microservices. A database-backed queue is sufficient initially; no external message broker is required.

The local profile uses SQLite and a local content-addressed artifact directory. The shared profile uses PostgreSQL and an object store through the same repository ports. Shared operation is qualified separately rather than assuming a local database is a multi-host service. Evidence packs and solver bundles are immutable artifacts referenced by digest.

### 3.2 Component responsibilities

| Component | Input | Output and responsibility |
| --- | --- | --- |
| Intake service | Narrative proposals, forms, traces | Typed workload revisions and clarification queue |
| Scenario service | Revision and policies | Frozen operating scenarios and explicit assumptions |
| Knowledge registry | Curated evidence and rules | Immutable pack manifests and applicability indexes |
| Normalizer | Workload revision | Unit-safe canonical demand model |
| Demand compiler | Stage graphs and schedules | Time-scoped rates, jobs and traffic flows |
| Candidate generator | Demand and platform catalog | Stable ordered execution candidates |
| Resource evaluators | Candidate and applicable evidence | Compute, memory, host, storage and network assessments |
| Constraint resolver | Assessments and objectives | Feasible set, preferred candidate and alternatives |
| Explanation builder | Derivation graph | Recommendation facts and rationalisation |
| downstream design tool projector | Selected candidate and target profile | Existing-field payload and separate mapping ledger |
| Integration service | Approved submission request | External run references and immutable response artifacts |
| Design assessor | Intended requirements and downstream design tool result | Domain-by-domain verification and obligations |
| Report service | Frozen run and decisions | Human-readable dossier and intake worksheet |
| Optional MCP adapter | Authorized tool requests | Thin wrappers over the application API |

The evaluators share one canonical domain model. UI code MUST NOT recompute GPU counts, rates, reserves or rounding. Report templates render compiler facts; they do not calculate new engineering facts. An optional narrative generator must cite those facts and cannot alter their status.

### 3.3 Extension points

Workload families, platform profiles and evidence records are data-driven where possible. New calculation behavior is delivered as a reviewed, tested module with a versioned interface. Arbitrary executable code embedded in uploaded knowledge packs is prohibited. A future HPC or video module may define its own work units and memory model while retaining common scenario, evidence and result contracts.

## 4 Canonical data contracts

### 4.1 Principal entities

Case identifies the customer engagement and access boundary. WorkloadRevision is an immutable structured description with source references. ScenarioSet captures operating conditions and growth horizons. KnowledgePackManifest identifies all evidence, rules and platform catalogs. CompilationRun binds these to an engine and solver version. IntendedConfiguration is the actual workload-derived configuration. Recommendation selects a configuration under a declared objective. NeonProjection holds a target-specific payload and MappingLedger. Submission and ExternalRun record integration state. DesignAssessment and DecisionRecord hold review outcomes without modifying source artifacts.

Draft editing uses optimistic concurrency. Freezing a draft creates a new WorkloadRevision; historical revisions never change. Evidence records are similarly superseded or withdrawn, not overwritten. Blob content can be purged under a retention policy, but a purged record must explicitly lose replay availability rather than pretending it remains reproducible.

### 4.2 Quantity and observation contract

Every engineering quantity carries dimension, unit, scope and horizon. Internal byte counts and device counts use checked integers; rates and ratios use fixed-scale decimal or rational arithmetic. JSON encodes exact large integers and decimal quantities as canonical strings where necessary, avoiding precision loss above JavaScript's safe integer range. Conversion to downstream design tool's numeric fields is validated for representability and documented rounding.

An observation includes value, origin, source reference, confidence basis where calibrated, acceptance state and assumption owner. Unknown has an explicit discriminant. Negative capacity, NaN, infinity and incompatible dimensions fail validation. Derived values reference graph nodes rather than copying unexplained constants.

Illustrative Anubis quantity fragment:

```json
{
  "value": "100",
  "unit": "request/s",
  "scope": {"stage_id": "llm_1", "scenario_id": "peak"},
  "origin": "derived",
  "derivation_id": "demand_017"
}
```

### 4.3 Workload and scenario contracts

WorkloadRevision contains applications, stage graphs, model references, quality constraints, activity, data assets, execution preferences, tenancy policies, service objectives, growth drivers and assumption references. A ModelReference includes exact revision or an explicitly unresolved shortlist. Hardware SKU, HBM variant, runtime, tokenizer, precision and parallelism remain independent identifiers.

ScenarioSet records scheduled overlap, arrival traces or bounded distributions, cache state, failures, restoration behavior and permitted degradation. Every latency objective declares metric, percentile, measurement boundary and unit. A whole-workflow deadline is not interchangeable with model-service latency. Retry behavior has limits; graph validation rejects unbounded expansion unless a qualified model explicitly supports it.

### 4.4 Evidence contract

Each evidence record contains immutable source and artifact digests, configuration fingerprint, workload shape, results, measurement boundary, quality conditions, sample coverage, variation, validity domain and reuse permissions. Pack governance distinguishes normative requirements, recommendations, benchmark rules, vendor facts and Anubis policies. ITU-T F.748.26 supplies the evaluation-record structure [1]. MLPerf-derived evidence retains its benchmark release and execution conditions [2].

Prediction records additionally identify model version, calibration dataset digest, held-out evaluation, error bounds and permitted interpolation dimensions. AIConfigurator or another external predictor is wrapped by a pinned adapter; its outputs enter as prediction artifacts rather than being promoted automatically to measurements [3].

### 4.5 Result contracts and status dimensions

CompilationResult contains characterization, domain requirements, all assessed candidates, preferred candidate, alternatives, diagnostics, unresolved questions and provenance. Each recommendation fact has value, unit, scope, evidence basis, feasibility status, binding constraints, assumptions and derivation reference.

EvidenceBasis is measured, directly_supported, derived, bounded or insufficient. Feasibility is pass, fail, conditional or unknown. ProjectionMode is direct, substitution or partial. AssessmentState is verified, conditional, external_adjustment or unverifiable. SelectionState is experimental, selected or finalized. These dimensions MUST NOT be collapsed into one green status.

IntendedConfiguration separates active GPUs, continuity reserve, installed GPUs and topology rounding; HBM, host DRAM and NVMe; live, usable and raw storage; individual directional network flows; and exclusive versus shared operating windows. Hardware without a downstream design tool representation is valid in this contract.

## 5 Deterministic compilation pipeline

### 5.1 Stages and failure behavior

The compiler performs validation, normalization, demand expansion, evidence matching, candidate generation, joint evaluation, ranking, explanation and artifact assembly. A schema-valid partial result is returned for insufficient information. Malformed inputs produce structured field errors. Runtime failures are distinct from engineering infeasibility.

Validation checks units, graph cycles, distribution consistency, model identity, mutually exclusive policies and reserve semantics. Normalization resolves accepted defaults from named profiles. Demand expansion builds stage rates, token distributions, training jobs and data flows. Evidence matching applies hard compatibility filters before ranked matching; unsupported interpolation produces a diagnostic.

Candidate generation enumerates permitted model/runtime/platform combinations in stable order. Cheap incompatibility and memory checks prune candidates before expensive performance evaluation. Complete candidates include placement, storage and network assumptions. Resource evaluations record bottlenecks and never turn missing measurements into zero-cost dependencies.

### 5.2 Reference algorithm

```text
compile(frozen_input):
    validate_schema_and_dimensions(frozen_input)
    demand = normalize_and_expand(frozen_input)
    candidates = generate_in_stable_order(demand, frozen_pack)
    for candidate in candidates:
        evidence = match_with_explicit_applicability(candidate)
        result = evaluate_all_scenarios(candidate, evidence)
        record_constraints_and_derivations(result)
    rank_only_under_declared_objectives()
    return canonical_result_with_partial_domains_if_needed()
```

The finite candidate search domain, platform limits and scenario set are recorded. Finding the best candidate within that domain is not a global optimality claim over all possible hardware. If a bounded search is interrupted, return the feasible incumbent and search coverage with optimality unproven. Never present search exhaustion or a timeout as proof of infeasibility.

### 5.3 Coupling and scheduling

Initial release evaluators calculate whole candidate operating points using calibrated profiles. Where iteration is needed, update dependencies in a fixed sequence and terminate on stable discrete configuration and bounded numeric residual. A deterministic iteration cap produces conditional or unknown results on non-convergence. Cache, network or storage benefits require explicit evidence rather than optimistic feedback.

Scheduling uses declared job windows and placement constraints. Pooling is allowed only under tenancy policy and qualified interference behavior. Failure scenarios remove actual domains from the placement graph. A spare GPU on an unavailable node cannot satisfy a resilience constraint. End-to-end workflow latency uses a validated model or trace replay; adding independent p95 values is prohibited.

### 5.4 Semantic reproducibility

The replay key includes normalized input, accepted assumption set, scenarios, policy, pack digest, engine version, solver configuration and external-prediction artifacts. It excludes timestamps, actor display names, job IDs and report pagination. Canonical JSON follows a pinned serialization profile based on RFC 8785, with domain-specific normalization completed before serialization [4]. Decimal strings prevent accidental binary-float differences; array ordering is explicitly defined.

The core cannot read live prices, mutable URLs, current time or ambient environment. Randomized modelling uses stored seeds and a pinned implementation, but a seed alone does not guarantee cross-platform equality. The release's numeric backend, solver, architecture and rounding are recorded. Exact replay is certified only for the declared execution profile; other profiles must pass cross-profile equivalence tests before being advertised as interchangeable.

Parallel execution may evaluate independent candidates, but deterministic reduction and ordering remove scheduler-dependent ranking. Semantic JSON digests are the replay criterion. PDF or DOCX byte identity is not required because document metadata and renderer versions can differ.

## 6 Knowledge and standards governance

Knowledge packs progress through draft, validated, released, deprecated and withdrawn. Curators ingest evidence, record its applicability and source, and run calibration and regression checks before publication. Release creates an immutable manifest containing artifact digests, dependency versions and the rules that admit each record.

A standards matrix maps source/version/clause to an Anubis field, validator or test. Alignment claims are scoped to implemented provisions. No blanket certification is inherited from using a standard's vocabulary. Vendor reference architectures constrain only matching platform profiles [5]. Facilities requirements remain downstream; ISO/IEC 22237 does not supply the compute-sizing algorithm [6].

The registry records licensing and permitted storage or redistribution of evidence. Private customer traces are isolated from public packs and may yield redacted measurement summaries. Withdrawn evidence triggers an impact report for dependent runs; historical data and audit facts are not silently rewritten. Recompilation with a replacement pack creates a new result.

## 7 API design

### 7.1 General contract

Publish OpenAPI 3.1.1 and JSON schemas as versioned artifacts. OpenAPI describes the transport and payload contracts; it does not define engineering semantics [7]. The initial base path is /api/v1. Additive fields may be introduced compatibly; semantic changes to units, defaults, status interpretation or ranking require explicit contract versioning.

All collections have bounded pagination. Mutating draft requests use If-Match revision checks. Expensive commands accept an Idempotency-Key scoped to principal, operation and payload digest. Reusing a key with different content returns 409. Long operations return 202 with job and result links. Errors contain stable code, message, field path, retryable flag, remediation and correlation ID. Domain infeasibility is a completed result, not HTTP 500.

### 7.2 Operation coverage

The following endpoint families are the implementation contract. Collection GET and item GET are supplied for persisted entities unless access policy forbids them. Archive, purge and administrative operations also use APIs; no GUI-only controls are permitted.

| Area | Representative operations | Outcome |
| --- | --- | --- |
| Cases | POST /cases; GET and PATCH /cases/{id}; POST archive | Engagement and access scope |
| Intake | POST /cases/{id}/drafts; PATCH /drafts/{id}; POST /drafts/{id}/validate | Versioned editable description |
| Revision | POST /drafts/{id}/freeze; GET /revisions/{id} | Immutable workload revision |
| Elicitation | POST /clarification-runs; POST /assumption-decisions | Ordered questions and recorded decisions |
| Scenarios | POST /scenario-sets; POST /scenario-sets/{id}/fork | Frozen operating alternatives |
| Evidence | POST /evidence-records; POST /evidence-records/{id}/validate | Qualified source records |
| Packs | POST /knowledge-packs; POST validate, release or withdraw | Governed versioned knowledge |
| Sizing | POST /compilations; GET /compilations/{id} | Requirements and configuration candidates |
| Analysis | POST /comparisons; POST /sensitivity-runs | Differences and material uncertainty |
| Selection | POST /recommendation-decisions | Selected configuration and objective |
| Projection | POST /neon-projections; GET /neon-projections/{id} | Existing-field payload and mapping ledger |
| Integration | POST /neon-submissions; POST /neon-submissions/{id}/reconcile | Experimental or finalised handoff |
| Results | POST /external-result-imports; POST /design-assessments | Imported artifacts and domain assessment |
| Finalization | POST /finalization-decisions | Audited selected deliverable state |
| Reporting | POST /reports; GET /artifacts/{id} | Dossier, worksheet and machine exports |
| Jobs | GET /jobs/{id}; GET /jobs/{id}/events; POST /jobs/{id}/cancel | Progress and cancellation |
| Administration | APIs for memberships, roles, integrations, retention and audits | Complete operational control |

Representative compilation request, with illustrative identifiers:

```json
{
  "workload_revision_id": "wr_0042",
  "scenario_set_id": "ss_0007",
  "knowledge_pack_id": "kp_0012",
  "policy_id": "policy_0003",
  "execution_profile_id": "deterministic_v1"
}
```

The service resolves these identifiers to immutable digests before queueing. A caller cannot pass a mutable latest alias into the compiler. An alias may be resolved at the API boundary and the resolved value returned before execution.

### 7.3 Jobs and concurrency

Job states are queued, running, cancel_requested, succeeded, failed and cancelled. A successful computation may have a conditional engineering result. Cancellation is cooperative at defined checkpoints. A result committed before a cancellation race remains succeeded and the cancellation response reports that fact.

Worker leases expire and can be reclaimed. Attempts write temporary artifacts and atomically commit the result manifest. A deterministic replay may be reused only when authorization and all semantic digests match. A database transaction records the run, result references and audit event; large blobs are staged and verified before attachment. Orphan cleanup never deletes referenced artifacts.

## 8 downstream design tool integration without intake changes

### 8.1 Observed contract and scope

The local downstream design tool checkout was inspected at Git commit c1ed300383d68bda6ee1d66bc8c39f44c2045370 on 27 September 2026. The checked-in GUI serializer, schema, API description and server implementation provide the baseline evidence. This is source inspection, not a live deployment compatibility test. The adapter MUST verify the deployed version and permitted operations before submitting [N1–N4].

The observed GUI platform selector exposes HGX_B300 and GB300_NVL72. The input schema also includes an any platform value, which must not be treated as equivalent to an explicit GUI selection. Adapter profiles target an actual supported workflow and its effective semantics, not merely a permissive JSON schema.

### 8.2 Projection rules

| Intended Anubis value | Existing downstream design tool path | Mapping requirement |
| --- | --- | --- |
| Selected modelling platform | requirements.platform | Explicit direct or user-selected substitute |
| Installed target GPUs | requirements.target_gpu_count | Preserve intended count and record downstream design tool rounding |
| Fabric choice | requirements.network_fabric and east_west_fabric | Keep legacy and explicit fields consistent |
| Storage fabric | requirements.storage_fabric | Use exact supported enum |
| Storage purpose and vendor | requirements.storage_role and storage_vendor_preference | Preference is not qualification |
| Usable capacity | requirements.storage_capacity.usable | Value and unit, with tier scope in ledger |
| Read and write demand | storage_performance_profile.aggregate_read_gbps and aggregate_write_gbps | These observed fields represent GB/s, not network Gbps |
| Metadata demand | storage_performance_profile metadata rate fields | Preserve operations per second |
| Protocols | requirements.storage_protocols | Existing boolean keys only |
| Tenancy and business model | requirements.tenancy_model and operating_model | Keep separate internal dimensions |
| Storage class | requirements.storage_model | Do not treat HPS_CMX as arbitrary two-tier storage |
| External connectivity | external_connectivity existing fields | Bandwidth is Gbps; map purposes and policy |
| Detailed server resources | No general complete field mapping established | Retain intended specification outside the design tool |

Paths under storage_performance_profile in this table are relative to requirements. Exact fields are enumerated in the adapter's allowlist with target-specific schema and semantic tests. The observed serializer supports capacity reserve and growth fields; the adapter MUST reconcile whether Anubis has already applied them to avoid applying either twice. If downstream behavior cannot be established, mark the affected sizing outcome conditional.

The current single usable-capacity structure cannot be assumed to preserve independent object and file tiers. Export the selected supported storage scope and retain other tiers externally, or create explicitly separate design scenarios where appropriate. Do not add capacities and claim that tier semantics survived. Similarly, an existing fabric selection does not necessarily encode every desired separation or latency constraint; assess the returned result and retain external obligations.

### 8.3 Intended and modelling configurations

NeonProjection references intended_configuration_id, target_profile_id, modelling_platform, payload_digest and mapping_ledger_id. Its actual downstream design tool payload contains none of these Anubis-specific metadata fields. The mapping ledger records original value, projected value, unit conversion, rule, decision owner, information loss and affected domains.

For B200 to B300 or GB300 substitutions, compare at least GPUs per node, node/rack count, NIC endpoints, link rates, scale-up connectivity, storage clients and failure domains. The mapper does not automatically replace intended sizing with the substitute's optimal GPU count. It presents mapping options and their consequences for user selection. A modelled platform may be useful for storage or external connectivity even when its compute fabric is not reusable.

Substitution approval records authority for that scenario; repeated submissions of the unchanged approved scenario do not require another identical decision. Any material change to its effects creates a new decision requirement. Insufficient substitution evidence permits an explicitly partial or conditional handoff rather than blocking all Anubis capability.

### 8.4 Existing API paths

The inspected source exposes authenticated API v1 routes including POST /api/v1/compiler-runs/reference-architecture, project working-state operations, POST /api/v1/projects/{id}/runs and GET /api/v1/runs/{id}. The project-run path consumes the project's working-state input_profile; it rejects supplying an independent run input. Secure execution uses expected_state_version and an idempotency key, and returns an asynchronous job [N2,N3].

The adapter supports two profiles after contract qualification. A stateless compilation profile sends the supported intake to the direct compilation route when authorized. A project profile creates or selects an isolated experimental project, reads its working state, updates the input_profile using the existing version check, then starts a run using that expected version. It follows the actual returned job/result references rather than inventing a job route. Exact request bodies and authentication scopes come from the pinned deployed contract.

Legacy /api/v0 routes are disabled by the inspected secure server profile and MUST NOT be used as an authentication workaround [N4]. If the deployed API differs or an operation is unavailable, fall back to a worksheet/export and explicit result import. No downstream design tool upgrade is required to complete an Anubis sizing engagement.

### 8.5 Integration reliability and finalization

Submission states are prepared, dispatching, submitted, awaiting_result, completed, failed and outcome_unknown. Before dispatch, persist an outbox record with the payload digest and stable idempotency key. After a timeout, reconcile before retrying a mutation whose remote outcome is unknown. Where downstream design tool offers no idempotency or lookup sufficient to disambiguate the result, require explicit reconciliation; exactly-once delivery cannot be promised across that boundary.

Experimental submissions never overwrite an accepted baseline by default. Finalised submission is an Anubis selection state; it does not silently invoke downstream design tool promotion or approval operations. Those are separate authorized actions when supported. Store external project/run IDs, exact request and response digests, target profile and correlation IDs. Remote errors and authority warnings remain visible.

### 8.6 Closing the design loop

DesignAssessment maps each material requirement to returned architecture evidence or an external specification. Each domain is verified, conditional, requires external adjustment or unverifiable. A missing field is unverifiable, not passed. Returned GPU rounding can trigger renewed storage-client, host or network calculations; it cannot silently alter the frozen workload.

IterationPolicy sets permitted input changes, maximum scenarios, compute or commercial budget, stopping criteria and who may finalize. Stop on satisfied review criteria, exhausted budget, no material improvement or required human decision. Agents cannot satisfy the loop by relaxing quality or resilience unless that change is authorized and versioned. Final customer acceptance and unresolved engineering obligations coexist explicitly.

## 9 Optional MCP and agents

The MCP server exposes task-oriented tools such as validate_workload, compile_scenario, compare_runs, project_to_neon, submit_experiment and assess_design. Each calls an API operation with the caller's effective identity. Resources expose immutable run summaries and evidence references subject to access checks. Protocol version and transport are pinned; MCP is an integration protocol, not an engineering inference engine [8].

Narrative extraction produces proposed observations with source spans. The consultant reviews material assumptions through the API, or a pre-authorized policy may accept designated low-impact defaults. Neither prompts nor retrieved documents can release a knowledge pack, override a failed constraint or grant a user additional permissions. Tool results are treated as data.

Agent credentials are scoped by case and operation. Experimental iteration may be pre-authorized within bounds. Finalization and external writes follow explicit engagement policy and the user's standing authorization. Agents cannot obtain broader rights merely by calling another MCP server. An integration credential for downstream design tool is held in a secret store and never exposed in prompts or reports.

## 10 Persistence security and operations

### 10.1 Storage and audit

Relational records hold case ownership, revisions, runs, jobs, decisions, submissions and artifact references. Content-addressed blobs hold traces, evidence, canonical JSON, external results and documents. Tenant-scoped access checks precede every read, including cache hits and artifact downloads. Deduplication must not reveal whether another tenant owns identical content.

Audit records contain actor, operation, case, before/after references, authority decision, correlation ID and timestamp. Append-only audit storage records changes; tamper evidence requires an additional signed or protected audit mechanism if the deployment claims it. Database backups and artifact backups are restored together using a manifest consistency check.

### 10.2 Access and data protection

Roles are viewer, consultant, architect, evidence curator, release approver and administrator, with service identities for agents and adapters. Shared deployments use authenticated sessions or scoped service credentials and encrypted transport. A local profile binds to loopback and still protects privileged operations; it must not expose an unsecured service on the network by default.

Uploads are size-limited, typed and quarantined before parsing. Parsers and prediction tools run with resource limits. Outbound adapter destinations are configured, not supplied as arbitrary URLs in a workload, preventing requests to unintended internal endpoints. Logs exclude secrets and raw customer prompts by default. Redacted traces, retention and deletion controls are API operations with auditable scope.

Application availability and data recovery targets are deployment choices, distinct from the AI factory availability being sized. Establish RPO/RTO in the deployment profile and prove restore procedures before shared production use. No unmeasured uptime commitment is implied by this architecture.

### 10.3 Observability and graceful degradation

Measure API latency, queue age, candidate count, evaluator time, evidence-match coverage, unresolved requirements, replay divergence, integration retries and outcome_unknown submissions. Logs identify semantic run digests and correlation IDs without leaking customer data. Health reports distinguish compiler readiness, registry integrity, storage access and downstream design tool connectivity.

downstream design tool unavailability does not prevent sizing or report generation. Agent unavailability does not affect deterministic operations. Missing evidence produces partial domain results. Prediction-adapter failure produces a structured unresolved assessment, not a fabricated fallback rate. Search exhaustion preserves feasible incumbents and diagnostics.

## 11 Verification and acceptance

### 11.1 Engineering tests

Golden cases cover model fit, latency-aware replica sizing, failure-domain loss, batch scheduling, agent retries, mixed workloads, cache-cold behavior, storage overlap and fabric alternatives. Property tests check dimensional consistency and monotonic resource demand under fixed execution policy. Monotonicity is not assumed for an optimized runtime across changing batches or architectures; those cases require explicit fixtures.

Metamorphic tests include equivalent unit representations, reordered non-semantic inputs and identical accepted assumptions producing the same result. Increasing demand cannot improve a fixed candidate's spare capacity. Evidence removal cannot turn an unknown candidate into pass. Reserve and growth are applied exactly once. Every reported vendor exclusion has a scoped failing predicate.

Calibration tests use held-out representative workloads and predeclared tolerances, measuring false feasibility separately from average prediction error. The architecture does not invent a universal acceptable percentage error. Benchmark definitions and customer qualification remain separately labelled. Pack release requires documented applicability and unresolved coverage.

### 11.2 Contract and workflow acceptance

| Test ID | Acceptance scenario | Required outcome |
| --- | --- | --- |
| AT01 | Complete consultation through API only | Same semantic result as GUI journey |
| AT02 | Replay pinned run | Identical canonical semantic digest |
| AT03 | B200 intended design with B300 projection | Intended platform preserved; substitute explicit |
| AT04 | Substitute changes NIC/node count | Affected network domain flagged or recalculated |
| AT05 | Storage 8 GB/s and external 8 Gbps | No byte/bit confusion |
| AT06 | Separate object and file tiers | No silent collapse into one verified tier |
| AT07 | Interrupted external submission | Reconciled without blind duplicate creation |
| AT08 | Concurrent edit before downstream design tool run | Version conflict rather than stale compilation |
| AT09 | Missing or withdrawn evidence | Unknown/conditional result and impact notice |
| AT10 | Agent attempts policy override | Denied and audited |
| AT11 | Finalised partial mapping | External obligations preserved in report |
| AT12 | Future downstream design tool B200 support | New adapter maps existing intended model directly |

Unit and mocked contract tests precede a deployed integration suite against the exact supported downstream design tool version. Source inspection alone is insufficient for an integration release. GUI tests verify that users can distinguish measured, predicted, assumed and substituted facts. Report tests verify recommendation completeness and matching provenance.

### 11.3 Release gates

A compiler release passes schema, deterministic replay, golden-case, dependency-boundary and security checks. A knowledge-pack release additionally passes evidence and calibration review. A downstream design tool adapter release passes target-contract and semantic-loss tests. A shared deployment passes tenant isolation, backup/restore and concurrency tests. Artifacts record engine, pack, adapter and report-template versions independently.

## 12 Delivery sequence and architecture decisions

Milestone 1 establishes canonical schemas, the API, draft/revision lifecycle, evidence registry and an inference vertical slice that produces a concrete recommendation and manual downstream design tool worksheet. It proves the end-to-end boundary before expanding the taxonomy.

Milestone 2 adds training/tuning, data-flow storage sizing, host resources, network scenarios and failure placement. Milestone 3 adds qualified storage configurations, tenancy/interference profiles and rationalised alternatives. Milestone 4 enables the existing downstream design tool API adapter, domain assessment and bounded experimental loops. Milestone 5 adds MCP wrappers and assisted elicitation; it introduces no new calculation authority. Each milestone requires the applicable acceptance tests, not merely UI completion.

Initial decision records are: ADR01 modular monolith and pure core; ADR02 API parity; ADR03 exact quantities and semantic reproducibility; ADR04 immutable evidence and revision model; ADR05 intended versus modelling configurations; ADR06 unchanged downstream design tool intake; ADR07 explicit partial projection; ADR08 bounded agent orchestration; ADR09 asynchronous jobs and external reconciliation; ADR10 scoped evidence qualification.

The main implementation risks are evidence scarcity, misleading cross-platform extrapolation, subtle intake semantics, unschedulable mixed workloads and overclaiming substitution equivalence. The corresponding controls are explicit coverage, calibrated applicability, target-profile tests, placement-aware scenarios and per-domain assessment. These controls should preserve useful partial outputs rather than narrowing Anubis to downstream design tool's current hardware catalog.

## Appendix A Implementation package structure

```text
anubis/
  contracts/          JSON schemas and OpenAPI
  src/domain/         quantities and canonical entities
  src/compiler/       pure pipeline and evaluators
  src/application/    commands jobs and authorization
  src/persistence/    repositories and migrations
  src/adapters/       downstream design tool and prediction integrations
  src/api/            HTTP transport
  ui/                 API client and consultation interface
  mcp/                optional API wrappers
  knowledge/          manifests and curated pack sources
  tests/              replay calibration and contract cases
  docs/adr/           architecture decisions
```

Dependencies point inward: transport and adapters depend on application contracts; application services depend on domain and compiler interfaces; the core depends on neither transport nor persistence. A dependency test enforces this direction. External predictor adapters do not import UI or downstream design tool-specific schema into the domain model.

## Appendix B Artifact set for one completed case

A completed case has a workload revision, scenario set, pinned pack manifest, compilation result, intended configuration, selected recommendation, explanation graph, sizing dossier and decisions. If downstream design tool is used, it additionally has the exact intake payload, mapping ledger, submission record, returned architecture artifacts and design assessment. A final report includes the chosen configuration, alternatives considered, material assumptions, evidence basis and externally implemented requirements. None of these supporting artifacts require new downstream design tool intake fields.

## References and implementation evidence

[1] ITU-T. F.748.26, AI cloud platform performance evaluation. https://www.itu.int/rec/T-REC-F.748.26-202402-I/en

[2] MLCommons. Benchmark suites and submission guidance. https://mlcommons.org/benchmarks/ ; https://docs.mlcommons.org/inference/submission/

[3] NVIDIA and AI Dynamo contributors. AIConfigurator. https://github.com/ai-dynamo/aiconfigurator

[4] Rundgren, A., Jordan, B., and Erdtman, S. RFC 8785, JSON Canonicalization Scheme. June 2020. https://www.rfc-editor.org/rfc/rfc8785

[5] NVIDIA. NVL72 AI Factory Enterprise Reference Architecture. https://docs.nvidia.com/enterprise-reference-architectures/nvl72-ai-factory/latest/abstract.html

[6] ISO/IEC. ISO/IEC 22237-1:2021. https://www.iso.org/standard/78550.html

[7] OpenAPI Initiative. OpenAPI Specification 3.1.1. https://spec.openapis.org/oas/v3.1.1.html

[8] Model Context Protocol. Architecture, protocol revision 2025-06-18. https://modelcontextprotocol.io/specification/2025-06-18/architecture

[N1] downstream design tool checkout c1ed300383d68bda6ee1d66bc8c39f44c2045370. src/ui/reference_architecture/app.js, requestFromForm, and index.html platform and storage controls.

[N2] Same checkout. docs/api/openapi-v1.yaml and openapi-v1.1.yaml, API contract descriptions. These accompany rather than replace deployed behavior checks.

[N3] Same checkout. src/api/application_api.cpp, direct compiler route, project working-state and project-run handling, including expected_state_version and secure asynchronous submission.

[N4] Same checkout. src/api/reference_architecture_server.cpp, API v1 dispatch and secure-profile rejection of legacy v0 routes; ckp/reference_architecture_compiler/v0_2_0/schemas/input_schema.json.

Online references and local source inspected 27 September 2026. Protocol revisions above are deliberate baselines, not claims of the latest available version.
