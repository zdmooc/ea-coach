"""Rapports : Markdown (lecture humaine, résumé GitHub) et JSON (outillage)."""

from __future__ import annotations

from datetime import date
import json

from .engine import Report

ICON = {"pass": "✅", "na": "➖", ("fail", "error"): "❌", ("fail", "warning"): "⚠️", ("fail", "info"): "ℹ️"}
SEV_LABEL = {"error": "Manque bloquant", "warning": "Alerte", "info": "Information"}
MAX_FINDINGS = 25


def _icon(r) -> str:
    return ICON.get(r.status) or ICON[(r.status, r.severity)]


def to_markdown(report: Report, today: date | None = None) -> str:
    today = today or date.today()
    errors = report.count("fail", "error")
    warnings = report.count("fail", "warning")
    infos = report.count("fail", "info")
    lines = [
        f"# Rapport EA Coach — {report.project}",
        "",
        f"{today.isoformat()} · jeu de règles **{report.pack['name']}** · modèle « {report.model_name} » "
        f"({report.model_stats['elements']} éléments, {report.model_stats['relationships']} relations, {report.model_stats['views']} vues)",
        "",
    ]
    verdict = "✅ Aucun manque bloquant." if report.blocking == 0 else f"❌ {report.blocking} manque(s) bloquant(s) à corriger."
    lines += [
        f"**{verdict}** {warnings} alerte(s), {infos} information(s), "
        f"{report.count('pass')} contrôle(s) conforme(s), {report.count('na')} non applicable(s) par adaptation déclarée.",
        "",
    ]
    if report.tailoring_errors:
        lines += ["## Adaptation (tailoring) invalide", ""] + [f"- ❌ {e}" for e in report.tailoring_errors] + [""]

    lines += ["## Synthèse par phase", "", "| Phase | ✅ | ❌ | ⚠️ | ℹ️ | ➖ |", "| --- | --- | --- | --- | --- | --- |"]
    for ph in report.phases:
        rs = [r for r in report.results if r.rule["phase"] == ph["id"]]
        if not rs:
            continue
        c = lambda st, sev=None: sum(1 for r in rs if r.status == st and (sev is None or r.severity == sev))
        lines.append(f"| {ph['label']} | {c('pass')} | {c('fail', 'error')} | {c('fail', 'warning')} | {c('fail', 'info')} | {c('na')} |")
    lines.append("")

    failing = sorted([r for r in report.results if r.status == "fail"], key=lambda r: ("error", "warning", "info").index(r.severity))
    if failing:
        lines += ["## À corriger", ""]
        for r in failing:
            lines += [f"### {_icon(r)} {r.rule['id']} — {r.rule['title']}", "", f"*{SEV_LABEL[r.severity]}.* {r.rule.get('why', '')}", ""]
            for f in r.findings[:MAX_FINDINGS]:
                who = f"**{f.element_name or '(sans nom)'}** ({f.element_type}) : " if f.element_id else ""
                lines.append(f"- {who}{f.message}")
            if len(r.findings) > MAX_FINDINGS:
                lines.append(f"- … et {len(r.findings) - MAX_FINDINGS} autre(s).")
            lines += ["", f"**Que faire :** {r.rule.get('fix', '')}", ""]

    na = [r for r in report.results if r.status == "na"]
    if na:
        lines += ["## Non applicable (adaptation déclarée)", ""] + [f"- ➖ **{r.rule['id']}** {r.rule['title']} — {r.reason}" for r in na] + [""]

    ok = [r for r in report.results if r.status == "pass"]
    if ok:
        lines += ["## Conforme", ""] + [f"- ✅ {r.rule['id']} {r.rule['title']}" for r in ok] + [""]

    lines += [
        "---",
        "",
        "*EA Coach contrôle la présence et la traçabilité de ce que la méthode attend. Il ne juge pas la qualité "
        "du contenu et ne remplace pas une revue d'architecture. TOGAF® et ArchiMate® sont des marques de The Open Group ; "
        "ce jeu de règles est une lecture outillée de la méthode, non une publication de The Open Group.*",
    ]
    return "\n".join(lines) + "\n"


def to_json(report: Report) -> str:
    return json.dumps({
        "project": report.project,
        "pack": report.pack,
        "model": {"name": report.model_name, **report.model_stats},
        "summary": {
            "blocking": report.blocking,
            "errors": report.count("fail", "error"),
            "warnings": report.count("fail", "warning"),
            "infos": report.count("fail", "info"),
            "passed": report.count("pass"),
            "not_applicable": report.count("na"),
        },
        "tailoring_errors": report.tailoring_errors,
        "results": [
            {
                "id": r.rule["id"], "phase": r.rule["phase"], "title": r.rule["title"], "kind": r.rule["kind"],
                "status": r.status, "severity": r.severity, "reason": r.reason or None,
                "findings": [f.__dict__ for f in r.findings],
            }
            for r in report.results
        ],
    }, ensure_ascii=False, indent=2) + "\n"
