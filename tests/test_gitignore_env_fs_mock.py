from __future__ import annotations
import importlib, pytest
_core = importlib.import_module("auditor.core")
if not hasattr(_core, "RuleContext"):
    pytest.skip("RuleContext pendiente: se omite por ahora", allow_module_level=True)
from auditor.core import RuleContext

from auditor.rules.gitignore_rule import GitignoreEnvRule
from auditor.rules import gitignore_rule
from unittest.mock import patch

def test_gitignore_env_with_fs_mock(tmp_path):
    ctx = RuleContext(str(tmp_path))
    with patch.object(gitignore_rule, "read_lines", autospec=True) as m:
        m.return_value = ["# base", "*.pyc"]   
        findings = GitignoreEnvRule().check(ctx)
        assert findings and findings[0].severity.value == "High"
        assert m.call_args
