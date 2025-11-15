# Auditor de Repositorio

* Videos: https://drive.google.com/drive/folders/18TawdGPUfcHBPnMcYzzRQUUV_AHDQN2W?usp=sharing

Estructura mínima del auditor con las primeras reglas y un flujo de trabajo impulsado por Makefile.

## Reglas implementadas

* **R001**: `.env` debe estar listado en `.gitignore`.
* **R002**: **Configuración vía variables de entorno** (heurística).
* **R003**: El **Makefile** debe incluir objetivos requeridos (`run`, `test`, `lint`, `plan`, `apply`).
* **R004**: El repositorio debe tener un archivo de licencia válido (LICENSE, LICENSE.txt, COPYING, etc.).
* **R005**: La cobertura de código debe ser de al menos 90% (verifica archivo coverage.xml).
* **R006**: No deben existir secretos expuestos en el código (API keys, tokens, contraseñas, etc.).

## Renderizador de Reportes

El módulo de reporting permite generar informes en formato Markdown a partir de los resultados del auditor.

1. **Generar el reporte JSON**:
   ```bash
   python -m auditor --repo . --output report.json
   ```

2. **Convertir a Markdown**:
   ```bash
   python -m auditor.reporting.md_renderer --input report.json --output report.md
   ```

## Estructura del proyecto

auditor/
  core.py            # Finding, Severity, RuleContext, run_rules
  reporting/         # Módulo de generación de reportes
    md_renderer.py   # Generador de reportes Markdown
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

````

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
````

### Objetivos

* `make test`
  Instala las dependencias de desarrollo (una vez) y ejecuta toda la suite.
* `make lint`
  Instala y ejecuta **ruff** sobre `auditor/` y `tests/` para aplicar estilo y calidad.
* `make run`
  Alias para ejecutar los tests rápidamente.
* `make audit`
  Ejecuta el auditor sobre el repositorio actual y genera `report.json`.
* `make publish-report`
  Publica el reporte de auditoría en GitHub Projects (requiere configuración de tokens).


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

> Estado actual: **~93–94%** de cobertura (pasa el gate de S1 con holgura).

## Notas útiles para correr localmente

* Si la CLI o los smokes reportan un hallazgo inesperado en el “repo bueno”, verifica que el test haya generado `coverage.xml` con `line-rate ≥ 0.90`.
* Para ver líneas no cubiertas: usar `--cov-report=term-missing`.

## CI (S1) — verificación de calidad

* **Lint** con `ruff`.
* **Tests + cobertura** con `pytest` y **gate** de cobertura usando `tools/read_coverage.py 85`.
* Escaneo de secretos (acción separada en el pipeline).

### Workflow de Compliance Audit

El archivo `.github/workflows/compliance.yml` ejecuta automáticamente el auditor en cada pull request:

**Características:**
- Se activa en cada PR para validar cumplimiento antes de mergear
- Ejecuta `python -m auditor` con flag `--fail-on high` (falla si hay hallazgos de severidad alta)
- Ignora directorios `tests` y `hooks` durante el análisis
- Sube el reporte `report.json` como artefacto para revisión posterior (disponible incluso si el workflow falla)

**Uso:**
```bash
# El workflow se ejecuta automáticamente en PRs
# Para ver el reporte: Actions → tu workflow → Artifacts → compliance-report
```

---

## Pruebas de integración y gates 

En el segundo sprint se extendió la suite de pruebas para validar no solo las reglas individuales, sino también el comportamiento de la CLI y su integración con el workflow de compliance.

### Smokes avanzados de CLI

Se agregaron pruebas que ejercitan la CLI en escenarios más cercanos al uso real:

* **CLI sobre repos sintéticos con cobertura:**

  * `test_cli_good_repo` genera un `coverage.xml` sintético con `line-rate=0.95` sobre `good_repo` y verifica que:

    * la ejecución de `auditor.cli.main` retorne código `0`,
    * el resumen (`summary.total`) reporte **0 findings**.
  * `test_cli_bad_repo` ejecuta la CLI sobre `bad_repo` y comprueba que:

    * se activen las reglas esperadas (`R001`, `R002`, `R003`, `license.present`, `R005`),
    * haya al menos varios findings de severidad **High**,
    * el exit code siga siendo `0` cuando el umbral es `--fail-on none`.

* **Flag `--fail-on`:**

  * `test_cli_fail_on_high` valida que, frente a un repositorio con hallazgos High, usar `--fail-on high` hace que la CLI retorne código `2`.
  * `test_cli_fail_on_levels` parametriza los niveles `none`, `low`, `medium`, `high` sobre un repo con problemas y comprueba que el código de salida cambia según el umbral configurado, cubriendo completamente la lógica de mapeo de severidades en la CLI.

* **Salida a archivo (`--output`):**

  * `test_cli_output_file_good_repo` asegura que, al usar `--output report.json` sobre `good_repo`, se genera un archivo JSON válido que contiene:

    * `repo_root` con la ruta evaluada,
    * `summary.total == 0`.

### Validación de `--ignore-dirs` y reglas de secretos

Se añadió una prueba específica para comprobar que la CLI respeta directorios ignorados al buscar secretos:

* **Ignorar directorios con posibles secretos:**

  * `test_cli_ignore_dirs_skips_secrets_in_tests` construye un repo sintético con:

    * código “limpio” en `src/app.py`,
    * una asignación sospechosa (`API_KEY = ...`) dentro de `tests/test_app.py`,
    * un `coverage.xml` válido para no disparar la regla de cobertura.
  * La prueba ejecuta la CLI con:

    ```bash
    --ignore-dirs tests
    ```

    captura la salida en JSON y verifica que:

    * el código de salida sea `0`,
    * no aparezcan findings con `rule_id == "R006"`, demostrando que `SecretsRule` respeta los directorios ignorados configurados en `RuleContext`.

### Contrato del workflow de compliance (tests tipo “mini E2E”)

Para reflejar fielmente el comportamiento del workflow definido en `.github/workflows/compliance.yml`, se añadieron pruebas que ejecutan exactamente el mismo comando que corre en CI, pero contra repos sintéticos:

* **Comando del workflow sobre repo sano:**

  * `test_workflow_command_good_repo`:

    * genera `coverage.xml` con `line-rate=0.95` en `good_repo`,
    * ejecuta:

      ```bash
      python -m auditor --repo <good_repo> \
                        --output report.json \
                        --ignore-dirs tests hooks \
                        --fail-on high
      ```
    * valida que el exit code sea `0` y que `summary.total == 0`.

* **Comando del workflow sobre repo con problemas:**

  * `test_workflow_command_bad_repo`:

    * ejecuta el mismo comando sobre `bad_repo`,
    * comprueba que:

      * el exit code sea `2` (hay hallazgos de severidad High),
      * el reporte JSON contenga findings,
      * el resumen agregue al menos un hallazgo de severidad **High**.

Estas pruebas actúan como una “simulación local” del pipeline de compliance: si pasan en local, el mismo comando que corre en GitHub Actions debería comportarse igual, bloqueando PRs con problemas y dejando pasar repositorios que cumplen todas las reglas.

### Cobertura y calidad

La ampliación de la suite de tests en este sprint mantiene la cobertura del módulo `auditor/` por encima del 90% y da mayor confianza en:

* el contrato de la CLI (parámetros, códigos de salida, estructura del JSON),
* la interacción entre reglas (incluida la de cobertura),
* el comportamiento de `--fail-on` como gate de severidad,
* el efecto de `--ignore-dirs` en reglas de análisis estático como `SecretsRule`.

La combinación de estos tests unitarios y de “mini E2E” facilita interpretar los resultados del workflow de compliance y explicar por qué un pull request es bloqueado o aceptado según las políticas definidas.


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