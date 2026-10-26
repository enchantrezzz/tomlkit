# Week 11 final TDD log (Track D)

**Group A · tomlkit · branch `week11-track-d` · final code commit `6b8884f`**

This is the completed TDD log for the three test-first features delivered in Week 8.
All three cycles were written test-first, one red/green/refactor sequence per
defect, and the commits are merged on `master`. The raw pytest output for every
step is retained in `week8/tdd_runs/` and copied to `week11/tdd_runs/`.

## 1. Cycles

| Cycle | Defect fixed | Step | Commit | Time (SAST) | Evidence | Result |
|---|---|---|---|---|---|---|
| **C1** | **D1** — `date()` accepts datetime strings | Red | `9472f8a` | 2026-10-18 23:00:55 | `c1_red.txt` | 4 failed, 1 passed |
| | | Green | `a4f54db` | 23:01:24 | `c1_green.txt` | 1,475 passed |
| | | Refactor | `fad6c12` | 23:01:45 | `c1_refactor.txt` | 1,475 passed |
| **C2** | **D7** — multiline strings emit a bare CR | Red | `51c6863` | 23:01:59 | `c2_red.txt` | 6 failed, 2 passed |
| | | Green | `a38a3d8` | 23:03:22 | `c2_green.txt` | 1,485 passed |
| | | Refactor | `26421d6` | 23:03:40 | `c2_refactor.txt` | 1,485 passed |
| **C3** | **D6** — `comment()` with a bare CR | Red | `3c33afc` | 23:03:51 | `c3_red.txt` | 2 failed, 2 passed |
| | | Green | `c829a38` | 23:04:11 | `c3_green.txt` | 1,489 passed |
| | | Refactor | `b60559f` | 23:04:37 | `c3_refactor.txt` | 1,489 passed |

Each green step made the smallest change that satisfied the failing tests; each
refactor step kept the full suite green and removed duplication.

## 2. Traceability

| Cycle | Defect | Requirement (RTM) | Test file | Behaviour |
|---|---|---|---|---|
| C1 | D1 | R08 — date/time/datetime factories reject strings of another kind | `tests_tdd/test_tdd_cycles.py` | `tomlkit.date("1979-05-27T07:32:00")` raises `ValueError`; plain dates still work |
| C2 | D7 | R10 — string forms reject sequences invalid for the chosen form | `tests_tdd/test_tdd_cycles.py` | Bare CR is escaped in basic multiline strings and rejected in literal multiline strings; CRLF is preserved |
| C3 | D6 | R14 — comments always produce valid TOML | `tests_tdd/test_tdd_cycles.py` | `comment()` splits every line-break form so the output re-parses |

The defects were not invented for the exercise:

- **D1** was also exposed by the Hypothesis property test
  `test_p5_date_rejects_datetime_strings` in `tests_property/test_properties.py`.
- **D7** was found by Hypothesis property P3 and is recorded as a named
  regression test (`test_d7_multiline_string_with_bare_cr`).
- **D6** was found during the Week 9 exploratory/formatting work; the TDD cycle
  turns it into a permanent regression test.

This gives a clean Track D story: property-based testing found two real
input-space defects, test-first development fixed them, and the mutation report
measures the resulting suite.

## 3. Final verification

Final suite (all project tests):

```bash
python -m pytest -q tests tests_ai tests_manual tests_bdd \
  tests_integration tests_property tests_tdd
```

Result on the frozen Week 11 commit:

```
1502 passed, 5 xfailed
```

(5.6 s on an idle machine; 26.4 s when the mutation run was using all
cores. The pass/fail result is the same.)

Environment: Ubuntu (WSL2), Python 3.13.14, pytest 9.1.1,
pytest-bdd 9.0.0, Hypothesis 6.170.12, mutmut 3.8.0.

The five xfails are the documented open defects/known limitations carried from
earlier weeks (D2, D3, D5, M1 and the D8 spacing case). They are strict xfails,
not silently skipped tests.

## 4. What the TDD cycles changed

- C1: `api.date()` now checks the exact type instead of `isinstance`, so a
  `datetime` is no longer accepted as a `date`.
- C2: `String.from_raw()` escapes a lone CR for basic multiline strings and
  rejects it for literal multiline strings, while preserving CRLF.
- C3: `api.comment()` treats CR, LF and CRLF as line breaks and emits one
  comment marker per line.

The refactors shared the exact-type helper (`_parse_rfc3339_as`) and the
bare-CR rule (`_BARE_CR` / `BARE_CR`) instead of duplicating logic.

## 5. Note on the fourth cycle

No fourth cycle was added. The brief requires at least three test-first
features, and C1–C3 satisfy that requirement. Adding a late fourth change
would have moved the frozen commit used for the Week 11 mutation run and
risked the final evidence for no additional rubric credit.
