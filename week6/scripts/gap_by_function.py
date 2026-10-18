"""Map missed lines/branches from coverage JSON to enclosing functions."""
import ast, json, sys, collections
cov = json.load(open(sys.argv[1]))
root = sys.argv[2]
out = []
for fname, data in cov["files"].items():
    if fname.endswith(("__init__.py", "_types.py", "_compat.py")): continue
    tree = ast.parse(open(f"{root}/{fname}").read())
    funcs = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.append((node.lineno, node.end_lineno, node.name))
    cls_of = {}
    for c in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
        for n in c.body:
            if isinstance(n, ast.FunctionDef): cls_of[n.lineno] = c.name
    def owner(line):
        best = None
        for s, e, n in funcs:
            if s <= line <= e and (best is None or s > best[0]): best = (s, e, n)
        if not best: return "<module>"
        return f"{cls_of.get(best[0], '')}.{best[2]}".lstrip(".")
    miss = collections.Counter(owner(l) for l in data["missing_lines"])
    for fn, n in miss.items(): out.append((n, fname, fn))
for n, f, fn in sorted(out, reverse=True)[: int(sys.argv[3])]:
    print(f"{n:4d}  {f}  {fn}")
