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

The [16 GPU-complete customer scenarios](docs/gpu-complete-scenarios.md) include exact intake values, explicit planning assumptions, expected B300/B200/H200 counts and handoff success criteria. Use these completed scenarios for customer demonstrations. The original incomplete descriptions are retained separately as negative tests, not as successful sizing playbooks.

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

Counts use the explicit fictional planning inputs in the linked catalogue. Reference capacities are example assumptions, not benchmark measurements.

After building, run `python3 scripts/validate_scenario_catalogue.py`. Run `npx playwright test tests/ui/gpu-readiness.spec.ts tests/ui/mvp.spec.ts` to validate manual and assisted intake, missing-field warnings, reference sizing and handoff journeys. See [recorded GPU and handoff results](testing-evidence/gpu-readiness/scenario-results.json).

Intake now shows **GPU estimate blocked** and names the minimum missing fields before calculation. For specialist workloads, select **Reference capacity for independent work** and provide matching demand, memory and separately sourced H200/B200/B300 capacity assumptions. These are planning estimates, not a claim of measured hardware performance. Unknown inputs remain visible and never become invented GPU counts.

## Explain saved results

Select **Explain this to me** from calculation results or Design handoff. Choose a tested Copilot connection for plain-language prose, or use the deterministic explanation without an LLM. The explanation covers workload GPUs versus factory size, memory, storage, all four network roles and missing requirements. It cannot change the calculation or submit a handoff. Saved narratives remain linked to their exact result and can be downloaded or retrieved later.

Corporate data requires a connection approved for corporate processing. The public/fictional option is intended for explicitly public examples. Failed or invalid model responses use a labelled deterministic fallback. See [Copilot operation](docs/copilot-operation.txt) and [explanation validation](testing-evidence/explanations/README.md).

## Complete customer playbooks

Each Word guide includes both manual and Copilot-assisted routes through GPU estimates, design handoff, explanation and saved completion, with exact input tables, diagrams and screenshots.

| Scenario | Word playbook |
|---|---|
| S11 Larch Media Archive | [Video analysis and archive assistant](docs/playbooks/S11_Larch_Media_Archive_Playbook.docx) |
| S13 Nacre Customer Portal | [Hosted service with local continuity fallback](docs/playbooks/S13_Nacre_Customer_Portal_Playbook.docx) |
| S14 Orchid Neocloud | [Reserved premium and shared standard pools](docs/playbooks/S14_Orchid_Neocloud_Playbook.docx) |
| S16 Quartz Industrial Research | [Independent GPU simulation groups](docs/playbooks/S16_Quartz_Industrial_Research_Playbook.docx) |

The [technical architecture PDF](docs/Anubis_Technical_Architecture.pdf) and [workload methodology PDF](docs/Anubis_Workload_Sizing_Methodology.pdf) include the implementation addendum for complete-scenario sizing and read-only explanations.

## Repository scope

This repository starts with a fresh source snapshot, without predecessor Git history. It includes application source, tests, configuration and technical documentation. Historical customer exports, generated document/media archives, local credentials and databases are excluded. Some document-generation utilities refer to historical assets that are not included. They are not needed to build or run Anubis.

The repository is publicly readable and cloneable. Push access is restricted to authorized maintainers. Third-party notices are retained under third_party. Anubis is licensed under Apache License 2.0.

## Licence and attribution

Anubis is open-source software under the [Apache License 2.0](LICENSE), free for personal and commercial use. Created by **Traiano Giuseppe Welcome**. Redistributors must preserve applicable licence and attribution notices. See [NOTICE](NOTICE) and the [licensing guide](docs/licensing.md) for scope and third-party terms.
