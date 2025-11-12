from __future__ import annotations
from auditor.core import RuleContext
from auditor.rules.config_rule import ConfigViaEnvRule
import pytest

@pytest.mark.parametrize("uses_env, has_static, expected", [
    (True, False, 0),
    (True, True, 0),
    (False, True, 1),
])
def test_config_env_heuristic_bounds(tmp_path, uses_env, has_static, expected):
    r = tmp_path
    (r / "src").mkdir()
    (r / "src" / "app.py").write_text(
        "import os\nprint(os.environ['X'])\n" if uses_env else "print('x')\n",
        encoding="utf-8"
    )
    if has_static:
        (r / "config.json").write_text("{}", encoding="utf-8")
    findings = ConfigViaEnvRule().check(RuleContext(str(r)))
    assert len(findings) == expected
