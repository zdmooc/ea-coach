#!/usr/bin/env python3
"""Génère docs/regles-togaf-adm.md à partir du jeu de règles (une seule source : le TOML)."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ea_coach.engine import load_rules  # noqa: E402

KIND = {"presence": "Présence", "trace": "Traçabilité", "deliverable": "Livrable", "view": "Vue",
        "plateaus": "Base / cible / écart", "in_view": "Qualité"}
SEV = {"error": "Bloquant", "warning": "Alerte", "info": "Info"}

pack = load_rules("togaf-adm")
lines = [f"# Règles « {pack['pack']['name']} »", "", f"Référence : {pack['pack']['reference']}.", "",
         "Fichier source : `ea_coach/rules/togaf-adm.toml` (ce tableau est généré par `tools/rules_table.py`).", ""]
for ph in pack["phase"]:
    rules = [r for r in pack["rule"] if r["phase"] == ph["id"]]
    lines += [f"## {ph['label']}", "", "| Règle | Contrôle | Type | Sévérité | Pourquoi |", "| --- | --- | --- | --- | --- |"]
    lines += [f"| {r['id']} | {r['title']} | {KIND[r['kind']]} | {SEV[r['severity']]} | {r['why']} |" for r in rules]
    lines.append("")
Path("docs/regles-togaf-adm.md").write_text("\n".join(lines), encoding="utf-8")
print(f"docs/regles-togaf-adm.md : {len(pack['rule'])} règles")
