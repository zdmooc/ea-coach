"""Moteur de règles : applique un jeu de règles à un modèle et à un projet,
en respectant l'adaptation (tailoring) déclarée par le projet.

Le moteur ne connaît pas TOGAF : il exécute des types de règles génériques
(presence, trace, deliverable, view, plateaus, in_view) décrits dans un fichier TOML.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import glob
import tomllib

from .model import Model, normalize_viewpoint

SEVERITIES = ("error", "warning", "info")
BUILTIN_RULES = Path(__file__).parent / "rules"


@dataclass
class Finding:
    message: str
    element_id: str | None = None
    element_name: str | None = None
    element_type: str | None = None


@dataclass
class Result:
    rule: dict
    status: str  # pass | fail | na
    severity: str
    findings: list[Finding] = field(default_factory=list)
    reason: str = ""  # justification d'une non-applicabilité


@dataclass
class Report:
    project: str
    pack: dict
    phases: list[dict]
    results: list[Result]
    tailoring_errors: list[str]
    model_name: str = ""
    model_stats: dict = field(default_factory=dict)

    def count(self, status: str, severity: str | None = None) -> int:
        return sum(1 for r in self.results if r.status == status and (severity is None or r.severity == severity))

    @property
    def blocking(self) -> int:
        return self.count("fail", "error") + len(self.tailoring_errors)


# ---------- Chargement ----------

def load_rules(ref: str, base: Path | None = None) -> dict:
    """`ref` est un jeu intégré (ex. « togaf-adm ») ou un chemin vers un fichier TOML."""
    candidate = BUILTIN_RULES / f"{ref}.toml"
    path = candidate if candidate.exists() else Path(ref) if Path(ref).is_absolute() else (base or Path.cwd()) / ref
    if not path.exists():
        raise FileNotFoundError(f"Jeu de règles introuvable : {ref}")
    with open(path, "rb") as f:
        pack = tomllib.load(f)
    ids = [r["id"] for r in pack.get("rule", [])]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path} : identifiants de règles en double")
    phases = {p["id"] for p in pack.get("phase", [])}
    for r in pack.get("rule", []):
        if r.get("phase") not in phases:
            raise ValueError(f"{path} : règle {r['id']} rattachée à une phase inconnue « {r.get('phase')} »")
        if r.get("severity", "error") not in SEVERITIES:
            raise ValueError(f"{path} : règle {r['id']} : sévérité inconnue")
    return pack


def load_tailoring(path: str | Path) -> dict:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    data.setdefault("project", {})
    data.setdefault("deliverables", {})
    data.setdefault("not_applicable", {})
    data.setdefault("severity", {})
    data["_dir"] = str(Path(path).resolve().parent)
    return data


# ---------- Types de règles ----------

def _presence(rule, model: Model, ctx) -> list[Finding]:
    found = model.of_type(*rule["types"])
    need = rule.get("min", 1)
    if len(found) >= need:
        return []
    return [Finding(f"{len(found)} élément(s) de type {', '.join(rule['types'])} ; au moins {need} attendu(s).")]


def _trace(rule, model: Model, ctx) -> list[Finding]:
    linked = set(rule["linked"])
    rel_types = set(rule["rel_types"]) if rule.get("rel_types") else None
    direction = rule.get("direction", "any")
    findings = []
    for e in sorted(model.of_type(*rule["subject"]), key=lambda x: x.name):
        if not any(other.type in linked for _, other in model.links(e.id, direction, rel_types)):
            findings.append(Finding(
                f"Aucune relation vers : {', '.join(sorted(linked)) if len(linked) <= 6 else 'un élément attendu'}.",
                e.id, e.name, e.type,
            ))
    return findings


def _deliverable(rule, model: Model, ctx) -> list[Finding]:
    key = rule["key"]
    declared = ctx["tailoring"]["deliverables"].get(key)
    if not declared:
        return [Finding(f"Livrable « {key} » non déclaré dans [deliverables] du tailoring.")]
    paths = [declared] if isinstance(declared, str) else list(declared)
    root = ctx["root"]
    missing = [p for p in paths if not glob.glob(str(root / p), recursive=True)]
    return [Finding(f"Fichier introuvable : {p}") for p in missing]


def _view(rule, model: Model, ctx) -> list[Finding]:
    wanted = {normalize_viewpoint(v) for v in rule.get("viewpoints", [])}
    contains = set(rule.get("contains", []))
    for v in model.views:
        if wanted and normalize_viewpoint(v.viewpoint) in wanted:
            return []
        if contains and any(model.elements.get(eid) and model.elements[eid].type in contains for eid in v.elements):
            return []
    expected = ", ".join(rule.get("viewpoints", [])) or "—"
    return [Finding(f"Aucune vue avec un de ces viewpoints ({expected})"
                    + (f" ni montrant : {', '.join(sorted(contains))}" if contains else "") + ".")]


def _plateaus(rule, model: Model, ctx) -> list[Finding]:
    plateaus = {p.id for p in model.of_type("Plateau")}
    findings = []
    if len(plateaus) < 2:
        findings.append(Finding(f"{len(plateaus)} plateau(x) ; au moins 2 attendus (base et cible)."))
    gaps = model.of_type("Gap")
    if not gaps:
        findings.append(Finding("Aucun Gap : l'écart entre base et cible n'est pas modélisé."))
    for g in gaps:
        touched = {other.id for _, other in model.links(g.id) if other.id in plateaus}
        if len(touched) < 2:
            findings.append(Finding("Gap relié à moins de deux plateaux distincts.", g.id, g.name, g.type))
    return findings


def _in_view(rule, model: Model, ctx) -> list[Finding]:
    types = set(rule.get("types", []))
    return [
        Finding("Présent dans aucune vue.", e.id, e.name, e.type)
        for e in sorted(model.elements.values(), key=lambda x: (x.type, x.name))
        if (not types or e.type in types) and not model.in_any_view(e.id)
    ]


KINDS = {
    "presence": _presence, "trace": _trace, "deliverable": _deliverable,
    "view": _view, "plateaus": _plateaus, "in_view": _in_view,
}


# ---------- Exécution ----------

def check(model: Model, pack: dict, tailoring: dict, root: str | Path | None = None) -> Report:
    root = Path(root or tailoring["project"].get("root") or tailoring["_dir"])
    if not root.is_absolute():
        root = (Path(tailoring["_dir"]) / root).resolve()
    ctx = {"tailoring": tailoring, "root": root}
    rule_ids = {r["id"] for r in pack["rule"]}
    tailoring_errors = []

    exemptions = tailoring["not_applicable"]
    for rid, decl in exemptions.items():
        if rid not in rule_ids:
            tailoring_errors.append(f"[not_applicable.\"{rid}\"] : règle inconnue.")
        elif not str((decl or {}).get("reason", "")).strip():
            tailoring_errors.append(f"[not_applicable.\"{rid}\"] : une justification (reason) est obligatoire.")
    for rid, sev in tailoring["severity"].items():
        if rid not in rule_ids:
            tailoring_errors.append(f"[severity] « {rid} » : règle inconnue.")
        elif sev not in SEVERITIES:
            tailoring_errors.append(f"[severity] « {rid} » : sévérité « {sev} » inconnue.")

    results = []
    for rule in pack["rule"]:
        severity = tailoring["severity"].get(rule["id"], rule.get("severity", "error"))
        if severity not in SEVERITIES:
            severity = rule.get("severity", "error")
        exempt = exemptions.get(rule["id"])
        if exempt and str(exempt.get("reason", "")).strip():
            results.append(Result(rule, "na", severity, reason=str(exempt["reason"]).strip()))
            continue
        kind = KINDS.get(rule["kind"])
        if kind is None:
            raise ValueError(f"Règle {rule['id']} : type « {rule['kind']} » inconnu")
        findings = kind(rule, model, ctx)
        results.append(Result(rule, "fail" if findings else "pass", severity, findings))

    stats = {}
    for e in model.elements.values():
        stats[e.type] = stats.get(e.type, 0) + 1
    return Report(
        project=tailoring["project"].get("name", "Projet"),
        pack=pack["pack"], phases=pack["phase"], results=results,
        tailoring_errors=tailoring_errors, model_name=model.name,
        model_stats={"elements": len(model.elements), "relationships": len(model.relationships), "views": len(model.views), "by_type": stats},
    )
