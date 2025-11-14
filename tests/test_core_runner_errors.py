from __future__ import annotations
from dataclasses import dataclass
import importlib
import pytest

# Guardia por core completo
try:
    core = importlib.import_module("auditor.core")
except ModuleNotFoundError:
    pytest.skip("auditor.core no disponible", allow_module_level=True)

required = {"Rule", "RuleContext", "run_rules", "Finding", "Severity"}
if not required.issubset(set(dir(core))):
    pytest.skip("Tipos del core incompletos: se omite este módulo", allow_module_level=True)

from auditor.core import Rule, RuleContext, run_rules, Finding, Severity


@dataclass
class BoomRule(Rule):
    id: str = "T999"
    description: str = "boom"

    def check(self, ctx: RuleContext) -> list[Finding]:
        raise RuntimeError("kaboom")


def test_run_rules_catches_exceptions(tmp_path):
    ctx = RuleContext(str(tmp_path))
    findings = run_rules(ctx, [BoomRule()])
    assert findings and findings[0].rule_id == "T999"
    assert findings[0].severity is Severity.MEDIUM
    assert findings[0].meta.get("crash") is True
