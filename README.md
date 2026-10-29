# THIS PROJECT HAS BEEN ARCHIVED

`flet-notifications` is now part of the main [Flet repository](https://github.com/flet-dev/flet/tree/main/sdk/python/packages/flet-notifications).

# flet-notifications

[![pypi](https://img.shields.io/pypi/v/flet-notifications.svg)](https://pypi.python.org/pypi/flet-notifications)
[![python](https://img.shields.io/badge/python-%3E%3D3.10-%2334D058)](https://pypi.org/project/flet-notifications)
[![license](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/Nwokike/flet-notifications/blob/main/LICENSE)

Cross-platform local notifications for [Flet](https://flet.dev) apps.

A 1:1 wrapping of the official [flutter_local_notifications](https://pub.dev/packages/flutter_local_notifications) Flutter plugin. One `uv add flet-notifications` covers Android, iOS, macOS, Windows, Linux and Web — no Python dependencies beyond `flet` (verified on Flet 0.85.0 through 1.0.x in CI).

## Documentation

Detailed documentation to this package can be found [here](https://flet.dev/docs/services/notifications/).

## Test it first

Every release builds the example app for every platform. Sideload any of them and every button is live:

| Variant | Download | Notes |
| :--- | :---: | :--- |
| 📱 **ARM64** (most phones/TVs) | [**app-arm64-v8a-release.apk**](https://github.com/Nwokike/flet-notifications/releases/latest/download/app-arm64-v8a-release.apk) | Modern 64-bit Android devices — grab this one unless you know otherwise |
| 📱 **ARMv7** (older phones/TV boxes) | [**app-armeabi-v7a-release.apk**](https://github.com/Nwokike/flet-notifications/releases/latest/download/app-armeabi-v7a-release.apk) | Legacy 32-bit Android devices |
| 💻 **x86_64** (emulators/ChromeOS) | [**app-x86_64-release.apk**](https://github.com/Nwokike/flet-notifications/releases/latest/download/app-x86_64-release.apk) | Android emulators & Chromebooks |
| 🖥️ **Windows** | [**flet-notifications-example-windows.zip**](https://github.com/Nwokike/flet-notifications/releases/latest/download/flet-notifications-example-windows.zip) | Portable zip |
| 🍎 **macOS** | [**flet-notifications-example-macos.dmg**](https://github.com/Nwokike/flet-notifications/releases/latest/download/flet-notifications-example-macos.dmg) | Disk image |
| 🐧 **Linux** | [**tar.gz**](https://github.com/Nwokike/flet-notifications/releases/latest/download/flet-notifications-example-linux-x86_64.tar.gz) · [**deb**](https://github.com/Nwokike/flet-notifications/releases/latest/download/flet-notifications-example_amd64.deb) · [**rpm**](https://github.com/Nwokike/flet-notifications/releases/latest/download/flet-notifications-example_x86_64.rpm) | Bundle or packages |
| 🌐 **Web** | [**flet-notifications-example-web.tar.gz**](https://github.com/Nwokike/flet-notifications/releases/latest/download/flet-notifications-example-web.tar.gz) | Static bundle |

Plain `flet run` launches the prebuilt client without the extension's Dart half — notifications need a built app (an artifact above, or `flet build <platform>`).

## Platform Support

| Platform | Show | Schedule | Actions & callbacks | Channels | Progress | Notes |
|----------|:----:|:--------:|:-------------------:|:--------:|:--------:|-------|
| iOS      |  ✅  |    ✅    |         ✅          |    —     |    —     | 13+; attachments, interruption levels |
| Android  |  ✅  |    ✅    |         ✅          |    ✅    |    ✅    | 7.0+ (API 24); Android TV works |
| macOS    |  ✅  |    ✅    |         ✅          |    —     |    —     | 10.15+ |
| Windows  |  ✅  | one-shot |         ✅          |    —     |    ✅    | 10+; `cancel`/queries need MSIX identity |
| Linux    |  ✅  |    —     |         ✅          |    —     |    —     | D-Bus server; capabilities vary |
| Web      |  ✅  |    —     |   Chrome/Edge only  |    —     |    —     | Notifications API; gesture-gated permissions |


## License

MIT
