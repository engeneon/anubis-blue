# Anubis Customer Workload Stories
## Three scenarios for structured discovery and deterministic sizing

Version 1.0 | 24 October 2026

## Purpose and use

These three fictional customer stories illustrate how a consultant can develop business requirements into structured Anubis workload descriptions. Meridian Industrial Services preserves the initial maintenance-assistant example. Harbor Inference Cloud introduces a shared commercial inference service. Aster Language Research introduces a dedicated training programme with periodic evaluation and checkpoint recovery.

All company names, volumes and operating requirements are illustrative. Within each story, confirmed means agreed by the fictional customer, not independently measured. Estimates and unresolved inputs remain explicit. The arithmetic demonstrates application demand only; no GPU count, vendor qualification or production performance is claimed.

| Scenario | Principal workload | Main sizing challenge |
|---|---|---|
| Meridian Industrial Services | Private interactive assistant with overnight processing | Latency, context memory and scheduled resource sharing |
| Harbor Inference Cloud | Multi-tenant model-serving service | Tenant guarantees, burst correlation and failure capacity |
| Aster Language Research | Continued pretraining and evaluation | Training deadline, distributed scaling and checkpoint recovery |

Each story follows the same sequence: customer narrative, discovery findings, application composition, initial demand arithmetic, material questions and the intended Anubis case. The consultant can populate supported builder components without using an LLM. Unknowns become clarification items or bounded scenarios rather than hidden defaults.

## 1 Meridian Industrial Services
### Customer story

Meridian Industrial Services manufactures and maintains equipment across several countries. It wants employees and contracted service partners to use an AI assistant to search technical manuals, interpret maintenance records and help diagnose equipment faults. Answers must cite their sources and respect each user's access permissions.

The initial deployment serves 6,000 registered users: field technicians, service-desk staff and engineering specialists. The company estimates 1,200 active users during its busiest hour and expects adoption to double over two years. It also wants overnight processing of maintenance reports and may later fine-tune a model using engineer-reviewed examples.

The technology director explains:

“Our technicians spend too much time searching manuals and previous maintenance reports. We want them to ask a question, receive an answer grounded in our documents and follow up without starting again. The assistant should identify the equipment, retrieve the right documents and, where necessary, query our maintenance system. It must never expose one partner's records to another.”

“Our documentation and customer records must stay in our controlled environment. We are open to different GPU and storage suppliers, but we need a defensible configuration and a clear expansion path.”

### Discovery findings

| Topic | Customer information | Current status |
|---|---|---|
| Users and activity | 6,000 registered users; 1,200 active in the busiest hour; one question per active user every two minutes | Population confirmed; activity estimated |
| Workflow | Retrieval, inference, optional maintenance-system query and revised answer | Stages agreed; branching frequency unknown |
| Model | Self-hosted language model must pass a technical-answer evaluation | Model size and runtime undecided |
| Tokens | Retrieved material and conversation history may dominate prompt length; answers approximately 300 to 700 tokens | Prompt distribution unknown; output estimate |
| Service targets | First visible response within two seconds; most answers complete within fifteen seconds | Percentile and measurement boundary unresolved |
| Knowledge corpus | Approximately 8 TB of manuals, reports and extracted text | Initial inventory; deduplication and usable content unresolved |
| Batch work | Approximately 30,000 new reports daily; processing window 22:00 to 06:00 | Volume estimated; report-length distribution unknown |
| Fine-tuning | Weekly adaptation after sufficient reviewed examples exist | Future scenario; method and dataset undecided |
| Isolation | Shared technical content for staff; partner-specific access to records | Business requirement confirmed |
| Resilience | Continue interactive service after one GPU server fails | Permitted throughput degradation unresolved |
| Connectivity | Regional document transfers and enterprise-network tool queries | Transfer windows and network measurements missing |
| Growth and suppliers | Twice the adoption over two years; no mandated hardware supplier | Planning scenario and confirmed procurement flexibility |

### Application composition

| Workload | Processing stages | Operating pattern |
|---|---|---|
| Interactive assistant | Access check, authorized retrieval, inference, optional tool query and second inference | Business hours with regional overlap |
| Overnight processing | Read reports, extract text, batch inference, write summaries, embed and update index | Eight-hour completion window |
| Future adaptation | Prepare reviewed examples, fine-tune, evaluate and publish accepted model | Separate future operating scenario |

Authentication and the maintenance system are visible dependencies. Their presence does not automatically mean Anubis provisions them inside the GPU cluster. CPU preprocessing, retrieval infrastructure and index updates still need explicit ownership and resource treatment.

### Initial demand arithmetic

The accepted activity estimate gives 1,200 divided by 120 seconds, or 10 user questions per second during the busy hour. If a provisional 25 percent of questions require exactly one additional inference call, the application generates 12.5 inference calls per second. This branching rate is an assumption to validate; it is not a measured property of the application.

Thirty thousand reports in eight hours requires approximately 1.04 completed reports per second on average. Document lengths, the number of processing stages and usable execution time determine the actual batch demand. The two interactive inference stages may have different prompt distributions and latency targets, so their calls cannot automatically share one performance profile.

### Questions that change the sizing

The consultant first establishes which model meets answer-quality requirements, then obtains prompt, output and conversation-length distributions. Short-term arrival bursts must be separated from busy-hour averages. Tool-call frequency, retry rates and cache behaviour determine additional demand.

The customer must define the service retained after a node failure and whether batch processing may be delayed. Regional working hours may prevent an idle overnight period. Partner access isolation must be distinguished from dedicated GPU requirements; neither application access controls nor physical exclusivity should be inferred without an explicit requirement.

### Resulting Anubis case and handoff

The case contains an initial interactive workload, a scheduled batch workload and a separate future fine-tuning scenario. Each carries activity, service objectives, data assets and accepted assumptions. The engine assesses whether pooling is feasible and reports the constraints that determine installed capacity.

A completed recommendation would identify qualified GPU and host configurations, KV-cache and other memory requirements, storage tiers, network requirements and isolation conditions. Anubis maps supported requirements into downstream design tool and retains detailed execution and server specifications externally where necessary. A useful explanation would state whether latency, memory, batch completion or failure coverage determines the configuration, without assigning that conclusion before evaluation.

## 2 Harbor Inference Cloud
### Customer story

Harbor Inference Cloud is a regional infrastructure provider launching a private model-serving service for software companies. It intends to host customer-approved language models within one region and expose token-metered APIs. Customers bring their own application workflows; Harbor operates model endpoints rather than a shared retrieval application.

The launch cohort has twelve contracted tenants. Eight purchase a standard service class and four a priority class. Harbor wants to pool infrastructure where possible, preserve tenant separation and offer a paid dedicated-endpoint option. It expects normal traffic to be well below contractual bursts but has no production trace showing how tenants peak together.

The head of platform explains:

“We want to sell reliable inference capacity without buying a separate cluster for every customer. Some tenants have steady traffic and others receive sharp bursts when their users start work. We need to know what we can safely share and what we must reserve.”

“Priority tenants need to retain their contracted service after one server fails. Standard tenants can be rate-limited within the published policy. Model upgrades must be tested before we redirect customer traffic, and we must never mix one tenant's cached content with another's.”

### Discovery findings

| Topic | Customer information | Current status |
|---|---|---|
| Tenant population | Eight standard tenants and four priority tenants at launch | Contract cohort confirmed |
| Standard traffic | Each tenant expects 5 requests/s normally and requests a 15 requests/s burst limit | Normal rate estimated; admission policy proposed |
| Priority traffic | Each tenant expects 10 requests/s normally and requests 25 requests/s within its reservation | Normal rate estimated; guarantee wording unresolved |
| Model portfolio | Two approved endpoint classes, one compact and one larger model | Exact revisions, runtimes and tenant mix pending |
| Request shape | Provisional fleet mean of 2,000 input and 400 output tokens per request | Means estimated; tails and per-class distributions missing |
| Latency | Priority p95 first-token latency at most one second and p95 inter-token latency at most 50 ms | Proposed targets; measurement boundaries to be fixed |
| Isolation | Separate credentials, usage accounting, quotas and tenant cache namespaces | Requirement confirmed; sharing implementation unqualified |
| Failure policy | Priority reservations survive one server failure; standard service may be throttled | Requirement agreed in principle; recovery interval unresolved |
| Operations | Online inference runs continuously; upgrades need a test or canary window | Confirmed; overlap capacity undecided |
| Data storage | Model weights, endpoint versions and usage metadata; no central customer document corpus | Scope confirmed; retention and artifact sizes missing |
| External connectivity | Private and internet API access, plus model-artifact ingestion | Connection mix, bursts and redundancy targets pending |
| Expansion | Up to twenty-four tenants over the planning horizon | Growth scenario; future service-class mix unknown |

### Application composition

| Workload | Processing stages | Operating pattern |
|---|---|---|
| Standard endpoint | Authenticate, enforce quota, route to model, prefill and decode, meter response | Continuous with permitted throttling |
| Priority endpoint | Authenticate, check reservation, route to eligible replica, prefill and decode | Continuous with stronger service commitments |
| Model rollout | Ingest artifacts, validate, load candidate, run evaluation and shift traffic | Scheduled but overlapping live service |

The builder represents tenant classes and model endpoints as distinct demand groups. Each model class has its own evidence match and execution layout. A fleet-average request size cannot qualify a large-context tenant. Dedicated endpoints remain a separate scenario rather than an assumed consequence of logical tenant isolation.

### Initial demand arithmetic

Estimated normal load is eight times 5 plus four times 10, giving 80 requests/s. The arithmetic sum of all requested burst limits is eight times 15 plus four times 25, giving 220 requests/s. That sum is a simultaneous-admission scenario, not evidence that all tenants will peak together. Until the contract or a qualified traffic model says otherwise, statistical multiplexing cannot be used to promise every tenant its full limit concurrently on less capacity.

Under the provisional fleet means, 80 requests/s corresponds to 160,000 input tokens/s and 32,000 output tokens/s. At 220 requests/s the corresponding illustrative totals are 440,000 and 88,000 tokens/s. These totals do not determine replicas: per-model routing, sequence lengths, batching and latency objectives must be evaluated separately.

The priority class requests an aggregate reservation of 100 requests/s. If that becomes the contractual surviving-capacity requirement, Anubis must test its placement after a node is removed. It cannot treat an unavailable replica on the failed server as reserve capacity. Recovery-time compliance also requires evidence beyond steady surviving throughput.

### Questions that change the sizing

Harbor must decide whether burst limits are guaranteed simultaneously, subject to admission control or opportunistic. Tenant correlation and time-zone distribution determine the value of pooling, while model routing determines whether nominally spare GPUs can serve the affected traffic without a reload.

The consultant needs per-endpoint prompt and output distributions, maximum sequence lengths, cancellation behaviour and cache policy. Priority latency must specify whether it includes gateway and network time. Cache isolation, interference and scheduling behaviour need qualification for the proposed serving stack. Model rollout may temporarily require both versions to remain loaded.

API token throughput is not directly a WAN line rate. External capacity needs actual encoded request and response byte sizes, streaming overhead, connection counts, artifact transfers and redundancy conditions. Storage sizing needs model version retention and observability retention; it should not invent a large document store simply because this is an AI service.

### Resulting Anubis case and handoff

The case includes normal operation, simultaneous admitted bursts, one-node failure, model rollout and growth scenarios. It compares pooled service, separate priority pools and dedicated endpoints using the same stated obligations. Feasibility of a neocloud operating model is conditional on the isolation and service evidence, not just total GPU capacity.

The recommendation identifies GPU pools, per-model replicas, memory and host requirements, tenant operating rules and external connectivity. downstream design tool receives supported compute, fabric, storage, tenancy and connectivity parameters. Detailed reservation policies, cache isolation and rate-limit behaviour remain in the companion specification and assessment obligations. Anubis should explain which commercial commitments increase installed capacity and which admission-policy changes could reduce it.

## 3 Aster Language Research
### Customer story

Aster Language Research develops language technology for a group of affiliated institutions. It wants a dedicated environment for continued pretraining of an existing dense language model, followed by supervised fine-tuning and evaluation. This is not an initial foundation-model training run from random weights.

The proposed campaign uses a 30-billion-parameter base model and 120 billion additional training tokens. The research lead wants the main training phase finished within thirty calendar days. The base model, data rights and quality acceptance process must be approved before execution; Anubis sizes the declared campaign but does not establish training effectiveness.

The research director explains:

“We need a predictable training environment for a month-long campaign. We can dedicate the cluster to the main job during that period. Afterward, teams should be able to use it for smaller experiments and evaluation.”

“We cannot afford to lose a day's work when a server fails. Checkpoints need to complete without disrupting training for too long, and we need a realistic recovery plan. We also need to know whether the dataset preparation and evaluation jobs should run on separate resources.”

### Discovery findings

| Topic | Customer information | Current status |
|---|---|---|
| Training objective | Continued pretraining of an existing dense model | Objective confirmed; quality outcome not guaranteed by sizing |
| Model and tokens | 30 billion parameters; 120 billion additional tokens | Planning values; exact architecture and tokenizer pending |
| Deadline | Main training phase within thirty calendar days | Business target confirmed; start and finish boundaries pending |
| Execution | Distributed training; no prescribed GPU platform | Runtime, precision, optimizer and parallelism undecided |
| Data | Prepared training corpus expected to occupy 60 decimal TB | Estimate; raw, tokenized and retained copies not fully inventoried |
| Ingestion | Transfer the prepared corpus into the environment within twelve hours before the campaign | Proposed window; source performance unknown |
| Checkpoints | Save every thirty minutes; complete a write within two minutes | Proposed operational targets; actual checkpoint size unknown |
| Retention | Keep the four latest recovery checkpoints and one daily checkpoint for thirty days | Policy proposed; duplicate copies must be counted correctly |
| Resilience | Recover from a single-node failure without losing excessive completed work | Restart target and permitted data-loss interval unresolved |
| Evaluation | Periodic evaluation during the campaign and broader testing afterward | Dataset sizes and overlap schedule missing |
| Tenancy | Main campaign may use an exclusive allocation; later experiments may share | Confirmed scheduling preference |
| Growth | Possible second campaign and concurrent smaller experiments next year | Separate future scenario |

### Application composition

| Workload | Processing stages | Operating pattern |
|---|---|---|
| Data preparation | Read source material, clean and tokenize, validate shards, publish prepared corpus | Before the main training window unless separately scheduled |
| Main training | Load model and optimizer state, stream batches, compute and synchronize, write checkpoints | Dedicated distributed job for the campaign |
| Evaluation and tuning | Load selected checkpoints, run benchmark jobs, fine-tune approved variants | Explicit overlap windows or post-campaign allocation |

The workload description separates data preparation, training and evaluation. Their completion windows and ownership determine whether they consume the same GPU, CPU, storage and network resources. Model quality checks and dataset approval remain customer responsibilities. Anubis records these constraints but cannot derive quality from parameter count or training duration.

### Initial demand arithmetic

Thirty days contains 2,592,000 seconds. Processing 120 billion training tokens in that interval requires approximately 46,296 tokens/s averaged over the entire calendar period. If an explicitly accepted scenario allocates 85 percent of that period to effective training, the required throughput during effective training is approximately 54,466 tokens/s. The 85 percent allowance is illustrative, not a measured availability or scaling factor. Any explicit evaluation, restart or checkpoint overhead must be reconciled with it to avoid counting the same loss twice.

Moving 60 decimal TB in twelve hours requires approximately 1.389 GB/s of payload, or 11.11 Gbps. This is a lower-bound transfer calculation. Protocol overhead, line utilization, source and destination performance, redundancy and competing traffic determine the provisioned connectivity.

For a storage stress scenario only, suppose a complete recovery checkpoint is 2 TiB. Writing it in 120 seconds requires approximately 17.07 GiB/s of durable aggregate write throughput before competing traffic. The 2 TiB assumption must be replaced by the actual checkpoint representation, including the required model and optimizer states and any sharding effects. Four recent checkpoints plus thirty daily checkpoints give an upper bound of 34 distinct retained checkpoints, or 68 TiB under that assumption, before additional copies, in-flight writes and reserve. If a recent checkpoint is also a daily checkpoint, it is counted once.

### Questions that change the sizing

The research team must provide the exact model architecture, sequence length, global batch policy, tokenizer, optimizer, precision and activation-recomputation choices. Applicable training evidence must establish memory fit and delivered throughput for the chosen execution layout. Parameter count alone cannot establish GPU count or scaling efficiency.

The checkpoint interval is not automatically the maximum lost-work interval. Write duration, checkpoint validity, detection and recovery behaviour matter. The team must specify the accepted recovery point and restart target and test storage read performance as well as write performance. It must also decide whether the training job pauses for evaluation or runs alongside it.

Anubis needs dataset access patterns, preprocessing throughput, number of readers and caching policy to determine storage demand. Collective communication and topology evidence are needed before prescribing InfiniBand, Ethernet or a particular network separation. A dedicated training allocation during one campaign does not establish permanent single-workload exclusivity for the entire factory.

### Resulting Anubis case and handoff

The case binds a training campaign to its deadline and execution constraints, plus data-ingestion, checkpoint, recovery and evaluation scenarios. It compares supported GPU platforms and execution layouts against time, memory, communication and storage constraints. A future shared-experiment scenario is evaluated independently from the exclusive campaign.

The recommendation should identify a feasible training configuration, per-node host resources, checkpoint and dataset storage requirements, communication characteristics and the assumptions behind completion time. downstream design tool receives supported architectural parameters. Model execution details, checkpoint semantics and any unsupported server specifications remain in the companion specification. The explanation should identify whether compute throughput, distributed scaling, memory fit, recovery or data delivery constrains the design.

## 4 Common treatment in Anubis

These stories exercise different parts of the same deterministic process. The consultant records observations with units, scopes and sources; composes supported stages; defines service and operating scenarios; and accepts only explicit assumptions. The engine matches evidence, evaluates complete configurations and produces recommendations with traceable constraints.

| Review question | Meridian | Harbor | Aster |
|---|---|---|---|
| What drives demand | Employee activity and report volume | Tenant contracts and endpoint traffic | Training tokens and campaign deadline |
| What needs early clarification | Context and workflow expansion | Admission guarantees and traffic correlation | Execution layout and training efficiency |
| What tests sharing | Regional overlap and batch windows | Tenant isolation and interference | Evaluation overlap and later experiments |
| What tests resilience | Interactive service after node failure | Surviving priority reservations | Checkpoint validity and restart time |
| What prevents premature sizing | Unknown model and request shape | Unqualified per-model service profiles | Unknown memory and distributed throughput |

Each completed case should produce a workload model, demand scenarios, candidate comparison, selected AI Factory requirements and a downstream design tool mapping ledger. Partial evidence may support useful partial results, but it cannot justify a definitive GPU count or vendor exclusion. The report must keep business acceptance, engineering feasibility and downstream design tool representation separate.
