from __future__ import annotations
from pathlib import Path
import importlib
import pytest

from auditor.core import RuleContext

def _get_secrets_rule():
    try:
        mod = importlib.import_module("auditor.rules.secrets_rule")
    except ModuleNotFoundError:
        pytest.skip("Regla de secretos aún no implementada (auditor.rules.secrets_rule)")
    for name in ("SecretsRule", "SecretsNoneRule", "SecretScanRule"):
        if hasattr(mod, name):
            return getattr(mod, name)()
    pytest.skip("Clase de regla de secretos no encontrada en secrets_rule")


def _mk_repo_with_files(tmp_path: Path) -> Path:
    repo = tmp_path
    (repo / "src").mkdir(parents=True, exist_ok=True)
    # Contenido por defecto con un patrón que la heurística reconoce
    (repo / "src" / "app.py").write_text("api_key = 'sk_test_12345'\n", encoding="utf-8")
    return repo


def test_secrets_ok(tmp_path: Path):
    repo = _mk_repo_with_files(tmp_path)
    # limpiar contenido sensible
    (repo / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")

    rule = _get_secrets_rule()
    findings = rule.check(RuleContext(str(repo)))
    assert findings == []


def test_secrets_detected_high(tmp_path: Path):
    repo = _mk_repo_with_files(tmp_path)
    # asegurar contenido con patrón de secreto
    (repo / "src" / "app.py").write_text(
        "token = 'sk_live_ABCDEF0123456789'\n", encoding="utf-8"
    )

    rule = _get_secrets_rule()
    findings = rule.check(RuleContext(str(repo)))
    assert findings, "Debe detectar secreto"
    f = findings[0]
    # chequeo suave de severidad alta
    if hasattr(f, "severity"):
        assert str(f.severity).lower().endswith("high")
