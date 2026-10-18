"""Risk-based test prioritisation for the AI-only suite (COMP 441 Week 7).

risk(function) = cyclomatic complexity (radon) x log(1 + 2-year churn of its file)
score(test)    = risk of the functions it executes that no earlier test executed
order          = greedy "additional risk" ordering, ties broken by shorter runtime

Mutation data is NOT used to build the order, so the APFD evaluation on mutants
is a fair, out-of-sample check.

usage: prioritise.py <coverage_contexts.db> <radon_cc.json> <churn.tsv> <durations.txt>
                     <kill_matrix.json> <out_dir>
"""
import ast
import csv
import json
import math
import random
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

db, radon_path, churn_path, dur_path, kill_path, out = sys.argv[1:7]
out = Path(out)

# --- function spans + complexity ---
cc = json.load(open(radon_path))
spans = []  # (file, start, end, qualname, cc)
for f, blocks in cc.items():
    for b in blocks:
        if b["type"] == "class":
            for m in b.get("methods", []):
                spans.append((f, m["lineno"], m["endline"], f"{b['name']}.{m['name']}", m["complexity"]))
        else:
            q = f"{b['classname']}.{b['name']}" if b.get("classname") else b["name"]
            spans.append((f, b["lineno"], b["endline"], q, b["complexity"]))

churn = {}
for row in csv.reader(open(churn_path), delimiter="\t"):
    churn[row[0]] = int(row[1])


def risk(f, c):
    return c * math.log1p(churn.get(f, 0))


def owner(f, line):
    best = None
    for s in spans:
        if s[0] == f and s[1] <= line <= s[2] and (best is None or s[1] > best[1]):
            best = s
    return best


# --- which functions each test executes (coverage contexts) ---
con = sqlite3.connect(db)
files = {i: p for i, p in con.execute("select id, path from file")}
ctx = {i: c for i, c in con.execute("select id, context from context")}
from coverage.numbits import numbits_to_nums  # noqa: E402

test_funcs = defaultdict(set)
for fid, cid, bits in con.execute("select file_id, context_id, numbits from line_bits"):
    name = ctx[cid]
    if not name:
        continue
    test = name.split("|")[0]
    rel = files[fid][files[fid].rindex("tomlkit/"):]
    for ln in numbits_to_nums(bits):
        o = owner(rel, ln)
        if o:
            test_funcs[test].add((o[0], o[3], o[4]))

# --- durations ---
dur = defaultdict(lambda: 0.001)
for line in open(dur_path):
    m = re.match(r"\s*([\d.]+)s (call|setup|teardown)\s+(\S+)", line)
    if m:
        dur[m.group(3)] += float(m.group(1))

tests = sorted(test_funcs)

# --- greedy additional-risk ordering ---
covered, order, remaining = set(), [], set(tests)
while remaining:
    def gain(t):
        return sum(risk(f, c) for f, q, c in test_funcs[t] - covered)
    best = max(remaining, key=lambda t: (gain(t), -dur[t], t))
    order.append((best, gain(best)))
    covered |= test_funcs[best]
    remaining.remove(best)

with open(out / "priority_order.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["rank", "test", "new_risk_covered", "functions_executed", "top_function"])
    for i, (t, g) in enumerate(order, 1):
        top = max(test_funcs[t], key=lambda x: risk(x[0], x[2]))
        w.writerow([i, t, round(g, 1), len(test_funcs[t]), f"{top[1]} (CC {top[2]})"])

# --- APFD on the sampled mutant kill matrix ---
kills = json.load(open(kill_path))  # mutant -> [failing test ids]
faults = {m: set(ts) & set(tests) for m, ts in kills.items()}
faults = {m: ts for m, ts in faults.items() if ts}


def apfd(seq):
    pos = {t: i + 1 for i, t in enumerate(seq)}
    n, m = len(seq), len(faults)
    return 1 - sum(min(pos[t] for t in ts) for ts in faults.values()) / (n * m) + 1 / (2 * n)


def first_detect_curve(seq):
    pos = {t: i + 1 for i, t in enumerate(seq)}
    firsts = sorted(min(pos[t] for t in ts) for ts in faults.values())
    return firsts


prio = [t for t, _ in order]
coll = [l.strip() for l in open(Path(dur_path).with_name("collection_order.txt"))]
default = [t for t in coll if t in set(tests)]  # pytest's real collection order
rng = random.Random(441)
rand = []
for _ in range(200):
    s = tests[:]
    rng.shuffle(s)
    rand.append(apfd(s))

res = {
    "tests": len(tests),
    "mutants_in_matrix": len(faults),
    "apfd_risk_based": round(apfd(prio), 4),
    "apfd_default_order": round(apfd(default), 4),
    "apfd_random_mean": round(sum(rand) / len(rand), 4),
    "apfd_random_min": round(min(rand), 4),
    "apfd_random_max": round(max(rand), 4),
}
for label, seq in [("risk_based", prio), ("default_order", default)]:
    f = first_detect_curve(seq)
    res[f"tests_to_detect_50pct_{label}"] = f[len(f) // 2]
    res[f"tests_to_detect_90pct_{label}"] = f[int(len(f) * 0.9)]
json.dump(res, open(out / "prioritisation_eval.json", "w"), indent=2)

# cumulative detection curve for charting
rows = []
for label, seq in [("Risk-based", prio), ("Default order", default)]:
    pos = {t: i + 1 for i, t in enumerate(seq)}
    firsts = [min(pos[t] for t in ts) for ts in faults.values()]
    for k in [1, 5, 10, 20, 30, 40, 50, 75, 100, 150, 200, 250, 300, len(seq)]:
        rows.append((label, k, round(100 * sum(1 for x in firsts if x <= k) / len(firsts), 1)))
with open(out / "detection_curve.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["order", "tests_run", "pct_mutants_detected"])
    w.writerows(rows)
print(json.dumps(res, indent=2))
