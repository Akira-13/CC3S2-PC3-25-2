from __future__ import annotations
from pathlib import Path
from typing import List
import re

from auditor.core import Finding, Rule, RuleContext, Severity

class LicenseRule(Rule):
    id = "R004"
    description = "El repositorio debe tener un archivo de licencia válido"
    
    LICENSE_FILES = ["LICENSE", "LICENSE.txt", "COPYING", "COPYING.txt"]
    
    def check(self, ctx: RuleContext) -> List[Finding]:
        repo = Path(ctx.repo_root)
        
        # Buscar archivos de licencia
        for lic_file in self.LICENSE_FILES:
            license_path = repo / lic_file
            if license_path.exists() and license_path.stat().st_size > 0:
                return [
                    Finding(
                        rule_id=self.id,
                        message=f"Licencia válida encontrada: {lic_file}",
                        severity=Severity.LOW,
                        path=str(license_path)
                    )
                ]
        
        # No se encontró licencia
        return [
            Finding(
                rule_id=self.id,
                message="No se encontró archivo de licencia válido",
                severity=Severity.HIGH,
                path=str(repo),
                meta={"suggested_files": self.LICENSE_FILES}
            )
        ]