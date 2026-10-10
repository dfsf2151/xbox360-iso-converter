#!/usr/bin/env bash
# Builds Xbox360-ISO-Converter-x86_64.AppImage from prebuilt release binaries.
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

ISO2GOD_URL=https://github.com/iliazeus/iso2god-rs/releases/download/v1.8.1/iso2god-x86_64-linux
XISO_URL=https://github.com/XboxDev/extract-xiso/releases/download/build-202609111233/extract-xiso_Linux.zip
TOOL_URL=https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
PY_PAGE=https://github.com/niess/python-appimage/releases/expanded_assets/python3.12

mkdir -p dl
[ -f dl/iso2god ] || curl -fsSL -o dl/iso2god "$ISO2GOD_URL"
[ -f dl/xiso.zip ] || curl -fsSL -o dl/xiso.zip "$XISO_URL"
[ -f dl/appimagetool ] || curl -fsSL -o dl/appimagetool "$TOOL_URL"
if [ ! -f dl/python.AppImage ]; then
    py=$(curl -fsSL "$PY_PAGE" | grep -o 'href="[^"]*manylinux2014_x86_64.AppImage"' | sed 's/href="//;s/"$//' | tail -1)
    curl -fsSL -o dl/python.AppImage "https://github.com$py"
fi
chmod +x dl/iso2god dl/appimagetool dl/python.AppImage
rm -rf dl/xiso && python3 -I -m zipfile -e dl/xiso.zip dl/xiso

rm -rf AppDir squashfs-root
(cd dl && ./python.AppImage --appimage-extract >/dev/null && mv squashfs-root ../AppDir)
A=AppDir
rm -f $A/AppRun $A/python*.desktop $A/python.png $A/.DirIcon
mkdir -p $A/usr/bin $A/usr/share/x360
install -m755 dl/iso2god dl/xiso/extract-xiso $A/usr/bin/
install -m755 xbox360-iso-gui.py $A/usr/share/x360/
cp dl/xiso/LICENSE.TXT $A/usr/share/x360/extract-xiso-LICENSE.txt
cp packaging/iso2god-LICENSE.txt $A/usr/share/x360/
install -m755 packaging/AppRun $A/
cp packaging/xbox360-iso-converter.desktop packaging/xbox360-iso-converter.svg $A/
ln -sf xbox360-iso-converter.svg $A/.DirIcon

ARCH=x86_64 dl/appimagetool --appimage-extract-and-run -n $A Xbox360-ISO-Converter-x86_64.AppImage
