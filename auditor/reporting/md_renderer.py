import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import sys


@dataclass
class Finding:
    """Clase que representa un hallazgo del auditor."""
    rule_id: str
    file: str
    message: str
    severity: str = "low"
    line: Optional[int] = None
    context: Optional[str] = None


def load_json_report(input_path: str) -> Dict[str, Any]:
    """Carga el reporte JSON del auditor.
    
    Args:
        input_path: Ruta al archivo JSON de entrada.
        
    Returns:
        Dict con los datos del reporte.
        
    Raises:
        FileNotFoundError: Si el archivo no existe.
        json.JSONDecodeError: Si el archivo no es un JSON válido.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_findings(report_data: Dict) -> List[Finding]:
    """Convierte los datos del reporte en una lista de objetos Finding.
    
    Args:
        report_data: Datos del reporte del auditor.
        
    Returns:
        Lista de objetos Finding.
    """
    findings = []
    for finding_data in report_data.get('findings', []):
        try:
            # Obtener metadatos adicionales
            meta = finding_data.get('meta', {})
            finding = Finding(
                rule_id=finding_data.get('rule_id', 'unknown'),
                file=finding_data.get('path', ''),  # Usar 'path' en lugar de 'file'
                message=finding_data.get('message', ''),
                severity=finding_data.get('severity', 'low').lower(),
                line=meta.get('line'),  # Obtener la línea de los metadatos
                context=meta.get('context')
            )
            findings.append(finding)
        except (TypeError, ValueError) as e:
            print(f"Warning: Error al procesar hallazgo: {e}", file=sys.stderr)
    return findings


def group_by_severity(findings: List[Finding]) -> Dict[str, List[Finding]]:
    """Agrupa los hallazgos por severidad.
    
    Args:
        findings: Lista de hallazgos a agrupar.
        
    Returns:
        Diccionario con los hallazgos agrupados por severidad.
    """
    severity_groups: Dict[str, List[Finding]] = {
        'high': [],
        'medium': [],
        'low': []
    }
    
    for finding in findings:
        severity = finding.severity.lower()
        if severity not in severity_groups:
            severity_groups[severity] = []
        severity_groups[severity].append(finding)
        
    return severity_groups


def generate_markdown(report_data: Dict) -> str:
    """Genera el reporte en formato Markdown.
    
    Args:
        report_data: Datos del reporte del auditor.
        
    Returns:
        String con el reporte en formato Markdown.
    """
    findings = parse_findings(report_data)
    severity_groups = group_by_severity(findings)
    
    # Contar hallazgos por severidad
    counts = {
        'high': len(severity_groups['high']),
        'medium': len(severity_groups['medium']),
        'low': len(severity_groups['low']),
        'total': len(findings)
    }
    
    # Generar el reporte
    lines = [
        '# Reporte de Auditoría de Repositorio',
        '',
        '## Resumen',
        f"- Hallazgos totales: {counts['total']}",
        f"- Alta severidad: {counts['high']}",
        f"- Media severidad: {counts['medium']}",
        f"- Baja severidad: {counts['low']}",
        ''
    ]
    
    if counts['total'] == 0:
        lines.extend([
            '## Resultado',
            'No se encontraron problemas en el análisis del repositorio.'
        ])
        return '\n'.join(lines)
    
    # Generar secciones por severidad
    for severity, findings_list in [('high', severity_groups['high']),
                                   ('medium', severity_groups['medium']),
                                   ('low', severity_groups['low'])]:
        if not findings_list:
            continue
            
        severity_title = severity.capitalize()
        lines.extend([
            f'## {severity_title} Severidad',
            '',
            '| Regla | Archivo | Línea | Mensaje |',
            '|-------|---------|-------|---------|'
        ])
        
        for finding in sorted(findings_list, key=lambda x: (x.file, x.line or 0)):
            line_num = str(finding.line) if finding.line is not None else 'N/A'
            
            file_path = finding.file if hasattr(finding, 'file') and finding.file else 'N/A'
            lines.append(
                f"| {finding.rule_id} | `{file_path}` | {line_num} | {finding.message} |"
            )
        
        lines.append('')
    
    return '\n'.join(lines)


def save_report(content: str, output_path: str) -> None:
    """Guarda el reporte en un archivo.
    
    Args:
        content: Contenido del reporte.
        output_path: Ruta donde guardar el archivo.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description='Renderiza un reporte JSON del auditor a formato Markdown.'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Ruta al archivo JSON de entrada'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='report.md',
        help='Ruta donde guardar el reporte Markdown (por defecto: report.md)'
    )
    
    args = parser.parse_args()
    
    try:
        # Cargar y validar el reporte JSON
        report_data = load_json_report(args.input)
        
        # Generar el reporte Markdown
        markdown_content = generate_markdown(report_data)
        
        # Guardar el reporte
        save_report(markdown_content, args.output)
        print(f"Reporte generado exitosamente en: {args.output}")
        return 0
        
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {args.input}", file=sys.stderr)
        return 1
    except json.JSONDecodeError:
        print(f"Error: El archivo {args.input} no es un JSON válido", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error inesperado: {str(e)}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())