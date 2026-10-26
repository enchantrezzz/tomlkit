"""Summarise a mutmut results file for the Week 11 report.

Usage:
    python week11/mutation_v2/scripts/summarise_v2.py \
        week11/mutation_v2/mutmut_results_v2.txt \
        week11/mutation_v2/mutation_v2_summary.json \
        week11/mutation_v2/v1_vs_v2.csv

Input lines look like:
    tomlkit.api.x_loads__mutmut_1: killed
"""

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path


STATUS_KEYS = {
    "killed": "killed",
    "survived": "survived",
    "timeout": "timeout",
    "no tests": "no_tests",
    "suspicious": "suspicious",
    "skipped": "skipped",
}


def module_of(mutant: str) -> str:
    parts = mutant.split(".")
    return parts[1] if len(parts) > 1 else "unknown"


def parse(path: Path):
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        mutant, status = line.rsplit(":", 1)
        status = status.strip().lower()
        if status not in STATUS_KEYS:
            continue
        rows.append((mutant.strip(), module_of(mutant.strip()), STATUS_KEYS[status]))
    return rows


def summarise(rows):
    totals = Counter()
    by_module = {}
    for mutant, module, status in rows:
        totals[status] += 1
        totals["total"] += 1
        m = by_module.setdefault(
            module, Counter(total=0, killed=0, timeout=0, survived=0, no_tests=0)
        )
        m["total"] += 1
        m[status] += 1

    def add_scores(c):
        detected = c["killed"] + c["timeout"]
        c["score"] = round(100.0 * detected / c["total"], 1) if c["total"] else 0.0
        covered = c["total"] - c["no_tests"]
        c["covered_score"] = round(100.0 * detected / covered, 1) if covered else 0.0
        return c

    out = {"TOTAL": add_scores(totals)}
    for module in sorted(by_module):
        out[module] = add_scores(by_module[module])
    return out


def main():
    results_path, out_json, out_csv = sys.argv[1:4]
    rows = parse(Path(results_path))
    summary = summarise(rows)
    Path(out_json).write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")

    survivors = sorted(m for m, _, s in rows if s == "survived")
    Path(out_json).with_name("survivors_v2.txt").write_text(
        "\n".join(survivors) + ("\n" if survivors else ""), encoding="utf-8"
    )

    v1_path = Path("week7/mutation_v1_summary.json")
    v1 = json.loads(v1_path.read_text(encoding="utf-8")) if v1_path.exists() else {"TOTAL": {}}
    modules = sorted(set(summary) | set(v1))
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["module", "v1_total", "v1_score", "v2_total", "v2_score", "delta_pp"])
        for module in modules:
            a = v1.get(module, {})
            b = summary.get(module, {})
            w.writerow(
                [
                    module,
                    a.get("total", ""),
                    a.get("score", ""),
                    b.get("total", ""),
                    b.get("score", ""),
                    round(b.get("score", 0) - a.get("score", 0), 1)
                    if b and a
                    else "",
                ]
            )

    total = summary["TOTAL"]
    print(
        f"total={total['total']} killed={total['killed']} timeout={total['timeout']} "
        f"survived={total['survived']} no_tests={total['no_tests']} "
        f"score={total['score']}% covered={total['covered_score']}%"
    )
    print(f"survivors written: {len(survivors)}")


if __name__ == "__main__":
    main()
