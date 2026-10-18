# Week 7 evidence: Mutation Testing Report v1 (Group A, Track D, tomlkit @ 8c959b5)

## Results (AI-only suite `tests_ai/`, mutmut 3.8.0)
| | Mutants |
|---|---|
| Killed | 3,071 |
| Timeout (counted as detected) | 20 |
| Survived | 1,878 |
| No tests (code never executed) | 386 |
| **Total** | **5,355** |

Mutation score = (killed + timeout) / total = **57.7%** (62.2% of mutants in executed code).

## Reproduce
```bash
. .venv/bin/activate && pip install mutmut==3.8.0 hypothesis
mutmut run --max-children 8           # config in pyproject.toml [tool.mutmut]; ~7 min
mutmut results --all true > week7/mutmut_results_v1.txt
mutmut show <mutant-name>             # diff of one mutant

# kill tests written for 11 survivors (each fails against its mutant):
cp -r tests_manual mutants/ && cd mutants
MUTANT_UNDER_TEST="tomlkit.items.xǁArrayǁinsert__mutmut_14" python -m pytest tests_manual -k test_k6_

# risk-based prioritisation + APFD evaluation
pytest -q --cov=tomlkit --cov-context=test --cov-report= tests_ai --durations=0 > week7/durations_ai.txt
pytest --collect-only -q tests_ai | grep :: > week7/collection_order.txt
python week7/scripts/kill_matrix.py mutants week7/mutmut_results_v1.txt 300 week7/kill_matrix.json
python week7/scripts/prioritise.py .coverage week7/radon_cc.json week7/churn_2y.tsv \
       week7/durations_ai.txt week7/kill_matrix.json week7
python week7/scripts/classify_survivors.py <survivor-list> <diff-dir> week7/survivor_categories_v1.csv
```

## Files
- `mutmut_results_v1.txt`, `mutation_v1_summary.json` - every mutant's status; score per module
- `survivor_categories_v1.csv` - all 1,878 survivors with diff and heuristic category
- `kill_matrix.json` - which AI tests fail for 300 randomly sampled killed mutants (seed 441)
- `priority_order.csv` - ranked execution order for the suite
- `prioritisation_eval.json`, `detection_curve.csv` - APFD of risk-based vs pytest order vs random
- `churn_2y.tsv` - lines changed per file since 2024-10-18 (git log --numstat)
