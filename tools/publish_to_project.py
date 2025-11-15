from __future__ import annotations

import argparse
import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Protocol, Tuple, List
from dotenv import load_dotenv

load_dotenv()

# modelos

@dataclass
class PublishConfig:
    owner: str           # org o user de github
    project_number: int  # numero del project
    item_key: str        # clave de tarjeta


@dataclass
class Summary:
    total: int
    high: int
    medium: int
    low: int
    # describe la tendencia de las vulnerabilidades respecto al sprint anterior
    trend: Optional[str] = None  # "up", "down", "flat", etc.


class ProjectsAPI(Protocol):
    """capa de acceso a GitHub Projects
    mockeable en tests
    """

    def find_item_by_key(self, cfg: PublishConfig) -> Optional[str]:
        """busca el item del proyecto por la clave lógica (cfg.item_key). devuelve item_id o none"""
        ...

    def create_item(self, cfg: PublishConfig) -> str:
        """crea un nuevo item (tarjeta) en el project y devuelve su id"""
        ...

    def update_fields(
        self,
        item_id: str,
        fields: Dict[str, Any],
        note: str,
    ) -> None:
        """actualiza campos custom y una nota/resumen en el item"""
        ...


# rate limiting / retry logic

def with_retry(func, *args, retries: int = 3, base_delay: float = 1.0, **kwargs):
    attempt = 0
    while True:
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            attempt += 1
            if attempt > retries:
                logging.error("Max retries exceeded calling %s: %s", func.__name__, exc)
                raise
            delay = base_delay * (2 ** (attempt - 1))
            logging.warning("Error calling %s (attempt %s/%s): %s. Retrying in %.1fs",
                            func.__name__, attempt, retries, exc, delay)
            time.sleep(delay)


# lógica principal de publicación

def load_report(path: Path) -> Tuple[Summary, List[Dict[str, Any]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    summary_data = data.get("summary", {})
    findings = data.get("findings", [])

    summary = Summary(
        total=summary_data.get("total", len(findings)),
        high=summary_data.get("by_severity", {}).get("High", 0),
        medium=summary_data.get("by_severity", {}).get("Medium", 0),
        low=summary_data.get("by_severity", {}).get("Low", 0),
    )
    return summary, findings


def load_trend(path: Optional[Path]) -> Optional[str]:
    """espera un JSON con {'trend': 'up'|'down'|'flat'}."""
    if path is None or not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("trend")


def build_note(summary: Summary) -> str:
    lines = [
        "# Repo-Compliance Report",
        "",
        f"- Total findings: {summary.total}",
        f"- High: {summary.high}",
        f"- Medium: {summary.medium}",
        f"- Low: {summary.low}",
    ]
    if summary.trend:
        lines.append(f"- Trend vs sprint anterior: **{summary.trend}**")
    return "\n".join(lines)


def build_fields(summary: Summary) -> Dict[str, Any]:
    """Mapea el Summary a campos custom del Project.

    Aquí usas las *keys* que tengas configuradas en el Project.
    Por ejemplo: 'high_count', 'medium_count', etc.
    """
    return {
        "high_count": summary.high,
        "medium_count": summary.medium,
        "low_count": summary.low,
        "total_findings": summary.total,
        "trend": summary.trend or "n/a",
    }


def publish_to_project(
    api: ProjectsAPI,
    cfg: PublishConfig,
    report_path: Path,
    trend_path: Optional[Path] = None,
) -> str:
    """función principal
    devuelve el item_id del Project actualizado.
    """
    logging.info("Loading report from %s", report_path)
    summary, _findings = load_report(report_path)

    # cargar trend si existe
    trend = load_trend(trend_path)
    if trend:
        summary.trend = trend

    note = build_note(summary)
    fields = build_fields(summary)

    logging.info(
        "Prepared summary for %s: total=%s high=%s medium=%s low=%s trend=%s",
        cfg.item_key, summary.total, summary.high, summary.medium, summary.low, summary.trend,
    )

    # idempotencia: si ya existe la tarjeta, la re-usamos
    item_id = with_retry(api.find_item_by_key, cfg)
    if item_id is None:
        logging.info("No existing item found for key=%s. Creating new item.", cfg.item_key)
        item_id = with_retry(api.create_item, cfg)
        # Verify the item exists before updating
        time.sleep(1)
        item_id = with_retry(api.find_item_by_key, cfg) or item_id
    else:
        logging.info("Found existing item %s for key=%s. Updating.", item_id, cfg.item_key)

    # actualizar campos y nota
    with_retry(api.update_fields, item_id, fields, note)
    logging.info("Successfully updated item %s for key=%s", item_id, cfg.item_key)

    return item_id

# api

class GitHubProjectsClient:
    """Cliente de API de GitHub Projects V2 usando GraphQL"""

    GRAPHQL_ENDPOINT = "https://api.github.com/graphql"

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _execute_graphql(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta una consulta GraphQL contra la API de GitHub"""
        import requests
        
        payload = {
            "query": query,
            "variables": variables,
        }
        
        response = requests.post(
            self.GRAPHQL_ENDPOINT,
            json=payload,
            headers=self.headers,
            timeout=30,
        )
        response.raise_for_status()
        
        data = response.json()
        if "errors" in data:
            raise Exception(f"GraphQL errors: {data['errors']}")
        
        return data.get("data", {})

    def _get_project_id(self, cfg: PublishConfig) -> str:
        """Obtiene el ID de nodo del proyecto"""
        query = """
        query($owner: String!, $number: Int!) {
          user(login: $owner) {
            projectV2(number: $number) {
              id
            }
          }
        }
        """
        
        variables = {
            "owner": cfg.owner,
            "number": cfg.project_number,
        }
        
        data = self._execute_graphql(query, variables)
        
        # Intentar primero usuario, luego organización
        project_id = None
        if data.get("user") and data["user"].get("projectV2"):
            project_id = data["user"]["projectV2"]["id"]
        
        if not project_id:
            raise Exception(f"Project {cfg.project_number} not found for owner {cfg.owner}")
        
        return project_id

    def find_item_by_key(self, cfg: PublishConfig) -> Optional[str]:
        """Busca un item existente verificando el título/contenido para item_key"""
        project_id = self._get_project_id(cfg)
        
        query = """
        query($projectId: ID!, $first: Int!) {
        node(id: $projectId) {
            ... on ProjectV2 {
            items(first: $first) {
                nodes {
                id
                content {
                    ... on DraftIssue {
                    id
                    title
                    body
                    }
                }
                }
            }
            }
        }
        }
        """
        
        variables = {
            "projectId": project_id,
            "first": 100,  # Ajustar si tienes más items
        }
        
        data = self._execute_graphql(query, variables)
        
        items = data.get("node", {}).get("items", {}).get("nodes", [])
        for item in items:
            content = item.get("content", {})
            title = content.get("title", "")
            body = content.get("body", "")
            
            # Verificar si item_key aparece en título o cuerpo
            if cfg.item_key in title or cfg.item_key in body:
                return content.get("id")
        
        return None

    def create_item(self, cfg: PublishConfig) -> str:
        """Crea un nuevo item de borrador en el proyecto"""
        project_id = self._get_project_id(cfg)
        
        mutation = """
        mutation($projectId: ID!, $title: String!, $body: String!) {
        addProjectV2DraftIssue(input: {
            projectId: $projectId
            title: $title
            body: $body
        }) {
            projectItem {
            id
            }
            draftIssue {
            id
            }
        }
        }
        """
        
        variables = {
            "projectId": project_id,
            "title": f"Compliance Report - {cfg.item_key}",
            "body": f"Key: {cfg.item_key}\n\nInitial report placeholder.",
        }
        
        data = self._execute_graphql(mutation, variables)
        item_id = data["addProjectV2DraftIssue"]["draftIssue"]["id"]
        
        logging.info("Created new project item: %s", item_id)
        return item_id

    def update_fields(
        self,
        item_id: str,
        fields: Dict[str, Any],
        note: str,
    ) -> None:
        """Actualiza el cuerpo/nota del item con el resumen
        
        Nota: Actualizar campos personalizados requiere sus IDs de campo que varían por proyecto.
        Para simplicidad, esta implementación actualiza el cuerpo del borrador.
        Para actualizar campos personalizados, necesitarías consultar los IDs de campo y usar updateProjectV2ItemFieldValue.
        """
        mutation = """
        mutation($itemId: ID!, $body: String!) {
          updateProjectV2DraftIssue(input: {
            draftIssueId: $itemId
            body: $body
          }) {
            draftIssue {
              id
            }
          }
        }
        """
        
        variables = {
            "itemId": item_id,
            "body": note,
        }
        
        self._execute_graphql(mutation, variables)
        logging.info("Updated project item %s with new summary", item_id)


# cli

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="publish-to-project",
        description="Publica el resultado del auditor en GitHub Projects (Sprint 3).",
    )
    p.add_argument(
        "--report",
        default="report.json",
        help="Ruta al JSON de salida del auditor (default: report.json)",
    )
    p.add_argument(
        "--trend",
        default=None,
        help="Ruta opcional a un JSON con información de trend.",
    )
    p.add_argument(
        "--owner",
        default=os.getenv("GITHUB_OWNER", ""),
        help="Owner (org/user) del proyecto. También puede venir de GITHUB_OWNER.",
    )
    p.add_argument(
        "--project-number",
        type=int,
        default=int(os.getenv("GITHUB_PROJECT_NUMBER", "1")),
        help="Número del GitHub Project v2.",
    )
    p.add_argument(
        "--item-key",
        default=os.getenv("PROJECT_ITEM_KEY", ""),
        help="Clave lógica del item (ej: repo:CC3S2-PC3-25-2).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(message)s",
    )

    args = _parse_args(argv)

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logging.error("GITHUB_TOKEN is required in the environment")
        return 1

    if not args.owner or not args.item_key:
        logging.error("owner and item-key are required (flags or env vars)")
        return 1

    cfg = PublishConfig(
        owner=args.owner,
        project_number=args.project_number,
        item_key=args.item_key,
    )

    report_path = Path(args.report)
    trend_path = Path(args.trend) if args.trend else None

    if not report_path.exists():
        logging.error("Report file %s does not exist", report_path)
        return 1

    api = GitHubProjectsClient(token=token)

    try:
        publish_to_project(api, cfg, report_path, trend_path)
    except Exception as exc:
        logging.error("Failed to publish to project: %s", exc)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
