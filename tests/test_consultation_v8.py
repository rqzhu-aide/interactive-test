"""Independent v8 observer evidence; no live candidate or v7 fixture writer.

The fixture models retained public turns and journal snapshots, not a real host
or scientific analysis. Adversarial variants change evidence, never its parser.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import session_driver as driver
from consultation_observer import evaluate_frames


FORMAT = "consultation-journal-v8"
STAMP = "2026-10-06T12:00:00Z"
REQUEST = "Please propose an analysis of the randomized site policy."
ACCEPT = "Yes, carry out N1 with the stated limits."
OPTION = ("Estimate the site policy effect using the randomized panel; compare "
          "assigned groups, check balance, and save estimates with uncertainty. "
          "The claim is limited to these sites. Full saved scope.")
OFFER = "[Next steps]\n\n[N1] " + OPTION
PUBLIC_INPUT = b"site,assigned,outcome\n1,0,4\n2,1,6\n"


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha(value):
    return hashlib.sha256(value).hexdigest()


class V8Evidence:
    """A scope in turn 1, then actual recording, acceptance and work in turn 2."""

    def __init__(self, public_offer=OFFER, recorded_option=OPTION, early_output=False, recorded_label="N1"):
        self.journal = [{"format": FORMAT, "case": "case-observer-fixture",
                         "created_at": STAMP, "_meta": {"request_hash": sha(b"initialize")}}]
        self.journal[0]["_meta"]["integrity_hash"] = sha(encoded(self.journal[0]))
        self.frames, self.plans, self.response_bodies, self.manifests = [], {}, {}, {}
        self.files = {"panel.csv": sha(PUBLIC_INPUT)}
        self.add("user_message", {"text": REQUEST, "complete": True,
                                  "source": "conversation:user-1"})
        self.add("knowledge", {"user_message": "e1", "updates": [
            {"entity": "f1", "kind": "evidence", "evidence_kind": "file",
             "source_ref": "panel.csv", "source_sha256": sha(PUBLIC_INPUT),
             "summary": "Synthetic randomized-site panel for observer checks."},
            {"entity": "d1", "kind": "scientific_decision", "decision_kind": "target",
             "statement": "Estimate the site policy effect.", "status": "current",
             "user_contribution_refs": ["e1"]}],
            "next_action": {"kind": "lead_only", "reason": "Offer the requested analysis."}})
        self.assignment = {"specialist_id": "design_worker", "operation": "execution",
                           "design_id": "randomized_assignment"}
        self.terms = {"target": "Estimate the site policy effect.", "population": "These sites",
                      "evidence": "Randomized site panel", "approach": "Compare assigned groups",
                      "checks": ["Check balance"], "outputs": "Estimates with uncertainty",
                      "claim_boundary": "The claim is limited to these sites."}
        self.execution = {"inputs": [{"source_ref": "panel.csv", "path": "panel.csv",
                                      "sha256": sha(PUBLIC_INPUT)}],
                          "treatment": "Assigned policy", "comparator": "Assigned control",
                          "outcome": "Outcome score", "timing": "After assignment",
                          "estimand": "Average assignment effect", "design_id": "randomized_assignment",
                          "exclusions": []}
        self.basis = [{"ref": "f1", "event_ref": "e2"}, {"ref": "d1", "event_ref": "e2"},
                      {"ref": "e1", "event_ref": "e1"}]
        self.add("scope", {"action": "analysis", "terms": self.terms, "execution": self.execution,
                           "assignment": self.assignment, "basis_versions": self.basis})
        self.add("reply_prepared", {"responds_to": "e2", "renderer": "lead-markdown-v11",
            "response": {"user_questions": [], "explanations": [], "questions": [], "next_steps": [
                {"option_id": "estimate", "kind": "action", "actor": "consultant",
                 "label": "Estimate the effect", "scope": "Use the proposed analysis.",
                 "scope_ref": "e3"}]}})
        self.response_bodies["e4"] = OFFER
        self.files["replies/e4.md"] = sha(OFFER.encode("utf-8"))
        if early_output:
            self.files["runs/e8/outputs/early.csv"] = sha(b"estimate\n2\n")
        self.snapshot(REQUEST, public_offer)

        self.add("user_message", {"text": ACCEPT, "complete": True,
                                  "source": "conversation:user-2"})
        self.add("reply_recorded", {"prepared": "e4", "before_user": "e5",
            "source": {"kind": "assistant_recorded", "locator": "conversation:assistant-1"},
            "items": [{"kind": "option", "label": recorded_label, "text": recorded_option, "scope_ref": "e3"}]})
        self.add("decision", {"user_message": "e5", "actual_reply": "e6", "item": recorded_label,
            "scope": "e3", "choice": "accept", "next_action": {"kind": "specialist",
                "scope": "e3", "decision": "e7", "assignment": self.assignment,
                "reason": "Execute the selected analysis."}})
        authored = {**copy.deepcopy(self.execution), "kind": "analysis", "objective": self.terms["target"],
                    "claim_boundary": self.terms["claim_boundary"], "target": self.terms["target"],
                    "population": self.terms["population"], "estimator": self.terms["approach"],
                    "diagnostics": self.terms["checks"]}
        input_record = {"source_ref": "panel.csv", "path": "panel.csv",
                        "source_path": "C:/observer-fixture/panel.csv", "source_sha256": sha(PUBLIC_INPUT),
                        "bytes": len(PUBLIC_INPUT), "snapshot_ref": "runs/e8/inputs/0001.csv",
                        "snapshot_sha256": sha(PUBLIC_INPUT)}
        plan = {**copy.deepcopy(authored), "plan_schema_version": 8, "run_id": "e8",
                "responds_to": "e7", "frozen_at": STAMP, "authored_plan": authored,
                "inputs": [input_record], "evidence_bindings": [], "scope": "e3",
                "decision": "e7", "basis_versions": self.basis}
        plan_ref = "runs/e8/plan.yaml"
        self.plans[plan_ref] = plan
        self.files[plan_ref] = sha(encoded(plan))
        self.files[input_record["snapshot_ref"]] = sha(PUBLIC_INPUT)
        self.add("work", {"phase": "started", "run": "e8", "kind": "analysis", "responds_to": "e7",
                          "scope": "e3", "decision": "e7", "plan_ref": plan_ref,
                          "plan_sha256": self.files[plan_ref], "started_at": STAMP,
                          "claim_boundary": self.terms["claim_boundary"]})
        self.snapshot(ACCEPT, "[To answer your question]\n\n[A1] The selected analysis has started.")

    def add(self, kind, data):
        ref = "e" + str(len(self.journal))
        row = {"id": ref, "recorded_at": STAMP, "type": kind, "data": copy.deepcopy(data),
               "_meta": {"request_hash": sha(encoded({"fixture_entry": ref, "op": kind, "data": data})),
                         "previous_hash": self.journal[-1]["_meta"]["integrity_hash"]}}
        row["_meta"]["integrity_hash"] = sha(encoded(row))
        self.journal.append(row)
        return ref

    def snapshot(self, user, assistant):
        event = f"{len(self.frames) + 1:03d}"
        files = {**self.files, "journal.jsonl": sha(b"\n".join(encoded(row) for row in self.journal) + b"\n")}
        self.frames.append(copy.deepcopy({"event": event, "public": {"user": user, "assistant": assistant},
            "journal": self.journal, "journal_format": FORMAT, "plans": self.plans, "manifests": self.manifests, "files": files,
            "response_bodies": self.response_bodies, "public_paths": ["panel.csv"], "root_prefix": "",
            "observed_work_root": "C:/observer-fixture", "observed_project_root": "C:/observer-fixture",
            "evidence_refs": ["private/events/" + event + "/public.json",
                              "private/events/" + event + "/work-snapshot/journal.jsonl"]}))

    def through_report_start(self, discussion="completed", later_review=False):
        """Resume an existing run, then offer/accept a report on its findings.

        The progress-only variant deliberately omits completed findings from
        public discussion. Raw-ID observation must not certify that discussion.
        """
        resume = "Continue the accepted analysis and explain its findings."
        self.resume_user = self.add("user_message", {"text": resume, "complete": True,
                                                      "source": "conversation:user-3"})
        progress = "The selected analysis has started."
        self.add("reply_recorded", {"before_user": self.resume_user,
            "source": {"kind": "assistant_recorded", "locator": "conversation:assistant-2"},
            "items": [{"kind": "findings" if discussion == "progress" else "explanation",
                       "label": "A1", "text": progress,
                       **({"work_refs": ["e8"]} if discussion == "progress" else {})}]})
        self.resume_handling = self.add("knowledge", {"user_message": self.resume_user,
            "next_action": {"kind": "specialist", "scope": "e3", "decision": "e7",
                            "assignment": self.assignment, "reason": "Resume the existing run."}})
        manifest_ref = "runs/e8/manifest.json"
        output = b"estimate\n2\n"
        self.files["runs/e8/outputs/estimate.csv"] = sha(output)
        self.manifests[manifest_ref] = {"run_id": "e8", "responds_to": "e7", "scope": "e3", "decision": "e7",
            "plan_ref": "runs/e8/plan.yaml", "plan_sha256": self.files["runs/e8/plan.yaml"],
            "files": [{"path": "outputs/estimate.csv", "sha256": sha(output), "bytes": len(output)}]}
        self.files[manifest_ref] = sha(encoded(self.manifests[manifest_ref]))
        self.completion = self.add("work", {"phase": "completed", "run": "e8", "kind": "analysis", "responds_to": "e7",
            "manifest_ref": manifest_ref, "manifest_sha256": self.files[manifest_ref]})
        self.completed_review = self.add("review", {"responds_to": self.resume_handling,
            "assignment": self.assignment, "summary": "Completed assignment comparison.",
            "question_addressed": "What did the assigned-group comparison show?",
            "work_performed": ["Compared assigned groups."],
            "findings": ["The estimate is 2 outcome units for these sites; precision is limited."],
            "work_refs": ["e8"]})
        finding = {"kind": "findings", "label": "A1",
                   "text": "The estimate is 2 outcome units for these sites; precision is limited.",
                   "work_refs": [self.completed_review if discussion == "review" else "e8"]}
        prepared_findings = {"summary": finding["text"], "diagnostics": [],
                             "limitations": [], "work_refs": finding["work_refs"]}
        items = [] if discussion == "progress" else [finding]
        handling, public_user = self.resume_handling, resume
        governing_ref = "e8"
        if later_review:
            self.first_closeout = self.add("reply_prepared", {"responds_to": handling,
                "renderer": "lead-markdown-v11", "response": {"user_questions": [],
                    "explanations": [], "questions": [], "next_steps": [], "findings": prepared_findings}})
            self.snapshot(resume, "[To answer your question]\n\n[A1] " + finding["text"])
            public_user = "Assess whether the uncertainty changes the claim before offering a report."
            user = self.add("user_message", {"text": public_user, "complete": True,
                                              "source": "conversation:user-4"})
            self.add("reply_recorded", {"prepared": self.first_closeout, "before_user": user,
                "source": {"kind": "assistant_recorded", "locator": "conversation:assistant-3"}, "items": items})
            assessment = {"specialist_id": "domain_expert", "operation": "review"}
            handling = self.add("knowledge", {"user_message": user, "next_action": {
                "kind": "specialist", "assignment": assessment, "reason": "Assess the requested qualification."}})
            self.later_review = self.add("review", {"responds_to": handling, "assignment": assessment,
                "summary": "A distinct assessment of uncertainty.", "question_addressed": public_user,
                "work_performed": ["Examined the uncertainty qualification."],
                "findings": ["The uncertainty prevents a directional policy recommendation."], "work_refs": ["e8"]})
            governing_ref, items = self.later_review, []  # Deliberately not communicated yet.
        report_assignment = {"specialist_id": "report_writer", "operation": "reporting"}
        terms = {**self.terms, "target": "Summarize the completed site analysis.",
                 "approach": "Synthesize existing findings", "checks": ["Retain uncertainty and limits"],
                 "outputs": "Markdown report"}
        execution = {"inputs": [], "format": "markdown", "evidence_refs": [governing_ref]}
        report_scope = self.add("scope", {"action": "report", "terms": terms, "execution": execution,
            "assignment": report_assignment, "basis_versions": [{"ref": governing_ref, "event_ref": governing_ref}],
            "findings_refs": [governing_ref]})
        option = "Summarize the completed site analysis in Markdown, retaining uncertainty and site-specific limits; use existing findings without new computation."
        self.closeout = self.add("reply_prepared", {"responds_to": handling, "renderer": "lead-markdown-v11",
            "response": {"user_questions": [], "explanations": [], "questions": [],
                "next_steps": [{"option_id": "report", "kind": "action", "actor": "consultant",
                "label": "Write the report", "scope": option, "scope_ref": report_scope}],
                **({"findings": prepared_findings} if items else {})}})
        public = (("[To answer your question]\n\n[A1] " + finding["text"] + "\n\n") if items else "")
        self.snapshot(public_user, public + "[Next steps]\n\n[N1] " + option)
        accept = "Yes, write the report in N1 with those limits."
        ordinal = len(self.frames) + 1
        user = self.add("user_message", {"text": accept, "complete": True,
                                          "source": f"conversation:user-{ordinal}"})
        actual = self.add("reply_recorded", {"prepared": self.closeout, "before_user": user,
            "source": {"kind": "assistant_recorded", "locator": f"conversation:assistant-{ordinal - 1}"},
            "items": [*items, {"kind": "option", "label": "N1", "text": option, "scope_ref": report_scope}]})
        decision = "e" + str(len(self.journal))
        self.add("decision", {"user_message": user, "actual_reply": actual, "item": "N1", "scope": report_scope,
            "choice": "accept", "next_action": {"kind": "specialist", "scope": report_scope,
                "decision": decision, "assignment": report_assignment, "reason": "Write the selected report."}})
        self.report_run = "e" + str(len(self.journal))
        authored = {**execution, "kind": "report", "objective": terms["target"], "purpose": terms["target"],
                    "claim_boundary": terms["claim_boundary"]}
        plan_ref = f"runs/{self.report_run}/plan.yaml"
        basis = next(row["data"]["basis_versions"] for row in self.journal if row.get("id") == report_scope)
        plan = {**authored, "authored_plan": authored, "plan_schema_version": 8, "run_id": self.report_run,
                "responds_to": decision, "scope": report_scope, "decision": decision, "basis_versions": basis,
                "frozen_at": STAMP, "evidence_bindings": []}
        self.plans[plan_ref], self.files[plan_ref] = plan, sha(encoded(plan))
        self.add("work", {"phase": "started", "run": self.report_run, "kind": "report", "responds_to": decision,
            "scope": report_scope, "decision": decision, "plan_ref": plan_ref, "plan_sha256": self.files[plan_ref],
            "started_at": STAMP, "claim_boundary": terms["claim_boundary"]})
        self.snapshot(accept, "[What has been done]\n\nThe report has started.")
        return self


class V8ChronologyTests(unittest.TestCase):
    def observe(self, evidence):
        """Check both public observer routing and the driver's frozen-v8 routing."""
        direct = evaluate_frames(copy.deepcopy(evidence.frames))
        frozen = {"observation_profile": {"profile": "consultation-loop-v8", "journal_format": FORMAT,
                   "consultation_loop": True, "agent_recorded_reply": True,
                   "public_presentation": "four-section-responses-v1",
                   "public_presentation_renderer": "lead-markdown-v11", "public_presentation_option_max_words": 50},
                  "case_manifest": {"sources": [{"destination": "panel.csv"}]}}
        with patch.object(driver, "retained_frames", return_value=copy.deepcopy(evidence.frames)):
            dispatched = driver.consultation_loop_check(Path("unused-v8-fixture"), frozen)
        for key in ("profile", "status", "actions", "findings", "unobserved"):
            self.assertEqual(direct[key], dispatched[key], key)
        self.assertEqual(dispatched["profile"], "consultation-loop-v8")
        self.assertEqual([action["run_id"] for action in dispatched["actions"]],
                         ["e8"] + ([evidence.report_run] if hasattr(evidence, "report_run") else []))
        self.assertFalse(any(item["code"] in {"journal_unobserved", "entry_observation_incomplete"}
                             for item in dispatched["unobserved"]), dispatched)
        return dispatched

    def test_actual_offer_and_later_choice_are_observed_without_host_capture(self):
        result = self.observe(V8Evidence())
        self.assertEqual(result["status"], "no_structural_breach", result)
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["unobserved"], [])
        action = result["actions"][0]
        self.assertEqual(action["actual_reply_observation"]["actual_assistant_text"], OFFER)
        self.assertEqual(action["accepted_user_sources"][0]["actual_user_text"], ACCEPT)
        self.assertFalse(action["actual_reply_observation"]["native_identity_verified"])

    def test_saved_approval_cannot_substitute_an_option_absent_from_public_reply(self):
        result = self.observe(V8Evidence(public_offer="[To answer your question]\n\n[A1] Please explain the assignment."))
        self.assertEqual(result["status"], "breach", result)
        self.assertEqual({item["code"] for item in result["findings"]}, {"recorded_offer_not_presented"})

    def test_missing_or_error_marked_public_reply_remains_unobserved(self):
        for public_offer, public_error in ((None, None), (OFFER, "Public capture is incomplete.")):
            with self.subTest(public_error=public_error):
                evidence = V8Evidence(public_offer=public_offer)
                if public_error:
                    evidence.frames[0]["public_error"] = public_error
                result = self.observe(evidence)
                self.assertEqual(result["status"], "unobserved", result)
                self.assertEqual(result["findings"], [])
                self.assertTrue(any(item["code"] == "actual_offer_unobserved"
                                    for item in result["unobserved"]), result)
                self.assertNotEqual(result["actions"][0]["actual_reply_observation"]["status"], "current")

    def test_managed_work_before_acceptance_is_not_erased_by_later_approval(self):
        result = self.observe(V8Evidence(early_output=True))
        self.assertEqual(result["status"], "breach", result)
        self.assertEqual({item["code"] for item in result["findings"]}, {"protected_artifact_before_choice"})

    def test_whitespace_only_public_difference_preserves_offer_correspondence(self):
        result = self.observe(V8Evidence(public_offer="[Next steps]\r\n\r\n[N1] " + OPTION.replace(" ", "  ")))
        self.assertEqual(result["status"], "no_structural_breach", result)
        self.assertEqual(result["unobserved"], [])

    def test_paraphrased_recording_requires_review_without_inventing_a_breach(self):
        result = self.observe(V8Evidence(recorded_option="Estimate the randomized site effect with uncertainty and site-specific limits."))
        self.assertEqual(result["status"], "unobserved", result)
        self.assertEqual(result["findings"], [])
        self.assertTrue(any(item["code"] == "offer_wording_unverified"
                            for item in result["unobserved"]), result)
        self.assertTrue(any(item["code"] == "actual_item_correspondence_review"
                            for item in result["public_presentation_check"]["findings"]), result)

    def test_incorrect_recorded_label_does_not_prove_the_public_option_was_absent(self):
        result = self.observe(V8Evidence(recorded_label="N2"))
        self.assertEqual(result["status"], "unobserved", result)
        self.assertEqual(result["findings"], [])
        self.assertTrue(any(item["code"] == "offer_wording_unverified"
                            for item in result["unobserved"]), result)

    def test_unparseable_public_format_does_not_prove_the_offer_was_absent(self):
        result = self.observe(V8Evidence(public_offer=OPTION))
        self.assertEqual(result["status"], "unobserved", result)
        self.assertEqual(result["findings"], [])
        self.assertTrue(any(item["code"] == "offer_wording_unverified"
                            for item in result["unobserved"]), result)

    def test_progress_reference_and_completed_findings_keep_distinct_public_evidence(self):
        for discussion in ("progress", "completed"):
            with self.subTest(discussion=discussion):
                evidence = V8Evidence().through_report_start(discussion)
                result = self.observe(evidence)
                self.assertEqual(result["findings"], [])
                self.assertEqual(result["actions"][-1]["prior_discussion_refs"], ["e8"])
                deliveries = [row for row in result["delivery_correspondence"] if row["event"] == "004"
                              and any("e8" in item.get("work_refs", []) for item in row.get("items", []))]
                self.assertEqual(len(deliveries), 1)
                delivery = deliveries[0]
                self.assertEqual(delivery["public_ordinal"], 2 if discussion == "progress" else 3)
                self.assertTrue(delivery["semantic_review_required"])
                prior_ids = {row.get("id") for row in evidence.frames[delivery["public_ordinal"] - 1]["journal"]}
                self.assertEqual(evidence.completion in prior_ids, discussion == "completed")
                self.assertTrue(any("raw work IDs" in value for value in result["limitations"]))
                self.assertTrue(any("Progress is not completed findings" in value for value in result["review_requirements"]))

    def test_review_backed_findings_retain_links_for_private_review_without_false_breach(self):
        evidence = V8Evidence().through_report_start("review")
        result = self.observe(evidence)
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["actions"][-1]["prior_discussion_refs"], [evidence.completed_review])
        self.assertEqual({row["code"] for row in result["unobserved"]}, {"report_discussion_unobserved"})
        review = next(row for row in evidence.journal if row.get("id") == evidence.completed_review)
        self.assertEqual(review["data"]["work_refs"], ["e8"])
        self.assertTrue(any("review-to-run links" in value for value in result["review_requirements"]))

    def test_distinct_later_review_is_not_covered_by_an_earlier_same_run_discussion(self):
        evidence = V8Evidence().through_report_start("review", later_review=True)
        result = self.observe(evidence)
        self.assertEqual(result["findings"], [])
        refs = result["actions"][-1]["prior_discussion_refs"]
        self.assertIn(evidence.completed_review, refs)
        self.assertNotIn(evidence.later_review, refs)
        self.assertEqual({row["code"] for row in result["unobserved"]}, {"report_discussion_unobserved"})

    def test_resumed_closeout_uses_current_handling_without_rewriting_original_run(self):
        evidence = V8Evidence().through_report_start()
        result = self.observe(evidence)
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["unobserved"], [])
        closeout = next(row for row in result["response_correspondence"] if row["exchange_ref"] == evidence.closeout)
        self.assertEqual(closeout["responds_to"], evidence.resume_handling)
        self.assertEqual(closeout["user_message_refs"], [evidence.resume_user])
        self.assertEqual(result["actions"][0]["responds_to"], "e7")
        self.assertEqual(evidence.plans["runs/e8/plan.yaml"]["responds_to"], "e7")
        self.assertEqual(evidence.manifests["runs/e8/manifest.json"]["responds_to"], "e7")
        self.assertEqual(sum(row["type"] == "decision" and row["data"].get("scope") == "e3"
                             for row in evidence.journal[1:]), 1)


if __name__ == "__main__":
    unittest.main()
