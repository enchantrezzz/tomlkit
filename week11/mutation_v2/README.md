# Week 11 – Mutation testing v2

- Code: `master` at `6b8884f` (includes the Week 8 TDD fixes)
- Tool: mutmut 3.8.0, same `[tool.mutmut]` settings as v1; only `tests_dir` / `also_copy` change
- Score = (killed + timeout) / all mutants

| Run | Test folders | Killed + timeout | Mutants | Score |
|---|---|---|---|---|
| AI-only (re-run on current code) | `tests_ai` | 3,112 | 5,389 | 57.7% |
| Hybrid v2 | `tests_ai`, `tests_manual`, `tests_property`, `tests_tdd`, `tests_bdd`, `tests_integration` | 3,336 | 5,389 | 61.9% |

Hybrid outcome counts: 3,315 killed, 21 timeout, 1,704 survived, 348 no tests, 1 segfault.
Excluding mutants with no covering test: 3,336 / 5,041 = 66.2%.

Files:
- `ai_only_results.txt`, `hybrid_v2_results.txt` – `mutmut results --all true` for each run
- `per_module.csv` – score per module, both runs
- `run_v2.sh` – script used to run both (paths are from the run environment)
