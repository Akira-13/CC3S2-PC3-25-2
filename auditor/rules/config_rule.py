from __future__ import annotations
from pathlib import Path
from typing import List
import re

from auditor.core import Finding, Rule, RuleContext, Severity
from auditor.utils.fs import read_lines


class ConfigViaEnvRule(Rule):
    """
    R002: La configuración debe realizarse vía variables de entorno.
    Heurística D2:
      - Si NO se detecta uso de os.environ en código Python
      - Y hay archivos de configuración estáticos típicos (config.json, *.yaml, settings.*)
      => Finding Medium con recomendación de migrar a ENV.
    """

    id = "R002"
    description = "La configuración debe provenir de variables de entorno (no archivos estáticos)"

    def _python_files(self, root: Path) -> List[Path]:
        return [p for p in root.rglob("*.py") if "/.venv/" not in str(p)]

    def _has_env_usage(self, root: Path) -> bool:
        env_pat = re.compile(r"\bos\.environ\b|\benviron\[|\bos\.getenv\s*\(", re.IGNORECASE)
        for py in self._python_files(root):
            for line in read_lines(py):
                if env_pat.search(line):
                    return True
        return False

    def _has_static_configs(self, root: Path) -> List[str]:
        candidates = [
            "config.json", "config.yaml", "config.yml",
            "settings.json", "settings.yaml", "settings.yml",
            "appsettings.json", "application.yaml", "application.yml",
        ]
        found = []
        for rel in candidates:
            if (root / rel).exists():
                found.append(rel)
        return found

    def check(self, ctx: RuleContext) -> List[Finding]:
        root = Path(ctx.repo_root)
        uses_env = self._has_env_usage(root)
        static_files = self._has_static_configs(root)

        if not uses_env and static_files:
            return [
                Finding(
                    rule_id=self.id,
                    message=(
                        "No se detecta uso de os.environ y existen archivos de configuración estáticos: "
                        + ", ".join(static_files)
                    ),
                    severity=Severity.MEDIUM,
                    path=str(root),
                    meta={"static_configs": static_files, "recommendation": "Usar variables de entorno"},
                )
            ]

        return []