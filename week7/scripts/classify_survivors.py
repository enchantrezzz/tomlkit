"""Classify surviving mutants by the kind of change, from their diffs.
usage: classify_survivors.py <survivors.txt> <diff_dir> <out.csv>"""
import csv, re, sys, collections
from pathlib import Path

surv = [l.strip() for l in open(sys.argv[1]) if l.strip()]
d = Path(sys.argv[2])

RULES = [
    ("Exception message or construction", lambda m, a, b: ("exceptions" in m) or re.search(r"(Error|raise|message|msg)", a) and re.search(r"XX|\.lower|\.upper|None\)|\(None", b) or ('"' in a and a.lower() == b.lower() and a != b and re.search(r"Error|raise", a))),
    ("String literal changed (XX..XX / case)", lambda m, a, b: "XX" in b or (a.lower() == b.lower() and a != b)),
    ("Control flow (continue/break/return)", lambda m, a, b: re.fullmatch(r"(continue|break|return)\b.*", a) and re.fullmatch(r"(continue|break|return)\b.*", b)),
    ("Argument dropped or set to None", lambda m, a, b: b.count("None") > a.count("None") or len(b) < len(a) and a.replace(" ", "").startswith(b.replace(" ", "")[:10]) and "," in a),
    ("Boundary / off-by-one (< vs <=, +1, index)", lambda m, a, b: re.search(r"(<=|>=|<|>|\[\d+:?\]|[+-] ?\d)", a) and re.sub(r"\d", "", a) == re.sub(r"\d", "", b) or re.sub(r"<=|>=", "<", a) == re.sub(r"<=|>=", "<", b) or re.sub(r"[<>]=?", "<", a) == re.sub(r"[<>]=?", "<", b)),
    ("Boolean logic (and/or, True/False, not)", lambda m, a, b: re.search(r"\b(and|or|True|False|not)\b", a + b)),
    ("Arithmetic / assignment operator", lambda m, a, b: re.search(r"[+\-*/]=?|==|!=", a + b)),
]

counts = collections.Counter()
rows = []
for m in surv:
    p = d / f"{m}.diff"
    if not p.exists():
        continue
    lines = p.read_text().splitlines()
    a = " ".join(l[1:].strip() for l in lines if l.startswith("-"))
    b = " ".join(l[1:].strip() for l in lines if l.startswith("+"))
    cat = "Other"
    for name, rule in RULES:
        try:
            if rule(m, a, b):
                cat = name
                break
        except Exception:
            pass
    counts[cat] += 1
    rows.append((m, cat, a[:120], b[:120]))
with open(sys.argv[3], "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["mutant", "category", "original", "mutated"]); w.writerows(rows)
tot = sum(counts.values())
for k, v in counts.most_common():
    print(f"{v:5d} {100*v/tot:5.1f}%  {k}")
print(tot)
