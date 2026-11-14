#!/usr/bin/env bash
# Build a signed, notarized and stapled Anubis.dmg for Apple Silicon Macs.
#
#   packaging/macos/build-dmg.sh <version>
#
# Environment:
#   ANUBIS_SIGN_IDENTITY  Developer ID Application identity (name or SHA-1). Required.
#   ANUBIS_NOTARY_PROFILE notarytool keychain profile (default: anubis-notary).
#                         Create it with: xcrun notarytool store-credentials anubis-notary ...
#   ANUBIS_SKIP_NOTARIZE  Set to 1 for a signed but un-notarized local test build.
#   ANUBIS_BUNDLE_ID      Default: com.engeneon.anubis
set -euo pipefail

VERSION="${1:?usage: build-dmg.sh <version>}"
IDENTITY="${ANUBIS_SIGN_IDENTITY:?set ANUBIS_SIGN_IDENTITY to a Developer ID Application identity}"
PROFILE="${ANUBIS_NOTARY_PROFILE:-anubis-notary}"
BUNDLE_ID="${ANUBIS_BUNDLE_ID:-com.engeneon.anubis}"
MIN_MACOS=13.0
ARCH=arm64
OPENSSL_VERSION=3.5.9
OPENSSL_SHA256=603f5602e2eef00d77fbd429d34dcd5822bb301757a1bc9cdb24c670f1eb859a

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HERE="$ROOT/packaging/macos"
WORK="$ROOT/build-macos"
DEPS="$WORK/deps"
APP="$WORK/Anubis.app"
DMG="$WORK/Anubis-$VERSION-macos-$ARCH.dmg"
export MACOSX_DEPLOYMENT_TARGET="$MIN_MACOS"
JOBS="$(sysctl -n hw.ncpu)"
cd "$ROOT"

step() { printf '\n==> %s\n' "$*"; }

# 1. OpenSSL, static, built for the minimum macOS so the app does not require the build Mac's OS.
if [[ ! -f "$DEPS/openssl/lib/libssl.a" ]]; then
  step "Building OpenSSL $OPENSSL_VERSION (static, macOS $MIN_MACOS+)"
  mkdir -p "$DEPS/src"
  tarball="$DEPS/src/openssl-$OPENSSL_VERSION.tar.gz"
  [[ -f "$tarball" ]] || curl -fsSL -o "$tarball" \
    "https://github.com/openssl/openssl/releases/download/openssl-$OPENSSL_VERSION/openssl-$OPENSSL_VERSION.tar.gz"
  echo "$OPENSSL_SHA256  $tarball" | shasum -a 256 -c -
  rm -rf "$DEPS/src/openssl-$OPENSSL_VERSION"
  tar -xzf "$tarball" -C "$DEPS/src"
  (cd "$DEPS/src/openssl-$OPENSSL_VERSION" &&
    ./Configure darwin64-arm64-cc no-shared no-tests no-docs no-apps \
      --prefix="$DEPS/openssl" --libdir=lib "-mmacosx-version-min=$MIN_MACOS" >/dev/null &&
    make -j"$JOBS" >/dev/null && make install_sw >/dev/null)
fi

# 2. Server binary (Release). SQLite comes from the macOS SDK.
step "Building anubis server"
SDK="$(xcrun --sdk macosx --show-sdk-path)"
cmake -S . -B "$WORK/cmake" -G "Unix Makefiles" -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_OSX_ARCHITECTURES="$ARCH" -DCMAKE_OSX_DEPLOYMENT_TARGET="$MIN_MACOS" \
  -DOPENSSL_ROOT_DIR="$DEPS/openssl" -DOPENSSL_USE_STATIC_LIBS=TRUE \
  -DSQLite3_INCLUDE_DIR="$SDK/usr/include" -DSQLite3_LIBRARY="$SDK/usr/lib/libsqlite3.tbd" >/dev/null
cmake --build "$WORK/cmake" -j"$JOBS" --target anubis anubis_tests anubis_characterization_tests
ctest --test-dir "$WORK/cmake" --output-on-failure

# 3. Browser UI.
step "Building UI"
npm ci --ignore-scripts --no-audit --no-fund
npm run build

# 4. Native launcher.
step "Building Anubis.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources/anubis"
xcrun swiftc -O -target "$ARCH-apple-macos$MIN_MACOS" -framework Cocoa -framework WebKit \
  "$HERE/AnubisApp.swift" -o "$APP/Contents/MacOS/Anubis"
cp "$WORK/cmake/anubis" "$APP/Contents/MacOS/anubis-server"
res="$APP/Contents/Resources/anubis"
mkdir -p "$res/ui" "$res/tests"
cp -R ui/dist "$res/ui/dist"
cp -R contracts knowledge "$res/"
cp -R tests/fixtures "$res/tests/fixtures"
cp LICENSE NOTICE "$APP/Contents/Resources/"
sed -e "s/@VERSION@/$VERSION/" -e "s/@BUILD@/$VERSION/" -e "s/@BUNDLE_ID@/$BUNDLE_ID/" \
  -e "s/@MIN_MACOS@/$MIN_MACOS/" "$HERE/Info.plist.in" >"$APP/Contents/Info.plist"
plutil -lint "$APP/Contents/Info.plist" >/dev/null

iconset="$WORK/Anubis.iconset"
rm -rf "$iconset" && mkdir -p "$iconset"
for s in 16 32 128 256 512; do
  sips -z $s $s ui/assets/anubis-logo.png --out "$iconset/icon_${s}x${s}.png" >/dev/null
  sips -z $((s * 2)) $((s * 2)) ui/assets/anubis-logo.png --out "$iconset/icon_${s}x${s}@2x.png" >/dev/null
done
iconutil -c icns "$iconset" -o "$APP/Contents/Resources/Anubis.icns"

# Refuse to ship anything that links outside the OS.
for bin in "$APP/Contents/MacOS/"*; do
  if otool -L "$bin" | tail -n +2 | grep -vE '^\s*(/usr/lib/|/System/Library/)'; then
    echo "error: $bin links a non-system library" >&2; exit 1
  fi
done

# 5. Sign inside-out with the hardened runtime and a secure timestamp.
step "Signing"
sign() { codesign --force --timestamp --options runtime --entitlements "$HERE/entitlements.plist" -s "$IDENTITY" "$@"; }
sign --identifier "$BUNDLE_ID.server" "$APP/Contents/MacOS/anubis-server"
sign "$APP"
codesign --verify --deep --strict --verbose=2 "$APP"

notarize() {  # notarize <file>: submit, wait, print Apple's log on rejection
  local out="$WORK/notary-$(basename "$1").log"
  xcrun notarytool submit "$1" --keychain-profile "$PROFILE" --wait --timeout 1h | tee "$out"
  if ! grep -q 'status: Accepted' "$out"; then
    local id; id="$(awk '/^  id:/{print $2; exit}' "$out")"
    [[ -n "$id" ]] && xcrun notarytool log "$id" --keychain-profile "$PROFILE" >&2
    exit 1
  fi
}
skip_notary() { [[ "${ANUBIS_SKIP_NOTARIZE:-0}" == 1 ]]; }

# Staple the app itself so it opens offline after being copied out of the DMG.
if ! skip_notary; then
  step "Notarizing Anubis.app (this usually takes a few minutes)"
  ditto -c -k --keepParent "$APP" "$WORK/Anubis-app.zip"
  notarize "$WORK/Anubis-app.zip"
  xcrun stapler staple "$APP"
  rm -f "$WORK/Anubis-app.zip"
fi

# 6. DMG with an Applications shortcut.
step "Creating DMG"
stage="$WORK/dmg"
rm -rf "$stage" "$DMG" && mkdir -p "$stage"
cp -R "$APP" "$stage/"
ln -s /Applications "$stage/Applications"
hdiutil create -volname "Anubis $VERSION" -srcfolder "$stage" -fs HFS+ -format UDZO -ov "$DMG" >/dev/null
codesign --force --timestamp -s "$IDENTITY" "$DMG"

# 7. Notarize and staple the DMG.
if skip_notary; then
  echo "warning: skipping notarization; Gatekeeper will block this DMG on other Macs" >&2
else
  step "Notarizing DMG"
  notarize "$DMG"
  xcrun stapler staple "$DMG"
  xcrun stapler validate "$DMG"
  spctl --assess --type open --context context:primary-signature --verbose=2 "$DMG"
  spctl --assess --type execute --verbose=2 "$APP"
fi

(cd "$WORK" && shasum -a 256 "$(basename "$DMG")" >"$(basename "$DMG").sha256")
step "Done: $DMG"
cat "$DMG.sha256"
