from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


SeverityCounts = Dict[str, int]
JSONDict = Dict[str, Any]


def _load_json(path: Path) -> JSONDict:
    if not path.exists():
        raise SystemExit(f"Archivo de entrada no encontrado: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("El archivo de entrada debe contener un objeto JSON (dict)")
    return data


def _extract_summary(data: JSONDict) -> tuple[int, SeverityCounts]:
    summary = data.get("summary", {}) or {}
    findings = data.get("findings") or []

    total = summary.get("total")
    if total is None:
        total = len(findings)

    by_sev = summary.get("by_severity") or {}
    # Normalizar claves
    return int(total), {
        "High": int(by_sev.get("High", 0)),
        "Medium": int(by_sev.get("Medium", 0)),
        "Low": int(by_sev.get("Low", 0)),
    }


def _render_table_by_severity(by_sev: SeverityCounts) -> List[str]:
    lines: List[str] = []
    lines.append("## Findings por severidad\n")
    lines.append("| Severidad | Count |")
    lines.append("|----------|-------|")
    for sev in ("High", "Medium", "Low"):
        lines.append(f"| {sev} | {by_sev.get(sev, 0)} |")
    lines.append("")
    return lines


def _render_from_metrics(metrics: JSONDict) -> str:
    total, by_sev = _extract_summary(metrics)
    time_metrics = metrics.get("time_metrics") or {}

    lines: List[str] = []
    lines.append("# Compliance summary (métricas)\n")
    lines.append(f"- Total findings (acumulado): **{total}**")
    lines.append(
        f"- High: **{by_sev['High']}**, "
        f"Medium: **{by_sev['Medium']}**, "
        f"Low: **{by_sev['Low']}**"
    )
    lines.append("")

    # Tabla por severidad
    lines.extend(_render_table_by_severity(by_sev))

    if time_metrics:
        lines.append("## Métricas de tiempo\n")
        ct = time_metrics.get("cycle_time_hours")
        at = time_metrics.get("approval_time_hours")
        rt = time_metrics.get("remediation_time_hours")
        bt = time_metrics.get("blocked_time_hours")

        if ct is not None:
            lines.append(f"- **Cycle time**: ~{ct:.2f} h")
        if at is not None:
            lines.append(f"- **Approval time**: ~{at:.2f} h")
        if rt is not None:
            lines.append(f"- **Remediation time**: ~{rt:.2f} h")
        if bt is not None:
            lines.append(f"- **Blocked time**: ~{bt:.2f} h")
        lines.append("")

    lines.append("## Notas\n")
    lines.append(
        "- Usa estos números para comparar entre sprints y detectar si los High "
        "están bajando y si el tiempo de remediación mejora."
    )
    lines.append("")
    return "\n".join(lines)


def _render_from_auditor_report(report: JSONDict) -> str:
    total, by_sev = _extract_summary(report)
    findings: List[JSONDict] = report.get("findings") or []

    lines: List[str] = []
    lines.append("# Compliance summary (reporte actual)\n")
    lines.append(f"- Total findings: **{total}**")
    lines.append(
        f"- High: **{by_sev['High']}**, "
        f"Medium: **{by_sev['Medium']}**, "
        f"Low: **{by_sev['Low']}**"
    )
    lines.append("")

    # Tabla por severidad
    lines.extend(_render_table_by_severity(by_sev))

    lines.append("## Top findings\n")
    if not findings:
        lines.append("_No hay findings en este reporte._")
        return "\n".join(lines)

    severity_order = {"High": 3, "Medium": 2, "Low": 1}
    sorted_findings = sorted(
        findings,
        key=lambda f: severity_order.get(str(f.get("severity")), 0),
        reverse=True,
    )

    top_n = min(10, len(sorted_findings))
    for f in sorted_findings[:top_n]:
        rule_id = f.get("rule_id", "unknown")
        sev = f.get("severity", "unknown")
        msg = str(f.get("message", "")).strip()
        path = f.get("path") or ""
        extra = f" (`{path}`)" if path else ""
        lines.append(f"- **[{sev}] {rule_id}**: {msg}{extra}")

    lines.append("")
    lines.append(
        "_Revisa primero los findings de severidad **High**, luego Medium. "
        "Los Low se pueden planificar como mejora continua._"
    )
    lines.append("")
    return "\n".join(lines)


def _is_metrics_payload(data: JSONDict) -> bool:
    # Heurística: si tiene time_metrics o proviene de auditor.metrics
    if "time_metrics" in data:
        return True
    # Campo opcional por si en el futuro se etiqueta
    if data.get("kind") == "metrics":
        return True
    return False


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Renderiza un resumen en Markdown a partir de un JSON de métricas "
            "o de un report.json del auditor."
        )
    )
    parser.add_argument(
        "--input",
        default="auditor/metrics/metrics.json",
        help="Ruta al archivo JSON de entrada (metrics.json o report.json)",
    )
    parser.add_argument(
        "--output",
        default="summary.md",
        help="Ruta de salida para el resumen en Markdown",
    )
    args = parser.parse_args(argv)

    in_path = Path(args.input)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    data = _load_json(in_path)

    if _is_metrics_payload(data):
        md = _render_from_metrics(data)
    else:
        md = _render_from_auditor_report(data)

    out_path.write_text(md, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
