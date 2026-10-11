# flet-notifications example

Every API on one screen, with a timestamped event log: show, action buttons
with inline reply, scheduling, styles, channels, progress, grouping,
per-platform options, the foreground service and every probe.

```bash
uv run flet run src/main.py   # desktop preview (no notifications — prebuilt client)
uv run flet build apk --yes --project notifications --org ng.kiri -v
uv run flet-notifications-patch --project-root build/flutter
cd build/flutter/android && ./gradlew assembleRelease -Psplit-per-abi=true
```
