# Week 6 evidence (Group A, Track D, tomlkit @ 8c959b5)

Run everything from the repo root.

## Reproduce
```bash
python -m venv .venv && . .venv/bin/activate
pip install -e . pytest pytest-cov radon pylint ruff crosshair-tool
git submodule update --init

# AI-only baseline (expect 385 passed, 3 xfailed; 81.7% stmt / 66.3% branch)
pytest -q --cov=tomlkit --cov-branch --cov-report=html:week6/htmlcov_ai tests_ai
# Existing suite, separate run (expect 1058 passed; 89.5% / 83.1%)
pytest -q --cov=tomlkit --cov-branch tests

python week6/scripts/assert_audit.py tests_ai week6/assertion_audit.csv
python week6/scripts/gap_by_function.py week6/cov_ai.json . 25

radon cc tomlkit -s -n C --total-average
radon mi tomlkit -s
pylint tomlkit --disable=C0114,C0115,C0116
ruff check tomlkit --select ALL --statistics

cd week6/symbolic && crosshair check ch_date.py --per_condition_timeout=60
```

## Files
- `tests_ai/` — AI-generated suite + `PROMPT_LOG.md` (prompts, iterations)
- `rtm/rtm_week6.csv` — traceability matrix (16 requirements); `build_rtm.py` validates test refs
- `assertion_audit.csv` — per-test assertion verdict
- `htmlcov_ai/`, `cov_*.json` — coverage
- `radon_*`, `pylint.txt` — static analysis
- `symbolic/` — CrossHair contract + counterexample for defect D1
