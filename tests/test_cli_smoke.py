from __future__ import annotations
from pathlib import Path
import json
import importlib
import pytest

@pytest.fixture
def cli_module():
    return importlib.import_module("auditor.cli")

def _write_coverage(root: Path, pct: float) -> None:
    xml = f"<coverage line-rate='{pct:.2f}'><packages/></coverage>"
    (root / "coverage.xml").write_text(xml, encoding="utf-8")


def test_cli_good_repo(good_repo: Path, capsys, cli_module):
    """Repo válido debe retornar 0 findings y exit code 0"""
    _write_coverage(good_repo, 0.95)
    
    exit_code = cli_module.main(["--repo", str(good_repo)])
    out = capsys.readouterr().out
    data = json.loads(out)
    
    assert exit_code == 0
    assert data["summary"]["total"] == 0


def test_cli_bad_repo(bad_repo: Path, capsys, cli_module):
    """Repo inválido debe reportar 5 findings esperados"""
    exit_code = cli_module.main(["--repo", str(bad_repo)])
    out = capsys.readouterr().out
    data = json.loads(out)
    
    # Debe detectar: R001, R002, R003, license.present, R005
    rule_ids = {f["rule_id"] for f in data["findings"]}
    expected = {"R001", "R002", "R003", "license.present", "R005"}
    
    assert exit_code == 0  # --fail-on=none por defecto
    assert expected.issubset(rule_ids)
    assert data["summary"]["by_severity"]["High"] >= 2


def test_cli_fail_on_high(bad_repo: Path, cli_module):
    """--fail-on high debe retornar exit 2 cuando hay findings High"""
    exit_code = cli_module.main(["--repo", str(bad_repo), "--fail-on", "high"])
    assert exit_code == 2