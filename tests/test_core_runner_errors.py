from __future__ import annotations
from dataclasses import dataclass
import importlib
import pytest

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
