#!/bin/sh
set -eu

VERSION="1.1.0"
PACKAGE="freak-media-player"
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BUILD_ROOT="$ROOT/build/linux"
DIST_ROOT="$ROOT/dist/linux"
PYINSTALLER_DIST="$BUILD_ROOT/pyinstaller-dist"
APP_SOURCE="$PYINSTALLER_DIST/FreakMediaPlayer"
ARCH=$(uname -m)

case "$ARCH" in
    x86_64) DEB_ARCH="amd64"; RPM_ARCH="x86_64" ;;
    aarch64|arm64) DEB_ARCH="arm64"; RPM_ARCH="aarch64" ;;
    *) echo "Unsupported architecture: $ARCH" >&2; exit 1 ;;
esac

rm -rf "$BUILD_ROOT" "$DIST_ROOT"
mkdir -p "$BUILD_ROOT" "$DIST_ROOT"

python3 -m PyInstaller --noconfirm --clean \
    --distpath "$PYINSTALLER_DIST" \
    --workpath "$BUILD_ROOT/pyinstaller-work" \
    "$ROOT/FreakMediaPlayer.dev.spec"

make_payload() {
    destination="$1"
    mkdir -p "$destination/FreakMediaPlayer"
    cp -R "$APP_SOURCE/." "$destination/FreakMediaPlayer/"
    install -m 0755 "$ROOT/packaging/linux/install.sh" "$destination/install.sh"
    install -m 0755 "$ROOT/packaging/linux/freak-media-player" "$destination/freak-media-player"
    install -m 0644 "$ROOT/packaging/linux/freak-media-player.desktop" "$destination/freak-media-player.desktop"
    install -m 0644 "$ROOT/src/freak_media_player/assets/app_logo.png" "$destination/freak-media-player.png"
    install -m 0644 "$ROOT/README.md" "$destination/README.md"
    install -m 0644 "$ROOT/THIRD_PARTY_NOTICES.md" "$destination/THIRD_PARTY_NOTICES.md"
}

TAR_NAME="FreakMediaPlayer-$VERSION-linux-$ARCH"
TAR_STAGE="$BUILD_ROOT/$TAR_NAME"
make_payload "$TAR_STAGE"
tar -C "$BUILD_ROOT" -czf "$DIST_ROOT/$TAR_NAME.tar.gz" "$TAR_NAME"

if command -v dpkg-deb >/dev/null 2>&1; then
    DEB_ROOT="$BUILD_ROOT/deb"
    mkdir -p "$DEB_ROOT/DEBIAN" "$DEB_ROOT/opt/$PACKAGE" \
        "$DEB_ROOT/usr/bin" "$DEB_ROOT/usr/share/applications" \
        "$DEB_ROOT/usr/share/icons/hicolor/256x256/apps" \
        "$DEB_ROOT/usr/share/doc/$PACKAGE"
    cp -R "$APP_SOURCE/." "$DEB_ROOT/opt/$PACKAGE/"
    ln -s "/opt/$PACKAGE/FreakMediaPlayer" "$DEB_ROOT/usr/bin/freak-media-player"
    install -m 0644 "$ROOT/packaging/linux/freak-media-player.desktop" "$DEB_ROOT/usr/share/applications/freak-media-player.desktop"
    install -m 0644 "$ROOT/src/freak_media_player/assets/app_logo.png" "$DEB_ROOT/usr/share/icons/hicolor/256x256/apps/freak-media-player.png"
    install -m 0644 "$ROOT/README.md" "$DEB_ROOT/usr/share/doc/$PACKAGE/README.md"
    install -m 0644 "$ROOT/THIRD_PARTY_NOTICES.md" "$DEB_ROOT/usr/share/doc/$PACKAGE/THIRD_PARTY_NOTICES.md"
    printf '%s\n' \
        'Package: freak-media-player' \
        "Version: $VERSION" \
        'Section: sound' \
        'Priority: optional' \
        "Architecture: $DEB_ARCH" \
        'Maintainer: Freak Media Player contributors' \
        'Depends: libc6, libgl1, libxkbcommon-x11-0, libxcb-cursor0' \
        'Description: Native desktop player for local audio and internet radio' \
        > "$DEB_ROOT/DEBIAN/control"
    dpkg-deb --root-owner-group --build "$DEB_ROOT" "$DIST_ROOT/${PACKAGE}_${VERSION}_${DEB_ARCH}.deb"
else
    echo "dpkg-deb not found; skipped .deb package."
fi

if command -v rpmbuild >/dev/null 2>&1; then
    RPM_TOP="$BUILD_ROOT/rpmbuild"
    mkdir -p "$RPM_TOP/BUILD" "$RPM_TOP/BUILDROOT" "$RPM_TOP/RPMS" "$RPM_TOP/SOURCES" "$RPM_TOP/SPECS" "$RPM_TOP/SRPMS"
    PAYLOAD_TAR="$RPM_TOP/SOURCES/$PACKAGE-$VERSION.tar.gz"
    tar -C "$TAR_STAGE" -czf "$PAYLOAD_TAR" .
    sed \
        -e "s/@VERSION@/$VERSION/g" \
        -e "s/@ARCH@/$RPM_ARCH/g" \
        "$ROOT/packaging/linux/freak-media-player.spec.in" \
        > "$RPM_TOP/SPECS/freak-media-player.spec"
    rpmbuild --define "_topdir $RPM_TOP" -bb "$RPM_TOP/SPECS/freak-media-player.spec"
    find "$RPM_TOP/RPMS" -name '*.rpm' -exec cp {} "$DIST_ROOT/" \;
else
    echo "rpmbuild not found; skipped .rpm package."
fi

(cd "$DIST_ROOT" && sha256sum ./* > SHA256SUMS.txt)
echo "Linux release artifacts written to $DIST_ROOT"
