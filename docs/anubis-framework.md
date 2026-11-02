# Anubis AI Factory Workload Sizing Framework

## A deterministic method for translating incomplete workload descriptions into infrastructure recommendations

Version 1.0 | 27 September 2026 | Methodology paper

## Abstract

AI infrastructure planning often begins with incomplete business descriptions rather than measurable computational requirements. Customers may know their intended applications, users and service expectations while remaining uncertain about models, concurrency, data movement or deployment arrangements. This paper defines Anubis, a standalone workload-sizing framework that converts such descriptions into concrete AI factory requirements through consultant-assisted elicitation, typed workload modelling, governed performance evidence and deterministic constraint evaluation. The method separates customer intent, normalized demand, intended infrastructure configuration and projection into an architecture tool. It jointly evaluates compute, memory, storage, communication, host resources, tenancy and operational continuity. Recommendations identify a preferred configuration, binding constraints, alternatives and validation obligations. Anubis can describe platforms beyond the current coverage of downstream AI Factory design tool or process; a separate adapter maps selected scenarios into downstream design tool's unchanged intake, preserving user-selected substitutions and externally implemented specifications. An API exposes all operations, while optional agents support elicitation and iteration without becoming numerical authorities. The contribution is a reproducible synthesis and decision method grounded in established performance evaluation and benchmark practices. Worked examples are synthetic arithmetic demonstrations, not empirical performance results. An evaluation protocol is specified for subsequent validation against representative workloads.

Keywords: AI infrastructure; workload characterization; capacity planning; deterministic compilation; GPU clusters; evidence provenance; architecture automation

## 1 Introduction and contribution

An application requirement such as serving several thousand users does not determine a GPU count. The missing relationships include active-user behavior, model quality, request shape, service deadlines, sharing policy and the data paths that support execution. A useful sizing application must help a consultant resolve those relationships and then deliver an engineering recommendation understandable to a customer.

Anubis answers: what configuration is required, why is it required, and which variations remain feasible? Its leading output is a recommendation across GPU platform and count, memory placement, host resources, storage tiers, internal fabrics, external connectivity and tenancy. Supporting calculations are available without forcing the customer to reconstruct the recommendation from a resource spreadsheet.

The method contributes four linked elements. First, it gives incomplete inputs an explicit status and a controlled path to refinement. Second, it uses workload graphs and operating scenarios to translate application behavior into measurable demand. Third, it evaluates complete execution configurations against joint constraints and frozen evidence. Fourth, it preserves the intended configuration independently of its representation in a downstream architecture tool. This separation permits broad sizing coverage without changing an existing architecture intake.

This is a finalized methodological baseline for Anubis, not a claim of an implemented or empirically validated system. The formulas and decision policies below define the intended method. Accuracy claims require the evaluation described in Section 12. The framework is not presented as an existing universal industry sizing standard.

## 2 Scope and authority boundaries

Anubis owns workload intake, characterization, demand expansion, performance prediction, resource sizing, configuration recommendations, evidence management and requirement assessment. downstream AI Factory design tool or process owns architecture compilation using its usual intake parameters. No additional downstream design tool input parameter is required by this framework.

The complete workflow is customer intent, consultant clarification, optional agent-assisted structuring, Anubis sizing, architect or agent scenario selection, downstream design tool architecture compilation, and customer review. Revisions can return to any upstream stage. Agents may ask questions and invoke APIs, but numerical conclusions come from Anubis's governed engine. Humans select business priorities, accept assumptions and authorize finalization or substitutions according to the engagement policy.

Anubis is not restricted to platforms that downstream design tool currently represents. An intended B200 configuration, for example, can remain authoritative in Anubis while a user chooses a supported B300 or GB300 modelling platform in downstream design tool. The substitution is a projection decision, not a revision of the intended hardware. Host specifications and other unrepresented requirements remain available for external design and implementation.

This distinction does not confer physical equivalence. Differences in node count, NIC population, topology, failure domains or scale-up behavior can affect the usefulness of individual downstream design tool outputs. Anubis records applicability by design domain rather than rejecting the whole workflow or treating the whole design as verified.

## 3 Established foundations and their use

ITU-T F.748.26 provides a framework for evaluating AI cloud platforms. Anubis adopts its configuration, workload, evaluation and reporting structure as an evidence-management foundation; it does not derive a universal sizing algorithm from that document. A clause-level applicability matrix distinguishes mandatory provisions from recommendations before any conformance claim is made [1].

MLPerf supplies standardized inference, training and storage benchmarking practices and results. Anubis uses applicable metrics and configuration-specific evidence, while preserving the distinction between official benchmark results and customer-specific qualification. Adapting a workload for customer relevance does not automatically preserve benchmark compliance [2–4].

NVIDIA reference architectures constrain corresponding platform profiles. AIConfigurator can provide versioned inference predictions and candidate configurations; these remain predictions unless separately measured [5,6]. Research on PagedAttention and activation recomputation shows why runtime memory management and training execution choices materially affect capacity and cannot be reduced to parameter count alone [7,8]. ISO/IEC 22237 informs the facilities boundary; its general scope excludes IT and telecommunications equipment selection and configuration [9].

The synthesis, uncertainty treatment, scenario policies, selection objectives and downstream design tool projection defined here are Anubis engineering decisions. Source attribution must not convert a locally chosen policy into a claimed standards requirement.

## 4 Formal model and input semantics

Let W be a normalized workload specification, S the operating-scenario set, K a frozen knowledge pack, P the selection and reserve policy, and V the compiler version. The semantic compilation is:

    C = Compile(W, S, K, P, V)                                      (1)

C contains workload characterization, resource requirements, candidate assessments, a preferred intended configuration and a derivation graph. A separate projection uses the selected configuration c, target intake contract T and approved mapping decisions A:

    J = Project(c, T, A)                                           (2)

J contains only existing downstream design tool intake values. A companion mapping ledger remains in Anubis. Changing T or A does not change the historical meaning of c. Repeating Equation 1 with identical semantic inputs must produce identical semantic outputs; timestamps and execution identifiers are excluded from that claim.

### 4.1 Values and uncertainty

Every material input has a path, value or unresolved marker, unit, scope, source, origin status, owner and revision. Origin status is supplied, measured, assumed or derived. Assumption acceptance is separate from origin: an accepted assumption is still an assumption. Quantities can be scalars, bounded intervals, histograms or trace references. A missing value is never represented by zero.

Scopes identify whether a value is per request, model, replica, device, node, tenant, pool or factory and the time horizon to which it applies. Storage distinguishes logical live bytes, required usable capacity and raw media. Rates distinguish bytes from bits and decimal from binary units. Customer demand uncertainty, prediction error and operational reserve are recorded separately to prevent repeated multiplication of margins.

Intervals without a probability model are scenario bounds, not confidence intervals. Statistical prediction intervals require documented calibration. Anubis does not infer an undocumented joint distribution from independently supplied percentiles.

### 4.2 Minimum intake and progressive disclosure

The first interview collects application purpose, quality constraints, user or job scale, acceptable response or completion time, data size and change rate, sharing expectations, continuity objectives and planning horizon. The questionnaire then exposes only relevant technical branches.

| Intake branch | Required characterization | Refinement when material |
| --- | --- | --- |
| Interactive inference | Model or quality-qualified shortlist; activity rate; latency goals | Joint prompt/output distributions, burst duration, cache behavior |
| Batch inference | Work volume, release times and deadlines | Batching, retries, priority and overlap with online service |
| Training and tuning | Model, data volume, method and completion window | Optimizer, batch, sequence length and parallelism |
| RAG and agents | Workflow stages, visits and dependency order | Branches, tool calls, retries and context growth |
| Storage and movement | Working set, retention, ingestion and locations | File sizes, metadata, checkpoint and load windows |
| Tenancy and operation | Trust boundaries, guarantees and scheduling policy | Isolation enforcement, placement and interference evidence |

Two routes are supported. A trace-led route derives distributions from representative telemetry with recorded coverage. An interview-led route uses named assumptions and low, central and high scenarios. Narrative extraction proposes fields for review; it does not directly become a sizing result.

The next-question policy ranks unresolved inputs by whether they block a decision and by the change in the preferred configuration under plausible values. With no justified probability distribution, this is sensitivity ordering rather than expected information gain. A stable tie-breaker makes questionnaire ordering reproducible.

### 4.3 Readiness is scoped

A case may support a storage recommendation while compute evidence remains insufficient. Readiness is evaluated by output domain: exploratory, conditionally resolved or resolved within the stated evidence domain. The interface leads with the best supported recommendation and identifies specific missing facts, rather than suppressing all useful results because one domain is incomplete.

## 5 Workload characterization and demand expansion

### 5.1 Application graphs

Represent each application as a directed graph of inference, embedding, retrieval, CPU processing, training, transfer and external-service stages. Edges carry order, payload, branch conditions and fan-out. Cycles require finite iteration bounds or an explicitly qualified stochastic model. Unknown agent loops cannot be silently assigned unlimited or zero cost.

For application a with transaction rate lambda_a and expected visits v_aj to stage j, stage demand is:

    lambda_j = sum_a(lambda_a * v_aj)                              (3)
    input_tokens_j/s = lambda_j * E[input_tokens_j]                 (4)
    output_tokens_j/s = lambda_j * E[output_tokens_j]               (5)

These equations describe mean work. Latency evaluation retains distributions, dependency order and correlations. For independent retry probability p with at most k retries, expected attempts are sum from i=0 to k of p^i; correlated failures or load-dependent retries require scenario traces or a richer model. Stage-level p95 latencies are not added to claim an application p95.

Open-loop traffic specifies external arrival rate. Closed-loop traffic specifies active users, think time and response-dependent submission behavior. Converting one to the other requires an explicit behavioral assumption; counting both as independent demand double-counts work. Stable-system concurrency can be checked using mean arrival rate times mean time in system, but this consistency check does not establish tail latency.

### 5.2 Training and inference proportions

The headline mix is projected occupied GPU-hours over a named horizon and selected hardware scenario:

    inference_share = inference_GPU_hours / total_GPU_hours        (6)

Report training, inference and other GPU work, plus shared overhead and unallocated reserve separately. For heterogeneous hardware, report shares by pool unless a justified normalization exists. GPU-hours are configuration-dependent; therefore the initial workload classification is qualitative and the numerical mix is refined after sizing. Peak allocation and fabric-dominating workload are reported separately from time-averaged shares.

### 5.3 Operating scenarios

Scenarios include normal operation, declared peaks with duration, batch overlap, cold model starts, checkpoint coincidence, maintenance, failure recovery and growth horizons. Demand aggregates according to the schedule and correlation assumptions. Summing every workload's independent maximum is a named conservative scenario, not the default interpretation of a mixed portfolio.

Growth is applied to its actual driver. User growth, context growth, data retention and model replacement may have different trajectories. A single compound annual factor is permissible only as an explicit simplification. Design capacity, future expansion and operational reserve remain distinguishable.

## 6 Joint resource resolution

### 6.1 Candidate representation and selection

A candidate specifies GPU SKU and variant, node platform, runtime, quality-approved precision, parallelism, replica placement, admission policy, memory tiers, storage services, fabric classes and tenancy constraints. The engine evaluates candidates against every applicable scenario and hard constraint. It returns pass, fail, conditional or unknown with binding constraints and reasons.

The feasible set contains candidates meeting all hard requirements within their evidence domain. Among those candidates, the engine applies the declared objective: for example verified cost, energy, or hardware quantity within one platform family. Missing prices prohibit a lowest-cost claim. Cross-platform alternatives with incomparable objectives remain on a Pareto frontier. Stable identifiers break equal-score ties without pretending the tie-breaker has engineering significance.

Compute, storage and communication evaluation is coupled. A storage bottleneck can reduce achieved training rate; a different parallelism arrangement can alter E–W traffic and memory placement. The engine either evaluates each complete candidate consistently or uses a bounded, deterministic iteration with conservative resource updates and an explicit unresolved result on non-convergence. It cannot accept separately feasible components whose combined operating point has not been evaluated.

### 6.2 Inference compute and GPU memory

The sizing unit is a complete serving replica, or a qualified prefill/decode configuration, at a defined request distribution and service objective. GPU TFLOPS and HBM bandwidth support screening bounds; they do not independently establish tail-latency-compliant capacity.

For each device, memory feasibility requires:

    M_weights + M_KV + M_activations + M_workspace
      + M_runtime_reserve <= M_usable_device                       (7)

For conventional attention with uniform layers, the unsharded KV payload is approximated by:

    M_KV = 2 * layers * KV_heads * head_dimension
             * bytes_per_element * sum_i(retained_tokens_i)       (8)

Sharding, replication, block allocation, prefix sharing, sliding windows and quantization metadata modify the realized allocation. Hybrid and latent-attention architectures require their own memory models. MoE weight storage reflects resident experts rather than only active parameters. Host offload and storage offload create new bandwidth and latency requirements; they are not free extensions of HBM. Runtime-dependent cache management is a material sizing variable [7].

Let q_c be a replica's qualified request rate under the required latency constraints. For a planning admission factor u, if not already included in q_c:

    healthy_replicas = ceil(design_request_rate / (q_c * u))        (9)

The capacity must satisfy TTFT, token-generation and completion objectives simultaneously. Published throughput without matching latency conditions is inadequate. Disaggregated prefill and decode require separate pool sizing plus qualified KV-transfer capacity. Additional replicas are admitted only while routing and shared dependencies remain within their measured or calibrated limits.

### 6.3 Training and tuning

Training candidates satisfy both per-device memory and completion deadlines. A first-order dense-transformer screening estimate is work approximately 6 * parameters * training_tokens. This estimate excludes important architecture and sequence-dependent terms and is not the final estimator for MoE, multimodal, reinforcement learning or arbitrary fine-tuning.

    job_time(c) = work / achieved_compute_rate(c)
                    + overhead_excluded_from_rate(c)              (10)

Measured job or step throughput is preferred when applicable. MFU, communication, input stalls and checkpoint costs must not be deducted twice. Candidate qualification fixes optimizer, precision, batch, sequence length, accumulation, recomputation and parallelism. Memory includes weights, gradients, optimizer state, activation peaks and runtime workspace. LoRA reduces trainable state but does not make all base-model memory or computation disappear. Research on recomputation and parallelism supports configuration-specific treatment [8].

Job admission accounts for start deadlines, preemption cost, checkpoint restoration and the availability of a feasible gang placement. Total GPU-hours alone cannot prove a set of jobs is schedulable within its windows.

### 6.4 CPU memory and local storage

CPU demand is estimated from measured core-seconds per operation on a defined CPU class:

    cores >= sum_j(rate_j * core_seconds_j) / CPU_utilization      (11)

The result is supplemented by memory-bandwidth, NUMA, PCIe and NIC-processing constraints. Host RAM is built from concurrent processes, pinned buffers, data loaders, model staging, caches and offloaded state. Local storage covers resident artifacts, image cache, scratch, checkpoint staging and logs, including write endurance and load bandwidth. Per-node minima accompany aggregate quantities.

Shared retrieval, database, orchestration and monitoring services are separate resource pools. Their requirements are not hidden inside a universal CPU-to-GPU multiplier. Platform minimums can be used where documented, but must remain distinct from measured workload demand.

### 6.5 Storage services

Storage is resolved by data lifecycle and access semantics. Object repositories, active file data, checkpoints, vector indexes, local caches and optional KV offload are separate services even when one system implements several. POSIX semantics, a client protocol and a physical storage product are distinct attributes.

    checkpoint_write_Bps = concurrent_checkpoint_bytes / save_s   (12)
    model_load_Bps = concurrent_uncached_model_bytes / load_s      (13)
    required_usable_bytes = live_retained_and_staged_bytes
                              / (1 - free_space_fraction)         (14)

Required usable capacity excludes raw protection overhead; a product realization adds that separately. Duplication, compression and cache benefits are applied only with justified ratios. A cache-cold or miss-rate stress scenario prevents optimistic hit rates from becoming hidden requirements.

Read and write rates, IOPS, metadata rates, request sizes, tail latency and client concurrency are evaluated jointly. Simultaneous operations are added according to the scenario. For asynchronous checkpoints, both local staging occupancy and sustained drain capacity must remain bounded. Applicable MLPerf Storage evidence assists qualification but does not replace this customer data-flow model [4].

Vendor qualification is a predicate over a named product, software release, hardware configuration, protocol and workload. Outcomes are qualified, conditionally qualified, fails a stated requirement, or evidence insufficient. A WEKA or VAST recommendation and a PowerScale exclusion require evidence at that scope. Absence of evidence cannot justify excluding an entire vendor. Filesystem, protocol, usable capacity and performance requirements are always emitted independently of the shortlist.

### 6.6 Fabrics and external connectivity

Anubis builds a directional traffic graph for scale-up communication, E–W collectives, storage, frontend and external flows. Each edge carries volume, rate, concurrency, latency budget and failure behavior. Screening line rate is:

    line_bits/s >= 8 * payload_bytes/s / (efficiency * utilization) (15)

Collective timing, small-message latency, incast, topology and oversubscription still require applicable evidence. Aggregate line rate alone cannot prove training efficiency or an inference SLO. Dedicated and converged fabrics are evaluated as alternatives under simultaneous traffic, isolation and failure conditions. InfiniBand is required only where qualified alternatives fail a binding requirement; otherwise it can be preferred or one of several feasible technologies.

External bandwidth derives from source volume and transfer window, interactive payloads, replication and external services. Latency derives from the application's dependency budget and source location, not from bandwidth arithmetic. Private connectivity, internet access, ownership and security-edge policy need customer or architect decisions. The recommendation states usable directional rate, relevant RTT bound, redundancy and connection type where resolved.

### 6.7 Tenancy and continuity

Single tenancy, multi-tenancy and a neocloud business model are separate concepts. Feasibility depends on trust boundaries, minimum guarantees, placement, performance interference, isolation mechanisms and governance. A workload may require exclusive nodes during a training window while other pools remain shared. Factory-wide exclusivity is concluded only when the scope of the constraints warrants it.

For each declared failure scenario f, surviving capacity and placement must meet that scenario's service requirement:

    qualified_surviving_capacity(c, f) >= required_demand(f)        (16)

The scenario also includes recovery time, queued work, restoration bandwidth and any approved degraded-service objective. An availability percentage alone does not determine spare GPUs. Resilience additions, ordinary admission reserve and future growth are separately recorded. Explicit failure-domain placement avoids treating an extra replica on the failed node as resilience.

## 7 Evidence and uncertainty governance

The performance knowledge pack contains measurement records, calibrated prediction models, platform compatibility, storage and network profiles, rule definitions and applicability limits. Records retain configuration fingerprints, source identifiers, dates, workload distributions, quality criteria, duration, repetitions and supporting artifacts. Selection is deterministic: hard compatibility checks precede proximity or preference ranking.

Evidence basis is measured, directly supported, derived, bounded or insufficient. Feasibility is pass, fail, conditional or unknown. These are independent: a measured result can be an incompatible measurement, and a derived result can be adequate within validated bounds. Evidence quality is assessed per requirement rather than averaged into a misleading global confidence score.

Interpolation is permitted only by a named rule within a calibrated region and across declared dimensions. Hardware generation, model architecture, precision or topology changes require their own justification. Extrapolation is separately marked and may support only an exploratory bound. Public benchmark leadership does not establish superiority for an unrelated workload.

Each conclusion links to a derivation graph containing input paths, rule versions, evidence identifiers, arithmetic, rounding and binding constraints. An assumption change invalidates dependent conclusions and creates a new compilation. Historical results remain replayable with their frozen packs. An evidence withdrawal flags affected results for review without rewriting their history.

## 8 Recommendation and rationalised alternatives

The customer-facing report leads with the recommended configuration. It states the workload mix and denominator; GPU type, count and placement; HBM, host and local-cache requirements; storage service capacities and performance; network separation and technology; external connectivity; and tenancy conditions. Each decision includes a short explanation and the constraint that determined it.

Alternatives are complete scenarios with explicit concessions. For example, a slower batch deadline may reduce GPUs, or a non-overlapping checkpoint schedule may make a converged fabric feasible. Anubis does not change quality, isolation or resilience requirements merely to obtain a cheaper answer. Cost claims require current, comparable commercial evidence pinned to the scenario.

A recommendation is resolved within its evidence domain, conditional on named obligations, or exploratory. This status accompanies the concrete answer; it does not replace the answer with a list of generic caveats. A customer can select a conditional proposal while its outstanding validation remains visible.

## 9 Projection into the unchanged downstream design tool intake

Projection has three modes: direct mapping, user-selected substitution and partial mapping. The adapter emits only the existing intake contract. All workload graphs, evidence, actual server details, substitutions and unmapped requirements stay in Anubis. Future downstream design tool support expands projection coverage without shrinking or redefining Anubis's intended configuration model.

For a B200 intended platform and a B300 modelling selection, the mapper retains both configurations and compares node count, GPUs per node, NIC endpoints, storage clients, scale-up domains and failure domains. It does not assume equal GPU count means equal network demand. The user can use applicable storage, connectivity or tenancy designs and handle physical compute outside the design tool.

Each returned design domain is classified as verified against available requirements, conditionally reusable, requires external adjustment, or unverifiable from returned data. The complete substituted design must not be described as a verified implementation of the intended hardware when only some domains have been assessed.

Projection also handles semantic loss. Two storage tiers cannot be silently collapsed into one capacity field, nor can rounded GPU targets be treated as unchanged demand. A mapping ledger records conversions, omitted details and the domains affected. Experimental submissions remain separate from selected final submissions. No extra ledger fields are inserted into downstream design tool requests.

## 10 API and agent assisted design loop

Every Anubis operation is exposed by an API, including intake, clarification, scenario creation, evidence administration, compilation, comparison, selection, projection, reporting and integration. The GUI uses those operations. Optional MCP tools are wrappers around the same contracts, not alternative calculation paths.

An agent can structure a customer narrative, request missing information, invoke scenarios and explain differences. Proposed values retain their origin and acceptance status. External documents and tool outputs cannot change engineering policy or authority. Human and agent actions share traceable authorization and revision controls.

An optional downstream design tool adapter submits projected values through existing API operations and retrieves results. Anubis assesses those results against the intended requirements and returns revisions or acceptance obligations. Iteration is bounded by declared scenario count, compute or cost budget and stop conditions. It cannot converge by silently relaxing customer requirements. Finalization, customer acceptance and engineering verification are different states.

## 11 Worked synthetic example

This example demonstrates arithmetic and decision semantics only. All performance and operating assumptions are illustrative and are not results for B300, B200 or any named vendor product.

Assume 1,000 active users each initiate one transaction per minute during a base period. The declared busy-period multiplier is two and each transaction visits a local LLM three times. Mean prompt and output sizes are 2,000 and 400 tokens. Equations 3–5 yield 33.33 transactions/s, 100 LLM calls/s, 200,000 input tokens/s and 40,000 output tokens/s. Token distributions and service objectives must still be supplied for performance qualification.

Assume a hypothetical four-GPU replica has been qualified at 12 calls/s for exactly that request distribution and the required SLOs. A separate admission factor of 0.8 yields 9.6 calls/s per replica. Eleven healthy replicas are required. An eight-GPU node hosts two replicas. Six nodes supply twelve replicas, but losing one leaves ten and only 96 calls/s. Seven nodes provide fourteen replicas, leaving twelve and 115.2 calls/s after one node fails. The candidate therefore installs 56 GPUs. This establishes steady surviving capacity, not failover time; recovery still needs qualification.

Now suppose data ingestion transfers 20 decimal TB in four hours. Payload rate is 1.389 GB/s, or 11.11 Gbps. With protocol efficiency 0.90 and planned utilization 0.70, the line-rate requirement is 17.64 Gbps. A nominal 25 Gbps option is a candidate if endpoint and WAN conditions support it; the arithmetic establishes no RTT guarantee.

Suppose the object tier has 1.2 PiB of live and retained data and a 20% free-space policy. It requires 1.5 PiB usable capacity. A file tier with 0.24 PiB requires 0.30 PiB under the same policy. Two simultaneous 2 TiB checkpoints completed within 120 seconds require 34.13 GiB/s of durable write throughput before additional simultaneous traffic. These facts do not identify a vendor until a specific configuration is evaluated.

| Result | Illustrative value | Remaining qualification |
| --- | --- | --- |
| Peak local inference | 100 calls/s | Distribution and SLO match |
| Installed compute | 56 GPUs on 7 nodes | Real platform evidence and failover behavior |
| Ingestion line requirement | At least 17.64 Gbps | Source, path, latency and continuity |
| Object usable capacity | 1.50 PiB | Protection realization and access performance |
| File usable capacity | 0.30 PiB | Read, metadata and client behavior |
| Checkpoint write demand | 34.13 GiB/s | Durable concurrent performance |

The example intentionally does not infer training percentage, InfiniBand necessity, vendor exclusion or factory-wide exclusivity. Those conclusions require inputs absent from the example. A complete customer case would resolve them through the same process rather than fill them with defaults disguised as measurements.

## 12 Evaluation protocol

Validation must establish reproducibility, predictive usefulness and decision quality. The test corpus should include short and long context inference, bursty arrivals, cache-cold starts, MoE, training and tuning, mixed portfolios, checkpoint overlap and failure scenarios. Split data by configuration families where possible so held-out evaluation does not merely repeat calibration points.

Compare Anubis with throughput-only sizing, theoretical-compute sizing and a qualified expert baseline. Report throughput and latency prediction error, memory fit failures, deadline violations, false-feasible recommendations, overprovisioning and unresolved coverage. Tail latency and false feasibility deserve separate reporting; average error can conceal expensive failures.

Before a calibration release, declare workload-specific error limits, acceptable risk and evidence-domain boundaries. No numerical accuracy target is claimed in this paper. Repeated runs characterize measurement variation. Tests should examine unknown handling, correct unit conversion, reserve accounting, failure placement and deterministic candidate ranking.

Sensitivity studies remove context distributions, topology or data-flow information to measure their effect. Projection tests compare intended and modelled platform endpoints, confirm that no new downstream design tool fields are emitted, and check that unsupported physical details survive in the Anubis dossier. A mocked downstream design tool result cannot establish real integration compatibility; deployed contract tests are a separate gate.

## 13 Limitations and conclusion

The method depends on representative inputs and evidence. Proprietary models, changing runtimes, novel attention schemes and unmeasured co-tenancy can remain outside its qualified domain. Deterministic execution guarantees repeatability of decisions, not truth of assumptions. Correlation, rare failures and agent behavior can be expensive to characterize. Model quality remains an application acceptance condition, not a result of hardware sizing.

Anubis provides a structured route from incomplete intent to a concrete configuration, with explainable alternatives and preserved uncertainty. Its independent configuration model supports future hardware and external physical specifications, while a constrained adapter keeps downstream design tool's current intake unchanged. The empirical evaluation remains a necessary next stage before claiming predictive accuracy or production qualification.

## References

[1] ITU-T. Recommendation F.748.26, Technical specification for artificial intelligence cloud platforms Performance evaluation. February 2024. https://www.itu.int/rec/T-REC-F.748.26-202402-I/en

[2] MLCommons. MLPerf Inference Datacenter benchmark and results. https://mlcommons.org/benchmarks/inference-datacenter/

[3] MLCommons. Benchmark suites and inference submission guidance. https://mlcommons.org/benchmarks/ ; https://docs.mlcommons.org/inference/submission/

[4] MLCommons. MLPerf Storage benchmark and rules. https://mlcommons.org/benchmarks/storage/ ; https://github.com/mlcommons/storage/blob/main/Rules.md

[5] NVIDIA. NVIDIA NVL72 AI Factory Enterprise Reference Architecture. https://docs.nvidia.com/enterprise-reference-architectures/nvl72-ai-factory/latest/abstract.html

[6] NVIDIA and AI Dynamo contributors. AIConfigurator. https://github.com/ai-dynamo/aiconfigurator

[7] Kwon, W., et al. Efficient Memory Management for Large Language Model Serving with PagedAttention. SOSP 2023. https://doi.org/10.48550/arXiv.2309.06180

[8] Korthikanti, V., et al. Reducing Activation Recomputation in Large Transformer Models. 2022. https://doi.org/10.48550/arXiv.2205.05198

[9] ISO/IEC. ISO/IEC 22237-1:2021, Data centre facilities and infrastructures General concepts. https://www.iso.org/standard/78550.html

Online sources accessed 27 September 2026. Mutable benchmark and software sources must be pinned to release or commit identifiers when admitted into a production knowledge pack.
