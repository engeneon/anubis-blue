# Documentation site validation

The static site builder validates all local page and asset links. The browser check visits nine pages at 390px and 1440px widths, verifies one primary heading per page, checks for horizontal page overflow and browser errors, loads all screenshots, and checks file signatures and content types for six PDFs and four Word downloads.

Run `python3 scripts/build_docs_site.py`, then `node scripts/validate_docs_site.mjs`. See `local-validation.json` for the recorded 28 successful checks. Representative mobile and desktop screenshots were visually reviewed. The four playbook PDFs contain the token instructions, manual and assisted workflows, and saved-result explanations.

This change publishes documentation only. It does not change application sizing, APIs, persistence or workflow behaviour.

Live publication verification: all nine HTML pages and ten PDF/Word downloads returned HTTP 200. Download content types were confirmed as PDF or Word rather than text. A mobile browser followed the homepage action to Getting Started and found the access-token bootstrap instructions. See `live-validation.json`. GitHub Pages deployment run: https://github.com/engeneon/anubis-blue/actions/runs/41605474261.
