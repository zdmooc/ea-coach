"""Tests d'EA Coach (bibliothèque standard uniquement : python -m unittest)."""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import textwrap
import unittest

from ea_coach.cli import main
from ea_coach.engine import check, load_rules, load_tailoring
from ea_coach.model import Element, Model, Relationship, View, load_model, normalize_viewpoint
from ea_coach.report import to_json, to_markdown

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "examples" / "cert-exam-trainer"
DEMO = ROOT / "examples" / "demo-incomplet"
CERT_DELIVERABLES = [
    "docs/architecture/00-preliminary.md", "docs/architecture/01-vision.md", "docs/architecture/06-roadmap.md",
    "docs/architecture/07-governance.md", "docs/architecture/adr/ADR-001-pwa-statique.md",
]


def model(elements, relationships=(), views=()):
    return Model("test", {e.id: e for e in elements}, list(relationships), list(views))


def rule(**kw):
    base = {"id": "T-01", "phase": "p", "title": "t", "severity": "error"}
    return {**base, **kw}


def pack(*rules):
    return {"pack": {"id": "t", "name": "test"}, "phase": [{"id": "p", "label": "Phase"}], "rule": list(rules)}


def tailoring(tmp: Path, text: str = "") -> dict:
    f = tmp / "tailoring.toml"
    f.write_text(textwrap.dedent(text), encoding="utf-8")
    return load_tailoring(f)


class ModelLoading(unittest.TestCase):
    def test_open_exchange_format(self):
        m = load_model(EXAMPLE / "model.xml")
        self.assertEqual(m.source_format, "oef")
        self.assertEqual(m.name, "Cert Exam Trainer")
        self.assertGreater(len(m.of_type("Requirement")), 5)
        self.assertEqual(len(m.views), 6)
        self.assertTrue(all(v.elements for v in m.views))
        principle = m.of_type("Principle")[0]
        self.assertTrue(m.links(principle.id, "out", {"Influence"}))

    def test_archi_native_format(self):
        m = load_model(DEMO / "model.archimate")
        self.assertEqual(m.source_format, "archi")
        self.assertEqual(len(m.of_type("Stakeholder")), 2)
        self.assertEqual({r.type for r in m.relationships}, {"Association", "Realization", "Serving"})
        self.assertEqual(m.views[0].elements, {"id-c1", "id-c2"})
        self.assertEqual(m.views[0].relationships, {"id-rel3"})
        self.assertEqual(normalize_viewpoint(m.views[0].viewpoint), normalize_viewpoint("Application Cooperation"))

    def test_unknown_format(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "x.xml"
            f.write_text("<racine/>", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_model(f)


class RuleKinds(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.t = tailoring(self.tmp)

    def run_rule(self, r, m):
        return check(m, pack(r), self.t).results[0]

    def test_presence(self):
        r = rule(kind="presence", types=["Principle"], min=2)
        self.assertEqual(self.run_rule(r, model([Element("p1", "Principle", "P1")])).status, "fail")
        self.assertEqual(self.run_rule(r, model([Element("p1", "Principle", "P1"), Element("p2", "Principle", "P2")])).status, "pass")

    def test_trace_lists_each_untraced_element(self):
        r = rule(kind="trace", subject=["Goal"], linked=["Stakeholder"])
        m = model([Element("g1", "Goal", "Porté"), Element("g2", "Goal", "Orphelin"), Element("s", "Stakeholder", "S")],
                  [Relationship("r", "Association", "s", "g1")])
        res = self.run_rule(r, m)
        self.assertEqual(res.status, "fail")
        self.assertEqual([f.element_name for f in res.findings], ["Orphelin"])

    def test_trace_direction_and_relation_type(self):
        r = rule(kind="trace", subject=["Requirement"], linked=["ApplicationComponent"], direction="in", rel_types=["Realization"])
        e = [Element("q", "Requirement", "Q"), Element("c", "ApplicationComponent", "C")]
        self.assertEqual(self.run_rule(r, model(e, [Relationship("r", "Association", "c", "q")])).status, "fail")
        self.assertEqual(self.run_rule(r, model(e, [Relationship("r", "Realization", "q", "c")])).status, "fail")  # mauvais sens
        self.assertEqual(self.run_rule(r, model(e, [Relationship("r", "Realization", "c", "q")])).status, "pass")

    def test_deliverable(self):
        r = rule(kind="deliverable", key="vision")
        self.assertIn("non déclaré", self.run_rule(r, model([])).findings[0].message)
        self.t["deliverables"]["vision"] = "docs/vision.md"
        self.assertIn("introuvable", self.run_rule(r, model([])).findings[0].message)
        (self.tmp / "docs").mkdir()
        (self.tmp / "docs/vision.md").write_text("# Vision", encoding="utf-8")
        self.assertEqual(self.run_rule(r, model([])).status, "pass")
        self.t["deliverables"]["vision"] = ["docs/*.md", "docs/absent.md"]
        self.assertEqual(len(self.run_rule(r, model([])).findings), 1)

    def test_view_by_viewpoint_or_content(self):
        r = rule(kind="view", viewpoints=["Implementation and Migration"], contains=["Plateau"])
        e = [Element("p", "Plateau", "P")]
        self.assertEqual(self.run_rule(r, model(e, views=[View("v", "V", "Layered", {"x"})])).status, "fail")
        self.assertEqual(self.run_rule(r, model(e, views=[View("v", "V", "implementation_migration")])).status, "pass")
        self.assertEqual(self.run_rule(r, model(e, views=[View("v", "V", "", {"p"})])).status, "pass")

    def test_plateaus_and_gap(self):
        r = rule(kind="plateaus")
        p = [Element("a", "Plateau", "Base"), Element("b", "Plateau", "Cible")]
        self.assertEqual(len(self.run_rule(r, model(p[:1])).findings), 2)
        gap_one_side = model(p + [Element("g", "Gap", "G")], [Relationship("r1", "Association", "g", "a")])
        self.assertEqual(self.run_rule(r, gap_one_side).findings[0].element_name, "G")
        ok = model(p + [Element("g", "Gap", "G")], [Relationship("r1", "Association", "g", "a"), Relationship("r2", "Association", "g", "b")])
        self.assertEqual(self.run_rule(r, ok).status, "pass")

    def test_in_view(self):
        r = rule(kind="in_view")
        m = model([Element("a", "Goal", "Vu"), Element("b", "Goal", "Oublié")], views=[View("v", "V", "", {"a"})])
        self.assertEqual([f.element_name for f in self.run_rule(r, m).findings], ["Oublié"])


class Tailoring(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.p = pack(rule(kind="presence", types=["Principle"]), rule(id="T-02", kind="presence", types=["Goal"], severity="warning"))

    def test_justified_exemption_is_not_applicable(self):
        t = tailoring(self.tmp, '[not_applicable."T-01"]\nreason = "Hors périmètre"\n')
        rep = check(model([]), self.p, t)
        self.assertEqual((rep.results[0].status, rep.results[0].reason), ("na", "Hors périmètre"))
        self.assertEqual(rep.blocking, 0)

    def test_exemption_without_reason_is_refused(self):
        t = tailoring(self.tmp, '[not_applicable."T-01"]\nreason = "  "\n')
        rep = check(model([]), self.p, t)
        self.assertEqual(rep.results[0].status, "fail")  # la règle s'applique quand même
        self.assertEqual(len(rep.tailoring_errors), 1)
        self.assertEqual(rep.blocking, 2)

    def test_unknown_rule_and_severity_override(self):
        t = tailoring(self.tmp, '[not_applicable."X-99"]\nreason = "r"\n[severity]\n"T-01" = "warning"\n"T-02" = "grave"\n')
        rep = check(model([]), self.p, t)
        self.assertEqual(rep.results[0].severity, "warning")
        self.assertEqual(len(rep.tailoring_errors), 2)
        self.assertEqual(rep.count("fail", "error"), 0)


class TogafPack(unittest.TestCase):
    def test_pack_is_consistent(self):
        p = load_rules("togaf-adm")
        self.assertGreaterEqual(len(p["rule"]), 30)
        for r in p["rule"]:
            for key in ("title", "why", "fix"):
                self.assertTrue(r.get(key), f"{r['id']} : champ {key} vide")

    def test_cert_exam_trainer_example_is_complete(self):
        with tempfile.TemporaryDirectory() as d:
            for rel in CERT_DELIVERABLES:
                f = Path(d) / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text("# livrable", encoding="utf-8")
            rep = check(load_model(EXAMPLE / "model.xml"), load_rules("togaf-adm"), load_tailoring(EXAMPLE / "tailoring.toml"), d)
            failing = [(r.rule["id"], [f.message for f in r.findings]) for r in rep.results if r.status == "fail"]
            self.assertEqual(failing, [])

    def test_demo_reports_expected_gaps(self):
        rep = check(load_model(DEMO / "model.archimate"), load_rules("togaf-adm"), load_tailoring(DEMO / "tailoring.toml"))
        status = {r.rule["id"]: r.status for r in rep.results}
        self.assertEqual(status["B-03"], "na")
        for rid in ("PRE-01", "A-04", "A-06", "EF-01", "RM-02", "D-01"):
            self.assertEqual(status[rid], "fail", rid)
        self.assertEqual(status["A-01"], "pass")
        rm02 = next(r for r in rep.results if r.rule["id"] == "RM-02")
        self.assertEqual([f.element_name for f in rm02.findings], ["Disponibilité 99,9 %"])
        self.assertTrue(any("D-02" in e for e in rep.tailoring_errors))
        md = to_markdown(rep)
        self.assertIn("## Adaptation (tailoring) invalide", md)
        self.assertIn("Migration purement technique", md)
        data = json.loads(to_json(rep))
        self.assertEqual(data["summary"]["blocking"], rep.blocking)


class CommandLine(unittest.TestCase):
    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_exit_codes(self):
        code, out, _ = self.run_cli("check", str(DEMO / "tailoring.toml"))
        self.assertEqual(code, 1)
        self.assertIn("# Rapport EA Coach", out)
        self.assertEqual(self.run_cli("check", str(DEMO / "tailoring.toml"), "--no-fail")[0], 0)
        code, out, _ = self.run_cli("check", str(DEMO / "tailoring.toml"), "--format", "json", "--no-fail")
        self.assertEqual(json.loads(out)["project"], "Démo incomplète (banque fictive)")
        self.assertEqual(self.run_cli("check", "absent.toml")[0], 2)


if __name__ == "__main__":
    unittest.main()
