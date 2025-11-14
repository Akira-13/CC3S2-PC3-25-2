from pathlib import Path
import sys, xml.etree.ElementTree as ET

def read_coverage_pct(xml_path: str | Path) -> float:
    root = ET.parse(xml_path).getroot()
    return float(root.attrib.get("line-rate", "0")) * 100.0

if __name__ == "__main__":
    min_pct = float(sys.argv[1]) if len(sys.argv) > 1 else 90.0
    pct = read_coverage_pct("coverage.xml")
    print(f"Coverage: {pct:.2f}% (min {min_pct:.2f}%)")
    sys.exit(1 if pct < min_pct else 0)
