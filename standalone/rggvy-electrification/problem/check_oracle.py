"""Check frozen real-source bytes and data handling, never a causal effect.

Standard library only. Reads the bounded archive in memory without extraction.
The Stata reader deliberately supports only this frozen release-115 file.
"""
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import struct
import zipfile

ROOT = Path(__file__).resolve().parent
MEMBERS = {"villages.dta", "households.tsv", "village_variables.csv", "household_variables.csv"}
NUMERIC = {251: ("b", 1, 101), 252: ("h", 2, 32741),
           253: ("i", 4, 2147483621), 254: ("f", 4, 1.7014118346046923e38),
           255: ("d", 8, 8.98846567431158e307)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(root, name):
    return json.loads((root / name).read_text(encoding="utf-8"))


def records(data, delimiter=","):
    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig")), delimiter=delimiter))


def stata115(data, selected):
    require(data[:4] == bytes([115, 2, 1, 0]), "unexpected Stata format")
    k, n = struct.unpack_from("<HI", data, 4)
    types = list(data[109:109 + k])
    pos = 109 + k

    def strings(width):
        nonlocal pos
        result = [data[pos + j * width:pos + (j + 1) * width].split(b"\0", 1)[0].decode("latin1")
                  for j in range(k)]
        pos += k * width
        return result

    names = strings(33)
    pos += 2 * (k + 1)
    strings(49)  # display formats
    strings(33)  # value-label names
    labels = strings(81)
    require(len(set(names)) == k, "duplicate Stata variable names")
    while True:
        kind, length = struct.unpack_from("<bi", data, pos)
        pos += 5
        require(length >= 0 and pos + length <= len(data), "invalid Stata expansion field")
        if kind == 0:
            require(length == 0, "invalid Stata expansion terminator")
            break
        pos += length
    widths = [t if 1 <= t <= 244 else NUMERIC[t][1] for t in types]
    stride = sum(widths)
    require(len(data) == pos + n * stride, "Stata data length or row count differs")
    offsets, offset = {}, 0
    for name, t, width in zip(names, types, widths):
        offsets[name] = (offset, t, width)
        offset += width
    require(set(selected) <= set(names), "required Stata variable absent")
    result = []
    for i in range(n):
        row = {}
        base = pos + i * stride
        for name in selected:
            off, t, width = offsets[name]
            if t <= 244:
                value = data[base + off:base + off + width].split(b"\0", 1)[0].decode("latin1")
            else:
                fmt, _, missing = NUMERIC[t]
                value = struct.unpack_from("<" + fmt, data, base + off)[0]
                if value >= missing:
                    value = None
            row[name] = value
        result.append(row)
    return {"format": 115, "rows": n, "columns": k, "row_bytes": stride,
            "data_offset": pos, "names": names, "labels": labels}, result


def legacy_sample_summary(villages, sample_flag):
    """Describe a legacy pool and its screen, not an outcome-specific bandwidth."""
    selected = [r for r in villages if r[sample_flag] == 1]
    return {"rows": len(selected), "below": sum(r["p_300_X"] < 0 for r in selected),
            "at": sum(r["p_300_X"] == 0 for r in selected), "above": sum(r["p_300_X"] > 0 for r in selected),
            "population_mismatch": sum(r["pop_mismatch20"] == 1 for r in selected),
            "population_mismatch_unknown": sum(r["pop_mismatch20"] is None for r in selected),
            "after_excluding_flagged_mismatches": sum(r["pop_mismatch20"] != 1 for r in selected)}


def check_data(root=ROOT):
    root = Path(root)
    path = root / "public/data.zip"
    require(path.stat().st_size <= 25_000_000, "data bundle exceeds 25 MB")
    with zipfile.ZipFile(path) as archive:
        require(len(archive.infolist()) == len(MEMBERS) and set(archive.namelist()) == MEMBERS,
                "data archive member allowlist differs")
        require(all(i.file_size <= 80_000_000 for i in archive.infolist()), "oversized archive member")
        raw = {name: archive.read(name) for name in MEMBERS}
    fields = ["pca01_id", "st_code", "district", "tot_p", "p_300_X", "p_300_D",
              "rf_sample_150", "rf_sample_200", "pop_mismatch20", "lights_max2001", "lights_max2011"]
    meta, villages = stata115(raw["villages.dta"], fields)
    dictionary = records(raw["village_variables.csv"])
    require([r["variable"] for r in dictionary] == meta["names"], "village dictionary order differs")
    require([r["source_label"] for r in dictionary] == meta["labels"], "village source labels differ")
    households = records(raw["households.tsv"], "\t")
    hh_dictionary = records(raw["household_variables.csv"])
    require([r["variable"] for r in hh_dictionary] == list(households[0]), "household dictionary differs")
    require(all(r["st_code"] == 22 for r in villages), "non-Chhattisgarh village")
    require(all(r["st_code"] == "22" for r in households), "non-Chhattisgarh household")
    require(len({r["pca01_id"] for r in villages}) == len(villages), "duplicate census village key")
    require(len({(r["st_code"], r["dt_code"], r["nss_hh_id"]) for r in households}) == len(households),
            "unexpected duplicate household/district key")
    id_years = defaultdict(set)
    totals = defaultdict(float)
    for r in households:
        id_years[r["nss_hh_id"]].add(r["year"])
        weight = float(r["weight_normalized"])
        require(math.isfinite(weight) and weight > 0, "invalid normalized survey weight")
        totals[(r["dt_code"], r["year"])] += weight
    require(all(len(years) == 1 for years in id_years.values()), "source household ID spans survey waves")
    require(all(abs(total - 1_000_000) < 0.1 for total in totals.values()), "district-wave weight normalization changed")
    require(all(r["p_300_X"] == r["tot_p"] - 300 for r in villages), "RD running variable changed")
    require(all(r["p_300_D"] == int(r["tot_p"] >= 300) for r in villages), "cutoff coding changed")
    pure = [r for r in households if r["sample_1011"] == "1"]
    treated = [r for r in households if r["year"] == "2010" and r["treat_x_post"] == "1"]
    cutoff = [r for r in villages if r["tot_p"] == 300]
    missing = lambda value: value in ("", "NA", "NaN", ".")
    by_year = {year: [r for r in households if r["year"] == year] for year in ("2000", "2005", "2010")}
    require(all(float(r["tot_p01"]) > 300 for r in households), "household aggregate population changed")

    outputs = (root / "public/records/outputs_nss.do").read_text(encoding="utf-8")
    sections = {}
    for table in (3, 5, 7):
        section = re.search(r"\*\* Table " + str(table) + r":(.*?)(?=\*\* Table |\Z)", outputs, re.S)
        require(section is not None, "main table source missing")
        sections[str(table)] = 'keep if ifs==""' in section.group(1)
    sensitivity = re.search(r"\*\* Table B9:(.*?)(?=\*\* Table |\Z)", outputs, re.S)
    require(sensitivity is not None, "sensitivity table source missing")
    names = set(meta["names"])
    return {
        "villages": {"rows": len(villages), "columns": meta["columns"], "stata_release": meta["format"],
            "row_bytes": meta["row_bytes"], "data_offset": meta["data_offset"],
            "unique_pca01_id": len({r["pca01_id"] for r in villages}),
            "districts": len({r["district"] for r in villages}),
            "missing_lights_2001": sum(r["lights_max2001"] is None for r in villages),
            "missing_lights_2011": sum(r["lights_max2011"] is None for r in villages),
            "cutoff_300_rows": len(cutoff), "cutoff_300_instrument_one": sum(r["p_300_D"] == 1 for r in cutoff),
            "legacy_rf_sample_150": legacy_sample_summary(villages, "rf_sample_150"),
            "legacy_rf_sample_200": legacy_sample_summary(villages, "rf_sample_200"),
            "has_shrug_consumption": "secc11_rural_cons_pc" in names},
        "households": {"rows": len(households), "columns": len(households[0]),
            "unique_nss_hh_id": len(id_years), "duplicate_source_id_rows": len(households) - len(id_years),
            "rows_by_year": {y: len(rs) for y, rs in by_year.items()},
            "unique_ids_by_year": {y: len({r["nss_hh_id"] for r in rs}) for y, rs in by_year.items()},
            "districts": len({r["dt_code"] for r in households}), "district_year_cells": len(totals),
            "stdt_cluster_groups": len({r["stdt_cluster"] for r in households}),
            "stdt_presplit_groups": len({r["stdt_presplit"] for r in households}),
            "treated_districts_2010": sorted({r["district"] for r in treated}),
            "groups_containing_treated_districts": len({r["stdt_cluster"] for r in treated}),
            "sample_1011_rows": len(pure), "sample_1011_groups": len({r["stdt_cluster"] for r in pure}),
            "missing_frame_population_by_year": {y: sum(missing(r["frame_population"]) for r in rs) for y, rs in by_year.items()},
            "tot_p01_range": [min(float(r["tot_p01"]) for r in households), max(float(r["tot_p01"]) for r in households)],
            "normalized_weight_sum_per_district_year": 1_000_000},
        "source_semantics": {"main_tables_unrestricted": sections,
            "table_B9_uses_sample_1011": 'keep if ifs==" if sample_1011"' in sensitivity.group(1),
            "known_causal_truth": False},
        "member_sha256": {name: sha(raw[name]) for name in sorted(MEMBERS)}
    }


def main():
    problem = read_json(ROOT, "problem.json")
    oracle = read_json(ROOT, "oracle.json")
    world = read_json(ROOT, "world.json")
    require(problem["problem_id"] == oracle["problem_id"] == "rggvy-electrification", "problem identity differs")
    require(world["world_id"] == "real-rggvy-chhattisgarh-v1", "world identity differs")
    require(oracle["specification"]["known_causal_truth"] is False, "real study cannot supply oracle causal truth")
    for name, expected_hash in problem["files"].items():
        require(sha((ROOT / name).read_bytes()) == expected_hash, "frozen bytes changed: " + name)
    for source in world["source_inventory"]:
        require(sha((ROOT / source["file"]).read_bytes()) == source["sha256"], "source identity differs")
    require({s["id"]: (s["file"], s["availability"]) for s in problem["sources"]} ==
            {s["source_id"]: (s["file"], s["availability"]) for s in world["source_inventory"]},
            "source availability differs from frozen world")
    actual = check_data()
    require(actual == oracle["expected"], "data handling or source metadata differs from frozen oracle")
    print(json.dumps({"ok": True, "problem_id": problem["problem_id"],
        "known_causal_truth": False, "checks": "frozen identities, bounded archive, Stata schema, survey/district bookkeeping and source specifications; no causal effect test",
        "files": len(problem["files"])}))


if __name__ == "__main__":
    main()
