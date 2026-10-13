"""Independent actual-output observations, without granting consent or grading science."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from consultation_observer import (evaluate_frames, public_item_words,
                                   public_presentation_check, _typed_public_items)


def frame(response, message=None, renderer="lead-markdown-v9", number=1, user="Please explain this result."):
    exchange = {"exchange_id": "exchange-" + str(number), "renderer": renderer, "response": response}
    groups = []
    for item in _typed_public_items(exchange):
        if not groups or groups[-1][0] != item["section"]:
            groups.append((item["section"], []))
        groups[-1][1].append(item["text"] if item["kind"] == "summary" else "[" + str(item["position"]) + "] " + item["text"])
    body = "\n\n".join("[" + label + "]\n\n" + "\n\n".join(items) for label, items in groups)
    row = {"event_id": "prepared-" + str(number), "sequence": 1, "type": "exchange_prepared", "payload": {"exchange": exchange}}
    return {"event": f"{number:03d}", "public": {"user": user, "assistant": body if message is None else message},
            "journal": [row], "files": {}, "plans": {}, "exchange_indexes": [{"exchange_id": exchange["exchange_id"],
                "response_sha256": hashlib.sha256(body.encode()).hexdigest()}], "response_bodies": {exchange["exchange_id"]: body}}


class PublicPresentationTests(unittest.TestCase):
    def inspect(self, response, message=None, **kwargs):
        return public_presentation_check([frame(response, message, **kwargs)])

    def test_direct_answer_and_explanation_need_no_extra_sections(self):
        for response, kind in (({"user_questions": [{"question_ref": "q1", "text": "What does it mean?", "answer": "The estimate is conditional."}]}, "answer"),
                               ({"explanations": [{"text": "The estimate is conditional.", "basis_refs": []}]}, "explanation")):
            with self.subTest(kind=kind):
                result = self.inspect(response)
                self.assertEqual(result["status"], "no_presentation_issue_observed", result)
                self.assertEqual(result["replies"][0]["sections"], ["To answer your question"])
                self.assertEqual(result["replies"][0]["items"][0]["kind"], kind)

    def test_mixed_types_keep_deterministic_positions_and_distinct_ids(self):
        response = {"user_questions": [{"question_ref": "answer-id", "text": "Why?", "answer": "A bounded answer."}],
                    "explanations": [{"text": "A useful explanation.", "basis_refs": ["evidence-id"]}],
                    "findings": {"summary": "A conditional finding.", "diagnostics": ["Checked dates."], "limitations": ["No random assignment."], "work_refs": ["run-id"]},
                    "status": "Checked the supplied dates.", "questions": [{"question_ref": "information-id", "text": "When did collection begin?"}],
                    "next_steps": [{"option_id": "option-id", "actor": "consultant", "label": "Discuss assumptions", "scope": "Review their implications."}]}
        result = self.inspect(response)
        self.assertFalse(result["findings"], result)
        items = result["replies"][0]["items"]
        self.assertEqual([item["kind"] for item in items], ["answer", "explanation", "findings", "summary", "question", "option"])
        self.assertEqual([item["position"] for item in items], [1, 2, 3, None, 1, 1])
        self.assertEqual(items[1]["source_path"], "response.explanations[0]")
        self.assertEqual(items[2]["refs"], ["run-id"])
        self.assertEqual(items[-2]["question_ref"], "information-id")
        self.assertEqual(items[-1]["option_id"], "option-id")

    def test_whole_items_count_labels_echoes_qualifiers_and_not_destinations(self):
        for count in (49, 50, 51):
            with self.subTest(count=count):
                text = " ".join(["word"] * (count - 2)) + " [source label](<https://example.test/a long destination>)"
                self.assertEqual(public_item_words(text), count)
                result = self.inspect({"explanations": [{"text": text}]})
                self.assertEqual(result["replies"][0]["items"][0]["word_count"], count)
                self.assertEqual(any(item["code"] == "public_item_overlength" for item in result["findings"]), count > 50)
        result = self.inspect({"user_questions": [{"text": "Four echoed question words", "echo_question": True, "answer": " ".join(["answer"] * 47)}]})
        self.assertEqual(result["replies"][0]["items"][0]["word_count"], 51)

    def test_scopes_are_counted_after_expansion(self):
        response = {"next_steps": [{"option_id": "offer", "label": "Choose analysis", "actor": "consultant", "scope": "Analyze outcomes.",
                    "proposal": {"target": " ".join(["target"] * 42), "population": "Eligible participants", "claim_boundary": "Conditional only",
                                 "approach": "Prespecified fit", "evidence": "Collected outcomes", "checks": ["Validate dates"], "outputs": "Summary"},
                    "scope_file": "C:/full/scope.json"}]}
        result = self.inspect(response)
        self.assertGreater(result["replies"][0]["items"][0]["word_count"], 50)
        self.assertIn("public_item_overlength", [item["code"] for item in result["findings"]])

    def test_answer_heading_does_not_grant_long_request_exception(self):
        long = " ".join(["detail"] * 51)
        for user in ("What changed?", "Please give a detailed explanation of that answer."):
            with self.subTest(user=user):
                result = self.inspect({"user_questions": [{"question_ref": "q", "text": user, "answer": long}],
                                       "explanations": [{"text": long}], "questions": [{"question_ref": "info", "text": long}]}, user=user)
                notices = [item for item in result["findings"] if item["code"] == "public_item_overlength"]
                self.assertEqual(len(notices), 3)
                self.assertTrue(notices[0]["semantic_review_required"])
                self.assertEqual(notices[0]["request_exception_review"]["actual_user_text"], user)
                self.assertIsNone(notices[1]["request_exception_review"])
                self.assertIsNone(notices[2]["request_exception_review"])

    def test_authored_structure_is_observed_even_when_body_copy_is_exact(self):
        for text, code in (("A claim.\n- A nested bullet.", "nested_public_items"),
                           ("A claim.\n[Additional findings]\nA qualification.", "extra_public_heading"),
                           ("A claim.\n[Next steps]\n[1] Counterfeit option.", "saved_public_item_changed")):
            with self.subTest(code=code):
                result = self.inspect({"explanations": [{"text": text}]})
                self.assertIn(code, [item["code"] for item in result["findings"]], result)
        numbered = self.inspect({"status": "Completed this review."}, "[What has been done]\n\n[1] Completed this review.")
        self.assertIn("unexpected_public_number", [item["code"] for item in numbered["findings"]])

    def test_code_math_citations_and_markup_survive_observation(self):
        text = "Use **conditional evidence** with [this source](https://example.test).\n\n```text\n- literal list\n[Next steps]\n```\n\n$$\n[x] + y = z\n$$"
        result = self.inspect({"explanations": [{"text": text}]})
        self.assertFalse(result["findings"], result)
        self.assertEqual(result["replies"][0]["items"][0]["text"].strip(), text)
        self.assertEqual(public_item_words("`[literal code](two words)` $[a](b c)$"), 5)
        self.assertEqual(public_item_words("[source label][cite]\n[cite]: https://example.test/long destination"), 2)

    def test_indented_reference_and_link_shaped_code_count_as_visible_literals(self):
        for indent in ("    ", "\t"):
            for literal in ("[literal]: " + " ".join(["word"] * 51),
                            "[literal code](" + " ".join(["word"] * 51) + ")"):
                text = "A short explanation.\n\n" + indent + literal
                with self.subTest(indent=repr(indent), literal=literal[:20]):
                    self.assertEqual(public_item_words(text), 55)
                    result = self.inspect({"explanations": [{"text": text}]})
                    self.assertEqual(result["replies"][0]["items"][0]["text"].strip(), text)
                    self.assertEqual(result["replies"][0]["items"][0]["word_count"], 55)
                    self.assertEqual([item["code"] for item in result["findings"]], ["public_item_overlength"])

    def test_reference_definitions_are_hidden_only_in_ordinary_prose(self):
        literal = "[literal]: " + " ".join(["word"] * 51)
        for opener, closer in (("```text", "```"), ("$$", "$$"), (r"\[", r"\]")):
            with self.subTest(opener=opener):
                text = "A short explanation.\n\n" + opener + "\n" + literal + "\n" + closer
                self.assertEqual(public_item_words(text), 55)
                result = self.inspect({"explanations": [{"text": text}]})
                self.assertEqual(result["replies"][0]["items"][0]["text"].strip(), text)
                self.assertEqual([item["code"] for item in result["findings"]], ["public_item_overlength"])
        for indent in ("", " ", "   "):
            with self.subTest(indent=repr(indent)):
                self.assertEqual(public_item_words("A short explanation.\n" + indent + literal), 3)

    def test_more_than_ten_items_and_restart_in_next_section(self):
        result = self.inspect({"explanations": [{"text": "Detail " + str(index)} for index in range(12)],
                               "questions": [{"question_ref": "remaining", "text": "When?"}]})
        self.assertFalse(result["findings"], result)
        self.assertEqual(result["replies"][0]["items"][11]["position"], 12)
        self.assertEqual(result["replies"][0]["items"][12]["position"], 1)

    def test_content_correspondence_is_separate_from_scientific_judgment(self):
        result = self.inspect({"findings": {"summary": "Estimate two.", "diagnostics": [], "limitations": ["Conditional on assumptions."]}},
                              "[To answer your question]\n\n[1] Estimate two.")
        issue = next(item for item in result["findings"] if item["code"] == "saved_public_item_changed")
        self.assertEqual(issue["category"], "content_correspondence")
        self.assertTrue(issue["semantic_review_required"])
        self.assertNotIn("scientific_failure", result)

    def test_old_numbered_summary_is_not_reclassified_by_new_contract(self):
        result = self.inspect({"status": "Completed."}, "[What has been done]\n\n[1] Completed.", renderer="lead-markdown-v8")
        self.assertEqual(result["status"], "not_applicable")
        self.assertFalse(result["findings"])

    def test_real_store_fresh_legacy_fixture_is_retained_and_flagged(self):
        fixture_path = Path(__file__).resolve().parent / "fixtures/runtime-fresh-renderer-fixture.json"
        original = fixture_path.read_bytes()
        fixture = json.loads(original)
        frames = copy.deepcopy(fixture["frames"])
        self.assertTrue(fixture["journal_replay_valid"])
        self.assertFalse(fixture["fresh_exchange"]["appeared_in_previous_snapshot"])
        result = public_presentation_check(frames, default_renderer="lead-markdown-v9")
        self.assertEqual(result["status"], "review_required")
        self.assertEqual([reply["event"] for reply in result["replies"]], ["001", "002"])
        reply = result["replies"][1]
        self.assertEqual(reply["actual_assistant_text"], frames[1]["public"]["assistant"])
        self.assertEqual(reply["renderer_observation"]["status"], "fresh_unexpected_renderer")
        codes = [item["code"] for item in result["findings"] if item["event"] == "002"]
        self.assertIn("unexpected_current_renderer", codes)
        self.assertIn("public_sections_unobserved", codes)
        self.assertIn("nested_public_items", codes)
        self.assertIn("private/events/002/public.json", result["evidence_refs"])
        self.assertEqual(frames, fixture["frames"])
        self.assertEqual(fixture_path.read_bytes(), original)

    def test_unchanged_preexisting_legacy_exchange_keeps_its_original_contract(self):
        prior = frame({"status": "Completed."}, "[What has been done]\n\n[1] Completed.", renderer="lead-markdown-v8")
        current = copy.deepcopy(prior)
        current["event"] = "002"
        original = copy.deepcopy([prior, current])
        result = public_presentation_check([prior, current], default_renderer="lead-markdown-v9")
        # The first snapshot cannot establish its own history; the second can.
        self.assertEqual([item["code"] for item in result["findings"]], ["renderer_history_unobserved"])
        reply = result["replies"][1]
        self.assertEqual(reply["status"], "historical_profile_not_applied")
        self.assertEqual(reply["renderer_observation"]["status"], "unchanged_preexisting_exchange")
        self.assertEqual(reply["actual_assistant_text"], current["public"]["assistant"])
        self.assertFalse(reply["items"])
        self.assertEqual([prior, current], original)

    def test_changed_legacy_row_cannot_claim_historical_exemption(self):
        prior = frame({"status": "Completed."}, renderer="lead-markdown-v8")
        for change in ("event_id", "saved_text"):
            current = copy.deepcopy(prior)
            current["event"] = "002"
            row = current["journal"][0]
            if change == "event_id":
                row["event_id"] = "newly-prepared"
            else:
                row["payload"]["exchange"]["response"]["status"] = "Changed summary."
            current["public"]["assistant"] = "Plain current output.\n- Nested list."
            with self.subTest(change=change):
                result = public_presentation_check([prior, current], default_renderer="lead-markdown-v9")
                codes = [item["code"] for item in result["findings"] if item["event"] == "002"]
                self.assertIn("unexpected_current_renderer", codes)
                self.assertIn("public_sections_unobserved", codes)

    def test_missing_preceding_journal_cannot_certify_history_or_invent_freshness(self):
        current = frame({"status": "Completed."}, "Plain output.", renderer="lead-markdown-v8", number=2)
        for prior in (None, {"event": "001", "public": {}, "journal": None},
                      {"event": "001", "public": {}, "journal": ["unreadable row"]},
                      {"event": "001", "public": {}, "journal": [{"event_id": "broken"}]}):
            with self.subTest(prior=prior):
                result = public_presentation_check(([prior] if prior else []) + [current], default_renderer="lead-markdown-v9")
                codes = [item["code"] for item in result["findings"] if item["event"] == "002"]
                self.assertEqual(codes, ["renderer_history_unobserved"])
                self.assertEqual(result["status"], "review_required")
                reply = next(reply for reply in result["replies"] if reply["event"] == "002")
                self.assertEqual(reply["actual_assistant_text"], "Plain output.")
                self.assertEqual(reply["status"], "renderer_history_unobserved")

    def test_v10_profile_observes_fresh_v9_but_preserves_unchanged_v9(self):
        prior = frame({"status": "Completed."})
        for unchanged in (False, True):
            current = copy.deepcopy(prior) if unchanged else frame({"status": "New summary."}, number=2)
            current["event"] = "002"
            with self.subTest(unchanged=unchanged):
                result = public_presentation_check([prior, current], default_renderer="lead-markdown-v10")
                codes = [item["code"] for item in result["findings"] if item["event"] == "002"]
                self.assertEqual("unexpected_current_renderer" in codes, not unchanged)
                self.assertEqual(result["replies"][1]["status"], "observed")

    def test_v10_requested_scope_is_counted_once_in_answer_and_short_option(self):
        response = {"user_questions": [{"question_ref": "detail-question", "text": "Explain the complete plan.",
                                       "answer": "Here are its complete terms.", "scope_ref": "scope-one", "basis_refs": ["user-detail"]}],
                    "next_steps": [{"option_id": "offer", "scope_ref": "scope-one", "label": "Choose analysis", "scope": "Use this plan.",
                                    "proposal": {"target": " ".join(["target"] * 40), "population": "Eligible participants",
                                                 "claim_boundary": "Conditional only", "approach": "Prespecified fit",
                                                 "evidence": "Collected outcomes", "checks": ["Validate dates"], "outputs": "Summary"},
                                    "scope_file": "C:/full/scope.json"}]}
        result = self.inspect(response, renderer="lead-markdown-v10", user="Please explain the complete detailed plan before I select it.")
        answer, option = result["replies"][0]["items"]
        self.assertEqual(answer["refs"], ["detail-question", "user-detail", "scope-one"])
        self.assertEqual(answer["scope_ref"], "scope-one")
        self.assertIn("Evidence: Collected outcomes.", answer["text"])
        self.assertIn("[Full saved scope](<C:/full/scope.json>)", answer["text"])
        self.assertEqual(option["text"].strip(), "Choose analysis\n\nUse this plan.\n\nUse the complete scope in [1] under [To answer your question].")
        self.assertGreater(answer["word_count"], 50)
        self.assertLessEqual(option["word_count"], 50)
        notices = [item for item in result["findings"] if item["code"] == "public_item_overlength"]
        self.assertEqual(len(notices), 1)
        self.assertEqual(notices[0]["source_path"], "response.user_questions[0]")
        self.assertTrue(notices[0]["semantic_review_required"])
        self.assertEqual(notices[0]["request_exception_review"]["question_ref"], "detail-question")

    def test_v10_scope_pointer_and_terms_correspondence_remain_independent(self):
        response = {"user_questions": [{"question_ref": "first", "answer": "A short answer."},
                                       {"question_ref": "detail", "answer": "The requested plan.", "scope_ref": "scope"}],
                    "next_steps": [{"option_id": "offer", "scope_ref": "scope", "label": "Choose plan", "scope": "Use these terms.",
                                    "proposal": {"target": "Treatment comparison", "population": "Eligible population", "evidence": "Supplied data",
                                                 "approach": "Prespecified analysis", "checks": ["Check dates"], "outputs": "Summary", "claim_boundary": "Conditional"},
                                    "scope_file": "scope.json"}]}
        retained = frame(response, renderer="lead-markdown-v10")
        body = retained["public"]["assistant"]
        self.assertIn("Use the complete scope in [2] under [To answer your question].", body)
        self.assertFalse(public_presentation_check([retained])["findings"])
        for before, after in (("scope in [2]", "scope in [1]"), ("Eligible population.", "Everyone.")):
            with self.subTest(before=before):
                changed = copy.deepcopy(retained)
                changed["public"]["assistant"] = body.replace(before, after)
                result = public_presentation_check([changed])
                self.assertIn("saved_public_item_changed", [item["code"] for item in result["findings"]])

    def test_saved_exchange_and_reviewer_observations_retain_separate_presentation_check(self):
        import session_driver as driver
        retained = frame({"explanations": [{"text": " ".join(["explanation"] * 51)}]})
        exchange = retained["journal"][0]["payload"]["exchange"]
        exchange.update(turn_id="turn", event_ref="prepared-1", response_sha256=retained["exchange_indexes"][0]["response_sha256"])
        with tempfile.TemporaryDirectory() as directory:
            attempt = Path(directory)
            event = attempt / "events/001"
            (event / "project-status").mkdir(parents=True)
            driver.write(event / "project-status/process.json", {"exit_code": 0, "error": None})
            driver.write(event / "project-status/stdout.txt", {"views": {"work": {"current_exchange_ref": exchange["exchange_id"], "exchanges": [exchange]}}})
            driver.write(event / "public.json", retained["public"])
            driver.observe_exchange(event)
            observation = driver.read(event / "exchange-observation.json")
            self.assertEqual(observation["status"], "matched")
            self.assertEqual(observation["public_presentation_check"]["status"], "review_required")
            self.assertEqual(observation["explanations"], exchange["response"]["explanations"])
            frozen = {"observation_profile": {"consultation_loop": True, "public_presentation": "four-section-responses-v1"}, "case_manifest": {"sources": []}}
            index = {"sha256": "synthetic-index", "files": {"private/events/001/public.json": "synthetic-hash"}}
            with patch.object(driver, "retained_frames", return_value=[retained]), patch.object(driver, "candidate_loading_check", return_value=None), patch.object(driver, "source_release_observations", return_value=[]):
                reviewed = driver.review_observations(attempt, {"turns": 1}, frozen, index)
            self.assertEqual(reviewed["consultation_loop_check"]["status"], "no_structural_breach")
            issue = next(item for item in reviewed["machine_findings"] if item["check"] == "public_presentation")
            self.assertEqual(issue["observation"]["code"], "public_item_overlength")
            self.assertEqual(issue["observation"]["severity"], "minor")


class DeliveryIdentityObservationTests(unittest.TestCase):
    def observe(self, message_ref="native-1", native_text=None, equivalence=False, return_frames=False):
        first = frame({"explanations": [{"text": "Conditional result."}]})
        first["public_identity"] = {"session_id": "session", "conversation_ref": "claude-code:session", "message_ref": "native-1",
                                    "ordinal": 10, "evidence_refs": ["native-evidence"]}
        if native_text is not None:
            first["public"]["assistant"] = native_text
        second = copy.deepcopy(first)
        second["event"] = "002"
        second["public_identity"]["message_ref"] = "native-2"
        second["public_identity"]["ordinal"] = 20
        captured = first["response_bodies"]["exchange-1"]
        if equivalence:
            captured = captured.replace("\n", "\r\n")
        delivery = {"delivery_id": "capture", "exchange_ref": "exchange-1", "source_ref": "observed.txt", "capture_protocol": "captured-delivery-v2",
                    "capture_message": {"conversation_ref": "claude-code:session", "message_ref": message_ref, "ordinal": 10},
                    "observed_response_sha256": hashlib.sha256(captured.encode()).hexdigest(), "response_sha256": first["exchange_indexes"][0]["response_sha256"]}
        if equivalence:
            delivery["response_equivalence"] = "lf-crlf-v1"
        second["journal"].append({"event_id": "capture", "sequence": 2, "type": "exchange_delivery", "payload": {"delivery": delivery}})
        second["delivery_captures"] = {"observed.txt": captured}
        return [first, second] if return_frames else evaluate_frames([first, second])

    def test_identical_text_does_not_make_an_older_recapture_new(self):
        result = self.observe()
        capture = result["delivery_correspondence"][0]
        self.assertEqual(capture["public_match_events"], ["001", "002"])
        self.assertTrue(capture["native_identity_verified"])
        self.assertEqual(capture["identity_match_events"], ["001"])
        self.assertFalse(capture["latest_observed_conversation_message"])
        self.assertEqual(capture["order_status"], "native_order_matched")

    def test_matching_another_message_cannot_repair_the_claimed_identity(self):
        result = self.observe(message_ref="native-1", native_text="Changed native message.")
        # Restore one later public copy, while the claimed native identity differs.
        self.assertIn("delivery_message_identity_mismatch", [item["code"] for item in result["findings"]])

    def test_lf_crlf_is_named_separately_from_raw_equality(self):
        result = self.observe(equivalence=True)
        capture = result["delivery_correspondence"][0]
        self.assertEqual(capture["status"], "line_endings_equivalent_public_capture")
        self.assertFalse(capture["raw_byte_equality"])
        self.assertTrue(capture["captured_body_line_endings_equivalent"])

    def test_capture_identity_without_native_evidence_remains_unobserved(self):
        result = self.observe(message_ref="unavailable-native")
        capture = result["delivery_correspondence"][0]
        self.assertEqual(capture["status"], "exact_public_capture")
        self.assertFalse(capture["native_identity_verified"])
        self.assertEqual(capture["identity_status"], "native_identity_unobserved")
        self.assertEqual(capture["order_status"], "unobserved")

    def test_older_recapture_does_not_displace_a_newer_discrepancy(self):
        frames = self.observe(return_frames=True)
        second = frames[-1]
        second["public"]["assistant"] += " Removed the condition."
        newer = copy.deepcopy(second["journal"][-1])
        newer.update(event_id="newer-capture", sequence=3)
        newer["payload"]["delivery"].update(delivery_id="newer", source_ref="newer.txt",
            capture_message={"conversation_ref": "claude-code:session", "message_ref": "native-2", "ordinal": 20},
            observed_response_sha256=hashlib.sha256(second["public"]["assistant"].encode()).hexdigest())
        second["journal"].append(newer)
        second["delivery_captures"]["newer.txt"] = second["public"]["assistant"]
        third = copy.deepcopy(second)
        third["event"] = "003"
        third["public_identity"].update(message_ref="native-3", ordinal=30)
        old = copy.deepcopy(second["journal"][1])
        old.update(event_id="older-recapture", sequence=4)
        old["payload"]["delivery"]["delivery_id"] = "old-again"
        third["journal"].append(old)
        result = evaluate_frames([*frames, third])
        self.assertEqual(result["delivery_applicability"][0]["applicable_delivery_refs"], ["newer"])
        self.assertEqual(result["delivery_correspondence"][-1]["identity_match_events"], ["001"])
        self.assertFalse(result["delivery_correspondence"][-1]["latest_observed_conversation_message"])

    def test_multiple_unidentified_messages_do_not_use_append_order(self):
        frames = self.observe(return_frames=True)
        delivery = frames[-1]["journal"][-1]["payload"]["delivery"]
        delivery.pop("capture_message")
        extra = copy.deepcopy(frames[-1]["journal"][-1])
        extra.update(event_id="another-capture", sequence=3)
        changed = frames[-1]["public"]["assistant"] + " Changed scope."
        extra["payload"]["delivery"].update(delivery_id="another", source_ref="another.txt", observed_response_sha256=hashlib.sha256(changed.encode()).hexdigest())
        frames[-1]["journal"].append(extra)
        frames[-1]["delivery_captures"]["another.txt"] = changed
        result = evaluate_frames(frames)
        self.assertEqual(result["delivery_applicability"][0]["status"], "unresolved")
        self.assertIn("delivery_message_order_unobserved", [item.get("code") for item in result["unobserved"]])

    def test_same_native_identity_conflicting_bytes_are_not_a_newer_message(self):
        frames = self.observe(return_frames=True)
        extra = copy.deepcopy(frames[-1]["journal"][-1])
        extra.update(event_id="conflicting-capture", sequence=3)
        changed = "Altered qualification."
        extra["payload"]["delivery"].update(delivery_id="conflict", source_ref="conflict.txt", observed_response_sha256=hashlib.sha256(changed.encode()).hexdigest())
        frames[-1]["journal"].append(extra)
        frames[-1]["delivery_captures"]["conflict.txt"] = changed
        result = evaluate_frames(frames)
        self.assertIn("delivery_message_identity_conflict", [item["code"] for item in result["findings"]])
        self.assertEqual(result["delivery_applicability"][0]["status"], "unresolved")

    def test_claimed_line_ending_equivalence_cannot_hide_changed_content(self):
        frames = self.observe(equivalence=True, return_frames=True)
        delivery = frames[-1]["journal"][-1]["payload"]["delivery"]
        changed = "Different result."
        frames[-1]["delivery_captures"][delivery["source_ref"]] = changed
        delivery["observed_response_sha256"] = hashlib.sha256(changed.encode()).hexdigest()
        result = evaluate_frames(frames)
        self.assertIn("delivery_equivalence_mismatch", [item["code"] for item in result["findings"]])

    def test_missing_prepared_body_is_unobserved_equivalence_not_a_wording_change(self):
        frames = self.observe(equivalence=True, return_frames=True)
        for retained in frames:
            retained.pop("response_bodies")
        result = evaluate_frames(frames)
        self.assertIsNone(result["delivery_correspondence"][0]["captured_body_line_endings_equivalent"])
        self.assertIn("delivery_equivalence_body_unavailable", [item.get("code") for item in result["unobserved"]])
        self.assertNotIn("delivery_equivalence_mismatch", [item["code"] for item in result["findings"]])

    def test_native_order_requires_compatible_retained_prefixes(self):
        for compatible in (False, True):
            with self.subTest(compatible=compatible):
                frames = self.observe(return_frames=True)
                frames[0]["public_identity"]["ordinal"] = 1
                frames[1]["public_identity"]["ordinal"] = 2
                old = frames[1]["journal"][-1]["payload"]["delivery"]
                old["capture_message"]["ordinal"] = 1
                extra = copy.deepcopy(frames[1]["journal"][-1])
                extra.update(event_id="second-native", sequence=3)
                newer = extra["payload"]["delivery"]
                newer.update(delivery_id="new-native", source_ref="native-two.txt",
                             capture_message={"conversation_ref": "claude-code:session", "message_ref": "native-2", "ordinal": 2})
                frames[1]["journal"].append(extra)
                frames[1]["delivery_captures"]["native-two.txt"] = frames[1]["delivery_captures"]["observed.txt"]
                frames[1]["delivery_native_orders"] = {}
                for capture, path in ((old, ["native-1"]), (newer, ["native-1" if compatible else "unrelated", "native-2"])):
                    proof = {"session_id": "session", "transcript_sha256": "a" * 64,
                             "messages": [{"message_uuid": identity, "record_sha256": "b" * 64} for identity in path]}
                    sha = hashlib.sha256((json.dumps(proof) + "\n").encode()).hexdigest()
                    capture["capture_message"].update(order_path=path, order_sha256=sha)
                    frames[1]["delivery_native_orders"][capture["source_ref"]] = {"value": proof, "sha256": sha, "evidence_ref": "synthetic-native-order"}
                result = evaluate_frames(frames)
                self.assertEqual(result["delivery_applicability"][0]["status"], "ordered_attributed_messages" if compatible else "unresolved")
                if compatible:
                    self.assertEqual(result["delivery_applicability"][0]["applicable_delivery_refs"], ["new-native"])


class PendingIntakeObservationTests(unittest.TestCase):
    def test_pending_original_message_blocks_protected_start_until_interpreted(self):
        from test_consultation_loop import Transcript
        for reconcile in (False, True):
            with self.subTest(reconcile=reconcile):
                transcript = Transcript()
                transcript.scope("main")
                offer = transcript.reply("Help", ["main"], renderer="lead-markdown-v8")
                choice = transcript.decide("main", "Use that scope", offer)
                source = {"evidence_id": "raw-direction", "kind": "user_statement", "source_ref": "chat:raw-direction",
                          "source_excerpt": "Use that analysis and retain my correction.", "complete_message": True,
                          "source_intake": "primary-message-v1"}
                transcript.row("memory_updated", {"changes": {"evidence": [source]}})
                if reconcile:
                    transcript.row("reply_interpreted", {"interpretation": {"interpretation_id": "reconciled-direction", "incoming_refs": [source["evidence_id"]],
                        "components": [{"kind": "correction", "meaning": source["source_excerpt"], "established": [], "unresolved": []}]}})
                transcript.run("main", choice)
                transcript.reply(source["source_excerpt"], renderer="lead-markdown-v8")
                observed = evaluate_frames(transcript.frames)
                self.assertEqual("protected_start_with_pending_user_direction" in [item["code"] for item in observed["findings"]], not reconcile)
                intake = observed["incoming_message_interpretations"][0]
                self.assertEqual(intake["actual_source_text"], source["source_excerpt"])
                self.assertEqual(intake["status"], "interpreted" if reconcile else "awaiting_interpretation")
                self.assertTrue(intake["semantic_review_required"])

    def test_historical_unconsumed_sources_are_not_retroactively_pending(self):
        retained = frame({"explanations": [{"text": "Existing context."}]}, renderer="lead-markdown-v8")
        retained["journal"].append({"event_id": "old-source", "sequence": 2, "type": "memory_updated", "payload": {
            "changes": {"evidence": [{"evidence_id": "old-context", "kind": "user_statement", "complete_message": True, "source_excerpt": "Old information."}]}}})
        result = evaluate_frames([retained])
        self.assertFalse(result["incoming_message_interpretations"])


if __name__ == "__main__":
    unittest.main()
