"""Build the submission zip for the CDU IT Code Fair 2026 AI Challenge.

Run from the repo root with the project interpreter:
    venv/Scripts/python scripts/package_submission.py --team <N>
Refuses to run on a dirty working tree or a red quality gate. Writes
dist/AI-Challenge_Team-<N>_FairTurn.zip from a fixed include list, walking directories;
the zip is deterministic (sorted entries, fixed timestamps) so a rerun is byte-identical.
"""

import argparse
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ``submission/`` holds the team's report PDF and slides (see submission/README.md).
INCLUDE_DIRS = ("fair_turn", "scripts", "tests", "data/build", "data/geo", "submission")
INCLUDE_FILES = (
    "data/raw/PROVENANCE.md",
    "data/raw/nt_fs17_repairs_and_maintenance_2025-10.pdf",
    "data/audit/sample.jsonl",
    "docs/PRODUCT.md",
    "docs/user-guide.md",
    "constants.md",
    "README.md",
    "pyproject.toml",
    "requirements.txt",
    "uv.lock",
    ".streamlit/config.toml",
)
EXCLUDE_SEGMENTS = {
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".hypothesis",
    "venv",
    ".venv",
    "runtime",
}
ZIP_DATE_TIME = (2026, 1, 1, 0, 0, 0)


def dirty_paths(root: Path = ROOT) -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True
    )
    return result.stdout.strip()


def gate_exit_code(root: Path = ROOT) -> int:
    return subprocess.run([sys.executable, str(root / "scripts" / "gate.py")], cwd=root).returncode


def _is_excluded(path: Path) -> bool:
    return any(part in EXCLUDE_SEGMENTS for part in path.parts) or path.suffix == ".pyc"


def _iter_include_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    for rel_dir in INCLUDE_DIRS:
        base = root / rel_dir
        if not base.is_dir():
            continue
        for file_path in base.rglob("*"):
            if file_path.is_file() and not _is_excluded(file_path.relative_to(root)):
                paths.append(file_path)
    for rel_file in INCLUDE_FILES:
        file_path = root / rel_file
        if file_path.is_file():
            paths.append(file_path)
    return sorted(set(paths), key=lambda p: p.relative_to(root).as_posix())


def build_zip(out_dir: Path, team: str, root: Path = ROOT) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"AI-Challenge_Team-{team}_FairTurn.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in _iter_include_paths(root):
            arcname = file_path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(arcname, date_time=ZIP_DATE_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, file_path.read_bytes())
    return zip_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--team", required=True)
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    parser.add_argument("--skip-gate", action="store_true")
    args = parser.parse_args(argv)

    # Step 1: refuse on an uncommitted change, so the zip always matches a committed state.
    dirty = dirty_paths()
    if dirty:
        print(f"package_submission: working tree is dirty:\n{dirty}", file=sys.stderr)
        return 1

    # Step 2: refuse on a red gate, unless explicitly skipped.
    if not args.skip_gate:
        code = gate_exit_code()
        if code:
            print(f"package_submission: gate is red (exit {code})", file=sys.stderr)
            return 1

    # Step 3: walk the fixed include list and write the deterministic zip.
    zip_path = build_zip(args.out, args.team)
    size = zip_path.stat().st_size
    print(f"{zip_path} ({size} bytes)")
    # Step 4: the report is a required deliverable the code cannot write; say loudly when it
    # is missing rather than ship a zip that silently lacks it.
    if not any((ROOT / "submission").glob("*.pdf")):
        print(
            "package_submission: WARNING no report PDF in submission/ - the zip has none",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
