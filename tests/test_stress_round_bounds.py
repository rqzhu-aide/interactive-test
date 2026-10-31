"""Reply-bound checks, with separate cap-only and real frozen-runner boundary fixtures."""
from pathlib import Path
import copy
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "interactive-test/scripts"))
import session_driver as d
import compose_case as c

PLANNING_IDS = tuple(name for name in c.STANDALONE_IDS if name != c.RGGVY_ID)

class Mechanics(unittest.TestCase):
    """Cap-only checks: integrity, actor binding and project observation are mocked."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.a = Path(self.temp.name)
        (self.a / "events").mkdir()
        (self.a / "case/public").mkdir(parents=True)
        (self.a / "testing/references").mkdir(parents=True)
        (self.a / "testing/references/user-simulator.md").write_text("Policy")
        (self.a / "case/public/initial.txt").write_text("Use causal-consultant.")
        self.actor = {"facts": [], "rules": [], "consultant_reply_bounds": {"minimum": 8,"maximum":12}}
        d.write(self.a / "case/actor.json", self.actor)
        self.case = {"actor":"actor.json","reviewer":"reviewer.json","initial_message":"public/initial.txt","sources":[],"minimum_consultant_replies":8,"run_limits":{"consultant_turns":12},"completion_contract":"full_report"}
        self.config = {"limits":{"consultant_turns":12,"active_seconds":100,"elapsed_seconds":100},"call_timeout_seconds":10,"mode":"diagnostic"}
        self.frozen = {"case_manifest":self.case,"configuration":self.config,"reviewer_packet":{"criteria":[{"id":"stress-gap","required":True}],"useful_stop":True}}
        d.write(self.a / "freeze.json", self.frozen)
        self.state = {"status":"ready","turns":0,"work":str(self.a / "work"),"session_id":"test","started_at":time.time(),"active_seconds":0,"breaches":[],"public_files":{},"released_sources":[]}
        self.save()
        for name in ("integrity","validate_actor_input","observe_project"):
            p = patch.object(d,name)
            p.start()
            self.addCleanup(p.stop)

    def save(self): d.write(self.a / "state.json", self.state)
    def seed(self,n):
        for k in range(1,n+1):
            e = self.a / "events" / f"{k:03d}"
            (e / "transport").mkdir(parents=True, exist_ok=True)
            d.write(e / "public.json", {"user":"Please explain.","assistant":"Delivered."})
            d.write(e / "transport/transport.json", {"error":None,"message":"Delivered."})
            d.write(e / "actor.json", self.reply())
        self.state["turns"] = n
        self.save()
    def reply(self,stop=False):
        return {"message":None if stop else "Please explain.","fact_ids":[],"rule_ids":[],"attachments":[],"unanswered_questions":[],"fixture_gaps":[],"stop":stop}
    def review(self,unobserved=False):
        return {"evidence_sha256":"test","test_validity":"valid","test_validity_reason":"mock","outcome":"objective_met","stop_reason":"mock","reviewer":"mock","coverage":{"stress-gap":{"status":"unobserved" if unobserved else "observed","reason":"mock","evidence_refs":["p"]}},"findings":[]}
    def assess(self,n,report=True,unobserved=False):
        return d.assess(self.review(unobserved),self.state,self.frozen,{"sha256":"test","files":{"p":"hash"}},completion_check={"satisfied":report},delivered_replies=n)
    def invoke(self,*args):
        out = args[-1]; out.mkdir()
        value={"active_seconds":0.01,"message":"Delivered.","error":None}
        d.write(out / "transport.json",value)
        return value

    def planning_case(self, identity="forest-planning", cap=12):
        manifest = d.read(ROOT / "interactive-test/standalone" / identity / "case.json")
        self.case.pop("minimum_consultant_replies", None)
        self.actor.pop("consultant_reply_bounds", None)
        for key in ("case_id", "edition", "run_limits", "completion_contract"):
            self.case[key] = manifest[key]
        self.config["limits"]["consultant_turns"] = cap
        d.write(self.a / "case/actor.json", self.actor)
        d.write(self.a / "freeze.json", self.frozen)

    def test_resumed_planning_cases_reject40_and_dispatch_with12(self):
        self.seed(1)
        for identity in PLANNING_IDS:
            with self.subTest(case=identity):
                self.planning_case(identity, cap=40)
                before = d.inventory(self.a)
                with patch.object(d, "invoke") as invoke, self.assertRaisesRegex(ValueError, "planning run configuration"):
                    d.step(self.a, self.reply())
                invoke.assert_not_called()
                self.assertEqual(d.inventory(self.a), before)
                self.planning_case(identity)
                previous_turns = self.state["turns"]
                with patch.object(d, "invoke", side_effect=self.invoke) as invoke:
                    self.assertEqual(d.step(self.a, self.reply())["status"], "ready")
                invoke.assert_called_once()
                self.state = d.read(self.a / "state.json")
                self.assertEqual(self.state["turns"], previous_turns + 1)

    def test_planning_preflight_rejects40_before_candidate_validation(self):
        for identity in PLANNING_IDS:
            manifest = d.read(ROOT / "interactive-test/standalone" / identity / "case.json")
            config = {**self.config, "node_command": ["node"], "candidate_loading": "adapter",
                      "limits": {**self.config["limits"], "consultant_turns": 40}}
            probe = type("Probe", (), {"returncode": 0, "stdout": b"22.0.0", "stderr": b""})()
            with self.subTest(case=identity), patch.object(d, "validate_config"), \
                    patch.object(d, "validate_case", return_value=manifest), \
                    patch.object(d.subprocess, "run", return_value=probe), \
                    patch.object(d, "candidate_inventory") as inventory:
                with self.assertRaisesRegex(ValueError, "planning run configuration"):
                    d.preflight(self.a / "case", self.a / "candidate", config)
                inventory.assert_not_called()

    def test_planning_early_useful_stop_needs_no_minimum_or_report(self):
        self.planning_case()
        self.seed(3)
        self.assertEqual(d.step(self.a, self.reply(True))["status"], "awaiting_review")
        self.state = d.read(self.a / "state.json")
        review = self.review()
        review.update(outcome="useful_stop", useful_stop_basis="The chosen preparation step is clear.")
        result = d.assess(review, self.state, self.frozen, {"sha256": "test", "files": {"p": "hash"}})
        self.assertEqual(result["outcome"], "useful_stop")
        self.assertIsNone(result["completion_check"])
        self.assertEqual(self.state["turns"], 3)

    def test_planning_cap12_never_dispatches13(self):
        self.planning_case()
        self.seed(12)
        with patch.object(d, "invoke") as invoke:
            self.assertEqual(d.step(self.a, self.reply())["status"], "limit_reached")
        invoke.assert_not_called()
        self.state = d.read(self.a / "state.json")
        self.assertEqual(self.assess(12)["outcome"], "incomplete")
        self.assertFalse((self.a / "events/013").exists())

    def test_cap_only_planning_stop_and_review_preserve_supplied_historical_finding(self):
        # The shared integrity/actor mocks isolate the cap exemption and supplied
        # finding. FrozenRunnerMechanics covers identity and actor binding below.
        self.planning_case(cap=40)
        self.seed(20)
        Path(self.state["work"]).mkdir()
        d.write(self.a / "case/reviewer.json", self.frozen["reviewer_packet"])
        frozen_bytes = (self.a / "freeze.json").read_bytes()
        with patch.object(d, "invoke") as invoke:
            self.assertEqual(d.step(self.a, self.reply(True))["status"], "awaiting_review")
        invoke.assert_not_called()
        observations = {"machine_findings": [], "completion_check": None,
                        "consultation_loop_check": {"status": "no_structural_breach", "findings": []},
                        "missing_captures": []}
        with patch.object(d, "review_observations", return_value=observations):
            inspected = d.inspect(self.a, "reviewer")
            review = self.review()
            review.update(evidence_sha256=inspected["evidence_sha256"],
                          observations_sha256=inspected["observations_sha256"], outcome="incomplete")
            review["coverage"]["stress-gap"]["evidence_refs"] = ["private/freeze.json"]
            review["findings"] = [{"owner": "harness", "severity": "material", "criterion": "stress-gap",
                                   "description": "Configured 40 replies despite the frozen ceiling of 12.",
                                   "consequence": "Delivered 20 replies outside the intended test budget.",
                                   "evidence_refs": ["private/freeze.json"]}]
            result = d.finish(self.a, review)
        self.assertEqual(result["findings"], review["findings"])
        self.assertEqual(result["resources"]["limits"]["consultant_turns"], 40)
        self.assertEqual(result["outcome"], "incomplete")
        self.assertEqual(d.read(self.a / "state.json")["status"], "finished")
        self.assertEqual((self.a / "freeze.json").read_bytes(), frozen_bytes)

    def test_early_stop5_rejected_without_mutating_conversation(self):
        self.seed(5)
        before=d.inventory(self.a)
        with self.assertRaisesRegex(ValueError,"cannot stop before 8"):
            d.step(self.a,self.reply(True))
        self.assertEqual(before,d.inventory(self.a))
        self.assertEqual(self.assess(5)["outcome"],"incomplete")
    def test_config14_rejected_by_actual_step_before_any_dispatch(self):
        self.seed(5); self.config["limits"]["consultant_turns"]=14
        d.write(self.a / "freeze.json",self.frozen)
        with patch.object(d,"invoke") as invoke, self.assertRaisesRegex(ValueError,"configuration"):
            d.step(self.a,self.reply())
        invoke.assert_not_called()
        self.assertEqual(d.read(self.a / "state.json")["turns"],5)

    def test_new_stress_case_cannot_omit_minimum_before_dispatch(self):
        self.case["edition"] = "case-specific-continuity-stress-v1"
        del self.case["minimum_consultant_replies"]
        d.write(self.a / "freeze.json", self.frozen)
        before = d.inventory(self.a)
        with patch.object(d, "invoke") as invoke, self.assertRaisesRegex(ValueError, "requires minimum_consultant_replies"):
            d.step(self.a, self.reply())
        invoke.assert_not_called()
        self.assertEqual(d.inventory(self.a), before)
    def test_report12_permits_final_actor_stop(self):
        self.seed(11)
        with patch.object(d,"invoke",side_effect=self.invoke):
            self.assertEqual(d.step(self.a,self.reply())["status"],"ready")
        self.state=d.read(self.a / "state.json")
        self.assertEqual(d.delivered_reply_count(self.a),12)
        self.assertEqual(d.step(self.a,self.reply(True))["status"],"awaiting_review")
        self.state=d.read(self.a / "state.json")
        self.assertEqual(self.assess(12)["outcome"],"objective_met")
        self.assertFalse((self.a / "events/013").exists())
    def test_nonstop12_never_dispatches13_and_is_incomplete(self):
        self.seed(12)
        with patch.object(d,"invoke") as invoke:
            self.assertEqual(d.step(self.a,self.reply())["status"],"limit_reached")
        invoke.assert_not_called()
        self.state=d.read(self.a / "state.json")
        self.assertEqual(self.assess(12)["outcome"],"incomplete")
        self.assertFalse((self.a / "events/013").exists())
    def test_no_report12_incomplete(self):
        self.seed(12)
        self.assertEqual(self.assess(12,report=False)["outcome"],"incomplete")
    def test_unrelated_unobserved12_quality_inconclusive_not_incomplete(self):
        self.seed(12)
        self.config["mode"]="verified_host"
        review=self.review(unobserved=True)
        review["host_checks"]={key:{"verified":True,"reason":"Mock retained host evidence.","evidence_refs":["private/host/mock"]}
                               for key in ("candidate_loading","exact_resume","private_isolation","role_separation")}
        result=d.assess(review,self.state,self.frozen,{"sha256":"test","files":{"p":"hash","private/host/mock":"hash"}},
                        completion_check={"satisfied":True},delivered_replies=12)
        self.assertEqual(result["test_validity"],"valid")
        self.assertEqual(result["outcome"],"objective_met")
        self.assertEqual(result["quality_rating"],"inconclusive")
    def test_review_explicit_incomplete12_preserved(self):
        self.seed(12)
        review=self.review();review["outcome"]="incomplete"
        review["stop_reason"]="The required public audience revision did not occur."
        result=d.assess(review,self.state,self.frozen,{"sha256":"test","files":{"p":"hash"}},
                        completion_check={"satisfied":True},delivered_replies=12)
        self.assertEqual(result["outcome"],"incomplete")
        self.assertEqual(result["coverage"]["stress-gap"]["status"],"observed")
    def test_observed_consultant_failure_is_quality_fail(self):
        self.seed(12)
        review=self.review()
        review["findings"]=[{"owner":"consultant","severity":"material","criterion":"stress-gap",
                             "description":"A delivered revision was lost.","consequence":"The report ignored the client preference.","evidence_refs":["p"]}]
        result=d.assess(review,self.state,self.frozen,{"sha256":"test","files":{"p":"hash"}},
                        completion_check={"satisfied":True},delivered_replies=12)
        self.assertEqual(result["outcome"],"objective_met")
        self.assertEqual(result["quality_rating"],"fail")
    def test_ordinary5_still_accepts_stop_and_success(self):
        self.seed(5); del self.case["minimum_consultant_replies"]
        self.case["run_limits"]["consultant_turns"] = 14
        self.config["limits"]["consultant_turns"] = 14
        del self.actor["consultant_reply_bounds"]
        d.write(self.a / "case/actor.json", self.actor)
        d.write(self.a / "freeze.json",self.frozen)
        self.assertEqual(d.step(self.a,self.reply(True))["status"],"awaiting_review")
        self.state=d.read(self.a / "state.json")
        self.assertEqual(self.assess(5)["outcome"],"objective_met")
        self.assertNotIn("delivered_consultant_replies",d.actor_view(self.a,self.state))
    def test_failed_dispatch_not_delivered_and_cannot_retry(self):
        self.seed(4)
        def failure(*args):
            value=self.invoke(*args);value.update(error="provider_error",message=None)
            d.write(args[-1] / "transport.json",value);return value
        with patch.object(d,"invoke",side_effect=failure):
            self.assertEqual(d.step(self.a,self.reply())["status"],"execution_error")
        self.state=d.read(self.a / "state.json")
        self.assertEqual(self.state["turns"],5)
        self.assertEqual(d.delivered_reply_count(self.a),4)
        self.assertEqual(self.assess(4)["outcome"],"execution_error")
        with self.assertRaisesRegex(ValueError,"cannot send"):
            d.step(self.a,self.reply())
    def test_rejected_actor_reply_does_not_consume_round(self):
        self.seed(7); reply=self.reply();reply["fact_ids"]=["invented"]
        with self.assertRaisesRegex(ValueError,"unknown"):
            d.step(self.a,reply)
        self.assertEqual(d.delivered_reply_count(self.a),7)
        with patch.object(d,"invoke",side_effect=self.invoke):
            d.step(self.a,self.reply())
        self.assertEqual(d.delivered_reply_count(self.a),8)
    def test_dynamic_actor_bundle_has_count_and_budget(self):
        self.seed(11)
        bundle=d.actor_view(self.a,self.state)
        self.assertEqual(bundle["delivered_consultant_replies"],11)
        self.assertEqual(bundle["remaining_consultant_replies"],1)
    def test_direct_human_cancel_review_can_end_early_incomplete(self):
        self.seed(3)
        review=self.review();review["outcome"]="incomplete";review["stop_reason"]="Human cancelled."
        result=d.assess(review,self.state,self.frozen,{"sha256":"test","files":{"p":"hash"}},completion_check={"satisfied":False},delivered_replies=3)
        self.assertEqual(result["outcome"],"incomplete")

    def finish_review(self, n, outcome="objective_met"):
        self.seed(n)
        d.write(self.a / "case/reviewer.json", self.frozen["reviewer_packet"])
        observations={"machine_findings":[],"completion_check":{"satisfied":True},
                      "consultation_loop_check":{"status":"no_structural_breach","findings":[]},"missing_captures":[]}
        d.write(self.a / "review-observations.json",observations)
        index={"sha256":"test","files":{"p":"hash"},"observations_sha256":d.digest(self.a / "review-observations.json")}
        d.write(self.a / "review-index.json",index)
        review=self.review();review["outcome"]=outcome
        review["observations_sha256"]=index["observations_sha256"]
        with patch.object(d,"evidence",return_value=index), patch.object(d,"review_observations",return_value=observations):
            return d.finish(self.a,review)
    def test_actual_finish_recounts_delivered_and_prevents_early_success(self):
        result=self.finish_review(5)
        self.assertEqual(result["outcome"],"incomplete")
        self.assertEqual(d.read(self.a / "state.json")["status"],"finished")

    def test_actual_finish_cannot_bypass_new_edition_minimum(self):
        self.case["edition"] = "case-specific-continuity-stress-v1"
        del self.case["minimum_consultant_replies"]
        d.write(self.a / "freeze.json", self.frozen)
        with self.assertRaisesRegex(ValueError, "requires minimum_consultant_replies"):
            self.finish_review(5)
        self.assertEqual(d.read(self.a / "state.json")["status"], "ready")
        self.assertFalse((self.a / "assessment.json").exists())
    def test_actual_finish_allows_human_cancel_early(self):
        result=self.finish_review(3,"incomplete")
        self.assertEqual(result["outcome"],"incomplete")
        self.assertEqual(d.read(self.a / "state.json")["status"],"finished")
    def test_actual_finish_allows_complete_report12(self):
        result=self.finish_review(12)
        self.assertEqual(result["outcome"],"objective_met")
        self.assertEqual(d.read(self.a / "state.json")["status"],"finished")

    def test_actual_finish_accepts_minimum8_and_rejects_above12(self):
        self.assertEqual(self.finish_review(8)["outcome"], "objective_met")
        self.state["status"] = "ready"
        self.assertEqual(self.finish_review(13)["outcome"], "incomplete")

    def test_delivery_needs_matching_successful_retained_transport(self):
        self.seed(8)
        d.write(self.a / "events/002/public.json", {"assistant": " "})
        d.write(self.a / "events/003/transport/transport.json", {"error": "provider_error", "message": "Delivered."})
        d.write(self.a / "events/004/transport/transport.json", {"error": None, "message": "Different."})
        d.write(self.a / "events/005/transport/transport.json", {"message": "Delivered."})
        (self.a / "events/006/transport/transport.json").unlink()
        d.write(self.a / "events/007/public.json", {"assistant": None})
        self.assertEqual(d.delivered_reply_count(self.a), 2)
        before = d.inventory(self.a)
        with self.assertRaisesRegex(ValueError, "cannot stop before 8"):
            d.step(self.a, self.reply(True))
        self.assertEqual(d.inventory(self.a), before)

    def test_missing_or_mismatched_actor_bounds_rejected_before_dispatch(self):
        for bounds in (None, {}, {"minimum": 8, "maximum": 14}, {"minimum": 8.0, "maximum": 12}):
            with self.subTest(bounds=bounds):
                actor = copy.deepcopy(self.actor)
                if bounds is None:
                    del actor["consultant_reply_bounds"]
                else:
                    actor["consultant_reply_bounds"] = bounds
                d.write(self.a / "case/actor.json", actor)
                before = d.inventory(self.a)
                with patch.object(d, "invoke") as invoke, self.assertRaisesRegex(ValueError, "actor bounds"):
                    d.step(self.a, self.reply())
                invoke.assert_not_called()
                self.assertEqual(d.inventory(self.a), before)

    def test_preflight_checks_actual_config_cap_before_candidate_validation(self):
        config = {**self.config, "node_command": ["node"], "candidate_loading": "adapter",
                  "limits": {**self.config["limits"], "consultant_turns": 14}}
        probe = type("Probe", (), {"returncode": 0, "stdout": b"22.0.0", "stderr": b""})()
        with patch.object(d, "validate_config"), patch.object(d, "validate_case", return_value=self.case), \
                patch.object(d.subprocess, "run", return_value=probe), patch.object(d, "candidate_inventory") as inventory:
            with self.assertRaisesRegex(ValueError, "actual run configuration"):
                d.preflight(self.a / "case", self.a / "candidate", config)
            inventory.assert_not_called()


class FrozenRunnerMechanics(unittest.TestCase):
    """Synthetic attempts with real integrity, actor binding and retrospective review.

    Only consultant transport and per-dispatch project observation are mocked.
    These fixtures do not perform startup admission or replay an archived runner.
    """

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def attempt(self, identity="forest-planning", cap=40, mismatch=False, turns=0):
        a = self.root / f"{identity}-{cap}-{int(mismatch)}-{turns}"
        (a / "case/public").mkdir(parents=True)
        (a / "events").mkdir()
        (a / "testing/references").mkdir(parents=True)
        (a / "testing/scripts").mkdir()
        (a / "testing/references/user-simulator.md").write_text("Synthetic reply policy.", encoding="utf-8")
        original = d.read(ROOT / "interactive-test/standalone" / identity / "case.json")
        case = {key: original[key] for key in ("case_id", "edition", "run_limits", "completion_contract", "reply_limits")}
        case.update(actor="actor.json", reviewer="reviewer.json", initial_message="public/initial.txt", sources=[])
        initial = (ROOT / "interactive-test/standalone" / identity / original["initial_message"]).read_text(encoding="utf-8")
        (a / "case/public/initial.txt").write_text(initial, encoding="utf-8")
        d.write(a / "case/actor.json", {"facts": [], "rules": []})
        d.write(a / "case/reviewer.json", {"criteria": [{"id": "planning", "required": True}]})
        case["files"] = d.inventory(a / "case")
        d.write(a / "case/case.json", case)
        skill = a / "work/.claude/skills/causal-consultant"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("Synthetic candidate identity only.", encoding="utf-8")
        runner = a / "testing/scripts/session_driver.py"
        runner.write_bytes(Path(d.__file__).read_bytes() + (b"\n# Synthetic different frozen runner.\n" if mismatch else b""))
        frozen = {"case_manifest": case, "case_sha256": d.digest(a / "case/case.json"),
                  "configuration": {"limits": {"consultant_turns": cap, "active_seconds": 1000, "elapsed_seconds": 1000},
                                    "call_timeout_seconds": 10, "mode": "diagnostic"},
                  "candidate_files": d.inventory(skill), "adapter_files": {"session_driver.py": d.digest(runner)}}
        d.write(a / "freeze.json", frozen)
        d.write(a / "state.json", {"status": "ready", "turns": turns, "work": str(a / "work"),
                                  "session_id": "synthetic-consultant", "started_at": time.time() if turns else None,
                                  "active_seconds": 0, "breaches": [], "public_files": {}, "released_sources": []})
        for number in range(1, turns + 1):
            event = a / "events" / f"{number:03d}"
            (event / "transport").mkdir(parents=True)
            d.write(event / "actor.json", self.reply(a))
            d.write(event / "public.json", {"user": "Please explain.", "assistant": "Synthetic delivered reply."})
            d.write(event / "transport/transport.json", {"error": None, "message": "Synthetic delivered reply."})
        return a

    def reply(self, a, stop=False):
        return {"message": None if stop else (a / "case/public/initial.txt").read_text(encoding="utf-8"),
                "fact_ids": [], "rule_ids": [], "attachments": [], "unanswered_questions": [], "fixture_gaps": [], "stop": stop}

    def bound_stop(self, a):
        reply = self.reply(a, stop=True)
        reply["actor_context"] = {"input_sha256": d.inspect(a, "actor")["input_sha256"], "context_id": "synthetic-actor"}
        return reply

    def invoke(self, *args):
        output = args[-1]
        output.mkdir()
        result = {"active_seconds": 0.01, "message": "Synthetic delivered reply.", "error": None}
        d.write(output / "transport.json", result)
        return result

    def test_initial_dispatch_planning_caps_for_all_four_cases(self):
        self.assertEqual(len(PLANNING_IDS), 4)
        for identity in PLANNING_IDS:
            for cap in (40, 12):
                with self.subTest(case=identity, cap=cap):
                    a = self.attempt(identity, cap=cap)
                    reply = self.reply(a)
                    before = d.inventory(a)
                    with patch.object(d, "invoke", side_effect=self.invoke) as invoke, patch.object(d, "observe_project"):
                        if cap == 40:
                            with self.assertRaisesRegex(ValueError, "planning run configuration"):
                                d.step(a, reply)
                            invoke.assert_not_called()
                            self.assertEqual(d.inventory(a), before)
                        else:
                            self.assertEqual(d.step(a, reply)["status"], "ready")
                            invoke.assert_called_once()
                            self.assertTrue(invoke.call_args.args[3])  # First invocation, not resume.
                            self.assertEqual(invoke.call_args.args[4], reply["message"])
                            self.assertEqual(d.read(a / "state.json")["turns"], 1)
                            self.assertEqual(d.delivered_reply_count(a), 1)

    def test_matching_runner_cap40_stop_requires_bound_actor_input(self):
        a = self.attempt(turns=1)
        reply = self.bound_stop(a)
        invalid = [self.reply(a, stop=True), copy.deepcopy(reply)]
        invalid[1]["actor_context"]["context_id"] = "synthetic-consultant"
        with patch.object(d, "invoke") as invoke:
            for candidate, error in zip(invalid, ("later replies require", "contexts must be separate")):
                with self.subTest(error=error):
                    before = d.inventory(a)
                    with self.assertRaisesRegex(ValueError, error):
                        d.step(a, candidate)
                    self.assertEqual(d.inventory(a), before)
            frozen_bytes = (a / "freeze.json").read_bytes()
            self.assertEqual(d.step(a, reply)["status"], "awaiting_review")
        invoke.assert_not_called()
        self.assertEqual(d.read(a / "events/002-stop.json"), reply)
        self.assertEqual(d.read(a / "state.json")["turns"], 1)
        self.assertEqual((a / "freeze.json").read_bytes(), frozen_bytes)

    def test_matching_planning_runner_accepts_bound_stop_at12_without_dispatch13(self):
        a = self.attempt(cap=12, turns=12)
        reply = self.bound_stop(a)
        with patch.object(d, "invoke") as invoke:
            self.assertEqual(d.step(a, reply)["status"], "awaiting_review")
        invoke.assert_not_called()
        self.assertEqual(d.read(a / "state.json")["turns"], 12)
        self.assertEqual(d.delivered_reply_count(a), 12)
        self.assertEqual(d.read(a / "events/013-stop.json"), reply)
        self.assertFalse((a / "events/013").exists())

    def test_mismatched_runner_cap40_stop_rejected_without_mutation(self):
        a = self.attempt(mismatch=True, turns=1)
        reply = self.bound_stop(a)
        before = d.inventory(a)
        with patch.object(d, "invoke") as invoke, self.assertRaisesRegex(ValueError, "adapter changed during attempt"):
            d.step(a, reply)
        invoke.assert_not_called()
        self.assertEqual(d.inventory(a), before)
        self.assertEqual(d.read(a / "state.json")["status"], "ready")

    def test_mismatched_runner_evidence_can_finish_with_frozen_cap40(self):
        a = self.attempt(mismatch=True, turns=1)
        frozen_bytes = (a / "freeze.json").read_bytes()
        with patch.object(d, "invoke") as invoke:
            inspected = d.inspect(a, "reviewer")
            observations = inspected["observations"]
            # This deliberately incomplete synthetic capture must remain visible.
            self.assertEqual({item["check"] for item in observations["machine_findings"]}, {"capture_completeness"})
            review = {"evidence_sha256": inspected["evidence_sha256"],
                      "observations_sha256": inspected["observations_sha256"], "reviewer": "synthetic reviewer",
                      "test_validity": "invalid", "test_validity_reason": "Synthetic mechanics fixture; no host execution.",
                      "outcome": "incomplete", "stop_reason": "Historical identity and cap retained for review.",
                      "coverage": {"planning": {"status": "unobserved", "reason": "No consultation was evaluated."}},
                      "findings": [{"owner": "harness", "severity": "material", "criterion": "planning",
                                    "description": "Frozen configuration permits 40 replies against a case ceiling of 12.",
                                    "consequence": "This configuration exceeds the intended planning budget.",
                                    "evidence_refs": ["private/freeze.json"]}],
                      "machine_finding_dispositions": {item["id"]: {"status": "confirmed",
                          "reason": "The synthetic fixture omits full transport and project captures.",
                          "evidence_refs": ["private/events/001/public.json"]} for item in observations["machine_findings"]}}
            result = d.finish(a, review)
        invoke.assert_not_called()
        self.assertEqual(result["outcome"], "incomplete")
        self.assertEqual(result["quality_rating"], "inconclusive")
        self.assertEqual(result["findings"], review["findings"])
        self.assertEqual(result["resources"]["limits"]["consultant_turns"], 40)
        self.assertEqual(d.read(a / "state.json")["status"], "finished")
        self.assertEqual((a / "freeze.json").read_bytes(), frozen_bytes)


class BoundValidation(unittest.TestCase):
    def test_planning_admission_requires_integer_frozen_and_configured12(self):
        case = {"edition": "prospective-single-question", "run_limits": {"consultant_turns": 12}}
        invalid_limits = (None, {}, {"consultant_turns": True}, {"consultant_turns": 12.0},
                          {"consultant_turns": 11}, {"consultant_turns": 40})
        for limits in invalid_limits:
            with self.subTest(manifest_limits=limits), self.assertRaisesRegex(ValueError, "planning case"):
                d.validate_reply_bounds({**case, "run_limits": limits}, enforce_planning_cap=True)
            with self.subTest(config_limits=limits), self.assertRaisesRegex(ValueError, "planning run configuration"):
                d.validate_reply_bounds(case, config={"limits": limits}, enforce_planning_cap=True)
        d.validate_reply_bounds(case, config={"limits": {"consultant_turns": 12}}, enforce_planning_cap=True)
        # Assessment has no new admission gate, and cannot rewrite historical configuration.
        config = {"limits": {"consultant_turns": 40}}
        d.validate_reply_bounds(case, config=config)
        self.assertEqual(config["limits"]["consultant_turns"], 40)

    def test_new_stress_edition_requires_minimum(self):
        for case in ({"edition": "case-specific-continuity-stress-v1"},
                     {"edition": "case-specific-continuity-stress-v1", "run_limits": {"consultant_turns": 12}}):
            with self.subTest(case=case), self.assertRaisesRegex(ValueError, "requires minimum_consultant_replies"):
                d.validate_reply_bounds(case)

    def test_manifest_requires_exact_integer_bounds(self):
        valid = {"minimum_consultant_replies": 8, "run_limits": {"consultant_turns": 12}}
        for minimum in (True, 8.0, "8", None, 7, 9):
            with self.subTest(minimum=minimum), self.assertRaisesRegex(ValueError, "8 to 12"):
                d.validate_reply_bounds({**valid, "minimum_consultant_replies": minimum})
        for limits in (None, {}, {"consultant_turns": True}, {"consultant_turns": 12.0}, {"consultant_turns": 14}):
            with self.subTest(limits=limits), self.assertRaisesRegex(ValueError, "8 to 12"):
                d.validate_reply_bounds({**valid, "run_limits": limits})
        d.validate_reply_bounds(valid)

    def test_missing_or_noninteger_config_caps_have_clear_error(self):
        case = {"minimum_consultant_replies": 8, "run_limits": {"consultant_turns": 12}}
        for config in ({}, {"limits": None}, {"limits": {}}, {"limits": {"consultant_turns": True}},
                       {"limits": {"consultant_turns": 12.0}}, {"limits": {"consultant_turns": 14}}):
            with self.subTest(config=config), self.assertRaisesRegex(ValueError, "actual run configuration"):
                d.validate_reply_bounds(case, config=config)

    def test_absent_minimum_preserves_ordinary_and_old_frozen_bounds(self):
        for cap in (14, 40):
            d.validate_reply_bounds({"edition": "case-specific-continuity-v1", "run_limits": {"consultant_turns": cap}}, {},
                                    {"limits": {"consultant_turns": cap}})
            d.validate_reply_bounds({"edition": "case-specific-continuity-v1", "run_limits": {"consultant_turns": cap}}, {},
                                    {"limits": {"consultant_turns": cap}}, enforce_planning_cap=True)

    def test_real_case_validator_checks_frozen_actor_agreement(self):
        with tempfile.TemporaryDirectory() as temporary:
            case = Path(temporary) / "case"
            manifest = c.compose_case("rggvy-electrification", output=case)
            manifest["minimum_consultant_replies"] = 8
            manifest["run_limits"]["consultant_turns"] = 12
            actor = d.read(case / "actor.json")
            actor["consultant_reply_bounds"] = {"minimum": 8, "maximum": 12}
            d.write(case / "actor.json", actor)
            manifest["files"] = d.inventory(case)
            del manifest["files"]["case.json"]
            d.write(case / "case.json", manifest)
            check = type("Check", (), {"returncode": 0, "stderr": b""})()
            with patch.object(d.subprocess, "run", return_value=check):
                self.assertEqual(d.validate_case(case), manifest)
            actor["consultant_reply_bounds"]["maximum"] = 14
            d.write(case / "actor.json", actor)
            manifest["files"] = d.inventory(case)
            del manifest["files"]["case.json"]
            d.write(case / "case.json", manifest)
            with self.assertRaisesRegex(ValueError, "actor bounds"):
                d.validate_case(case)


if __name__ == "__main__":
    unittest.main(verbosity=2)
