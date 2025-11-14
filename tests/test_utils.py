from __future__ import annotations
from pathlib import Path

from auditor.utils.fs import read_lines, ensure_paths_exist


def test_read_lines_missing(tmp_path: Path) -> None:
    """
    Si el archivo no existe, read_lines debe devolver lista vacía.
    """
    missing = tmp_path / "no_such_file.txt"
    lines = read_lines(missing)
    assert lines == []


def test_ensure_paths_exist(tmp_path: Path) -> None:
    """
    Debe retornar un mapa {ruta_relativa: bool} indicando existencia por ruta.
    """
    # prepara estructura
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    # 'dir/x' no existe; 'b.txt' tampoco
    result = ensure_paths_exist(tmp_path, ["a.txt", "b.txt", "dir/x"])

    assert result == {
        "a.txt": True,
        "b.txt": False,
        "dir/x": False,
    }
