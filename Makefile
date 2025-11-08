.PHONY: test lint run

run:
	python -m pytest -q

lint:
	python -m pip install ruff >/dev/null 2>&1 || true
	ruff check auditor tests

test:
	python -m pip install -r requirements-dev.txt >/dev/null 2>&1 || true
	pytest -q

audit:
	python -m auditor --repo . --output report.json --fail-on none
	@echo "Reporte JSON en report.json"