from __future__ import annotations
from pathlib import Path
from typing import Iterable

def read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except FileNotFoundError:
        return []

def find_repo_root(start: str | Path) -> Path:
    # Por simplicidad, asumimos start es la raíz
    return Path(start).resolve()

def ensure_paths_exist(root: Path, rel_paths: Iterable[str]) -> dict[str, bool]:
    out: dict[str, bool] = {}
    for p in rel_paths:
        out[p] = (root / p).exists()
    return out