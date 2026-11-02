# Anubis Blue

Anubis is a deterministic AI Factory workload sizing application with an optional, human-reviewed Consultant Copilot. It estimates GPU requirements, records assumptions, and exports requirements for a downstream AI Factory design tool or process.

## Install on macOS

Follow the [Mac installation guide](docs/macos-installation-guide.txt), including first-login access-token setup, restarting, backup and recovery. The evaluated platform is Apple Silicon. Linux installation guidance is deferred.

## Use the application

- [MVP workflow and supported scope](docs/mvp-1.0-guide.txt)
- [Copilot configuration and operation](docs/copilot-operation.txt)
- [Application sizing guide](docs/usability-user-guide.html)
- [Methodology](docs/anubis-framework-v2.txt)
- [Architecture](docs/anubis-technical-architecture.md)

Manual sizing does not require a model provider. Live Copilot calls require a separately configured backend API credential and provider account. No credentials or customer databases are distributed here.

## Validate

After installing dependencies and building as documented:

```sh
ctest --test-dir build --output-on-failure
npx playwright install chromium
npm run test:mvp
python3 scripts/test_local_restart.py
```

The MVP browser checks use a fixture provider. They verify software behaviour, not live-model interpretation or physical GPU performance. Estimates are planning outputs, not hardware performance guarantees.

## Repository scope

This repository starts with a fresh source snapshot, without predecessor Git history. It includes application source, tests, configuration and technical documentation. Historical customer exports, generated document/media archives, local credentials and databases are excluded. Some document-generation utilities refer to historical assets that are not included. They are not needed to build or run Anubis.

The repository is publicly readable and cloneable. Push access is restricted to authorized maintainers. Third-party notices are retained under third_party. Public visibility does not grant additional software licence rights.
