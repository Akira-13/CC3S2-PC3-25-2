from __future__ import annotations

import argparse
import csv
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv no instalado


GITHUB_API = "https://api.github.com"


# ==========================
# Helpers básicos
# ==========================

def _get_token() -> str:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN no está definido en el entorno.")
    return token


def _headers() -> Dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {_get_token()}",
    }


def _parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


# ==========================
# Modelos
# ==========================

@dataclass
class PRInfo:
    number: int
    created_at: datetime
    merged_at: Optional[datetime]
    head_sha: str


@dataclass
class ReviewInfo:
    state: str
    submitted_at: datetime


@dataclass
class RunInfo:
    id: int
    name: str
    conclusion: Optional[str]
    created_at: datetime
    updated_at: datetime
    head_sha: str


@dataclass
class Metrics:
    pr_number: int
    severity_counts: Dict[str, int]
    cycle_time_hours: Optional[float]
    approval_time_hours: Optional[float]
    remediation_time_hours: Optional[float]
    blocked_time_hours: Optional[float]
    trend: Dict[str, str]
    
    def to_publish_format(self) -> Dict[str, Any]:
        """Convert to format expected by publish_to_project"""
        return {
            "summary": {
                "total": self.severity_counts.get("High", 0) + self.severity_counts.get("Medium", 0) + self.severity_counts.get("Low", 0),
                "by_severity": self.severity_counts
            },
            "findings": [],  # Empty since we only have counts
            "time_metrics": {
                "cycle_time_hours": self.cycle_time_hours,
                "approval_time_hours": self.approval_time_hours,
                "remediation_time_hours": self.remediation_time_hours,
                "blocked_time_hours": self.blocked_time_hours
            }
        }


# ==========================
# GitHub API
# ==========================

def get_pr(repo: str, pr_number: int) -> PRInfo:
    url = f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}"
    resp = requests.get(url, headers=_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return PRInfo(
        number=data["number"],
        created_at=_parse_iso(data["created_at"]),
        merged_at=_parse_iso(data["merged_at"]) if data.get("merged_at") else None,
        head_sha=data["head"]["sha"],
    )


def get_pr_reviews(repo: str, pr_number: int) -> List[ReviewInfo]:
    url = f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}/reviews"
    resp = requests.get(url, headers=_headers(), timeout=30)
    resp.raise_for_status()
    reviews: List[ReviewInfo] = []
    for item in resp.json():
        if not item.get("submitted_at"):
            continue
        reviews.append(
            ReviewInfo(
                state=item["state"],
                submitted_at=_parse_iso(item["submitted_at"]),
            )
        )
    return reviews


def get_workflow_runs_for_pr(
    repo: str,
    workflow_id_or_file: str,
    head_sha: str,
    per_page: int = 50,
) -> List[RunInfo]:

    url = f"{GITHUB_API}/repos/{repo}/actions/workflows/{workflow_id_or_file}/runs"
    params = {"per_page": per_page}

    resp = requests.get(url, headers=_headers(), params=params, timeout=30)
    resp.raise_for_status()

    runs: List[RunInfo] = []
    for run in resp.json().get("workflow_runs", []):
        if run.get("head_sha") != head_sha:
            continue
        runs.append(
            RunInfo(
                id=run["id"],
                name=run["name"],
                conclusion=run.get("conclusion"),
                created_at=_parse_iso(run["created_at"]),
                updated_at=_parse_iso(run["updated_at"]),
                head_sha=run["head_sha"],
            )
        )
    runs.sort(key=lambda r: r.created_at)
    return runs


# ==========================
# Métricas del proceso
# ==========================

def compute_cycle_time(pr: PRInfo) -> Optional[float]:
    if pr.merged_at is None:
        return None
    delta = pr.merged_at - pr.created_at
    return delta.total_seconds() / 3600.0


def compute_approval_time(reviews: List[ReviewInfo], pr_created_at: datetime) -> Optional[float]:
    approvals = [r for r in reviews if r.state.upper() == "APPROVED"]
    if not approvals:
        return None
    last_approval = max(approvals, key=lambda r: r.submitted_at)
    delta = last_approval.submitted_at - pr_created_at
    return delta.total_seconds() / 3600.0


def compute_remediation_and_blocked_time(runs: List[RunInfo]):
    if not runs:
        return None, None

    failures = [r for r in runs if r.conclusion == "failure"]
    successes = [r for r in runs if r.conclusion == "success"]

    if not failures or not successes:
        return None, None

    first_failure = min(failures, key=lambda r: r.created_at)
    last_failure = max(failures, key=lambda r: r.created_at)
    first_success = min(successes, key=lambda r: r.created_at)

    remediation = (first_success.created_at - first_failure.created_at).total_seconds() / 3600.0
    blocked = (first_success.created_at - last_failure.created_at).total_seconds() / 3600.0

    return remediation, blocked


# ==========================
# Report del auditor
# ==========================

def load_report(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compute_severity_counts(report: Dict[str, Any]) -> Dict[str, int]:
    findings = report.get("findings", [])
    counts = {"High": 0, "Medium": 0, "Low": 0}
    for f in findings:
        sev = f.get("severity")
        if sev in counts:
            counts[sev] += 1
    return counts


def compute_trend(current_counts: Dict[str, int]) -> Dict[str, str]:
    # Sin previous_metrics → tendencia no disponible
    return {sev: "n/a" for sev in current_counts}


# ==========================
# Orquestador
# ==========================

def compute_metrics_for_pr(
    repo: str,
    pr_number: int,
    workflow_id_or_file: str,
    report: Dict[str, Any],
) -> Metrics:

    pr = get_pr(repo, pr_number)
    reviews = get_pr_reviews(repo, pr_number)
    runs = get_workflow_runs_for_pr(repo, workflow_id_or_file, pr.head_sha)

    sev_counts = compute_severity_counts(report)
    cycle = compute_cycle_time(pr)
    approval = compute_approval_time(reviews, pr.created_at)
    remediation, blocked = compute_remediation_and_blocked_time(runs)
    trend = compute_trend(sev_counts)

    return Metrics(
        pr_number=pr.number,
        severity_counts=sev_counts,
        cycle_time_hours=cycle,
        approval_time_hours=approval,
        remediation_time_hours=remediation,
        blocked_time_hours=blocked,
        trend=trend,
    )


# ==========================
# Persistencia JSON / CSV
# ==========================

def save_metrics_json(metrics: Metrics, path: Path) -> None:
    """Save in format expected by publish_to_project"""
    data = metrics.to_publish_format()
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def save_trends_json(metrics: Metrics, path: Path) -> None:
    """Save trends in format expected by publish_to_project"""
    # Use overall trend (total) as the main trend indicator
    overall_trend = metrics.trend.get("total", "n/a")
    path.write_text(json.dumps({"trend": overall_trend}, indent=2), encoding="utf-8")


def save_metrics_csv(metrics: Metrics, path: Path) -> None:
    header = [
        "pr_number", "high", "medium", "low",
        "cycle_time_hours", "approval_time_hours",
        "remediation_time_hours", "blocked_time_hours",
        "trend_high", "trend_medium", "trend_low",
    ]

    sev = metrics.severity_counts
    trend = metrics.trend

    row = [
        metrics.pr_number,
        sev["High"], sev["Medium"], sev["Low"],
        metrics.cycle_time_hours,
        metrics.approval_time_hours,
        metrics.remediation_time_hours,
        metrics.blocked_time_hours,
        trend["High"], trend["Medium"], trend["Low"],
    ]

    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(header)
        writer.writerow(row)


# ==========================
# CLI
# ==========================

def _parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="metrics",
        description="Calcula métricas del auditor (Sprint 3).",
    )
    p.add_argument("--repo", help="Formato: owner/repo (usa GITHUB_OWNER/PROJECT_ITEM_KEY del env si no se especifica)")
    p.add_argument("--pr-number", type=int, required=True)
    p.add_argument("--workflow", default="compliance.yml")
    p.add_argument("--report", default="report.json")
    p.add_argument("--out-metrics", default="auditor/metrics/metrics.json")
    p.add_argument("--out-csv", default="auditor/metrics/metrics.csv")
    p.add_argument("--out-trends", default="auditor/metrics/trends.json")
    p.add_argument("--metrics-dir", default=".metrics", help="Directorio para almacenar métricas históricas")
    p.add_argument("--demo", action="store_true", help="Modo demo: genera métricas sin llamar a GitHub API")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)

    report_path = Path(args.report)
    if not report_path.exists():
        print(f"[metrics] Error: no existe {report_path}")
        return 1

    report = load_report(report_path)

    # Use environment variables for repo if not provided
    if not args.repo:
        github_owner = os.getenv("GITHUB_OWNER")
        project_key = os.getenv("PROJECT_ITEM_KEY")
        print(f"[metrics] Debug: GITHUB_OWNER={github_owner}, PROJECT_ITEM_KEY={project_key}")
        if not github_owner or not project_key:
            print("[metrics] Error: --repo es requerido o GITHUB_OWNER/PROJECT_ITEM_KEY deben estar definidos")
            return 1
        args.repo = f"{github_owner}/{project_key}"
        print(f"[metrics] Usando repo: {args.repo}")

    try:
        if args.demo:
            # Demo mode: generate mock metrics without GitHub API
            sev_counts = compute_severity_counts(report)
            trend = compute_trend(sev_counts)
            
            metrics = Metrics(
                pr_number=args.pr_number,
                severity_counts=sev_counts,
                cycle_time_hours=24.5,
                approval_time_hours=2.1,
                remediation_time_hours=1.8,
                blocked_time_hours=0.5,
                trend=trend,
            )
        else:
            metrics = compute_metrics_for_pr(
                repo=args.repo,
                pr_number=args.pr_number,
                workflow_id_or_file=args.workflow,
                report=report,
            )
    except Exception as exc:
        print(f"[metrics] Error calculando métricas: {exc}")
        return 2

    # Create metrics directory if it doesn't exist
    metrics_dir = Path("auditor/metrics")
    metrics_dir.mkdir(exist_ok=True)
    
    save_metrics_json(metrics, Path(args.out_metrics))
    save_metrics_csv(metrics, Path(args.out_csv))
    save_trends_json(metrics, Path(args.out_trends))

    print(f"[metrics] Métricas generadas correctamente. {'(Modo demo)' if args.demo else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())