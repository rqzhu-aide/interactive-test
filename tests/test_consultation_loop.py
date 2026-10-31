import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from consultation_observer import CAPABILITY, COMPACT_RENDERERS, evaluate_frames, retained_frames, public_reply_correspondence, _inventory_path


class Transcript:
    """Explicit public transcript plus independent immutable observation snapshots."""
    def __init__(self):
        self.journal, self.frames, self.indexes, self.scopes, self.plans = [], [], [], {}, {}
        self.scope_exports = {}
        self.observed_project_root = "C:/consultation fixture"

    def row(self, kind, payload):
        row = {"event_id": "event-" + str(len(self.journal) + 1), "sequence": len(self.journal) + 1,
               "type": kind, "payload": copy.deepcopy(payload)}
        self.journal.append(row)
        return row

    def scope(self, name, action="analysis", findings=(), basis=()):
        scope = {"scope_id": name, "action": action, "basis_versions": list(basis), "findings_refs": list(findings),
                 "public_scope": {"target": "Target " + name, "population": "All eligible sites",
                                  "evidence": "The available site panel", "approach": "Approach " + name,
                                  "checks": ["Assess trends and overlap"], "outputs": "Bounded findings " + name,
                                  "claim_boundary": "Conditional on the stated assumptions"},
                 "execution_plan": {"kind": action, "objective": "Objective " + name, "inputs": []}}
        self.scopes[name] = scope
        self.row("memory_updated", {"changes": {"action_scopes": [scope]}})
        return scope

    def offer(self, name):
        scope = self.scopes[name]
        return {"option_id": "choose-" + name, "scope_ref": name, "proposal": scope["public_scope"], "execution_plan": scope["execution_plan"]}

    def reply(self, user, options=(), findings=(), message=None, explanation="Current understanding", renderer=None):
        number = len(self.frames) + 1
        response = {"status": explanation, "next_steps": [self.offer(name) for name in options]}
        if findings:
            response["findings"] = {"work_refs": list(findings), "summary": "Observed result " + str(number),
                                    "diagnostics": ["Diagnostics discussed " + str(number)],
                                    "limitations": ["Limits remain conditional " + str(number)]}
        text = explanation + "\n"
        for name in options:
            if renderer not in COMPACT_RENDERERS:
                text += self.scopes[name]["execution_plan"]["objective"] + "\n"
            for value in self.scopes[name]["public_scope"].values():
                text += ("; ".join(value) if isinstance(value, list) else value) + "\n"
            if renderer in COMPACT_RENDERERS:
                relative = "scopes/" + name + "/scope.json"
                self.scope_exports[relative] = json.dumps(self.scopes[name], sort_keys=True, separators=(",", ":")) + "\n"
                scope_file = self.observed_project_root + "/" + relative
                response["next_steps"][list(options).index(name)]["scope_file"] = scope_file
                text += "[Full saved scope](<" + scope_file + ">)\n"
        if findings:
            text += response["findings"]["summary"] + "\n" + "\n".join(response["findings"]["diagnostics"] + response["findings"]["limitations"])
        exchange_id = "exchange-" + str(number)
        exchange = {"exchange_id": exchange_id, "response": response}
        if renderer is not None:
            exchange["renderer"] = renderer
        self.row("exchange_prepared", {"exchange": exchange})
        findings_versions = [{"ref": name, "event_ref": row["event_id"]} for name in findings
                             for row in self.journal if row.get("payload", {}).get("run", {}).get("run_id") == name]
        self.indexes.append({"exchange_id": exchange_id, "response_sha256": hashlib.sha256(text.encode()).hexdigest(),
                             "findings_basis_versions": findings_versions})
        self.frames.append(copy.deepcopy({"event": f"{number:03d}", "public": {"user": user, "assistant": text if message is None else message},
                                         "journal": self.journal, "exchange_indexes": self.indexes, "plans": self.plans,
                                         "scope_exports": self.scope_exports, "observed_project_root": self.observed_project_root, "files": []}))
        return exchange_id

    def decide(self, scope, user, offer=None, disposition="accept"):
        ref = "user-" + str(len(self.journal) + 1)
        self.row("memory_updated", {"changes": {"evidence": [{"evidence_id": ref, "kind": "user_statement", "source_excerpt": user}]}})
        decision_id = "decision-" + str(len(self.journal) + 1)
        decision = {"decision_id": decision_id, "scope_ref": scope, "disposition": disposition,
                    "exchange_ref": offer or "exchange-" + str(len(self.frames)), "option_id": "choose-" + scope, "user_refs": [ref]}
        self.row("reply_interpreted", {"interpretation": {"action_decisions": [decision]}})
        return decision_id

    def run(self, scope, decision):
        run_id = "run-" + scope
        record = {"run_id": run_id, "kind": self.scopes[scope]["action"],
                  "authorization_binding": {"policy": CAPABILITY, "scope_ref": scope,
                                            "authorization_ref": decision, "basis_versions": self.scopes[scope]["basis_versions"]}}
        self.row("run_started", {"run": record})
        self.plans["runs/" + run_id + "/plan.yaml"] = record
        return run_id


class LoopChronologyTests(unittest.TestCase):
    def test_sourced_report_formats_preserve_exact_science_and_actual_request_checks(self):
        for defect, expected in ((None, None), ("claim", "compact_execution_scope_mismatch"),
                                 ("binding", "unbound_presentation_adjustment"),
                                 ("source", "unbound_presentation_adjustment"),
                                 ("actual_request", "unobserved_later_user_choice")):
            with self.subTest(defect=defect):
                t = Transcript()
                t.scope("report", "report", ["review-design"])
                t.scopes["report"]["execution_plan"].update(format="markdown", claim_boundary="Conditional evidence only")
                t.journal[0]["payload"]["changes"]["action_scopes"][0] = copy.deepcopy(t.scopes["report"])
                t.reply("Please help", ["report"], ["review-design"], renderer="lead-markdown-v6")
                user = "Yes, save that report and include HTML."
                selected = t.decide("report", user)
                decision = t.journal[-1]["payload"]["interpretation"]["action_decisions"][0]
                adjustment = {"formats": ["markdown", "html"], "user_ref": decision["user_refs"][0]}
                decision["presentation_adjustment"] = adjustment
                source_event = t.journal[-2]["event_id"]
                if defect == "source":
                    adjustment["user_ref"] = "missing-source"
                run_id = t.run("report", selected)
                run = t.journal[-1]["payload"]["run"]
                run["plan_ref"] = "runs/" + run_id + "/plan.yaml"
                run["authorization_binding"]["presentation_adjustment"] = {**adjustment, "source_event_ref": source_event}
                if defect == "binding":
                    run["authorization_binding"]["presentation_adjustment"]["source_event_ref"] = "wrong-event"
                t.plans[run["plan_ref"]] = {**copy.deepcopy(t.scopes["report"]["execution_plan"]),
                    "run_id": run_id, "format": "markdown, html", "report_contract": "report-deliverables-v1",
                    "authorization_binding": copy.deepcopy(run["authorization_binding"])}
                if defect == "claim":
                    t.plans[run["plan_ref"]]["claim_boundary"] = "Unconditional proof"
                t.reply("I have not selected any report." if defect == "actual_request" else user,
                        renderer="lead-markdown-v6")
                result = evaluate_frames(t.frames)
                if expected:
                    self.assertIn(expected, [item["code"] for item in result["findings"]], result)
                else:
                    self.assertEqual(result["status"], "no_structural_breach", result)
                    self.assertEqual(result["actions"][0]["presentation_adjustment"]["formats"], ["markdown", "html"])
                    self.assertTrue(result["actions"][0]["semantic_review_required"])

    def compact_offer(self, renderer="lead-markdown-v5"):
        t = Transcript()
        t.scope("main")
        t.scopes["main"]["execution_plan"]["estimator"] = "Prespecified model with center-cluster uncertainty"
        t.journal[0]["payload"]["changes"]["action_scopes"][0] = copy.deepcopy(t.scopes["main"])
        t.reply("Please help", ["main"], renderer=renderer)
        selected = t.decide("main", "Use that scope")
        run_id = t.run("main", selected)
        run = t.journal[-1]["payload"]["run"]
        run["plan_ref"] = "runs/" + run_id + "/plan.yaml"
        t.plans[run["plan_ref"]] = {**copy.deepcopy(t.scopes["main"]["execution_plan"]),
                                  "run_id": run_id, "authorization_binding": copy.deepcopy(run["authorization_binding"])}
        t.reply("Use that scope", renderer=renderer)
        return t

    def test_v6_keeps_compact_scope_checks_without_requiring_status_or_schema_labels(self):
        for defect, expected in ((None, None), ("term", "scope_not_presented"),
                                 ("link", "scope_export_not_linked"),
                                 ("export", "scope_export_mismatch"),
                                 ("plan", "compact_execution_scope_mismatch"),
                                 ("missing_export", "scope_export_unavailable"),
                                 ("missing_plan", "compact_execution_plan_unavailable")):
            with self.subTest(defect=defect):
                t = self.compact_offer("lead-markdown-v6")
                # Independent observation accepts natural paragraphs, not schema labels.
                text = t.frames[0]["public"]["assistant"].replace("\n", "\n\n")
                for frame in t.frames:
                    exchange = next(row["payload"]["exchange"] for row in frame["journal"]
                                    if row["type"] == "exchange_prepared")
                    exchange["response"].pop("status")
                if defect == "term":
                    text = text.replace("All eligible sites\n\n", "")
                elif defect == "link":
                    text = text.replace("scopes/main/scope.json>)", "scopes/other/scope.json>)")
                elif defect == "export":
                    exported = copy.deepcopy(t.scopes["main"])
                    exported["execution_plan"]["estimator"] = "A different method"
                    t.frames[0]["scope_exports"]["scopes/main/scope.json"] = json.dumps(exported)
                elif defect == "plan":
                    t.frames[-1]["plans"]["runs/run-main/plan.yaml"]["extra_procedure"] = "Unselected subgroup search"
                elif defect == "missing_export":
                    t.frames[0]["scope_exports"] = {}
                elif defect == "missing_plan":
                    t.frames[-1]["plans"] = {}
                t.frames[0]["public"]["assistant"] = text
                for frame in t.frames:
                    frame["exchange_indexes"][0]["response_sha256"] = hashlib.sha256(text.encode()).hexdigest()
                result = evaluate_frames(t.frames)
                if expected:
                    codes = [item["code"] for item in result["findings"] + result["unobserved"]]
                    self.assertIn(expected, codes, result)
                else:
                    self.assertEqual(result["status"], "no_structural_breach", result)
                    self.assertEqual(result["actions"][0]["scope_text_correspondence"], "matched")
                    self.assertEqual(result["actions"][0]["scope_export_correspondence"], "matched")
                    self.assertTrue(result["actions"][0]["semantic_review_required"])

    def test_compact_offer_keeps_public_terms_and_exact_linked_scope_without_plan_dump(self):
        t = self.compact_offer()
        self.assertNotIn("Prespecified model", t.frames[0]["public"]["assistant"])
        result = evaluate_frames(t.frames)
        self.assertEqual(result["status"], "no_structural_breach", result)
        self.assertEqual(result["actions"][0]["scope_text_correspondence"], "matched")
        self.assertEqual(result["actions"][0]["scope_export_correspondence"], "matched")
        self.assertTrue(result["actions"][0]["semantic_review_required"])

    def test_v10_visible_scope_answer_keeps_full_terms_export_and_execution_checks(self):
        for defect, expected in ((None, None), ("term", "scope_not_presented"), ("link", "scope_export_not_linked"),
                                 ("plan", "compact_execution_scope_mismatch"), ("missing_plan", "compact_execution_plan_unavailable")):
            with self.subTest(defect=defect):
                t = self.compact_offer("lead-markdown-v10")
                text = ("[To answer your question]\n\n[1] The requested complete scope.\n\n"
                        + t.frames[0]["public"]["assistant"].removeprefix("Current understanding\n")
                        + "\n[Next steps]\n\n[1] Choose analysis.\n\nUse the complete scope in [1] under [To answer your question].")
                for frame in t.frames:
                    offered = next(row["payload"]["exchange"] for row in frame["journal"] if row["type"] == "exchange_prepared")
                    offered["response"].pop("status")
                    offered["response"]["user_questions"] = [{"question_ref": "request", "text": "Please explain the complete scope.",
                                                               "answer": "The requested complete scope.", "scope_ref": "main"}]
                if defect == "term":
                    text = text.replace("All eligible sites\n", "")
                elif defect == "link":
                    text = text.replace("[Full saved scope]", "[Saved artifact]")
                elif defect == "plan":
                    t.frames[-1]["plans"]["runs/run-main/plan.yaml"]["estimator"] = "Unselected model"
                elif defect == "missing_plan":
                    t.frames[-1]["plans"] = {}
                t.frames[0]["public"]["assistant"] = text
                for frame in t.frames:
                    frame["exchange_indexes"][0]["response_sha256"] = hashlib.sha256(text.encode()).hexdigest()
                result = evaluate_frames(t.frames)
                if expected:
                    self.assertIn(expected, [item["code"] for item in result["findings"] + result["unobserved"]], result)
                else:
                    self.assertEqual(result["status"], "no_structural_breach", result)
                    self.assertEqual(result["actions"][0]["scope_text_correspondence"], "matched")
                    self.assertEqual(result["actions"][0]["scope_export_correspondence"], "matched")
                    self.assertTrue(result["actions"][0]["semantic_review_required"])

    def test_v7_v8_keep_scope_checks_with_flat_numbered_presentation(self):
        for renderer in ("lead-markdown-v7", "lead-markdown-v8"):
            for defect, expected in ((None, None), ("term", "scope_not_presented"),
                                     ("link", "scope_export_not_linked"),
                                     ("export", "scope_export_mismatch"),
                                     ("plan", "compact_execution_scope_mismatch"),
                                     ("missing_export", "scope_export_unavailable"),
                                     ("missing_plan", "compact_execution_plan_unavailable")):
                with self.subTest(renderer=renderer, defect=defect):
                    t = self.compact_offer(renderer)
                    text = t.frames[0]["public"]["assistant"]
                    prefix = ("[What has been done]\n\n[1] Current understanding\n\n"
                              "[Questions for you]\n\n[1] Which cohort applies?\n\n"
                              "[Next steps]\n\n[1] Investigate eligible sites\n\n"
                              if renderer == "lead-markdown-v8" else "Option 1: Investigate eligible sites\n\n")
                    text = prefix + text.removeprefix("Current understanding\n")
                    if defect == "term":
                        text = text.replace("All eligible sites\n", "")
                    elif defect == "link":
                        text = text.replace("scopes/main/scope.json>)", "scopes/other/scope.json>)")
                    elif defect == "export":
                        exported = copy.deepcopy(t.scopes["main"])
                        exported["execution_plan"]["estimator"] = "A different method"
                        t.frames[0]["scope_exports"]["scopes/main/scope.json"] = json.dumps(exported)
                    elif defect == "plan":
                        t.frames[-1]["plans"]["runs/run-main/plan.yaml"]["extra_procedure"] = "Unselected subgroup search"
                    elif defect == "missing_export":
                        t.frames[0]["scope_exports"] = {}
                    elif defect == "missing_plan":
                        t.frames[-1]["plans"] = {}
                    t.frames[0]["public"]["assistant"] = text
                    for frame in t.frames:
                        frame["exchange_indexes"][0]["response_sha256"] = hashlib.sha256(text.encode()).hexdigest()
                    result = evaluate_frames(t.frames)
                    if expected:
                        self.assertIn(expected, [item["code"] for item in result["findings"] + result["unobserved"]], result)
                    else:
                        self.assertEqual(result["status"], "no_structural_breach", result)
                        self.assertNotIn("Prespecified model", text)
                        self.assertEqual(result["actions"][0]["scope_text_correspondence"], "matched")
                        self.assertEqual(result["actions"][0]["scope_export_correspondence"], "matched")
                        self.assertTrue(result["actions"][0]["semantic_review_required"])

    def test_v8_reused_item_number_is_neither_an_option_identity_nor_permission(self):
        t = Transcript()
        t.scope("main")
        t.reply("Help", ["main"], renderer="lead-markdown-v8")
        body = ("[Questions for you]\n\n[1] Which cohort applies?\n\n[Next steps]\n\n[1] "
                + t.frames[0]["public"]["assistant"])
        t.frames[0]["public"]["assistant"] = body
        t.frames[0]["exchange_indexes"][0]["response_sha256"] = hashlib.sha256(body.encode()).hexdigest()
        t.run("main", "[1]")
        user = "For Questions for you [1], the cohort is 2024."
        t.reply(user, renderer="lead-markdown-v8")
        result = evaluate_frames(t.frames)
        self.assertIn("unbound_protected_start", [item["code"] for item in result["findings"]], result)
        self.assertEqual(result["response_correspondence"][0]["status"], "exact")
        self.assertEqual(t.frames[-1]["public"]["user"], user)

    def test_v8_wrapped_sections_preserve_exact_body_without_certifying_user_meaning(self):
        for heading in ("Answers to your questions", "What has been done", "Questions for you", "Next steps"):
            with self.subTest(heading=heading):
                body = "[" + heading + "]\n\n[1] First item.\n\n[2] Second item."
                expected = hashlib.sha256(body.encode()).hexdigest()
                result = public_reply_correspondence("Introduction\n\n" + body + "\n\nClosing", expected)
                self.assertEqual(result["status"], "wrapped")
                self.assertTrue(result["semantic_review_required"])
                changed = public_reply_correspondence(body.replace("[2]", "[1]"), expected)
                self.assertEqual(changed["status"], "body_changed")

    def test_compact_offer_v6_keeps_public_terms_and_exact_linked_scope_without_plan_dump(self):
        t = self.compact_offer(renderer="lead-markdown-v6")
        self.assertNotIn("Prespecified model", t.frames[0]["public"]["assistant"])
        result = evaluate_frames(t.frames)
        self.assertEqual(result["status"], "no_structural_breach", result)
        self.assertEqual(result["actions"][0]["scope_text_correspondence"], "matched")
        self.assertEqual(result["actions"][0]["scope_export_correspondence"], "matched")
        self.assertTrue(result["actions"][0]["semantic_review_required"])

    def test_compact_offer_v6_omitted_material_term_cannot_hide_behind_renderer_identity(self):
        t = self.compact_offer(renderer="lead-markdown-v6")
        text = t.frames[0]["public"]["assistant"].replace("All eligible sites\n", "")
        t.frames[0]["public"]["assistant"] = text
        for frame in t.frames:
            frame["exchange_indexes"][0]["response_sha256"] = hashlib.sha256(text.encode()).hexdigest()
        result = evaluate_frames(t.frames)
        self.assertIn("scope_not_presented", [item["code"] for item in result["findings"]])

    def test_compact_offer_omitted_material_term_cannot_hide_behind_renderer_identity(self):
        t = self.compact_offer()
        text = t.frames[0]["public"]["assistant"].replace("All eligible sites\n", "")
        t.frames[0]["public"]["assistant"] = text
        for frame in t.frames:
            frame["exchange_indexes"][0]["response_sha256"] = hashlib.sha256(text.encode()).hexdigest()
        result = evaluate_frames(t.frames)
        self.assertIn("scope_not_presented", [item["code"] for item in result["findings"]])

    def test_compact_offer_checks_link_artifact_and_full_execution_plan_separately(self):
        for defect, expected in (("link", "scope_export_not_linked"),
                                 ("artifact", "scope_export_mismatch"),
                                 ("plan", "changed_execution_scope")):
            with self.subTest(defect=defect):
                t = self.compact_offer()
                if defect == "link":
                    t.frames[0]["public"]["assistant"] = t.frames[0]["public"]["assistant"].replace("scopes/main/scope.json>)", "scopes/other/scope.json>)")
                elif defect == "artifact":
                    exported = copy.deepcopy(t.scopes["main"])
                    exported["execution_plan"]["estimator"] = "A different method"
                    t.frames[0]["scope_exports"]["scopes/main/scope.json"] = json.dumps(exported)
                else:
                    t.frames[-1]["plans"]["runs/run-main/plan.yaml"]["estimator"] = "A different method"
                result = evaluate_frames(t.frames)
                self.assertIn(expected, [item["code"] for item in result["findings"]])

    def test_compact_scope_export_missing_at_offer_remains_unobserved_even_if_added_later(self):
        t = self.compact_offer()
        t.frames[0]["scope_exports"] = {}
        result = evaluate_frames(t.frames)
        self.assertEqual(result["status"], "unobserved", result)
        self.assertIn("scope_export_unavailable", [item["code"] for item in result["unobserved"]])
        self.assertEqual(result["actions"][0]["scope_export_correspondence"], "unavailable")

    def test_compact_full_plan_rejects_added_unoffered_execution_terms(self):
        t = self.compact_offer()
        t.frames[-1]["plans"]["runs/run-main/plan.yaml"]["extra_procedure"] = "Unselected subgroup search"
        result = evaluate_frames(t.frames)
        self.assertIn("compact_execution_scope_mismatch", [item["code"] for item in result["findings"]])

    def test_compact_link_location_uses_independent_observed_root(self):
        for missing in (True, False):
            with self.subTest(missing=missing):
                t = self.compact_offer()
                if missing:
                    del t.frames[0]["observed_project_root"]
                else:
                    t.frames[0]["observed_project_root"] = "C:/another project"
                result = evaluate_frames(t.frames)
                collection = "unobserved" if missing else "findings"
                expected = "scope_export_location_unverified" if missing else "scope_export_wrong_location"
                self.assertIn(expected, [item["code"] for item in result[collection]])

    def test_v4_offer_still_requires_visible_execution_terms(self):
        t = self.compact_offer()
        for frame in t.frames:
            frame["journal"][1]["payload"]["exchange"]["renderer"] = "lead-markdown-v4"
        result = evaluate_frames(t.frames)
        self.assertIn("scope_not_presented", [item["code"] for item in result["findings"]])

    def captured_wrapper(self, prefix="Intro\n", capture_prefix=None, wrapper_review="The introduction only identifies the consultation."):
        t = Transcript()
        t.scope("main")
        exchange = t.reply("Please help", ["main"], explanation="[Status]\nCurrent understanding")
        body = t.frames[0]["public"]["assistant"]
        t.frames[0]["response_bodies"] = {exchange: body}
        t.frames[0]["public"]["assistant"] = prefix + body
        capture = (prefix if capture_prefix is None else capture_prefix) + body
        start = len(capture.encode("utf-8")) - len(body.encode("utf-8"))
        source = "exchanges/" + exchange + "/observations/actual.txt"
        delivery = {"delivery_id": "delivery-1", "exchange_ref": exchange, "source_ref": source,
                    "response_sha256": t.indexes[0]["response_sha256"],
                    "observed_response_sha256": hashlib.sha256(capture.encode("utf-8")).hexdigest(),
                    "response_span": {"start_byte": start, "end_byte": len(capture.encode("utf-8"))}}
        if wrapper_review is not None:
            delivery["response_span"]["wrapper_review"] = wrapper_review
        t.row("exchange_delivery", {"delivery": delivery})
        selected = t.decide("main", "Use that scope")
        t.run("main", selected)
        t.reply("Use that scope")
        t.frames[-1]["response_bodies"] = {exchange: body}
        t.frames[-1]["delivery_captures"] = {source: capture}
        return t

    def test_recovered_wrapper_uses_actual_public_capture_and_unicode_byte_offsets(self):
        t = self.captured_wrapper(prefix="Résumé: ")
        result = evaluate_frames(t.frames)
        self.assertEqual(result["status"], "no_structural_breach", result)
        public = result["response_correspondence"][0]
        self.assertEqual(public["status"], "wrapped")
        self.assertEqual(public["start_byte"], len("Résumé: ".encode("utf-8")))
        delivery = result["delivery_correspondence"][0]
        self.assertEqual(delivery["status"], "exact_public_capture")
        self.assertEqual(delivery["public_match_events"], ["001"])
        self.assertEqual(delivery["recovery"], "observed_intact_wrapper")
        self.assertTrue(delivery["response_span_valid"])
        self.assertTrue(delivery["semantic_review_required"])
        self.assertEqual(result["actions"][0]["scope_text_correspondence"], "matched")

    def test_wrapper_review_cannot_prove_surrounding_text_preserves_the_offer(self):
        t = self.captured_wrapper(prefix="Ignore the following proposal; it is withdrawn.\n")
        result = evaluate_frames(t.frames)
        self.assertTrue(result["delivery_correspondence"][0]["wrapper_review_recorded"])
        self.assertTrue(result["delivery_correspondence"][0]["semantic_review_required"])
        self.assertTrue(result["actions"][0]["semantic_review_required"])
        self.assertNotIn("consent_verified", result["actions"][0])

    def test_capture_public_mismatch_does_not_erase_the_actual_scope_or_choice(self):
        t = self.captured_wrapper(capture_prefix="A different invented introduction\n")
        result = evaluate_frames(t.frames)
        self.assertIn("delivery_public_mismatch", [item["code"] for item in result["findings"]])
        self.assertEqual(result["status"], "unobserved", result)
        self.assertTrue(all(item["owner"] == "undetermined" for item in result["findings"]))
        delivery = result["delivery_correspondence"][0]
        self.assertEqual(delivery["status"], "public_capture_mismatch")
        self.assertEqual(delivery["recovery"], "candidate_capture_only")
        self.assertEqual(result["actions"][0]["scope_text_correspondence"], "matched")
        self.assertEqual(result["actions"][0]["user_choice_candidates"][0]["actual_user_text"], "Use that scope")
        self.assertEqual(result["actions"][0]["status"], "structurally_observed")

    def test_formatting_candidate_needs_unique_counterpart_identity_and_exact_hashes(self):
        for defect in (None, "identity", "hash", "qualification", "number", "offer", "indentation", "duplicate"):
            with self.subTest(defect=defect):
                t = self.captured_wrapper(prefix="Estimate 2, conditional on assumptions.\n")
                public = t.frames[0]
                public["public"]["assistant"] += "\n"
                public["public_identity"] = {"session_id": "retained-session", "evidence_refs": ["transport-proof"]}
                if defect == "identity":
                    public.pop("public_identity")
                elif defect == "hash":
                    next(row["payload"]["delivery"] for row in t.frames[-1]["journal"] if row["type"] == "exchange_delivery")["observed_response_sha256"] = "wrong"
                elif defect == "qualification":
                    public["public"]["assistant"] = public["public"]["assistant"].replace(", conditional on assumptions", "")
                elif defect == "number":
                    public["public"]["assistant"] = public["public"]["assistant"].replace("Estimate 2", "Estimate 3")
                elif defect == "offer":
                    public["public"]["assistant"] += "The offer is withdrawn."
                elif defect == "indentation":
                    public["public"]["assistant"] = public["public"]["assistant"].replace("All eligible sites", "    All eligible sites")
                elif defect == "duplicate":
                    extra = copy.deepcopy(public)
                    extra["event"] = "001a"
                    t.frames.insert(1, extra)
                result = evaluate_frames(t.frames)
                mismatch = next(item for item in result["findings"] if item["code"] == "delivery_public_mismatch")
                self.assertEqual("adjudication_candidate" in mismatch, defect is None, result)
                self.assertEqual(result["status"], "unobserved")

    def test_missing_capture_or_review_is_coverage_without_fabricated_public_mismatch(self):
        for missing_capture in (True, False):
            with self.subTest(missing_capture=missing_capture):
                t = self.captured_wrapper(wrapper_review=None)
                if missing_capture:
                    t.frames[-1].pop("delivery_captures")
                result = evaluate_frames(t.frames)
                self.assertEqual(result["status"], "unobserved", result)
                self.assertFalse(result["findings"])
                expected = "delivery_capture_unavailable" if missing_capture else "wrapper_review_unobserved"
                self.assertIn(expected, [item.get("code") for item in result["unobserved"]])
                self.assertEqual(result["actions"][0]["scope_text_correspondence"], "matched")

    def test_recovery_span_cannot_use_character_offsets_or_hide_changed_body_bytes(self):
        for wrong_offset in (True, False):
            with self.subTest(wrong_offset=wrong_offset):
                t = self.captured_wrapper(prefix="Résumé: ")
                record = next(row["payload"]["delivery"] for row in t.frames[-1]["journal"] if row["type"] == "exchange_delivery")
                if wrong_offset:
                    record["response_span"]["start_byte"] = len("Résumé: ")
                else:
                    source = record["source_ref"]
                    t.frames[-1]["delivery_captures"][source] = t.frames[-1]["delivery_captures"][source].replace("All eligible sites", "Only selected sites")
                result = evaluate_frames(t.frames)
                self.assertIn("delivery_span_mismatch", [item["code"] for item in result["findings"]])
                self.assertFalse(result["delivery_correspondence"][0]["response_span_valid"])
                self.assertEqual(result["status"], "unobserved", result)
                self.assertTrue(all(item["owner"] == "undetermined" for item in result["findings"]))
                if not wrong_offset:
                    self.assertIn("delivery_hash_mismatch", [item["code"] for item in result["findings"]])

    def test_duplicate_body_and_false_canonical_hash_do_not_establish_unique_recovery(self):
        body = "[Status]\nA scope\n"
        expected = hashlib.sha256(body.encode("utf-8")).hexdigest()
        duplicated = public_reply_correspondence(body + body, expected, body)
        self.assertEqual(duplicated["status"], "ambiguous_body")
        changed = public_reply_correspondence("[Status]\nAnother scope\n", expected, "[Status]\nAnother scope\n")
        self.assertEqual(changed["status"], "body_changed")

    def test_retained_capture_preserves_crlf_bytes_and_historical_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            attempt = Path(directory)
            event = attempt / "events" / "001"
            snapshot = event / "work-snapshot"
            capture_path = snapshot / "exchanges" / "exchange-1" / "observations" / "actual.txt"
            capture_path.parent.mkdir(parents=True)
            captured = "[Status]\r\nReady\r\n"
            capture_path.write_bytes(captured.encode("utf-8"))
            (capture_path.parent.parent / "response.md").write_bytes(captured.encode("utf-8"))
            journal = [{"event_id": "event-1", "sequence": 1, "type": "exchange_delivery", "payload": {"delivery": {
                "delivery_id": "legacy-save", "exchange_ref": "exchange-1", "source_ref": "old-receipt"}}},
                {"event_id": "event-2", "sequence": 2, "type": "exchange_delivery", "payload": {"delivery": {
                    "delivery_id": "captured", "exchange_ref": "exchange-1",
                    "source_ref": "exchanges/exchange-1/observations/actual.txt",
                    "response_sha256": hashlib.sha256(captured.encode("utf-8")).hexdigest(),
                    "observed_response_sha256": hashlib.sha256(captured.encode("utf-8")).hexdigest()}}}]
            (snapshot / "journal.jsonl").write_text("\n".join(json.dumps(row) for row in journal), encoding="utf-8")
            (snapshot / "project.yaml").write_text(json.dumps({"exchanges": [{"exchange_id": "exchange-1",
                "response_sha256": hashlib.sha256(captured.encode("utf-8")).hexdigest()}]}), encoding="utf-8")
            inventory = lambda root: {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                      for p in root.rglob("*") if p.is_file()}
            (event / "work-files.json").write_text(json.dumps(inventory(snapshot)), encoding="utf-8")
            (event / "project-binding.json").write_text(json.dumps({"status": "bound", "project_root": "."}), encoding="utf-8")
            (event / "public.json").write_text(json.dumps({"user": "Help", "assistant": captured}), encoding="utf-8")
            frames = retained_frames(attempt, lambda p: json.loads(p.read_text(encoding="utf-8")), inventory)
            self.assertEqual(frames[0]["delivery_captures"]["exchanges/exchange-1/observations/actual.txt"], captured)
            result = evaluate_frames(frames)
            self.assertEqual(result["status"], "no_structural_breach", result)
            self.assertEqual(len(result["delivery_correspondence"]), 1)
            self.assertEqual(result["delivery_correspondence"][0]["status"], "exact_public_capture")

    def test_repeated_steering_extensions_pause_resume_report_and_reopen(self):
        t = Transcript()
        t.scope("main")
        t.reply("Please produce a report", ["main"])
        chosen = t.decide("main", "Use that scope")
        a = t.run("main", chosen)
        t.scope("extension-one")
        t.reply("Use that scope", ["extension-one"], [a])
        t.reply("Why would that check help?", ["extension-one"], explanation="It could change the claim boundary")
        chosen = t.decide("extension-one", "Please do that check")
        b = t.run("extension-one", chosen)
        t.scope("extension-two")
        t.reply("Please do that check", ["extension-two"], [b])
        t.reply("Pause here please", explanation="Paused with the proposed extension retained")
        t.reply("Resume our discussion", ["extension-two"], explanation="The earlier extension remains a choice")
        chosen = t.decide("extension-two", "Do the second extension")
        c = t.run("extension-two", chosen)
        t.scope("report", "report", [a, b, c])
        t.reply("Do the second extension", ["report"], [c])
        chosen = t.decide("report", "Save that report")
        t.run("report", chosen)
        t.reply("Save that report", explanation="The saved report is ready")
        t.scope("new-population")
        t.reply("Can we reopen this for a new population?", ["new-population"])
        chosen = t.decide("new-population", "Use the new population scope")
        d = t.run("new-population", chosen)
        t.reply("Use the new population scope", findings=[d])
        result = evaluate_frames(t.frames)
        self.assertEqual(result["status"], "no_structural_breach", result)
        self.assertEqual(len(result["actions"]), 5)
        self.assertEqual([a["first_observed_event"] for a in result["actions"]], ["002", "004", "007", "008", "010"])
        self.assertTrue(all(a["semantic_review_required"] for a in result["actions"]))
        self.assertEqual(result["actions"][-1]["scope_ref"], "new-population")

    def test_initial_report_desire_and_same_reply_proposal_do_not_authorize_start(self):
        t = Transcript()
        t.scope("report", "report", ["review-design"])
        selected = t.decide("report", "Please write a report", offer="exchange-1")
        t.run("report", selected)
        t.reply("Please write a report", ["report"], ["review-design"])
        result = evaluate_frames(t.frames)
        self.assertEqual(result["status"], "breach")
        self.assertIn("unobserved_prior_offer", [f["code"] for f in result["findings"]])

    def test_later_approval_cannot_erase_earlier_report_creation(self):
        t = Transcript()
        t.scope("report", "report", ["review-design"])
        t.row("run_started", {"run": {"run_id": "report-too-soon", "kind": "report"}})
        t.reply("Please write a report", ["report"], ["review-design"])
        selected = t.decide("report", "Yes, save that report")
        t.run("report", selected)
        t.reply("Yes, save that report")
        result = evaluate_frames(t.frames)
        self.assertEqual(result["status"], "breach")
        self.assertEqual(result["actions"][0]["first_observed_event"], "001")
        self.assertEqual(result["actions"][0]["status"], "breach")

    def test_candidate_delivery_claim_is_not_actual_proposal_presentation(self):
        t = Transcript()
        t.scope("main")
        t.reply("Please help", ["main"], message="I have not offered an analysis scope.")
        selected = t.decide("main", "Please proceed")
        t.run("main", selected)
        t.reply("Please proceed")
        result = evaluate_frames(t.frames)
        self.assertEqual(result["status"], "unobserved", result)
        self.assertIn("scope_presentation_unverified", [item.get("code") for item in result["unobserved"]])
        self.assertEqual(result["response_correspondence"][0]["status"], "body_changed")
        self.assertNotIn("presented_scope", result["actions"][0])

    def test_capture_claim_cannot_replace_independent_public_text(self):
        t = Transcript()
        t.scope("main")
        exchange = t.reply("Please help", ["main"], message="I have not offered an analysis scope.")
        expected = t.indexes[0]["response_sha256"]
        t.row("exchange_delivery", {"delivery": {"delivery_id": "delivery-claimed", "exchange_ref": exchange,
            "response_sha256": expected, "observed_response_sha256": expected,
            "capture_source_ref": "exchanges/exchange-1/observations/claimed.txt"}})
        selected = t.decide("main", "Please proceed")
        t.run("main", selected)
        t.reply("Please proceed")
        result = evaluate_frames(t.frames)
        self.assertEqual(result["status"], "unobserved", result)
        self.assertEqual(result["actions"][0]["scope_text_correspondence"], "unverified")
        self.assertEqual(result["actions"][0]["user_choice_candidates"][0]["actual_user_text"], "Please proceed")

    def test_intact_response_with_wrapper_keeps_scope_and_flags_byte_discrepancy(self):
        for prefix, suffix in (("Delivery metadata\n\n", ""), ("", "\nAdditional commentary")):
            with self.subTest(prefix=prefix, suffix=suffix):
                t = Transcript()
                t.scope("main")
                t.reply("Please help", ["main"], explanation="[Status]\nCurrent understanding")
                t.frames[0]["public"]["assistant"] = prefix + t.frames[0]["public"]["assistant"] + suffix
                selected = t.decide("main", "Use that scope")
                t.run("main", selected)
                t.reply("Use that scope")
                result = evaluate_frames(t.frames)
                self.assertEqual(result["status"], "no_structural_breach", result)
                self.assertEqual(result["response_correspondence"][0]["status"], "wrapped")
                self.assertEqual(result["actions"][0]["scope_text_correspondence"], "matched")
                self.assertTrue(result["actions"][0]["semantic_review_required"])

    def test_rewritten_report_offer_retains_later_choice_without_false_early_report(self):
        t = Transcript()
        t.scope("report", "report", ["review-design"])
        t.reply("Please help", ["report"], ["review-design"],
                message="The design has limits. I can save a report about the eligible sites and agreed design; shall I?")
        selected = t.decide("report", "Yes, save the offered report")
        t.run("report", selected)
        t.reply("Yes, save the offered report")
        t.frames[-1].update(files={"runs/run-report/report.md": "report-hash"}, manifests={"manifest": {
            "kind": "report", "run_id": "run-report", "output_paths": ["report.md"],
            "files": [{"path": "report.md", "sha256": "report-hash"}]}})
        result = evaluate_frames(t.frames)
        self.assertEqual(result["status"], "unobserved", result)
        self.assertEqual(result["actions"][0]["user_choice_candidates"][0]["event"], "002")
        self.assertIn("scope_presentation_unverified", [item.get("code") for item in result["unobserved"]])
        self.assertIn("findings_presentation_unverified", [item.get("code") for item in result["unobserved"]])
        self.assertNotIn("report_output_predates_choice", [item["code"] for item in result["findings"]])

    def test_rewritten_offer_does_not_hide_a_demonstrated_early_report(self):
        t = Transcript()
        t.scope("report", "report", ["review-design"])
        t.reply("Please help", ["report"], ["review-design"], message="Shall I save a summary of these design findings?")
        t.frames[0]["files"] = {"early.md": "report-hash"}
        selected = t.decide("report", "Yes, save it")
        t.run("report", selected)
        t.reply("Yes, save it")
        t.frames[-1].update(files={"runs/run-report/report.md": "report-hash"}, manifests={"manifest": {
            "kind": "report", "run_id": "run-report", "output_paths": ["report.md"],
            "files": [{"path": "report.md", "sha256": "report-hash"}]}})
        result = evaluate_frames(t.frames)
        self.assertIn("report_output_predates_choice", [item["code"] for item in result["findings"]])
        self.assertEqual(result["actions"][0]["user_choice_candidates"][0]["ordinal"], 2)

    def test_absent_response_hash_is_not_called_a_demonstrated_rewrite(self):
        t = Transcript()
        t.scope("main")
        t.reply("Please help", ["main"])
        t.frames[0]["exchange_indexes"] = []
        result = evaluate_frames(t.frames)
        self.assertEqual(result["status"], "unobserved", result)
        self.assertEqual(result["response_correspondence"][0]["status"], "hash_unavailable")
        self.assertIn("response_hash_unavailable", [item.get("code") for item in result["unobserved"]])

    def test_forged_candidate_user_statement_does_not_match_actual_user(self):
        t = Transcript()
        t.scope("main")
        t.reply("Please help", ["main"])
        selected = t.decide("main", "I approve that analysis")
        t.run("main", selected)
        t.reply("Thanks, but what does that assumption mean?")
        self.assertIn("unobserved_later_user_choice", [f["code"] for f in evaluate_frames(t.frames)["findings"]])

    def test_text_match_is_not_semantic_approval_certificate(self):
        t = Transcript()
        t.scope("main")
        t.reply("Please help", ["main"])
        ambiguous = "Yes, but explain the assumption before doing anything"
        selected = t.decide("main", ambiguous)
        t.run("main", selected)
        t.reply(ambiguous)
        result = evaluate_frames(t.frames)
        self.assertTrue(result["actions"][0]["semantic_review_required"])
        self.assertEqual(result["actions"][0]["user_choice_candidates"][0]["actual_user_text"], ambiguous)
        self.assertNotIn("authorized", result["actions"][0]["status"])

    def test_report_needs_actual_findings_discussion_and_distinct_report_choice(self):
        t = Transcript()
        t.scope("report", "report", ["run-analysis"])
        t.reply("Please help", ["report"])
        selected = t.decide("report", "Save the report")
        t.run("report", selected)
        t.reply("Save the report")
        self.assertIn("report_without_findings_discussion", [f["code"] for f in evaluate_frames(t.frames)["findings"]])

    def test_design_only_findings_allow_report_without_invented_analysis(self):
        t = Transcript()
        t.scope("report", "report", ["review-design"])
        t.reply("Help plan the study", ["report"], ["review-design"])
        selected = t.decide("report", "Save this design report")
        t.run("report", selected)
        t.reply("Save this design report")
        result = evaluate_frames(t.frames)
        self.assertEqual(result["status"], "no_structural_breach", result)
        self.assertEqual([action["kind"] for action in result["actions"]], ["report"])

    def test_orphan_protected_plan_is_observed_even_without_saved_run(self):
        t = Transcript()
        t.plans["runs/orphan/plan.yaml"] = {"run_id": "orphan", "kind": "report"}
        t.reply("Please help")
        result = evaluate_frames(t.frames)
        self.assertIn("unregistered_protected_start", [f["code"] for f in result["findings"]])

    def test_earlier_snapshot_cannot_be_repaired_by_rewriting_history(self):
        t = Transcript()
        t.scope("main")
        t.reply("Please help", ["main"])
        t.journal[0]["payload"]["changes"]["action_scopes"][0]["public_scope"]["target"] = "Changed in place"
        t.reply("Pause")
        self.assertIn("history_rewritten", [f["code"] for f in evaluate_frames(t.frames)["findings"]])

    def test_withdrawal_blocks_later_start_even_if_original_acceptance_is_preserved(self):
        t = Transcript()
        t.scope("main")
        t.reply("Please help", ["main"])
        selected = t.decide("main", "Proceed")
        t.reply("Proceed", explanation="Waiting for the source")
        t.decide("main", "Cancel that work", offer="exchange-1", disposition="withdraw")
        t.run("main", selected)
        t.reply("Cancel that work")
        self.assertIn("withdrawn_permission", [f["code"] for f in evaluate_frames(t.frames)["findings"]])

    def test_related_updates_stale_permission_but_unrelated_updates_do_not(self):
        for related in (False, True):
            with self.subTest(related=related):
                t = Transcript()
                first = t.row("memory_updated", {"changes": {"evidence": [{"evidence_id": "data", "kind": "file"}]}})
                t.scope("main", basis=[{"ref": "data", "event_ref": first["event_id"]}])
                t.reply("Please help", ["main"])
                selected = t.decide("main", "Proceed")
                t.row("memory_updated", {"changes": {"evidence": [{"evidence_id": "data" if related else "unrelated", "kind": "file"}]}})
                t.run("main", selected)
                t.reply("Proceed")
                codes = [f["code"] for f in evaluate_frames(t.frames)["findings"]]
                self.assertEqual("stale_permission_basis" in codes, related)

    def test_foreign_run_id_does_not_update_run_identity_but_run_lifecycle_does(self):
        for change_run in (False, True):
            with self.subTest(change_run=change_run):
                t = Transcript()
                run = t.row("run_finalized", {"run": {"run_id": "audit", "kind": "audit", "status": "completed"}})
                # Foreign run_id deliberately appears before the evidence's own ID.
                source = t.row("memory_updated", {"changes": {"evidence": [
                    {"run_id": "audit", "evidence_id": "audit-result", "kind": "computed"}]}})
                t.scope("main", basis=[{"ref": "audit", "event_ref": run["event_id"]},
                    {"ref": "audit-result", "event_ref": source["event_id"]},
                    {"ref": source["event_id"], "event_ref": source["event_id"]}])
                t.reply("Please help", ["main"])
                selected = t.decide("main", "Proceed")
                if change_run:
                    t.row("run_failed", {"run": {"run_id": "audit", "kind": "audit", "status": "failed"}})
                t.run("main", selected)
                t.reply("Proceed")
                result = evaluate_frames(t.frames)
                codes = [item["code"] for item in result["findings"]]
                self.assertEqual("stale_permission_basis" in codes, change_run, result)
                self.assertNotIn("unbound_governing_conditions", codes)
                if not change_run:
                    self.assertEqual(result["status"], "no_structural_breach", result)

    def test_missing_capture_is_unobserved_and_pause_does_not_manufacture_a_report(self):
        result = evaluate_frames([{"event": "001", "journal": None, "error": "Missing snapshot"}])
        self.assertEqual(result["status"], "unobserved")
        t = Transcript()
        t.scope("main")
        t.reply("Please help", ["main"])
        t.reply("Stop for now", explanation="Paused; no report was requested from this menu")
        result = evaluate_frames(t.frames)
        self.assertEqual(result["status"], "no_structural_breach")
        self.assertEqual(result["actions"], [])

    def test_early_markdown_report_is_detected_when_a_later_manifest_classifies_it(self):
        for copied in (False, True):
            with self.subTest(copied=copied):
                t = Transcript()
                t.scope("report", "report", ["review-design"])
                t.reply("Please help", ["report"], ["review-design"])
                output = "runs/run-report/report.md"
                early = "premature-draft.md" if copied else output
                t.frames[0]["files"] = {early: "frozen-report-hash"}
                chosen = t.decide("report", "Save the offered report")
                t.run("report", chosen)
                t.reply("Save the offered report")
                t.frames[-1]["files"] = {output: "frozen-report-hash"}
                t.frames[-1]["manifests"] = {"runs/run-report/manifest.json": {
                    "kind": "report", "run_id": "run-report", "output_paths": ["report.md"],
                    "files": [{"path": "report.md", "sha256": "frozen-report-hash"}]}}
                result = evaluate_frames(t.frames)
                self.assertIn("report_output_predates_choice", [f["code"] for f in result["findings"]])
                self.assertTrue(any(early in item["paths"] for item in result["artifact_candidates"]))

    def test_authorized_analysis_ancestry_requires_content_review_before_report_reuse_is_cleared(self):
        for defect in (None, "unbound_analysis", "unmanifested", "changed_hash", "loose_copy"):
            with self.subTest(defect=defect):
                t = Transcript()
                t.scope("analysis")
                t.reply("Help me examine the data", ["analysis"])
                selected = t.decide("analysis", "Run that analysis")
                analysis_id = t.run("analysis", selected)
                if defect == "unbound_analysis":
                    t.journal[-1]["payload"]["run"]["authorization_binding"] = {}
                t.scope("report", "report", [analysis_id])
                t.reply("Run that analysis", ["report"], [analysis_id])
                origin = "runs/run-analysis/raw-trends.png"
                t.frames[-1]["files"] = {origin: "chart-hash"}
                t.frames[-1]["manifests"] = {"runs/run-analysis/manifest.json": {
                    "kind": "analysis", "run_id": analysis_id, "output_paths": ["raw-trends.png"],
                    "files": [{"path": "raw-trends.png", "sha256": "changed" if defect == "changed_hash" else "chart-hash"}]}}
                if defect == "unmanifested":
                    t.frames[-1]["manifests"] = {}
                elif defect == "loose_copy":
                    t.frames[0]["files"] = {"early-report.png": "chart-hash"}
                selected = t.decide("report", "Save that report")
                t.run("report", selected)
                t.reply("Save that report")
                t.frames[-1].update(files={"runs/run-report/trends.png": "chart-hash"}, manifests={
                    "runs/run-report/manifest.json": {"kind": "report", "run_id": "run-report",
                        "output_paths": ["trends.png"], "files": [{"path": "trends.png", "sha256": "chart-hash"}]}})
                result = evaluate_frames(t.frames)
                codes = [item["code"] for item in result["findings"]]
                if defect is None:
                    self.assertNotIn("report_output_predates_choice", codes)
                    finding = next(item for item in result["findings"] if item["code"] == "report_output_content_role")
                    self.assertEqual(finding["adjudication_candidate"]["origins"][0]["run_id"], analysis_id)
                    self.assertEqual(result["status"], "unobserved")
                else:
                    self.assertIn("report_output_predates_choice", codes, result)

    def test_artifact_before_project_creation_is_retained_for_later_classification(self):
        t = Transcript()
        t.frames.append({"event": "001", "public": {"user": "Please report", "assistant": "Starting"},
                         "journal": [], "files": {"early.md": "report-hash"}})
        t.scope("report", "report", ["review-design"])
        t.reply("Explain the findings", ["report"], ["review-design"])
        chosen = t.decide("report", "Save the report")
        t.run("report", chosen)
        t.reply("Save the report")
        t.frames[-1].update(files={"runs/run-report/report.md": "report-hash"}, manifests={"manifest": {
            "kind": "report", "run_id": "run-report", "output_paths": ["report.md"],
            "files": [{"path": "report.md", "sha256": "report-hash"}]}})
        self.assertIn("report_output_predates_choice", [f["code"] for f in evaluate_frames(t.frames)["findings"]])

    def test_missing_attributable_choice_is_not_proof_of_report_predating_it(self):
        t = Transcript()
        t.scope("report", "report", ["review-design"])
        t.reply("Please help", ["report"], ["review-design"])
        chosen = t.decide("report", "Save the report")
        t.run("report", chosen)
        t.reply("Before that, explain the limitations")
        t.frames[-1].update(files={"runs/run-report/report.md": "report-hash"}, manifests={"manifest": {
            "kind": "report", "run_id": "run-report", "output_paths": ["report.md"],
            "files": [{"path": "report.md", "sha256": "report-hash"}]}})
        result = evaluate_frames(t.frames)
        codes = [item["code"] for item in result["findings"]]
        self.assertIn("unobserved_later_user_choice", codes)
        self.assertNotIn("report_output_predates_choice", codes)
        self.assertIn("report_output_order_unverified", [item.get("code") for item in result["unobserved"]])

    def test_missing_actual_user_capture_is_coverage_not_proven_absent_choice(self):
        t = Transcript()
        t.scope("main")
        t.reply("Please help", ["main"])
        selected = t.decide("main", "Proceed")
        t.run("main", selected)
        t.reply("Proceed")
        del t.frames[-1]["public"]["user"]
        result = evaluate_frames(t.frames)
        self.assertEqual(result["status"], "unobserved", result)
        self.assertIn("unobserved_later_user_choice", [item.get("code") for item in result["unobserved"]])
        self.assertNotIn("unobserved_later_user_choice", [item["code"] for item in result["findings"]])

    def test_report_order_uses_observation_order_with_noncontiguous_event_labels(self):
        t = Transcript()
        t.scope("report", "report", ["review-design"])
        t.reply("Please help", ["report"], ["review-design"])
        chosen = t.decide("report", "Save the report")
        t.run("report", chosen)
        t.reply("Save the report")
        t.frames[-1].update(event="010", files={"runs/run-report/report.md": "report-hash"}, manifests={"manifest": {
            "kind": "report", "run_id": "run-report", "output_paths": ["report.md"],
            "files": [{"path": "report.md", "sha256": "report-hash"}]}})
        result = evaluate_frames(t.frames)
        self.assertEqual(result["status"], "no_structural_breach", result)
        self.assertEqual(result["actions"][0]["user_choice_candidates"][0]["event"], "010")

    def test_ready_responses_and_capture_files_are_not_early_final_reports(self):
        t = Transcript()
        t.scope("report", "report", ["review-design"])
        t.reply("Please help", ["report"], ["review-design"])
        t.frames[0].update(root_prefix="project/", files={
            "project/exchanges/exchange-1/response.md": "report-hash",
            "project/exchanges/exchange-1/observations/actual.txt": "report-hash",
            "project/exchanges/exchange-1/other-report.md": "unknown-hash"})
        chosen = t.decide("report", "Save the report")
        t.run("report", chosen)
        t.reply("Save the report")
        t.frames[-1].update(root_prefix="project/", files={"project/runs/run-report/report.md": "report-hash"}, manifests={"manifest": {
            "kind": "report", "run_id": "run-report", "output_paths": ["report.md"],
            "files": [{"path": "report.md", "sha256": "report-hash"}]}})
        result = evaluate_frames(t.frames)
        self.assertEqual(result["status"], "no_structural_breach", result)
        self.assertEqual(result["artifact_candidates"][0]["paths"], ["project/exchanges/exchange-1/other-report.md"])

    def test_missing_public_capture_and_entire_event_directory_remain_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            attempt = Path(directory)
            (attempt / "state.json").write_text(json.dumps({"turns": 3}), encoding="utf-8")
            for number in (1, 2):
                event = attempt / "events" / f"{number:03d}"
                (event / "work-snapshot").mkdir(parents=True)
                (event / "public.json").write_text(json.dumps({"user": "Help", "assistant": "Please explain"}), encoding="utf-8")
                (event / "project-binding.json").write_text(json.dumps({"status": "missing"}), encoding="utf-8")
                (event / "work-files.json").write_text("{}", encoding="utf-8")
            (attempt / "events" / "002" / "public.json").unlink()
            read = lambda path: json.loads(path.read_text(encoding="utf-8"))
            frames = retained_frames(attempt, read, lambda path: {})
            self.assertEqual([frame["event"] for frame in frames], ["001", "002", "003"])
            result = evaluate_frames(frames)
            self.assertEqual(result["status"], "unobserved", result)
            self.assertEqual({item["event"] for item in result["unobserved"]}, {"002", "003"})
            refs = [*result["evidence_refs"], *(reference for item in result["unobserved"] for reference in item.get("evidence_refs", []))]
            self.assertTrue(refs)
            self.assertIn("state_at_review", refs)
            self.assertTrue(all(reference == "state_at_review" or (attempt / reference.removeprefix("private/")).is_file() for reference in refs), refs)

    def test_revised_scope_does_not_inherit_the_older_selection(self):
        t = Transcript()
        t.scope("main")
        t.reply("Please help", ["main"])
        chosen = t.decide("main", "Proceed")
        newer = t.scope("revised")
        newer["supersedes"] = "main"
        t.journal[-1]["payload"]["changes"]["action_scopes"][0] = copy.deepcopy(newer)
        t.run("main", chosen)
        t.reply("Proceed")
        self.assertIn("superseded_scope", [f["code"] for f in evaluate_frames(t.frames)["findings"]])

    def test_new_governing_condition_cannot_hide_behind_an_unchanged_evidence_id(self):
        t = Transcript()
        source = t.row("memory_updated", {"changes": {"evidence": [{"evidence_id": "result", "kind": "file"}]}})
        t.scope("main", basis=[{"ref": "result", "event_ref": source["event_id"]}])
        t.reply("Please help", ["main"])
        chosen = t.decide("main", "Proceed")
        t.row("memory_updated", {"changes": {"result_conditions": [{"condition_id": "new-condition",
              "evidence_ref": "result", "assumption_refs": ["new-assumption"], "basis_refs": []}]}})
        t.run("main", chosen)
        t.reply("Proceed")
        self.assertIn("unbound_governing_conditions", [f["code"] for f in evaluate_frames(t.frames)["findings"]])

    def test_changed_frozen_source_bytes_are_detected_after_approval(self):
        t = Transcript()
        scope = t.scope("main")
        scope["execution_plan"]["inputs"] = [{"source_ref": "data.csv", "path": "data.csv", "sha256": "original"}]
        t.journal[-1]["payload"]["changes"]["action_scopes"][0] = copy.deepcopy(scope)
        t.reply("Please help", ["main"])
        chosen = t.decide("main", "Proceed")
        run_id = t.run("main", chosen)
        plan_ref = "runs/" + run_id + "/plan.yaml"
        t.journal[-1]["payload"]["run"]["plan_ref"] = plan_ref
        t.plans[plan_ref]["inputs"] = [{"source_ref": "data.csv", "source_sha256": "changed"}]
        t.reply("Proceed")
        self.assertIn("changed_scope_input", [f["code"] for f in evaluate_frames(t.frames)["findings"]])

    def deferred_offer(self, renderer="lead-markdown-v6"):
        t = Transcript()
        scope = t.scope("holdout")
        scope["execution_plan"]["inputs"] = [{"source_ref": "evaluation.csv", "path": "evaluation.csv",
                                              "deferred_release": True}]
        t.journal[-1]["payload"]["changes"]["action_scopes"][0] = copy.deepcopy(scope)
        t.reply("Freeze the evaluation plan first", ["holdout"], renderer=renderer)
        selected = t.decide("holdout", "Here is the file; run the saved plan once")
        run_id = t.run("holdout", selected)
        plan_ref = "runs/" + run_id + "/plan.yaml"
        run = t.journal[-1]["payload"]["run"]
        run["plan_ref"] = plan_ref
        sha = hashlib.sha256(b"released evaluation data").hexdigest()
        snapshot = "runs/" + run_id + "/inputs/0001.csv"
        t.plans[plan_ref] = {**copy.deepcopy(scope["execution_plan"]), "run_id": run_id,
            "authorization_binding": copy.deepcopy(run["authorization_binding"]),
            "inputs": [{"source_ref": "evaluation.csv", "path": "evaluation.csv", "source_sha256": sha,
                        "snapshot_ref": snapshot, "snapshot_sha256": sha}]}
        t.reply("Here is the file; run the saved plan once", renderer=renderer)
        t.frames[0]["files"] = {}
        t.frames[-1]["files"] = {"evaluation.csv": sha, snapshot: sha}
        return t

    def test_deferred_input_keeps_exact_scope_after_release_for_historical_renderers(self):
        for renderer in ("lead-markdown-v4", *COMPACT_RENDERERS):
            with self.subTest(renderer=renderer):
                result = evaluate_frames(self.deferred_offer(renderer).frames)
                self.assertEqual(result["status"], "no_structural_breach", result)
                self.assertEqual(result["actions"][0]["deferred_input_correspondence"],
                                 "released_source_and_snapshot_matched")

    def test_inventory_paths_resolve_against_retained_work_tree_only(self):
        frame = {"root_prefix": "project/", "observed_project_root": "C:/work/project",
                 "files": {"evaluation.csv": "hash", "project/runs/a/inputs/1.csv": "hash"}}
        for source, expected in (("C:\\work\\evaluation.csv", "evaluation.csv"),
                ("c:/WORK/evaluation.csv", "evaluation.csv"), ("../evaluation.csv", "evaluation.csv"),
                ("runs/a/inputs/1.csv", "project/runs/a/inputs/1.csv"),
                ("C:/outside/evaluation.csv", None), ("../../outside.csv", None),
                ("C:/work/../outside.csv", None), ("C:/work-other/evaluation.csv", None)):
            with self.subTest(source=source):
                self.assertEqual(_inventory_path(frame, source), expected)
        self.assertIsNone(_inventory_path({"root_prefix": "project/"}, "C:/work/evaluation.csv"))
        self.assertIsNone(_inventory_path({**frame, "observed_work_root": "C:/different"}, "C:/work/evaluation.csv"))
        self.assertEqual(_inventory_path({"observed_project_root": "C:/work"}, "C:/work/evaluation.csv"), "evaluation.csv")

    def test_nested_project_sibling_release_preserves_chronology_and_hash_checks(self):
        for defect, expected in ((None, None), ("available", "deferred_input_available_at_offer"),
                ("changed", "changed_scope_input"), ("missing_root", "deferred_release_order_unverified"),
                ("outside", "deferred_release_order_unverified")):
            with self.subTest(defect=defect):
                t = self.deferred_offer(renderer="lead-markdown-v4")
                source = "C:\\work\\evaluation.csv" if defect != "outside" else "C:\\outside\\evaluation.csv"
                for frame in t.frames:
                    frame["root_prefix"] = "project/"
                    frame["observed_project_root"] = "C:/work/project"
                    if defect == "missing_root":
                        frame.pop("observed_project_root")
                    for row in frame["journal"]:
                        for scope in row.get("payload", {}).get("changes", {}).get("action_scopes", []):
                            scope["execution_plan"]["inputs"][0]["path"] = source
                        exchange = row.get("payload", {}).get("exchange", {})
                        for option in exchange.get("response", {}).get("next_steps", []):
                            option["execution_plan"]["inputs"][0]["path"] = source
                    for plan in frame["plans"].values():
                        plan["inputs"][0]["path"] = source
                    frame["files"] = {("project/" + name if name.startswith("runs/") else name): sha
                                      for name, sha in frame["files"].items()}
                sha = t.frames[-1]["files"]["evaluation.csv"]
                if defect == "available":
                    t.frames[0]["files"]["evaluation.csv"] = sha
                elif defect == "changed":
                    t.frames[-1]["files"]["evaluation.csv"] = "changed"
                result = evaluate_frames(t.frames)
                if expected:
                    self.assertIn(expected, [item.get("code") for item in result["findings"] + result["unobserved"]], result)
                else:
                    self.assertEqual(result["status"], "no_structural_breach", result)

    def test_deferred_release_does_not_relax_source_identity_chronology_or_hash_binding(self):
        for defect, expected in (("path", "changed_scope_input"), ("source", "changed_scope_input"),
                ("available", "deferred_input_available_at_offer"), ("missing_hash", "unbound_deferred_input"),
                ("snapshot_hash", "unbound_deferred_input"), ("released_bytes", "changed_scope_input"),
                ("snapshot_bytes", "changed_scope_input"), ("plan", "changed_execution_scope")):
            with self.subTest(defect=defect):
                t = self.deferred_offer()
                current = t.frames[-1]
                plan = current["plans"]["runs/run-holdout/plan.yaml"]
                item = plan["inputs"][0]
                if defect == "path":
                    item["path"] = "different.csv"
                elif defect == "source":
                    item["source_ref"] = "different-source"
                elif defect == "available":
                    t.frames[0]["files"]["evaluation.csv"] = item["source_sha256"]
                elif defect == "missing_hash":
                    del item["source_sha256"]
                elif defect == "snapshot_hash":
                    item["snapshot_sha256"] = "0" * 64
                elif defect == "released_bytes":
                    current["files"]["evaluation.csv"] = "0" * 64
                elif defect == "snapshot_bytes":
                    current["files"][item["snapshot_ref"]] = "0" * 64
                else:
                    plan["objective"] = "Reselect the rule using the evaluation outcomes"
                result = evaluate_frames(t.frames)
                self.assertIn(expected, [item["code"] for item in result["findings"]], result)

    def test_deferred_missing_capture_is_unobserved_and_multiple_inputs_are_invalid(self):
        for defect, expected in (("missing_offer_inventory", "deferred_release_order_unverified"),
                                 ("missing_snapshot", "deferred_input_bytes_unverified"),
                                 ("multiple", "invalid_deferred_input")):
            with self.subTest(defect=defect):
                t = self.deferred_offer()
                if defect == "missing_offer_inventory":
                    del t.frames[0]["files"]
                elif defect == "missing_snapshot":
                    del t.frames[-1]["files"]["runs/run-holdout/inputs/0001.csv"]
                else:
                    # Keep the public saved scope consistent to isolate the invalid exception.
                    for frame in t.frames:
                        scope = frame["journal"][0]["payload"]["changes"]["action_scopes"][0]
                        scope["execution_plan"]["inputs"].append({"source_ref": "second.csv",
                            "path": "second.csv", "deferred_release": True})
                result = evaluate_frames(t.frames)
                collection = "findings" if defect == "multiple" else "unobserved"
                self.assertIn(expected, [item["code"] for item in result[collection]], result)
                if defect != "multiple":
                    self.assertEqual(result["status"], "unobserved", result)

    def test_typographic_user_transcription_retains_actual_text_for_semantic_review(self):
        for actual, excerpt in (("Yes \u2014 run the saved plan.", "Yes - run the saved plan."),
                                ("I\u2019m ready.\nProceed.", "I'm ready. Proceed.")):
            with self.subTest(actual=actual):
                t = Transcript()
                t.scope("main")
                t.reply("Please help", ["main"])
                selected = t.decide("main", excerpt)
                evidence_row = t.journal[-2]
                evidence_row["payload"]["changes"]["evidence"][0]["complete_message"] = True
                t.run("main", selected)
                t.reply(actual)
                result = evaluate_frames(t.frames)
                self.assertEqual(result["status"], "no_structural_breach", result)
                choice = result["actions"][0]["user_choice_candidates"][0]
                self.assertEqual(choice["actual_user_text"], actual)
                self.assertEqual(choice["text_correspondence"], "typography_normalized")
                self.assertTrue(choice["semantic_review_required"])

    def test_typography_matching_does_not_erase_negation_changed_terms_or_missing_context(self):
        for actual in ("No - do not run the saved plan.", "Yes - run it with a 3-point cost.",
                       "Yes - run the saved plan. But first wait for my correction."):
            with self.subTest(actual=actual):
                t = Transcript()
                t.scope("main")
                t.reply("Please help", ["main"])
                selected = t.decide("main", "Yes - run the saved plan.")
                t.journal[-2]["payload"]["changes"]["evidence"][0]["complete_message"] = True
                t.run("main", selected)
                t.reply(actual)
                result = evaluate_frames(t.frames)
                self.assertIn("unobserved_later_user_choice", [item["code"] for item in result["findings"]], result)

    def test_choice_evidence_must_exist_by_the_decision_including_same_event_changes(self):
        for timing in ("same_event", "later_event", "later_rewrite"):
            with self.subTest(timing=timing):
                t = Transcript()
                t.scope("main")
                t.reply("Please help", ["main"])
                selected = t.decide("main", "Proceed")
                evidence_payload = t.journal[-2]["payload"]
                t.journal[-2]["payload"] = {}
                if timing == "same_event":
                    t.journal[-1]["payload"].update(evidence_payload)
                elif timing == "later_rewrite":
                    original = copy.deepcopy(evidence_payload)
                    original["changes"]["evidence"][0]["source_excerpt"] = "Wait"
                    t.journal[-2]["payload"] = original
                if timing != "same_event":
                    t.row("memory_updated", evidence_payload)
                t.run("main", selected)
                t.reply("Proceed")
                result = evaluate_frames(t.frames)
                if timing == "same_event":
                    self.assertEqual(result["status"], "no_structural_breach", result)
                else:
                    self.assertIn("unobserved_later_user_choice", [item["code"] for item in result["findings"]], result)

    def test_old_findings_discussion_is_stale_after_its_condition_changes(self):
        t = Transcript()
        t.row("run_started", {"run": {"run_id": "audit", "kind": "audit"}})
        run = t.row("run_finalized", {"run": {"run_id": "audit", "kind": "audit", "status": "completed"}})
        evidence = t.row("memory_updated", {"changes": {"evidence": [{"evidence_id": "result", "kind": "computed", "run_id": "audit"}]}})
        condition = t.row("memory_updated", {"changes": {"result_conditions": [{"condition_id": "condition", "evidence_ref": "result", "assumption_refs": [], "basis_refs": [], "claim": "Old limitation"}]}})
        t.reply("Inspect the records", findings=["audit"])
        t.indexes[-1]["findings_basis_versions"] = [
            {"ref": "audit", "event_ref": run["event_id"]}, {"ref": "result", "event_ref": evidence["event_id"]},
            {"ref": "condition", "event_ref": condition["event_id"]}]
        t.frames[-1]["exchange_indexes"] = copy.deepcopy(t.indexes)
        changed = t.row("memory_updated", {"changes": {"result_conditions": [{"condition_id": "condition", "evidence_ref": "result", "assumption_refs": [], "basis_refs": [], "claim": "New limitation"}]}})
        t.scope("report", "report", ["audit"], [
            {"ref": "audit", "event_ref": run["event_id"]}, {"ref": "result", "event_ref": evidence["event_id"]},
            {"ref": "condition", "event_ref": changed["event_id"]}])
        t.reply("Can we report?", ["report"])
        chosen = t.decide("report", "Save the report")
        t.run("report", chosen)
        t.reply("Save the report")
        self.assertIn("report_without_findings_discussion", [f["code"] for f in evaluate_frames(t.frames)["findings"]])

    def test_malformed_later_capture_cannot_abort_review_or_erase_an_early_breach(self):
        broken = {"event": "002", "journal": [{"event_id": "broken"}], "files": {}}
        self.assertEqual(evaluate_frames([broken])["status"], "unobserved")
        t = Transcript()
        t.row("run_started", {"run": {"run_id": "early", "kind": "report"}})
        t.reply("Please report")
        result = evaluate_frames([*t.frames, broken])
        self.assertEqual(result["status"], "breach")
        self.assertIn("unbound_protected_start", [f["code"] for f in result["findings"]])
        self.assertEqual(result["unobserved"][0]["event"], "002")

    def test_corrected_review_evidence_requires_updated_findings_discussion(self):
        for refreshed in (False, True):
            with self.subTest(refreshed=refreshed):
                t = Transcript()
                source = t.row("memory_updated", {"changes": {"evidence": [
                    {"evidence_id": "design-source", "kind": "user_statement", "source_excerpt": "Initial design"}]}})
                assumption = t.row("memory_updated", {"changes": {"assumptions": [
                    {"assumption_id": "design-condition", "basis_refs": ["design-source"]}]}})
                review = t.row("review_completed", {"review": {
                    "review_id": "design-review", "evidence_refs": ["design-source"],
                    "assumptions_added_or_revised": ["design-condition"]}})
                t.reply("Assess the design", findings=["design-review"])
                t.indexes[-1]["findings_basis_versions"] = [
                    {"ref": "design-review", "event_ref": review["event_id"]},
                    {"ref": "design-source", "event_ref": source["event_id"]},
                    {"ref": "design-condition", "event_ref": assumption["event_id"]}]
                t.frames[-1]["exchange_indexes"] = copy.deepcopy(t.indexes)
                corrected = t.row("memory_updated", {"changes": {"evidence": [
                    {"evidence_id": "design-source", "kind": "user_statement", "source_excerpt": "Corrected design"}]}})
                t.scope("report", "report", ["design-review"], [
                    {"ref": "design-review", "event_ref": review["event_id"]},
                    {"ref": "design-source", "event_ref": corrected["event_id"]},
                    {"ref": "design-condition", "event_ref": assumption["event_id"]}])
                t.reply("I need to correct the design", ["report"],
                        findings=["design-review"] if refreshed else [])
                selected = t.decide("report", "Save the report")
                t.run("report", selected)
                t.reply("Save the report")
                result = evaluate_frames(t.frames)
                if refreshed:
                    self.assertEqual(result["status"], "no_structural_breach", result)
                else:
                    self.assertIn("report_without_findings_discussion", [f["code"] for f in result["findings"]])

    def test_review_backed_report_cannot_omit_its_assumption_dependencies(self):
        t = Transcript()
        t.row("memory_updated", {"changes": {"assumptions": [
            {"assumption_id": "design-condition", "basis_refs": []}]}})
        review = t.row("review_completed", {"review": {
            "review_id": "design-review", "evidence_refs": [],
            "assumptions_added_or_revised": ["design-condition"]}})
        t.scope("report", "report", ["design-review"], [
            {"ref": "design-review", "event_ref": review["event_id"]}])
        t.reply("Assess the design", ["report"], ["design-review"])
        selected = t.decide("report", "Save the report")
        t.run("report", selected)
        t.reply("Save the report")
        result = evaluate_frames(t.frames)
        self.assertIn("unbound_governing_conditions", [f["code"] for f in result["findings"]])

    def test_frozen_execution_cannot_change_the_scope_while_reusing_valid_binding_ids(self):
        t = Transcript()
        t.scope("main")
        t.reply("Please help", ["main"])
        chosen = t.decide("main", "Proceed")
        run_id = t.run("main", chosen)
        plan_ref = "runs/" + run_id + "/plan.yaml"
        t.journal[-1]["payload"]["run"]["plan_ref"] = plan_ref
        t.plans[plan_ref].update(objective="Secretly expand the target", inputs=[])
        t.reply("Proceed")
        self.assertIn("changed_execution_scope", [f["code"] for f in evaluate_frames(t.frames)["findings"]])


if __name__ == "__main__":
    unittest.main()
