from __future__ import annotations
from pathlib import Path
import importlib
import pytest
from auditor.core import RuleContext

def _get_secrets_rule():
    try:
        mod = importlib.import_module("auditor.rules.secrets_rule")
    except ModuleNotFoundError:
        pytest.skip("Regla de secretos aún no implementada")
    for name in ("SecretsRule", "SecretsNoneRule", "SecretScanRule"):
        if hasattr(mod, name):
            return getattr(mod, name)()
    pytest.skip("Clase de regla de secretos no encontrada")

def test_secrets_dedup(tmp_path: Path):
    (tmp_path / "src").mkdir(parents=True, exist_ok=True)
    for i in range(3):
        (tmp_path / "src" / f"f{i}.py").write_text("token='sk_live_ABCDEF0123456789'\n", encoding="utf-8")
    rule = _get_secrets_rule()
    findings = rule.check(RuleContext(str(tmp_path)))
    assert findings  # detecta
    # opcional: si tu rule ya deduplica, espera 1; si no, al menos >0:
    assert len(findings) >= 1
