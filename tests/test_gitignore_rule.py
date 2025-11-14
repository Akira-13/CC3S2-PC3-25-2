from __future__ import annotations
from pathlib import Path
import tempfile

import pytest

from auditor.core import RuleContext

from auditor.rules import GitignoreEnvRule

@pytest.mark.parametrize(
    "gitignore_content, expected_findings",
    [
        ("", 1), # no .gitignore 
        ("# base\n*.pyc\n", 1), # sin .env
        ("# base\n.env\n*.pyc\n", 0), # con .env
    ],
)


def test_gitignore_rule_varios_casos(gitignore_content, expected_findings):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        gi = root / ".gitignore"


        if gitignore_content == "":
            # Caso: .gitignore inexistente => no crear el archivo
            pass
        else:
            gi.write_text(gitignore_content, encoding="utf-8")


        ctx = RuleContext(str(root))
        rule = GitignoreEnvRule()
        findings = rule.check(ctx)


        assert len(findings) == expected_findings
        if findings:
            # Si hay hallazgo, debe ser HIGH y del rule_id correcto
            f = findings[0]
            assert f.rule_id == rule.id
            assert f.severity.value == "High"