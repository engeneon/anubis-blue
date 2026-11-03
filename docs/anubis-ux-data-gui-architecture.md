# Anubis User Experience and Data Architecture
## Technical specification for the workload builder and analysis workspace

Version 1.0 | 24 October 2026 | Proposed implementation specification

## 1 Purpose and governing decisions

This document specifies the Anubis user experience, information architecture, application data model and GUI layout. It gives product designers and engineers an implementation baseline for turning incomplete customer knowledge into a reviewed workload model, a reproducible sizing recommendation and an existing-field Design handoff. It complements the Anubis framework and technical solution architecture dated 27 September 2026. It elaborates their knowledge registry into explicit EKB and CKP governance and makes LLM-independent operation a mandatory user journey.

Anubis shall support complete engagements through structured GUI and API operations without an LLM. Optional agents propose observations, scenarios and explanations through the same application API. The deterministic compiler owns calculations, eligibility and engineering conclusions. The GUI renders these results and never implements a second sizing engine.

The product uses a bounded, extensible workload builder. Templates create editable compositions of supported stages; typed quantities, ranges, schedules and structured imports express their behaviour. Free text remains a source note until a person or an optional agent proposes structured observations and the required acceptance policy is satisfied. An unsupported application remains a saved case with explicit coverage gaps.

downstream design tool intake remains unchanged. Intended hardware and complete Anubis requirements remain independent of the platform selected to model a design in downstream design tool. Requirements that cannot be represented in that intake accompany the handoff as external specifications. This document specifies proposed Anubis interfaces; it does not assert that those interfaces or a live downstream design tool integration are already implemented.

## 2 Users and information architecture

The consultant develops the workload description with the customer. The architect inspects execution choices, alternatives and downstream design tool mapping. The customer reviewer reads the recommendation and confirms business assumptions. The evidence curator prepares knowledge packages; the release approver authorizes their use. The administrator manages access and integrations. Roles may be combined in a small deployment, but authorization checks remain operation-specific on the server.

The primary navigation consists of Cases, Knowledge and Administration. Opening a case exposes Overview, Workload, Scenarios, Analysis, Compare, Handoff and Reports. Case membership is the access boundary. Customer review uses a restricted presentation of the same immutable artifacts rather than a separate set of calculations. Knowledge and Administration are hidden when inaccessible, and their API operations still enforce permissions.

The case header always identifies the customer case, selected scenario, workload revision and save or run state. The user can distinguish an editable draft from the frozen revision underlying a result. Switching a scenario must not silently replace the revision displayed in an existing analysis.

| Workspace | Main purpose | Primary action |
|---|---|---|
| Cases and Overview | Locate engagements; see owner, last activity and outstanding questions | Create or resume case |
| Workload | Compose stages and complete the phased intake | Validate and review |
| Scenarios | Define operating envelopes and controlled variations | Freeze and compile |
| Analysis and Compare | Inspect recommendations, constraints and differences | Select configuration |
| Handoff | Inspect the downstream design tool projection and returned design | Export or submit |
| Reports | Generate customer and engineering deliverables | Generate report |
| Knowledge | Inspect coverage, evidence and package activation | Validate or activate pack |

## 3 Phased workload builder

The builder permits backward navigation and incomplete saves. Each phase shows completion and coverage separately. Completion means the required description has been supplied for that phase; it does not imply the workload is sizeable or feasible. A contextual review queue explains why a missing field matters and links directly to it.

| Phase | Principal inputs | Exit condition |
|---|---|---|
| Purpose | Workload template, business objective and application boundaries | At least one application with a supported or explicitly unresolved family |
| Composition | Stage types, connections, local or external execution, branching | Graph structure validated or gaps recorded |
| Models | Model revision or shortlist, runtime restrictions, quality and precision choices | Execution constraints captured without silent substitution |
| Demand | Activity rates, token distributions, dataset sizes and job volumes | Quantities have units, scope and origin |
| Service | Latency metrics, throughput targets and completion deadlines | Metric boundary, percentile and time window defined |
| Data | Data assets, retention, access, ingestion and checkpoints | Storage and movement responsibilities identified |
| Operations | Overlap, tenancy, failure conditions and growth | Scenario conditions and reserve ownership explicit |
| Review | Assumptions, unknowns and description coverage | User can freeze a valid revision or save unresolved work |

### 3.1 Progressive disclosure and editing

Selecting a template creates normal editable entities with a template version reference. It does not create an opaque sizing category. For example, a retrieval assistant expands into retrieval and inference stages, with optional embedding and external-tool stages. Removing a stage shows affected connections and data references before confirmation; undo restores the draft operation. No historical revision is changed.

The default editor is a stage list with a selected-stage form. An optional graph view edits the same entities and supports equivalent keyboard actions. Branches specify their rate or scenario semantics; loops require a bounded count or an explicitly supported model. Independent maxima are not automatically treated as simultaneous peaks. Unsupported graph features produce actionable diagnostics and preserve all supplied information.

Users can choose a known value, estimate, accepted template assumption or unknown. Numeric estimates can be ranges with units. Zero is a valid value only where the field contract permits it and never represents unknown. Distribution summaries must identify their meaning; a mean and p95 do not imply a complete probability distribution. Intake cannot silently generate a distribution from those summaries.

### 3.2 Questions and assumptions

A versioned clarification policy orders questions by blocking dependency, materiality category and stable field identifier. If sensitivity results exist, their recorded influence may refine the order. The UI states why the question is being asked. It does not display a fabricated percentage confidence or an uncalibrated information-gain score.

Every proposed default displays value, scope, source, applicability and the consequence of acceptance. An engagement policy may pre-authorize low-impact defaults; accepted defaults remain visible and reversible in a new revision. A material assumption requires a recorded decision. Rejecting a proposal does not delete the original customer statement.

### 3.3 Imports and unsupported workloads

Structured CSV or JSON imports use a preview workflow: upload, quarantine and parse, select column mappings, confirm units and scopes, inspect rejected records, then commit observations. Imported traces may contain customer information; access and retention controls apply before previews are generated. Partial acceptance identifies the rows accepted and rejected. Import never activates evidence packages or executes embedded code.

An unsupported stage can retain typed observations, attached specifications and notes. The application identifies whether the gap is description, modelling or evidence coverage. Supported independent domains may still compile. The user can request a qualification task, export the case or continue with bounded scenarios. Selecting a nearby workload family solely to bypass a gap is not offered as an automatic fix.

## 4 GUI layout and interaction specification

The desktop workspace uses a persistent case header, compact left navigation, central task area and an optional right inspector. At approximately 1280 CSS pixels and above, navigation occupies about 220 pixels and the inspector 320 pixels; the centre takes remaining space. These are initial layout targets subject to usability testing, not fixed viewport requirements. At narrower widths the inspector becomes a separate panel; on a phone the stage list precedes the form. No essential action is available only through a graph or hover.

[[FIGURE:builder]]

Figure 1 Workload builder layout showing phase navigation, selected stage fields and contextual review

The header provides case switching, scenario context and Save status. Phase navigation remains within Workload; it does not replace the case-level navigation. The primary action is Continue until Review, then Freeze and compile. Save is available independently. A persistent footer may hold these actions on large screens, but must not obscure validation messages or focused inputs at zoomed layouts.

### 4.1 Field components

| Component | Required behaviour | Server contract |
|---|---|---|
| Quantity field | Value, unit, scope and origin displayed together | Dimension validation and canonical conversion |
| Catalogue selector | Searchable eligible values, revision and compatibility explanation | Pinned catalogue ID and item ID |
| Range or distribution editor | Explicit bounds or named distribution with parameters | Bounds and distribution validation |
| Observation control | Known, estimated, assumed or unknown | Discriminated observation type |
| Schedule editor | Time zone, window, recurrence and overlap visible | Normalized interval and recurrence semantics |
| Stage editor | Stable stage identity and dependency inspection | Typed nodes, edges and graph validation |
| Diagnostic link | Message, consequence and direct field navigation | Stable code, severity, path and remediation |

Schema metadata determines field identity, allowed values, validation dependencies and conditional relevance. Presentation metadata determines grouping, label and help text. Layout is implemented by registered UI components, not arbitrary package-supplied scripts. Conditional expressions use a restricted declarative vocabulary. The server evaluates authoritative validation; browser validation provides immediate feedback only.

When a field becomes irrelevant it is retained as inactive draft data, with a visible explanation and explicit exclusion from the frozen effective input. Reactivating a stage restores values for review. Freeze returns an effective-input preview so that hidden stale values cannot alter compilation.

### 4.2 Analysis workspace

[[FIGURE:analysis]]

Figure 2 Analysis layout with configuration summary, resource views and a derivation inspector

Analysis opens with a short recommendation, installed GPU and node counts, operating scenario and material conditional results. Resource tabs show Compute, Memory, Storage, Networks and Tenancy. Additional tabs show Workload flow, Evidence and Assumptions. The selected run and its immutable revision remain visible. Charts are projections of returned series and facts, with units, scenario and evidence basis in their labels.

Selecting a fact opens a derivation inspector containing its value and scope, input observations, applied rules, evidence references and unresolved qualifications. The inspector links to source fields without editing the historical result. Edit input creates or opens a draft based on the revision; the user recompiles to obtain a new result.

Compute shows service demand, execution groups, placement, failure coverage and installed count. Memory separates per-device HBM fit from per-node host RAM and aggregate totals. Workload mix declares its denominator and period. Demand plots align time windows and never stack unlike units. Headroom is reported by resource, not as a single universal score. Lack of evidence is labelled unresolved rather than plotted as zero.

### 4.3 Comparison and handoff

Compare supports two or more selected immutable runs, with a compact initial two-run view. It separates changed workload inputs, changed knowledge or engine versions, and changed outputs. If multiple bases changed, it labels the comparison as a combined change and does not attribute the effect to one input. Users can create a controlled scenario fork to isolate a factor.

Handoff displays intended configuration and downstream design tool modelling configuration side by side, followed by the field mapping ledger. A B200 intended design may be projected to an explicitly selected supported modelling platform while preserving the B200 specification. The screen identifies affected network endpoints, node counts and other domains requiring reassessment. Substitution is a scoped decision, reusable for unchanged submissions under that decision.

Export produces an existing-field worksheet or payload plus companion specifications. Submit shows the target integration, experimental or finalized selection state, mapping limitations and existing authorization. It does not require an identical approval repeatedly. Returned downstream design tool results retain their own authority labels. Assessment lists verified, conditional, externally adjusted and unverifiable requirements; finalized selection never converts an unresolved domain into verified.

## 5 Data architecture and ownership

The frontend is a typed API client. Relational storage holds case ownership, drafts, immutable revisions, jobs and decisions. A content-addressed artifact store holds traces, package files, results and reports. Local deployments use the previously specified SQLite profile; shared deployments use PostgreSQL and an object-store adapter. Repository interfaces preserve the logical model across deployments. Authorization is enforced before any cached or stored content is returned.

The architecture separates authored state, frozen engineering inputs, calculated outputs and presentation state. Filters, panel expansion and selected tabs are presentation state. They do not change the compilation digest. Scenario policies, accepted assumptions and evidence selection are engineering inputs and do change it. Display-unit preferences may change formatting but cannot modify stored engineering values.

| Entity | Key relationships and content | Mutability |
|---|---|---|
| Case | Customer context, owner, membership, engagement policy | Versioned editable metadata |
| WorkloadDraft | Case, base revision, observations, stages and assets | Optimistic concurrency version |
| WorkloadRevision | Frozen effective input, schema version, source and decision references | Immutable |
| Observation | Field path, quantity or unknown, origin, source, scope and decision | Draft mutable; frozen with revision |
| ScenarioSet | Workload revision, schedules, failures, growth and variations | Immutable when used by a run |
| KnowledgeLock | EKB, CKP, dependencies, overlays and activation profile digests | Immutable |
| CompilationRun | Revision, scenario, lock, engine and solver identity | Lifecycle updates; input binding immutable |
| CompilationResult | Candidates, facts, diagnostics, derivation graph and chart series | Immutable artifact |
| Recommendation decision | Selected candidate, objective, actor and rationale | Append-only decision |
| NeonProjection | Intended configuration, target profile, payload and mapping ledger | Immutable |
| Submission and Assessment | Projection, external IDs, returned artifacts and domain checks | Lifecycle record plus immutable events |
| ReportManifest | Run, decision, projection, template version and artifact digest | Immutable |

### 5.1 Relationships and integrity

A Case has many drafts and revisions. Each revision contains applications, stages, edges, observations, service objectives and data assets with stable IDs. A scenario references one workload revision; a compilation binds that revision, one scenario set and one resolved knowledge lock. A result can contain multiple candidates. A recommendation selects one candidate, and a projection references that exact selection and target contract. Reports resolve these references from a frozen manifest.

Foreign keys and service validation prevent cross-case references and dangling stage edges. Tenant identity is enforced in every repository query and artifact lookup. Reused content digests do not imply cross-tenant access. Deletion follows retention policy; purged content leaves a tombstone that explicitly states replay is unavailable. Source documents and private traces are not copied into public evidence packs by default.

### 5.2 Quantity and observation representation

Quantities carry dimension, canonical unit, value, scope and horizon. Exact large integers and decimal quantities are encoded as strings where required. Browser Number arithmetic is not used for authoritative conversion. The API returns canonical values and display-ready representations or a governed conversion contract. Locale affects entry and presentation only; parsing ambiguity is reported before save.

A known observation has a typed value and source. An estimated observation may have bounds and an estimation basis. An assumed observation references the proposal and acceptance decision. An unknown observation contains a reason and optional clarification reference rather than a numeric placeholder. Derived facts reference a derivation node and are not editable intake observations.

```json
{
  "id": "obs_peak_rate",
  "field_id": "activity.transaction_rate",
  "state": "estimated",
  "quantity": {"value": "100", "unit": "request/s"},
  "scope": {"stage_id": "stage_llm", "scenario_id": "peak"},
  "source_ref": "source_customer_interview",
  "basis": "Customer supplied peak estimate"
}
```

Acceptance status is separate from origin: customer-supplied information can still require clarification, and an accepted assumption remains an assumption. Source references resolve to immutable import records or document spans where available; the interface does not invent a location for a manually entered estimate.

## 6 Knowledge driven interface contracts

The knowledge system uses the sixteen package families defined in the agreed package inventory. Intake and characterisation packages govern the builder. Demand, execution, platform, storage, networking, tenancy and resilience packages govern compilation. Recommendation and downstream design tool projection packages govern downstream decisions. Evidence governance constrains all uses. This is a logical organization; deployment may bundle related families.

A workload component descriptor contains component ID and version, field schemas, allowed edge types, conditional questions, supported modelling capabilities, evidence prerequisites, default proposals and diagnostic definitions. Its UI descriptor references registered widgets and localization keys. A capability endpoint returns the currently activated intersection of description, modelling and evidence support, with reasons for gaps. It does not expose unpublished facts to unauthorized users.

EKB facts and CKP rules are imported immutably. Integration overlays adapt them without editing source packages. Activation profiles independently authorize use. A resolver produces a lock before compilation, rejecting incompatible dependencies and ambiguous equal-authority facts. Catalogue availability alone does not prove sizing support. Historical runs continue to show their pinned package versions after newer catalogues become available.

The user may migrate a draft to a newer schema or package baseline through a preview showing field changes, defaults, compatibility gaps and expected invalidations. Migration creates a new draft or revision and never rewrites historical inputs. A withdrawn evidence record triggers an impact notice and an option to recompile; its previous use remains in the audit trail.

## 7 API and frontend state architecture

The application uses the existing technical architecture's proposed /api/v1 namespace. Routes below are proposed Anubis contracts to be formalized in OpenAPI. No route requires a browser-only calculation or an LLM. Server responses supply effective permissions and structured errors; hidden controls are not an access-control mechanism.

| Operation | Proposed interface | Behaviour |
|---|---|---|
| Discover builder support | GET /capabilities and /component-descriptors | Versioned descriptors and coverage reasons |
| Create and edit intake | POST /cases/{id}/drafts; PATCH /drafts/{id} | If-Match revision checks and canonical field response |
| Validate and clarify | POST /drafts/{id}/validate; POST /clarification-runs | Diagnostics with stable paths and ordered questions |
| Freeze | POST /drafts/{id}/freeze | Effective input preview bound to submitted draft version |
| Compile | POST /compilations | Immutable input binding and asynchronous job reference |
| Read analysis | GET /compilations/{id}; GET /artifacts/{id} | Authorized result and derivation projections |
| Compare and select | POST /comparisons; POST /recommendation-decisions | Explicit baselines and audited selection |
| Handoff | POST /neon-projections; POST /neon-submissions | Mapping ledger and durable submission state |
| Assess and report | POST /design-assessments; POST /reports | Frozen assessment and report manifests |

The browser maintains three stores: server-query state, unsaved field edits and ephemeral view state. Forms debounce saves but display Unsaved, Saving, Saved or Save failed explicitly. A saved indicator is shown only after acknowledgement. A pending edit is flushed before navigation or freeze; failures retain the buffer and offer retry or local export where policy permits. Sensitive drafts are not persistently cached in browser storage by default.

Concurrent edits receive a version conflict with the latest draft version. The UI compares field-level changes and offers reapplication after review; it does not overwrite another user's draft. Changes made while a run executes create a later draft and never retarget that run. Cancellation is requested cooperatively; a result committed before cancellation remains completed and the UI explains the race.

Jobs expose queued, running, cancel requested, succeeded, failed and cancelled. Progress uses actual pipeline stages; percentage completion is shown only when a defensible denominator exists. The client reconnects using the job ID and polls with bounded backoff or consumes authenticated events. A network timeout during downstream design tool submission becomes outcome unknown until reconciled, not an invitation to create a duplicate design.

## 8 Status and explanation model

| Dimension | Values | Display rule |
|---|---|---|
| Description completeness | Incomplete, valid with unknowns, complete | Applies to input contract only |
| Coverage | Supported, partial, unsupported | Separate description, modelling and evidence coverage |
| Evidence basis | Measured, predicted, reference-derived, bounded, insufficient | Applies to each material fact |
| Feasibility | Pass, fail, conditional, unresolved | Does not inherit job success |
| Selection | Experimental, selected, finalized | Does not imply engineering verification |
| Projection | Direct, substitution, partial | Identifies information loss and external obligations |
| Assessment | Verified, conditional, external adjustment, unverifiable | Applies per requirement or domain |

Statuses have text and icons as well as color. There is no overall confidence percentage. An empty result distinguishes no candidates, invalid input, incomplete evidence, failed execution and insufficient permissions. A structured partial result is a legitimate compiler output and can still be inspected and reported.

Explanations use deterministic templates populated from facts and derivation references. An optional agent explanation is labelled assisted and links to those same facts. It cannot replace units, qualification labels or evidence status. A failed constraint can only change through a new governed input, rule or evidence revision, not by editing report prose.

## 9 Reporting and the customer review experience

The customer report begins with the recommended configuration and supported operating envelope. The architect view adds sizing derivation, alternatives and mapping details. The engineering appendix contains observation IDs, rule IDs, evidence references and package lock identifiers. These are presentation profiles of one result, not independent computations.

Report visuals include an annotated workload flow, aligned demand timelines, compute placement build-up, per-device memory allocation, constraint tables and controlled scenario comparisons. Scenario bands are labelled as assumption ranges unless a statistical interpretation is justified. Storage capacity tiers remain separate. GPU-hour mix identifies platform, period and whether it represents allocated or consumed time.

A report manifest binds the workload revision, scenarios, result, selected candidate, assessment and rendering template. Exported Word and PDF pagination may differ without changing semantic results. Machine-readable output includes exact values and provenance. Generating a report does not approve an architecture, publish customer data or authorize procurement. The customer acceptance record is separate from technical verification.

## 10 Accessibility security and operational behaviour

The proposed accessibility target is WCAG 2.2 AA, to be verified during implementation rather than asserted as achieved. Use labelled native controls, keyboard traversal, visible focus, accessible error summaries and text alternatives for all charts. Provide table equivalents for graphical data and list-based editing for graphs. Announce save and validation changes without repeatedly interrupting screen-reader users. Verify reflow at 320 CSS pixels and 200 percent zoom, including the optional inspector and sticky actions.

Case membership and operation scopes are checked server-side. Curator and activation privileges are distinct from ordinary scenario editing. Agents act under scoped identities. Imports, source notes and retrieved documents are untrusted content and cannot grant permissions or modify rules. Secrets remain in the integration credential store and never appear in descriptors, reports or client logs.

The GUI uses server-backed pagination and filters for large case and evidence collections. Large traces are summarized on the server, with aggregation scope visible. Graph complexity thresholds trigger a list representation rather than clipping nodes. Performance budgets should be established with representative case sizes before implementation acceptance; this document makes no measured latency claim. Telemetry records operation timings and diagnostic codes without raw customer prompts or traces by default.

If the knowledge service is unavailable, users can read cached authorized immutable results where supported, but cannot resolve new locks. If downstream design tool is unavailable, Anubis sizing and manual exports remain usable. If an agent service is unavailable, the complete structured workflow remains usable. Local unsaved edits are preserved in the active session during recoverable service failures, with their unsaved status explicit.

## 11 Acceptance scenarios and delivery sequence

| ID | Acceptance scenario | Required result |
|---|---|---|
| UX01 | Complete a supported inference case without an LLM | Intake, sizing, explanation, report and export succeed |
| UX02 | Leave a material context-length input unknown | No fabricated default; conditional or unresolved outcome |
| UX03 | Change a template stage and disable a dependent field | Effective-input preview excludes inactive values |
| UX04 | Edit a draft concurrently in two sessions | Conflict detected; no silent lost update |
| UX05 | Change a draft while a compilation runs | Result stays bound to original frozen revision |
| UX06 | Import malformed and ambiguous-unit rows | Preview identifies rejects; accepted rows remain traceable |
| UX07 | Select an unsupported component or model | Saved case and explicit coverage gap, not forced classification |
| UX08 | Inspect a GPU recommendation | Trace reaches observations, rules and qualified evidence |
| UX09 | Project intended B200 hardware into a downstream design tool substitute | Intended specification and affected domains remain visible |
| UX10 | Lose connectivity during downstream design tool submission | Outcome reconciled before another write |
| UX11 | Navigate with keyboard and inspect a chart | Equivalent form and tabular paths remain available |
| UX12 | Compare runs with changed knowledge and demand | Combined change disclosed; no false single-factor attribution |
| UX13 | Withdraw an evidence record used by a prior result | Impact notice; original result retained and labelled |
| UX14 | Attempt a cross-case artifact read | Access denied before content or cache disclosure |
| UX15 | Finalize a conditional recommendation | Finalization preserves conditional engineering status |

First deliver the case shell, descriptor-driven intake, immutable revision lifecycle and an inference analysis vertical slice. Next add structured imports, scenario comparison and full derivation inspection. Then extend workload families and introduce the existing-field Design handoff and assessment workflow. Knowledge administration and activation controls must exist before external packages can influence recommendations. Optional agent assistance follows API parity and does not change calculation authority.

Before implementation, record architecture decisions for the descriptor vocabulary, effective-input normalization, status dimensions, graph/list equivalence, draft concurrency and package migration. Product acceptance requires representative consultant and architect walkthroughs in addition to automated contract tests. The essential success measure is whether users can supply defensible inputs, understand the resulting configuration and identify what still requires validation.

## 12 Design basis and related specifications

This specification consolidates the agreed Anubis workload-builder, knowledge-package, reporting and deterministic-operation decisions through 24 October 2026. It supplements the Anubis Workload Sizing Framework and Technical Solution Architecture version 1.0, dated 27 September 2026. Proposed endpoint and schema additions remain Anubis-specific and do not expand downstream design tool intake.

The CKP/EKB separation follows the previously inspected downstream design tool ADR 0004 on CKP-driven compiler development and ADR 0013 on immutable knowledge and advisory authority separation. Their use here is a design precedent, not a claim of shared runtime activation. Detailed downstream design tool mappings must be qualified against the actual target deployment before release; the earlier source inspection is not a current live compatibility test.

## Saved-result explanation

Calculation results and Design handoff offer **Explain this to me**. A modal presents a deterministic option and approved model connections. Corporate data policy is the default. The user explicitly declares public or fictional data before using a public-only provider. Active status, disabled duplicate submission, saved history and text download make progress and persistence visible. Six short sections explain outcome, compute, memory, storage, networks and next steps. The calculation and handoff remain immutable. Missing inputs and failed feasibility are explained without presenting an invented recommendation.
