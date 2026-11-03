# GPU readiness and complete-scenario acceptance

The revised 16 scenarios all produce positive B300, B200 and H200 workload counts and a valid local design-handoff payload. See `scenario-results.json` for the counts and `validation-summary.json` for the verification scope.

The reference route repeats complete independent GPU groups from explicitly supplied capacities. Demonstration capacities are fictional planning assumptions, not benchmark evidence. The original incomplete scenarios remain separate boundary fixtures.

Run after building:

```sh
python3 scripts/validate_scenario_catalogue.py
npx playwright test
```

The GUI checks cover early missing-field warnings, click-to-field navigation, disabled calculation while incomplete, correction and recalculation, specialist reference sizing, Copilot preflight, and existing handoff/completion flows. The final targeted browser run follows the removal of irrelevant text-model metadata from reference outputs.

The installed smoke check used a separate browser session on port 8787. It did not create a saved case. Restart verification found the same 35 saved cases before and after restarting the application.
