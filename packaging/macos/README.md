# macOS app and DMG

`build-dmg.sh` builds `Anubis.app` and a signed, notarized and stapled DMG for Apple Silicon (macOS 13+).

## What the app is

- `Contents/MacOS/Anubis` is a small Swift window (`AnubisApp.swift`). It starts the bundled server, sets the session cookie and shows the UI in a WKWebView. Quitting the app stops the server.
- `Contents/MacOS/anubis-server` is the normal `anubis` binary. OpenSSL is linked statically. SQLite comes from macOS.
- `Contents/Resources/anubis` is the server's `--root`: `ui/dist`, `contracts`, `knowledge` and `tests/fixtures`.

## Where data lives

| What | Path |
|---|---|
| Database | `~/Library/Application Support/Anubis/anubis.sqlite` |
| Access token | `~/Library/Application Support/Anubis/identities.json` (created on first launch) |
| Provider keys (optional) | `~/Library/Application Support/Anubis/.env`, same format as the source install |
| Neon target (optional) | `~/Library/Application Support/Anubis/neon-target.json` |
| Server log | `~/Library/Logs/Anubis/server.log` |

The app uses port 8787, or the next free port up to 8887. The backup script works on the app database too:

```sh
python3 scripts/backup.py backup "$HOME/Library/Application Support/Anubis/anubis.sqlite" "$HOME/Anubis-backups/backup-01.sqlite"
```

## Build a release

Needs Xcode, CMake, Node and a `Developer ID Application` certificate in the keychain. Save the notary login once:

```sh
xcrun notarytool store-credentials anubis-notary --apple-id <apple-id> --team-id <team-id>
```

Then:

```sh
ANUBIS_SIGN_IDENTITY="<cert name or SHA-1>" packaging/macos/build-dmg.sh 0.0.1
```

The DMG and its `.sha256` land in `build-macos/`. Set `ANUBIS_SKIP_NOTARIZE=1` for a quick local test build. Gatekeeper blocks that build on other Macs.

The script builds OpenSSL from a pinned, checksummed tarball, runs the C++ tests, signs inside-out with the hardened runtime, notarizes and staples the app, then notarizes and staples the DMG.
