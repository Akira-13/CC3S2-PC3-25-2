from __future__ import annotations
from pathlib import Path
import json
import importlib

def _write_coverage_ok(root: Path, pct: float = 0.95) -> None:
    # line-rate ∈ [0,1]; con 0.95 cumplimos el umbral 0.90
    xml = f"<coverage line-rate='{pct:.2f}'><packages/></coverage>"
    (root / "coverage.xml").write_text(xml, encoding="utf-8")

def _assert_no_findings(out: str):
    data = json.loads(out)
    assert not data.get("findings"), f"Esperaba 0 findings, obtuve: {data.get('findings')}"

def _assert_has_findings(out: str):
    data = json.loads(out)
    assert data.get("findings"), "Esperaba findings, pero la lista está vacía"

def test_cli_smoke_good_repo(good_repo: Path, capsys):
    # Asegura que la regla de cobertura NO reporte nada
    _write_coverage_ok(good_repo, 0.95)

    cli = importlib.import_module("auditor.cli")
    cli.main(["--repo", str(good_repo)])
    out = capsys.readouterr().out
    _assert_no_findings(out)

def test_cli_smoke_bad_repo(bad_repo: Path, capsys):
    cli = importlib.import_module("auditor.cli")
    cli.main(["--repo", str(bad_repo)])
    out = capsys.readouterr().out
    _assert_has_findings(out)
