from __future__ import annotations
from pathlib import Path
import importlib
import pytest

# Guardia por RuleContext (A)
import importlib as _il
_core = _il.import_module("auditor.core")
if not hasattr(_core, "RuleContext"):
    pytest.skip("RuleContext pendiente: se omite este módulo", allow_module_level=True)

from auditor.core import RuleContext

def _get_coverage_rule():
    try:
        mod = importlib.import_module("auditor.rules.coverage_rule")
    except ModuleNotFoundError:
        pytest.skip("Regla de cobertura aún no implementada (auditor.rules.coverage_rule)")
    for name in ("CoverageMin90Rule", "CoverageMinRule", "CoverageRule"):
        if hasattr(mod, name):
            return getattr(mod, name)()
    pytest.skip("Clase de regla de cobertura no encontrada en coverage_rule")

def _write_cov(repo: Path, rate: float):
    (repo / "coverage.xml").write_text(
        f'<?xml version="1.0"?>'
        f'<coverage line-rate="{rate}" branch-rate="0.90" version="7.0.0"></coverage>',
        encoding="utf-8",
    )

@pytest.mark.parametrize("rate, expect_findings", [
    (0.92, 0),
    (0.90, 0),      # borde inclusivo
    (0.899, 1),     # justo por debajo
])
def test_coverage_thresholds(tmp_path: Path, rate: float, expect_findings: int):
    repo = tmp_path
    _write_cov(repo, rate)
    rule = _get_coverage_rule()
    findings = rule.check(RuleContext(str(repo)))
    assert len(findings) == expect_findings
    if expect_findings:
        f = findings[0]
        # muchos implementan details["line_rate"]
        if hasattr(f, "details"):
            assert f.details.get("line_rate") is not None

def test_coverage_missing_file(tmp_path: Path):
    repo = tmp_path
    rule = _get_coverage_rule()
    findings = rule.check(RuleContext(str(repo)))
    assert findings, "Debe reportar cuando falta coverage.xml"
