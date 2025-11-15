# Reporte de Auditoría de Repositorio

## Resumen
- Hallazgos totales: 8
- Alta severidad: 6
- Media severidad: 2
- Baja severidad: 0

## High Severidad

| Regla | Archivo | Línea | Mensaje |
|-------|---------|-------|---------|
| R006 | `.git\hooks\fsmonitor-watchman.sample` | 91 | Posible secreto expuesto: (?i)TOKEN\s*= |
| R006 | `.git\hooks\fsmonitor-watchman.sample` | 151 | Posible secreto expuesto: (?i)TOKEN\s*= |
| license.present | `C:\Users\Camila\Desktop\uni\7mo\DS\PC3\CC3S2-PC3-25-2` | N/A | No se encontró archivo de licencia válido |
| R006 | `tests\test_rule_secrets_none.py` | 23 | Posible secreto expuesto: (?i)API_?KEY\s*= |
| R006 | `tests\test_rule_secrets_none.py` | 41 | Posible secreto expuesto: (?i)TOKEN\s*= |
| R006 | `tests\test_secrest_multifile.py` | 20 | Posible secreto expuesto: (?i)TOKEN\s*= |

## Medium Severidad

| Regla | Archivo | Línea | Mensaje |
|-------|---------|-------|---------|
| R005 | `C:\Users\Camila\Desktop\uni\7mo\DS\PC3\CC3S2-PC3-25-2` | N/A | No se encontró archivo coverage.xml |
| R003 | `C:\Users\Camila\Desktop\uni\7mo\DS\PC3\CC3S2-PC3-25-2\Makefile` | N/A | Faltan targets obligatorios en Makefile: apply, plan |
