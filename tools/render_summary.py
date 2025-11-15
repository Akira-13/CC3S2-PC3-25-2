from __future__ import annotations
import json
from pathlib import Path
import argparse

def load_metrics(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data

def render_markdown(metrics: dict) -> str:
    # Supuesto de estructura:
    # {
    #     "summary": {"total": ..., "by_severity": {"High":..., "Medium":..., "Low":...}},
    #     "top_rules": [...],
    #     "delta": {"High": +1, "Medium": -2, ...}  # cambios vs sprint anterior
    # }
    summary = metrics.get("summary", {})
    by_sev = summary.get("by_severity", {})

    lines: list[str] = []
    lines.append("# Compliance summary\n")
    lines.append(f"- Total findings: **{summary.get('total', 0)}**")
    lines.append(
        f"- High: **{by_sev.get('High', 0)}**, "
        f"Medium: **{by_sev.get('Medium', 0)}**, "
        f"Low: **{by_sev.get('Low', 0)}**"
    )
    lines.append("")

    # Tabla por severidad
    lines.append("## Findings por severidad\n")
    lines.append("| Severidad | Count |")
    lines.append("|----------|-------|")
    for sev in ("High", "Medium", "Low"):
        lines.append(f"| {sev} | {by_sev.get(sev, 0)} |")
    lines.append("")

    # Cambios vs sprint anterior
    delta = metrics.get("delta", {})
    if delta:
        lines.append("## ¿Qué cambió desde el sprint anterior?\n")
        for sev in ("High", "Medium", "Low"):
            d = delta.get(sev, 0)
            if d > 0:
                desc = f"aumentó en {d}"
            elif d < 0:
                desc = f"disminuyó en {-d}"
            else:
                desc = "se mantuvo igual"
            lines.append(f"- {sev}: {desc}")
        lines.append("")

    # Recomendaciones
    recs = metrics.get("recommendations", [])
    if recs:
        lines.append("## Recomendaciones\n")
        for r in recs:
            lines.append(f"- {r}")
        lines.append("")

    return "\n".join(lines)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Renderiza un resumen legible desde metrics/current.json a reports/summary.md"
    )
    parser.add_argument(
        "--input",
        default="metrics/current.json",
        help="Ruta al archivo de métricas (JSON)",
    )
    parser.add_argument(
        "--output",
        default="reports/summary.md",
        help="Ruta de salida para el resumen en Markdown",
    )
    args = parser.parse_args(argv)

    in_path = Path(args.input)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    metrics = load_metrics(in_path)
    md = render_markdown(metrics)
    out_path.write_text(md, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
