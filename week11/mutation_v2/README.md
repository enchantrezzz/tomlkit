# Week 11 mutation testing v2 — evidence

**Track D · tomlkit · final hybrid suite**

This folder contains the Week 11 re-run of mutation testing on the final
project suite. The report is `mutation_v2_report.md`.

## Scope

- Source under mutation: `tomlkit/`, excluding `tomlkit/_compat.py` (platform
  compatibility shim) and `tomlkit/_types.py` (covered by the separate Week 10
  `_types.py` exercise). This keeps the v2 scope comparable to the Week 7 v1
  baseline.
- Final hybrid suite:
  `tests/`, `tests_ai/`, `tests_manual/`, `tests_bdd/`,
  `tests_integration/`, `tests_property/`, `tests_tdd/`.
- Runner: mutmut 3.8.0 on Ubuntu (WSL2), Python 3.13.14, pytest 9.1.1.
- One test is deselected because mutmut's trampoline adds stack frames to a
  deliberately deeply nested parser input and triggers `RecursionError`:
  `test_parse_rejects_deeply_nested_documents`. The test still runs in the
  normal suite; it is not part of the mutation run.

## Reproduce

```bash
# WSL2 / Ubuntu, from the repository root
python3 -m venv .venv && . .venv/bin/activate
pip install -e . pytest pytest-cov hypothesis pytest-bdd radon "mutmut==3.8.0"
git submodule update --init --recursive

# [tool.mutmut] used for the run:
# source_paths = ["tomlkit/"]
# tests_dir = ["tests/", "tests_ai/", "tests_manual/", "tests_bdd/",
#              "tests_integration/", "tests_property/", "tests_tdd/"]
# also_copy = [same directories]
# do_not_mutate = ["tomlkit/_compat.py", "tomlkit/_types.py"]
# pytest_add_cli_args = ["-p", "no:cacheprovider", "-k",
#                        "not test_parse_rejects_deeply_nested_documents"]

mutmut run --max-children 8
mutmut results --all true > week11/mutation_v2/mutmut_results_v2.txt
python week11/mutation_v2/scripts/summarise_v2.py \
  week11/mutation_v2/mutmut_results_v2.txt \
  week11/mutation_v2/mutation_v2_summary.json \
  week11/mutation_v2/v1_vs_v2.csv
```

## Files

| File | Purpose |
|---|---|
| `mutation_v2_report.md` | Report (Markdown source) |
| `mutmut_results_v2.txt` | Raw mutmut status for every mutant |
| `mutation_v2_summary.json` | Overall and per-module counts/scores |
| `v1_vs_v2.csv` | Week 7 v1 vs Week 11 v2 by module |
| `survivors_v2.txt` | Surviving mutant names |
| `survivor_rootcause_v2.md` | Root-cause analysis of selected survivors |
| `scripts/summarise_v2.py` | Builds the summary and comparison |

## Score formula

`score = (killed + timeout) / total × 100`

`covered_score = (killed + timeout) / (total − no_tests) × 100`

Timeouts are counted as detected, following the Week 7 convention. `no_tests`
means the mutated line was never executed by the suite.
