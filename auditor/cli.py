from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Dict, Any

from auditor.core import RuleContext, run_rules, Finding, Severity
from auditor.rules.gitignore_rule import GitignoreEnvRule
from auditor.rules.config_rule import ConfigViaEnvRule
from auditor.rules.makefile_rule import MakefileRule


SEVERITY_ORDER = {Severity.LOW: 1, Severity.MEDIUM: 2, Severity.HIGH: 3}
NO_THRESHOLD = 999999  # Valor especial para no aplicar umbral

def _finding_to_dict(f: Finding) -> Dict[str, Any]:
    return {
        "rule_id": f.rule_id,
        "message": f.message,
        "severity": f.severity.value,
        "path": f.path,
        "meta": f.meta or {},
    }

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="auditor",
        description="Repo-Compliance Auditor (mínimo)",
    )
    p.add_argument(
        "--repo",
        default=".",
        help="Ruta a la raíz del repositorio a auditar (default: .)",
    )
    p.add_argument(
        "--output",
        default="-",
        help="Archivo de salida JSON (default: stdout)",
    )
    p.add_argument(
        "--fail-on",
        choices=["none", "low", "medium", "high"],
        default="none",
        help=(
            "Umbral de severidad para salir con código != 0 si hay findings. "
            "Ej: --fail-on high -> exit 2 si existe algún High"
        ),
    )
    return p.parse_args(argv)

def _threshold_to_level(name: str) -> int:
    if name == "high":
        return SEVERITY_ORDER[Severity.HIGH]
    if name == "medium":
        return SEVERITY_ORDER[Severity.MEDIUM]
    if name == "low":
        return SEVERITY_ORDER[Severity.LOW]
    return NO_THRESHOLD

def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    repo_root = str(Path(args.repo).resolve())

    ctx = RuleContext(repo_root)
    rules = [
        GitignoreEnvRule(),
        ConfigViaEnvRule(),
        MakefileRule(),
    ]

    findings = run_rules(ctx, rules)
    payload = {
        "repo_root": repo_root,
        "summary": {
            "total": len(findings),
            "by_severity": {
                "High": sum(1 for f in findings if f.severity is Severity.HIGH),
                "Medium": sum(1 for f in findings if f.severity is Severity.MEDIUM),
                "Low": sum(1 for f in findings if f.severity is Severity.LOW),
            },
        },
        "findings": [_finding_to_dict(f) for f in findings],
    }

    # salida
    data = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output == "-":
        print(data)
    else:
        Path(args.output).write_text(data, encoding="utf-8")

    # exit code en función de --fail-on
    threshold = _threshold_to_level(args.fail_on)
    worst = max((SEVERITY_ORDER[f.severity] for f in findings), default=0)

    if worst >= threshold and threshold != NO_THRESHOLD:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())