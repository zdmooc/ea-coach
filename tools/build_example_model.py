#!/usr/bin/env python3
"""Génère le modèle ArchiMate (Open Exchange Format) de l'appli cert-exam-trainer,
à partir de son dossier docs/architecture (phases Preliminary → H, ADR-001 à 004).

Ce script ne sert qu'à produire le PREMIER modèle d'exemple. Ensuite, on l'ouvre et
on le fait évoluer dans Archi (Fichier › Importer › Open Exchange XML), puis on le
ré-exporte au même endroit.

    python3 tools/build_example_model.py examples/cert-exam-trainer/model.xml
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET

NS = "http://www.opengroup.org/xsd/archimate/3.0/"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
ET.register_namespace("", NS)
ET.register_namespace("xsi", XSI)

E: dict[str, tuple[str, str, str]] = {}  # id → (type, nom, documentation)
R: list[tuple[str, str, str, str]] = []  # (type, source, target, nom)


def el(id_, type_, name, doc=""):
    E[id_] = (type_, name, doc)


def rel(type_, source, target, name=""):
    assert source in E and target in E, (source, target)
    R.append((type_, source, target, name))


# ---------------- Motivation (Preliminary, Phase A) ----------------
el("sh-candidat", "Stakeholder", "Candidat (utilisateur)", "Réviser partout, savoir quand réserver l'examen, comprendre ses erreurs.")
el("sh-auteur", "Stakeholder", "Auteur des contenus", "Éditer en Markdown, sans double saisie.")
el("sh-opengroup", "Stakeholder", "The Open Group (indirect)", "Respect de la marque, pas de diffusion de questions officielles.")
el("sh-futurs", "Stakeholder", "Futurs utilisateurs", "Contenu en français, appli gratuite.")

el("dr-certif", "Driver", "Préparer TOGAF Foundation puis Practitioner en français")
el("dr-mobile", "Driver", "Réviser sur mobile, souvent sans réseau")
el("dr-markdown", "Driver", "Banques de questions en Markdown peu pratiques sur téléphone")
el("as-biais", "Assessment", "Bonne réponse en position A dans 60 % des questions sources (v1)",
   "391 questions sur 648 dans la première version des sources ; rééquilibré le 1er novembre 2026.")

el("go-reserver", "Goal", "Savoir quand réserver l'examen")
el("go-partout", "Goal", "Réviser partout, y compris hors ligne")
el("go-cout", "Goal", "Coût d'exploitation nul")
el("go-reutiliser", "Goal", "Réutiliser l'appli pour d'autres certifications")

el("oc-f101", "Outcome", "F101 : ≥ 32/40 sur 3 examens blancs consécutifs")
el("oc-f102", "Outcome", "F102 : ≥ 28/40 sur 3 examens blancs consécutifs")
el("oc-zero", "Outcome", "0 € par mois")

principles = {
    "p1": ("Hors ligne d'abord", "Tout le contenu est mis en cache ; aucun appel serveur pendant une session."),
    "p2": ("Coût d'exploitation nul", "Hébergement statique, pas de serveur ni de base de données."),
    "p3": ("Moteur indépendant des certifications", "Aucune règle d'examen dans js/core ; tout est décrit dans pack.json."),
    "p4": ("Le contenu vit dans les dépôts de cours", "Les packs JSON sont générés ; l'appli renvoie vers les cours sans les recopier."),
    "p5": ("Contenu original uniquement", "Pas de questions officielles ni de dumps ; mention de marque TOGAF."),
    "p6": ("Données personnelles sur l'appareil", "Pas de compte ; progression locale, exportable."),
    "p7": ("Un score doit refléter la compréhension", "Options mélangées ; progression remise à zéro quand une question change."),
}
for pid, (name, doc) in principles.items():
    el(f"pr-{pid}", "Principle", f"{pid.upper()} — {name}", doc)

requirements = {
    "r1": ("Fonctionner hors ligne après la première ouverture", "p1"),
    "r2": ("Aucun serveur ni base de données", "p2"),
    "r3": ("Aucune règle de certification dans le moteur", "p3"),
    "r4": ("Questions générées depuis le dépôt de cours, jamais modifiées à la main", "p4"),
    "r5": ("Questions originales et mention de marque", "p5"),
    "r6": ("Progression stockée sur l'appareil et exportable", "p6"),
    "r7": ("Options mélangées à chaque affichage", "p7"),
    "r8": ("Progression remise à zéro quand une question change (empreinte rev)", "p7"),
    "r9": ("Examens blancs au format officiel (nombre, durée, barème, seuil)", None),
    "r10": ("« Prêt à réserver » après 3 examens blancs consécutifs ≥ objectif", None),
}
for rid, (name, principle) in requirements.items():
    el(f"rq-{rid}", "Requirement", f"{rid.upper()} — {name}")
    if principle:
        rel("Influence", f"pr-{principle}", f"rq-{rid}")
el("cs-budget", "Constraint", "Projet personnel, sans budget d'exploitation")
rel("Influence", "cs-budget", "rq-r2")

for sh, targets in {
    "sh-candidat": ["dr-certif", "dr-mobile"],
    "sh-auteur": ["dr-markdown"],
    "sh-opengroup": ["as-biais"],
    "sh-futurs": ["dr-certif"],
}.items():
    for t in targets:
        rel("Association", sh, t)
rel("Influence", "sh-opengroup", "rq-r5")
rel("Influence", "dr-certif", "go-reserver")
rel("Influence", "dr-mobile", "go-partout")
rel("Influence", "dr-markdown", "go-partout")
rel("Influence", "as-biais", "go-reserver")
rel("Association", "sh-candidat", "go-cout")
rel("Association", "sh-futurs", "go-reutiliser")
rel("Realization", "oc-f101", "go-reserver")
rel("Realization", "oc-f102", "go-reserver")
rel("Realization", "oc-zero", "go-cout")
for r, g in [("r1", "go-partout"), ("r2", "oc-zero"), ("r3", "go-reutiliser"), ("r9", "go-reserver"), ("r10", "oc-f101"), ("r10", "oc-f102"), ("r7", "go-reserver"), ("r8", "go-reserver")]:
    rel("Realization", f"rq-{r}", g)

# ---------------- Phase B : métier ----------------
capabilities = {
    "entrainer": "S'entraîner",
    "simuler": "Simuler l'examen",
    "diagnostiquer": "Diagnostiquer (domaines et objectifs X2202)",
    "consolider": "Consolider (révision des erreurs)",
    "decider": "Décider de réserver",
    "ajouter": "Ajouter une certification",
}
for cid, name in capabilities.items():
    el(f"cap-{cid}", "Capability", name)
el("ba-candidat", "BusinessActor", "Candidat")
el("bp-seance", "BusinessProcess", "Séance quotidienne d'entraînement")
el("bp-examen", "BusinessProcess", "Examen blanc chronométré")
el("bp-reservation", "BusinessProcess", "Vérification avant réservation")
el("bp-contenu", "BusinessProcess", "Publication d'une banque de questions")
for bp in ("bp-seance", "bp-examen", "bp-reservation"):
    rel("Assignment", "ba-candidat", bp)
rel("Realization", "bp-seance", "cap-entrainer")
rel("Realization", "bp-seance", "cap-consolider")
rel("Realization", "bp-examen", "cap-simuler")
rel("Realization", "bp-examen", "cap-diagnostiquer")
rel("Realization", "bp-reservation", "cap-decider")
rel("Realization", "bp-contenu", "cap-ajouter")

# ---------------- Phase C : données et applications ----------------
data = {
    "pack": "Pack (définition des examens)",
    "questions": "Questions",
    "objectifs": "Objectifs X2202",
    "session": "Session",
    "progression": "Progression",
    "sauvegarde": "Fichier de sauvegarde",
}
for did, name in data.items():
    el(f"do-{did}", "DataObject", name)

components = {
    "ui": ("Interface mobile (main.js)", "Vues et actions ; aucune règle de certification."),
    "moteur": ("Moteur d'entraînement (js/core)", "Sélection, session, barème, progression, objectifs."),
    "stockage": ("Adaptateur de stockage", "Port de stockage : localStorage, repli mémoire."),
    "sw": ("Service worker (cache hors ligne)", "Réseau d'abord, cache en repli."),
    "pipeline": ("Pipeline de contenu", "content-pipeline/togaf/build.mjs : Markdown → pack JSON."),
    "validateur": ("Validateur de pack", "content-pipeline/validate.mjs, bloquant en CI."),
}
for cid, (name, doc) in components.items():
    el(f"ac-{cid}", "ApplicationComponent", name, doc)

services = {
    "entrainement": ("Entraînement avec correction", "moteur", ["questions", "session", "progression"], "bp-seance"),
    "examen": ("Examen blanc chronométré", "moteur", ["questions", "pack", "session"], "bp-examen"),
    "revision": ("Révision des erreurs", "moteur", ["progression"], "bp-seance"),
    "suivi": ("Suivi de progression et de préparation", "moteur", ["progression", "objectifs"], "bp-reservation"),
    "sauvegarde": ("Sauvegarde (export / import)", "stockage", ["progression", "sauvegarde"], "bp-reservation"),
    "horsligne": ("Fonctionnement hors ligne", "sw", ["pack", "questions"], "bp-seance"),
    "conversion": ("Conversion de contenu", "pipeline", ["pack", "questions", "objectifs"], "bp-contenu"),
    "validation": ("Validation de contenu", "validateur", ["pack", "questions", "objectifs"], "bp-contenu"),
}
for sid, (name, comp, accesses, process) in services.items():
    el(f"as-{sid}", "ApplicationService", name)
    rel("Realization", f"ac-{comp}", f"as-{sid}")
    for d in accesses:
        rel("Access", f"as-{sid}", f"do-{d}")
    rel("Serving", f"as-{sid}", process)
rel("Serving", "ac-moteur", "ac-ui")
rel("Serving", "ac-stockage", "ac-ui")
rel("Serving", "ac-validateur", "ac-pipeline")

for r, comp in [("r3", "moteur"), ("r4", "pipeline"), ("r5", "ui"), ("r5", "validateur"), ("r6", "stockage"),
                ("r7", "moteur"), ("r8", "moteur"), ("r8", "validateur"), ("r9", "moteur"), ("r9", "validateur"), ("r10", "moteur"), ("r1", "sw")]:
    rel("Realization", f"ac-{comp}", f"rq-{r}")

# ---------------- Phase D : technologie ----------------
el("dv-telephone", "Device", "Téléphone (Android, iOS)")
el("ss-navigateur", "SystemSoftware", "Navigateur mobile (Chrome, Samsung Internet, Safari)")
el("nd-pages", "Node", "GitHub Pages")
el("nd-actions", "Node", "GitHub Actions")
el("ts-hebergement", "TechnologyService", "Hébergement statique HTTPS")
el("ts-execution", "TechnologyService", "Exécution JavaScript et stockage local")
el("ts-ci", "TechnologyService", "Intégration continue (tests, validation, publication)")
el("ar-site", "Artifact", "Site statique (_site)")
rel("Composition", "dv-telephone", "ss-navigateur")
rel("Realization", "ss-navigateur", "ts-execution")
rel("Realization", "nd-pages", "ts-hebergement")
rel("Realization", "nd-actions", "ts-ci")
rel("Assignment", "nd-pages", "ar-site")
for comp in ("ui", "moteur", "stockage", "sw"):
    rel("Realization", "ar-site", f"ac-{comp}")
    rel("Serving", "ts-execution", f"ac-{comp}")
for comp in ("pipeline", "validateur"):
    rel("Serving", "ts-ci", f"ac-{comp}")
rel("Realization", "nd-pages", "rq-r2")

# ---------------- Phases E, F : migration ----------------
el("pl-base", "Plateau", "Base : révision sur les fichiers Markdown du dépôt de cours")
el("pl-actuel", "Plateau", "Actuel : appli v2.2 (2 novembre 2026)")
el("pl-cible", "Plateau", "Cible : moteur multi-certifications")
rel("Triggering", "pl-base", "pl-actuel")
rel("Triggering", "pl-actuel", "pl-cible")
el("gp-appli", "Gap", "Pas d'appli mobile, pas d'examen chronométré, scores biaisés")
el("gp-cible", "Gap", "Pas de parcours séquentiel, une seule certification, pas de synchronisation")
rel("Association", "gp-appli", "pl-base")
rel("Association", "gp-appli", "pl-actuel")
rel("Association", "gp-cible", "pl-actuel")
rel("Association", "gp-cible", "pl-cible")

lots = [
    ("v1", "v1 — Moteur générique et pack TOGAF", "Appli v1 publiée", "pl-actuel", "gp-appli"),
    ("v11", "v1.1 — Pack enrichi, justifications, séries", "Appli v1.1 publiée", "pl-actuel", "gp-appli"),
    ("v2", "v2 — Export et import de la progression", "Appli v2 publiée", "pl-actuel", "gp-appli"),
    ("v21", "v2.1 — Empreinte rev, Prêt à réserver (lot 1)", "Appli v2.1 publiée", "pl-actuel", "gp-appli"),
    ("v22", "v2.2 — Objectifs X2202 (lot 2)", "Appli v2.2 publiée", "pl-actuel", "gp-appli"),
    ("v23", "v2.3 — Parcours séquentiel", "Parcours Foundation → Practitioner", "pl-cible", "gp-cible"),
    ("v3", "v3 — Deuxième pack (ArchiMate 3.2)", "Pack ArchiMate publié", "pl-cible", "gp-cible"),
    ("v4", "v4 — Synchronisation optionnelle", "Adaptateur de synchronisation", "pl-cible", "gp-cible"),
]
prev = None
for lid, name, deliverable, plateau, gap in lots:
    el(f"wp-{lid}", "WorkPackage", name)
    el(f"dl-{lid}", "Deliverable", deliverable)
    rel("Realization", f"wp-{lid}", f"dl-{lid}")
    rel("Realization", f"dl-{lid}", plateau)
    rel("Association", f"wp-{lid}", gap)
    if prev:
        rel("Triggering", f"wp-{prev}", f"wp-{lid}")
    prev = lid

# ---------------- Vues ----------------
VIEWS = [
    ("v-motivation", "Motivation — parties prenantes, objectifs, principes", "Motivation",
     [["Stakeholder"], ["Driver", "Assessment"], ["Goal"], ["Outcome"], ["Principle"]]),
    ("v-exigences", "Exigences et leur réalisation", "Requirements Realization",
     [["Principle", "Constraint"], ["Requirement"], ["ApplicationComponent", "Node"]]),
    ("v-capacites", "Carte des capacités et processus", None,
     [["Capability"], ["BusinessProcess", "BusinessActor"]]),
    ("v-applications", "Coopération applicative et données", "Application Cooperation",
     [["ApplicationComponent"], ["ApplicationService"], ["DataObject"]]),
    ("v-technologie", "Technologie et déploiement", "Technology",
     [["ApplicationComponent"], ["TechnologyService", "Artifact"], ["Device", "SystemSoftware", "Node"]]),
    ("v-migration", "Feuille de route (implémentation et migration)", "Implementation and Migration",
     [["Plateau", "Gap"], ["WorkPackage"], ["Deliverable"]]),
]


def build(path: str) -> None:
    model = ET.Element(f"{{{NS}}}model", {"identifier": "id-cert-exam-trainer", f"{{{XSI}}}schemaLocation":
                       f"{NS} http://www.opengroup.org/xsd/archimate/3.1/archimate3_Diagram.xsd"})
    ET.SubElement(model, f"{{{NS}}}name", {"xml:lang": "fr"}).text = "Cert Exam Trainer"
    ET.SubElement(model, f"{{{NS}}}documentation", {"xml:lang": "fr"}).text = (
        "Modèle d'exemple d'EA Coach, dérivé de zdmooc/cert-exam-trainer docs/architecture (phases Preliminary à H, ADR-001 à 004).")
    els = ET.SubElement(model, f"{{{NS}}}elements")
    for eid, (etype, name, doc) in E.items():
        e = ET.SubElement(els, f"{{{NS}}}element", {"identifier": f"id-{eid}", f"{{{XSI}}}type": etype})
        ET.SubElement(e, f"{{{NS}}}name", {"xml:lang": "fr"}).text = name
        if doc:
            ET.SubElement(e, f"{{{NS}}}documentation", {"xml:lang": "fr"}).text = doc
    rels = ET.SubElement(model, f"{{{NS}}}relationships")
    rel_ids = []
    for i, (rtype, s, t, name) in enumerate(R, 1):
        rid = f"id-rel-{i:03d}"
        rel_ids.append((rid, s, t))
        r = ET.SubElement(rels, f"{{{NS}}}relationship", {"identifier": rid, "source": f"id-{s}", "target": f"id-{t}", f"{{{XSI}}}type": rtype})
        if name:
            ET.SubElement(r, f"{{{NS}}}name", {"xml:lang": "fr"}).text = name
    views = ET.SubElement(ET.SubElement(model, f"{{{NS}}}views"), f"{{{NS}}}diagrams")
    for vid, vname, viewpoint, rows in VIEWS:
        attrs = {"identifier": f"id-{vid}", f"{{{XSI}}}type": "Diagram"}
        if viewpoint:
            attrs["viewpoint"] = viewpoint
        v = ET.SubElement(views, f"{{{NS}}}view", attrs)
        ET.SubElement(v, f"{{{NS}}}name", {"xml:lang": "fr"}).text = vname
        placed = {}
        y = 24
        for row in rows:
            members = [eid for eid, (t, _, _) in E.items() if t in row]
            for i, eid in enumerate(members):
                col, line = i % 6, i // 6
                nid = f"id-{vid}-n-{eid}"
                placed[eid] = nid
                ET.SubElement(v, f"{{{NS}}}node", {"identifier": nid, "elementRef": f"id-{eid}", f"{{{XSI}}}type": "Element",
                                                    "x": str(24 + col * 190), "y": str(y + line * 84), "w": "170", "h": "64"})
            y += (max(1, (len(members) + 5) // 6)) * 84 + 36
        for rid, s, t in rel_ids:
            if s in placed and t in placed:
                ET.SubElement(v, f"{{{NS}}}connection", {"identifier": f"{rid}-{vid}", "relationshipRef": rid, f"{{{XSI}}}type": "Relationship",
                                                          "source": placed[s], "target": placed[t]})
    tree = ET.ElementTree(model)
    ET.indent(tree, space="  ")
    xml = ET.tostring(model, encoding="unicode").replace('xml:lang', 'xml:lang')
    with open(path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + xml + "\n")
    print(f"{path} : {len(E)} éléments, {len(R)} relations, {len(VIEWS)} vues")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "examples/cert-exam-trainer/model.xml")
