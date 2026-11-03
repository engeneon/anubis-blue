# GPU-complete customer scenario catalogue

Revision 2.0 · 3 November 2026

These 16 fictional customer demonstrations each have the numerical inputs needed to calculate H200, B200 and B300 GPU counts and prepare a downstream design handoff. Added inputs are explicit planning assumptions. Reference capacities are fictional example assumptions, not measured hardware performance.

The original incomplete stories are retained only as boundary tests in `tests/fixtures/architecture-boundary-scenarios.json`. They are not successful sizing demonstrations. The earlier S11, S13, S14 and S16 report-only playbooks are superseded as customer demonstrations by this complete input catalogue.

## Expected results

| ID | Customer | B300 GPUs | B200 GPUs | H200 GPUs | B300 factory anchor | Method |
|---|---|---:|---:|---:|---:|---|
| S01 | Alder Contact Services | 8 | 8 | 8 | 256 | analytical |
| S02 | Bracken Engineering | 8 | 8 | 8 | 256 | analytical |
| S03 | Cobalt Travel Operations | 8 | 8 | 8 | 256 | analytical |
| S04 | Dune Accounting | 8 | 8 | 8 | 256 | analytical |
| S05 | Estuary Transit | 40 | 48 | 72 | 256 | reference |
| S06 | Fable Creative Studio | 24 | 24 | 40 | 256 | reference |
| S07 | Grove Legal Technology | 16 | 16 | 24 | 256 | reference |
| S08 | Helix Language Institute | 8 | 8 | 8 | 256 | analytical |
| S09 | Juniper Retail | 8 | 8 | 8 | 256 | analytical |
| S10 | Kestrel Field Services | 16 | 24 | 32 | 256 | reference |
| S11 | Larch Media Archive | 24 | 24 | 32 | 256 | analytical + reference |
| S12 | Morrow Advertising | 32 | 40 | 48 | 256 | analytical + reference |
| S13 | Nacre Customer Portal | 8 | 8 | 8 | 256 | analytical |
| S14 | Orchid Neocloud | 16 | 16 | 16 | 256 | analytical |
| S15 | Peregrine Product Lab | 8 | 8 | 8 | 256 | analytical |
| S16 | Quartz Industrial Research | 16 | 16 | 24 | 256 | reference |

Counts are workload requirements rounded to whole eight-GPU nodes. The 256-GPU factory anchor is a separate infrastructure choice. GPU counts do not establish a qualified tenant count or certify latency. ±30% is the starting sensitivity envelope.

## Run a demonstration

1. Start Anubis with `python3 deploy/local/run.py`. Open `http://127.0.0.1:8787`. Retrieve your token locally from `.anubis/identities.json`, then enter it in **Access token**. Do not put it in a report.
2. Select **New engagement**, enter the customer name, and add each listed application pattern.
3. Confirm placement, reservation and overlap. Select each component in the diagram and enter its table values in **Describe scale**.
4. For reference workloads, select **Reference capacity for independent work**. Review and accept the reference source and independence conditions.
5. Resolve every item in **GPU estimate blocked**. Click a missing field to open its input.
6. In **Review and estimate**, accept the displayed planning assumptions, then select **Calculate estimate**. Verify all three comparisons against the table.
7. Select **Continue to Design handoff**, then **Prepare projection**. The factory anchor must be available with the workload counts retained in the companion requirements. Complete and save the engagement.

For Copilot, provide the original story plus the planning completion and exact inputs below. Review extracted facts before accepting. Reference capacities require explicit consultant entry and acceptance in the guided form. Copilot is not permitted to invent hardware throughput. Both routes use the same deterministic calculation.

## Common defaults and boundaries

For analytical text components the tables explicitly select dense8b, one model call and 2000/500 input/output tokens unless overridden. Memory defaults: BF16 weights and KV cache, 8192-token context, 32 concurrent sequences, 8 GB workspace. Training uses eight GPUs per replica, 16 bytes/parameter, 32 GB activation per GPU and 85% useful training time. Host defaults: 256 GB RAM, 3840 GB local disk and 16 CPU cores per workload GPU. Compute efficiency 0.35 and bandwidth efficiency 0.50 are analytical assumptions.

The B300 enterprise two-plane Spectrum-X profile and ±30% sensitivity are used. Unless stated below, storage capacity and network traffic remain unspecified. They are not zero. Storage networking is physically dedicated. Outside corpora are not automatically local storage or initial transfer volumes.

## S01 — Alder Contact Services

A regional service desk wants a local text classifier for 45,000 incoming messages daily. One model labels each message. no document search or tools are involved. The busiest hour receives 6,000 messages. Responses must arrive within five seconds.

**Planning completion.** All added numbers are explicit fictional customer planning assumptions for a reproducible demonstration. They are not historical measurements or qualified hardware benchmarks. Dense text components use dense8b, one call/request, 2000 input and 500 output tokens unless overridden in the intake table. 

**Arrangement:** overlap = yes. Tenancy = single. Accepted planning assumptions = yes.

### Message classification

| UI field | Entered value |
|---|---|
| **Component name** | Message classification |
| **Application pattern** | direct |
| **Compute location** | local |
| **Relationship** | independent |
| **Model preset** | dense8b |
| **Peak requests per minute** | 100 |
| **Model calls per request or job** | 1 |
| **Input tokens per model call** | 2000 |
| **Output tokens per model call** | 500 |
| **Search and indexing location** | none |

**Pass criteria:** Readiness lists no missing GPU inputs. B300, B200 and H200 comparisons each contain a positive node-rounded GPU estimate with conditional planning status. A planning:factory candidate is available for design handoff. Outside corpus and hosted compute are not silently included as local retained data or GPUs. Reference capacities remain explicitly labelled assumptions, with no claim of benchmark or latency qualification.

## S02 — Bracken Engineering

Eight thousand engineers ask an assistant questions about maintenance manuals. The existing external search platform returns passages. a local model writes the answer. The assistant serves 2,400 questions in the busiest hour. The 4 TB corpus is indexed by the external platform.

**Planning completion.** All added numbers are explicit fictional customer planning assumptions for a reproducible demonstration. They are not historical measurements or qualified hardware benchmarks. Dense text components use dense8b, one call/request, 2000 input and 500 output tokens unless overridden in the intake table. 

**Arrangement:** overlap = yes. Tenancy = single. Accepted planning assumptions = yes.

### Manual assistant

| UI field | Entered value |
|---|---|
| **Component name** | Manual assistant |
| **Application pattern** | retrieval |
| **Compute location** | local |
| **Relationship** | independent |
| **Model preset** | dense8b |
| **Peak requests per minute** | 40 |
| **Model calls per request or job** | 1 |
| **Input tokens per model call** | 2000 |
| **Output tokens per model call** | 500 |
| **Search and indexing location** | external |

**Pass criteria:** Readiness lists no missing GPU inputs. B300, B200 and H200 comparisons each contain a positive node-rounded GPU estimate with conditional planning status. A planning:factory candidate is available for design handoff. Outside corpus and hosted compute are not silently included as local retained data or GPUs. Reference capacities remain explicitly labelled assumptions, with no claim of benchmark or latency qualification.

## S03 — Cobalt Travel Operations

A travel operations assistant resolves disruption cases by checking schedules and hotel systems. It typically invokes a model four times but complex cases take up to twelve calls. About 1,500 cases arrive daily. Tool results influence the next action.

**Planning completion.** All added numbers are explicit fictional customer planning assumptions for a reproducible demonstration. They are not historical measurements or qualified hardware benchmarks. Dense text components use dense8b, one call/request, 2000 input and 500 output tokens unless overridden in the intake table. 

**Arrangement:** overlap = yes. Tenancy = single. Accepted planning assumptions = yes.

### Disruption case agent

| UI field | Entered value |
|---|---|
| **Component name** | Disruption case agent |
| **Application pattern** | agent |
| **Compute location** | local |
| **Relationship** | independent |
| **Model preset** | dense8b |
| **Peak requests per minute** | 30 |
| **Model calls per request or job** | 12 |
| **Input tokens per model call** | 3000 |
| **Output tokens per model call** | 600 |
| **Search and indexing location** | none |

**Pass criteria:** Readiness lists no missing GPU inputs. B300, B200 and H200 comparisons each contain a positive node-rounded GPU estimate with conditional planning status. A planning:factory candidate is available for design handoff. Outside corpus and hosted compute are not silently included as local retained data or GPUs. Reference capacities remain explicitly labelled assumptions, with no claim of benchmark or latency qualification.

## S04 — Dune Accounting

A service creates 80,000 text summaries of invoices between 22:00 and 06:00. Each invoice uses one model call. No interactive work runs on these resources during the processing window.

**Planning completion.** All added numbers are explicit fictional customer planning assumptions for a reproducible demonstration. They are not historical measurements or qualified hardware benchmarks. Dense text components use dense8b, one call/request, 2000 input and 500 output tokens unless overridden in the intake table. 

**Arrangement:** overlap = yes. Tenancy = single. Accepted planning assumptions = yes.

### Invoice summaries

| UI field | Entered value |
|---|---|
| **Component name** | Invoice summaries |
| **Application pattern** | batch |
| **Compute location** | local |
| **Relationship** | independent |
| **Model preset** | dense8b |
| **Peak requests per minute** | 100 |
| **Model calls per request or job** | 1 |
| **Input tokens per model call** | 2000 |
| **Output tokens per model call** | 500 |
| **Search and indexing location** | none |
| **Jobs per window** | 80000 |
| **Completion window in hours** | 8 |

**Pass criteria:** Readiness lists no missing GPU inputs. B300, B200 and H200 comparisons each contain a positive node-rounded GPU estimate with conditional planning status. A planning:factory candidate is available for design handoff. Outside corpus and hosted compute are not silently included as local retained data or GPUs. Reference capacities remain explicitly labelled assumptions, with no claim of benchmark or latency qualification.

## S05 — Estuary Transit

A transit operator plans live object detection on 180 camera streams. Cameras provide 1080p video, but detection is requested at five frames per second per camera. Only event clips are retained. There is no text-generation service.

**Planning completion.** All added numbers are explicit fictional customer planning assumptions for a reproducible demonstration. They are not historical measurements or qualified hardware benchmarks. Dense text components use dense8b, one call/request, 2000 input and 500 output tokens unless overridden in the intake table. 

**Arrangement:** overlap = yes. Tenancy = single. Accepted planning assumptions = yes.

### Camera detection

| UI field | Entered value |
|---|---|
| **Component name** | Camera detection |
| **Application pattern** | stream |
| **Compute location** | local |
| **Relationship** | independent |
| **Sizing method** | reference |
| **Peak work units per second** | 900 |
| **Work unit** | frame |
| **GPUs per reference group** | 8 |
| **Required GPU memory in GB** | 40 |
| **H200 work units per second per group** | 100 |
| **B200 work units per second per group** | 160 |
| **B300 work units per second per group** | 200 |
| **Independent reference groups can serve this demand** | Checked |
| **I accept this reference capacity and its scope** | Checked |
| **Reference source and conditions** | Fictional consultant planning assumption for this demonstration, not measured benchmark evidence. 180 cameras × 5 sampled frames/s. Fixed 1080p detector, BF16, complete eight-GPU independent camera-serving groups. |

**Pass criteria:** Readiness lists no missing GPU inputs. B300, B200 and H200 comparisons each contain a positive node-rounded GPU estimate with conditional planning status. A planning:factory candidate is available for design handoff. Outside corpus and hosted compute are not silently included as local retained data or GPUs. Reference capacities remain explicitly labelled assumptions, with no claim of benchmark or latency qualification.

## S06 — Fable Creative Studio

A studio produces 12,000 catalogue images per day in four-hour production windows. Image size is 1024 by 1024 pixels, with several candidate images per product. It has not chosen the generation model.

**Planning completion.** All added numbers are explicit fictional customer planning assumptions for a reproducible demonstration. They are not historical measurements or qualified hardware benchmarks. Dense text components use dense8b, one call/request, 2000 input and 500 output tokens unless overridden in the intake table. 

**Arrangement:** overlap = yes. Tenancy = single. Accepted planning assumptions = yes.

### Catalogue images

| UI field | Entered value |
|---|---|
| **Component name** | Catalogue images |
| **Application pattern** | generation |
| **Compute location** | local |
| **Relationship** | independent |
| **Sizing method** | reference |
| **Peak work units per second** | 0.833334 |
| **Work unit** | image |
| **GPUs per reference group** | 8 |
| **Required GPU memory in GB** | 80 |
| **H200 work units per second per group** | 0.2 |
| **B200 work units per second per group** | 0.3 |
| **B300 work units per second per group** | 0.4 |
| **Independent reference groups can serve this demand** | Checked |
| **I accept this reference capacity and its scope** | Checked |
| **Reference source and conditions** | Fictional consultant planning assumption for this demonstration, not measured benchmark evidence. 12,000 independent images in four hours. Fixed diffusion model, 1024 square, 30 steps, BF16. Each capacity is for a complete eight-GPU group. |

**Pass criteria:** Readiness lists no missing GPU inputs. B300, B200 and H200 comparisons each contain a positive node-rounded GPU estimate with conditional planning status. A planning:factory candidate is available for design handoff. Outside corpus and hosted compute are not silently included as local retained data or GPUs. Reference capacities remain explicitly labelled assumptions, with no claim of benchmark or latency qualification.

## S07 — Grove Legal Technology

A software supplier adapts an existing 8B text model monthly using 300,000 reviewed examples. It expects parameter-efficient fine-tuning, but the training team has not confirmed the method. Each run should finish within a weekend.

**Planning completion.** All added numbers are explicit fictional customer planning assumptions for a reproducible demonstration. They are not historical measurements or qualified hardware benchmarks. Dense text components use dense8b, one call/request, 2000 input and 500 output tokens unless overridden in the intake table. 

**Arrangement:** overlap = yes. Tenancy = single. Accepted planning assumptions = yes.

### Monthly model adaptation

| UI field | Entered value |
|---|---|
| **Component name** | Monthly model adaptation |
| **Application pattern** | adaptation |
| **Compute location** | local |
| **Relationship** | independent |
| **Sizing method** | reference |
| **Peak work units per second** | 0.000023149 |
| **Work unit** | training run |
| **GPUs per reference group** | 8 |
| **Required GPU memory in GB** | 80 |
| **H200 work units per second per group** | 0.000011574 |
| **B200 work units per second per group** | 0.000015432 |
| **B300 work units per second per group** | 0.000023148 |
| **Independent reference groups can serve this demand** | Checked |
| **I accept this reference capacity and its scope** | Checked |
| **Reference source and conditions** | Fictional consultant planning assumption for this demonstration, not measured benchmark evidence. Four independent 8B LoRA experiments in 48 hours. Each run uses 300,000 examples, 1,000 tokens/example, one epoch, BF16 and fixed adapter rank. Assumed group run times H200 24h, B200 18h, B300 12h. Rates conservatively rounded. No single training run is divided across groups. |

**Pass criteria:** Readiness lists no missing GPU inputs. B300, B200 and H200 comparisons each contain a positive node-rounded GPU estimate with conditional planning status. A planning:factory candidate is available for design handoff. Outside corpus and hosted compute are not silently included as local retained data or GPUs. Reference capacities remain explicitly labelled assumptions, with no claim of benchmark or latency qualification.

## S08 — Helix Language Institute

A research institute continues pretraining an existing language model on 90 billion tokens over 30 days. Data arrives from a separate research storage service. Training checkpoints are written during the campaign.

**Planning completion.** All added numbers are explicit fictional customer planning assumptions for a reproducible demonstration. They are not historical measurements or qualified hardware benchmarks. Dense text components use dense8b, one call/request, 2000 input and 500 output tokens unless overridden in the intake table. 

**Arrangement:** overlap = yes. Tenancy = single. Accepted planning assumptions = yes.

### Language pretraining

| UI field | Entered value |
|---|---|
| **Component name** | Language pretraining |
| **Application pattern** | training |
| **Compute location** | local |
| **Relationship** | independent |
| **Model preset** | dense8b |
| **Peak requests per minute** | 100 |
| **Model calls per request or job** | 1 |
| **Input tokens per model call** | 2000 |
| **Output tokens per model call** | 500 |
| **Search and indexing location** | none |
| **Training tokens** | 90000000000 |
| **Training deadline in days** | 30 |

**Pass criteria:** Readiness lists no missing GPU inputs. B300, B200 and H200 comparisons each contain a positive node-rounded GPU estimate with conditional planning status. A planning:factory candidate is available for design handoff. Outside corpus and hosted compute are not silently included as local retained data or GPUs. Reference capacities remain explicitly labelled assumptions, with no claim of benchmark or latency qualification.

## S09 — Juniper Retail

A retailer runs a document assistant for 18,000 staff and produces 20,000 store reports overnight. Staff access is disabled during the report window. Both activities use text models but have different input sizes.

**Planning completion.** All added numbers are explicit fictional customer planning assumptions for a reproducible demonstration. They are not historical measurements or qualified hardware benchmarks. Dense text components use dense8b, one call/request, 2000 input and 500 output tokens unless overridden in the intake table. Daytime assistant and overnight reports have confirmed separate windows. The same GPUs may be reused.

**Arrangement:** overlap = no. Tenancy = single. Accepted planning assumptions = yes.

### Store assistant

| UI field | Entered value |
|---|---|
| **Component name** | Store assistant |
| **Application pattern** | retrieval |
| **Compute location** | local |
| **Relationship** | independent |
| **Model preset** | dense8b |
| **Peak requests per minute** | 100 |
| **Model calls per request or job** | 1 |
| **Input tokens per model call** | 2000 |
| **Output tokens per model call** | 500 |
| **Search and indexing location** | external |

### Nightly reports

| UI field | Entered value |
|---|---|
| **Component name** | Nightly reports |
| **Application pattern** | batch |
| **Compute location** | local |
| **Relationship** | independent |
| **Model preset** | dense8b |
| **Peak requests per minute** | 100 |
| **Model calls per request or job** | 1 |
| **Input tokens per model call** | 2000 |
| **Output tokens per model call** | 500 |
| **Search and indexing location** | none |
| **Jobs per window** | 20000 |
| **Completion window in hours** | 8 |

**Pass criteria:** Readiness lists no missing GPU inputs. B300, B200 and H200 comparisons each contain a positive node-rounded GPU estimate with conditional planning status. A planning:factory candidate is available for design handoff. Outside corpus and hosted compute are not silently included as local retained data or GPUs. Reference capacities remain explicitly labelled assumptions, with no claim of benchmark or latency qualification.

## S10 — Kestrel Field Services

A repair agent searches equipment records, proposes repairs and creates work orders through tools. New manuals are indexed nightly while the agent remains available to technicians in other time zones. The corpus is 9 TB and grows by 40 GB daily.

**Planning completion.** All added numbers are explicit fictional customer planning assumptions for a reproducible demonstration. They are not historical measurements or qualified hardware benchmarks. Dense text components use dense8b, one call/request, 2000 input and 500 output tokens unless overridden in the intake table. 

**Arrangement:** overlap = yes. Tenancy = single. Accepted planning assumptions = yes.

### Repair agent

| UI field | Entered value |
|---|---|
| **Component name** | Repair agent |
| **Application pattern** | agent |
| **Compute location** | local |
| **Relationship** | independent |
| **Sizing method** | reference |
| **Peak work units per second** | 1 |
| **Work unit** | repair request |
| **GPUs per reference group** | 8 |
| **Required GPU memory in GB** | 80 |
| **H200 work units per second per group** | 0.5 |
| **B200 work units per second per group** | 0.8 |
| **B300 work units per second per group** | 1 |
| **Independent reference groups can serve this demand** | Checked |
| **I accept this reference capacity and its scope** | Checked |
| **Reference source and conditions** | Fictional consultant planning assumption for this demonstration, not measured benchmark evidence. Complete repair agent including local online retrieval and four text calls of 2000 input/500 output tokens per request. Fixed 8B answer/embedding models and 9 TB corpus. Excludes offline refresh, separately allocated. |
| **Search and indexing location** | local |
| **Reference includes local search and indexing** | Checked |
| **Locally retained data in TB** | 9 |
| **Daily growth in GB** | 40 |
| **Planning horizon in days** | 365 |

### Manual indexing

| UI field | Entered value |
|---|---|
| **Component name** | Manual indexing |
| **Application pattern** | other |
| **Compute location** | local |
| **Relationship** | independent |
| **Sizing method** | reference |
| **Peak work units per second** | 2 |
| **Work unit** | document |
| **GPUs per reference group** | 8 |
| **Required GPU memory in GB** | 40 |
| **H200 work units per second per group** | 1 |
| **B200 work units per second per group** | 2 |
| **B300 work units per second per group** | 3 |
| **Independent reference groups can serve this demand** | Checked |
| **I accept this reference capacity and its scope** | Checked |
| **Reference source and conditions** | Fictional consultant planning assumption for this demonstration, not measured benchmark evidence. 40 GB/day as 40,000 documents averaging 1 MB. Index 40,000 documents within 20,000 seconds. Fixed embedding model and document size. Independent indexing shards. Covers offline refresh only, excluding online repair agent. |

**Pass criteria:** Readiness lists no missing GPU inputs. B300, B200 and H200 comparisons each contain a positive node-rounded GPU estimate with conditional planning status. A planning:factory candidate is available for design handoff. Outside corpus and hosted compute are not silently included as local retained data or GPUs. Reference capacities remain explicitly labelled assumptions, with no claim of benchmark or latency qualification.

## S11 — Larch Media Archive

A broadcaster continuously analyses incoming video, then uses extracted descriptions to build searchable records. Editors ask a text assistant questions about the archive. Video ingestion and editor queries run together.

**Planning completion.** All added numbers are explicit fictional customer planning assumptions for a reproducible demonstration. They are not historical measurements or qualified hardware benchmarks. Dense text components use dense8b, one call/request, 2000 input and 500 output tokens unless overridden in the intake table. The assistant uses an existing search/index service outside this AI Factory. Video work runs locally and overlaps assistant demand.

**Arrangement:** overlap = yes. Tenancy = single. Accepted planning assumptions = yes.

### Video analysis

| UI field | Entered value |
|---|---|
| **Component name** | Video analysis |
| **Application pattern** | stream |
| **Compute location** | local |
| **Relationship** | independent |
| **Sizing method** | reference |
| **Peak work units per second** | 300 |
| **Work unit** | frame |
| **GPUs per reference group** | 8 |
| **Required GPU memory in GB** | 40 |
| **H200 work units per second per group** | 100 |
| **B200 work units per second per group** | 160 |
| **B300 work units per second per group** | 200 |
| **Independent reference groups can serve this demand** | Checked |
| **I accept this reference capacity and its scope** | Checked |
| **Reference source and conditions** | Fictional consultant planning assumption for this demonstration, not measured benchmark evidence. 60 concurrent archived video streams sampled at 5 frames/s. Fixed 1080p analysis model, BF16, independent complete eight-GPU worker groups. |

### Archive search

| UI field | Entered value |
|---|---|
| **Component name** | Archive search |
| **Application pattern** | retrieval |
| **Compute location** | local |
| **Relationship** | independent |
| **Model preset** | dense8b |
| **Peak requests per minute** | 40 |
| **Model calls per request or job** | 1 |
| **Input tokens per model call** | 2000 |
| **Output tokens per model call** | 500 |
| **Search and indexing location** | external |

**Pass criteria:** Readiness lists no missing GPU inputs. B300, B200 and H200 comparisons each contain a positive node-rounded GPU estimate with conditional planning status. A planning:factory candidate is available for design handoff. Outside corpus and hosted compute are not silently included as local retained data or GPUs. Reference capacities remain explicitly labelled assumptions, with no claim of benchmark or latency qualification.

## S12 — Morrow Advertising

An agency first uses a text agent to draft a campaign plan. If a customer approves it, an image generation job produces campaign assets. Several customer campaigns can be in different phases at once.

**Planning completion.** All added numbers are explicit fictional customer planning assumptions for a reproducible demonstration. They are not historical measurements or qualified hardware benchmarks. Dense text components use dense8b, one call/request, 2000 input and 500 output tokens unless overridden in the intake table. 

**Arrangement:** overlap = yes. Tenancy = single. Accepted planning assumptions = yes.

### Campaign planner

| UI field | Entered value |
|---|---|
| **Component name** | Campaign planner |
| **Application pattern** | agent |
| **Compute location** | local |
| **Relationship** | independent |
| **Model preset** | dense8b |
| **Peak requests per minute** | 20 |
| **Model calls per request or job** | 4 |
| **Input tokens per model call** | 2000 |
| **Output tokens per model call** | 500 |
| **Search and indexing location** | none |

### Approved campaign assets

| UI field | Entered value |
|---|---|
| **Component name** | Approved campaign assets |
| **Application pattern** | generation |
| **Compute location** | local |
| **Relationship** | independent |
| **Sizing method** | reference |
| **Peak work units per second** | 1 |
| **Work unit** | image |
| **GPUs per reference group** | 8 |
| **Required GPU memory in GB** | 80 |
| **H200 work units per second per group** | 0.2 |
| **B200 work units per second per group** | 0.3 |
| **B300 work units per second per group** | 0.4 |
| **Independent reference groups can serve this demand** | Checked |
| **I accept this reference capacity and its scope** | Checked |
| **Reference source and conditions** | Fictional consultant planning assumption for this demonstration, not measured benchmark evidence. 60 approved images/minute aggregate across overlapping campaigns. Fixed diffusion model, BF16, 1024 square, 30 steps. Independent eight-GPU serving groups, conditional invocation already reflected in image demand. |

**Pass criteria:** Readiness lists no missing GPU inputs. B300, B200 and H200 comparisons each contain a positive node-rounded GPU estimate with conditional planning status. A planning:factory candidate is available for design handoff. Outside corpus and hosted compute are not silently included as local retained data or GPUs. Reference capacities remain explicitly labelled assumptions, with no claim of benchmark or latency qualification.

## S13 — Nacre Customer Portal

A portal sends all language-model calls to an external provider. It handles 900,000 requests per day. The proposed factory hosts customer data and integration services, not the model. The customer asks whether this requires local GPUs.

**Planning completion.** All added numbers are explicit fictional customer planning assumptions for a reproducible demonstration. They are not historical measurements or qualified hardware benchmarks. Dense text components use dense8b, one call/request, 2000 input and 500 output tokens unless overridden in the intake table. The original outside-only service does not need local model GPUs. This revised demonstration explicitly adds a customer-approved local continuity fallback at 20 requests/minute. It is additional scope, not inferred from hosted traffic.

**Arrangement:** overlap = yes. Tenancy = single. Accepted planning assumptions = yes.

### Hosted text service

| UI field | Entered value |
|---|---|
| **Component name** | Hosted text service |
| **Application pattern** | direct |
| **Compute location** | external |
| **Relationship** | independent |
| **Model preset** | dense8b |
| **Peak requests per minute** | 100 |
| **Model calls per request or job** | 1 |
| **Input tokens per model call** | 2000 |
| **Output tokens per model call** | 500 |
| **Search and indexing location** | none |

### Local continuity fallback

| UI field | Entered value |
|---|---|
| **Component name** | Local continuity fallback |
| **Application pattern** | direct |
| **Compute location** | local |
| **Relationship** | independent |
| **Model preset** | dense8b |
| **Peak requests per minute** | 20 |
| **Model calls per request or job** | 1 |
| **Input tokens per model call** | 2000 |
| **Output tokens per model call** | 500 |
| **Search and indexing location** | none |

**Pass criteria:** Readiness lists no missing GPU inputs. B300, B200 and H200 comparisons each contain a positive node-rounded GPU estimate with conditional planning status. A planning:factory candidate is available for design handoff. Outside corpus and hosted compute are not silently included as local retained data or GPUs. Reference capacities remain explicitly labelled assumptions, with no claim of benchmark or latency qualification.

## S14 — Orchid Neocloud

A provider hosts twenty customers using text endpoints. Premium customers require dedicated resources. standard customers may share a pool. Both groups can peak together. Model choices vary between customers.

**Planning completion.** All added numbers are explicit fictional customer planning assumptions for a reproducible demonstration. They are not historical measurements or qualified hardware benchmarks. Dense text components use dense8b, one call/request, 2000 input and 500 output tokens unless overridden in the intake table. The 20 tenants are represented by two aggregate demand pools. Premium capacity is reserved. Tenant count is not multiplied into these already aggregated rates.

**Arrangement:** overlap = yes. Tenancy = multi. Accepted planning assumptions = yes.

### Premium model endpoints

| UI field | Entered value |
|---|---|
| **Component name** | Premium model endpoints |
| **Application pattern** | direct |
| **Compute location** | local |
| **Relationship** | independent |
| **Model preset** | dense8b |
| **Peak requests per minute** | 60 |
| **Model calls per request or job** | 1 |
| **Input tokens per model call** | 2000 |
| **Output tokens per model call** | 500 |
| **Search and indexing location** | none |
| **Reserve dedicated capacity** | Checked |

### Standard model endpoints

| UI field | Entered value |
|---|---|
| **Component name** | Standard model endpoints |
| **Application pattern** | direct |
| **Compute location** | local |
| **Relationship** | independent |
| **Model preset** | dense8b |
| **Peak requests per minute** | 300 |
| **Model calls per request or job** | 1 |
| **Input tokens per model call** | 2000 |
| **Output tokens per model call** | 500 |
| **Search and indexing location** | none |

**Pass criteria:** Readiness lists no missing GPU inputs. B300, B200 and H200 comparisons each contain a positive node-rounded GPU estimate with conditional planning status. A planning:factory candidate is available for design handoff. Outside corpus and hosted compute are not silently included as local retained data or GPUs. Reference capacities remain explicitly labelled assumptions, with no claim of benchmark or latency qualification.

## S15 — Peregrine Product Lab

A product team asks for an AI assistant for roughly 5,000 employees. It cannot yet say whether the assistant searches internal documents, uses tools, or runs locally. It has no usage logs or model selection.

**Planning completion.** All added numbers are explicit fictional customer planning assumptions for a reproducible demonstration. They are not historical measurements or qualified hardware benchmarks. Dense text components use dense8b, one call/request, 2000 input and 500 output tokens unless overridden in the intake table. Discovery is now resolved for this demonstration: a local answer model uses an existing search service outside this AI Factory and serves 40 questions/minute. Employee count is not used as demand.

**Arrangement:** overlap = yes. Tenancy = single. Accepted planning assumptions = yes.

### Proposed assistant

| UI field | Entered value |
|---|---|
| **Component name** | Proposed assistant |
| **Application pattern** | retrieval |
| **Compute location** | local |
| **Relationship** | independent |
| **Model preset** | dense8b |
| **Peak requests per minute** | 40 |
| **Model calls per request or job** | 1 |
| **Input tokens per model call** | 2000 |
| **Output tokens per model call** | 500 |
| **Search and indexing location** | external |

**Pass criteria:** Readiness lists no missing GPU inputs. B300, B200 and H200 comparisons each contain a positive node-rounded GPU estimate with conditional planning status. A planning:factory candidate is available for design handoff. Outside corpus and hosted compute are not silently included as local retained data or GPUs. Reference capacities remain explicitly labelled assumptions, with no claim of benchmark or latency qualification.

## S16 — Quartz Industrial Research

A manufacturer wants GPU-accelerated fluid simulation for turbine design. Engineers describe meshes, solver steps and simulation deadlines. No text model, retrieval, agent, media generation or model training is involved.

**Planning completion.** All added numbers are explicit fictional customer planning assumptions for a reproducible demonstration. They are not historical measurements or qualified hardware benchmarks. Dense text components use dense8b, one call/request, 2000 input and 500 output tokens unless overridden in the intake table. 

**Arrangement:** overlap = yes. Tenancy = single. Accepted planning assumptions = yes.

### Fluid simulation

| UI field | Entered value |
|---|---|
| **Component name** | Fluid simulation |
| **Application pattern** | other |
| **Compute location** | local |
| **Relationship** | independent |
| **Sizing method** | reference |
| **Peak work units per second** | 0.000138889 |
| **Work unit** | simulation |
| **GPUs per reference group** | 8 |
| **Required GPU memory in GB** | 90 |
| **H200 work units per second per group** | 0.000069444 |
| **B200 work units per second per group** | 0.000092592 |
| **B300 work units per second per group** | 0.000138888 |
| **Independent reference groups can serve this demand** | Checked |
| **I accept this reference capacity and its scope** | Checked |
| **Reference source and conditions** | Fictional consultant planning assumption for this demonstration, not measured benchmark evidence. Twelve independent CFD runs per 24h. Fixed solver/version, 20-million-cell mesh, 10,000 steps, FP64 mixed solver. Each job fits one eight-GPU group. Assumed group run times H200 4h, B200 3h, B300 2h. Rates conservatively rounded. No linear scaling of one larger mesh. |

**Pass criteria:** Readiness lists no missing GPU inputs. B300, B200 and H200 comparisons each contain a positive node-rounded GPU estimate with conditional planning status. A planning:factory candidate is available for design handoff. Outside corpus and hosted compute are not silently included as local retained data or GPUs. Reference capacities remain explicitly labelled assumptions, with no claim of benchmark or latency qualification.

## Obtaining customer values

| Parameter | Practical collection method |
|---|---|
| Peak rate | Count gateway or application requests in representative busy minutes. A daily total or registered user count is insufficient. |
| Calls and tokens | Trace complete transactions including retries and agent loops. Use model-serving logs or the exact tokenizer on representative prompts and outputs. |
| Batch volume and deadline | Obtain queue counts and the time between input availability and required completion. Convert work volume to a rate using that window. |
| Training tokens | Tokenize the dataset and multiply by epochs or repeated exposure. Examples are not tokens. Agree the useful training-time assumption. |
| Reference throughput | Measure or explicitly assume completed units per second for the exact model/solver, input size, precision and complete GPU group on each hardware platform. Record the source. |
| Reference memory | Record peak memory on the most heavily loaded GPU for the same configuration. Include model, working state and buffers. |
| Independent groups | Verify the scheduler can distribute separate requests or jobs to complete replicated groups. One larger mesh or model does not satisfy this assumption. |
| Local retained data | Inventory actual local retained copies. Do not substitute the size of an outside corpus or index. |
| Network requirements | Measure directional payload rates, initial data-transfer size and window, storage reads/writes and collective traffic separately. |

## Repeatable release gate

Run `python3 scripts/validate_scenario_catalogue.py` after building. It checks exact expected counts, reference arithmetic, sensitivity, memory failure, missing-input handling and all 16 saved handoff payloads. Results are written to `testing-evidence/gpu-readiness/scenario-results.json`. No demonstration passes solely because it can close with a status report.
