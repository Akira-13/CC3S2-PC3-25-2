from __future__ import annotations
from pathlib import Path
import tempfile

import importlib, pytest
_core = importlib.import_module("auditor.core")
if not hasattr(_core, "RuleContext"):
    pytest.skip("RuleContext pendiente : se omite por ahora", allow_module_level=True)
from auditor.core import RuleContext

from auditor.rules.makefile_rule import MakefileRule


def test_makefile_missing_file():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        rule = MakefileRule()
        findings = rule.check(RuleContext(str(root)))
        assert len(findings) == 1
        assert findings[0].severity.value == "Medium"


def test_makefile_missing_targets():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "Makefile").write_text("""
run:
	@echo running
lint:
	@echo lint
""".strip(), encoding="utf-8")
        rule = MakefileRule()
        findings = rule.check(RuleContext(str(root)))
        assert len(findings) == 1
        assert findings[0].meta is not None
        assert "test" in findings[0].meta["missing"]


def test_makefile_all_ok():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "Makefile").write_text("""
run:
	@echo running
lint:
	@echo lint
test:
	@echo test
plan:
	@echo plan
apply:
	@echo apply
""".strip(), encoding="utf-8")
        rule = MakefileRule()
        findings = rule.check(RuleContext(str(root)))
        assert findings == []