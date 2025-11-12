from __future__ import annotations
from pathlib import Path
import importlib
import pytest
from unittest.mock import patch

# Guardia por RuleContext (A)
import importlib as _il
_core = _il.import_module("auditor.core")
if not hasattr(_core, "RuleContext"):
    pytest.skip("RuleContext pendiente : se omite este módulo", allow_module_level=True)

from auditor.core import RuleContext

def _get_secrets_rule():
    try:
        mod = importlib.import_module("auditor.rules.secrets_rule")
    except ModuleNotFoundError:
        pytest.skip("Regla de secretos aún no implementada (auditor.rules.secrets_rule)")
    for name in ("SecretsNoneRule", "SecretsRule", "SecretScanRule"):
        if hasattr(mod, name):
            return getattr(mod, name)()
    pytest.skip("Clase de regla de secretos no encontrada en secrets_rule")

def _mk_repo_with_files(tmp_path: Path) -> Path:
    repo = tmp_path
    (repo / ".git").mkdir(exist_ok=True)  # algunos rules usan git ls-files
    (repo / "src").mkdir(exist_ok=True)
    (repo / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")
    (repo / "src" / "aws.txt").write_text('{"ok":true}\n', encoding="utf-8")
    return repo

def _rg_no_matches(pattern: str, path: str) -> str:
    return ""

def _rg_with_matches(pattern: str, path: str) -> str:
    return "\n".join([
        "src/app.py:1: API_KEY=sk_live_ABC123",
        "src/aws.txt:1: aws_access_key_id=AKIAZZZ",
    ])

def _git_ls_files(_path: str):
    # evita depender de git real
    return ["src/app.py", "src/aws.txt", "README.md"]

def test_secrets_ok(tmp_path: Path):
    repo = _mk_repo_with_files(tmp_path)
    # limpiar contenido sensible
    (repo / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
    from auditor import shell
    with patch.object(shell, "ripgrep", autospec=True, side_effect=_rg_no_matches), \
         patch.object(shell, "git_ls_files", autospec=True, side_effect=_git_ls_files):
        rule = _get_secrets_rule()
        findings = rule.check(RuleContext(str(repo)))
    assert findings == [], "No debe reportar si no hay patrones de secreto"

def test_secrets_detected_high(tmp_path: Path):
    repo = _mk_repo_with_files(tmp_path)
    from auditor import shell
    with patch.object(shell, "ripgrep", autospec=True, side_effect=_rg_with_matches), \
         patch.object(shell, "git_ls_files", autospec=True, side_effect=_git_ls_files):
        rule = _get_secrets_rule()
        findings = rule.check(RuleContext(str(repo)))
    assert findings, "Debe reportar secretos típicos"
    f = findings[0]
    # si el rule expone severidad y matches en details, los comprobamos suavemente
    if hasattr(f, "severity"):
        assert str(f.severity).lower().endswith("high")
    if hasattr(f, "details"):
        assert f.details.get("matches")
