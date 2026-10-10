# Phase 5 — Example Completion, All-Platform Build CI & Release

**Goal:** the example app exercises every API; CI builds the example for every
platform (ktv-player's `build-all.yml` pattern, plus the notification
patcher for Android); then the house release ritual.

## 1. Example app — probe buttons

Add to the Phase 3 row: **Are enabled**, **Open settings**, **Active list**,
**Launch details**, **Policy access** — with in-app status/log lines so the
CI-built artifacts demonstrate the full surface on real devices.

## 2. CI: `build-all.yml` (ktv-player pattern)

```
quality (ruff + pytest, blocks all)
  → prepare-release (tag/placeholder)
    → build-windows   (portable zip + Inno installer)
    → build-apk-split (flet build → flet-notifications-patch → gradlew assembleRelease)
    → build-aab       (same patch flow)
    → build-linux     (tar.gz, .deb, .rpm via fpm)
    → build-macos     (macos-latest runner, .dmg)
    → build-web       (static build, uploaded for preview)
```

Key differences from ktv-player:
- Android jobs run `uv run flet-notifications-patch --project-root
  build/flutter` after the first `flet build` pass (tolerant of the
  desugaring failure), then rebuild with `./gradlew assembleRelease`.
- No keystore secret available yet: APKs are debug-signed or unsigned in CI
  until the owner wires `KEYSTORE_BASE64` (noted in the workflow comments).
- iOS is **not** built in CI: it needs Apple signing, which is owner-side.
  Documented in the README.

`publish.yml` (tag `v*`): `uv build` → `pypa/gh-action-pypi-publish` with
Trusted Publisher (OIDC), exactly like flet-yandex-ads.

## 3. Owner-side prerequisite (flagged, not blocking code)

PyPI **pending trusted publisher** for project `flet-notifications`:
owner `Nwokike`, repo `Nwokike/flet-notifications`, workflow `publish.yml`,
environment `release`. Without it the first publish can't authenticate.
Everything else is in place.

## 4. Release ritual (house standard)

1. 3-agent independent verification swarm: API-parity agent (Python surface
   vs upstream plugin docs), packaging agent (wheel contents, package-data,
   example build config), tests/CI agent (run everything, audit the matrix).
2. Tag `v0.1.0` annotated, push.
3. Watch ALL CI jobs to completion (compat + publish + every build job).
4. Replace the placeholder release body with house-format release notes.
5. Confirm PyPI listing + `uvx --from flet-notifications python -c
   "import flet_notifications; print(flet_notifications.__all__)"`.
