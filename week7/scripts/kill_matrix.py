"""Build a per-test kill matrix for a random sample of killed mutants.
Runs the AI suite once per mutant inside mutmut's mutants/ dir and records which tests fail."""
import json, os, random, re, subprocess, sys
mutants_dir, results_txt, n, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
killed = [l.split(":")[0].strip() for l in open(results_txt) if l.strip().endswith("killed")]
random.Random(441).shuffle(killed)
sample = killed[:n]
matrix = {}
for i, m in enumerate(sample):
    env = dict(os.environ, MUTANT_UNDER_TEST=m)
    p = subprocess.run([sys.executable, "-m", "pytest", "tests_ai", "-q", "--tb=no", "-rf", "-p", "no:cacheprovider", "-p", "no:randomly"],
                       cwd=mutants_dir, env=env, capture_output=True, text=True, timeout=120)
    failed = re.findall(r"^FAILED (\S+)", p.stdout, re.M)
    failed = [f.split(" - ")[0] for f in failed]
    matrix[m] = failed
    if i % 25 == 0: print(i, m, len(failed), flush=True)
json.dump(matrix, open(out, "w"), indent=1)
print("done", len(matrix), sum(1 for v in matrix.values() if v))
