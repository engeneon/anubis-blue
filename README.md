# Anubis Blue

Anubis is a deterministic AI Factory workload sizing application with an optional, human-reviewed Consultant Copilot. It estimates GPU requirements, records assumptions, and exports requirements for a downstream AI Factory design tool or process.

## Install on macOS

Follow the [Mac installation guide](docs/macos-installation-guide.txt), including first-login access-token setup, restarting, backup and recovery. The evaluated platform is Apple Silicon. Linux installation guidance is deferred.

## Use the application

- [MVP workflow and supported scope](docs/mvp-1.0-guide.txt)
- [Copilot configuration and operation](docs/copilot-operation.txt)
- [Application sizing guide](docs/usability-user-guide.html)
- [Methodology](docs/anubis-framework-v2_1.txt)
- [Architecture](docs/anubis-technical-architecture.md)

Manual sizing does not require a model provider. Live Copilot calls require a separately configured backend API credential and provider account. No credentials or customer databases are distributed here.

## Validate

After installing dependencies and building as documented:

```sh
ctest --test-dir build --output-on-failure
npx playwright install chromium
npm run test:mvp
python3 scripts/test_local_restart.py
python3 scripts/validate_scenario_catalogue.py
```

The following 16 fictional customer scenarios form the architecture and scope test catalogue. Their acceptance objectives are listed below. The repeatable catalogue check verifies deterministic transformation and correctly unresolved results when numerical intake is incomplete. It does **not** establish complete GPU sizing for every scenario or certify every narrative objective. The two MVP browser tests separately exercise manual and reviewed-proposal sizing, handoff, closure and retrieval.

| ID | Customer scenario | Workload and validation objective |
|---|---|---|
| S01 | Alder Contact Services | Do not infer simultaneous requests from 45,000 daily items. |
| S02 | Bracken Engineering | Do not count the whole retrieval chain as two text-generation calls. |
| S03 | Cobalt Travel Operations | Preserve variable call expansion. do not replace it with one call. |
| S04 | Dune Accounting | Keep item count and deadline distinct from concurrent users. |
| S05 | Estuary Transit | Recognise streaming without routing camera frames through the text sizing equation. |
| S06 | Fable Creative Studio | Request specialised generation evidence. never infer demand from text tokens alone. |
| S07 | Grove Legal Technology | Do not silently apply full-pretraining memory or compute equations. |
| S08 | Helix Language Institute | Identify training and request ingestion/checkpoint detail rather than hiding those resources. |
| S09 | Juniper Retail | Create separate operating scenarios. no automatic addition of non-overlapping peaks. |
| S10 | Kestrel Field Services | Retain indexing as supporting work. do not infer zero GPU or CPU demand. |
| S11 | Larch Media Archive | Keep visual inference separate from text serving and do not treat the proposed arrows as proven latency. |
| S12 | Morrow Advertising | Preserve conditional relationship without treating it as an unconditional workload multiplier. |
| S13 | Nacre Customer Portal | Never recommend local model GPUs merely because the application uses AI. |
| S14 | Orchid Neocloud | Do not equate customer count with GPU count or a proven tenancy limit. |
| S15 | Peregrine Product Lab | Unknown must remain unknown. candidate patterns must not imply confirmed absence of retrieval or agents. |
| S16 | Quartz Industrial Research | Do not force a simulation into a language-model or training profile. |

See [scenario fixtures](tests/fixtures/architecture-scenarios.json) and [catalogue check results](testing-evidence/scenario-catalogue.json). Passing software checks do not qualify physical GPU performance. Fixture-provider tests do not qualify live Copilot interpretation.

## User playbooks

Four distinct scenarios were drawn randomly from all 16, without replacement or filtering. Each Word playbook covers both the manual and live Copilot-assisted routes, with an input register, architecture map, numbered screenshot instructions, token setup, parameter collection guidance and retrieval of saved outcomes.

| Scenario | Word playbook | Verified outcome |
|---|---|---|
| S13 Nacre Customer Portal | [Download playbook](docs/playbooks/S13_Nacre_Customer_Portal_Playbook.docx) | Outside model boundary retained. Report-only closure. |
| S14 Orchid Neocloud | [Download playbook](docs/playbooks/S14_Orchid_Neocloud_Playbook.docx) | Dedicated and shared groups retained. Missing per-group demand remains unresolved. |
| S16 Quartz Industrial Research | [Download playbook](docs/playbooks/S16_Quartz_Industrial_Research_Playbook.docx) | Simulation remains outside text-model sizing. Report-only closure. |
| S11 Larch Media Archive | [Download playbook](docs/playbooks/S11_Larch_Media_Archive_Playbook.docx) | Video and text activities remain distinct. Specialist evidence is required. |

These selected scenarios do not supply enough information for a complete GPU estimate. Their successful endpoint is a saved final-status report, not an invented design handoff. All eight manual/assisted walkthroughs reached that endpoint and were retrieved after reload. Three live provider requests timed out before explicit retries succeeded. Exact model wording can vary. See the [selection and validation record](testing-evidence/playbooks/validation.json).

## Technical documents

PDF editions are included under `docs`:

- [Anubis workload sizing methodology](docs/Anubis_Workload_Sizing_Methodology.pdf), version 2.1, SME evaluation edition dated 2 November 2026. Author: Traiano Giuseppe Welcome.
- [Anubis technical solution architecture](docs/Anubis_Technical_Architecture.pdf), SME evaluation edition 1.0 dated 2 November 2026.

The PDFs describe the methodology and implementation boundaries. The current walkthrough evidence is dated 3 November 2026 and is recorded separately. Future qualification goals in the documents are not completed release claims.

## Repository scope

This repository starts with a fresh source snapshot, without predecessor Git history. It includes application source, tests, configuration and technical documentation. Historical customer exports, generated document/media archives, local credentials and databases are excluded. Some document-generation utilities refer to historical assets that are not included. They are not needed to build or run Anubis.

The repository is publicly readable and cloneable. Push access is restricted to authorized maintainers. Third-party notices are retained under third_party. Public visibility does not grant additional software licence rights.
