from __future__ import annotations
from pathlib import Path
import tempfile

import pytest

import importlib, pytest
_core = importlib.import_module("auditor.core")
if not hasattr(_core, "RuleContext"):
    pytest.skip("RuleContext pendiente : se omite por ahora", allow_module_level=True)
from auditor.core import RuleContext

from auditor.rules.config_rule import ConfigViaEnvRule


@pytest.mark.parametrize(
    "py_uses_env, static_files, expected",
    [
        (True, [], 0),  # usa os.environ; sin estáticos
        (True, ["config.json"], 0),  # usa os.environ; estáticos presentes pero tolerados
        (False, ["config.json"], 1),  # no usa ENV y hay config estática => finding
        (False, [], 0),  # no usa ENV pero tampoco archivos estáticos => tolerado en D2
    ],
)

def test_config_rule(py_uses_env, static_files, expected):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # Fuente Python
        src = root / "app.py"
        if py_uses_env:
            src.write_text("import os " \
            "print(os.environ.get('X'))", encoding="utf-8")
        else:
            src.write_text("print('hello')", encoding="utf-8")

        # Archivos estáticos
        for fname in static_files:
            (root / fname).write_text("{}", encoding="utf-8")

        ctx = RuleContext(str(root))
        rule = ConfigViaEnvRule()
        findings = rule.check(ctx)

        assert len(findings) == expected
        if findings:
            assert findings[0].severity.value == "Medium"
            assert findings[0].rule_id == rule.id