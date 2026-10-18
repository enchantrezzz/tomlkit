# Prompt-Engineering Log — AI Baseline Suite (Week 6)

**Tool:** Claude (Anthropic), model `claude-opus-5-5`, used through the claude.ai app
**Date:** 18 Oct 2026
**Target:** `the-dezeray/tomlkit` @ `8c959b51c7da2734662af759a7c9f95e9a78060a`, package `tomlkit/` (v0.15.1)
**Output folder:** `tests_ai/`. This folder is kept separate from the project's own `tests/` so the AI-only suite can be measured on its own.

**Ground rules given to the model.** These were repeated in every prompt. The model gets the module source and README only. It does **not** see the existing `tests/` folder, the toml-test corpus or the CHANGELOG. This keeps the baseline "AI-only".

---

## P0 — Context / role prompt (sent once, at the start)

> You are a senior Python test engineer. I will give you source files from `tomlkit`, a style-preserving TOML 1.1 parser/serializer. Write **pytest** unit tests only. Use only the public API exported from `tomlkit/__init__.py` unless I name a module. Do not read or assume the project's existing tests. Every test must make a concrete assertion on a value or exception type. Group tests into classes per function or feature. Use `pytest.mark.parametrize` where it removes duplication. Name test files `test_ai_<module>.py`.

## P1 — Public API (`api.py`, `__init__.py`)

> Here is `tomlkit/api.py` and `tomlkit/__init__.py`. Generate unit tests for every public function: `parse/loads`, `dumps/dump/load`, `document`, the item factories (`integer`, `float_`, `boolean`, `string`, `date`, `time`, `datetime`, `array`, `table`, `inline_table`, `aot`, `key`, `value`, `key_value`, `ws`, `nl`, `comment`) and `register_encoder/unregister_encoder`. Cover the happy path, at least one invalid-input case per function, and round-trip (parse → dumps returns the identical string).

## P2 — Parser behaviour (via `parse`)

> Here is `tomlkit/parser.py`. Using only `tomlkit.parse` / `tomlkit.dumps`, write tests for: bare/quoted/dotted keys, all four string kinds and escapes, integers (dec/hex/oct/bin, underscores, signs), floats (exp, inf, nan), booleans, offset/local datetimes, dates, times, arrays (nested, multiline, trailing comma), inline tables, standard tables, arrays of tables, comments, and malformed input that must raise `ParseError` subclasses (duplicate keys, unterminated strings, invalid numbers, redefined tables). Check the `line`/`col` on at least one error.

## P3 — Items (`items.py`)

> Here is `tomlkit/items.py`. Write unit tests for `item()` conversion of Python types (bool, int, float, str, list, tuple, dict, list-of-dicts, date/time/datetime, unsupported type), `StringType.select`, `String.from_raw` (escaping, invalid sequences), `Integer`/`Float` arithmetic keeping TOML types, `Bool`, `Date`/`Time`/`DateTime` arithmetic, `Array` mutation (`append`, `insert`, `__setitem__`, `__delitem__`, `add_line`, `multiline`, slice assignment), `Table`/`InlineTable` (`append`, `add`, `remove`, `setdefault`, `unwrap`), `AoT`, `Key`/`SingleKey`/`DottedKey`, and `Item.comment` / `Item.indent`.

## P4 — Container / document editing (`container.py`)

> Here is `tomlkit/container.py`. Through `TOMLDocument` (a `Container`), test: adding/updating/deleting keys, preserving comments and whitespace when editing a parsed document, adding new tables after existing ones, dotted-key access, out-of-order tables, `unwrap()` returning plain Python types, `copy()`, `setdefault`, `KeyAlreadyPresent` and `NonExistentKey` errors.

## P5 — Utilities & errors (`_utils.py`, `source.py`, `exceptions.py`)

> Here are `_utils.py`, `source.py` and `exceptions.py`. Write tests for `parse_rfc3339` (datetime with Z / offsets / fraction, date, time, invalid), `escape_string`, `merge_dicts`, `Source` navigation (`inc`, `mark`, `extract`, `consume`, `end`, `_to_linecol`) and the exception classes' messages and `line`/`col`.

## P6 — File I/O (`toml_file.py`)

> Here is `tomlkit/toml_file.py`. Using pytest's `tmp_path`, test `TOMLFile.read` and `TOMLFile.write`, including preservation of `\n`, `\r\n` and mixed line endings on round-trip.

---

## Iterations (repair prompts)

The first generated suite was run unedited. Any test that failed was **not** silently fixed. Each failure is logged below with the repair prompt used. Failures where the AI's expectation was wrong are themselves a finding for the report.

**Run 1 (unedited output):** 387 tests collected. 379 passed and 8 failed.

| # | Failing test | Cause | Action |
|---|---|---|---|
| 1 | `test_ai_api::TestDateTimeFactories::test_date_rejects_datetime` | **Library defect D1.** `date()` checks `isinstance(value, date)`, and `datetime` is a subclass of `date`. | Kept as `xfail(strict=True)` |
| 2 | `test_ai_items::TestPickle` (Bool param) | **Library defect D2.** `Bool.__eq__` returns `NotImplemented` for another `Bool`, so `item(True) != item(True)`. | Split into a strict xfail plus a value check |
| 3 | `test_ai_parser::TestInlineTables::test_duplicate_key_in_inline` | **Library defect D3.** The inline duplicate raises a bare `KeyAlreadyPresent`, which is not a `ParseError` or a `ValueError`. | Kept as `xfail(strict=True, raises=KeyAlreadyPresent)` |
| 4 | `test_ai_items::TestStringType::test_toggle` | AI assumption wrong. `toggle()` flips single-line ↔ multi-line. | Repaired (R1) |
| 5 | `test_ai_items::TestKeys::test_concat` | AI misread the name `is_dotted()`. It means "followed by more keys" (parser state). | Repaired to `is_multi()` (R2) |
| 6 | `test_ai_parser::TestKeys::test_duplicate_key` | AI expected `KeyAlreadyPresent`. A top-level duplicate is wrapped in `ParseError`. | Repaired (R3) |
| 7 | `test_ai_utils::TestSource::test_inc_raises_when_asked` | Test misused the API (`UnexpectedCharError` needs a `char` argument). | Repaired (R4) |
| 8 | `test_ai_utils::TestExceptions::test_messages` | AI guessed the message format wrongly. | Repaired (R5, took 2 attempts) |

**Repair prompt used (R1–R5):**

> These tests fail against the real library. For each one, here is the traceback and the relevant source. If the source shows the library behaves as designed, fix the test's expectation and add a one-line comment explaining why. If the behaviour contradicts the docstring or README, do NOT change the expectation. Instead mark it `@pytest.mark.xfail(strict=True, reason="DEFECT ...")`.

**Run 2:** 388 collected, 385 passed, 3 xfailed (D1–D3). This is the frozen **AI-only baseline (v0)** that Week 7 mutation testing runs against.
