from __future__ import annotations
from pathlib import Path
import importlib
import pytest

# Guardia por RuleContext (A)
import importlib as _il
_core = _il.import_module("auditor.core")
if not hasattr(_core, "RuleContext"):
    pytest.skip("RuleContext pendiente : se omite este módulo", allow_module_level=True)

from auditor.core import RuleContext

def _get_license_rule():
    try:
        mod = importlib.import_module("auditor.rules.license_rule")
    except ModuleNotFoundError:
        pytest.skip("Regla de licencia aún no implementada (auditor.rules.license_rule)")
    for name in ("LicensePresentRule", "LicenseRule", "LicenseCheck"):
        if hasattr(mod, name):
            return getattr(mod, name)()
    pytest.skip("Clase de regla de licencia no encontrada en license_rule")

@pytest.mark.parametrize("name, empty, expect_findings", [
    ("LICENSE", False, 0),
    ("LICENSE.md", False, 0),
    ("COPYING", False, 0),
    ("NOTICE", False, 0),
    ("LICENSE", True, 1),
])
def test_license_variants(tmp_path: Path, name: str, empty: bool, expect_findings: int):
    repo = tmp_path
    (repo / name).write_text("   \n" if empty else "MIT License\n", encoding="utf-8")
    rule = _get_license_rule()
    findings = rule.check(RuleContext(str(repo)))
    assert len(findings) == expect_findings
    # chequeos suaves si hay findings
    if findings:
        f = findings[0]
        assert getattr(f, "rule_id", "license.present").startswith("license")

def test_license_missing(tmp_path: Path):
    rule = _get_license_rule()
    findings = rule.check(RuleContext(str(tmp_path)))
    assert findings, "Debe reportar ausencia de licencia"

