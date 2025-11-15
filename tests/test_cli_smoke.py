from __future__ import annotations
from pathlib import Path
import json
import importlib
import pytest

@pytest.fixture
def cli_module():
    return importlib.import_module("auditor.cli")

def _write_coverage(root: Path, pct: float) -> None:
    xml = f"<coverage line-rate='{pct:.2f}'><packages/></coverage>"
    (root / "coverage.xml").write_text(xml, encoding="utf-8")


def test_cli_good_repo(good_repo: Path, capsys, cli_module):
    """Repo válido debe retornar 0 findings y exit code 0"""
    _write_coverage(good_repo, 0.95)
    
    exit_code = cli_module.main(["--repo", str(good_repo)])
    out = capsys.readouterr().out
    data = json.loads(out)
    
    assert exit_code == 0
    assert data["summary"]["total"] == 0


def test_cli_bad_repo(bad_repo: Path, capsys, cli_module):
    """Repo inválido debe reportar 5 findings esperados"""
    exit_code = cli_module.main(["--repo", str(bad_repo)])
    out = capsys.readouterr().out
    data = json.loads(out)
    
    # Debe detectar: R001, R002, R003, license.present, R005
    rule_ids = {f["rule_id"] for f in data["findings"]}
    expected = {"R001", "R002", "R003", "license.present", "R005"}
    
    assert exit_code == 0  # --fail-on=none por defecto
    assert expected.issubset(rule_ids)
    assert data["summary"]["by_severity"]["High"] >= 2


def test_cli_output_file_good_repo(good_repo: Path, tmp_path: Path):
    cli = importlib.import_module("auditor.cli")
    out = tmp_path / "report.json"
    
    _write_coverage(good_repo, 0.95)
    exit_code = cli.main([
        "--repo", str(good_repo),
        "--output", str(out),  
    ])

    assert exit_code == 0
    assert out.exists()

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["summary"]["total"] == 0
    assert data["repo_root"]

@pytest.mark.parametrize("fail_on, expected_exit", [
    ("none", 0),
    ("low", 2),
    ("medium", 2),
    ("high", 2),
])
def test_cli_fail_on_levels(bad_repo: Path, fail_on: str, expected_exit: int):
    cli = importlib.import_module("auditor.cli")
    exit_code = cli.main([
        "--repo", str(bad_repo),
        "--fail-on", fail_on,
    ])
    assert exit_code == expected_exit

def test_workflow_command_good_repo(good_repo: Path, tmp_path: Path, monkeypatch):
    # Simulamos estar en el repo
    cli = importlib.import_module("auditor.cli")
    out = tmp_path / "report.json"

    _write_coverage(good_repo, 0.95)
    exit_code = cli.main([
        "--repo", str(good_repo),
        "--output", str(out),
        "--ignore-dirs", "tests", "hooks",
        "--fail-on", "high",
    ])

    assert exit_code == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["summary"]["total"] == 0

def test_workflow_command_bad_repo(bad_repo: Path, tmp_path: Path):
    cli = importlib.import_module("auditor.cli")
    out = tmp_path / "report.json"

    exit_code = cli.main([
        "--repo", str(bad_repo),
        "--output", str(out),
        "--ignore-dirs", "tests", "hooks",
        "--fail-on", "high",
    ])

    assert exit_code == 2  # porque hay High
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["summary"]["total"] > 0
    assert data["summary"]["by_severity"]["High"] >= 1


def test_cli_ignore_dirs_skips_secrets_in_tests(tmp_path: Path, capsys):
    repo = tmp_path / "repo"
    repo.mkdir()

    # src/app.py sin secretos
    src = repo / "src"
    src.mkdir()
    (src / "app.py").write_text("print('ok')\n", encoding="utf-8")

    # tests/test_app.py con un patrón que SecretsRule debería detectar
    tests_dir = repo / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_app.py").write_text(
        "API_KEY = 'NOT_A_SECRET'\n",
        encoding="utf-8",
    )

    # coverage.xml para no disparar R005
    (repo / "coverage.xml").write_text(
        "<coverage line-rate='0.95'><packages/></coverage>",
        encoding="utf-8",
    )

    cli = importlib.import_module("auditor.cli")
    exit_code = cli.main([
        "--repo", str(repo),
        "--output", "-",
        "--ignore-dirs", "tests",
    ])
    out = capsys.readouterr().out
    data = json.loads(out)

    assert exit_code == 0
    # Aseguramos que R006 NO aparece
    assert all(f["rule_id"] != "R006" for f in data["findings"])
