from __future__ import annotations
from pathlib import Path
from typing import List, Optional
import xml.etree.ElementTree as ET

from auditor.core import Finding, Rule, RuleContext, Severity

class CoverageRule(Rule):
    id = "R005"
    description = "La cobertura de código debe ser de al menos 90%"
    
    def _parse_coverage(self, coverage_path: Path) -> Optional[float]:
        try:
            tree = ET.parse(coverage_path)
            root = tree.getroot()
            # Buscar el atributo line-rate
            line_rate = float(root.attrib.get('line-rate', '0'))
            return line_rate
        except (ET.ParseError, ValueError, AttributeError):
            return None

    def check(self, ctx: RuleContext) -> List[Finding]:
        repo = Path(ctx.repo_root)
        coverage_path = repo / "coverage.xml"
        
        if not coverage_path.exists():
            return [
                Finding(
                    rule_id=self.id,
                    message="No se encontró archivo coverage.xml",
                    severity=Severity.MEDIUM,
                    path=str(repo)
                )
            ]
            
        line_rate = self._parse_coverage(coverage_path)
        if line_rate is None:
            return [
                Finding(
                    rule_id=self.id,
                    message="No se pudo analizar el archivo coverage.xml",
                    severity=Severity.MEDIUM,
                    path=str(coverage_path)
                )
            ]
            
        if line_rate < 0.9:
            return [
                Finding(
                    rule_id=self.id,
                    message=f"Cobertura insuficiente: {line_rate:.1%} (mínimo requerido: 90%)",
                    severity=Severity.MEDIUM,
                    path=str(coverage_path),
                    meta={"coverage": line_rate, "required": 0.9}
                )
            ]
            
        return []