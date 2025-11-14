from __future__ import annotations
from pathlib import Path
import pytest
import textwrap

@pytest.fixture
def good_repo(tmp_path: Path) -> Path:
    root = tmp_path / "good"
    root.mkdir()
    (root / ".gitignore").write_text(".env\n*.pyc\n", encoding="utf-8")
    (root / "LICENSE").write_text("MIT", encoding="utf-8")
    (root / "Makefile").write_text(textwrap.dedent("""\
    run:
        @echo run
    lint:
        @echo lint
    test:
        @echo test
    plan:
        @echo plan
    apply:
        @echo apply
    """), encoding="utf-8")
    (root / "src").mkdir()
    (root / "src" / "app.py").write_text("import os\nprint(os.environ.get('X'))\n", encoding="utf-8")
    return root

@pytest.fixture
def bad_repo(tmp_path: Path) -> Path:
    root = tmp_path / "bad"
    root.mkdir()
    (root / ".gitignore").write_text("*.pyc\n", encoding="utf-8")  
    (root / "Makefile").write_text(textwrap.dedent("""\
    lint:
        @echo lint
    test:
        @echo test
    """), encoding="utf-8")
    (root / "config.json").write_text("{}", encoding="utf-8")       # heurística de config estática
    (root / "src").mkdir()
    (root / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")
    return root
