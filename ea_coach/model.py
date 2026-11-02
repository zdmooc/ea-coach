"""Lecture d'un modèle ArchiMate.

Deux formats sont acceptés :
- l'Open Exchange Format de The Open Group (fichier .xml exporté par Archi :
  Fichier › Exporter › Modèle au format Open Exchange) ;
- le format natif d'Archi (fichier .archimate), pour éviter l'étape d'export.

Le modèle est réduit à ce dont les règles ont besoin : éléments, relations, vues.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import xml.etree.ElementTree as ET

XSI = "{http://www.w3.org/2001/XMLSchema-instance}type"
OEF_NS = "http://www.opengroup.org/xsd/archimate/3.0/"
ARCHI_NS = "http://www.archimatetool.com/archimate"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


@dataclass
class Element:
    id: str
    type: str
    name: str
    documentation: str = ""


@dataclass
class Relationship:
    id: str
    type: str
    source: str
    target: str
    name: str = ""


@dataclass
class View:
    id: str
    name: str
    viewpoint: str = ""
    elements: set[str] = field(default_factory=set)
    relationships: set[str] = field(default_factory=set)


@dataclass
class Model:
    name: str
    elements: dict[str, Element]
    relationships: list[Relationship]
    views: list[View]
    source_format: str = ""

    def of_type(self, *types: str) -> list[Element]:
        wanted = set(types)
        return [e for e in self.elements.values() if e.type in wanted]

    def links(self, element_id: str, direction: str = "any", rel_types=None):
        """Relations touchant un élément : liste de (relation, autre élément)."""
        out = []
        for r in self.relationships:
            if rel_types and r.type not in rel_types:
                continue
            if direction in ("out", "any") and r.source == element_id and r.target in self.elements:
                out.append((r, self.elements[r.target]))
            if direction in ("in", "any") and r.target == element_id and r.source in self.elements:
                out.append((r, self.elements[r.source]))
        return out

    def in_any_view(self, element_id: str) -> bool:
        return any(element_id in v.elements for v in self.views)


def normalize_viewpoint(value: str) -> str:
    """« Implementation and Migration », « implementation_migration »… → forme comparable."""
    v = re.sub(r"[^a-z]", "", (value or "").lower())
    return v.replace("and", "")


def _text(node, tag: str) -> str:
    """Premier texte d'un enfant (préférence pour le français), dans l'espace de noms OEF."""
    found = node.findall(f"{{{OEF_NS}}}{tag}")
    if not found:
        return ""
    for f in found:
        if (f.get(XML_LANG) or "").startswith("fr"):
            return (f.text or "").strip()
    return (found[0].text or "").strip()


def _load_oef(root: ET.Element) -> Model:
    ns = f"{{{OEF_NS}}}"
    elements = {}
    for e in root.iter(f"{ns}element"):
        elements[e.get("identifier")] = Element(
            id=e.get("identifier"), type=e.get(XSI, ""), name=_text(e, "name"), documentation=_text(e, "documentation")
        )
    relationships = [
        Relationship(id=r.get("identifier"), type=r.get(XSI, ""), source=r.get("source"), target=r.get("target"), name=_text(r, "name"))
        for r in root.iter(f"{ns}relationship")
    ]
    views = []
    for v in root.iter(f"{ns}view"):
        view = View(id=v.get("identifier"), name=_text(v, "name"), viewpoint=v.get("viewpoint", ""))
        for n in v.iter(f"{ns}node"):
            if n.get("elementRef"):
                view.elements.add(n.get("elementRef"))
        for c in v.iter(f"{ns}connection"):
            if c.get("relationshipRef"):
                view.relationships.add(c.get("relationshipRef"))
        views.append(view)
    return Model(name=_text(root, "name"), elements=elements, relationships=relationships, views=views, source_format="oef")


def _load_archi(root: ET.Element) -> Model:
    elements, relationships, views = {}, [], []
    for node in root.iter("element"):
        kind = (node.get(XSI) or "").split(":")[-1]
        if not kind:
            continue
        if kind == "ArchimateDiagramModel":
            view = View(id=node.get("id"), name=node.get("name", ""), viewpoint=node.get("viewpoint", ""))
            for child in node.iter("child"):
                if child.get("archimateElement"):
                    view.elements.add(child.get("archimateElement"))
            for conn in node.iter("sourceConnection"):
                if conn.get("archimateRelationship"):
                    view.relationships.add(conn.get("archimateRelationship"))
            views.append(view)
        elif kind.endswith("Relationship"):
            relationships.append(Relationship(
                id=node.get("id"), type=kind[: -len("Relationship")], source=node.get("source"),
                target=node.get("target"), name=node.get("name", ""),
            ))
        elif kind in ("SketchModel", "CanvasModel"):
            continue
        else:
            doc = node.find("documentation")
            elements[node.get("id")] = Element(
                id=node.get("id"), type=kind, name=node.get("name", ""),
                documentation=(doc.text or "").strip() if doc is not None else "",
            )
    return Model(name=root.get("name", ""), elements=elements, relationships=relationships, views=views, source_format="archi")


def load_model(path: str | Path) -> Model:
    root = ET.parse(path).getroot()
    if root.tag == f"{{{OEF_NS}}}model":
        return _load_oef(root)
    if root.tag in (f"{{{ARCHI_NS}}}model", "model") and (root.tag.startswith(f"{{{ARCHI_NS}}}") or root.get("version")):
        return _load_archi(root)
    raise ValueError(
        f"{path} : format non reconnu. Attendu : Open Exchange Format (.xml) ou modèle Archi (.archimate)."
    )
