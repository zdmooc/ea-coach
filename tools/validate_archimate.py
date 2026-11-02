#!/usr/bin/env python3
"""Vérifie qu'un modèle Open Exchange Format sera accepté par Archi :

1. conformité au schéma XSD officiel (archimate3_Diagram.xsd) — nécessite lxml ;
2. chaque relation est autorisée par la table ArchiMate 3.2 d'Archi (relationships.xml).

Les deux références viennent du dépôt open source d'Archi (licence MIT) et ne sont pas
recopiées ici : la CI les récupère (voir .github/workflows/ci.yml).

    python3 tools/validate_archimate.py MODEL.xml --archi /chemin/vers/archimatetool-archi
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ea_coach.model import load_model  # noqa: E402

LETTERS = {"Access": "a", "Composition": "c", "Flow": "f", "Aggregation": "g", "Assignment": "i", "Influence": "n",
           "Association": "o", "Realization": "r", "Specialization": "s", "Triggering": "t", "Serving": "v"}


def check_relationships(model_path: Path, table_path: Path) -> list[str]:
    table = {}
    for source in ET.parse(table_path).getroot():
        for target in source:
            table[(source.get("concept"), target.get("concept"))] = target.get("relations", "")
    model = load_model(model_path)
    errors = []
    for r in model.relationships:
        s, t = model.elements.get(r.source), model.elements.get(r.target)
        if not s or not t:
            errors.append(f"{r.id} : extrémité inconnue")
            continue
        if LETTERS.get(r.type, "?") not in table.get((s.type, t.type), ""):
            errors.append(f"{r.id} : {r.type} interdite de {s.type} « {s.name} » vers {t.type} « {t.name} »")
    return errors


def check_xsd(model_path: Path, xsd_dir: Path) -> list[str]:
    try:
        from lxml import etree
    except ImportError:
        return ["lxml absent : validation XSD impossible (pip install lxml)"]

    class Local(etree.Resolver):
        def resolve(self, url, pubid, context):
            name = url.rsplit("/", 1)[-1]
            local = xsd_dir / ("xml.xsd" if name.startswith("xml") and name.endswith(".xsd") else name)
            return self.resolve_filename(str(local), context) if local.exists() else None

    parser = etree.XMLParser()
    parser.resolvers.add(Local())
    schema = etree.XMLSchema(etree.parse(str(xsd_dir / "archimate3_Diagram.xsd"), parser))
    doc = etree.parse(str(model_path))
    return [] if schema.validate(doc) else [f"XSD ligne {e.line} : {e.message}" for e in schema.error_log]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--archi", required=True, help="clone (partiel) de github.com/archimatetool/archi")
    args = ap.parse_args()
    archi = Path(args.archi)
    model = Path(args.model)
    errors = check_xsd(model, archi / "org.opengroup.archimate.xmlexchange/xsd")
    errors += check_relationships(model, archi / "com.archimatetool.model/model/relationships.xml")
    for e in errors:
        print("✗", e)
    print(f"{model} : {'valide' if not errors else f'{len(errors)} erreur(s)'} (XSD Open Exchange + relations ArchiMate 3.2 d'Archi)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
