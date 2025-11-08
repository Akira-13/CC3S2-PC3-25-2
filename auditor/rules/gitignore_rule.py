from __future__ import annotations
from pathlib import Path
from typing import List
from auditor.core import Finding, Rule, RuleContext, Severity
from auditor.utils.fs import read_lines

class GitignoreEnvRule(Rule):
    id = "R001"
    description = "`.env` debe estar listado en .gitignore"

    def check(self, ctx: RuleContext) -> List[Finding]:
        repo = Path(ctx.repo_root)
        gi = repo / ".gitignore"
        lines = [l.strip() for l in read_lines(gi)]
        has_env = any(l == ".env" or l.endswith("/.env") for l in lines)

        if not lines: # .gitignore faltante
            return [
                Finding(
                    rule_id=self.id,
                    message="No se encontró .gitignore en la raíz del repositorio",
                    severity=Severity.HIGH,
                    path=str(gi),
                    meta={"hint": "Crea .gitignore e incluye la entrada .env"},
                )
            ]

        if not has_env:
            return [
                Finding(
                    rule_id=self.id,
                    message="El patrón '.env' no está presente en .gitignore",
                    severity=Severity.HIGH,
                    path=str(gi),
                    meta={"example": ".env"},
                )
            ]
        return []