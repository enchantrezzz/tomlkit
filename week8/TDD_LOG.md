# TDD log (Week 8, branch `week8-tdd`)

Each cycle has three commits: **red** (failing test only), **green** (minimal code change), **refactor** (no behaviour change, full suite green).
Raw pytest output for each step is in `tdd_runs/`. Times are commit times (SAST, UTC+2).

| Cycle | Defect | Step | Commit | Time | Evidence |
|---|---|---|---|---|---|
| C1 | D1 `date()` accepts datetime strings | Red | `19da06d` | 2026-10-18 23:00:55 | `tdd_runs/c1_red.txt`: 4 failed, 1 passed |
| | | Green | `fadd627` | 23:01:24 | one-line change in `api.date`; D1 xfail markers removed; 1,475 passed |
| | | Refactor | `9aeceab` | 23:01:45 | `_parse_rfc3339_as()` shared by date/time/datetime; 1,475 passed |
| C2 | D7 multiline strings emit a bare CR | Red | `2ad89a0` | 23:01:59 | `tdd_runs/c2_red.txt`: 6 failed, 2 passed |
| | | Green | `0f76f93` | 23:03:22 | `String.from_raw` escapes (MLB) or rejects (MLL) a lone CR; 1,485 passed |
| | | Refactor | `70d945c` | 23:03:40 | regex named once as `_BARE_CR`; 1,485 passed |
| C3 | D6 `comment()` with a bare CR | Red | `8377894` | 23:03:51 | `tdd_runs/c3_red.txt`: 2 failed, 2 passed |
| | | Green | `5e063da` | 23:04:11 | `api.comment` treats a lone CR as a line break; 1,489 passed |
| | | Refactor | `c44e251` | 23:04:37 | `BARE_CR` moved to `_utils` and shared by C2 and C3; 1,489 passed |

Tests: `tests_tdd/test_tdd_cycles.py`. Full-suite count = tests/ + tests_ai/ + tests_manual/ + tests_property/ + tests_tdd/.
