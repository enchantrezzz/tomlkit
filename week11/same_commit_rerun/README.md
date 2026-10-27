# Week 11 – same-commit mutation re-run

Separates the effect of the tests from the effect of the Week 8 code fixes.
The official v2 result (77.4%, full hybrid suite) is in `../mutation_v2/`.

- Code: `master` at `6b8884f` (same commit as v2)
- Tool: mutmut 3.8.0, same `[tool.mutmut]` scope as v1/v2; only `tests_dir` / `also_copy` change
- Score = (killed + timeout) / all mutants

| Run | Test folders | Killed + timeout | Score |
|---|---|---|---|
| AI-only | `tests_ai` | 3,112 / 5,389 | 57.7% |
| AI + group tests | `tests_ai`, `tests_manual`, `tests_property`, `tests_tdd`, `tests_bdd`, `tests_integration` | 3,336 / 5,389 | 61.9% |
| Full hybrid (v2, for reference) | the above + maintainers' `tests/` | 4,170 / 5,389 | 77.4% |

The AI-only score on `6b8884f` is 0.1 points below v1 (57.8% on `8c959b5`), so the
code fixes barely change it. Of the +19.6-point v1→v2 gain, about 4.2 points come from
the group's tests and about 15.5 from the maintainers' existing suite.

AI + group outcome counts: 3,315 killed, 21 timeout, 1,704 survived, 348 no tests, 1 segfault.

Files: `ai_only_results.txt`, `ai_plus_group_results.txt` (`mutmut results --all true`),
`per_module.csv`, `run.sh` (paths are from the run environment).
