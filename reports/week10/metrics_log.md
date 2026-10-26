# Week 10 Metrics Log: tomlkit (Track D)

Group project: COMP 441, AI-Augmented Test Suite
Repository: the-dezeray/tomlkit (fork of python-poetry/tomlkit)

## Step 2: Test suite run

- Date: 26 October 2026
- Command: `poetry run pytest -q tests`
- Result: 1058 passed, 0 failed
- Duration: 6.86s

## Step 3: Coverage

- Command: `poetry run pytest --cov=tomlkit --cov-branch --cov-report=term --cov-report=html tests`
- Tests: 1058 passed in 23.53s
- Statements: 3330 total, 353 missed, 2977 covered
- Statement coverage: 89.4% (2977 / 3330)
- Branches: 1523 total, 1282 covered, 241 missed
- Branch coverage: 84.2% (1282 / 1523)
- Combined coverage (coverage.py "Cover" column): 88% (not used in the report)
- Excluded lines: 12 (not counted in either figure)
- Weakest modules: _types.py (57%), items.py (81%), container.py (88%)
- Raw data: reports/week10/coverage.json, htmlcov/index.html

## Step 4: Mutation testing

- Scope: TBD
- Killed: TBD
- Survived: TBD
- Total: TBD
- Mutation score: TBD (killed / (killed + survived) x 100)
- Week 7 (v1) mutation score for comparison: TBD

## Step 5: Defect density

- Lines of code (SLOC, source only): TBD
- KLOC: TBD
- Defects found during project: TBD
- Defect density: TBD (defects / KLOC)

## Step 6: RTM completeness

- Total requirements: TBD
- Requirements with at least one passing test: TBD
- RTM completeness: TBD %

## Step 7: Property tests

- Functions covered by Hypothesis tests: TBD
