"""Group v2 survivors by function and pick candidates for root-cause analysis.

Usage:
    python week11/mutation_v2/scripts/pick_survivors.py \
        week11/mutation_v2/survivors_v2.txt \
        week11/mutation_v2/survivor_candidates.csv
"""

import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


def function_of(mutant: str) -> str:
    base = mutant.split("__mutmut_")[0]
    # mutmut encodes nested scopes as xǁClassǁmethod; normalise to dots.
    base = base.replace("xǁ", ".").replace("ǁ", ".")
    return base


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    src, out = sys.argv[1:3]
    survivors = [
        line.strip()
        for line in Path(src).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    counts = Counter(function_of(m) for m in survivors)
    examples = defaultdict(list)
    for m in survivors:
        examples[function_of(m)].append(m)

    rows = []
    for fn, n in counts.most_common():
        module = fn.split(".")[1] if "." in fn else "unknown"
        rows.append((fn, module, n, examples[fn][0]))

    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["function", "module", "survivors", "example_mutant"])
        w.writerows(rows)

    print(f"{len(survivors)} survivors across {len(counts)} functions")
    for fn, module, n, example in rows[:25]:
        print(f"{n:4d} {module:12s} {fn}  e.g. {example}")


if __name__ == "__main__":
    main()
