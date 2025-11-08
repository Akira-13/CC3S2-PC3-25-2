# Auditor de Repositorio

Estructura mínima del auditor con las primeras reglas y un flujo de trabajo impulsado por Makefile.

## Reglas implementadas

* **R001**: `.env` debe estar listado en `.gitignore`.
* **R002**: **Configuración vía variables de entorno** (heurística).
* **R003**: El **Makefile** debe incluir objetivos requeridos (`run`, `test`, `lint`, `plan`, `apply`).

## Estructura del proyecto (parcial)

```
auditor/
  core.py            # Finding, Severity, RuleContext, run_rules
  utils/fs.py        # Helpers del sistema de archivos
  rules/
    gitignore_rule.py  # R001
    config_rule.py     # R002
    makefile_rule.py   # R003
tests/
Makefile
pyproject.toml
```

## Make: puntos de entrada principales

El Makefile es la interfaz principal para los flujos de trabajo locales y los hooks de CI.

```makefile
.PHONY: test lint run

run:
	python -m pytest -q

lint:
	python -m pip install ruff >/dev/null 2>&1 || true
	ruff check auditor tests

test:
	python -m pip install -r requirements-dev.txt >/dev/null 2>&1 || true
	pytest -q
```

### Objetivos

* `make test`
  Instala las dependencias de desarrollo (una vez) y ejecuta toda la suite.
* `make lint`
  Instala y ejecuta **ruff** sobre `auditor/` y `tests/` para aplicar estilo y calidad.
* `make run`
  Alias para ejecutar los tests rápidamente.


## Inicio rápido

```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements
make test
make lint
```