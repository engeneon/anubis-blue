# Documentation site validation

The static site builder validates all local page and asset links. The browser check visits nine pages at 390px and 1440px widths, verifies one primary heading per page, checks for horizontal page overflow and browser errors, loads all screenshots, and checks file signatures and content types for six PDFs and four Word downloads.

Run `python3 scripts/build_docs_site.py`, then `node scripts/validate_docs_site.mjs`. See `local-validation.json` for the recorded 28 successful checks. Representative mobile and desktop screenshots were visually reviewed. The four playbook PDFs contain the token instructions, manual and assisted workflows, and saved-result explanations.

This change publishes documentation only. It does not change application sizing, APIs, persistence or workflow behaviour.
