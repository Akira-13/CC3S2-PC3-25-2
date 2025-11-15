from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from tools.publish_to_project import (
    publish_to_project,
    PublishConfig,
)


def test_publish_to_project_idempotent(tmp_path: Path):
    # Crear un report.json mínimo
    report = {
        "summary": {
            "total": 3,
            "by_severity": {"High": 1, "Medium": 1, "Low": 1},
        },
        "findings": [],
    }
    report_path = tmp_path / "report.json"
    report_path.write_text(__import__("json").dumps(report), encoding="utf-8")

    cfg = PublishConfig(owner="owner", project_number=1, item_key="repo:demo")

    # Cliente fake
    class FakeAPI:
        def __init__(self):
            self.find_calls = 0
            self.create_calls = 0
            self.update_calls = 0
            self._item_id = "ITEM-123"

        def find_item_by_key(self, cfg_):
            self.find_calls += 1
            # Primera vez no existe, segunda vez sí
            return None if self.find_calls == 1 else self._item_id

        def create_item(self, cfg_):
            self.create_calls += 1
            return self._item_id

        def update_fields(self, item_id, fields, note):
            self.update_calls += 1

    api = FakeAPI()

    # Primera publicación
    item_id_1 = publish_to_project(api, cfg, report_path, trend_path=None)
    # Segunda publicación (idempotente)
    item_id_2 = publish_to_project(api, cfg, report_path, trend_path=None)

    assert item_id_1 == "ITEM-123"
    assert item_id_2 == "ITEM-123"

    # Solo se crea UNA vez, pero se actualiza dos veces (dos ejecuciones)
    assert api.create_calls == 1
    assert api.update_calls == 2
