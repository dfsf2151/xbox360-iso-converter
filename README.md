# Xbox 360 ISO Converter

A small Linux app that converts an Xbox 360 (or original Xbox) ISO into:

- **GOD** (Games on Demand) — recommended for USB drives and Aurora
- **XEX** — an extracted folder with `default.xex`

It detects a mounted USB drive and saves to the right place automatically
(`Content/0000000000000000` for GOD, `Games/` for XEX).

## Download

Grab `Xbox360-ISO-Converter-x86_64.AppImage` from the Releases page, then:

```bash
chmod +x Xbox360-ISO-Converter-x86_64.AppImage
./Xbox360-ISO-Converter-x86_64.AppImage
```

Works on distributions with glibc 2.34 or newer (Ubuntu 22.04+, Debian 12+, Fedora 35+, Arch, Mint 21+).
Nothing else needs to be installed: Python, Tk and the conversion tools are bundled.

## Build

```bash
./build-appimage.sh
```

## Credits

- [iso2god-rs](https://github.com/iliazeus/iso2god-rs) — ISO to GOD conversion (MIT)
- [extract-xiso](https://github.com/XboxDev/extract-xiso) — ISO extraction
- [python-appimage](https://github.com/niess/python-appimage) — bundled Python with Tk
