# Track D specialised stream — property-based testing checkpoint

**Group A · tomlkit · Week 11**

Track D's specialised stream is property-based testing with Hypothesis. It was
introduced in Weeks 6–7 and is summarised here because it is the source of two
of the three TDD cycles in `week11/TDD_LOG.md`. This is not a new Week 11
deliverable; it is the completed Track D stream evidence for the final report.

## Why property-based testing for tomlkit

tomlkit is a parser/serialiser. Its main risk is not a single known example but
the input space: empty and malformed documents, unusual Unicode, all four TOML
string forms, integer boundaries, timezone offsets, and nested documents. An
example-based AI suite tests the examples the model thought of. Properties
state invariants over generated inputs and let Hypothesis search for
counterexamples.

## Properties implemented

File: `tests_property/test_properties.py`. Each property runs 200 generated
examples (Hypothesis `ci` profile).

| ID | Property | Strategy / input domain | Why it matters |
|---|---|---|---|
| P1 | `dumps(data)` then `parse(...).unwrap()` preserves the data | Recursive JSON-like docs with TOML scalars, lists and dicts | Serialise/parse contract |
| P2 | An unmodified document re-serialises byte-identically | Documents produced by `dumps` | Style/format preservation |
| P3 | `String.from_raw(s, kind)` round-trips, or literal forms reject invalid input | Arbitrary Unicode text × all `StringType` values | All four string forms, escaping and rejection |
| P4 | `integer(n)` / `value()` round-trip signed 64-bit integers | `INT64` boundaries | Numeric boundaries and raw text |
| P5 | `date()`, `time()`, `datetime()` accept exactly their own kind | Dates, times, datetimes with UTC/offset/naive zones | Factory contract and RFC 3339 handling |
| D7 | Multiline strings never emit a bare CR; CRLF is preserved | Bare CR / CRLF strings in MLB and MLL | Regression for a real defect |

## Evidence

Command:

```bash
python -m pytest -q tests_property -v
```

Result on the Week 11 frozen commit:

```
10 passed in 6.15s
```

Environment: Python 3.13.14, pytest 9.1.1, Hypothesis 6.170.12.

Raw output: `week11/property/pytest_property.txt`.

## What the stream found

Hypothesis produced two counterexamples that became real defects and TDD
cycles:

1. **D1 — `date()` accepted a datetime string.** `datetime` is a subclass of
   `date`, and `api.date()` used `isinstance`. Property P5 exposed the
   contract violation. Fixed test-first in C1 (`9472f8a` → `a4f54db` →
   `fad6c12`).
2. **D7 — multiline strings emitted a bare CR.** Property P3 generated a
   string containing a lone `\r`; `String.from_raw` emitted it inside a
   multiline string, producing output that did not round-trip. Fixed test-first
   in C2 (`51c6863` → `a38a3d8` → `26421d6`).

D6 (`comment()` with a bare CR) was found through exploratory testing rather
than PBT, and fixed in C3. Together these show the complementary value of
property-based, example-based and exploratory testing.

## Limitations

- Hypothesis is a search procedure, not a proof; 200 examples is a bounded
  sample, not exhaustive coverage.
- The document strategy generates valid Python data, not arbitrary TOML text;
  it does not exhaustively test the grammar or invalid-input space.
- Stateful testing (`RuleBasedStateMachine`) for repeated edits was not used;
  the Week 9 exploratory session covered repeated array edits manually.
- A passing property does not prove the absence of bugs; mutation testing
  measures how well the property suite detects seeded faults.

## Link to Week 11

The TDD regression tests are part of the final hybrid suite measured in
`week11/mutation_v2/`. The mutation report records the score improvement from
the Week 7 AI-only baseline to the final suite and identifies the survivors
that remain.
