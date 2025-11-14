from __future__ import annotations
from pathlib import Path
from typing import List, Pattern
import re

from auditor.core import Finding, Rule, RuleContext, Severity
from auditor.utils.fs import read_lines

class SecretsRule(Rule):
    id = "R006"
    description = "No deben existir secretos expuestos en el código"
    
    SECRET_PATTERNS = [
        r"(?i)SECRET_?KEY\s*=",
        r"(?i)API_?KEY\s*=",
        r"(?i)TOKEN\s*=",
        r"(?i)PASSWORD\s*=",
        r"(?i)SECRET\s*=",
    ]
    
    IGNORE_FILES = {
        ".gitignore",
        "*.md",
        "*.txt",
        "*.json",
        "*.xml",
        "*.yaml",
        "*.yml"
    }
    
    def _compile_patterns(self) -> list[Pattern]:
        return [re.compile(pattern) for pattern in self.SECRET_PATTERNS]
    
    def _is_ignored(self, path: Path) -> bool:
        return any(
            path.name == ignore or path.name.endswith(ignore.lstrip('*'))
            for ignore in self.IGNORE_FILES
        )
    
    def check(self, ctx: RuleContext) -> List[Finding]:
        repo = Path(ctx.repo_root)
        findings: List[Finding] = []
        patterns = self._compile_patterns()
        
        for file_path in repo.rglob("*"):
            if not file_path.is_file() or self._is_ignored(file_path):
                continue
                
            try:
                for line_num, line in enumerate(read_lines(file_path), 1):
                    for pattern in patterns:
                        if pattern.search(line):
                            findings.append(
                                Finding(
                                    rule_id=self.id,
                                    message=f"Posible secreto expuesto: {pattern.pattern}",
                                    severity=Severity.HIGH,
                                    path=str(file_path.relative_to(repo)),
                                    meta={
                                        "line": line_num,
                                        "snippet": line.strip(),
                                        "pattern": pattern.pattern
                                    }
                                )
                            )
                            break  # No reportar múltiples hallazgos por línea
            except (UnicodeDecodeError, PermissionError):
                continue
                
        return findings