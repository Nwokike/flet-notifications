"""Tests for the Android post-build patcher."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from flet_notifications.patcher import patch_gradle, patch_manifest

ANDROID_NS = "http://schemas.android.com/apk/res/android"

MANIFEST_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.example.app">
    <uses-permission android:name="android.permission.INTERNET" />
    <application
        android:label="app"
        android:icon="@mipmap/ic_launcher">
        <activity
            android:name=".MainActivity"
            android:exported="true" />
    </application>
</manifest>
"""

GRADLE_TEMPLATE = """android {
    namespace = "com.example.app"
    defaultConfig {
        applicationId = "com.example.app"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
    }
    dependencies {}
}
"""


@pytest.fixture
def manifest(tmp_path: Path) -> Path:
    path = tmp_path / "AndroidManifest.xml"
    path.write_text(MANIFEST_TEMPLATE, encoding="utf-8")
    return path


@pytest.fixture
def gradle(tmp_path: Path) -> Path:
    path = tmp_path / "build.gradle.kts"
    path.write_text(GRADLE_TEMPLATE, encoding="utf-8")
    return path


def _root(manifest: Path) -> ET.Element:
    return ET.parse(manifest).getroot()


def _receiver_names(manifest: Path) -> set[str]:
    app = _root(manifest).find("application")
    return {r.get(f"{{{ANDROID_NS}}}name") for r in app.findall("receiver")}


def test_patch_adds_receivers_and_permissions(manifest: Path):
    changed = patch_manifest(manifest)
    receivers = _receiver_names(manifest)
    assert (
        "com.dexterous.flutterlocalnotifications.ActionBroadcastReceiver" in receivers
    )
    assert (
        "com.dexterous.flutterlocalnotifications.ScheduledNotificationReceiver"
        in receivers
    )
    assert (
        "com.dexterous.flutterlocalnotifications.ScheduledNotificationBootReceiver"
        in receivers
    )
    root = _root(manifest)
    perms = {e.get(f"{{{ANDROID_NS}}}name") for e in root.findall("uses-permission")}
    assert "android.permission.POST_NOTIFICATIONS" in perms
    assert "android.permission.RECEIVE_BOOT_COMPLETED" in perms
    assert "android.permission.SCHEDULE_EXACT_ALARM" in perms
    assert "android.permission.INTERNET" in perms  # untouched
    assert len(changed) >= 7


def test_patch_is_idempotent(manifest: Path):
    first = patch_manifest(manifest)
    assert first  # something changed
    snapshot = manifest.read_text(encoding="utf-8")
    second = patch_manifest(manifest)
    assert second == []
    assert manifest.read_text(encoding="utf-8") == snapshot


def test_boot_receiver_gets_intent_filters(manifest: Path):
    patch_manifest(manifest)
    app = _root(manifest).find("application")
    boot = next(
        r
        for r in app.findall("receiver")
        if r.get(f"{{{ANDROID_NS}}}name", "").endswith(
            "ScheduledNotificationBootReceiver"
        )
    )
    actions = {
        e.get(f"{{{ANDROID_NS}}}name")
        for f in boot.findall("intent-filter")
        for e in f.findall("action")
    }
    assert "android.intent.action.BOOT_COMPLETED" in actions
    assert "android.intent.action.QUICKBOOT_POWERON" in actions
    assert boot.get(f"{{{ANDROID_NS}}}exported") == "false"


def test_gradle_patch_enables_desugaring(gradle: Path):
    changed = patch_gradle(gradle)
    text = gradle.read_text(encoding="utf-8")
    assert "isCoreLibraryDesugaringEnabled = true" in text
    assert "desugar_jdk_libs:2.1.4" in text
    assert "multiDexEnabled = true" in text
    assert len(changed) == 3


def test_gradle_patch_is_idempotent(gradle: Path):
    patch_gradle(gradle)
    snapshot = gradle.read_text(encoding="utf-8")
    assert patch_gradle(gradle) == []
    assert gradle.read_text(encoding="utf-8") == snapshot


def test_gradle_patch_missing_file_is_noop(tmp_path: Path):
    assert patch_gradle(tmp_path / "nope.kts") == []
