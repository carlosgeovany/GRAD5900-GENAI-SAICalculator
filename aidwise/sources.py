from __future__ import annotations

from pathlib import Path


POLICY_SUFFIXES = (".pdf", ".txt", ".md")


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


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


def template_csv_path() -> Path:
    return project_root() / "data" / "templates" / "student_input_template.csv"
