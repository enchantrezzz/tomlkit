"""Classify each AI test by assertion strength (AST-based heuristic)."""
import ast, sys, json, pathlib, csv

def classify(fn):
    asserts, raises, weak = [], 0, []
    for node in ast.walk(fn):
        if isinstance(node, ast.Assert):
            asserts.append(node)
        if isinstance(node, ast.With):
            for it in node.items:
                c = it.context_expr
                if isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "raises":
                    raises += 1
                    arg = c.args[0] if c.args else None
                    name = ast.unparse(arg) if arg is not None else ""
                    has_match = any(k.arg == "match" for k in c.keywords)
                    if name in ("ParseError", "ValueError", "TypeError", "(UnexpectedEofError, ParseError)") and not has_match:
                        weak.append(f"broad exception: raises({name}) without match")
    for a in asserts:
        t = a.test
        src = ast.unparse(t)
        if isinstance(t, ast.Call) and getattr(t.func, "id", "") == "isinstance":
            weak.append(f"type-only: {src}")
        elif isinstance(t, ast.Compare) and any(isinstance(o, ast.In) for o in t.ops) and isinstance(t.left, ast.Constant) and isinstance(t.left.value, str):
            weak.append(f"substring: {src}")
        elif isinstance(t, ast.BoolOp) and isinstance(t.op, ast.Or):
            weak.append(f"disjunctive: {src[:70]}")
        elif isinstance(t, ast.Compare) and any(isinstance(o, (ast.GtE, ast.LtE)) for o in t.ops):
            weak.append(f"inequality: {src}")
    strong = len(asserts) - len([w for w in weak if not w.startswith("broad")])
    if not asserts and not raises:
        verdict = "NO-ASSERT (smoke)"
    elif strong <= 0 and not raises:
        verdict = "WEAK"
    elif weak and (strong <= 0 or all(w.startswith("broad") for w in weak) and not asserts):
        verdict = "WEAK"
    elif weak:
        verdict = "PARTIAL"
    else:
        verdict = "STRONG"
    return len(asserts), raises, verdict, weak

rows = []
for f in sorted(pathlib.Path(sys.argv[1]).glob("test_ai_*.py")):
    tree = ast.parse(f.read_text())
    for cls in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
        for fn in [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test")]:
            n_a, n_r, v, w = classify(fn)
            rows.append(dict(file=f.name, test=f"{cls.name}::{fn.name}", asserts=n_a, raises=n_r, verdict=v, notes="; ".join(w)))
with open(sys.argv[2], "w", newline="") as fh:
    wr = csv.DictWriter(fh, fieldnames=rows[0].keys()); wr.writeheader(); wr.writerows(rows)
from collections import Counter
print(Counter(r["verdict"] for r in rows), "functions:", len(rows))
for r in rows:
    if r["verdict"] != "STRONG": print(r["verdict"], r["file"], r["test"], "|", r["notes"])
