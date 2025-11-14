from __future__ import annotations
from pathlib import Path
import importlib
from unittest.mock import patch
from auditor.core import RuleContext

def test_license_io_error_reports_high(tmp_path: Path):
    mod = importlib.import_module("auditor.rules.license_rule")
    rule = getattr(mod, "LicenseRule")()

    p = tmp_path / "LICENSE"
    p.write_text("MIT\n", encoding="utf-8")

    # forzamos error al leer
    with patch.object(type(p), "read_text", autospec=True, side_effect=OSError("boom")):
        findings = rule.check(RuleContext(str(tmp_path)))
    assert findings and findings[0].severity.name.lower() == "high"
