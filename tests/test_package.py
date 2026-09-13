"""Submission packaging (Task-20 acceptance criteria)."""

import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import package_submission as ps  # noqa: E402

MAX_ZIP_BYTES = 15 * 1024 * 1024


def test_zip_contains_include_roots_and_excludes_forbidden_segments(tmp_path, monkeypatch):
    monkeypatch.setattr(ps, "dirty_paths", lambda root=ps.ROOT: "")
    monkeypatch.setattr(ps, "gate_exit_code", lambda root=ps.ROOT: 0)

    zip_path = ps.build_zip(tmp_path, "9")
    assert zip_path.exists()
    assert zip_path.stat().st_size < MAX_ZIP_BYTES

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()

    for include_dir in ps.INCLUDE_DIRS:
        assert any(name.startswith(f"{include_dir}/") for name in names), include_dir
    for include_file in ps.INCLUDE_FILES:
        if (ps.ROOT / include_file).is_file():
            assert include_file in names, include_file

    for name in names:
        assert not any(segment in ps.EXCLUDE_SEGMENTS for segment in name.split("/")), name
        assert not name.endswith(".pyc"), name


def test_main_refuses_on_dirty_tree(tmp_path, monkeypatch):
    monkeypatch.setattr(ps, "dirty_paths", lambda root=ps.ROOT: "M some/file.py")
    monkeypatch.setattr(ps, "gate_exit_code", lambda root=ps.ROOT: 0)

    code = ps.main(["--team", "9", "--out", str(tmp_path), "--skip-gate"])

    assert code != 0
    assert list(tmp_path.glob("*.zip")) == []


def test_main_refuses_on_red_gate(tmp_path, monkeypatch):
    monkeypatch.setattr(ps, "dirty_paths", lambda root=ps.ROOT: "")
    monkeypatch.setattr(ps, "gate_exit_code", lambda root=ps.ROOT: 1)

    code = ps.main(["--team", "9", "--out", str(tmp_path)])

    assert code != 0
    assert list(tmp_path.glob("*.zip")) == []


def test_main_skip_gate_builds_zip_when_clean(tmp_path, monkeypatch):
    monkeypatch.setattr(ps, "dirty_paths", lambda root=ps.ROOT: "")
    monkeypatch.setattr(ps, "gate_exit_code", lambda root=ps.ROOT: pytest.fail("gate must not run"))

    code = ps.main(["--team", "9", "--out", str(tmp_path), "--skip-gate"])

    assert code == 0
    assert list(tmp_path.glob("AI-Challenge_Team-9_FairTurn.zip"))
