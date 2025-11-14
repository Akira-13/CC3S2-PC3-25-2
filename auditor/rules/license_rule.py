from __future__ import annotations
from pathlib import Path
from typing import List
from auditor.core import Rule, RuleContext, Finding, Severity

class LicenseRule(Rule):
    id: str = "license.present"
    description: str = "El proyecto debe incluir una licencia válida en la raíz"

    _CANDIDATES = [
        "LICENSE",
        "LICENSE.txt",
        "LICENSE.md",
        "COPYING",
        "COPYING.txt",
        "NOTICE",
    ]

    def check(self, ctx: RuleContext) -> List[Finding]:
        root = Path(ctx.repo_root)

        for name in self._CANDIDATES:
            p = root / name
            if p.exists():
                try:
                    content = p.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    content = ""
                if content.strip():
                    # Caso válido: sin findings
                    return []
                # Licencia vacía
                return [
                    Finding(
                        rule_id=self.id,
                        message="Licencia vacía",
                        severity=Severity.HIGH,
                        path=str(p),
                    )
                ]

        # No se encontró archivo de licencia aceptado
        return [
            Finding(
                rule_id=self.id,
                message="No se encontró archivo de licencia válido",
                severity=Severity.HIGH,
                path=str(root),
                meta={"suggested_files": self._CANDIDATES},
            )
        ]
