"""Compare v2 survivors with the Week 7 v1 survivor categories.

Usage:
    python week11/mutation_v2/scripts/compare_survivors.py \
        week7/survivor_categories_v1.csv \
        week11/mutation_v2/survivors_v2.txt \
        week11/mutation_v2/survivors_v1_v2.csv
"""

import csv
import sys
from pathlib import Path


def main():
    v1_csv, v2_txt, out_csv = sys.argv[1:4]
    v1 = {}
    with open(v1_csv, newline="", encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            v1[row["mutant"]] = row

    v2 = [
        line.strip()
        for line in Path(v2_txt).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    rows = []
    for m in v2:
        old = v1.get(m)
        rows.append(
            {
                "mutant": m,
                "module": m.split(".")[1] if "." in m else "unknown",
                "also_survived_v1": "yes" if old else "no",
                "v1_category": old["category"] if old else "",
                "v1_original": old["original"] if old else "",
                "v1_mutated": old["mutated"] if old else "",
            }
        )

    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["mutant"])
        w.writeheader()
        w.writerows(rows)

    overlap = sum(1 for r in rows if r["also_survived_v1"] == "yes")
    print(f"v2 survivors: {len(rows)}")
    print(f"also survived v1: {overlap}")
    print(f"new since v1: {len(rows) - overlap}")


if __name__ == "__main__":
    main()
