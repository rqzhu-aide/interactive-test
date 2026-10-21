"""Structural check for a prospective planning fixture, not a scientific oracle."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
CASE_VERSIONS = {"masks-planning": "1.1.3", "forest-planning": "1.1.3",
                 "medication-planning": "1.1.3", "surgery-planning": "1.1.4"}


def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main():
    manifest, actor, world, reviewer = [read(n) for n in ("case.json", "actor.json", "world.json", "reviewer.json")]
    actual = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in ROOT.rglob("*") if p.is_file() and p.name != "case.json"}
    assert actual == manifest["files"], "Unfrozen or modified case file"
    limits = {"max_words": 50, "max_items": 1}
    assert manifest["reply_limits"] == actor["reply_limits"] == actor["persona_profile"]["reply_limits"] == limits
    assert manifest["completion_contract"] == "focused"
    assert manifest["target_turns"] == 9 and manifest["expected_turn_range"] == [8, 10]
    assert manifest["run_limits"]["consultant_turns"] == 12
    assert "minimum_consultant_replies" not in manifest
    assert manifest["sources"] == actor["sources"] == []
    assert manifest["world_id"] == world["world_id"] and manifest["world_version"] == world["world_version"]
    assert manifest["case_version"] == CASE_VERSIONS[manifest["case_id"]]
    assert manifest["world_version"] == "1.1.0"
    assert manifest["suite_version"] == "prospective-study-design-1.1.0"
    public = (ROOT / manifest["initial_message"]).read_text(encoding="utf-8")
    assert "causal-consultant" in public and len(public.split()) <= 50
    world_facts = {f["fact_id"]: f for f in world["facts"]}
    actor_ids = [f["fact_id"] for f in actor["facts"]]
    assert len(actor_ids) == len(set(actor_ids))
    for f in actor["facts"]:
        source = world_facts[f["fact_id"]]
        for field in ("statement", "certainty", "source"):
            assert f[field] == source[field], "Actor/world disagreement: " + f["fact_id"]
        assert len(f["answer_example"].split()) <= 45
        assert f["available_when"] and f["disclosure_condition"]
    for c in reviewer["criteria"]:
        assert set(c.get("fact_ids", [])) <= set(actor_ids)
        if c.get("scope") == "if_route_selected":
            assert c.get("conditional") is True, "Conditional criterion lacks its Boolean declaration: " + c["id"]
    assert len({c["id"] for c in reviewer["criteria"]}) == len(reviewer["criteria"])
    for route in reviewer["acceptable_routes"]:
        assert set(route["requires_fact_ids"]) <= set(actor_ids)
    assert len(reviewer["acceptable_routes"]) >= 2
    assert world["world_only"]
    for forbidden_key in ("reviewer", "world_only", "provenance", "target_turns", "expected_turn_range", "core", "acceptable_routes"):
        def contains(value):
            if isinstance(value, dict):
                return forbidden_key in value or any(contains(v) for v in value.values())
            return isinstance(value, list) and any(contains(v) for v in value)
        assert not contains(actor), "Private evaluator field leaked into actor: " + forbidden_key
    private_identifiers = r"\b(Mitze|Kosfeld|Ferraro|Simorangkir|semaglutide|Volkow|Kaelber|Wallis|Coburn|Satkunasivam|Jena|Indonesia|Ontario|TriNetX|PKH)\b"
    assert not re.search(private_identifiers, public + json.dumps(actor), flags=re.I)
    assert not re.search(r"[\u2013\u2014]", public + json.dumps(actor, ensure_ascii=False))
    print("PASS: fixture identities, actor/world facts, references and private/public boundaries. Scientific and live-behavior validation are separate.")


if __name__ == "__main__":
    main()
