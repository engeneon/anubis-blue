# Customer documentation website

Published from `anubis-blue/main` at https://engeneon.github.io/anubis-blue/.

The site is static documentation. It does not host the Anubis application, accept customer workloads or include access tokens. The application runs on the user's Mac.

Run `python3 scripts/build_docs_site.py` to rebuild `_site`. The builder uses the existing validated scenario catalogue, playbook steps, screenshots, input registers and versioned PDF/Word editions. It checks local links before returning success. `_site` is generated and excluded from Git.

Run `node scripts/validate_docs_site.mjs` after building to check desktop and mobile layouts, images, console errors and PDF/Word downloads. Install Playwright Chromium first if necessary. `ANUBIS_CHROMIUM_PATH` optionally selects an existing Chromium executable. The check uses a temporary local HTTP server and does not call model providers.

GitHub Actions publishes on relevant changes to main. A workflow dispatch can republish without changing source. GitHub Pages is configured to use GitHub Actions. Preserve that setting when maintaining the repository.

Customer wording and site structure are in `scripts/build_docs_site.py`. Canonical screenshot instructions and inputs remain in `deliverables/complete-playbooks`. If application behaviour changes, recapture affected workflows and regenerate Word and PDF editions before republishing. Keep all editions aligned.

The four PDF files in `docs/playbooks` are rendered editions of the corresponding Word documents. Website download links provide normal document files. README links make PDFs primary and explicitly label Word downloads. Do not make a raw Word file the main customer entry point.
