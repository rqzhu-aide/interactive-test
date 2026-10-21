"""Private arithmetic and source checks; these do not grade model reasoning."""
import copy
import csv
import importlib.util
import json
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import compose_case
import generate_problem_bank


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def bank(identity):
    return (compose_case.RGGVY_ROOT / "problem" if identity == compose_case.RGGVY_ID
            else ROOT / "problems" / identity)


def checker(identity):
    spec = importlib.util.spec_from_file_location(identity.replace("-", "_"),
                                                bank(identity) / "check_oracle.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ScientificProbes(unittest.TestCase):
    def test_all_five_frozen_oracles_execute(self):
        for identity in (*generate_problem_bank.PROBLEM_IDS, "rggvy-electrification"):
            with self.subTest(problem=identity):
                result = subprocess.run([sys.executable, "-B", str(bank(identity) / "check_oracle.py")],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue(json.loads(result.stdout)["ok"])

    def test_generator_reproduces_frozen_synthetic_probes_and_source_bytes(self):
        for identity in generate_problem_bank.PROBLEM_IDS:
            for name, expected in generate_problem_bank.build(identity).items():
                with self.subTest(problem=identity, file=name):
                    self.assertEqual((ROOT / "problems" / identity / name).read_bytes(), expected)

    def test_lee_always_assessed_target_rejects_roster_weighting(self):
        module = checker("study-design")
        probes = module.read_json("oracle.json")["developer_probes"]
        module.check_developer_probes(probes)
        result = probes["lee_weighting"]["expected"]
        self.assertAlmostEqual(result["always_assessed_effect"], 17 / 7)
        self.assertEqual(result["roster_weighted_effect"], 3)
        wrong = copy.deepcopy(probes)
        wrong["lee_weighting"]["expected"]["always_assessed_weights"] = [0.5, 0.5]
        wrong["lee_weighting"]["expected"]["always_assessed_effect"] = 3
        with self.assertRaises(AssertionError):
            module.check_developer_probes(wrong)

    def test_non_detection_can_admit_zero_and_a_worthwhile_effect(self):
        module = checker("study-design")
        probes = module.read_json("oracle.json")["developer_probes"]
        interval = probes["non_detection"]["expected"]["interval"]
        self.assertLess(interval[0], 0)
        self.assertGreater(interval[1], probes["non_detection"]["worthwhile_effect"])
        wrong = copy.deepcopy(probes)
        wrong["non_detection"]["expected"]["contains_worthwhile_effect"] = False
        with self.assertRaises(AssertionError):
            module.check_developer_probes(wrong)

    def test_attainable_planning_source_and_worthwhile_effect_are_checked(self):
        module = checker("study-design")
        problem, world = module.read_json("problem.json"), module.read_json("world.json")
        module.check_retained_sources(problem, world)
        self.assertEqual(module.check_design()["worthwhile_effect_assumption"], 4)
        changed = copy.deepcopy(problem)
        next(s for s in changed["sources"] if s["id"] == "s-planning")["availability"] = "unavailable"
        with self.assertRaisesRegex(AssertionError, "availability"):
            module.check_retained_sources(changed, world)
        changed_world = copy.deepcopy(world)
        next(s for s in changed_world["source_inventory"] if s["source_id"] == "s-planning")["sha256"] = "0" * 64
        with self.assertRaises(AssertionError):
            module.check_retained_sources(problem, changed_world)

    def test_same_learner_correlation_allows_different_cluster_adjustment(self):
        module = checker("study-design")
        probes = module.read_json("oracle.json")["developer_probes"]
        module.check_developer_probes(probes)
        example = probes["cluster_covariance"]
        self.assertEqual(example["expected"]["marginal_correlations"], [0.7, 0.7])
        se1, se2 = example["expected"]["cluster_mean_adjusted_se"]
        self.assertGreater(se1, se2 * 1.3)
        wrong = copy.deepcopy(probes)
        wrong["cluster_covariance"]["expected"]["cluster_mean_adjusted_se"][0] = se2
        with self.assertRaises(AssertionError):
            module.check_developer_probes(wrong)

    def test_policy_levels_incremental_values_and_paired_uncertainty_reconcile(self):
        module = checker("cate-policy")
        actual = module.check_cate()
        module.close(actual, module.read_json("oracle.json")["expected"])
        result = actual["partitions"]["evaluation"]["fixed_benchmark_cell_contrasts"]
        self.assertAlmostEqual(result["incremental_net_gain"], 0.7791825494680051)
        self.assertAlmostEqual(result["no_offer_utility"], 0.974682648847834)
        self.assertAlmostEqual(result["absolute_utility"], 1.753865198315839)
        self.assertAlmostEqual(result["rule_minus_lottery"], 0.8300429877134717)
        self.assertAlmostEqual(result["rule_minus_lottery_se"], 0.0786110510777156)
        with (ROOT / "problems/cate-policy/public/evaluation.csv").open(encoding="utf-8", newline="") as stream:
            data = list(csv.DictReader(stream))
        groups = {}
        for row in data:
            key = tuple(row[k] for k in ("readiness_high", "barrier_flag", "baseline_band"))
            groups.setdefault(key, [[], []])[int(row["offer"])].append(float(row["skill_gain"]))
        lottery_variance = sum((0.375 / 8) ** 2 * sum(statistics.variance(g) / len(g) for g in cell)
                               for cell in groups.values())
        independent_variance = result["rule_incremental_se"] ** 2 + lottery_variance
        self.assertGreater(independent_variance, result["rule_minus_lottery_se"] ** 2)
        self.assertAlmostEqual(independent_variance - 2 * result["rule_lottery_covariance"],
                               result["rule_minus_lottery_se"] ** 2)
        wrong = copy.deepcopy(actual)
        wrong["partitions"]["evaluation"]["fixed_benchmark_cell_contrasts"]["absolute_utility"] = result["incremental_net_gain"]
        with self.assertRaises(AssertionError):
            module.close(wrong, module.read_json("oracle.json")["expected"])

    def test_unknown_completion_is_not_reclassified_as_failure(self):
        module = checker("data-quality-edge")
        expected = module.read_json("oracle.json")["expected"]
        module.close(module.check_edge(), expected)
        self.assertEqual(expected["observed_failures"], 30)
        self.assertEqual(expected["outcome_missing"], 30)
        self.assertEqual(expected["cohort_success_bounds"], [0.5, 0.75])
        data = {name: module.rows(name) for name in ("extract.csv", "participant-roster.csv")}
        for row in data["extract.csv"]:
            if row["completed_12weeks"] == "":
                row["completed_12weeks"] = "0"
        with patch.object(module, "rows", side_effect=lambda name: data[name]):
            with self.assertRaises(AssertionError):
                module.close(module.check_edge(), expected)

    def test_rggvy_legacy_membership_and_mismatch_exclusions(self):
        module = checker("rggvy-electrification")
        actual = module.check_data()
        self.assertEqual(actual, module.read_json(module.ROOT, "oracle.json")["expected"])
        result = actual["villages"]["legacy_rf_sample_200"]
        self.assertEqual((result["rows"], result["population_mismatch"], result["after_excluding_flagged_mismatches"]),
                         (556, 68, 488))
        rows = [{"flag": 1, "p_300_X": -1, "pop_mismatch20": 0},
                {"flag": 1, "p_300_X": 1, "pop_mismatch20": 1},
                {"flag": 0, "p_300_X": 2, "pop_mismatch20": 1},
                {"flag": 1, "p_300_X": 0, "pop_mismatch20": None}]
        result = module.legacy_sample_summary(rows, "flag")
        self.assertEqual((result["rows"], result["population_mismatch"], result["population_mismatch_unknown"],
                          result["after_excluding_flagged_mismatches"]), (3, 1, 1, 2))
        rows[0]["pop_mismatch20"] = 1
        self.assertEqual(module.legacy_sample_summary(rows, "flag")["after_excluding_flagged_mismatches"], 1)

    def test_new_private_probes_do_not_enter_actor_material(self):
        with tempfile.TemporaryDirectory(prefix="scientific-probes-") as directory:
            destination = Path(directory) / "case"
            manifest = compose_case.compose_case("study-design", "expert", destination)
            self.assertEqual(manifest["problem_version"], "1.3.0")
            self.assertEqual(manifest["persona_version"], "1.1.1")
            actor = (destination / "actor.json").read_text(encoding="utf-8")
            for private_marker in ("lee_weighting", "always_assessed_weights", "17 / 7", "CR2", "contains_worthwhile_effect",
                                   "claim_calibration", "power-under-pressure", "cluster_covariance"):
                self.assertNotIn(private_marker, actor)

    def test_applied_probe_inputs_are_separate_from_review_and_study_data(self):
        ids = set()
        for identity in generate_problem_bank.PROBLEM_IDS:
            module = checker(identity)
            oracle = module.read_json("oracle.json")
            for probe in oracle["developer_probes"]["applied_interpretation"]:
                self.assertNotIn(probe["id"], ids)
                ids.add(probe["id"])
                self.assertEqual(set(probe["input"]), {"request", "evidence"})
                self.assertNotIn("review", probe["input"])
                self.assertTrue(probe["review"])
            calibration = oracle["developer_probes"]["claim_calibration"]
            lo, hi = calibration["evidence"]["interval"]
            self.assertGreater(lo, 0)
            self.assertLess(lo, calibration["evidence"]["worthwhile_threshold"])
            self.assertGreater(hi, calibration["evidence"]["worthwhile_threshold"])
        self.assertEqual(len(ids), 7)


if __name__ == "__main__":
    unittest.main()
