"""Ligne de commande.

    python -m ea_coach check examples/cert-exam-trainer/tailoring.toml --root ../cert-exam-trainer

Code de sortie : 0 si aucun manque bloquant, 1 sinon (utile en CI), 2 si erreur d'utilisation.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from .engine import check, load_rules, load_tailoring
from .model import load_model
from .report import to_json, to_markdown


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="ea-coach", description="Contrôle de démarche d'architecture (compatible TOGAF®).")
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("check", help="contrôler un projet")
    c.add_argument("tailoring", help="fichier d'adaptation du projet (TOML)")
    c.add_argument("--model", help="modèle ArchiMate (.xml Open Exchange ou .archimate) ; par défaut [project].model")
    c.add_argument("--root", help="racine du projet pour les livrables ; par défaut [project].root")
    c.add_argument("--rules", help="jeu de règles (nom intégré ou fichier) ; par défaut [project].rules")
    c.add_argument("--format", choices=["md", "json"], default="md")
    c.add_argument("--out", help="fichier de sortie (sinon : écran)")
    c.add_argument("--no-fail", action="store_true", help="toujours renvoyer 0")
    args = parser.parse_args(argv)

    try:
        tailoring = load_tailoring(args.tailoring)
        base = Path(tailoring["_dir"])
        model_path = args.model or tailoring["project"].get("model")
        if not model_path:
            raise ValueError("Aucun modèle : utiliser --model ou [project].model dans le tailoring.")
        model_path = Path(model_path) if args.model else base / model_path
        model = load_model(model_path)
        pack = load_rules(args.rules or tailoring["project"].get("rules", "togaf-adm"), base)
        report = check(model, pack, tailoring, args.root)
    except (OSError, ValueError) as err:
        print(f"ea-coach : {err}", file=sys.stderr)
        return 2

    text = to_json(report) if args.format == "json" else to_markdown(report)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text)
    if args.format == "md" and os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(text)
    summary = (f"{report.blocking} manque(s) bloquant(s), {report.count('fail', 'warning')} alerte(s), "
               f"{report.count('pass')} conforme(s), {report.count('na')} non applicable(s).")
    print(summary, file=sys.stderr)
    return 0 if args.no_fail or report.blocking == 0 else 1
