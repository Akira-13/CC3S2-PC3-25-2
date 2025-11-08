from __future__ import annotations
from pathlib import Path
from typing import List, Set
import re

from auditor.core import Finding, RuleContext, Severity
from auditor.utils.fs import read_lines


class MakefileRule:
    """
    R003: Verificar Makefile y targets mínimos.
    Targets requeridos: run, test, lint, plan, apply
    """

    id = "R003"
    description = "Makefile debe incluir targets: run, test, lint, plan, apply"

    REQUIRED: Set[str] = {"run", "test", "lint", "plan", "apply"}

    def _targets_in(self, makefile: Path) -> Set[str]:
        targets: Set[str] = set()
        tgt_pat = re.compile(r"^([A-Za-z0-9._-]+):")
        for line in read_lines(makefile):
            m = tgt_pat.match(line.strip())
            if m:
                targets.add(m.group(1))
        return targets

    def check(self, ctx: RuleContext) -> List[Finding]:
        root = Path(ctx.repo_root)
        mf = root / "Makefile"

        if not mf.exists():
            return [
                Finding(
                    rule_id=self.id,
                    message="No se encontró Makefile en la raíz del repositorio",
                    severity=Severity.MEDIUM,
                    path=str(mf),
                    meta={"required": sorted(self.REQUIRED)},
                )
            ]

        present = self._targets_in(mf)
        missing = sorted(self.REQUIRED - present)

        if missing:
            return [
                Finding(
                    rule_id=self.id,
                    message=f"Faltan targets obligatorios en Makefile: {', '.join(missing)}",
                    severity=Severity.MEDIUM,
                    path=str(mf),
                    meta={"present": sorted(present), "missing": missing},
                )
            ]

        return []