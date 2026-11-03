# Saved-result explanation validation

Date: 3 November 2026.

The new **Explain this to me** action explains an immutable saved calculation at results and Design handoff. It supports approved model connections and a deterministic, model-free option. Explanations are separate persistent records with exact-result provenance.

## Results

| Check | Result | Evidence |
|---|---|---|
| Sixteen deterministic scenario estimates and explanation fixtures | Passed | `fixture-scenarios.json`, `tests/test_explanations.py` |
| Sixteen live DeepSeek explanations | All model-assisted, original results unchanged | `live-validation.json`, `S01-live-explanation.json` through `S16-live-explanation.json` |
| Missing demand and failed memory feasibility | No complete recommendation invented | `tests/test_explanations.py` |
| Extra numerical claim | Rejected and deterministic fallback saved | `tests/test_explanations.py` |
| Access control, classification policy and projection matching | Passed | `tests/test_explanations.py` |
| API explanation tests | 4 passed | `explanation-tests.log` |
| Existing Copilot regression | 17 passed | `copilot-tests.log` |
| Interpretation regression | 52 passed | `interpretation-tests.log` |
| Scenario catalogue | 12 checks passed, all 16 scenarios covered | `scenario-tests.log` |
| Browser regression | 11 passed, including explanation generation and history | `ui-tests.log` |

Live validation used public fictional examples, the configured DeepSeek `deepseek-flash` model and an isolated database. No production customer cases were modified. Raw credentials and private provider configuration are excluded.

The server inserts the numerical facts. The model supplies short qualitative interpretation. Literal numerical-claim and placeholder checks do not prove every qualitative statement correct. Consultants retain responsibility for reviewing interpretation. These checks do not establish hardware performance or a statistical error bound.

## Repeat

Build the C++ application and UI, then run:

```sh
python3 scripts/validate_scenario_catalogue.py
python3 tests/test_explanations.py
python3 tests/test_copilot.py
python3 tests/test_interpretation.py
npx playwright test
```

The tests use local fixture providers and do not require paid provider access. Live requalification requires an approved provider connection and its backend credential. Keep configuration outside published evidence. The GUI capture script accepts `ANUBIS_PLAYBOOK_CONFIG`, pointing to a private JSON object with local `base`, test `token`, tested `profile_id` and profile metadata. Capture each route with `node scripts/capture_complete_playbooks.mjs S11 manual` or `assisted`. Never publish that configuration file.

## Defects resolved during validation

- Serve the new browser module explicitly through the local API static route.
- Initialize explanation job retry state and strip stored health metadata before adapter validation.
- Use server-owned fact markers, concise model prose and at most one bounded corrective request.
- Preserve provider-profile checks before dispatch and publication.
- Extend the existing bounded transport read timeout from 40 to 120 seconds for longer valid provider responses. The explanation UI continues to show progress and can retrieve a completed result after the panel is closed.
- Make screenshot capture wait for proposal application and guided review completion instead of racing UI redraws.

## Illustrated customer walkthroughs

`playbook-validation.json` records all eight completed GUI journeys. Manual and live Copilot routes agree for each scenario:

| Scenario | B300 GPUs | B200 GPUs | H200 GPUs | Assisted explanation |
|---|---:|---:|---:|---|
| S11 Larch | 24 | 24 | 32 | Model-assisted |
| S13 Nacre | 8 | 8 | 8 | Model-assisted |
| S14 Orchid | 16 | 16 | 16 | Model-assisted |
| S16 Quartz | 16 | 16 | 24 | Model-assisted |

All routes prepared the selected 256-GPU factory-anchor handoff, saved an explanation and completed the engagement. Unknown storage and network requirements remain in the companion specification. Screenshot source artifacts contain fictional scenarios only. Word outputs are in `docs/playbooks`. `document-qa.json` records rendering checks. The installed application restart preserved all 35 pre-existing cases.

The public checkout also passed a fresh C++ build, both CTest suites and TypeScript build. Separate public-checkout explanation and scenario test logs are included. These tests validate the same source delivered in both repositories.
