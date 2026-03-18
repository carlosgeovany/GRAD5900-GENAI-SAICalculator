from __future__ import annotations

from pathlib import Path


WORKBOOK_SUFFIXES = (".xlsm", ".xlsx", ".xls")
POLICY_SUFFIXES = (".pdf", ".txt", ".md")


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def find_workbook() -> Path | None:
    candidates = [
        project_root() / "data" / "models",
        project_root() / "data" / "policy",
    ]
    for directory in candidates:
        if not directory.exists():
            continue
        for suffix in WORKBOOK_SUFFIXES:
            matches = sorted(directory.glob(f"*{suffix}"))
            if matches:
                return matches[0]
    return None


def find_policy_dir() -> Path:
    return project_root() / "data" / "policy"


def find_policy_documents() -> list[Path]:
    directory = find_policy_dir()
    if not directory.exists():
        return []
    matches: list[Path] = []
    for suffix in POLICY_SUFFIXES:
        matches.extend(sorted(directory.glob(f"*{suffix}")))
    return matches
