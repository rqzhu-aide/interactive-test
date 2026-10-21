import copy
import json
from pathlib import Path
import py_compile
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import session_driver as driver
from compose_case import compose_case


class InventoryTests(unittest.TestCase):
    def test_oracle_bytecode_does_not_change_fixture_or_composed_case_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bank = root / "problems"
            problem = bank / "study-design"
            shutil.copytree(ROOT / "problems/study-design", problem,
                            ignore=shutil.ignore_patterns("__pycache__"))
            before = driver.inventory(problem)
            cached = Path(py_compile.compile(str(problem / "check_oracle.py"), doraise=True))
            self.assertTrue(cached.is_file())  # Explicit compile also works under python -B.
            self.assertEqual(driver.inventory(problem), before)
            case = root / "case"
            manifest = compose_case("study-design", "standard", case, bank_root=bank)
            self.assertFalse(list(case.rglob("__pycache__")))
            py_compile.compile(str(case / "check_oracle.py"), doraise=True)
            self.assertEqual(driver.validate_case(case), manifest)

            # The cache directory is not a hiding place for scientific content.
            unexpected = cached.parent / "result.json"
            unexpected.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "problem file identity mismatch"):
                compose_case("study-design", "standard", root / "unexpected", bank_root=bank)
            self.assertFalse((root / "unexpected").exists())


class SessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = ROOT.parent / "causal-consultant"
        cls.node = shutil.which("node")
        if not cls.node or not cls.candidate.is_dir():
            raise RuntimeError("Integration tests require a shared Node and the sibling consultant " +
                               ", ".join(driver.CONSULTANT_VERSIONS) + " package")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.case = self.root / "case"
        compose_case("observational-did", "standard", self.case)
        self.attempt, self.work = self.root / "private", self.root / "work"
        self.config = {"claude_command": [sys.executable, str(ROOT / "tests/fake_claude.py"), "ok"],
                       "candidate_loading": "adapter",
                       "node_command": [self.node], "max_agent_turns_per_call": 10,
                       "call_timeout_seconds": 10, "mode": "diagnostic",
                       "limits": {"consultant_turns": 10, "active_seconds": 60, "elapsed_seconds": 120}}

    def begin(self):
        return driver.start(self.case, self.candidate, self.config, self.attempt, self.work)

    def begin_legacy_observer_fixture(self):
        # saved_run uses the retained lib/store.cjs v7 codec. Select its observer
        # only for these legacy fixtures, keeping the installed candidate intact.
        profile = {"consultant_version": driver.read(self.candidate / "package.json")["version"],
                   "profile": driver.LOOP_CAPABILITY, "enforcement": "observational_only",
                   "consultation_loop": True, "agent_recorded_reply": False,
                   "public_presentation": "four-section-responses-v1",
                   "public_presentation_renderer": "lead-markdown-v11"}
        with patch.object(driver, "candidate_observation_profile", return_value=profile):
            return self.begin()

    def test_fresh_loading_choice_is_required_without_guessing_command_identity(self):
        del self.config["candidate_loading"]
        for argv in (["claude"], ["a-wrapper"], ["python", "adapter.py"]):
            self.config["claude_command"] = argv
            with self.subTest(argv=argv), patch.object(driver.subprocess, "run") as run:
                with self.assertRaisesRegex(ValueError, "new attempts require candidate_loading"):
                    driver.preflight(self.case, self.candidate, self.config)
                run.assert_not_called()

    def test_fresh_native_choice_is_frozen_and_shown_before_dispatch(self):
        self.config.update(claude_command=["explicitly-selected-native"], candidate_loading="claude_explicit")
        with patch.object(driver, "capture", return_value={"error": None, "exit_code": 0}):
            result = self.begin()
        frozen = driver.read(self.attempt / "freeze.json")
        self.assertEqual(frozen["configuration"]["candidate_loading"], "claude_explicit")
        self.assertEqual(result["loading_setup"], frozen["loading_setup"])
        self.assertFalse(result["initial_message_sent"])
        self.assertEqual(driver.read(self.attempt / "state.json")["turns"], 0)

    def test_deliberate_discovery_cannot_claim_verified_host(self):
        self.config.update(candidate_loading="diagnostic_discovery", mode="verified_host")
        with self.assertRaisesRegex(ValueError, "diagnostic_discovery requires diagnostic mode"):
            driver.preflight(self.case, self.candidate, self.config)
        self.config["mode"] = "diagnostic"
        result = self.begin()
        self.assertEqual(result["loading_setup"]["candidate_loading"], "diagnostic_discovery")

    def test_historical_omitted_loading_config_continues_without_reconfiguration(self):
        self.begin()
        frozen = driver.read(self.attempt / "freeze.json")
        del frozen["configuration"]["candidate_loading"]
        del frozen["loading_setup"]
        driver.write(self.attempt / "freeze.json", frozen)
        driver.step(self.attempt, self.reply(True))
        driver.step(self.attempt, self.reply())
        state = driver.read(self.attempt / "state.json")
        self.assertEqual(state["turns"], 2)
        self.assertNotIn("candidate_loading", driver.read(self.attempt / "freeze.json")["configuration"])

    def reply(self, initial=False, **updates):
        record = {"message": (self.case / "public/initial-message.txt").read_text() if initial else "I cannot obtain additional office records.",
                  "fact_ids": [] if initial else ["f-record-access"], "rule_ids": [] if initial else ["r-known-facts"],
                  "attachments": [], "unanswered_questions": [], "fixture_gaps": [], "stop": False}
        if not initial and (self.attempt / "state.json").is_file() and driver.read(self.attempt / "state.json")["status"] == "ready":
            record["actor_context"] = {"input_sha256": driver.inspect(self.attempt, "actor")["input_sha256"],
                                       "context_id": "synthetic-actor-context"}
        return {**record, **updates}

    def manifest(self, *changed_problem_files):
        # Intentional test-only contract/identity overrides must also bind the
        # copied problem's inventory. Never refresh source or numerical hashes.
        if changed_problem_files:
            self.assertTrue(set(changed_problem_files) <= {"reviewer.json", "world.json"})
            problem = driver.read(self.case / "problem.json")
            for name in changed_problem_files:
                problem["files"][name] = driver.digest(self.case / name)
            driver.write(self.case / "problem.json", problem)
        manifest = driver.read(self.case / "case.json")
        manifest["files"] = {name: sha for name, sha in driver.inventory(self.case).items() if name != "case.json"}
        driver.write(self.case / "case.json", manifest)

    def assessment(self):
        view = driver.inspect(self.attempt, "reviewer")
        return {"evidence_sha256": view["evidence_sha256"], "test_validity": "valid", "outcome": "objective_met",
                "test_validity_reason": "Synthetic reviewer validity note.",
                "observations_sha256": view["observations_sha256"],
                "machine_finding_dispositions": {f["id"]: {"status": "confirmed", "reason": "Synthetic test accepts the observed check.",
                    "evidence_refs": ["private/events/001/public.json"]} for f in view["observations"]["machine_findings"]},
                "stop_reason": "Test-only reviewer assertion", "reviewer": "test-double",
                "coverage": {c["id"]: {"status": "observed", "reason": "Test-only coverage", "evidence_refs": ["private/events/001/public.json"]}
                             for c in driver.read(self.case / "reviewer.json")["criteria"]}, "findings": []}

    def full_report_case(self):
        manifest = driver.read(self.case / "case.json")
        manifest["completion_contract"] = "full_report"
        driver.write(self.case / "case.json", manifest)
        reviewer = driver.read(self.case / "reviewer.json")
        reviewer["useful_stop"] = True  # Exercise both otherwise-successful review outcomes.
        driver.write(self.case / "reviewer.json", reviewer)
        self.manifest("reviewer.json")

    def focused_endpoint(self):
        """Change only this temporary test's delivery contract, never its study facts."""
        manifest = driver.read(self.case / "case.json")
        manifest["completion_contract"] = "focused"
        driver.write(self.case / "case.json", manifest)

    def saved_run(self, run_id="report-main", status="completed", content="<html><body>Test-only report.</body></html>",
                  kind="report", project_root="consultation", prepare_only=False, offered=None):
        """Produce real helper artifacts; recorded fixture consent is not actual public consent."""
        script = r"""
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const [scripts, root] = process.argv.slice(1);
const spec = JSON.parse(fs.readFileSync(0, 'utf8'));
const store = require(path.join(scripts, 'lib/store.cjs'));
const runs = require(path.join(scripts, 'lib/runs.cjs'));
const current = () => store.status(root).project.state_meta;
const ids = event_id => ({event_id, expected_project_id: current().project_id, expected_last_event_id: current().last_event_id});
if (!fs.existsSync(path.join(root, 'journal.jsonl'))) {
  store.init(root, {event_id:'event-init', project_id:'project-test', project_understanding:{objective:'Test-only report evidence'}});
  store.record(root, {...ids('event-source'), type:'memory_updated', payload:{changes:{evidence:[{
    evidence_id:'source-data', kind:'file', source_ref:'panel.csv', summary:'Frozen public input for a structural test.',
    source_sha256:crypto.createHash('sha256').update(fs.readFileSync(spec.source)).digest('hex')
  }]}}});
}
let plan = {kind:spec.kind, objective:'Save a test-only artifact.', claim_boundary:'Structural test only.',
  inputs:[{source_ref:'panel.csv',path:spec.source}],
  ...(spec.kind === 'report' ? {purpose:'Test report completion.',evidence_refs:['source-data'],format:'html'} :
    {question:'Test an audit artifact.',diagnostics:[]})};
if (store.capabilities().capabilities.includes('consultation-loop-v1')) {
  plan = require(spec.fixture)(scripts, root, plan, spec.run_id, spec.offered, spec.prepare_only);
  if (spec.prepare_only) { process.stdout.write(JSON.stringify(plan)); process.exit(0); }
}
const start = plan.scope_ref && store.capabilities().capabilities.includes('concise-authoring-v1')
  ? {scope_ref:plan.scope_ref,interpretation_ref:plan.interpretation_ref,authorization_ref:plan.authorization_ref} : {plan};
runs.start(root, {...ids('event-start-'+spec.run_id),run_id:spec.run_id,...start});
const {event_id, ...writeIds} = ids('unused');
runs.write(root, {...writeIds,run_id:spec.run_id,path:'report.html',content:spec.content});
if (spec.status === 'completed') {
  runs.finalize(root, {...ids('event-final-'+spec.run_id),run_id:spec.run_id,code_paths:[],output_paths:['report.html'],
    diagnostic_paths:[],environment:{test_only:true},deviations:[],
    ...(spec.kind === 'report' && store.capabilities().capabilities.includes('report-deliverables-v1')
      ? {deliverable:{primary:'report.html',companions:[],assets:[]}} : {})});
} else if (spec.status !== 'in_progress') {
  const terminal = spec.status === 'failed' ? runs.failRun : runs.abandon;
  terminal(root, {...ids('event-terminal-'+spec.run_id),run_id:spec.run_id,reason:'Test-only unfinished revision.'});
}
process.stdout.write(JSON.stringify(store.status(root)));
"""
        result = subprocess.run([self.node, "-e", script,
                                 str(self.work / ".claude/skills/causal-consultant/scripts"), str(self.work / project_root)],
                                input=json.dumps({"run_id": run_id, "status": status, "content": content,
                                                  "kind": kind, "source": str(self.work / "panel.csv"),
                                                  "fixture": str(ROOT / "tests/fixtures/current_policy.cjs"),
                                                  "prepare_only": prepare_only, "offered": offered}),
                                text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def completion_check(self):
        state = driver.read(self.attempt / "state.json")
        return driver.full_report_completion(self.attempt, state, driver.evidence(self.attempt, state))

    def test_stages_complete_candidate_and_public_only_then_resumes(self):
        result = self.begin()
        self.assertFalse(result["initial_message_sent"])
        self.assertFalse((self.work / "fake-session.txt").exists())
        self.assertTrue((self.work / ".claude/skills/causal-consultant/package.json").is_file())
        self.assertEqual(driver.digest(self.work / "panel.csv"), driver.digest(self.case / "public/panel.csv"))
        self.assertFalse((self.work / "actor.json").exists())
        driver.step(self.attempt, self.reply(initial=True))
        driver.step(self.attempt, self.reply())
        actor = driver.inspect(self.attempt, "actor")
        self.assertEqual(len(actor["conversation"]), 2)
        self.assertEqual(set(actor), {"conversation", "public_files", "actor_disclosures", "actor_packet", "reply_policy", "public_file_hashes", "input_sha256"})
        self.assertEqual(actor["actor_disclosures"][-1]["fact_ids"], ["f-record-access"])
        self.assertNotIn("fact_ids", str(actor["conversation"]))
        self.assertEqual(driver.read(self.attempt / "state.json")["turns"], 2)

    def test_word_limit_rejects_actor_reply_before_dispatch(self):
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        with self.assertRaisesRegex(ValueError, "actor message exceeds word limit"):
            driver.step(self.attempt, self.reply(message="word " * 51))
        self.assertEqual(driver.read(self.attempt / "state.json")["turns"], 1)
        self.assertFalse((self.attempt / "events/002").exists())

    def test_missing_package_json_fails_before_consultation(self):
        broken = self.root / "broken"
        shutil.copytree(self.candidate, broken, ignore=shutil.ignore_patterns(".git", "node_modules"))
        (broken / "package.json").unlink()
        with self.assertRaises(FileNotFoundError):
            driver.start(self.case, broken, self.config, self.attempt, self.work)
        self.assertTrue((self.attempt / "startup-error.json").exists())
        self.assertFalse(self.work.exists())

    def test_private_world_identity_and_staging(self):
        manifest = driver.read(self.case / "case.json")
        manifest.update(world="world.json", world_id="world-test", world_version="1.0.0", persona_id="user-test")
        driver.write(self.case / "case.json", manifest)
        actor = driver.read(self.case / "actor.json")
        actor["persona_id"] = "user-test"
        driver.write(self.case / "actor.json", actor)
        world = {**driver.read(self.case / "world.json"), "world_id": "world-test", "world_version": "1.0.0", "private_truth": "TEST_ONLY_PRIVATE_VALUE"}
        driver.write(self.case / "world.json", world)
        self.manifest("world.json")
        driver.validate_case(self.case)
        for changed in ({**world, "world_id": "wrong"}, {**world, "world_version": "2.0.0"}):
            driver.write(self.case / "world.json", changed)
            self.manifest("world.json")
            with self.assertRaisesRegex(ValueError, "world identity mismatch"):
                driver.validate_case(self.case)
        driver.write(self.case / "world.json", world)
        self.manifest("world.json")
        self.begin()
        self.assertFalse((self.work / "world.json").exists())
        self.assertNotIn("TEST_ONLY_PRIVATE_VALUE", json.dumps(driver.inspect(self.attempt, "actor")))
        driver.step(self.attempt, self.reply(initial=True))
        with self.assertRaisesRegex(ValueError, "private path leaked"):
            driver.step(self.attempt, self.reply(message="Please read world.json."))

    def test_private_actor_learning_survives_replies_without_public_leak(self):
        self.begin()
        change = {"subject": "belief-context", "before": "The spreadsheet explains how the policy was introduced.",
                  "after": "The consultant also needs the policy's introduction records.",
                  "evidence": "The consultant's first reply asks which records describe the introduction."}
        with self.assertRaisesRegex(ValueError, "initial dispatch"):
            driver.step(self.attempt, self.reply(initial=True, belief_updates=[change]))
        driver.step(self.attempt, self.reply(initial=True))
        for invalid in ({"belief_updates": {}}, {"knowledge_updates": [{"subject": "x"}]},
                        {"decision_updates": [{**change, "evidence": ""}]},
                        {"belief_updates": [{**change, "extra": "reviewer truth"}]}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                driver.step(self.attempt, self.reply(**invalid))
        driver.step(self.attempt, self.reply(belief_updates=[change]))
        driver.step(self.attempt, self.reply(message="Please explain the available options."))
        visible = driver.inspect(self.attempt, "actor")
        self.assertEqual(visible["actor_updates"], [{"event": "002", "belief_updates": [change]}])
        self.assertEqual(len(visible["conversation"]), 3)
        self.assertNotIn("belief-context", json.dumps(visible["conversation"]))
        sent = (self.attempt / "events/002/transport/request.txt").read_text(encoding="utf-8")
        self.assertNotIn("belief-context", sent)
        self.assertEqual(driver.read(self.attempt / "events/002/actor.json")["belief_updates"], [change])

    def test_actor_resume_retains_disclosures_and_unanswered_questions_without_reviewer_truth(self):
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        outstanding = "Please explain why the introduction records matter before I choose."
        driver.step(self.attempt, self.reply(unanswered_questions=[outstanding]))
        first_view = driver.inspect(self.attempt, "actor")
        self.assertEqual(first_view["actor_disclosures"][-1], {
            "event": "002", "fact_ids": ["f-record-access"], "attachments": [],
            "unanswered_questions": [outstanding], "action_intents": []})
        driver.step(self.attempt, self.reply(message="I am still waiting for that explanation.",
                                           fact_ids=[], unanswered_questions=[outstanding]))
        resumed = driver.inspect(self.attempt, "actor")
        self.assertEqual(resumed["actor_disclosures"][:2], first_view["actor_disclosures"])
        self.assertEqual(resumed["actor_disclosures"][-1]["unanswered_questions"], [outstanding])
        self.assertNotIn("world", resumed)
        self.assertNotIn("reviewer_packet", resumed)
        self.assertNotIn("oracle", resumed)
        self.assertEqual(resumed["actor_packet"], driver.read(self.case / "actor.json"))
        for event in ("002", "003"):
            sent = (self.attempt / "events" / event / "transport/request.txt").read_text(encoding="utf-8")
            self.assertNotIn("f-record-access", sent)
            self.assertNotIn("unanswered_questions", sent)

    def test_candidate_inventory_accepts_only_explicit_compatible_versions(self):
        candidate = self.root / "version-probe"
        candidate.mkdir()
        (candidate / "SKILL.md").write_text("Test-only runtime file.", encoding="utf-8")
        for version in ("7.0.0", "7.0.1", "7.0.2", "7.0.4", "7.0.5", "7.0.6", "7.0.7", "7.0.8", "7.0.9", "7.0.10", "7.0.11", "7.0.12", "7.0.13", "7.2.0", "7.3.0", "7.3.1", "7.4.0", "7.4.1", "7.5.0", "7.5.1", "7.5.2", "7.5.3", "7.5.4", "7.5.5", "7.5.6", "8.0.0", "8.0.1", "8.0.2", "8.0.3", "8.0.4", "8.0.5", "8.0.6", "8.0.7", "8.0.8", "8.0.9", "8.0.10", "8.0.11", "8.0.12", "8.0.13", "8.0.14", "8.0.15"):
            with self.subTest(version=version):
                driver.write(candidate / "package.json", {"version": version, "files": ["SKILL.md"]})
                self.assertEqual(driver.candidate_inventory(candidate), {
                    "SKILL.md": driver.digest(candidate / "SKILL.md"),
                    "package.json": driver.digest(candidate / "package.json")})
        for version in ("6.9.9", "7.0.3", "7.0.14", "7.1.0", "7.0.2-preview", "7.0.4-preview", "7.0.5-preview", "7.0.6-preview", "7.0.7-preview", "7.0.8-preview", "7.0.9-preview", "7.0.10-preview", "7.0.11-preview", "7.0.12-preview", "7.0.13-preview", "7.5.4-preview", "7.5.3-preview", "7.5.2-preview", "8.0.11-preview", "8.0.12-preview", "8.0.13-preview", "8.0.14-preview", "8.0.15-preview", "8.0.16"):
            with self.subTest(version=version):
                driver.write(candidate / "package.json", {"version": version, "files": ["SKILL.md"]})
                with self.assertRaisesRegex(ValueError, "observation profile"):
                    driver.candidate_inventory(candidate)

    def test_v8_profiles_preserve_journal_and_option_word_limits(self):
        candidate = self.root / "v8-profile-probe"
        candidate.mkdir()
        for version, option_limit in (("8.0.0", 100), ("8.0.1", 50), ("8.0.2", 50), ("8.0.3", 50), ("8.0.4", 50), ("8.0.5", 50), ("8.0.6", 50), ("8.0.7", 50), ("8.0.8", 50), ("8.0.9", 50), ("8.0.10", 50), ("8.0.11", 50), ("8.0.12", 50), ("8.0.13", 50), ("8.0.14", 50), ("8.0.15", 50)):
            driver.write(candidate / "package.json", {"version": version})
            capability = {"ok": True, "version": version, "journal_schema": 8,
                          "default_journal_format": driver.V8_FORMAT,
                          "capabilities": sorted(driver.V8_CAPABILITIES)}
            with self.subTest(version=version), patch.object(driver.subprocess, "run") as run:
                run.return_value = subprocess.CompletedProcess([], 0, json.dumps(capability).encode(), b"")
                profile = driver.candidate_observation_profile(candidate, self.config)
                self.assertEqual(profile["consultant_version"], version)
                self.assertEqual(profile["profile"], driver.V8_LOOP_PROFILE)
                self.assertEqual(profile["journal_format"], driver.V8_FORMAT)
                self.assertTrue(profile["consultation_loop"])
                self.assertEqual(profile["public_presentation_renderer"], "lead-markdown-v11")
                self.assertEqual(profile["public_presentation_option_max_words"], option_limit)
                self.assertEqual(profile["enforcement"], "observational_only")

    def test_new_profile_requires_capability_and_preserves_old_profile(self):
        candidate = self.root / "profile-probe"
        candidate.mkdir()
        for version in ("7.0.5", "7.0.6"):
            driver.write(candidate / "package.json", {"version": version})
            for code, body in ((1, {}), (0, {"capabilities": []}), (0, []),
                               (0, {"capabilities": driver.EXCHANGE_CAPABILITY})):
                with self.subTest(version=version, code=code, body=body), patch.object(driver.subprocess, "run") as run:
                    run.return_value = subprocess.CompletedProcess([], code, json.dumps(body).encode(), b"")
                    with self.assertRaisesRegex(ValueError, version + ".*(capability|lacks)"):
                        driver.candidate_observation_profile(candidate, self.config)
            with self.subTest(version=version), patch.object(driver.subprocess, "run") as run:
                run.return_value = subprocess.CompletedProcess([], 0, json.dumps({
                    "capabilities": [driver.EXCHANGE_CAPABILITY]}).encode(), b"")
                profile = driver.candidate_observation_profile(candidate, self.config)
                self.assertEqual(profile["consultant_version"], version)
                self.assertEqual(profile["capabilities"], [driver.EXCHANGE_CAPABILITY])
                self.assertFalse(profile["user_question_routing"])
                self.assertEqual(profile["enforcement"], "observational_only")
                self.assertEqual(run.call_args.args[0][-1], "capabilities")
                run.return_value = subprocess.CompletedProcess([], 0, json.dumps({
                    "capabilities": [driver.EXCHANGE_CAPABILITY, driver.USER_QUESTION_CAPABILITY]}).encode(), b"")
                self.assertTrue(driver.candidate_observation_profile(candidate, self.config)["user_question_routing"])
        with patch.object(driver.subprocess, "run") as run:
            driver.write(candidate / "package.json", {"version": "7.0.4"})
            self.assertEqual(driver.candidate_observation_profile(candidate, self.config)["capabilities"], [])
            run.assert_not_called()

    def test_707_profile_requires_loop_capability_and_keeps_observational_limits(self):
        candidate = self.root / "loop-profile"
        candidate.mkdir()
        driver.write(candidate / "package.json", {"version": "7.0.7"})
        with patch.object(driver.subprocess, "run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, json.dumps({
                "capabilities": [driver.EXCHANGE_CAPABILITY]}).encode(), b"")
            with self.assertRaisesRegex(ValueError, "lacks consultation-loop-v1"):
                driver.candidate_observation_profile(candidate, self.config)
            run.return_value = subprocess.CompletedProcess([], 0, json.dumps({
                "capabilities": [driver.EXCHANGE_CAPABILITY, driver.LOOP_CAPABILITY]}).encode(), b"")
            profile = driver.candidate_observation_profile(candidate, self.config)
            self.assertTrue(profile["consultation_loop"])
            self.assertEqual(profile["enforcement"], "observational_only")

    def test_708_profile_requires_captured_delivery_and_proposal_preflight(self):
        candidate = self.root / "capture-profile"
        candidate.mkdir()
        driver.write(candidate / "package.json", {"version": "7.0.8"})
        required = [driver.EXCHANGE_CAPABILITY, driver.LOOP_CAPABILITY,
                    "captured-delivery-v1", "proposal-preflight-v1"]
        for missing in required:
            with self.subTest(missing=missing), patch.object(driver.subprocess, "run") as run:
                run.return_value = subprocess.CompletedProcess([], 0, json.dumps({
                    "capabilities": [item for item in required if item != missing]}).encode(), b"")
                with self.assertRaisesRegex(ValueError, "7.0.8 consultant lacks " + missing):
                    driver.candidate_observation_profile(candidate, self.config)
        with patch.object(driver.subprocess, "run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, json.dumps({
                "capabilities": required}).encode(), b"")
            profile = driver.candidate_observation_profile(candidate, self.config)
            self.assertTrue(profile["consultation_loop"])
            self.assertTrue(profile["captured_delivery"])
            self.assertTrue(profile["proposal_preflight"])
            self.assertEqual(profile["enforcement"], "observational_only")
            self.assertFalse(profile["intact_reply_recovery"])
            self.assertFalse(profile["source_attributed_memory"])
            run.return_value = subprocess.CompletedProcess([], 0, json.dumps({
                "capabilities": required + ["intact-reply-recovery-v1", "source-attributed-memory-v1"]}).encode(), b"")
            revised = driver.candidate_observation_profile(candidate, self.config)
            self.assertTrue(revised["intact_reply_recovery"])
            self.assertTrue(revised["source_attributed_memory"])

    def test_709_profile_requires_recovery_and_source_attribution_capabilities(self):
        candidate = self.root / "recovery-profile"
        candidate.mkdir()
        driver.write(candidate / "package.json", {"version": "7.0.9"})
        required = [driver.EXCHANGE_CAPABILITY, driver.LOOP_CAPABILITY,
                    "captured-delivery-v1", "proposal-preflight-v1",
                    "intact-reply-recovery-v1", "source-attributed-memory-v1"]
        for missing in required:
            with self.subTest(missing=missing), patch.object(driver.subprocess, "run") as run:
                run.return_value = subprocess.CompletedProcess([], 0, json.dumps({
                    "capabilities": [item for item in required if item != missing]}).encode(), b"")
                with self.assertRaisesRegex(ValueError, "7.0.9 consultant lacks " + missing):
                    driver.candidate_observation_profile(candidate, self.config)
        with patch.object(driver.subprocess, "run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, json.dumps({
                "capabilities": required}).encode(), b"")
            profile = driver.candidate_observation_profile(candidate, self.config)
            for field in ("consultation_loop", "captured_delivery", "proposal_preflight",
                          "intact_reply_recovery", "source_attributed_memory"):
                self.assertTrue(profile[field])
            self.assertEqual(profile["capabilities"], required)
            self.assertEqual(profile["enforcement"], "observational_only")

    def test_7010_profile_preserves_requirements_and_records_memory_extensions(self):
        candidate = self.root / "memory-profile"
        candidate.mkdir()
        driver.write(candidate / "package.json", {"version": "7.0.10"})
        required = [driver.EXCHANGE_CAPABILITY, driver.LOOP_CAPABILITY, "captured-delivery-v1",
                    "proposal-preflight-v1", "intact-reply-recovery-v1", "source-attributed-memory-v1"]
        with patch.object(driver.subprocess, "run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, json.dumps({"capabilities": required}).encode(), b"")
            profile = driver.candidate_observation_profile(candidate, self.config)
            self.assertFalse(profile["compact_proposals"])
            self.assertFalse(profile["reply_reconciliation"])
            run.return_value = subprocess.CompletedProcess([], 0, json.dumps({
                "capabilities": required + ["reply-reconciliation-v1", "case-brief-v1"]}).encode(), b"")
            profile = driver.candidate_observation_profile(candidate, self.config)
            self.assertTrue(profile["reply_reconciliation"])
            self.assertTrue(profile["case_brief"])

    def test_7011_and_7012_profiles_preserve_requirements_and_add_concise_authoring(self):
        candidate = self.root / "compact-profile"
        candidate.mkdir()
        inherited = [driver.EXCHANGE_CAPABILITY, driver.LOOP_CAPABILITY, "captured-delivery-v1",
                     "proposal-preflight-v1", "intact-reply-recovery-v1", "source-attributed-memory-v1",
                     "reply-reconciliation-v1", "compact-proposals-v1"]
        for version in ("7.0.11", "7.0.12"):
            driver.write(candidate / "package.json", {"version": version})
            required = inherited + (["concise-authoring-v1"] if version == "7.0.12" else [])
            for missing in required + ["lead-markdown-v5", None]:
                with self.subTest(version=version, missing=missing), patch.object(driver.subprocess, "run") as run:
                    run.return_value = subprocess.CompletedProcess([], 0, json.dumps({
                        "capabilities": [item for item in required if item != missing],
                        "renderers": [] if missing == "lead-markdown-v5" else ["lead-markdown-v4", "lead-markdown-v5"]}).encode(), b"")
                    if missing:
                        with self.assertRaisesRegex(ValueError, version + " consultant lacks " + missing):
                            driver.candidate_observation_profile(candidate, self.config)
                    else:
                        profile = driver.candidate_observation_profile(candidate, self.config)
                        self.assertTrue(profile["compact_proposals"])
                        self.assertEqual(profile["concise_authoring"], version == "7.0.12")
                        self.assertEqual(profile["enforcement"], "observational_only")
                        if version in ("7.5.3", "7.5.4"):
                            self.assertEqual(profile["public_presentation_renderer"],
                                             "lead-markdown-v10" if version == "7.5.4" else "lead-markdown-v9")

    def test_7013_profile_requires_conversational_responses_and_lead_markdown_v6(self):
        candidate = self.root / "conversational-profile"
        candidate.mkdir()
        required = [driver.EXCHANGE_CAPABILITY, driver.LOOP_CAPABILITY, "captured-delivery-v1",
                    "proposal-preflight-v1", "intact-reply-recovery-v1", "source-attributed-memory-v1",
                    "reply-reconciliation-v1", "compact-proposals-v1", "concise-authoring-v1",
                    "conversational-responses-v1"]
        renderers = ["lead-markdown-v4", "lead-markdown-v5", "lead-markdown-v6"]
        driver.write(candidate / "package.json", {"version": "7.0.13"})
        for missing in required + ["lead-markdown-v5", "lead-markdown-v6", None]:
            with self.subTest(missing=missing), patch.object(driver.subprocess, "run") as run:
                run.return_value = subprocess.CompletedProcess([], 0, json.dumps({
                    "capabilities": [item for item in required if item != missing],
                    "renderers": [item for item in renderers if item != missing]}).encode(), b"")
                if missing:
                    with self.assertRaisesRegex(ValueError, "7.0.13 consultant lacks " + missing):
                        driver.candidate_observation_profile(candidate, self.config)
                else:
                    profile = driver.candidate_observation_profile(candidate, self.config)
                    self.assertTrue(profile["compact_proposals"])
                    self.assertTrue(profile["concise_authoring"])
                    self.assertTrue(profile["conversational_responses"])
                    self.assertEqual(profile["enforcement"], "observational_only")

    def test_720_and_730_profiles_retain_requirements_and_require_deferred_release(self):
        candidate = self.root / "deferred-profile"
        candidate.mkdir()
        required = [driver.EXCHANGE_CAPABILITY, driver.LOOP_CAPABILITY, "captured-delivery-v1",
                    "proposal-preflight-v1", "intact-reply-recovery-v1", "source-attributed-memory-v1",
                    "reply-reconciliation-v1", "compact-proposals-v1", "concise-authoring-v1",
                    "conversational-responses-v1", "deferred-release-v1"]
        renderers = ["lead-markdown-v4", "lead-markdown-v5", "lead-markdown-v6"]
        for version in ("7.2.0", "7.3.0", "7.3.1", "7.4.0", "7.4.1", "7.5.0", "7.5.1", "7.5.2", "7.5.3", "7.5.4"):
            driver.write(candidate / "package.json", {"version": version})
            version_required = required + (["assisted-authoring-v1", "claude-transcript-capture-v1"] if version in ("7.4.0", "7.4.1", "7.5.0", "7.5.1", "7.5.2", "7.5.3", "7.5.4") else [])
            if version in ("7.5.0", "7.5.1", "7.5.2", "7.5.3", "7.5.4"):
                version_required += ["operational-summary-v1", "report-deliverables-v1", "report-presentation-adjustment-v1"]
            version_renderers = renderers + (["lead-markdown-v7"] if version in ("7.5.1", "7.5.2", "7.5.3", "7.5.4") else [])
            if version in ("7.5.2", "7.5.3", "7.5.4"):
                version_renderers += ["lead-markdown-v8"]
            if version in ("7.5.3", "7.5.4"):
                version_required += ["four-section-responses-v1", "message-bound-delivery-v2", "pending-intake-v1"]
                version_renderers += ["lead-markdown-v9"]
            if version == "7.5.4":
                version_required += ["visible-scope-answers-v1"]
                version_renderers += ["lead-markdown-v10"]
            for missing in version_required + version_renderers[1:] + [None]:
                with self.subTest(version=version, missing=missing), patch.object(driver.subprocess, "run") as run:
                    run.return_value = subprocess.CompletedProcess([], 0, json.dumps({
                        "capabilities": [item for item in version_required if item != missing],
                        "renderers": [item for item in version_renderers if item != missing]}).encode(), b"")
                    if missing:
                        with self.assertRaisesRegex(ValueError, version + " consultant lacks " + missing):
                            driver.candidate_observation_profile(candidate, self.config)
                    else:
                        profile = driver.candidate_observation_profile(candidate, self.config)
                        self.assertTrue(profile["conversational_responses"])
                        self.assertTrue(profile["deferred_release"])
                        self.assertEqual(profile["assisted_authoring"], version in ("7.4.0", "7.4.1", "7.5.0", "7.5.1", "7.5.2", "7.5.3", "7.5.4"))
                        self.assertEqual(profile["claude_transcript_capture"], version in ("7.4.0", "7.4.1", "7.5.0", "7.5.1", "7.5.2", "7.5.3", "7.5.4"))
                        self.assertEqual(profile["enforcement"], "observational_only")

    def test_legacy_actual_scope_response_and_later_choice_are_retained_independently(self):
        self.full_report_case()
        self.config["claude_command"][-1] = "fixture_response"
        self.begin_legacy_observer_fixture()
        offered = self.saved_run(prepare_only=True)["offered"]
        journal = [json.loads(line) for line in (self.work / "consultation/journal.jsonl").read_text(encoding="utf-8").splitlines()]
        scopes = [scope for row in journal for scope in row["payload"].get("changes", {}).get("action_scopes", [])]
        saved_scope = next(scope for scope in scopes if scope["scope_id"] == offered["scope"]["scope_id"])
        self.assertIn("basis_versions", saved_scope)
        self.assertNotIn("basis_refs", saved_scope)
        exchange = next(row["payload"]["exchange"] for row in journal
                        if row["type"] == "exchange_prepared" and row["payload"]["exchange"]["exchange_id"] == offered["exchange_ref"])
        option = next(item for item in exchange["response"]["next_steps"] if item["option_id"] == offered["option_id"])
        for field, source in (("proposal", "public_scope"), ("execution_plan", "execution_plan"), ("assignment", "assignment")):
            self.assertEqual(option[field], saved_scope[source])
        response = self.work / "fake-response.txt"
        response.write_text(offered["rendered_response"], encoding="utf-8")
        driver.step(self.attempt, self.reply(initial=True))
        self.assertFalse((self.work / "consultation/runs/report-main").exists())
        self.saved_run(offered=offered)
        response.write_text("The requested synthetic report is saved.", encoding="utf-8")
        user = "I choose the proposed report scope exactly as presented."
        driver.step(self.attempt, self.reply(message=user, fact_ids=[], rule_ids=[]))
        result = driver.finish(self.attempt, self.assessment())
        self.assertTrue(result["completion_check"]["satisfied"])
        check = result["consultation_loop_check"]
        self.assertEqual(check["profile"], driver.LOOP_CAPABILITY)
        # The fixture saves a separate review delivery without dispatching it.
        # Its capture discrepancy must not erase the actual later scope choice.
        self.assertEqual(check["status"], "unobserved", check)
        self.assertTrue(any(item["code"] == "delivery_public_mismatch" and item["owner"] == "undetermined"
                            for item in check["findings"]))
        self.assertEqual(check["actions"][0]["status"], "structurally_observed")
        self.assertEqual(check["actions"][0]["user_choice_candidates"][0]["actual_user_text"], user)
        self.assertTrue(check["actions"][0]["semantic_review_required"])
        self.assertEqual(result["test_validity"], "invalid")
        self.assertEqual(result["quality_rating"], "inconclusive")

    def test_validity_reason_required_and_mode_override_recorded(self):
        self.full_report_case()
        self.begin()
        self.saved_run()
        driver.step(self.attempt, self.reply(initial=True))
        review = self.assessment()
        without_reason = {key: value for key, value in review.items() if key != "test_validity_reason"}
        with self.assertRaises(ValueError) as raised:
            driver.finish(self.attempt, without_reason)
        self.assertIn("test validity reason required", str(raised.exception))
        result = driver.finish(self.attempt, review)
        self.assertEqual(result["test_validity"], "invalid")
        self.assertTrue(any("diagnostic mode" in note for note in result["validity_overrides"]))

    def test_legacy_saved_approval_and_actor_update_cannot_hide_unobserved_prior_offer(self):
        self.full_report_case()
        self.begin_legacy_observer_fixture()
        self.saved_run()
        driver.step(self.attempt, self.reply(initial=True))
        result = driver.finish(self.attempt, self.assessment())
        self.assertTrue(result["completion_check"]["satisfied"])
        self.assertEqual(result["consultation_loop_check"]["profile"], driver.LOOP_CAPABILITY)
        self.assertEqual(result["consultation_loop_check"]["status"], "breach")
        self.assertEqual(result["test_validity"], "invalid")
        self.assertEqual(result["quality_rating"], "fail")

    def test_project_root_binding_is_explicit_or_unique_and_contained(self):
        files = {"journal.jsonl": "root", ".claude/skills/example/journal.jsonl": "runtime"}
        self.assertEqual(driver.project_binding(files, {})["project_root"], ".")
        files["nested/journal.jsonl"] = "second"
        self.assertEqual(driver.project_binding(files, {})["status"], "ambiguous")
        self.assertEqual(driver.project_binding(files, {"project_root": "nested"})["project_root"], "nested")
        self.assertEqual(driver.project_binding({}, {})["status"], "missing")
        for value in ("../outside", "C:/outside", "nested/../outside", "nested/", "", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                driver.validate_config({**self.config, "project_root": value})

    def test_work_root_journal_is_observed_and_report_completion_uses_same_root(self):
        self.full_report_case()
        self.begin()
        self.saved_run(project_root=".")
        driver.step(self.attempt, self.reply(initial=True))
        event = self.attempt / "events/001"
        self.assertEqual(driver.read(event / "project-binding.json")["project_root"], ".")
        for command in ("status", "context", "verify"):
            self.assertEqual(driver.read(event / ("project-" + command) / "process.json")["exit_code"], 0)
        completion = self.completion_check()
        self.assertTrue(completion["satisfied"], completion["reason"])
        self.assertIn("work/runs/report-main/report.html", completion["evidence_refs"])
        self.assertFalse((self.work / "consultation").exists())

    def test_retained_frame_records_work_root_and_checks_transport_identity(self):
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        binding = driver.read(self.attempt / "events/001/project-binding.json")
        self.assertEqual(binding["observed_work_root"], self.work.resolve().as_posix())
        frames = driver.retained_frames(self.attempt, driver.read, driver.inventory)
        self.assertEqual(frames[0]["public_identity"]["session_id"], driver.read(self.attempt / "state.json")["session_id"])
        public = self.attempt / "events/001/public.json"
        original = driver.read(public)
        driver.write(public, {**original, "assistant": original["assistant"] + "Rewritten"})
        self.assertNotIn("public_identity", driver.retained_frames(self.attempt, driver.read, driver.inventory)[0])
        driver.write(public, original)
        command = self.attempt / "events/001/transport/command.json"
        value = driver.read(command)
        value["argv"][-1] = "wrong-session"
        driver.write(command, value)
        self.assertNotIn("public_identity", driver.retained_frames(self.attempt, driver.read, driver.inventory)[0])
        value["argv"][-1] = driver.read(self.attempt / "state.json")["session_id"]
        driver.write(command, value)
        driver.write(self.attempt / "events/001/transport/transport.json", [])
        self.assertNotIn("public_identity", driver.retained_frames(self.attempt, driver.read, driver.inventory)[0])

    def test_ambiguous_projects_are_not_silently_observed_or_counted_as_report(self):
        self.full_report_case()
        self.begin()
        self.saved_run(project_root="first")
        self.saved_run(project_root="second")
        driver.step(self.attempt, self.reply(initial=True))
        event = self.attempt / "events/001"
        self.assertEqual(driver.read(event / "project-binding.json")["status"], "ambiguous")
        self.assertFalse((event / "project-status").exists())
        self.assertFalse(self.completion_check()["satisfied"])

    def test_retained_native_message_identity_needs_one_complete_main_session_text(self):
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        event = self.attempt / "events/001"
        public = driver.read(event / "public.json")
        session = driver.read(self.attempt / "state.json")["session_id"]
        stdout = event / "transport/stdout.txt"
        original = stdout.read_bytes()
        native = {"type": "assistant", "session_id": session, "uuid": "synthetic-native-message",
                  "parent_tool_use_id": None, "message": {"role": "assistant", "content": [{"type": "text", "text": public["assistant"]}]}}
        for defect in (None, "different_text", "sidechain", "duplicate", "missing_uuid"):
            with self.subTest(defect=defect):
                record = copy.deepcopy(native)
                if defect == "different_text":
                    record["message"]["content"][0]["text"] += " Changed."
                elif defect == "sidechain":
                    record["parent_tool_use_id"] = "specialist-call"
                elif defect == "missing_uuid":
                    record.pop("uuid")
                prefix = (json.dumps(record) + "\n").encode()
                stdout.write_bytes(prefix + (prefix if defect == "duplicate" else b"") + original)
                identity = driver.retained_frames(self.attempt, driver.read, driver.inventory)[0]["public_identity"]
                self.assertEqual("message_ref" in identity, defect is None)
                if defect is None:
                    self.assertEqual(identity["conversation_ref"], "claude-code:" + session)
                    self.assertEqual(identity["message_ref"], "synthetic-native-message")
                self.assertNotIn("ordinal", identity)
        stdout.write_bytes(original)

    def test_explicit_project_binding_selects_recorded_report_among_projects(self):
        self.full_report_case()
        self.config["project_root"] = "second"
        self.begin()
        self.saved_run(project_root="first")
        self.saved_run(project_root="second")
        driver.step(self.attempt, self.reply(initial=True))
        completion = self.completion_check()
        self.assertTrue(completion["satisfied"], completion["reason"])
        self.assertEqual(completion["project_root"], "second")
        self.assertIn("work/second/runs/report-main/report.html", completion["evidence_refs"])

    def test_durable_final_correspondence_is_observed_without_journal_mutation(self):
        self.begin()
        project = self.work / "consultation"
        script = r"""
const fs = require('fs'), path = require('path');
const [scripts, root] = process.argv.slice(1);
const store = require(path.join(scripts, 'lib/store.cjs'));
store.init(root, {event_id:'event-init',project_id:'project-exchange',project_understanding:{objective:'Test exchange observation.'}});
const state = store.status(root).project.state_meta;
const receipt = store.record(root, {event_id:'event-close',expected_project_id:state.project_id,
 expected_last_event_id:state.last_event_id,type:'exchange_prepared',payload:{
 protocol:'durable-exchanges-v1',changes:{evidence:[{evidence_id:'user-message',kind:'user_statement',
 source_ref:'chat:turn-1',summary:'Please explain the current state.'}]},
 interpretation:{interpretation_id:'interpret-turn',turn_id:'turn-one',incoming_refs:['user-message'],basis_refs:[],
 components:[{kind:'instruction',meaning:'Explain current state.',established:['Explanation requested.'],unresolved:[]}],
 next_action:{kind:'lead_only',scope:'Explain current state.',reason:'No specialist review required.'}},
 exchange:{exchange_id:'exchange-one',turn_id:'turn-one',interpretation_ref:'interpret-turn',basis_refs:[],completed_work_refs:[],
 reconciliation:{changes:[],limitations:[],unresolved:[],next_direction:'Complete explanation.'},renderer:'lead-markdown-v1',
 response:{status:'RÃƒÂ©sumÃƒÂ©: test-only state.',questions:[],questions_none:'No questions.',next_steps:[],next_steps_none:'Complete.'}}}});
process.stdout.write(JSON.stringify(receipt));
"""
        run = subprocess.run([self.node, "-e", script,
                              str(self.work / ".claude/skills/causal-consultant/scripts"), str(project)],
                             text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        receipt = json.loads(run.stdout)
        before = (project / "journal.jsonl").read_bytes()
        state = driver.read(self.attempt / "state.json")
        state["started_at"] = time.time()
        messages = (receipt["rendered_response"], "Inline wrapper: " + receipt["rendered_response"] + "\nAdditional prose.", None,
                    receipt["rendered_response"].replace("test-only state", "changed state"),
                    receipt["rendered_response"] + "\n" + receipt["rendered_response"])
        for number, message in enumerate(messages, 1):
            event = self.attempt / "events" / f"{number:03d}"
            event.mkdir()
            driver.write(event / "public.json", {"user": "Test request.", "assistant": message, "attachments": []})
            driver.observe_project(event, state, self.config)
            observed = driver.read(event / "exchange-observation.json")
            self.assertEqual(observed["status"], ("matched", "wrapped", "unobserved", "mismatch", "mismatch")[number - 1])
            self.assertEqual(observed["enforcement"], "observational_only")
            if number == 2:
                self.assertFalse(observed["new_since_previous_observation"])
                self.assertNotEqual(observed["actual_response_sha256"], observed["expected_response_sha256"])
                self.assertEqual(observed["body_correspondence"]["status"], "wrapped")
                self.assertTrue(observed["body_correspondence"]["semantic_review_required"])
            if number == 1:
                self.assertEqual(observed["expected_response_sha256"], receipt["response_sha256"])
                self.assertEqual(observed["renderer"], "lead-markdown-v1")
                self.assertIsNone(observed["user_questions"])
                context = driver.read(event / "project-context/stdout.txt")
                self.assertEqual(context["views"]["work"]["current_exchange_ref"], "exchange-one")
        self.assertEqual(before, (project / "journal.jsonl").read_bytes())
        self.assertEqual(driver.read(self.attempt / "events/001/project-status/stdout.txt")["project"]["deliveries"], [])

    def test_v3_observation_preserves_user_questions_and_pending_view_without_delivery(self):
        self.begin()
        project = self.work / "consultation"
        script = r"""
const path = require('path');
const [scripts, root] = process.argv.slice(1);
const store = require(path.join(scripts, 'lib/store.cjs'));
store.init(root, {event_id:'event-init',project_id:'project-questions',project_understanding:{objective:'Test question capture.'}});
const state = store.status(root).project.state_meta;
const receipt = store.record(root, {event_id:'event-close',expected_project_id:state.project_id,
 expected_last_event_id:state.last_event_id,type:'exchange_prepared',payload:{
 protocol:'durable-exchanges-v1',changes:{evidence:[{evidence_id:'user-message',kind:'user_statement',
 source_ref:'chat:turn-1',source_excerpt:'Why does assignment matter, and what will the effect estimate be?',
 summary:'Why does assignment matter, and what will the effect estimate be?'}],questions:[
 {question_id:'question-why',origin:'user',statement:'Why does assignment matter?',status:'answered',reason:'Explained comparison.',basis_refs:['user-message']},
 {question_id:'question-effect',origin:'user',statement:'What will the effect estimate be?',status:'open',reason:'No analysis yet.',basis_refs:['user-message']},
 {question_id:'question-data',origin:'consultant',statement:'Can you share the data?',status:'open',basis_refs:['user-message']} ]},
 interpretation:{interpretation_id:'interpret-turn',turn_id:'turn-one',incoming_refs:['user-message'],basis_refs:[],
 components:[{kind:'question',meaning:'Explain assignment before work.',established:[],unresolved:[],user_question_ref:'question-why',answer_timing:'before_work'},
 {kind:'question',meaning:'Answer the effect question from eventual results.',established:[],unresolved:['No analysis yet.'],user_question_ref:'question-effect',answer_timing:'after_work'}],
 next_action:{kind:'lead_only',scope:'Explain assignment and retain the result question.',reason:'An explanation is needed first.'}},
 exchange:{exchange_id:'exchange-one',turn_id:'turn-one',interpretation_ref:'interpret-turn',basis_refs:[],completed_work_refs:[],
 reconciliation:{changes:['Explained assignment.'],limitations:['No analysis yet.'],unresolved:['Effect question remains open.'],next_direction:'Obtain the data.'},renderer:'lead-markdown-v3',
 response:{user_questions:[
 {question_ref:'question-why',text:'Why does assignment matter?',answer:'It determines which comparison can support the effect claim.',status:'answered',basis_refs:['user-message']},
 {question_ref:'question-effect',text:'What will the effect estimate be?',answer:'This remains pending until the data can be analyzed.',status:'pending',basis_refs:['user-message']}],
 status:'No analysis has been performed.',questions:[{question_ref:'question-data',text:'Can you share the data?',why:'The effect requires observations.',needed:'The study data file.'}],
 next_steps:[],next_steps_none:'Share the study data when available.'}}}});
process.stdout.write(JSON.stringify(receipt));
"""
        run = subprocess.run([self.node, "-e", script,
                              str(self.work / ".claude/skills/causal-consultant/scripts"), str(project)],
                             text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        receipt = json.loads(run.stdout)
        before = (project / "journal.jsonl").read_bytes()
        state = driver.read(self.attempt / "state.json")
        state["started_at"] = time.time()
        event = self.attempt / "events/001"
        event.mkdir()
        driver.write(event / "public.json", {"user": "Why does assignment matter, and what will the effect estimate be?",
                                             "assistant": receipt["rendered_response"], "attachments": []})
        driver.observe_project(event, state, self.config)
        observed = driver.read(event / "exchange-observation.json")
        self.assertEqual(observed["status"], "matched")
        self.assertEqual(observed["renderer"], "lead-markdown-v3")
        self.assertEqual([(item["question_ref"], item["status"]) for item in observed["user_questions"]],
                         [("question-why", "answered"), ("question-effect", "pending")])
        self.assertEqual(observed["pending_user_question_refs"], ["question-effect"])
        context = driver.read(event / "project-context/stdout.txt")
        self.assertEqual(context["views"]["work"]["pending_user_question_refs"], ["question-effect"])
        interpretation = next(item for item in context["views"]["work"]["interpretations"]
                              if item["interpretation_id"] == "interpret-turn")
        self.assertEqual([(item["user_question_ref"], item["answer_timing"])
                          for item in interpretation["components"] if item["kind"] == "question"],
                         [("question-why", "before_work"), ("question-effect", "after_work")])
        self.assertEqual(interpretation["next_action"]["kind"], "lead_only")
        self.assertEqual(before, (project / "journal.jsonl").read_bytes())
        self.assertEqual(driver.read(event / "project-status/stdout.txt")["project"]["deliveries"], [])

    def test_corrupt_or_unexpected_fixture_inputs_fail(self):
        for name in ("public/panel.csv", "actor.json"):
            original = (self.case / name).read_bytes()
            (self.case / name).write_bytes(original + b" ")
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                driver.validate_case(self.case)
            (self.case / name).write_bytes(original)
        (self.case / "unexpected.txt").write_text("extra")
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            driver.validate_case(self.case)

    def test_numeric_oracle_catches_coherently_rehashed_changed_data(self):
        data = self.case / "public/panel.csv"
        lines = data.read_text(encoding="utf-8").splitlines()
        column = lines[0].split(",").index("mean_skill_score")
        row = lines[1].split(",")
        row[column] = str(float(row[column]) + 100)
        lines[1] = ",".join(row)
        data.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.manifest()
        with self.assertRaisesRegex(ValueError, "self-check failed"):
            driver.validate_case(self.case)

    def requested_notes(self, *source_ids):
        """Add ordinary requested sources only to this composed test fixture."""
        manifest = driver.read(self.case / "case.json")
        actor = driver.read(self.case / "actor.json")
        for source_id in source_ids:
            name = source_id.removeprefix("s-") + ".txt"
            content = "A public note." if source_id == "s-note" else "Another public note."
            (self.case / "public" / name).write_text(content, encoding="utf-8")
            manifest["sources"].append({"id": source_id, "file": "public/" + name,
                "destination": name, "availability": "on_request"})
            actor["sources"].append({"source_id": source_id, "file": name, "availability": "when requested"})
        driver.write(self.case / "case.json", manifest)
        driver.write(self.case / "actor.json", actor)
        self.manifest()

    def assert_attachment_rejection(self, reply, reason, *, retained=False):
        before = driver.inventory(self.attempt)
        state = driver.read(self.attempt / "state.json")
        with patch.object(driver, "invoke") as invoke:
            with self.assertRaisesRegex(ValueError, reason):
                driver.step(self.attempt, reply)
            invoke.assert_not_called()
        after = driver.inventory(self.attempt)
        self.assertTrue(all(after[name] == sha for name, sha in before.items()))
        self.assertEqual(driver.read(self.attempt / "state.json"), state)
        self.assertFalse((self.attempt / f"events/{state['turns'] + 1:03d}").exists())
        added = set(after) - set(before)
        if retained:
            self.assertEqual(len(added), 1)
            path = added.pop()
            self.assertTrue(path.startswith("rejected-releases/"))
            rejected = driver.read(self.attempt / path)
            self.assertRegex(rejected["reason"], reason)
            self.assertFalse(rejected["dispatched"])
        else:
            self.assertEqual(added, set())

    def test_authorized_source_release_is_separate_from_actor_text(self):
        self.requested_notes("s-note")
        self.begin()
        self.assertFalse((self.work / "note.txt").exists())
        driver.step(self.attempt, self.reply(initial=True))
        with self.assertRaisesRegex(ValueError, "unauthorized"):
            driver.step(self.attempt, self.reply(attachments=["s-secret"]))
        driver.step(self.attempt, self.reply(message="Here is the note.txt you asked for.", attachments=["s-note"]))
        self.assertEqual((self.work / "note.txt").read_text(), "A public note.")
        self.assertEqual(driver.read(self.attempt / "events/002/releases.json")["s-note"]["sha256"], driver.digest(self.work / "note.txt"))
        self.assertNotIn("s-note", (self.work / "fake-message.txt").read_text())
        note = self.work / "note.txt"
        unchanged = (note.read_bytes(), note.stat().st_mtime_ns)
        driver.step(self.attempt, self.reply(message="Here is the same note again.", attachments=["s-note"]))
        self.assertEqual((note.read_bytes(), note.stat().st_mtime_ns), unchanged)
        self.assertEqual(driver.read(self.attempt / "events/003/releases.json"), {})
        self.assertEqual(driver.read(self.attempt / "events/003/public.json")["attachments"], ["note.txt"])
        self.assertEqual(driver.read(self.attempt / "state.json")["released_sources"].count("s-note"), 1)
        actor = driver.inspect(self.attempt, "actor")
        self.assertEqual([row["attachments"] for row in actor["actor_disclosures"]][-2:], [["s-note"], ["s-note"]])
        self.assessment()
        package = self.root / "ordinary-resend.zip"
        driver.export_package(self.attempt, package)
        self.assertEqual(driver.check_package(package)["completeness"], "complete")
        with zipfile.ZipFile(package) as archive:
            self.assertEqual(json.loads(archive.read("private/events/003/releases.json")), {})
            self.assertEqual(json.loads(archive.read("private/events/003/public.json"))["attachments"], ["note.txt"])
            self.assertEqual(archive.read("work/note.txt"), unchanged[0])

    def test_mixed_new_attachment_and_resend_record_one_acquisition_each(self):
        self.requested_notes("s-note", "s-other")
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        driver.step(self.attempt, self.reply(attachments=["s-note"]))
        before = (self.work / "note.txt").stat().st_mtime_ns
        driver.step(self.attempt, self.reply(attachments=["s-note", "s-other"]))
        self.assertEqual((self.work / "note.txt").stat().st_mtime_ns, before)
        self.assertEqual(list(driver.read(self.attempt / "events/003/releases.json")), ["s-other"])
        self.assertEqual(driver.read(self.attempt / "events/003/public.json")["attachments"], ["note.txt", "other.txt"])
        released = driver.read(self.attempt / "state.json")["released_sources"]
        self.assertEqual(released.count("s-note"), 1)
        self.assertEqual(released.count("s-other"), 1)

    def test_unrecorded_identical_attachment_cannot_claim_a_resend(self):
        self.requested_notes("s-note")
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        shutil.copyfile(self.case / "public/note.txt", self.work / "note.txt")
        self.assert_attachment_rejection(self.reply(attachments=["s-note"]), "release would overwrite a file", retained=True)
        self.assertNotIn("s-note", driver.read(self.attempt / "state.json")["released_sources"])

    def test_resend_cannot_restore_or_overwrite_missing_or_changed_public_bytes(self):
        self.requested_notes("s-note")
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        driver.step(self.attempt, self.reply(attachments=["s-note"]))
        note = self.work / "note.txt"
        original = note.read_bytes()
        for changed in (None, b"Changed public bytes."):
            with self.subTest(changed=changed):
                if changed is None:
                    note.unlink()
                else:
                    note.write_bytes(changed)
                self.assert_attachment_rejection(self.reply(attachments=["s-note"]), "released public input changed")
                self.assertEqual(note.read_bytes() if note.exists() else None, changed)
                note.write_bytes(original)

    def test_resend_keeps_actor_source_and_delivery_validation(self):
        self.requested_notes("s-note")
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        driver.step(self.attempt, self.reply(attachments=["s-note"]))
        reply = self.reply(attachments=["s-note"])
        reply["actor_context"]["context_id"] = driver.read(self.attempt / "state.json")["session_id"]
        self.assert_attachment_rejection(reply, "contexts must be separate")
        self.assert_attachment_rejection(self.reply(attachments=["s-note", "s-note"]), "duplicate release")
        self.assert_attachment_rejection(self.reply(attachments=["s-note", "s-unknown"]), "unauthorized source release", retained=True)
        for status in ("pending", "execution_error"):
            state = driver.read(self.attempt / "state.json")
            state["status"] = status
            driver.write(self.attempt / "state.json", state)
            self.assert_attachment_rejection(self.reply(attachments=["s-note"]), "attempt cannot send: " + status)

    def test_broken_original_acquisition_rejects_without_rewriting_evidence(self):
        self.requested_notes("s-note")
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        driver.step(self.attempt, self.reply(attachments=["s-note"]))
        ledger = self.attempt / "events/002/releases.json"
        snapshot = self.attempt / "events/002/work-snapshot/note.txt"
        for path, changed, reason in ((ledger, b"{", "original release evidence unreadable"),
                                     (ledger, b"[]", "original release evidence must be a JSON object"),
                                     (ledger, None, "original release evidence unreadable"),
                                     (snapshot, None, "original source snapshot changed or missing")):
            original = path.read_bytes()
            with self.subTest(path=path, changed=changed):
                if changed is None:
                    path.unlink()
                else:
                    path.write_bytes(changed)
                current = (self.work / "note.txt").read_bytes()
                self.assert_attachment_rejection(self.reply(attachments=["s-note"]), reason, retained=True)
                self.assertEqual((self.work / "note.txt").read_bytes(), current)
                path.write_bytes(original)

    def test_uncertain_or_failed_delivery_cannot_be_silently_resent(self):
        self.config["claude_command"][-1] = "changed"
        self.begin()
        result = driver.step(self.attempt, self.reply(initial=True))
        self.assertEqual(result["status"], "execution_error")
        with self.assertRaisesRegex(ValueError, "cannot send"):
            driver.step(self.attempt, self.reply())
        self.assertEqual(driver.read(self.attempt / "state.json")["turns"], 1)
        review = self.assessment()
        self.assertEqual(driver.finish(self.attempt, review)["outcome"], "execution_error")

    def test_pending_crash_and_operator_lock_refuse_new_dispatch(self):
        self.begin()
        state = driver.read(self.attempt / "state.json")
        state["status"] = "pending"
        driver.write(self.attempt / "state.json", state)
        with self.assertRaisesRegex(ValueError, "pending"):
            driver.step(self.attempt, self.reply(initial=True))
        (self.attempt / "operator.lock").write_text("interrupted")
        with self.assertRaisesRegex(ValueError, "lock"):
            driver.step(self.attempt, self.reply(initial=True))

    def test_whole_consultation_turn_cap_includes_attempts(self):
        self.config["limits"]["consultant_turns"] = 1
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        self.assertEqual(driver.step(self.attempt, self.reply())["status"], "limit_reached")
        result = driver.finish(self.attempt, self.assessment())
        self.assertEqual(result["outcome"], "incomplete")
        self.assertEqual(result["quality_rating"], "inconclusive")

    def test_changed_public_input_blocks_further_dispatch(self):
        self.begin()
        (self.work / "panel.csv").write_text("changed")
        with self.assertRaisesRegex(ValueError, "public input changed"):
            driver.step(self.attempt, self.reply(initial=True))

    def test_private_path_unknown_fact_and_changed_initial_message_rejected(self):
        self.begin()
        with self.assertRaisesRegex(ValueError, "exact frozen"):
            driver.step(self.attempt, self.reply())
        driver.step(self.attempt, self.reply(initial=True))
        with self.assertRaisesRegex(ValueError, "private path"):
            driver.step(self.attempt, self.reply(message=str(self.attempt / "actor.json")))
        with self.assertRaisesRegex(ValueError, "unknown fact_ids"):
            driver.step(self.attempt, self.reply(fact_ids=["invented-fact"]))

    def test_review_evidence_changes_are_detected(self):
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        review = self.assessment()
        (self.work / "late-output.txt").write_text("late mutation")
        with self.assertRaisesRegex(ValueError, "evidence changed"):
            driver.finish(self.attempt, review)

    def test_actor_input_binding_rejects_missing_stale_or_consultant_context(self):
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        reply = self.reply()
        with self.assertRaisesRegex(ValueError, "actor input digest"):
            driver.step(self.attempt, {**reply, "actor_context": {}})
        with self.assertRaisesRegex(ValueError, "contexts must be separate"):
            driver.step(self.attempt, {**reply, "actor_context": {
                **reply["actor_context"], "context_id": driver.read(self.attempt / "state.json")["session_id"]}})
        driver.step(self.attempt, reply)
        with self.assertRaisesRegex(ValueError, "stale"):
            driver.step(self.attempt, reply)
        stop = self.reply(message=None, stop=True)
        with self.assertRaisesRegex(ValueError, "actor input digest"):
            driver.step(self.attempt, {**stop, "actor_context": {}})
        self.assertEqual(driver.read(self.attempt / "state.json")["turns"], 2)

    def test_actor_current_selection_and_future_goal_are_separate(self):
        self.config["claude_command"][-1] = "fixture_response"
        self.begin()
        (self.work / "fake-response.txt").write_text("You can choose a data audit.", encoding="utf-8")
        driver.step(self.attempt, self.reply(initial=True))
        (self.work / "fake-response.txt").write_text("That audit checks which rows are usable.", encoding="utf-8")
        driver.step(self.attempt, self.reply(message="What is the audit for?"))
        message = "Please do that audit. I still want a report eventually."
        choices = [{"kind": "selection", "public_turn": 1, "option_quote": "choose a data audit",
                    "message_quote": "Please do that audit."},
                   {"kind": "goal_request", "message_quote": "I still want a report eventually."}]
        reply = self.reply(message=message, action_intents=choices)
        forged = copy.deepcopy(reply)
        forged["action_intents"][0]["option_quote"] = "Produce the final report"
        with self.assertRaisesRegex(ValueError, "actually presented option"):
            driver.step(self.attempt, forged)
        driver.step(self.attempt, reply)
        retained = driver.read(self.attempt / "events/003/actor.json")
        self.assertEqual(retained["action_intents"], choices)
        self.assertEqual((self.attempt / "events/003/transport/request.txt").read_text(), message)

    def test_final_checks_precede_review_and_cannot_be_omitted_or_replaced(self):
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        with self.assertRaisesRegex(ValueError, "inspect reviewer first"):
            driver.finish(self.attempt, {})
        review = self.assessment()
        observations = driver.read(self.attempt / "review-observations.json")
        self.assertFalse(observations["completion_check"]["satisfied"])
        with self.assertRaisesRegex(ValueError, "every final machine finding"):
            driver.finish(self.attempt, {**review, "machine_finding_dispositions": {}})
        with self.assertRaisesRegex(ValueError, "final observation snapshot"):
            driver.finish(self.attempt, {**review, "observations_sha256": "0" * 64})
        observations["completion_check"]["satisfied"] = True
        driver.write(self.attempt / "review-observations.json", observations)
        with self.assertRaisesRegex(ValueError, "final observation snapshot"):
            driver.finish(self.attempt, review)
        result = driver.finish(self.attempt, self.assessment())
        self.assertEqual(result["outcome"], "incomplete")

    def test_missing_raw_capture_is_reviewed_before_assessment(self):
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        (self.attempt / "events/001/transport/stdout.txt").unlink()
        view = driver.inspect(self.attempt, "reviewer")
        self.assertIn("private/events/001/transport/stdout.txt", view["observations"]["missing_captures"])
        self.assertIn("capture_completeness", [f["check"] for f in view["observations"]["machine_findings"]])
        self.assertEqual(driver.finish(self.attempt, self.assessment())["quality_rating"], "inconclusive")

    def test_heldout_gate_cannot_be_removed_or_aliased_in_case_manifest(self):
        self.case = self.root / "cate-case"
        compose_case("cate-policy", "standard", self.case)
        original = driver.read(self.case / "case.json")
        broken = copy.deepcopy(original)
        next(s for s in broken["sources"] if s["id"] == "s-evaluation").pop("release_prerequisite")
        driver.write(self.case / "case.json", broken)
        with self.assertRaisesRegex(ValueError, "prerequisite"):
            driver.validate_case(self.case)
        alias = copy.deepcopy(next(s for s in original["sources"] if s["id"] == "s-evaluation"))
        alias.update(id="s-alias", destination="another-file.csv")
        alias.pop("release_prerequisite")
        original["sources"].append(alias)
        driver.write(self.case / "case.json", original)
        with self.assertRaisesRegex(ValueError, "protected source"):
            driver.validate_case(self.case)

    def saved_evaluation_commitment(self):
        """Use the existing fake transport to retain a public pre-release plan."""
        self.case = self.root / "cate-case"
        compose_case("cate-policy", "standard", self.case)
        self.config["claude_command"][-1] = "fixture_response"
        self.begin()
        parts = {"candidate_rule": "Use the fixed training rule.", "utility": "Use net utility after cost.",
                 "comparators": "Compare treat none and the fixed comparator.",
                 "evaluation_procedure": "Evaluate once with a prespecified bootstrap interval."}
        plan = self.work / "evaluation-plan.md"
        plan.write_text("\n".join(parts.values()), encoding="utf-8")
        public = "I fixed and saved the candidate and evaluation plan in evaluation-plan.md."
        (self.work / "fake-response.txt").write_text(public, encoding="utf-8")
        driver.step(self.attempt, self.reply(initial=True))
        receipt = {"source_id": "s-evaluation", "public_turn": 1, "public_quote": public,
                   "commitments": {key: {"artifact": plan.name, "sha256": driver.digest(plan), "quote": value}
                                   for key, value in parts.items()}}
        return plan, receipt

    def test_heldout_release_refusal_then_saved_commitment_and_package_roundtrip(self):
        plan, receipt = self.saved_evaluation_commitment()
        reply = self.reply(message="Here are the evaluation records.", fact_ids=[], rule_ids=[], attachments=["s-evaluation"])
        with self.assertRaisesRegex(ValueError, "receipt"):
            driver.step(self.attempt, reply)
        source = next(s for s in driver.read(self.case / "case.json")["sources"] if s["id"] == "s-evaluation")
        self.assertFalse((self.work / source["destination"]).exists())
        self.assertEqual(driver.read(self.attempt / "state.json")["turns"], 1)
        self.assertEqual(len(list((self.attempt / "rejected-releases").glob("*.json"))), 1)
        original_invoke = driver.invoke
        def release_response(*args, **kwargs):
            result = original_invoke(*args, **kwargs)
            plan.write_text("Later work completed under the earlier fixed plan.", encoding="utf-8")
            return result
        with patch.object(driver, "invoke", side_effect=release_response):
            driver.step(self.attempt, {**reply, "source_release_receipts": [receipt]})
        self.assertTrue((self.work / source["destination"]).is_file())
        checks = driver.read(self.attempt / "events/002/source-release-check.json")["verified_receipts"]
        self.assertEqual(len(checks), 1)
        unchanged = ((self.work / source["destination"]).read_bytes(), (self.work / source["destination"]).stat().st_mtime_ns)
        driver.step(self.attempt, self.reply(message="Here are the same evaluation records again.",
                                             fact_ids=[], rule_ids=[], attachments=["s-evaluation"]))
        self.assertEqual(((self.work / source["destination"]).read_bytes(), (self.work / source["destination"]).stat().st_mtime_ns), unchanged)
        self.assertEqual(driver.read(self.attempt / "events/003/releases.json"), {})
        self.assertEqual(driver.read(self.attempt / "events/003/source-release-check.json"), {"verified_receipts": []})
        self.assertEqual(driver.read(self.attempt / "state.json")["released_sources"].count("s-evaluation"), 1)
        self.assertEqual(driver.read(self.attempt / "events/002/source-release-check.json")["verified_receipts"], checks)
        driver.finish(self.attempt, self.assessment())
        package = self.root / "run.zip"
        driver.export_package(self.attempt, package)
        result = driver.check_package(package)
        self.assertEqual(result["completeness"], "complete")
        with zipfile.ZipFile(package) as archive:
            self.assertEqual(json.loads(archive.read("private/events/003/releases.json")), {})
            self.assertEqual(json.loads(archive.read("private/events/003/public.json"))["attachments"], [source["destination"]])
            self.assertEqual(archive.read("work/" + source["destination"]), unchanged[0])

    def test_broken_original_protected_receipt_rejects_before_resend(self):
        _, receipt = self.saved_evaluation_commitment()
        driver.step(self.attempt, self.reply(message="Here are the evaluation records.", fact_ids=[], rule_ids=[],
            attachments=["s-evaluation"], source_release_receipts=[receipt]))
        path = self.attempt / "events/002/source-release-check.json"
        original = path.read_bytes()
        changed_receipts = ((b"{", "original release evidence unreadable"),
                            (b"[]", "original release evidence must be a JSON object"),
                            (None, "original release evidence unreadable"),
                            ({"verified_receipts": None}, "original gated receipt list is invalid"),
                            ({"verified_receipts": ["invalid"]}, "original gated receipt list is invalid"),
                            ({"verified_receipts": []}, "original gated receipt"),
                            ({"verified_receipts": [{"source_id": "s-evaluation"}]}, "original gated receipt is invalid"))
        for changed, reason in changed_receipts:
            with self.subTest(changed=changed):
                if changed is None:
                    path.unlink()
                elif isinstance(changed, bytes):
                    path.write_bytes(changed)
                else:
                    driver.write(path, changed)
                self.assert_attachment_rejection(self.reply(attachments=["s-evaluation"]), reason, retained=True)
                path.write_bytes(original)

    def test_diagnostic_cannot_pass_and_finalized_attempt_cannot_continue(self):
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        result = driver.finish(self.attempt, self.assessment())
        self.assertEqual(result["test_validity"], "invalid")
        self.assertEqual(result["quality_rating"], "inconclusive")
        self.assertIsNone(result["resources"]["aggregate_tokens"])
        with self.assertRaisesRegex(ValueError, "cannot send"):
            driver.step(self.attempt, self.reply())

    def test_material_consultant_finding_survives_invalid_test(self):
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        review = self.assessment()
        review["findings"] = [{"owner": "consultant", "severity": "material", "criterion": "c-evidence",
                               "description": "Test-only defect", "consequence": "Unsupported policy claim",
                               "evidence_refs": ["private/events/001/public.json"]}]
        self.assertEqual(driver.finish(self.attempt, review)["quality_rating"], "fail")

    def test_required_coverage_cannot_be_waived(self):
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        review = self.assessment()
        review["coverage"]["c-reproducibility"]["status"] = "not_applicable"
        with self.assertRaisesRegex(ValueError, "cannot be waived"):
            driver.finish(self.attempt, review)

    def test_configuration_rejects_implicit_bypass_and_invalid_limits(self):
        for update in ({"claude_command": ["claude", "--dangerously-skip-permissions"]},
                       {"max_agent_turns_per_call": 0}, {"mode": "verified_host"}):
            with self.subTest(update=update), self.assertRaises(ValueError):
                driver.validate_config({**self.config, **update})

    def test_configuration_validates_room_role_bindings(self):
        base = {**self.config, "reviewer_model": "zai/glm-5.3", "actor_runtime": "pi",
                "actor_model": "zai/glm-5.3-flash"}
        driver.validate_config(base)
        for update in ({"reviewer_model": "   "}, {"actor_runtime": "gemini"},
                       {"actor_model": ""}, {"actor_model": "zai/glm-5.3-flash"},
                       {"actor_runtime": "claude"}):
            with self.subTest(update=update), self.assertRaises(ValueError):
                driver.validate_config({**self.config, **update})

    def test_case_completion_contract_is_opt_in_and_validated(self):
        for contract in ("focused", "full_report"):
            manifest = driver.read(self.case / "case.json")
            manifest["completion_contract"] = contract
            driver.write(self.case / "case.json", manifest)
            self.assertEqual(driver.validate_case(self.case)["completion_contract"], contract)
        for contract in (None, True, "recap"):
            manifest["completion_contract"] = contract
            driver.write(self.case / "case.json", manifest)
            with self.assertRaisesRegex(ValueError, "completion contract"):
                driver.validate_case(self.case)

    def test_reportless_stop_finishes_incomplete_despite_reviewer_assertion(self):
        self.full_report_case()
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        stopped = driver.step(self.attempt, self.reply(message=None, stop=True, fact_ids=[], rule_ids=[]))
        self.assertEqual(stopped["status"], "awaiting_review")
        review = self.assessment()
        review["completion_check"] = {"satisfied": True, "reason": "Reviewer claims a report exists."}
        result = driver.finish(self.attempt, review)
        self.assertEqual(result["outcome"], "incomplete")
        self.assertFalse(result["completion_check"]["satisfied"])
        self.assertEqual(result["quality_rating"], "inconclusive")
        self.assertEqual(driver.read(self.attempt / "state.json")["status"], "finished")

    def test_reportless_useful_stop_cannot_bypass_full_report(self):
        self.full_report_case()
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        review = self.assessment()
        review.update(outcome="useful_stop", useful_stop_basis="Test-only permitted limited advice.")
        result = driver.finish(self.attempt, review)
        self.assertEqual(result["outcome"], "incomplete")
        self.assertFalse(result["completion_check"]["satisfied"])

    def test_six_consultant_turns_keep_session_and_complete_report_at_turn_cap(self):
        self.full_report_case()
        self.config["limits"]["consultant_turns"] = 6
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        for _ in range(4):
            self.assertEqual(driver.step(self.attempt, self.reply())["status"], "ready")
        self.saved_run()
        self.assertEqual(driver.step(self.attempt, self.reply(message="Please finish the saved report.",
                                                            fact_ids=[], rule_ids=[]))["status"], "ready")
        state = driver.read(self.attempt / "state.json")
        self.assertEqual(state["turns"], 6)
        transports = [driver.read(p) for p in sorted((self.attempt / "events").glob("*/transport/transport.json"))]
        self.assertEqual(len(transports), 6)
        self.assertEqual({t["session_id"] for t in transports}, {state["session_id"]})
        self.assertIn("--session-id", transports[0]["argv"])
        self.assertTrue(all("--resume" in t["argv"] for t in transports[1:]))
        driver.step(self.attempt, self.reply(message=None, stop=True, fact_ids=[], rule_ids=[]))
        result = driver.finish(self.attempt, self.assessment())
        self.assertEqual(result["outcome"], "objective_met")
        self.assertTrue(result["completion_check"]["satisfied"])
        self.assertEqual(result["completion_check"]["run_id"], "report-main")
        self.assertIn("work/consultation/runs/report-main/report.html", result["completion_check"]["evidence_refs"])
        self.assertFalse(result["resources"]["breaches"])

    def test_latest_verified_report_rejects_stale_or_missing_evidence(self):
        self.full_report_case()
        self.begin()
        self.saved_run()
        driver.step(self.attempt, self.reply(initial=True))
        self.assertTrue(self.completion_check()["satisfied"])
        output = self.work / "consultation/runs/report-main/report.html"
        verify_log = self.attempt / "events/001/project-verify/stdout.txt"
        snapshot_output = self.attempt / "events/001/work-snapshot/consultation/runs/report-main/report.html"
        for path, replacement in ((output, b"changed after verification"),
                                  (self.work / "panel.csv", b"source changed after verification"),
                                  (verify_log, None), (snapshot_output, None)):
            original = path.read_bytes()
            with self.subTest(path=path):
                if replacement is None:
                    path.unlink()
                else:
                    path.write_bytes(replacement)
                self.assertFalse(self.completion_check()["satisfied"])
                path.write_bytes(original)
        stale = driver.read(verify_log)
        original = verify_log.read_bytes()
        stale["last_event_id"] = "event-stale"
        driver.write(verify_log, stale)
        self.assertFalse(self.completion_check()["satisfied"])
        verify_log.write_bytes(original)
        self.saved_run(run_id="report-new", status="in_progress")
        result = driver.finish(self.attempt, self.assessment())
        self.assertEqual(result["outcome"], "incomplete")
        self.assertFalse(result["completion_check"]["satisfied"])

    def test_empty_manifested_report_does_not_complete_full_report(self):
        self.full_report_case()
        self.begin()
        self.saved_run(content="")
        driver.step(self.attempt, self.reply(initial=True))
        self.assertTrue(driver.read(self.attempt / "events/001/project-verify/stdout.txt")["ok"])
        result = driver.finish(self.attempt, self.assessment())
        self.assertEqual(result["outcome"], "incomplete")
        self.assertFalse(result["completion_check"]["satisfied"])

    def test_report_named_audit_output_and_loose_file_do_not_count_as_report(self):
        self.full_report_case()
        self.begin()
        self.saved_run(kind="audit")
        (self.work / "consultation/report.html").write_text("An unmanifested report-looking file.", encoding="utf-8")
        driver.step(self.attempt, self.reply(initial=True))
        self.assertTrue(driver.read(self.attempt / "events/001/project-verify/stdout.txt")["ok"])
        result = driver.finish(self.attempt, self.assessment())
        self.assertEqual(result["outcome"], "incomplete")

    def test_older_completed_report_cannot_hide_later_unfinished_revision(self):
        self.full_report_case()
        for status in ("in_progress", "failed", "abandoned"):
            with self.subTest(status=status):
                self.attempt, self.work = self.root / (status + "-private"), self.root / (status + "-work")
                self.begin()
                self.saved_run()
                self.saved_run(run_id="report-revision", status=status)
                driver.step(self.attempt, self.reply(initial=True))
                result = driver.finish(self.attempt, self.assessment())
                self.assertEqual(result["outcome"], "incomplete")
                self.assertFalse(result["completion_check"]["satisfied"])

    def test_full_report_keeps_cap_and_execution_failure_outcomes(self):
        self.full_report_case()
        self.config["limits"]["consultant_turns"] = 1
        for scenario, expected in (("ok", "incomplete"), ("provider_error", "execution_error")):
            with self.subTest(scenario=scenario):
                self.attempt, self.work = self.root / (scenario + "-private"), self.root / (scenario + "-work")
                self.config["claude_command"][-1] = scenario
                self.begin()
                driver.step(self.attempt, self.reply(initial=True))
                if scenario == "ok":
                    driver.step(self.attempt, self.reply())
                result = driver.finish(self.attempt, self.assessment())
                self.assertEqual(result["outcome"], expected)

    def test_focused_completion_still_needs_no_report(self):
        self.focused_endpoint()
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        result = driver.finish(self.attempt, self.assessment())
        self.assertEqual(result["outcome"], "objective_met")
        self.assertIsNone(result["completion_check"])

    def test_last_turn_observation_overrun_is_a_terminal_limit(self):
        self.config["limits"]["elapsed_seconds"] = 0.3
        self.begin()
        with patch.object(driver, "observe_project", side_effect=lambda *args: time.sleep(0.4)):
            result = driver.step(self.attempt, self.reply(initial=True))
        self.assertEqual(result["status"], "limit_reached")
        state = driver.read(self.attempt / "state.json")
        self.assertIn("whole_run_time_limit", state["breaches"])
        self.assertIn("ended_at", state)
        review = self.assessment()
        self.assertEqual(driver.finish(self.attempt, review)["quality_rating"], "inconclusive")

    def test_failed_consultation_clock_excludes_review_delay(self):
        self.config["claude_command"][-1] = "provider_error"
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        state = driver.read(self.attempt / "state.json")
        expected = state["ended_at"] - state["started_at"]
        time.sleep(0.05)
        result = driver.finish(self.attempt, self.assessment())
        self.assertEqual(result["resources"]["elapsed_seconds"], expected)

    def test_final_review_surfaces_unrecorded_source_copy_without_claiming_use(self):
        self.begin()
        manifest = driver.read(self.attempt / "freeze.json")["case_manifest"]
        source = next(item for item in manifest["sources"] if item["availability"] == "on_request")
        shutil.copyfile(self.attempt / "case" / source["file"], self.work / "renamed-record.txt")
        driver.step(self.attempt, self.reply(initial=True))
        observed = driver.inspect(self.attempt, "reviewer")["observations"]
        findings = [item for item in observed["machine_findings"] if item["check"] == "source_release_trace"]
        self.assertEqual(len(findings), 1)
        trace = findings[0]["observation"]
        self.assertEqual(trace["source_id"], source["id"])
        self.assertEqual(trace["status"], "acquisition_unverified")
        self.assertEqual(trace["first_observed_event"], 1)
        self.assertEqual(trace["first_observed_path"], "renamed-record.txt")
        # A confirmed evidence gap cannot become a pass even if other reviewed
        # dimensions would pass; this is not an attribution of early analysis.
        with patch.object(driver, "assess", return_value={"quality_rating": "pass"}):
            self.assertEqual(driver.finish(self.attempt, self.assessment())["quality_rating"], "inconclusive")

    def test_rating_rules_with_reviewed_host_and_missing_evidence(self):
        self.focused_endpoint()
        self.begin()
        driver.step(self.attempt, self.reply(initial=True))
        base = self.assessment()
        state = driver.read(self.attempt / "state.json")
        frozen = driver.read(self.attempt / "freeze.json")
        frozen["configuration"]["mode"] = "verified_host"
        frozen["reviewer_packet"] = driver.read(self.case / "reviewer.json")
        index = driver.read(self.attempt / "review-index.json")
        index["files"]["private/host/smoke.txt"] = "test-only"
        base["host_checks"] = {key: {"verified": True, "reason": "Test-only reviewed probe", "evidence_refs": ["private/host/smoke.txt"]}
                               for key in ("candidate_loading", "exact_resume", "private_isolation", "role_separation")}
        loop_check = driver.consultation_loop_check(self.attempt, frozen, index)
        self.assertEqual(driver.assess(base, state, frozen, index, loop_check=loop_check)["quality_rating"], "pass")
        missing = copy.deepcopy(base)
        missing["coverage"]["c-closeout"]["status"] = "unobserved"
        self.assertEqual(driver.assess(missing, state, frozen, index)["quality_rating"], "inconclusive")
        minor = copy.deepcopy(base)
        minor["findings"] = [{"owner": "consultant", "severity": "minor", "criterion": "c-evidence",
                              "description": "Test defect", "consequence": "Test consequence", "evidence_refs": ["private/events/001/public.json"]}]
        self.assertEqual(driver.assess(minor, state, frozen, index, loop_check=loop_check)["quality_rating"], "weak")
        for owner in ("simulator", "fixture", "harness", "environment"):
            invalid = copy.deepcopy(minor)
            invalid["findings"][0].update(owner=owner, severity="material")
            result = driver.assess(invalid, state, frozen, index)
            self.assertEqual(result["test_validity"], "invalid")
            self.assertEqual(result["quality_rating"], "inconclusive")
        uncertain = copy.deepcopy(minor)
        uncertain["findings"][0].update(owner="undetermined", severity="material")
        result = driver.assess(uncertain, state, frozen, index, loop_check=loop_check)
        self.assertEqual(result["test_validity"], "valid")
        self.assertEqual(result["quality_rating"], "inconclusive")
        attributable = copy.deepcopy(uncertain["findings"][0])
        attributable.update(owner="consultant", description="Separate attributable defect")
        uncertain["findings"].append(attributable)
        self.assertEqual(driver.assess(uncertain, state, frozen, index, loop_check=loop_check)["quality_rating"], "fail")
        no_host = copy.deepcopy(base)
        del no_host["host_checks"]
        with self.assertRaisesRegex(ValueError, "host check"):
            driver.assess(no_host, state, frozen, index)
        wrong_stop = copy.deepcopy(base)
        wrong_stop["outcome"] = "useful_stop"
        with self.assertRaisesRegex(ValueError, "does not permit"):
            driver.assess(wrong_stop, state, frozen, index)


class FindingResolutionTests(unittest.TestCase):
    """Exercise finish scoring with an otherwise valid synthetic host profile.

    Observations are injected after their separate observer tests. This does not
    qualify a live host or change diagnostic-mode behavior.
    """
    def score(self, kind="delivery_terminal_newlines", resolve=True, defect=None):
        with tempfile.TemporaryDirectory() as directory:
            attempt = Path(directory) / "attempt"
            work = Path(directory) / "work"
            (attempt / "case").mkdir(parents=True)
            work.mkdir()
            required = ["private/events/001/public.json", "private/events/002/work-snapshot/actual.txt",
                        "private/events/001/transport/transport.json", "private/host/smoke.txt", "state_at_review"]
            for ref in required:
                if ref.startswith("private/"):
                    path = attempt / ref.removeprefix("private/")
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("Test-only retained evidence", encoding="utf-8")
            driver.write(attempt / "state.json", {"status": "ready", "work": str(work), "turns": 2,
                "active_seconds": 0, "started_at": None, "breaches": []})
            driver.write(attempt / "freeze.json", {"configuration": {
                "mode": "diagnostic" if defect == "diagnostic" else "verified_host", "limits": {}},
                "case_manifest": {"reviewer": "reviewer.json", "completion_contract": "focused"},
                "observation_profile": {"consultation_loop": True}})
            driver.write(attempt / "case/reviewer.json", {"criteria": [{"id": "c-science"}]})
            candidate = {"kind": kind, "evidence_refs": required}
            if kind == "delivery_terminal_newlines":
                candidate.update(session_id="test-session", public_event="001", exchange_ref="exchange-1")
                code, check = "delivery_public_mismatch", "delivery_correspondence"
                resolution = {"kind": kind, "severity": "minor", "meaning_permission_timing_unchanged": True,
                              "review": "Complete counterparts differ only in a final newline; the offer and meaning are unchanged."}
            else:
                candidate["origins"] = [{"run_id": "analysis-1", "path": "runs/analysis-1/trends.png"}]
                code, check = "report_output_content_role", "artifact_provenance"
                resolution = {"kind": kind, "content_role": "diagnostic",
                              "review": "The retained image is the authorized raw-trends diagnostic, copied into the later report."}
            observation = {"code": code, "owner": "undetermined", "severity": "material",
                           "evidence_refs": required, "adjudication_candidate": candidate}
            if defect == "ineligible":
                observation.pop("adjudication_candidate")
            loop = {"status": "unobserved", "findings": [observation], "unobserved": [], "evidence_refs": required}
            observations = {"completion_check": None, "consultation_loop_check": loop, "missing_captures": [],
                            "machine_findings": [{"id": "primary", "check": check, "observation": observation}]}
            disposition = {"status": "confirmed", "reason": "Reviewed both retained sources.", "evidence_refs": required}
            if resolve:
                disposition["resolution"] = resolution
            dispositions = {"primary": disposition}
            if defect == "unresolved":
                disposition.update(status="unresolved")
                disposition.pop("resolution", None)
            elif defect == "missing_ref":
                disposition["evidence_refs"] = required[:1]
            elif defect == "missing_capture":
                observations["missing_captures"] = ["private/events/001/transport/stdout.txt"]
            elif defect in ("source_release", "authorization", "identity"):
                extra = {"code": "unbound_protected_start" if defect == "authorization" else "unresolved_identity",
                         "owner": "consultant" if defect == "authorization" else "undetermined",
                         "evidence_refs": required}
                observations["machine_findings"].append({"id": "extra", "check":
                    "source_release_trace" if defect == "source_release" else "consultation_loop" if defect == "authorization" else "unobserved",
                    "observation": extra})
                dispositions["extra"] = {"status": "confirmed", "reason": "Separate unresolved obligation.", "evidence_refs": required}
                if defect == "authorization":
                    loop["findings"].append(extra)
                    loop["status"] = "breach"
                elif defect == "identity":
                    loop["unobserved"].append(extra)
            with patch.object(driver, "review_observations", return_value=observations):
                prepared = driver.inspect(attempt, "reviewer")
                review = {"evidence_sha256": prepared["evidence_sha256"],
                    "observations_sha256": prepared["observations_sha256"],
                    "machine_finding_dispositions": dispositions,
                    "test_validity": "valid", "test_validity_reason": "Synthetic host-only scoring test.",
                    "outcome": "objective_met", "stop_reason": "Test completed", "reviewer": "test-reviewer",
                    "coverage": {"c-science": {"status": "observed", "reason": "Test coverage", "evidence_refs": required[:1]}},
                    "findings": [], "host_checks": {key: {"verified": True, "reason": "Synthetic host evidence",
                        "evidence_refs": ["private/host/smoke.txt"]}
                        for key in ("candidate_loading", "exact_resume", "private_isolation", "role_separation")}}
                if defect in ("material", "minor"):
                    review["findings"] = [{"owner": "consultant", "severity": defect, "criterion": "c-science",
                        "description": "Reviewed defect", "consequence": "Supported consequence", "evidence_refs": required}]
                return driver.finish(attempt, review)

    def test_reviewed_formatting_retains_raw_difference_without_forcing_inconclusive(self):
        result = self.score()
        self.assertEqual(result["quality_rating"], "pass")
        self.assertEqual(result["consultation_loop_check"]["status"], "unobserved")
        self.assertEqual(result["adjudicated_consultation_loop_status"], "no_structural_breach")
        self.assertEqual(result["machine_finding_adjudications"][0]["kind"], "delivery_terminal_newlines")
        self.assertEqual(self.score(resolve=False)["quality_rating"], "inconclusive")
        self.assertEqual(self.score(defect="minor")["quality_rating"], "weak")

    def test_formatting_resolution_cannot_waive_other_gaps_or_failures(self):
        for defect in ("source_release", "missing_capture", "identity", "diagnostic", "unresolved"):
            with self.subTest(defect=defect):
                self.assertEqual(self.score(defect=defect)["quality_rating"], "inconclusive")
        for defect in ("authorization", "material"):
            with self.subTest(defect=defect):
                self.assertEqual(self.score(defect=defect)["quality_rating"], "fail")
        for defect in ("ineligible", "missing_ref"):
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                self.score(defect=defect)

    def test_diagnostic_reuse_requires_content_review_and_preserves_premature_report_finding(self):
        kind = "authorized_diagnostic_reuse"
        self.assertEqual(self.score(kind, resolve=False)["quality_rating"], "inconclusive")
        self.assertEqual(self.score(kind)["quality_rating"], "pass")
        self.assertEqual(self.score(kind, defect="material")["quality_rating"], "fail")


if __name__ == "__main__":
    unittest.main()
