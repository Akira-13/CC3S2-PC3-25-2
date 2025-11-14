from __future__ import annotations

from auditor.core import RuleContext

from auditor.rules.gitignore_rule import GitignoreEnvRule
import pytest

@pytest.mark.parametrize("content,expected", [
    (".env\n", 0),
    ("", 1),
    ("# base\n*.pyc\n", 1),
])
def test_gitignore_env_param(tmp_path, content, expected):
    r = tmp_path
    (r / ".gitignore").write_text(content, encoding="utf-8")
    findings = GitignoreEnvRule().check(RuleContext(str(r)))
    assert len(findings) == expected
