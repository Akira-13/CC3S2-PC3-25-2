# Auditor de Repositorio

Estructura mínima del auditor con las primeras reglas y un flujo de trabajo impulsado por Makefile.

## Reglas implementadas

* **R001**: `.env` debe estar listado en `.gitignore`.
* **R002**: **Configuración vía variables de entorno** (heurística).
* **R003**: El **Makefile** debe incluir objetivos requeridos (`run`, `test`, `lint`, `plan`, `apply`).
* **R004**: El repositorio debe tener un archivo de licencia válido (LICENSE, LICENSE.txt, COPYING, etc.).
* **R005**: La cobertura de código debe ser de al menos 90% (verifica archivo coverage.xml).
* **R006**: No deben existir secretos expuestos en el código (API keys, tokens, contraseñas, etc.).

## Estructura del proyecto (parcial)

```
auditor/
  core.py            # Finding, Severity, RuleContext, run_rules
  utils/fs.py        # Helpers del sistema de archivos
  rules/
    gitignore_rule.py  # R001
    config_rule.py     # R002
    makefile_rule.py   # R003
    license_rule.py    # R004
    coverage_rule.py   # R005
    secrets_rule.py    # R006
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

---

## Pruebas y fixtures (Sprint 1)

Trabajo realizado en este sprint para asegurar calidad y verificabilidad del auditor:

* **Fixtures realistas**:

  * `good_repo`: crea estructura mínima válida con `.gitignore`, `LICENSE`, `Makefile`, `src/…`.
  * `bad_repo`: crea estructura intencionalmente incompleta para provocar findings.
* **Parametrización exhaustiva**:

  * Bordes de cobertura en `test_rule_coverage_min.py` (p. ej., `0.899`, `0.90`, `0.92`).
  * Variantes de licencia en `test_rule_license_present.py` (formatos aceptados y vacíos).
* **Smokes de la CLI**:

  * Ejecutan `auditor.cli` contra repos “bueno/malo”.
  * En el “repo bueno” se genera un `coverage.xml` sintético con `line-rate ≥ 0.90` para no disparar falsos positivos de cobertura.
* **Mocks disciplinados**:

  * Uso de `patch.object(..., autospec=True)` y verificación de llamadas donde aplica.
* **Buenas prácticas de test**:

  * Uso sistemático de `tmp_path` para aislar filesystem.
  * Casos límite y errores controlados (p. ej., excepción al leer `LICENSE`).

### Estructura de tests (resumen)

```
tests/
  conftest.py                  # good_repo / bad_repo
  test_cli_smoke.py            # smokes de CLI con repos sintéticos
  test_config_rule.py
  test_core_runner_errors.py   # captura de excepciones en run_rules
  test_coverage_boundaries.py
  test_gitignore_env_fs_mock.py
  test_gitignore_env_param.py
  test_gitignore_rule.py
  test_license_io_error.py     # rama de error al leer licencia
  test_makefile_rule.py
  test_makefile_targets_param.py
  test_rule_coverage_min.py
  test_rule_license_present.py
  test_rule_secrets_none.py
  test_secrest_multifile.py    # detección de secretos en múltiples archivos
  test_utils.py
```

## Cómo ejecutar la suite y medir cobertura

```bash
pytest -vv --maxfail=1
pytest -vv --cov=auditor --cov-report=term-missing --cov-report=xml
```

**Gate de cobertura (S1 ≥ 85%):**

```bash
python tools/read_coverage.py 85
```

> Estado actual: **~93%** de cobertura (pasa el gate de S1 con holgura).

## Notas útiles para correr localmente

* Si la CLI o los smokes reportan un hallazgo inesperado en el “repo bueno”, verifica que el test haya generado `coverage.xml` con `line-rate ≥ 0.90`.
* Para ver líneas no cubiertas: usar `--cov-report=term-missing`.

## CI (S1) — verificación de calidad

* **Lint** con `ruff`.
* **Tests + coverage** con `pytest` y **gate** de cobertura usando `tools/read_coverage.py 85`.
* Escaneo de secretos (acción separada en el pipeline).

---

## Herramientas adicionales

### Publicador de GitHub Projects

El directorio `tools/` incluye `publish-to-project.py`, una herramienta para publicar automáticamente los resultados del auditor en GitHub Projects V2.

**Características:**
- Publica resúmenes de hallazgos en tarjetas de proyecto
- Idempotente: actualiza tarjetas existentes en lugar de crear duplicados
- Soporta seguimiento de tendencias entre sprints
- Integración vía API GraphQL de GitHub

**Uso rápido:**
```bash
export GITHUB_TOKEN="tu_token"
python tools/publish-to-project.py \
  --report report.json \
  --owner Akira-13 \
  --project-number 1 \
  --item-key "repo:CC3S2-PC3-25-2"
```

Ver `tools/README.md` para documentación completa.
