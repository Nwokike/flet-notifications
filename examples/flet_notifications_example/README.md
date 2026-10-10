# flet-notifications example

Demonstrates the full `flet-notifications` API on one screen: immediate
notifications, action buttons with inline reply, cancellation, scheduling
(one-shot, recurring, periodic), styles, Android channels, progress,
grouping, the foreground service, and every platform probe. Each button
writes to the event log so CI-built artifacts can be verified on device.

Run it during development with `uv run flet run src/main.py`
(desktop preview; notifications need a platform build) and package it for
a device with:

```bash
uv run flet build apk --yes --project notifications --org ng.kiri -v
uv run flet-notifications-patch --project-root build/flutter
cd build/flutter/android && ./gradlew assembleRelease
```
