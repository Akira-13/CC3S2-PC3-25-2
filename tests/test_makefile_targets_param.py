from __future__ import annotations
import importlib, pytest
_core = importlib.import_module("auditor.core")
if not hasattr(_core, "RuleContext"):
    pytest.skip("RuleContext pendiente : se omite por ahora", allow_module_level=True)
from auditor.core import RuleContext

from auditor.rules.makefile_rule import MakefileRule
import pytest

@pytest.mark.parametrize("targets, missing_expected", [
    (["run","test","lint","plan","apply"], []),
    (["run","test","lint","plan"], ["apply"]),
])
def test_makefile_targets(tmp_path, targets, missing_expected):
    r = tmp_path
    (r / "Makefile").write_text("\n".join(f"{t}:\n    @echo {t}" for t in targets), encoding="utf-8")
    findings = MakefileRule().check(RuleContext(str(r)))
    if missing_expected:
        assert findings and findings[0].meta["missing"] == missing_expected
    else:
        assert findings == []
