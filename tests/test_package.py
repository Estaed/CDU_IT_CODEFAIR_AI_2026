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


def test_zip_includes_the_fs17_pdf(monkeypatch):
    monkeypatch.setattr(ps, "dirty_paths", lambda root=ps.ROOT: "")
    monkeypatch.setattr(ps, "gate_exit_code", lambda root=ps.ROOT: 0)

    names = {p.relative_to(ps.ROOT).as_posix() for p in ps._iter_include_paths(ps.ROOT)}

    fs17 = "data/raw/nt_fs17_repairs_and_maintenance_2025-10.pdf"
    if (ps.ROOT / fs17).is_file():
        assert fs17 in names
    else:
        pytest.skip(f"{fs17} absent in this worktree")


def test_zip_excludes_runtime_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(ps, "dirty_paths", lambda root=ps.ROOT: "")
    monkeypatch.setattr(ps, "gate_exit_code", lambda root=ps.ROOT: 0)

    fake_root = tmp_path / "repo"
    for rel_dir in ps.INCLUDE_DIRS:
        (fake_root / rel_dir).mkdir(parents=True, exist_ok=True)
        (fake_root / rel_dir / "keep.txt").write_text("x", encoding="utf-8")
    runtime_dir = fake_root / "data" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime.jsonl").write_text("{}\n", encoding="utf-8")

    out_dir = tmp_path / "dist"
    zip_path = ps.build_zip(out_dir, "9", root=fake_root)
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()

    assert not any("data/runtime" in name for name in names)
    assert "data/runtime/runtime.jsonl" not in names


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
