from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, List, Dict, Any


class Severity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

@dataclass
class Finding:
    rule_id: str
    message: str
    severity: Severity
    path: str | None = None
    meta: Dict[str, Any] | None = None

class RuleContext:
    def __init__(self, repo_root: str, ignore_dirs: list[str] | None = None):
        self.repo_root = repo_root
        self.ignore_dirs = ignore_dirs or []

class Rule(Protocol):
    id: str
    description: str

    def check(self, ctx: RuleContext) -> List[Finding]:
        ...

# Runner simple para ejecutar un conjunto de reglas
def run_rules(ctx: RuleContext, rules: List[Rule]) -> List[Finding]:
    findings: List[Finding] = []
    for rule in rules:
        try:
            findings.extend(rule.check(ctx))
        except Exception as exc: # proteger el runner
            findings.append(
                Finding(
                    rule_id=rule.id,
                    message=f"Rule crashed: {exc}",
                    severity=Severity.MEDIUM,
                    meta={"crash": True},
                )
            )
    return findings