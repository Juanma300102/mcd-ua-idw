"""Tests for script discovery."""

import importlib
from pathlib import Path

import pytest

from mcd_ua_idw.script_runner.discovery import discover_scripts


def write_module(package: Path, name: str, source: str) -> None:
    (package / f"{name}.py").write_text(source, encoding="utf-8")


def test_discover_scripts_detects_async_run_with_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = tmp_path / "sample_scripts"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    write_module(
        package,
        "valid",
        'NAME = "Valid script"\nVERSION = 3\nasync def run(session):\n    return {}\n',
    )
    write_module(package, "sync_run", "VERSION = 1\ndef run(session):\n    return {}\n")
    write_module(package, "no_session", "VERSION = 1\nasync def run():\n    return {}\n")
    write_module(package, "helper", "VALUE = 1\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()

    scripts = discover_scripts("sample_scripts")

    assert [script.name for script in scripts] == ["Valid script"]
    assert scripts[0].module_name == "sample_scripts.valid"
    assert scripts[0].version == 3


def test_discover_scripts_uses_module_slug_as_default_display_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = tmp_path / "default_scripts"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    write_module(
        package,
        "load_people",
        "VERSION = 1\nasync def run(session):\n    return {}\n",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()

    scripts = discover_scripts("default_scripts")

    assert len(scripts) == 1
    assert scripts[0].name == "load_people"
    assert scripts[0].version == 1
    assert scripts[0].slug == "load_people"


def test_discover_scripts_requires_version_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = tmp_path / "missing_version_scripts"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    write_module(package, "bad", "async def run(session):\n    return {}\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()

    with pytest.raises(ValueError, match="VERSION is required"):
        discover_scripts("missing_version_scripts")


def test_discover_scripts_rejects_invalid_version(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = tmp_path / "bad_scripts"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    write_module(package, "bad", "VERSION = 0\nasync def run(session):\n    return {}\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()

    with pytest.raises(ValueError, match="VERSION"):
        discover_scripts("bad_scripts")
