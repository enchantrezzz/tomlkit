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

- Scope: tomlkit/_types.py (4 of 6 planned modules so far; see note)
- Runner: python -m pytest -x --assert=plain tests (tests/ only, 1058 tests)
- Killed: 4 (mutants 6, 8, 9, 10)
- Survived: 6 (mutants 1-5 equivalent; mutant 7 is a test gap, see defect D1)
- Total: 10
- Mutation score (brief formula): 40% (4 / 10 x 100)
- Adjusted score (excluding 5 equivalent mutants): 80% (4 / 5 x 100)
- Week 7 (v1) mutation score for comparison: [FILL IN from Week 7 report]
- Note: items.py, container.py, api.py and parser.py are not yet mutated.

| D1 | 26 Oct 2026 | _CustomDict.__or__ drops existing keys because copy() returns {} (tomlkit/_types.py, line 66) | Mutation testing (mutant 7) |

## Step 5: Defect density

- Lines of code: radon raw -s tomlkit, total SLOC = 4158 (LOC = 6197)
- KLOC: 4.158
- Defects with recorded evidence: 8 (provisional; full group defect log not yet consolidated)
  - D1: date() accepted datetime strings (fixed, commit a4f54db)
  - D2: Bool.__eq__ returns NotImplemented for another Bool (open, xfail)
  - D3: inline-table duplicate raises KeyAlreadyPresent, not ParseError (open, xfail)
  - D5: key([]) serialises to an unparseable key (open, xfail; output is now empty string)
  - D6: comment() writes unparseable TOML for a bare CR (fixed, commit c829a38)
  - D7: bare CR in multiline strings (fixed, commit a38a3d8)
  - D8: insertion at position 0 drops the space after the inserted element (Week 9 session; open)
  - M1: _CustomDict.__or__ drops existing keys because copy() returns {} (open, xfail-noted; mutant 7 survives)
- Defect density: 1.92 defects per KLOC (8 / 4.158), provisional
- Environment note: Week 9 session used Python 3.14.7; Week 10 measurements used Python 3.12.10, pytest 7.4.4

## Step 6: RTM completeness

- Total requirements: 16 (R01 to R16, week6/rtm/rtm_week6.csv)
- Requirements verified by a test of the requirement itself: 14
- RTM completeness: 88% (14 / 16 x 100)
- Excluded: R15 (listed tests do not exercise the D5 case); R16 (untested)
- Test run: poetry run pytest -q tests_ai -> 386 passed, 2 xfailed (D2, D3)
- Partial requirements still counted as verified only where a listed test passes: R03, R04, R12, R13

## Step 7: Property tests (Track D)

- File: tests/test_properties.py
- Hypothesis properties: parse reads back any TOML integer; dumps(parse(s)) == s for integer documents
- Result: 2 passed
- Covered functions: parse, dumps
